from prga import *
from itertools import product

import sys

ctx = Scanchain.new_context(4)
gbl_clk = ctx.create_global("clk", is_clock = True)
gbl_clk.bind((0, 1), 0)
ctx.create_segment('L2', 20, 2)

builder = ctx.build_io_block("iob")
o = builder.create_input("outpad", 1)
i = builder.create_output("inpad", 1)
builder.connect(builder.instances['io'].pins['inpad'], i)
builder.connect(o, builder.instances['io'].pins['outpad'])
iob = builder.commit()

builder = ctx.build_logic_block("clb")
grady18v2 = ctx.primitives["grady18v2"]
N = 2

lin = len(grady18v2.ports["in"])
lout = len(grady18v2.ports["out"])

clk = builder.create_global(gbl_clk, Orientation.south)
ce = builder.create_input("ce", 1, Orientation.west)
in_ = builder.create_input("in", lin * N, Orientation.west)
out = builder.create_output("out", lout * N, Orientation.east)
cin = builder.create_input("cin", 1, Orientation.south)
for i, inst in enumerate(builder.instantiate(grady18v2, "i_grady18", N)):
    builder.connect(clk, inst.pins['clk'])
    builder.connect(ce, inst.pins['ce'])
    builder.connect(in_[lin * i: lin * (i + 1)], inst.pins['in'])
    builder.connect(inst.pins['out'], out[lout * i: lout * (i + 1)])
    builder.connect(cin, inst.pins["cin"], vpr_pack_patterns = ["carrychain"])
    cin = inst.pins["cout"]
builder.connect(cin, builder.create_output("cout", 1, Orientation.north), vpr_pack_patterns = ["carrychain"])
clb = builder.commit()

ctx.create_tunnel("carrychain", clb.ports["cout"], clb.ports["cin"], (0, -1))
clbtile = ctx.build_tile(clb).fill( (0.4, 0.25) ).auto_connect().commit()

iotiles = {}
for ori in Orientation:
    builder = ctx.build_tile(iob, 4, name = "t_io_{}".format(ori.name[0]),
            edge = OrientationTuple(False, **{ori.name: True}))
    iotiles[ori] = builder.fill( (1., 1.) ).auto_connect().commit()

builder = ctx.build_array("subarray", 3, 3, set_as_top = False)
for x, y in product(range(builder.width), range(builder.height)):
    builder.instantiate(clbtile, (x, y))
pattern = SwitchBoxPattern.cycle_free(fill_corners = [Corner.northeast, Corner.southeast])
subarray = builder.fill( pattern ).auto_connect().commit()

builder = ctx.build_array('top', 8, 8, set_as_top = True)
for x, y in product(range(builder.width), range(builder.height)):
    if x in (0, builder.width - 1) and y in (0, builder.height - 1):
        pass
    elif x == 0:
        builder.instantiate(iotiles[Orientation.west], (x, y))
    elif x == builder.width - 1:
        builder.instantiate(iotiles[Orientation.east], (x, y))
    elif y == 0:
        builder.instantiate(iotiles[Orientation.south], (x, y))
    elif y == builder.height - 1:
        builder.instantiate(iotiles[Orientation.north], (x, y))
    elif x % 3 == 1 and y % 3 == 1:
        builder.instantiate(subarray, (x, y))
top = builder.fill( pattern ).auto_connect().commit()

Flow(
        Translation(),
        SwitchPathAnnotation(),
        Scanchain.InsertProgCircuitry(),
        VPRArchGeneration('vpr/arch.xml'),
        VPR_RRG_Generation('vpr/rrg.xml'),
        VerilogCollection('rtl'),
        YosysScriptsCollection('syn'),
        ).run(ctx, Scanchain.new_renderer())

ctx.pickle("ctx.pkl" if len(sys.argv) < 2 else sys.argv[1])
