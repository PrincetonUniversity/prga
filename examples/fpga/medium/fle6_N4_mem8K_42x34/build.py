from prga import *

from itertools import product
import sys

N = 6
subarray_width, subarray_height = 8, 8
subarray_col, subarray_row = 5, 4

ctx = Scanchain.new_context(1)

gbl_clk = ctx.create_global("clk", is_clock = True)
gbl_clk.bind((0, 1), 0)
l1a = ctx.create_segment('L1', 40, 1)
l4a = ctx.create_segment('L4', 20, 4)

memory = ctx.build_memory("dpram_a10d8", 10, 8).commit()

builder = ctx.build_logic_block("clb")
clk = builder.create_global(gbl_clk, Orientation.south)
iw = builder.create_input("iw", N // 2 * 6, Orientation.west)
ie = builder.create_input("ie", N // 2 * 6, Orientation.east)
ow = builder.create_output("ow", N // 2 * 2, Orientation.west)
oe = builder.create_output("oe", N // 2 * 2, Orientation.east)
cin = builder.create_input("cin", 1, Orientation.south)
for i, inst in enumerate(builder.instantiate(ctx.primitives["fle6"], "cluster", N)):
    builder.connect(clk, inst.pins['clk'])
    if i % 2 == 0:
        i = i // 2
        builder.connect(iw[6 * i: 6 * (i + 1)], inst.pins["in"])
        builder.connect(inst.pins['out'], oe[2 * i: 2 * (i + 1)])
    else:
        i = i // 2
        builder.connect(ie[6 * i: 6 * (i + 1)], inst.pins["in"])
        builder.connect(inst.pins['out'], ow[2 * i: 2 * (i + 1)])
    builder.connect(cin, inst.pins["cin"], vpr_pack_patterns = ["carrychain"])
    cin = inst.pins["cout"]
builder.connect(cin, builder.create_output("cout", 1, Orientation.north), vpr_pack_patterns = ["carrychain"])
clb = builder.commit()

builder = ctx.build_io_block("iob")
o = builder.create_input("outpad", 1)
i = builder.create_output("inpad", 1)
builder.connect(builder.instances['io'].pins['inpad'], i)
builder.connect(o, builder.instances['io'].pins['outpad'])
iob = builder.commit()

builder = ctx.build_logic_block("bram", 1, 2)
inst = builder.instantiate(ctx.primitives["dpram_a10d8"], "bram_inst")
builder.connect(builder.create_global(gbl_clk, Orientation.south), inst.pins["clk"])
for port in ("addr1", "we1", "data1"):
    builder.connect(builder.create_input(port, len(inst.pins[port]), Orientation.west, (0, 0)), inst.pins[port])
for port in ("addr2", "we2", "data2"):
    builder.connect(builder.create_input(port, len(inst.pins[port]), Orientation.west, (0, 1)), inst.pins[port])
builder.connect(inst.pins["out1"], builder.create_output("out1", len(inst.pins["out1"]), Orientation.east, (0, 0)))
builder.connect(inst.pins["out2"], builder.create_output("out2", len(inst.pins["out2"]), Orientation.east, (0, 1)))
bram = builder.commit()

ctx.create_tunnel("carrychain", clb.ports["cout"], clb.ports["cin"], (0, -1))

iotiles = {ori: ctx.build_tile(iob, 8, name = "tile_io_{}".format(ori.name[0]),
        edge = OrientationTuple(False, **{ori.name: True})).fill( (1., 1.) ).auto_connect().commit()
        for ori in Orientation}
clbtile = ctx.build_tile(clb).fill( (0.4, 0.25) ).auto_connect().commit()
bramtile = ctx.build_tile(bram).fill( (0.4, 0.25) ).auto_connect().commit()

pattern = SwitchBoxPattern.wilton

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

flow = Flow(
    TranslationPass(),
    Scanchain.InjectConfigCircuitry(),
    VPRArchGeneration("vpr/arch.xml"),
    VPR_RRG_Generation("vpr/rrg.xml"),
    VerilogCollection('rtl'),
    YosysScriptsCollection("syn"),
    )
flow.run(ctx, Scanchain.new_renderer())

ctx.pickle(sys.argv[1] if len(sys.argv) > 1 else "ctx.pkl")
