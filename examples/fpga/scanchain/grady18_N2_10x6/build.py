from prga import *
from itertools import product

import sys

ctx = Scanchain.new_context(2)
gbl_clk = ctx.create_global("clk", is_clock = True)
gbl_clk.bind((0, 1), 0)
ctx.create_segment('L1', 20, 1)

builder = ctx.build_io_block("iob")
o = builder.create_input("outpad", 1)
i = builder.create_output("inpad", 1)
builder.connect(builder.instances['io'].pins['inpad'], i)
builder.connect(o, builder.instances['io'].pins['outpad'])
iob = builder.commit()

builder = ctx.build_logic_block("clb")
clk = builder.create_global(gbl_clk, Orientation.south)
in_ = builder.create_input("in", 16, Orientation.west)
out = builder.create_output("out", 8, Orientation.east)
cin = builder.create_input("cin", 1, Orientation.south)
for i, inst in enumerate(builder.instantiate(ctx.primitives["grady18"], "i_grady18", 2)):
    builder.connect(clk, inst.pins['clk'])
    builder.connect(in_[8 * i: 8 * (i + 1)], inst.pins['in'])
    builder.connect(inst.pins["cout_fabric"], out[4 * i + 2: 4 * i + 4])
    builder.connect(inst.pins['out'], out[4 * i: 4 * i + 2])
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

builder = ctx.build_array('top', 10, 6, set_as_top = True)
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
    else:
        builder.instantiate(clbtile, (x, y))
top = builder.fill( SwitchBoxPattern.cycle_free ).auto_connect().commit()

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
