from prga import *

from prga.netlist.net.util import NetUtils
from itertools import product
import sys

ctx = Scanchain.new_context(1)
gbl_clk = ctx.create_global("clk", is_clock = True)
gbl_clk.bind((0, 1), 0)
l1 = ctx.create_segment('L1', 12, 1)
l2 = ctx.create_segment('L4', 3, 4)

mux8to1 = ctx.build_primitive("mux8to1")
sel= mux8to1.create_input("sel",4)
data_in= mux8to1.create_input("data_in",8)
out = mux8to1.create_output("out",1)
NetUtils.connect([sel,data_in],out,fully = True)
mux8to1= mux8to1.build_logical_counterpart(verilog_template = "mux8to1.v").commit()

builder = ctx.build_cluster("cluster")
clk = builder.create_clock("clk")
i = builder.create_input("i", 4)
o = builder.create_output("o", 1)
lut = builder.instantiate(ctx.primitives["lut4"], "lut")
ff = builder.instantiate(ctx.primitives["flipflop"], "ff")
builder.connect(clk, ff.pins['clk'])
builder.connect(i, lut.pins['in'])
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

builder = ctx.build_logic_block("dsp", 1,2)
inst = builder.instantiate(ctx.primitives["mux8to1"],"dsp_inst")
for port in ("sel","data_in"):
	 builder.connect(builder.create_input(port, len(inst.pins[port]), Orientation.west, (0, 0)), inst.pins[port])
builder.connect(inst.pins["out"], builder.create_output("out", len(inst.pins["out"]),  Orientation.east, (0, 0)))
dsp = builder.commit()

builder = ctx.build_logic_block("clb")
clk = builder.create_global(gbl_clk, Orientation.south)
for i, inst in enumerate(builder.instantiate(cluster, "cluster", 1)):
    builder.connect(clk, inst.pins['clk'])
    builder.connect(builder.create_input("i{}".format(i), 4, Orientation.west), inst.pins['i'])
    builder.connect(inst.pins['o'], builder.create_output("o{}".format(i), 1, Orientation.east))
clb = builder.commit()

clbtile = ctx.build_tile(clb).fill( (0.25, 0.15) ).auto_connect().commit()
dsptile = ctx.build_tile(dsp).fill( (0.25, 0.15) ).auto_connect().commit()

iotiles = {}
for ori in Orientation:
    builder = ctx.build_tile(iob, 4, name = "t_io_{}".format(ori.name[0]),
            edge = OrientationTuple(False, **{ori.name: True}))
    iotiles[ori] = builder.fill( (1., 1.) ).auto_connect().commit()

builder = ctx.build_array('subarray', 4, 4, set_as_top = False)
for x, y in product(range(4), range(4)):
    if x == 2:
        if y % 2 == 0:
            builder.instantiate(dsptile, (x, y))
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
top = builder.fill(SwitchBoxPattern.cycle_free).auto_connect().commit()



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
