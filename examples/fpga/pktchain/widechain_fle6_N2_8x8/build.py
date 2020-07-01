from prga import *

from itertools import product
import sys

ctx = Pktchain.new_context(phit_width = 32, cfg_width = 2)
gbl_clk = ctx.create_global("clk", is_clock = True)
gbl_clk.bind((0, 1), 0)
ctx.create_segment("L1", 16, 1)
ctx.create_segment("L4", 4, 4)

builder = ctx.build_io_block("iob")
o = builder.create_input("outpad", 1)
i = builder.create_output("inpad", 1)
builder.connect(builder.instances['io'].pins['inpad'], i)
builder.connect(o, builder.instances['io'].pins['outpad'])
iob = builder.commit()

builder = ctx.build_logic_block("clb")
clk = builder.create_global(gbl_clk, Orientation.south)
in_ = builder.create_input("in", 12, Orientation.west)
out = builder.create_output("out", 4, Orientation.east)
xbar_i, xbar_o = [in_], []
cin = builder.create_input("cin", 1, Orientation.south)
for i, inst in enumerate(builder.instantiate(ctx.primitives["fle6"], "cluster", 2)):
    builder.connect(clk, inst.pins['clk'])
    builder.connect(inst.pins['out'], out[2 * i: 2 * (i + 1)])
    builder.connect(cin, inst.pins["cin"], vpr_pack_patterns = ["carrychain"])
    xbar_i.append(inst.pins["out"])
    xbar_o.append(inst.pins["in"])
    cin = inst.pins["cout"]
builder.connect(cin, builder.create_output("cout", 1, Orientation.north), vpr_pack_patterns = ["carrychain"])
builder.connect(xbar_i, xbar_o, fully = True)
clb = builder.commit()

ctx.create_tunnel("carrychain", clb.ports["cout"], clb.ports["cin"], (0, -1))

pattern = SwitchBoxPattern.cycle_free

iotiles = {ori: ctx.build_tile(iob, 4, name = "tile_io_{}".format(ori.name[0]),
        edge = OrientationTuple(False, **{ori.name: True})).fill( (1., 1.) ).auto_connect().commit()
        for ori in Orientation}
clbtile = ctx.build_tile(clb).fill( (0.4, 0.25) ).auto_connect().commit()

builder = ctx.build_array('subarray', 1, 4, set_as_top = False)
for x, y in product(range(1), range(4)):
    if True:
        builder.instantiate(clbtile, (x, y))
subarray = builder.fill(pattern).auto_connect().commit()

width, height = 10, 10
builder = ctx.build_array('top', width, height, set_as_top = True)
for x, y in product(range(width), range(height)):
    if x == 0 and y == 0:
        pass
    elif x == 0 and y == height - 1:
        pass
    elif x == width - 1 and y == 0:
        pass
    elif x == width - 1 and y == height - 1:
        pass
    elif x in (0, width - 1) and 0 < y < height - 1:
        builder.instantiate(iotiles[Orientation.west if x == 0 else Orientation.east], (x, y))
    elif y in (0, height - 1) and 0 < x < width - 1:
        builder.instantiate(iotiles[Orientation.south if y == 0 else Orientation.north], (x, y))
    elif 0 < x < width - 1 and 0 < y < height - 1 and y % 4 == 1:
        builder.instantiate(subarray, (x, y))
top = builder.fill( pattern ).auto_connect().commit()

def iter_instances(module):
    if module.name == "top":
        for x in range(5):
            for xx in range(2):
                if (t := module.instances.get( (x * 2 + xx, 9) )) is not None:
                    yield t
                for corner in Corner:
                    if (box := module.instances.get( ((x * 2 + xx, 9), corner) )) is not None:
                        yield box
            yield None
            for yy in range(4):
                if (t := module.instances.get( (x * 2, 8 - yy) )) is not None:
                    yield t
                for corner in Corner:
                    if (box := module.instances.get( ((x * 2, 8 - yy), corner) )) is not None:
                        yield box
            yield None
            for yy in range(4):
                if (t := module.instances.get( (x * 2, 4 - yy) )) is not None:
                    yield t
                for corner in Corner:
                    if (box := module.instances.get( ((x * 2, 4 - yy), corner) )) is not None:
                        yield box
            yield None
            for xx in range(2):
                if (t := module.instances.get( (x * 2 + xx, 0) )) is not None:
                    yield t
                for corner in Corner:
                    if (box := module.instances.get( ((x * 2 + xx, 0), corner) )) is not None:
                        yield box
            yield None
            for yy in range(4):
                if (t := module.instances.get( (x * 2 + 1, 1 + yy) )) is not None:
                    yield t
                for corner in Corner:
                    if (box := module.instances.get( ((x * 2 + 1, 1 + yy), corner) )) is not None:
                        yield box
            yield None
            for yy in range(4):
                if (t := module.instances.get( (x * 2 + 1, 5 + yy) )) is not None:
                    yield t
                for corner in Corner:
                    if (box := module.instances.get( ((x * 2 + 1, 5 + yy), corner) )) is not None:
                        yield box
            yield None
            yield None
    else:
        for i in itervalues(module.instances):
            yield i

flow = Flow(
    TranslationPass(),
    Pktchain.InjectConfigCircuitry(),
    VPRArchGeneration("vpr/arch.xml"),
    VPR_RRG_Generation("vpr/rrg.xml"),
    VerilogCollection('rtl'),
    YosysScriptsCollection("syn"),
    )
flow.run(ctx, Pktchain.new_renderer())

ctx.pickle(sys.argv[1])
