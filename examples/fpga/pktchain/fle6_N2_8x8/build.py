from prga.compatible import *
from prga.core.common import *
from prga.passes.translation import *
from prga.passes.vpr import *
from prga.passes.rtl import *
from prga.passes.yosys import *
from prga.cfg.pktchain.lib import Pktchain
from prga.netlist.module.util import ModuleUtils
from prga.netlist.net.util import NetUtils
from prga.util import enable_stdout_logging

from itertools import product
from pympler.asizeof import asizeof as size

enable_stdout_logging("prga")

ctx = Pktchain.new_context(phit_width = 8, cfg_width = 1)
gbl_clk = ctx.create_global("clk", is_clock = True)
gbl_clk.bind((0, 1), 0)
ctx.create_segment("L1", 16, 1)
ctx.create_segment("L4", 4, 4)

# memory = ctx.create_memory("dpram_a10d8", 10, 8).commit()

builder = ctx.create_io_block("iob", 2)
o = builder.create_input("outpad", 1)
i = builder.create_output("inpad", 1)
builder.connect(builder.instances['io'].pins['inpad'], i)
builder.connect(o, builder.instances['io'].pins['outpad'])
iob = builder.commit()

pattern = SwitchBoxPattern.cycle_free

iotiles = {}
for ori in Orientation:
    builder = ctx.create_array('iotile_{}'.format(ori.name), 1, 1 if ori.dimension.is_y else 4,
            set_as_top = False, edge = OrientationTuple(False, **{ori.name: True}))
    for x, y in product(range(builder.width), range(builder.height)):
        builder.instantiate(iob, (x, y))
    builder.fill( (0.5, 0.5), sbox_pattern = pattern )
    iotiles[ori] = builder.commit()

builder = ctx.create_logic_block("clb")
clk = builder.create_global(gbl_clk, Orientation.south)
in_ = builder.create_input("in", 12, Orientation.west)
out = builder.create_output("out", 4, Orientation.east)
xbar_i, xbar_o = [in_], []
cin = builder.create_input("cin", 1, Orientation.south)
for i, inst in enumerate(builder.instantiate(ctx.primitives["fle6"], "cluster", vpr_num_pb = 2)):
    builder.connect(clk, inst.pins['clk'])
    # builder.connect(in_[6 * i: 6 * (i + 1)], inst.pins['in'])
    builder.connect(inst.pins['out'], out[2 * i: 2 * (i + 1)])
    builder.connect(cin, inst.pins["cin"], pack_patterns = ["carrychain"])
    xbar_i.append(inst.pins["out"])
    xbar_o.append(inst.pins["in"])
    cin = inst.pins["cout"]
builder.connect(cin, builder.create_output("cout", 1, Orientation.north), pack_patterns = ["carrychain"])
builder.connect(xbar_i, xbar_o, fully = True)
clb = builder.commit()

ctx.create_tunnel("carrychain", clb.ports["cout"], clb.ports["cin"], (0, -1))

# builder = ctx.create_logic_block("bram", 1, 2)
# inst = builder.instantiate(ctx.primitives["dpram_a10d8"], "bram_inst")
# builder.connect(builder.create_global(gbl_clk, Orientation.south), inst.pins["clk"])
# for port in ("addr1", "we1", "data1"):
#     builder.connect(builder.create_input(port, len(inst.pins[port]), Orientation.west, (0, 0)), inst.pins[port])
# for port in ("addr2", "we2", "data2"):
#     builder.connect(builder.create_input(port, len(inst.pins[port]), Orientation.west, (0, 1)), inst.pins[port])
# builder.connect(inst.pins["out1"], builder.create_output("out1", len(inst.pins["out1"]), Orientation.east, (0, 0)))
# builder.connect(inst.pins["out2"], builder.create_output("out2", len(inst.pins["out2"]), Orientation.east, (0, 1)))
# bram = builder.commit()

builder = ctx.create_array('subarray', 1, 4, set_as_top = False)
for x, y in product(range(1), range(4)):
    # if x == 2:
    #     if y % 2 == 0:
    #         builder.instantiate(bram, (x, y))
    # else:
    if True:
        builder.instantiate(clb, (x, y))
builder.fill( (0.25, 0.15), sbox_pattern = pattern )
subarray = builder.commit()

cornertiles = {}
for corner in Corner:
    builder = ctx.create_array('cornertile_{}'.format(corner.name), 1, 1,
            set_as_top = False, edge = OrientationTuple(False, **{ori.name: True for ori in corner.decompose()}))
    builder.fill( (0.5, 0.5), sbox_pattern = pattern )
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
    elif x in (0, width - 1) and 0 < y < height - 1 and y % 4 == 1:
        builder.instantiate(iotiles[Orientation.west if x == 0 else Orientation.east], (x, y))
    elif y in (0, height - 1) and 0 < x < width - 1:
        builder.instantiate(iotiles[Orientation.south if y == 0 else Orientation.north], (x, y))
    elif 0 < x < width - 1 and 0 < y < height - 1 and y % 4 == 1:
        builder.instantiate(subarray, (x, y))
builder.auto_connect()
top = builder.commit()

TranslationPass().run(ctx)

def iter_instances(module):
    if module.name == "top":
        for x in range(5):
            yield module.instances[x * 2,     9]
            yield module.instances[x * 2,     5]
            yield module.instances[x * 2,     1]
            yield module.instances[x * 2,     0]
            yield module.instances[x * 2 + 1, 0]
            yield module.instances[x * 2 + 1, 1]
            yield module.instances[x * 2 + 1, 5]
            yield module.instances[x * 2 + 1, 9]
            yield None
    else:
        for i in itervalues(module.instances):
            yield i

Pktchain.complete_pktchain(ctx, iter_instances = iter_instances)
Pktchain.annotate_user_view(ctx)

VPRArchGeneration("vpr/arch.xml").run(ctx)
VPR_RRG_Generation("vpr/rrg.xml").run(ctx)

# scalable = VPRScalableDelegate(1.0)
# for ori in Orientation:
#     scalable.add_active_tile(iob, ori, (0.5, 0.5))
# scalable.add_active_tile(clb, fc = (0.25, 0.15))
# scalable.add_active_tile(bram, fc = (0.25, 0.15))
# scalable.add_layout_rule("fill", 0, clb)
# scalable.add_layout_rule("corners", 100, None)
# scalable.add_layout_rule("row", 2, iob, Orientation.south, starty = 0)
# scalable.add_layout_rule("row", 2, iob, Orientation.north, starty = "H - 1")
# scalable.add_layout_rule("col", 2, iob, Orientation.west, startx = 0)
# scalable.add_layout_rule("col", 2, iob, Orientation.east, startx = "W - 1")
# scalable.add_layout_rule("col", 1, bram, startx = 6, repeatx = 8)
# 
# VPRScalableArchGeneration("vpr/arch.scal.xml", scalable).run(ctx)

r = Pktchain.new_renderer()

VerilogCollection(r, 'rtl').run(ctx)

YosysScriptsCollection(r, "syn").run(ctx)

r.render()

ctx.pickle("ctx.pickled")
ctx.pickle_summary("summary.pickled")
