from prga.compatible import *
from prga.core.common import *
from prga.passes.translation import *
from prga.passes.vpr import *
from prga.passes.rtl import *
from prga.passes.yosys import *
from prga.cfg.scanchain.lib import ScanchainSwitchDatabase, Scanchain
from prga.netlist.module.util import ModuleUtils
from prga.netlist.net.util import NetUtils

from itertools import product
from pympler.asizeof import asizeof as size

ctx = Scanchain.new_context(1)
gbl_clk = ctx.create_global("clk", is_clock = True)
gbl_clk.bind((0, 1), 0)
l1 = ctx.create_segment('L1', 16, 1)
l2 = ctx.create_segment('L4', 16, 4)

builder = ctx.create_cluster("cluster")
o = builder.create_output("o", 2)
lut = builder.instantiate(ctx.primitives["fraclut6"], "lut")
ff = builder.instantiate(ctx.primitives["mdff"], "ff")
builder.connect(builder.create_clock("clk"), ff.pins['clk'])
builder.connect(builder.create_input("ce", 1), ff.pins["ce"])
builder.connect(builder.create_input("sr", 1), ff.pins["sr"])
builder.connect(builder.create_input("i", 6), lut.pins['in'])
builder.connect(lut.pins['o5'], o[1])
builder.connect(lut.pins['o6'], o[0])
builder.connect(lut.pins['o6'], ff.pins['D'], pack_patterns = ('lut6_dff', 'lut5A_dff'))
builder.connect(ff.pins['Q'], o[0])
cluster = builder.commit()

builder = ctx.create_io_block("iob", 2)
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
    builder.fill( (0.5, 0.5), sbox_pattern = SwitchBoxPattern.cycle_free )
    iotiles[ori] = builder.commit()

builder = ctx.create_logic_block("clb")
clk = builder.create_global(gbl_clk, Orientation.south)
ce = builder.create_input("ce", 1, Orientation.south)
sr = builder.create_input("sr", 1, Orientation.south)
for i, inst in enumerate(builder.instantiate(cluster, "cluster", vpr_num_pb = 2)):
    builder.connect(clk, inst.pins['clk'])
    builder.connect(ce, inst.pins['ce'])
    builder.connect(sr, inst.pins['sr'])
    builder.connect(builder.create_input("i{}".format(i), 6, Orientation.west), inst.pins['i'])
    builder.connect(inst.pins['o'], builder.create_output("o{}".format(i), 2, Orientation.east))
clb = builder.commit()

builder = ctx.create_array('subarray', 4, 4, set_as_top = False)
for pos in product(range(4), range(4)):
    builder.instantiate(clb, pos)
builder.fill( (0.25, 0.15), sbox_pattern = SwitchBoxPattern.cycle_free )
subarray = builder.commit()

cornertiles = {}
for corner in Corner:
    builder = ctx.create_array("cornertile_{}".format(corner.case("ne", "nw", "se", "sw")), 1, 1,
            set_as_top = False, edge = OrientationTuple(False, **{ori.name: True for ori in corner.decompose()}))
    builder.fill( (1., 1.), sbox_pattern = SwitchBoxPattern.cycle_free)
    cornertiles[corner] = builder.commit()

width, height = 10, 10
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
    elif (x in (0, width - 1) and 0 < y < height - 1) or (y in (0, width - 1) and 0 < x < height - 1):
        builder.instantiate(iotiles[Orientation.west if x == 0 else
            Orientation.east if x == width - 1 else Orientation.south if y == 0 else Orientation.north], (x, y))
    elif 0 < x < width - 1 and 0 < y < height - 1 and x % 4 == 1 and y % 4 == 1:
        builder.instantiate(subarray, (x, y))
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

ctx.pickle("ctx.pickled")
