from prga import *
# from prga.passes.test import Tester
from itertools import product
import sys
from prga.compatible import *
from prga.netlist.net.util import NetUtils
from itertools import chain

ctx = Scanchain.new_context(1)
gbl_clk = ctx.create_global("clk", is_clock = True)
gbl_clk.bind((0, 1), 0)
l1 = ctx.create_segment('L1', 12, 1)
l2 = ctx.create_segment('L4', 3, 4)

builder = ctx.build_cluster("cluster")
clk = builder.create_clock("clk")
i = builder.create_input("i", 4)
o = builder.create_output("o", 1)
lut = builder.instantiate(ctx.primitives["lut4"], "lut")
ff = builder.instantiate(ctx.primitives["flipflop"], "ff")
builder.connect(clk, ff.pins['clk'])
builder.connect(i, lut.pins['bits_in'])
builder.connect(lut.pins['out'], o)
builder.connect(lut.pins['out'], ff.pins['D'], vpr_pack_patterns = ('lut_dff', ))
builder.connect(ff.pins['Q'], o)
cluster = builder.commit()

builder = ctx.build_io_block("iob")
o = builder.create_input("outpad", 1)
i = builder.create_output("inpad", 1)
builder.connect(builder.instances['io'].pins['inpad'], i)
builder.connect(o, builder.instances['io'].pins['outpad'])
iob = builder.commit()

builder = ctx.build_logic_block("clb")
clk = builder.create_global(gbl_clk, Orientation.south)
for i, inst in enumerate(builder.instantiate(cluster, "cluster", 2)):
    builder.connect(clk, inst.pins['clk'])
    builder.connect(builder.create_input("i{}".format(i), 4, Orientation.west), inst.pins['i'])
    builder.connect(inst.pins['o'], builder.create_output("o{}".format(i), 1, Orientation.east))
clb = builder.commit()

clbtile = ctx.build_tile(clb).fill( (0.4, 0.25) ).auto_connect().commit()

iotiles = {}
for ori in Orientation:
    builder = ctx.build_tile(iob, 4, name = "t_io_{}".format(ori.name[0]),
            edge = OrientationTuple(False, **{ori.name: True}))
    iotiles[ori] = builder.fill( (1., 1.) ).auto_connect().commit()

builder = ctx.build_array('subarray', 1, 1, set_as_top = False)
for pos in product(range(1), range(1)):
    builder.instantiate(clbtile, pos)
subarray = builder.fill(SwitchBoxPattern.cycle_free).auto_connect().commit()

width, height = 8, 8
builder = ctx.build_array('top', width, height, set_as_top = True)
for x, y in product(range(width), range(height)):
    if x in (0, width - 1) and y in (0, height - 1):
        pass
    elif (x in (0, width - 1) and 0 < y < height - 1) or (y in (0, height - 1) and 0 < x < width - 1):
        builder.instantiate(iotiles[Orientation.west if x == 0 else
            Orientation.east if x == width - 1 else Orientation.south if y == 0 else Orientation.north], (x, y))
    elif 0 < x < width - 1 and 0 < y < height - 1:
        builder.instantiate(subarray, (x, y))
top = builder.fill( SwitchBoxPattern.cycle_free ).auto_connect().commit()


flow = Flow(
        TranslationPass(),
        Scanchain.InjectConfigCircuitry(),
        VPRArchGeneration('vpr/arch.xml'),
        VPR_RRG_Generation('vpr/rrg.xml'),
        VerilogCollection('rtl'),
        YosysScriptsCollection('syn'),
        # Tester('rtl','unit_tests')
        )
flow.run(ctx, Scanchain.new_renderer())

ctx.pickle(sys.argv[1])
