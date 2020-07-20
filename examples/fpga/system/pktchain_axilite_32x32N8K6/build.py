from prga import *
from prga.core.context import Context

from prga.netlist.module.module import Module
from prga.netlist.module.util import ModuleUtils
from prga.netlist.net.common import PortDirection
from prga.integration.integration import Integration

from itertools import product, chain
import os, sys

K, N = 6, 8
maw, mdw = 10, 32
subarray_width, subarray_height = 4, 4  # must be even
top_width, top_height = 8, 8            # must be even
memcol_idx = (2, )

try:
    ctx = Context.unpickle("ctx.tmp.pkl")

except FileNotFoundError:
    ctx = Pktchain.new_context(phit_width = 32, cfg_width = 1)
    
    # ============================================================================
    # -- Routing Resources -------------------------------------------------------
    # ============================================================================
    gbl_clk = ctx.create_global("clk", is_clock = True)
    gbl_clk.bind((0, 16), 0)
    l1a = ctx.create_segment('L1', 40, 1)
    l4a = ctx.create_segment('L4', 20, 4)
    
    # ============================================================================
    # -- Primitives --------------------------------------------------------------
    # ============================================================================
    memory = ctx.build_memory("prga_RAM", maw, mdw).commit()
    
    # ============================================================================
    # -- Blocks ------------------------------------------------------------------
    # ============================================================================
    # -- IOB ---------------------------------------------------------------------
    builder = ctx.build_io_block("iob")
    o = builder.create_input("outpad", 1)
    i = builder.create_output("inpad", 1)
    builder.connect(builder.instances['io'].pins['inpad'], i)
    builder.connect(o, builder.instances['io'].pins['outpad'])
    iob = builder.commit()
    
    # -- CLB ---------------------------------------------------------------------
    builder = ctx.build_logic_block("prga_clb")
    clk = builder.create_global(gbl_clk, Orientation.south)
    in_ = builder.create_input("in", N * 6 // 2, Orientation.west)
    out = builder.create_output("out", N * 2, Orientation.east)
    cin = builder.create_input("cin", 1, Orientation.south)
    xbar_i, xbar_o = [in_], []
    for i, inst in enumerate(builder.instantiate(ctx.primitives["fle6"], "i_cluster", N)):
        builder.connect(clk, inst.pins['clk'])
        builder.connect(inst.pins['out'], out[2 * i: 2 * (i + 1)])
        builder.connect(cin, inst.pins["cin"], vpr_pack_patterns = ["carrychain"])
        xbar_i.append(inst.pins["out"])
        xbar_o.append(inst.pins["in"])
        cin = inst.pins["cout"]
    builder.connect(cin, builder.create_output("cout", 1, Orientation.north), vpr_pack_patterns = ["carrychain"])
    # crossbar
    builder.connect(xbar_i, xbar_o, fully = True)
    clb = builder.commit()
    
    ctx.create_tunnel("carrychain", clb.ports["cout"], clb.ports["cin"], (0, -1))
    
    # -- BRAM --------------------------------------------------------------------
    builder = ctx.build_logic_block("prga_bram", 1, subarray_height)
    inst = builder.instantiate(memory, "i_ram")
    builder.connect(builder.create_global(gbl_clk, Orientation.south), inst.pins["clk"])
    builder.connect(builder.create_input("addr1", len(inst.pins["addr1"]), Orientation.south, (0, 0)), inst.pins["addr1"])
    builder.connect(builder.create_input("we1", len(inst.pins["we1"]), Orientation.south, (0, 0)), inst.pins["we1"])
    builder.connect(builder.create_input("addr2", len(inst.pins["addr2"]), Orientation.north, (0, subarray_height - 1)),
            inst.pins["addr2"])
    builder.connect(builder.create_input("we2", len(inst.pins["we2"]), Orientation.north, (0, subarray_height - 1)),
            inst.pins["we2"])
    w = len(inst.pins["data1"]) // subarray_height + (1 if len(inst.pins["data1"]) % subarray_height else 0)
    for i in range(subarray_height):
        ww = min(w, len(inst.pins["data1"]) - i * w)
        slice_ = slice(i * w, i * w + ww)
        builder.connect(builder.create_input("data1_"+str(i), ww, Orientation.west, (0, i)), inst.pins["data1"][slice_])
        builder.connect(builder.create_input("data2_"+str(i), ww, Orientation.west, (0, i)), inst.pins["data2"][slice_])
        builder.connect(inst.pins["out1"][slice_], builder.create_output("out1_"+str(i), ww, Orientation.east, (0, i)))
        builder.connect(inst.pins["out2"][slice_], builder.create_output("out2_"+str(i), ww, Orientation.east, (0, i)))
    bram = builder.commit()
    
    # ============================================================================
    # -- Tiles -------------------------------------------------------------------
    # ============================================================================
    iotile = ctx.build_tile(iob, 16, edge = OrientationTuple(False, west = True)).fill( (.5, .5) ).auto_connect().commit()
    clbtile = ctx.build_tile(clb).fill( (0.25, 0.15) ).auto_connect().commit()
    bramtile = ctx.build_tile(bram).fill( (0.4, 0.25) ).auto_connect().commit()
    
    # ============================================================================
    # -- Subarrays ---------------------------------------------------------------
    # ============================================================================
    pattern = SwitchBoxPattern.cycle_free
    
    # -- CLB Subarray ------------------------------------------------------------
    builder = ctx.build_array("prga_logic_region", subarray_width, subarray_height, set_as_top = False)
    for x, y in product(range(builder.width), range(builder.height)):
        builder.instantiate(clbtile, (x, y))
    logicregion = builder.fill( pattern ).auto_connect().commit()
    
    # -- RAM Subarray ------------------------------------------------------------
    builder = ctx.build_array("prga_mem_region", subarray_width, subarray_height, set_as_top = False)
    for x, y in product(range(builder.width), range(builder.height)):
        if x == builder.width // 2:
            if y == 0:
                builder.instantiate(bramtile, (x, y))
        else:
            builder.instantiate(clbtile, (x, y))
    memregion = builder.fill( pattern ).auto_connect().commit()
    
    # -- IOs ---------------------------------------------------------------------
    builder = ctx.build_array("prga_io_region", 1, subarray_height,
            set_as_top = False, edge = OrientationTuple(False, west = True))
    for x, y in product(range(builder.width), range(builder.height)):
        builder.instantiate(iotile, (x, y))
    ioregion = builder.fill( pattern ).auto_connect().commit()
    
    # -- Edge Fillers ------------------------------------------------------------
    edgefillers = {}
    for ori in Orientation:
        if ori.is_west:
            continue
        builder = ctx.build_array("prga_edge_region_{}".format(ori.name[0]),
                1 if ori.dimension.is_x else subarray_width,
                1 if ori.dimension.is_y else subarray_height,
                set_as_top = False, edge = OrientationTuple(False, **{ori.name: True}))
        edgefillers[ori] = builder.fill( pattern ).auto_connect().commit()
    
    # -- Corner Fillers ----------------------------------------------------------
    cornerregions = {}
    for corner in Corner:
        builder = ctx.build_array("prga_corner_region_{}".format(corner.case("ne", "nw", "se", "sw")), 1, 1,
                set_as_top = False, edge = OrientationTuple(False, **{ori.name: True for ori in corner.decompose()}))
        cornerregions[corner] = builder.fill( pattern ).auto_connect().commit()
    
    # ============================================================================
    # -- Fabric ------------------------------------------------------------------
    # ============================================================================
    builder = ctx.build_array("prga_fabric", top_width * subarray_width + 2, top_height * subarray_height + 2,
            set_as_top = True)
    for x, y in product(range(builder.width), range(builder.height)):
        if x == 0:
            if y == 0:
                builder.instantiate(cornerregions[Corner.southwest], (x, y))
            elif y == top_height * subarray_height + 1:
                builder.instantiate(cornerregions[Corner.northwest], (x, y))
            elif y % subarray_height == 1:
                builder.instantiate(ioregion, (x, y))
        elif x == top_width * subarray_width + 1:
            if y == 0:
                builder.instantiate(cornerregions[Corner.southeast], (x, y))
            elif y == top_height * subarray_height + 1:
                builder.instantiate(cornerregions[Corner.northeast], (x, y))
            elif y % subarray_height == 1:
                builder.instantiate(edgefillers[Orientation.east], (x, y))
        elif x % subarray_width == 1:
            if y == 0:
                builder.instantiate(edgefillers[Orientation.south], (x, y))
            elif y == top_height * subarray_height + 1:
                builder.instantiate(edgefillers[Orientation.north], (x, y))
            elif y % subarray_height == 1:
                if (x - 1) // subarray_width in memcol_idx:
                    builder.instantiate(memregion, (x, y))
                else:
                    builder.instantiate(logicregion, (x, y))
    fabric = builder.auto_connect().commit()

    # ============================================================================
    # -- Configuration Chain Injection -------------------------------------------
    # ============================================================================
    def iter_instances(module):
        if module.name in ("prga_logic_region", "prga_mem_region"):
            for x in range(subarray_width):
                if x % 2 == 0:
                    for y in range(subarray_height):
                        if y > 0 and (i := module.instances.get( ((x, y), Corner.southwest) )): yield i
                        if i := module.instances.get( ((x, y), Corner.northwest) ): yield i
                    for y in reversed(range(subarray_height)):
                        if i := module.instances.get( (x, y) ): yield i
                    for y in range(subarray_height):
                        if y > 0 and (i := module.instances.get( ((x, y), Corner.southeast) )): yield i
                        if i := module.instances.get( ((x, y), Corner.northeast) ): yield i
                else:
                    for y in reversed(range(subarray_height)):
                        if i := module.instances.get( ((x, y), Corner.northwest) ): yield i
                        if y > 0 and (i := module.instances.get( ((x, y), Corner.southwest) )): yield i
                    for y in range(subarray_height):
                        if i := module.instances.get( (x, y) ): yield i
                    for y in reversed(range(subarray_height)):
                        if i := module.instances.get( ((x, y), Corner.northeast) ): yield i
                        if y > 0 and (i := module.instances.get( ((x, y), Corner.southeast) )): yield i
            for x in reversed(range(subarray_width)):
                if i := module.instances.get( ((x, 0), Corner.southeast) ): yield i
                if i := module.instances.get( ((x, 0), Corner.southwest) ): yield i
        elif module.name == "prga_io_region":
            for y in range(subarray_height):
                yield module.instances[0, y]
            for y in reversed(range(subarray_height)):
                if i := module.instances.get( ((0, y), Corner.northeast) ): yield i
                if i := module.instances.get( ((0, y), Corner.southeast) ): yield i
        elif module.name == "prga_edge_region_n":
            for x in range(subarray_width):
                yield module.instances[(x, 0), Corner.southeast]
            for x in reversed(range(subarray_width)):
                yield module.instances[(x, 0), Corner.southwest]
        elif module.name == "prga_edge_region_s":
            for x in range(subarray_width):
                yield module.instances[(x, 0), Corner.northeast]
            for x in reversed(range(subarray_width)):
                yield module.instances[(x, 0), Corner.northwest]
        elif module.name == "prga_edge_region_e":
            for y in range(subarray_height):
                yield module.instances[(0, y), Corner.northwest]
            for y in reversed(range(subarray_height)):
                yield module.instances[(0, y), Corner.southwest]
        elif module.name == "prga_fabric":
            for x in range(top_width // 2 + 1):
                # lower half
                xx = 0 if x == 0 else ((2 * x - 1) * subarray_width + 1)
                for y in reversed(range(top_height // 2 + 1)):
                    yy = 0 if y == 0 else ((y - 1) * subarray_height + 1)
                    yield module.instances[xx, yy]
                xx = 1 if x == 0 else (xx + subarray_width)
                for y in range(top_height // 2 + 1):
                    yy = 0 if y == 0 else ((y - 1) * subarray_height + 1)
                    yield module.instances[xx, yy]
                yield None
                yield None
                # upper half
                for y in range(top_height // 2 + 1, top_height + 2):
                    yy = (y - 1) * subarray_height + 1
                    yield module.instances[xx, yy]
                xx = 0 if x == 0 else (xx - subarray_width)
                for y in reversed(range(top_height // 2 + 1, top_height + 2)):
                    yy = (y - 1) * subarray_height + 1
                    yield module.instances[xx, yy]
                yield None
                yield None
        else:
            for i in module.instances.values():
                yield i
    
    flow = Flow(
        TranslationPass(),
        Pktchain.InjectConfigCircuitry(iter_instances = iter_instances),
        VPRArchGeneration("vpr/arch.xml"),
        VPR_RRG_Generation("vpr/rrg.xml"),
        VerilogCollection('rtl'),
        YosysScriptsCollection("syn"),
        )
    flow.run(ctx, Pktchain.new_renderer())

    ctx.pickle("ctx.tmp.pkl")

Flow(Pktchain.BuildSystem("constraints/io.pads"),
        VerilogCollection("rtl")).run(ctx, Pktchain.new_renderer())

ctx.pickle(sys.argv[1])
