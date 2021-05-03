from prga import *
from itertools import product

import sys

ctx = Context()
gbl_clk = ctx.create_global("clk", is_clock = True)
gbl_clk.bind((0, 1), 0)
ctx.create_segment('L2', 20, 2)

memory = ctx.create_memory(8, 8)

builder = ctx.build_logic_block("clb")
clk = builder.create_global(gbl_clk, Orientation.south)
in_ = builder.create_input("in", 12, Orientation.west)
out = builder.create_output("out", 4, Orientation.east)
cin = builder.create_input("cin", 1, Orientation.south)
for i, inst in enumerate(builder.instantiate(ctx.primitives["fle6"], "i_cluster", 2)):
    builder.connect(clk, inst.pins['clk'])
    builder.connect(in_[6 * i: 6 * (i + 1)], inst.pins['in'])
    builder.connect(inst.pins['out'], out[2 * i: 2 * (i + 1)])
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
inst = builder.instantiate(memory, "i_ram")
builder.connect(builder.create_global(gbl_clk, Orientation.south), inst.pins["clk"])
builder.connect(builder.create_input("we", 1, Orientation.west, (0, 0)), inst.pins["we"])
builder.connect(builder.create_input("waddr", len(inst.pins["waddr"]), Orientation.west, (0, 0)), inst.pins["waddr"])
builder.connect(builder.create_input("din", len(inst.pins["din"]), Orientation.east, (0, 0)), inst.pins["din"])
builder.connect(builder.create_input("raddr", len(inst.pins["raddr"]), Orientation.west, (0, 1)), inst.pins["raddr"])
builder.connect(inst.pins["dout"], builder.create_output("dout", len(inst.pins["dout"]), Orientation.east, (0, 1)))
# for port in ("addr1", "we1", "data1"):
#     builder.connect(builder.create_input(port, len(inst.pins[port]), Orientation.west, (0, 0)), inst.pins[port])
# for port in ("addr2", "we2", "data2"):
#     builder.connect(builder.create_input(port, len(inst.pins[port]), Orientation.west, (0, 1)), inst.pins[port])
# builder.connect(inst.pins["out1"], builder.create_output("out1", len(inst.pins["out1"]), Orientation.east, (0, 0)))
# builder.connect(inst.pins["out2"], builder.create_output("out2", len(inst.pins["out2"]), Orientation.east, (0, 1)))
bram = builder.commit()

ctx.create_tunnel("carrychain", clb.ports["cout"], clb.ports["cin"], (0, -1))

iotiles = {}
for ori in Orientation:
    builder = ctx.build_tile(iob, 4, name = "t_io_{}".format(ori.name[0]),
            edge = OrientationTuple(False, **{ori.name: True}))
    iotiles[ori] = builder.fill( (1., 1.) ).auto_connect().commit()

clbtile = ctx.build_tile(clb).fill( (0.4, 0.25) ).auto_connect().commit()
bramtile = ctx.build_tile(bram).fill( (0.4, 0.25) ).auto_connect().commit()

pattern = SwitchBoxPattern.wilton

builder = ctx.build_array('subarray', 4,     4,     set_as_top = False)
for x, y in product(range(builder.width), range(builder.height)):
    if x == 2:
        if y % 2 == 0:
            builder.instantiate(bramtile, (x, y))
    else:
        builder.instantiate(clbtile, (x, y))
subarray = builder.fill( pattern ).auto_connect().commit()

builder = ctx.build_array('top', 10, 10, set_as_top = True)
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
    elif x % 4 == 1 and y % 4 == 1:
        builder.instantiate(subarray, (x, y))
top = builder.fill( pattern ).auto_connect().commit()

Flow(
        VPRArchGeneration('vpr/arch.xml'),
        VPR_RRG_Generation('vpr/rrg.xml'),
        YosysScriptsCollection('syn'),
        Materialization('scanchain', chain_width = 1),
        Translation(),
        SwitchPathAnnotation(),
        ProgCircuitryInsertion(),
        VerilogCollection('rtl'),
        ).run(ctx)

ctx.pickle("ctx.pkl" if len(sys.argv) < 2 else sys.argv[1])
