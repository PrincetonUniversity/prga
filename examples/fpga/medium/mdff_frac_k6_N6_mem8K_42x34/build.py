from prga.compatible import *
from prga.core.common import *
from prga.passes.translation import *
from prga.passes.vpr import *
from prga.passes.rtl import *
from prga.passes.yosys import *
from prga.cfg.scanchain.lib import ScanchainSwitchDatabase, Scanchain
from prga.netlist.module.util import ModuleUtils
from prga.netlist.net.util import NetUtils
from prga.util import enable_stdout_logging

from itertools import product
from pympler.asizeof import asizeof as size

enable_stdout_logging(__name__)

K = 6
N = 6
subarray_width, subarray_height = 8, 8
subarray_col, subarray_row = 5, 4

ctx = Scanchain.new_context(1)
gbl_clk = ctx.create_global("clk", is_clock = True)
gbl_clk.bind((0, 1), 0)
l1a = ctx.create_segment('L1A', 20, 1)
l4a = ctx.create_segment('L4A', 10, 4)
l1b = ctx.create_segment('L1B', 20, 1)
l4b = ctx.create_segment('L4B', 10, 4)

memory = ctx.create_memory("dpram_a10d8", 10, 8).commit()

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

builder = ctx.create_io_block("iob", 8)
o = builder.create_input("outpad", 1)
i = builder.create_output("inpad", 1)
builder.connect(builder.instances['io'].pins['inpad'], i)
builder.connect(o, builder.instances['io'].pins['outpad'])
iob = builder.commit()

iotiles = {}
for ori in Orientation:
    if ori.is_auto:
        continue
    builder = ctx.create_array('iotile_{}'.format(ori.name), 1, 1,
            set_as_top = False, edge = OrientationTuple(False, **{ori.name: True}))
    builder.instantiate(iob, (0, 0))
    builder.fill( (0.5, 0.5) )
    iotiles[ori] = builder.commit()

builder = ctx.create_logic_block("clb")
clk = builder.create_global(gbl_clk, Orientation.south)
ce = builder.create_input("ce", 1, Orientation.south)
sr = builder.create_input("sr", 1, Orientation.south)
for i in range(N):
    inst = builder.instantiate(cluster, "cluster{}".format(i))
    builder.connect(clk, inst.pins['clk'])
    builder.connect(ce, inst.pins['ce'])
    builder.connect(sr, inst.pins['sr'])
    builder.connect(builder.create_input("i{}".format(i), K, Orientation.west), inst.pins['i'])
    builder.connect(inst.pins['o'], builder.create_output("o{}".format(i), 2, Orientation.east))
clb = builder.commit()

builder = ctx.create_logic_block("bram", 1, 2)
inst = builder.instantiate(ctx.primitives["dpram_a10d8"], "bram_inst")
builder.connect(builder.create_global(gbl_clk, Orientation.south), inst.pins["clk"])
for port in ("addr1", "we1", "data1"):
    builder.connect(builder.create_input(port, len(inst.pins[port]), Orientation.west, (0, 0)), inst.pins[port])
for port in ("addr2", "we2", "data2"):
    builder.connect(builder.create_input(port, len(inst.pins[port]), Orientation.west, (0, 1)), inst.pins[port])
builder.connect(inst.pins["out1"], builder.create_output("out1", len(inst.pins[port]), Orientation.east, (0, 0)))
builder.connect(inst.pins["out2"], builder.create_output("out2", len(inst.pins[port]), Orientation.east, (0, 1)))
bram = builder.commit()

builder = ctx.create_array('subarray', subarray_width, subarray_height, set_as_top = False)
for x, y in product(range(builder.width), range(builder.height)):
    if x == 6:
        if y % 2 == 0:
            builder.instantiate(bram, (x, y))
    else:
        builder.instantiate(clb, (x, y))
builder.fill( (0.25, 0.15), segments = (l4a, l1a, l4b, l1b),
        sbox_pattern = SwitchBoxPattern.span_limited, max_span = 60)
subarray = builder.commit()

top_width = subarray_width * subarray_col + 2
top_height = subarray_height * subarray_row + 2
builder = ctx.create_array('top', top_width, top_height, hierarchical = True, set_as_top = True)
for x, y in product(range(top_width), range(top_height)):
    if (x in (0, top_width - 1) and 0 < y < top_height - 1) or (y in (0, top_height) and 0 < x < top_width - 1):
        builder.instantiate(iotiles[Orientation.west if x == 0 else
            Orientation.east if x == top_width - 1 else Orientation.south if y == 0 else Orientation.north], (x, y))
    elif x < top_width - 1 and y < top_height - 1 and x % subarray_width == 1 and y % subarray_height == 1:
        builder.instantiate(subarray, (x, y))
builder.auto_connect()
top = builder.commit()

TranslationPass().run(ctx)

Scanchain.complete_scanchain(ctx, ctx.database[ModuleView.logical, top.key])

VPRInputsGeneration('vpr').run(ctx)

r = Scanchain.new_renderer()

VerilogCollection(r, 'rtl').run(ctx)

YosysScriptsCollection(r, "syn").run(ctx)

r.render()

ctx.pickle("ctx.pickled")
