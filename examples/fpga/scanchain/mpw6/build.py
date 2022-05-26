from prga import *
from prga.core.common import IO, IOType, PortDirection
from prga.algorithm.interconnect import InterconnectAlgorithms
from itertools import product

import sys

# key parameters
k, N, W, H = 4, 8, 10, 10
ext_prog_clk = False

print ("[INFO] Using {} prog_clk".format("external" if ext_prog_clk else "internal"))

# secondary parameters
n_L1 = 12
n_io = 2
fs_i = 0.25
fs_o = 0.15
chain_width = 1

# context
ctx = Context()
gbl_clk = ctx.create_global("clk", is_clock = True)
gbl_clk.bind((0, 1), 0)
ctx.create_segment('L1', n_L1, 1)

# slice
builder = ctx.build_slice("slice")
clk = builder.create_clock("clk")
i = builder.create_input("i", 4)
o = builder.create_output("o", 1)
lut = builder.instantiate(ctx.primitives["lut" + str(k)], "lut")
ff = builder.instantiate(ctx.primitives["flipflop"], "ff")
builder.connect(clk, ff.pins['clk'])
builder.connect(i, lut.pins['in'])
builder.connect(lut.pins['out'], o)
builder.connect(lut.pins['out'], ff.pins['D'], vpr_pack_patterns = ('lut_dff', ))
builder.connect(ff.pins['Q'], o)
cluster = builder.commit()

# IOB
builder = ctx.build_io_block("iob")
o = builder.create_input("outpad", 1)
i = builder.create_output("inpad", 1)
builder.connect(builder.instances['io'].pins['inpad'], i)
builder.connect(o, builder.instances['io'].pins['outpad'])
iob = builder.commit()

# CLB
builder = ctx.build_logic_block("clb")
clk = builder.create_global(gbl_clk,                        Orientation.south)
in_ = builder.create_input ("in",       N * k // 2,         Orientation.west)
out = builder.create_output("out",      N,                  Orientation.east)
# xbar_i, xbar_o = [], []
# xbar_i.extend(in_)
for i, inst in enumerate(builder.instantiate(cluster, "cluster", N)):
    builder.connect(clk,                inst.pins['clk'])
    builder.connect(inst.pins["o"],     out[i])

# each input pin of `inst` connects to 2 input ports of `clb`
cons = [[] for _ in range(N)]
for n, m in InterconnectAlgorithms.crossbar(len(in_), N, 2*k):
    cons[m].append(n)
print ("iport-ipin:", cons)
for i, con in enumerate(cons):
    for j, c in enumerate(con):
        builder.connect(in_[c], builder.instances["cluster", i].pins["i"][j%k])

# each input pin of `inst` connects to 1 output pins of another `inst`
cons = [[] for _ in range(N)]
for n, m in InterconnectAlgorithms.crossbar(N, N, k):
    cons[m].append(n)
print ("opin-ipin:", cons)
for i, con in enumerate(cons):
    for j, c in enumerate(con):
        builder.connect(builder.instances["cluster", c].pins["o"],
                builder.instances["cluster", i].pins["i"][j%k])

    # xbar_i.extend(inst.pins["o"])
    # xbar_o.extend(inst.pins["i"])
# crossbar: 50% connectivity
# for i, sink in enumerate(xbar_o):
#     for j, src in enumerate(xbar_i):
#         if j % 2 == i % 2:
#             builder.connect(src, sink)
clb = builder.commit()

# CLB tile
clbtile = ctx.build_tile(clb).fill( (fs_i, fs_o) ).auto_connect().commit()

# IO tile
iotiles = {}
for ori in Orientation:
    builder = ctx.build_tile(iob, n_io, name = "t_io_{}".format(ori.name[0]),
            edge = OrientationTuple(False, **{ori.name: True}))
    iotiles[ori] = builder.fill( (.5, .5) ).auto_connect().commit()

# Top
builder = ctx.build_array('top', W, H, set_as_top = True)
for x, y in product(range(builder.width), range(builder.height)):
    if x in (0, builder.width - 1) and y in (0, builder.height - 1):
        pass
    elif x == 0:
        builder.instantiate(iotiles[Orientation.west], (x, y))
    elif x == builder.width - 1:
        builder.instantiate(iotiles[Orientation.east], (x, y))
    elif y == 0:
        pass
        # builder.instantiate(iotiles[Orientation.south], (x, y))
    elif y == builder.height - 1:
        builder.instantiate(iotiles[Orientation.north], (x, y))
    else:
        builder.instantiate(clbtile, (x, y))
top = builder.fill( SwitchBoxPattern.cycle_free ).auto_connect().commit()

Flow(
        VPRArchGeneration('vpr/arch.xml'),
        VPR_RRG_Generation('vpr/rrg.xml'),
        YosysScriptsCollection('syn'),
        ).run(ctx)

def iter_instances (module):
    if module.name == "top":
        # zig-zag
        for x in range(module.width):
            for y in range(module.height):
                if i := module.instances.get( ((x, y), Corner.southwest) ): yield i
                if i := module.instances.get(  (x, y)                    ): yield i
                if i := module.instances.get( ((x, y), Corner.northwest) ): yield i
            for y in reversed(range(module.height)):
                if i := module.instances.get( ((x, y), Corner.northeast) ): yield i
                if i := module.instances.get( ((x, y), Corner.southeast) ): yield i
    else:
        for i in module.instances.values():
            yield i

Flow(
        Materialization('scanchain', chain_width = chain_width),
        Translation(),
        SwitchPathAnnotation(),
        ProgCircuitryInsertion(iter_instances = iter_instances),
        VerilogCollection('rtl'),
        ).run(ctx)

# remove unusable I/O from IOPlanner (due to physical I/O limitations of the caravel wrapper)
def create_io (x,y,subtile,global_ = None):
    return IO( (PortDirection.input_, PortDirection.output), (x, y), subtile, global_ )

ios = [
        # hard-wired clock
        create_io (0, 1, 0, gbl_clk),

        # west bank: 9 I/Os
        create_io (0, 1, 1),
        create_io (0, 2, 0),
        create_io (0, 3, 0),
        # create_io (0, 3, 1),
        create_io (0, 4, 0),
        create_io (0, 5, 0),
        create_io (0, 6, 0),
        ]

if ext_prog_clk:
    ios.append ( create_io (0, 6, 1) )

ios.extend ([
        create_io (0, 7, 0),
        create_io (0, 8, 0),

        # north bank: 9 I/Os
        create_io (1, H-1, 0),
        create_io (2, H-1, 0),
        create_io (2, H-1, 1),
        create_io (3, H-1, 0),
        create_io (4, H-1, 0),
        create_io (5, H-1, 0),
        create_io (6, H-1, 0),
        create_io (7, H-1, 0),
        # create_io (7, H-1, 1),
        create_io (8, H-1, 1),

        # east bank: 13 I/Os, but less recommended for use
        # create_io (9, 8, 1),
        create_io (W-1, 8, 0),
        create_io (W-1, 7, 1),
        create_io (W-1, 7, 0),
        create_io (W-1, 6, 0),
        create_io (W-1, 5, 1),
        create_io (W-1, 5, 0),
        create_io (W-1, 4, 0),
        create_io (W-1, 3, 1),
        create_io (W-1, 3, 0),
        create_io (W-1, 2, 1),
        create_io (W-1, 2, 0),
        create_io (W-1, 1, 1),
        create_io (W-1, 1, 0),
        ])

ctx.summary.ios = ios

ctx.pickle("ctx.pkl" if len(sys.argv) < 2 else sys.argv[1])

visited, next_, flist = [clbtile.key], [ctx.database[ModuleView.design, clbtile.key]], []
while next_:
    d = next_.pop(0)
    flist.append(getattr(d, "verilog_src", d.name + ".v"))
    for sub in d.instances.values():
        if sub.model.key not in visited:
            next_.append(sub.model)
            visited.append(sub.model.key)
with open("rtl/Flist.clb", 'w') as f:
    # f.write("rtl/include/prga_utils.vh\n")
    # f.write("rtl/include/pktchain.vh\n")
    for ff in flist:
        f.write("rtl/" + ff + "\n")

visited, next_, flist = [top.key], [ctx.database[ModuleView.design, top.key]], []
while next_:
    d = next_.pop(0)
    flist.append(getattr(d, "verilog_src", d.name + ".v"))
    for sub in d.instances.values():
        if sub.model.key not in visited and sub.model.key != clbtile.key:
            next_.append(sub.model)
            visited.append(sub.model.key)
with open("rtl/Flist.top", 'w') as f:
    # f.write("rtl/include/prga_utils.vh\n")
    # f.write("rtl/include/pktchain.vh\n")
    for ff in flist:
        f.write("rtl/" + ff + "\n")

# pinout
s_ext_clk = """      chip-level I/O       |  PRGA top pin  | direction 
---------------------------+----------------+-----------
 clock                     | prog_clk       |  I        
 mprj io[37]               | ipin_x0y1_0    |  I        
 mprj io[36]               | prog_din       |  I        
 mprj io[35]               | prog_done      |  I        
 mprj io[34]               | prog_rst       |  I        
 mprj io[33]               | prog_we        |  I        
 mprj io[1]                | prog_dout      |  O
 mprj io[0]                | prog_we_o      |  O
---------------------------+----------------+-----------"""

s_int_clk = """      chip-level I/O       |  PRGA top pin  | direction 
---------------------------+----------------+-----------
 mprj io[37]               | prog_clk       |  I        
 mprj io[36]               | ipin_x0y1_0    |  I        
 mprj io[35]               | prog_din       |  I        
 mprj io[34]               | prog_done      |  I        
 mprj io[33]               | prog_rst       |  I        
 mprj io[32]               | prog_we        |  I        
 mprj io[1]                | prog_dout      |  O
 mprj io[0]                | prog_we_o      |  O
---------------------------+----------------+-----------"""

tmpl = """
                           | ipin_x{x}y{y}_{z}    |  I        
 mprj io[{pin:>2d}]               | opin_x{x}y{y}_{z}    |  O        
                           | oe_x{x}y{y}_{z}      |  O        
---------------------------+----------------+-----------"""

with open("pinout.txt", "w") as f:
    if ext_prog_clk:
        f.write (s_ext_clk)
    else:
        f.write (s_int_clk)

    for io, id_ in zip(ctx.summary.ios[1:], reversed(range(2, 33 if ext_prog_clk else 32))):
        f.write (tmpl.format(pin=id_, x=io.position.x, y=io.position.y, z=io.subtile))

    f.write ("\n")

# wrapper connection
s_int_clk = """
`define MPRJ_IO_37_I
`define MPRJ_IO_37_CONN prog_clk

`define MPRJ_IO_36_I
`define MPRJ_IO_36_CONN ipin_x0y1_0

`define MPRJ_IO_35_I
`define MPRJ_IO_35_CONN prog_din

`define MPRJ_IO_34_I
`define MPRJ_IO_34_CONN prog_done

`define MPRJ_IO_33_I
`define MPRJ_IO_33_CONN prog_rst

`define MPRJ_IO_32_I
`define MPRJ_IO_32_CONN prog_we

`define MPRJ_IO_1_O
`define MPRJ_IO_1_CONN  prog_dout

`define MPRJ_IO_0_O
`define MPRJ_IO_0_CONN  prog_we_o
"""

tmpl = """
`define MPRJ_IO_{pin}_IO
`define MPRJ_IO_{pin}_CONN x{x}y{y}_{z}
"""

with open("conn.v", "w") as f:
    if ext_prog_clk:
        raise RuntimeError ("external prog_clk not supported")
    else:
        f.write ( s_int_clk )

    for io, id_ in zip(ctx.summary.ios[1:], reversed(range(2, 33 if ext_prog_clk else 32))):
        f.write ( tmpl.format ( pin = id_, x = io.position.x, y = io.position.y, z = io.subtile ) )
