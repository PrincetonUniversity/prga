from prga.compatible import *
from prga.core.common import *
from prga.passes.translation import *
from prga.passes.vpr import *
from prga.passes.rtl import *
from prga.passes.yosys import *
from prga.cfg.scanchain.lib import Scanchain
from prga.netlist.module.util import ModuleUtils
from prga.netlist.net.util import NetUtils
from prga.util import enable_stdout_logging

from itertools import product
import logging, sys

# enable_stdout_logging("prga", logging.INFO)

ctx = Scanchain.new_context(1)
gbl_clk = ctx.create_global("clk", is_clock = True)
gbl_clk.bind((0, 1), 0)
l1 = ctx.create_segment('L1', 12, 1)
l2 = ctx.create_segment('L4', 3, 4)

builder = ctx.create_cluster("cluster")
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

builder = ctx.create_io_block("iob", 4)
o = builder.create_input("outpad", 1)
i = builder.create_output("inpad", 1)
builder.connect(builder.instances['io'].pins['inpad'], i)
builder.connect(o, builder.instances['io'].pins['outpad'])
iob = builder.commit()

iotiles = {}
for ori in Orientation:
    builder = ctx.create_array('iotile_{}'.format(ori.name), 1, 1,
            set_as_top = False, edge = OrientationTuple(False, **{ori.name: True}))
    builder.instantiate(iob, (0, 0))
    builder.fill( (0.5, 0.5), sbox_pattern = SwitchBoxPattern.cycle_free)
    iotiles[ori] = builder.commit()

builder = ctx.create_logic_block("clb")
clk = builder.create_global(gbl_clk, Orientation.south)
for i, inst in enumerate(builder.instantiate(cluster, "cluster", 2)):
    builder.connect(clk, inst.pins['clk'])
    builder.connect(builder.create_input("i{}".format(i), 4, Orientation.west), inst.pins['i'])
    builder.connect(inst.pins['o'], builder.create_output("o{}".format(i), 1, Orientation.east))
clb = builder.commit()

builder = ctx.create_array('subarray', 1, 1, set_as_top = False)
for pos in product(range(1), range(1)):
    builder.instantiate(clb, pos)
builder.fill( (0.4, 0.25), sbox_pattern = SwitchBoxPattern.cycle_free)
subarray = builder.commit()

cornertiles = {}
for corner in Corner:
    builder = ctx.create_array("cornertile_{}".format(corner.case("ne", "nw", "se", "sw")), 1, 1,
            set_as_top = False, edge = OrientationTuple(False, **{ori.name: True for ori in corner.decompose()}))
    builder.fill( (1., 1.), sbox_pattern = SwitchBoxPattern.cycle_free)
    cornertiles[corner] = builder.commit()

width, height = 7, 7
builder = ctx.create_array('top', width, height, hierarchical = True, set_as_top = True)
for x, y in product(range(width), range(height)):
    if x == 0 and y == 0:
        builder.instantiate(cornertiles[Corner.southwest], (x, y))
    elif x == 0 and y == height - 1:
        builder.instantiate(cornertiles[Corner.northwest], (x, y))
    elif x == width - 1 and y == 0:
        builder.instantiate(cornertiles[Corner.southeast], (x, y))
    elif x == width - 1 and y == height - 1:
        builder.instantiate(cornertiles[Corner.northeast], (x, y))
    elif (x in (0, width - 1) and 0 < y < height - 1) or (y in (0, height - 1) and 0 < x < width - 1):
        builder.instantiate(iotiles[Orientation.west if x == 0 else
            Orientation.east if x == width - 1 else Orientation.south if y == 0 else Orientation.north], (x, y))
    elif 0 < x < width - 1 and 0 < y < height - 1:
        builder.instantiate(subarray, (x, y))
# builder.fill( (0.15, 0.1), channel_on_edge = OrientationTuple(False) )
builder.auto_connect()
top = builder.commit()

TranslationPass().run(ctx)

Scanchain.complete_scanchain(ctx, ctx.database[ModuleView.logical, top.key])
Scanchain.annotate_user_view(ctx)

VPRArchGeneration('vpr/arch.xml').run(ctx)
VPR_RRG_Generation("vpr/rrg.xml").run(ctx)

r = Scanchain.new_renderer()
 
VerilogCollection(r, 'rtl').run(ctx)

YosysScriptsCollection(r, "syn").run(ctx)

r.render()

ctx.pickle(sys.argv[1])
