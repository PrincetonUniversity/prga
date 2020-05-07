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

from itertools import product, chain
from pympler.asizeof import asizeof as size

enable_stdout_logging("prga")

K = 6
N = 6
subarray_width, subarray_height = 8, 8
subarray_col, subarray_row = 5, 4

ctx = Pktchain.new_context(phit_width = 32, cfg_width = 1)
gbl_clk = ctx.create_global("clk", is_clock = True)
gbl_clk.bind((0, 1), 0)
l1a = ctx.create_segment('L1A', 20, 1)
l4a = ctx.create_segment('L4A', 10, 4)
l1b = ctx.create_segment('L1B', 20, 1)
l4b = ctx.create_segment('L4B', 10, 4)

memory = ctx.create_memory("dpram_a10d8", 10, 8).commit()

builder = ctx.create_io_block("iob", 8)
o = builder.create_input("outpad", 1)
i = builder.create_output("inpad", 1)
builder.connect(builder.instances['io'].pins['inpad'], i)
builder.connect(o, builder.instances['io'].pins['outpad'])
iob = builder.commit()

pattern = SwitchBoxPattern.cycle_free

iotiles = {}
for ori in Orientation:
    builder = ctx.create_array('iotile_{}'.format(ori.name),
            1 if ori.dimension.is_x else subarray_width,
            1 if ori.dimension.is_y else subarray_height,
            set_as_top = False, edge = OrientationTuple(False, **{ori.name: True}))
    for x, y in product(range(builder.width), range(builder.height)):
        builder.instantiate(iob, (x, y))
    builder.fill( (0.5, 0.5), sbox_pattern = pattern )
    iotiles[ori] = builder.commit()

builder = ctx.create_logic_block("clb")
clk = builder.create_global(gbl_clk, Orientation.south)
iw = builder.create_input("iw", N // 2 * 6, Orientation.west)
ie = builder.create_input("ie", N // 2 * 6, Orientation.east)
ow = builder.create_output("ow", N // 2 * 2, Orientation.west)
oe = builder.create_output("oe", N // 2 * 2, Orientation.east)
cin = builder.create_input("cin", 1, Orientation.south)
for i, inst in enumerate(builder.instantiate(ctx.primitives["fle6"], "cluster", vpr_num_pb = N)):
    builder.connect(clk, inst.pins['clk'])
    if i % 2 == 0:
        i = i // 2
        builder.connect(iw[6 * i: 6 * (i + 1)], inst.pins["in"])
        builder.connect(inst.pins['out'], oe[2 * i: 2 * (i + 1)])
    else:
        i = i // 2
        builder.connect(ie[6 * i: 6 * (i + 1)], inst.pins["in"])
        builder.connect(inst.pins['out'], ow[2 * i: 2 * (i + 1)])
    builder.connect(cin, inst.pins["cin"], pack_patterns = ["carrychain"])
    cin = inst.pins["cout"]
builder.connect(cin, builder.create_output("cout", 1, Orientation.north), pack_patterns = ["carrychain"])
clb = builder.commit()

ctx.create_tunnel("carrychain", clb.ports["cout"], clb.ports["cin"], (0, -1))

builder = ctx.create_logic_block("bram", 1, 2)
inst = builder.instantiate(ctx.primitives["dpram_a10d8"], "bram_inst")
builder.connect(builder.create_global(gbl_clk, Orientation.south), inst.pins["clk"])
for port in ("addr1", "we1", "data1"):
    builder.connect(builder.create_input(port, len(inst.pins[port]), Orientation.west, (0, 0)), inst.pins[port])
for port in ("addr2", "we2", "data2"):
    builder.connect(builder.create_input(port, len(inst.pins[port]), Orientation.west, (0, 1)), inst.pins[port])
builder.connect(inst.pins["out1"], builder.create_output("out1", len(inst.pins["out1"]), Orientation.east, (0, 0)))
builder.connect(inst.pins["out2"], builder.create_output("out2", len(inst.pins["out2"]), Orientation.east, (0, 1)))
bram = builder.commit()

builder = ctx.create_array('subarray', subarray_width, subarray_height, set_as_top = False)
for x, y in product(range(builder.width), range(builder.height)):
    if x == 6:
        if y % 2 == 0:
            builder.instantiate(bram, (x, y))
    else:
        builder.instantiate(clb, (x, y))
builder.fill( (0.25, 0.15), segments = (l4a, l1a, l4b, l1b), sbox_pattern = pattern )
subarray = builder.commit()

cornertiles = {}
for corner in Corner:
    builder = ctx.create_array("cornertile_{}".format(corner.case("ne", "nw", "se", "sw")), 1, 1,
            set_as_top = False, edge = OrientationTuple(False, **{ori.name: True for ori in corner.decompose()}))
    builder.fill( (0.5, 0.5), sbox_pattern = pattern )
    cornertiles[corner] = builder.commit()

top_width = subarray_width * subarray_col + 2
top_height = subarray_height * subarray_row + 2
builder = ctx.create_array('top', top_width, top_height, hierarchical = True, set_as_top = True)
for x, y in product(range(top_width), range(top_height)):
    if x == 0 and y == 0:
        builder.instantiate(cornertiles[Corner.southwest], (x, y))
    elif x == 0 and y == top_height - 1:
        builder.instantiate(cornertiles[Corner.northwest], (x, y))
    elif x == top_width - 1 and y == 0:
        builder.instantiate(cornertiles[Corner.southeast], (x, y))
    elif x == top_width - 1 and y == top_height - 1:
        builder.instantiate(cornertiles[Corner.northeast], (x, y))
    elif x in (0, top_width - 1) and 0 < y < top_height - 1 and y % subarray_height == 1:
        builder.instantiate(iotiles[Orientation.west if x == 0 else Orientation.east], (x, y))
    elif y in (0, top_height - 1) and 0 < x < top_width - 1 and x % subarray_width == 1:
        builder.instantiate(iotiles[Orientation.south if y == 0 else Orientation.north], (x, y))
    elif 0 < x < top_width - 1 and 0 < y < top_height - 1 and x % subarray_width == 1 and y % subarray_height == 1:
        builder.instantiate(subarray, (x, y))
builder.auto_connect()
top = builder.commit()

TranslationPass().run(ctx)

def iter_instances(module):
    if module.name == "top":
        for x in chain(iter([0]), iter(subarray_width * x + 1 for x in range(subarray_col)), iter([top_width - 1])):
            for y in chain(iter([top_height - 1]),
                    iter(subarray_height * y + 1 for y in reversed(range(0, subarray_row, 2))),
                    iter([0]),
                    iter(subarray_height * y + 1 for y in range(1, subarray_row, 2))):
                yield module.instances[x, y]
            yield None
    else:
        for i in itervalues(module.instances):
            yield i

Pktchain.complete_pktchain(ctx, iter_instances = iter_instances)
Pktchain.annotate_user_view(ctx)

VPRArchGeneration('vpr/arch.xml').run(ctx)
VPR_RRG_Generation("vpr/rrg.xml").run(ctx)

r = Pktchain.new_renderer()

VerilogCollection(r, 'rtl').run(ctx)

YosysScriptsCollection(r, "syn").run(ctx)

r.render()

ctx.pickle("ctx.pickled")
