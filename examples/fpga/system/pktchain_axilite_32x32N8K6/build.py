from prga.compatible import *
from prga.core.common import *
from prga.core.context import *
from prga.passes.translation import *
from prga.passes.vpr import *
from prga.passes.rtl import *
from prga.passes.yosys import *
from prga.cfg.pktchain.lib import Pktchain
from prga.cfg.pktchain.system import PktchainSystem
from prga.netlist.module.module import Module
from prga.netlist.module.util import ModuleUtils
from prga.netlist.net.util import NetUtils
from prga.util import enable_stdout_logging

from itertools import product, chain
import os, logging
enable_stdout_logging("prga", logging.DEBUG)

K, N = 6, 8
maw, mdw = 10, 32
subarray_width, subarray_height = 4, 4  # must be even
top_width, top_height = 8, 8            # must be even
memcol_idx = (2, )

try:
    f = open("ctx.tmp.pkl", "rb")
    ctx = Context.unpickle(f)

    # patches
    if "i_clkdiv" not in ctx._database[ModuleView.logical, "pktchain_axilite_intf"].instances:
        clkdiv = ctx._database[ModuleView.logical, "prga_clkdiv"] = Module("prga_clkdiv",
                view = ModuleView.logical,
                verilog_template = "cdclib/prga_clkdiv.v")
        ModuleUtils.instantiate(ctx._database[ModuleView.logical, "pktchain_axilite_intf"],
                clkdiv, "i_clkdiv")
except FileNotFoundError:
    ctx = Pktchain.new_context(phit_width = 32, cfg_width = 1)
    
    # ============================================================================
    # -- Routing Resources -------------------------------------------------------
    # ============================================================================
    gbl_clk = ctx.create_global("clk", is_clock = True)
    gbl_clk.bind((0, 16), 0)
    l1a = ctx.create_segment('L1A', 20, 1)
    l4a = ctx.create_segment('L4A', 10, 4)
    l1b = ctx.create_segment('L1B', 20, 1)
    l4b = ctx.create_segment('L4B', 10, 4)
    
    # ============================================================================
    # -- Primitives --------------------------------------------------------------
    # ============================================================================
    memory = ctx.create_memory("prga_RAM", maw, mdw).commit()
    
    # ============================================================================
    # -- Blocks ------------------------------------------------------------------
    # ============================================================================
    # -- IOB ---------------------------------------------------------------------
    builder = ctx.create_io_block("prga_iob", 16)
    o = builder.create_input("outpad", 1)
    i = builder.create_output("inpad", 1)
    builder.connect(builder.instances['io'].pins['inpad'], i)
    builder.connect(o, builder.instances['io'].pins['outpad'])
    iob = builder.commit()
    
    # -- CLB ---------------------------------------------------------------------
    builder = ctx.create_logic_block("prga_clb")
    clk = builder.create_global(gbl_clk, Orientation.south)
    in_ = builder.create_input("in", N * 6 // 2, Orientation.west)
    out = builder.create_output("out", N * 2, Orientation.east)
    cin = builder.create_input("cin", 1, Orientation.south)
    xbar_i, xbar_o = [in_], []
    for i, inst in enumerate(builder.instantiate(ctx.primitives["fle6"], "i_cluster", vpr_num_pb = N)):
        builder.connect(clk, inst.pins['clk'])
        # builder.connect(in_[6 * i: 6 * (i + 1)], inst.pins["in"])
        builder.connect(inst.pins['out'], out[2 * i: 2 * (i + 1)])
        builder.connect(cin, inst.pins["cin"], pack_patterns = ["carrychain"])
        xbar_i.append(inst.pins["out"])
        xbar_o.append(inst.pins["in"])
        cin = inst.pins["cout"]
    builder.connect(cin, builder.create_output("cout", 1, Orientation.north), pack_patterns = ["carrychain"])
    # crossbar
    builder.connect(xbar_i, xbar_o, fully = True)
    clb = builder.commit()
    
    ctx.create_tunnel("carrychain", clb.ports["cout"], clb.ports["cin"], (0, -1))
    
    # -- BRAM --------------------------------------------------------------------
    builder = ctx.create_logic_block("prga_bram", 1, subarray_height)
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
    pattern = SwitchBoxPattern.cycle_free
    
    # -- CLB Subarray ------------------------------------------------------------
    builder = ctx.create_array("prga_logictile", subarray_width, subarray_height, set_as_top = False)
    for x, y in product(range(builder.width), range(builder.height)):
        builder.instantiate(clb, (x, y))
    builder.fill( (0.25, 0.15), segments = (l4a, l1a, l4b, l1b), sbox_pattern = pattern )
    logictile = builder.commit()
    
    # -- RAM Subarray ------------------------------------------------------------
    builder = ctx.create_array("prga_memtile", subarray_width, subarray_height, set_as_top = False)
    for x, y in product(range(builder.width), range(builder.height)):
        if x == builder.width // 2:
            if y == 0:
                builder.instantiate(bram, (x, y))
        else:
            builder.instantiate(clb, (x, y))
    builder.fill( (0.25, 0.15), segments = (l4a, l1a, l4b, l1b), sbox_pattern = pattern )
    memtile = builder.commit()
    
    # -- IOs ---------------------------------------------------------------------
    builder = ctx.create_array("prga_iotile", 1, subarray_height,
            set_as_top = False, edge = OrientationTuple(False, west = True))
    for x, y in product(range(builder.width), range(builder.height)):
        builder.instantiate(iob, (x, y))
    builder.fill( (0.5, 0.5), sbox_pattern = pattern )
    iotile = builder.commit()
    
    # -- Edge Fillers ------------------------------------------------------------
    edgetiles = {}
    for ori in Orientation:
        if ori.is_west:
            continue
        builder = ctx.create_array("prga_edgetile_{}".format(ori.name[0]),
                1 if ori.dimension.is_x else subarray_width,
                1 if ori.dimension.is_y else subarray_height,
                set_as_top = False, edge = OrientationTuple(False, **{ori.name: True}))
        builder.fill( (0.5, 0.5), sbox_pattern = pattern )
        edgetiles[ori] = builder.commit()
    
    # -- Corner Fillers ----------------------------------------------------------
    cornertiles = {}
    for corner in Corner:
        builder = ctx.create_array("prga_cornertile_{}".format(corner.case("ne", "nw", "se", "sw")), 1, 1,
                set_as_top = False, edge = OrientationTuple(False, **{ori.name: True for ori in corner.decompose()}))
        builder.fill( (0.5, 0.5), sbox_pattern = pattern )
        cornertiles[corner] = builder.commit()
    
    # ============================================================================
    # -- Fabric ------------------------------------------------------------------
    # ============================================================================
    builder = ctx.create_array("prga_fabric", top_width * subarray_width + 2, top_height * subarray_height + 2,
            hierarchical = True, set_as_top = True)
    for x, y in product(range(builder.width), range(builder.height)):
        if x == 0:
            if y == 0:
                builder.instantiate(cornertiles[Corner.southwest], (x, y))
            elif y == top_height * subarray_height + 1:
                builder.instantiate(cornertiles[Corner.northwest], (x, y))
            elif y % subarray_height == 1:
                builder.instantiate(iotile, (x, y))
        elif x == top_width * subarray_width + 1:
            if y == 0:
                builder.instantiate(cornertiles[Corner.southeast], (x, y))
            elif y == top_height * subarray_height + 1:
                builder.instantiate(cornertiles[Corner.northeast], (x, y))
            elif y % subarray_height == 1:
                builder.instantiate(edgetiles[Orientation.east], (x, y))
        elif x % subarray_width == 1:
            if y == 0:
                builder.instantiate(edgetiles[Orientation.south], (x, y))
            elif y == top_height * subarray_height + 1:
                builder.instantiate(edgetiles[Orientation.north], (x, y))
            elif y % subarray_height == 1:
                if (x - 1) // subarray_width in memcol_idx:
                    builder.instantiate(memtile, (x, y))
                else:
                    builder.instantiate(logictile, (x, y))
    builder.auto_connect()
    fabric = builder.commit()
    
    # ============================================================================
    # -- Translation -------------------------------------------------------------
    # ============================================================================
    TranslationPass().run(ctx)
    
    # ============================================================================
    # -- Configuration Chain Injection -------------------------------------------
    # ============================================================================
    def iter_instances(module):
        if module.name in ("prga_logictile", "prga_memtile"):
            for x in range(subarray_width):
                if x % 2 == 0:
                    for y in range(subarray_height):
                        if y > 0 and (i := module.instances.get( ((x, y), Subtile.southwest), None )): yield i
                        if i := module.instances.get( ((x, y), Subtile.west), None ): yield i
                        if i := module.instances.get( ((x, y), Subtile.northwest), None ): yield i
                    for y in reversed(range(subarray_height)):
                        if i := module.instances.get( ((x, y), Subtile.north), None ): yield i
                        if i := module.instances.get( ((x, y), Subtile.center), None ): yield i
                        if y > 0 and (i := module.instances.get( ((x, y), Subtile.south), None )): yield i
                    for y in range(subarray_height):
                        if y > 0 and (i := module.instances.get( ((x, y), Subtile.southeast), None )): yield i
                        if i := module.instances.get( ((x, y), Subtile.east), None ): yield i
                        if i := module.instances.get( ((x, y), Subtile.northeast), None ): yield i
                else:
                    for y in reversed(range(subarray_height)):
                        if i := module.instances.get( ((x, y), Subtile.northwest), None ): yield i
                        if i := module.instances.get( ((x, y), Subtile.west), None ): yield i
                        if y > 0 and (i := module.instances.get( ((x, y), Subtile.southwest), None )): yield i
                    for y in range(subarray_height):
                        if y > 0 and (i := module.instances.get( ((x, y), Subtile.south), None )): yield i
                        if i := module.instances.get( ((x, y), Subtile.center), None ): yield i
                        if i := module.instances.get( ((x, y), Subtile.north), None ): yield i
                    for y in reversed(range(subarray_height)):
                        if i := module.instances.get( ((x, y), Subtile.northeast), None ): yield i
                        if i := module.instances.get( ((x, y), Subtile.east), None ): yield i
                        if y > 0 and (i := module.instances.get( ((x, y), Subtile.southeast), None )): yield i
            for x in reversed(range(subarray_width)):
                if i := module.instances.get( ((x, 0), Subtile.southeast), None ): yield i
                if i := module.instances.get( ((x, 0), Subtile.south), None ): yield i
                if i := module.instances.get( ((x, 0), Subtile.southwest), None ): yield i
        elif module.name == "prga_iotile":
            for y in range(subarray_height):
                for i in range(iob.capacity):
                    yield module.instances[(0, y), i]
            for y in reversed(range(subarray_height)):
                if i := module.instances.get( ((0, y), Subtile.northeast), None ): yield i
                if i := module.instances.get( ((0, y), Subtile.east), None ): yield i
                if i := module.instances.get( ((0, y), Subtile.southeast), None ): yield i
        elif module.name == "prga_edgetile_n":
            for x in range(subarray_width):
                yield module.instances[(x, 0), Subtile.southeast]
            for x in reversed(range(subarray_width)):
                yield module.instances[(x, 0), Subtile.southwest]
        elif module.name == "prga_edgetile_s":
            for x in range(subarray_width):
                yield module.instances[(x, 0), Subtile.northeast]
            for x in reversed(range(subarray_width)):
                yield module.instances[(x, 0), Subtile.northwest]
        elif module.name == "prga_edgetile_e":
            for y in range(subarray_height):
                yield module.instances[(0, y), Subtile.northwest]
            for y in reversed(range(subarray_height)):
                yield module.instances[(0, y), Subtile.southwest]
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
                # upper half
                for y in range(top_height // 2 + 1, top_height + 2):
                    yy = (y - 1) * subarray_height + 1
                    yield module.instances[xx, yy]
                xx = 0 if x == 0 else (xx - subarray_width)
                for y in reversed(range(top_height // 2 + 1, top_height + 2)):
                    yy = (y - 1) * subarray_height + 1
                    yield module.instances[xx, yy]
                yield None
        else:
            for i in itervalues(module.instances):
                yield i
    
    Pktchain.complete_pktchain(ctx, iter_instances = iter_instances)
    Pktchain.annotate_user_view(ctx)

    VPRArchGeneration('vpr/arch.xml').run(ctx)
    VPR_RRG_Generation("vpr/rrg.xml").run(ctx)
    
    ctx.pickle("ctx.tmp.pkl")

PktchainSystem.build_system_axilite(ctx, name = "prga_system",
        io_start_pos = (0, 16), io_start_subblock = 1, io_scan_direction = Orientation.south)

r = Pktchain.new_renderer()

p = VerilogCollection(r, "rtl")
p.run(ctx)
YosysScriptsCollection(r, "syn").run(ctx)

PktchainSystem.generate_axilite_io_assignment_constraint(ctx, r, "constraints/io.a8d4.pads")

p._process_module(Pktchain._build_pktchain_backbone(ctx, 2, 2))

r.render()

ctx.pickle("ctx.pkl")
