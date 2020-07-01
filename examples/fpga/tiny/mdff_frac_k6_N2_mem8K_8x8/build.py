from prga import *

from itertools import product
import sys

ctx = Scanchain.new_context(1)
gbl_clk = ctx.create_global("clk", is_clock = True)
gbl_clk.bind((0, 1), 0)
l1 = ctx.create_segment('L1', 16, 1)
l2 = ctx.create_segment('L4', 16, 4)

memory = ctx.build_memory("dpram_a10d8", 10, 8).commit()

builder = ctx.build_cluster("cluster")
o = builder.create_output("o", 2)
lut = builder.instantiate(ctx.primitives["fraclut6"], "lut")
ff = builder.instantiate(ctx.primitives["mdff"], "ff")
builder.connect(builder.create_clock("clk"), ff.pins['clk'])
builder.connect(builder.create_input("ce", 1), ff.pins["ce"])
builder.connect(builder.create_input("sr", 1), ff.pins["sr"])
builder.connect(builder.create_input("i", 6), lut.pins['in'])
builder.connect(lut.pins['o5'], o[1])
builder.connect(lut.pins['o6'], o[0])
builder.connect(lut.pins['o6'], ff.pins['D'], vpr_pack_patterns = ('lut6_dff', 'lut5A_dff'))
builder.connect(ff.pins['Q'], o[0])
cluster = builder.commit()

builder = ctx.build_io_block("iob")
o = builder.create_input("outpad", 1)
i = builder.create_output("inpad", 1)
builder.connect(builder.instances['io'].pins['inpad'], i)
builder.connect(o, builder.instances['io'].pins['outpad'])
iob = builder.commit()

builder = ctx.build_logic_block("clb")
clk = builder.create_global(gbl_clk, Orientation.south)
ce = builder.create_input("ce", 1, Orientation.south)
sr = builder.create_input("sr", 1, Orientation.south)
for i, inst in enumerate(builder.instantiate(cluster, "cluster", 2)):
    builder.connect(clk, inst.pins['clk'])
    builder.connect(ce, inst.pins['ce'])
    builder.connect(sr, inst.pins['sr'])
    builder.connect(builder.create_input("i{}".format(i), 6, Orientation.west), inst.pins['i'])
    builder.connect(inst.pins['o'], builder.create_output("o{}".format(i), 2, Orientation.east))
clb = builder.commit()

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

iotiles = {ori: ctx.build_tile(iob, 4, name = "tile_io_{}".format(ori.name[0]),
        edge = OrientationTuple(False, **{ori.name: True})).fill( (1., 1.) ).auto_connect().commit()
        for ori in Orientation}
clbtile = ctx.build_tile(clb).fill( (0.4, 0.25) ).auto_connect().commit()
bramtile = ctx.build_tile(bram).fill( (0.4, 0.25) ).auto_connect().commit()

builder = ctx.build_array('subarray', 4, 4, set_as_top = False)
for x, y in product(range(4), range(4)):
    if x == 2:
        if y % 2 == 0:
            builder.instantiate(bramtile, (x, y))
    else:
        builder.instantiate(clbtile, (x, y))
subarray = builder.fill( SwitchBoxPattern.cycle_free ).auto_connect().commit()

width, height = 10, 10
builder = ctx.build_array('top', width, height, set_as_top = True)
for x, y in product(range(width), range(height)):
    if x in (0, width - 1) and y in (0, height - 1):
        pass
    elif (x in (0, width - 1) and 0 < y < height - 1) or (y in (0, width - 1) and 0 < x < height - 1):
        builder.instantiate(iotiles[Orientation.west if x == 0 else
            Orientation.east if x == width - 1 else Orientation.south if y == 0 else Orientation.north], (x, y))
    elif 0 < x < width - 1 and 0 < y < height - 1 and x % 4 == 1 and y % 4 == 1:
        builder.instantiate(subarray, (x, y))
top = builder.fill( SwitchBoxPattern.cycle_free ).auto_connect().commit()

flow = Flow(
        TranslationPass(),
        Scanchain.InjectConfigCircuitry(),
        VPRArchGeneration('vpr/arch.xml'),
        VPR_RRG_Generation('vpr/rrg.xml'),
        VerilogCollection('rtl'),
        YosysScriptsCollection('syn'),
        )
flow.run(ctx, Scanchain.new_renderer())

ctx.pickle(sys.argv[1])
