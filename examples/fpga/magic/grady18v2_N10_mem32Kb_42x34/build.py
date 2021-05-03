from prga import *

from itertools import product
import sys
    
try:
    ctx = Context.unpickle("ctx.tmp.pkl")

except FileNotFoundError:
    N = 10
    subarray_width, subarray_height = 8, 8
    subarray_col, subarray_row = 5, 4
    mem_core_addr_width = 9     # 512
    mem_data_width = 64
    mem_addr_width = 12         # 4K8b
    
    ctx = Context()
    
    gbl_clk = ctx.create_global("clk", is_clock = True)
    gbl_clk.bind((0, 1), 0)
    l1 = ctx.create_segment('L1', 80, 1)
    l4 = ctx.create_segment('L4', 20, 4)
    
    builder = ctx.build_logic_block("clb")
    grady18v2 = ctx.primitives["grady18"]
    
    lin = len(grady18v2.ports["in"])
    lout = len(grady18v2.ports["out"])
    
    clk = builder.create_global(gbl_clk, Orientation.south)
    ce = builder.create_input("ce", 1, Orientation.west)
    in_ = builder.create_input("in", lin * N, Orientation.west)
    out = builder.create_output("out", lout * N, Orientation.east)
    cin = builder.create_input("cin", 1, Orientation.south)
    for i, inst in enumerate(builder.instantiate(grady18v2, "i_ble", N)):
        builder.connect(clk, inst.pins['clk'])
        builder.connect(ce, inst.pins['ce'])
        builder.connect(in_[lin * i: lin * (i + 1)], inst.pins['in'])
        builder.connect(inst.pins['out'], out[lout * i: lout * (i + 1)])
        builder.connect(cin, inst.pins["cin"], vpr_pack_patterns = ["carrychain"])
        cin = inst.pins["cout"]
    builder.connect(cin, builder.create_output("cout", 1, Orientation.north), vpr_pack_patterns = ["carrychain"])
    clb = builder.commit()
    
    ctx.create_tunnel("carrychain", clb.ports["cout"], clb.ports["cin"], (0, -1))
    
    builder = ctx.build_io_block("iob")
    o = builder.create_input("outpad", 1)
    i = builder.create_output("inpad", 1)
    builder.connect(builder.instances['io'].pins['inpad'], i)
    builder.connect(o, builder.instances['io'].pins['outpad'])
    iob = builder.commit()
    
    builder = ctx.build_logic_block("bram", 1, 2)
    inst = builder.instantiate(
            ctx.create_multimode_memory(
                mem_core_addr_width,
                mem_data_width,
                addr_width = mem_addr_width),
            "i_ram")
    builder.connect(builder.create_global(gbl_clk, Orientation.south), inst.pins["clk"])
    builder.connect(builder.create_input("we", 1, Orientation.west, (0, 0)), inst.pins["we"])
    builder.connect(builder.create_input("din", mem_data_width, Orientation.east, (0, 0)), inst.pins["din"])
    builder.connect(builder.create_input("waddr", mem_addr_width, Orientation.west, (0, 0)), inst.pins["waddr"])
    builder.connect(builder.create_input("raddr", mem_addr_width, Orientation.west, (0, 1)), inst.pins["raddr"])
    builder.connect(inst.pins["dout"], builder.create_output("dout", mem_data_width, Orientation.east, (0, 1)))
    bram = builder.commit()
    
    iotiles = {ori: ctx.build_tile(iob, 8, name = "tile_io_{}".format(ori.name[0]),
            edge = OrientationTuple(False, **{ori.name: True})).fill( (0.5, 0.5) ).auto_connect().commit()
            for ori in Orientation}
    clbtile = ctx.build_tile(clb).fill( (0.15, 0.25) ).auto_connect().commit()
    bramtile = ctx.build_tile(bram).fill( (0.15, 0.25) ).auto_connect().commit()
    
    pattern = SwitchBoxPattern.cycle_free
    
    builder = ctx.build_array('subarray', subarray_width, subarray_height, set_as_top = False)
    for x, y in product(range(builder.width), range(builder.height)):
        if x == 6:
            if y % 2 == 0:
                builder.instantiate(bramtile, (x, y))
        else:
            builder.instantiate(clbtile, (x, y))
    subarray = builder.fill( pattern ).auto_connect().commit()
    
    top_width = subarray_width * subarray_col + 2
    top_height = subarray_height * subarray_row + 2
    builder = ctx.build_array('top', top_width, top_height, set_as_top = True)
    for x, y in product(range(top_width), range(top_height)):
        if x in (0, top_width - 1) and y in (0, top_height - 1):
            pass
        elif (x in (0, top_width - 1) and 0 < y < top_height - 1) or (y in (0, top_height - 1) and 0 < x < top_width - 1):
            builder.instantiate(iotiles[Orientation.west if x == 0 else
                Orientation.east if x == top_width - 1 else Orientation.south if y == 0 else Orientation.north], (x, y))
        elif 0 < x < top_width - 1 and 0 < y < top_height - 1 and x % subarray_width == 1 and y % subarray_height == 1:
            builder.instantiate(subarray, (x, y))
    top = builder.fill( pattern ).auto_connect().commit()
    
    Flow(
            VPRArchGeneration("vpr/arch.xml"),
            VPR_RRG_Generation("vpr/rrg.xml"),
            YosysScriptsCollection("syn"),
            ).run(ctx)

    ctx.pickle("ctx.tmp.pkl")

Flow(
        Materialization('magic'),
        Translation(),
        SwitchPathAnnotation(),
        ProgCircuitryInsertion(),
        VerilogCollection('rtl'),
        ).run(ctx)

ctx.pickle(sys.argv[1] if len(sys.argv) > 1 else "ctx.pkl")
