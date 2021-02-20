from prga import *
from itertools import product

import sys
import os

# ============================================================================
# -- Create Context ----------------------------------------------------------
# ============================================================================
ctx = Magic.new_context()

# ============================================================================
# -- Routing Resources -------------------------------------------------------
# ============================================================================
gbl_clk = ctx.create_global("clk", is_clock = True)
gbl_clk.bind((0, 1), 0)

# Channel width: 200
l1 = ctx.create_segment('L1', 20, 1)
l4 = ctx.create_segment('L4', 16, 4)
l16 = ctx.create_segment('L16', 1, 16)

# ============================================================================
# -- Primitives --------------------------------------------------------------
# ============================================================================
# -- picorv32 IP core --------------------------------------------------------
builder = ctx.build_primitive("picorv32",
        vpr_model = "picorv32",
        # Use absolute path here, so the file is not copied into our generated RTL directory
        verilog_src = os.path.join(os.path.abspath(os.path.dirname(__file__)), "src/picorv32.v"))

# only create used ports
clk         = builder.create_clock ("clk")
resetn      = builder.create_input ("resetn",    1)
mem_valid   = builder.create_output("mem_valid", 1)
mem_instr   = builder.create_output("mem_instr", 1)
mem_ready   = builder.create_input ("mem_ready", 1)
mem_addr    = builder.create_output("mem_addr",  32)
mem_wdata   = builder.create_output("mem_wdata", 32)
mem_wstrb   = builder.create_output("mem_wstrb", 4)
mem_rdata   = builder.create_input ("mem_rdata", 32)
irq         = builder.create_input ("irq",       32)

# timing arcs
builder.create_timing_arc(TimingArcType.seq_end,   clk, resetn)
builder.create_timing_arc(TimingArcType.seq_start, clk, mem_valid)
builder.create_timing_arc(TimingArcType.seq_start, clk, mem_instr)
builder.create_timing_arc(TimingArcType.seq_end,   clk, mem_ready)
builder.create_timing_arc(TimingArcType.seq_start, clk, mem_addr)
builder.create_timing_arc(TimingArcType.seq_start, clk, mem_wdata)
builder.create_timing_arc(TimingArcType.seq_start, clk, mem_wstrb)
builder.create_timing_arc(TimingArcType.seq_end,   clk, mem_rdata)
builder.create_timing_arc(TimingArcType.seq_end,   clk, irq)

builder = builder.build_design_view_counterpart(
        # Use absolute path here, so the file is not copied into our generated RTL directory
        verilog_src = os.path.join(os.path.abspath(os.path.dirname(__file__)), "src/picorv32.v"))
builder.commit()

# -- negedge DFF ------------------------------------------------------------
builder = ctx.build_primitive("dffn",
        vpr_model = "dffn",
        # Use absolute path here, so the file is not copied into our generated RTL directory
        verilog_src = os.path.join(os.path.abspath(os.path.dirname(__file__)), "src/dffn.v"),
        techmap_template = "dffn.techmap.tmpl.v",
        techmap_order = -1.,    # techmap `dffn` after LUT mapping
        )

# ports
clk = builder.create_clock ("clk")
D   = builder.create_input ("D", 1)
Q   = builder.create_output("Q", 1)

# timing arcs
builder.create_timing_arc(TimingArcType.seq_end,   clk, D)
builder.create_timing_arc(TimingArcType.seq_start, clk, Q)

builder = builder.build_design_view_counterpart(
        # Use absolute path here, so the file is not copied into our generated RTL directory
        verilog_src = os.path.join(os.path.abspath(os.path.dirname(__file__)), "src/dffn.v"))
builder.commit()

# ============================================================================
# -- Blocks ------------------------------------------------------------------
# ============================================================================
# -- IOB ---------------------------------------------------------------------
builder = ctx.build_io_block("iob")
o = builder.create_input("outpad", 1)
i = builder.create_output("inpad", 1)
builder.connect(builder.instances['io'].pins['inpad'], i)
builder.connect(o, builder.instances['io'].pins['outpad'])
iob = builder.commit()

# -- CLB ---------------------------------------------------------------------
builder = ctx.build_logic_block("clb")
grady18v2 = ctx.primitives["grady18v2"]
N = 4

lin = len(grady18v2.ports["in"])
lout = len(grady18v2.ports["out"])

clk = builder.create_global(gbl_clk, Orientation.south)
ce = builder.create_input("ce", 1, Orientation.west)
in_ = builder.create_input("in", lin * N // 2, Orientation.west)
out = builder.create_output("out", lout * N, Orientation.east)
cin = builder.create_input("cin", 1, Orientation.south)

xin, xout = [], []
xin.extend(in_)

for i, inst in enumerate(builder.instantiate(grady18v2, "i_grady18", N)):
    builder.connect(clk, inst.pins['clk'])
    builder.connect(ce, inst.pins['ce'])
    builder.connect(cin, inst.pins["cin"], vpr_pack_patterns = ["carrychain"])
    builder.connect(inst.pins["out"], out[i * 2 : (i + 1) * 2])
    cin = inst.pins["cout"]
    xout.extend(inst.pins['in'])
    xin.extend(inst.pins['out'])

builder.connect(cin, builder.create_output("cout", 1, Orientation.north), vpr_pack_patterns = ["carrychain"])
for (i, pxin), (j, pxout) in product(enumerate(xin), enumerate(xout)):
    if i % 2 == j % 2:
        builder.connect(pxin, pxout)
clb = builder.commit()

# -- CLB (2) -----------------------------------------------------------------
# Special negedge DFF block: step 1 - build slice
builder = ctx.build_slice("lut6dffn")
clk = builder.create_clock ("clk")
in_ = builder.create_input ("in",  6)
out = builder.create_output("out", 1)

lut6 = builder.instantiate(ctx.primitives["lut6"], "i_lut6")
dffn = builder.instantiate(ctx.primitives["dffn"], "i_dffn")

builder.connect(in_,              lut6.pins["in"])
builder.connect(lut6.pins["out"], dffn.pins["D"], vpr_pack_patterns = ["lut6_dffn"])
builder.connect(lut6.pins["out"], out)
builder.connect(clk,              dffn.pins["clk"])
builder.connect(dffn.pins["Q"],   out)

slice_ = builder.commit()

# step 2 - build block
builder = ctx.build_logic_block("dffn_clb")
N = 4

clk = builder.create_global(gbl_clk,           Orientation.south)
in_ = builder.create_input ("in",  6 * N // 2, Orientation.west)
out = builder.create_output("out", N,          Orientation.east)

xin, xout = [], []
xin.extend(in_)

for i, inst in enumerate(builder.instantiate(slice_, "i_slice", N)):
    builder.connect(clk, inst.pins["clk"])
    builder.connect(inst.pins["out"], out[i])
    xout.extend(inst.pins["in"])
    xin .extend(inst.pins["out"])

for (i, pxin), (j, pxout) in product(enumerate(xin), enumerate(xout)):
    if i % 2 == j % 2:
        builder.connect(pxin, pxout)
dffn_clb = builder.commit()

# -- BRAM --------------------------------------------------------------------
# BRAM (1Kb): 128x8, 256x4, 512x2, 1K1b
builder = ctx.build_logic_block("bram", 1, 2)
inst = builder.instantiate(
        ctx.create_multimode_memory(7, 8, addr_width = 10),
        "i_ram")
builder.connect(builder.create_global(gbl_clk, Orientation.south), inst.pins["clk"])
builder.connect(builder.create_input("we", 1, Orientation.west, (0, 0)), inst.pins["we"])
builder.connect(builder.create_input("din", 8, Orientation.east, (0, 0)), inst.pins["din"])
builder.connect(builder.create_input("waddr", 10, Orientation.west, (0, 0)), inst.pins["waddr"])
builder.connect(builder.create_input("raddr", 10, Orientation.west, (0, 1)), inst.pins["raddr"])
builder.connect(inst.pins["dout"], builder.create_output("dout", 8, Orientation.east, (0, 1)))
bram = builder.commit()

# -- Pico Core Block ---------------------------------------------------------
# Hard pico core: takes 8x8 tiles, no routing tracks over it
builder = ctx.build_logic_block("bpico", 8, 8, )
inst = builder.instantiate(ctx.primitives["picorv32"], "i_core",
        translate_attrs = {
            "verilog_parameters":  {
                "BARREL_SHIFTER":   1,
                "COMPRESSED_ISA":   1,
                "ENABLE_MUL":       1,
                "ENABLE_DIV":       1,
                "ENABLE_COUNTERS":  1,
                "ENABLE_IRQ":       1,
                "ENABLE_IRQ_QREGS": 1,
                "STACKADDR":        1024,
                "PROGADDR_RESET":   "32'h0010_0000",
                "PROGADDR_IRQ":     "32'h0000_0000",
                },
            },
        )
        
builder.connect(builder.create_global(gbl_clk, Orientation.east, (7, 0)), inst.pins["clk"])
builder.connect(builder.create_input("resetn", 1, Orientation.east, (7, 0)), inst.pins["resetn"])
builder.connect(inst.pins["mem_valid"], builder.create_output("mem_valid", 1, Orientation.east, (7, 0)))
builder.connect(inst.pins["mem_instr"], builder.create_output("mem_instr", 1, Orientation.east, (7, 0)))
builder.connect(builder.create_input("mem_ready", 1, Orientation.east, (7, 0)), inst.pins["mem_ready"])
builder.connect(inst.pins["mem_wstrb"], builder.create_output("mem_wstrb", 4, Orientation.east, (7, 0)))
builder.connect(inst.pins["mem_addr"][15:0], builder.create_output("mem_addr_l", 16, Orientation.east, (7, 0)))
builder.connect(inst.pins["mem_addr"][31:16], builder.create_output("mem_addr_h", 16, Orientation.east, (7, 1)))
builder.connect(inst.pins["mem_wdata"][15:0], builder.create_output("mem_wdata_l", 16, Orientation.east, (7, 2)))
builder.connect(inst.pins["mem_wdata"][31:16], builder.create_output("mem_wdata_h", 16, Orientation.east, (7, 3)))
builder.connect(builder.create_input("mem_rdata_l", 16, Orientation.east, (7, 4)), inst.pins["mem_rdata"][15:0])
builder.connect(builder.create_input("mem_rdata_h", 16, Orientation.east, (7, 5)), inst.pins["mem_rdata"][31:16])
builder.connect(builder.create_input("irq_l", 16, Orientation.east, (7, 6)), inst.pins["irq"][15:0])
builder.connect(builder.create_input("irq_h", 16, Orientation.east, (7, 7)), inst.pins["irq"][31:16])
bpico = builder.commit()

# ============================================================================
# -- Tiles -------------------------------------------------------------------
# ============================================================================
# -- CLB tile ----------------------------------------------------------------
ctx.create_tunnel("carrychain", clb.ports["cout"], clb.ports["cin"], (0, -1))
clbtile = ctx.build_tile(clb).fill( (0.15, 0.25) ).auto_connect().commit()

# the other type of CLB tile
dffntile = ctx.build_tile(dffn_clb).fill( (0.15, 0.25) ).auto_connect().commit()

# -- IOB tile ----------------------------------------------------------------
iotiles = {}
for ori in Orientation:
    builder = ctx.build_tile(iob, 4, name = "t_io_{}".format(ori.name[0]),
            edge = OrientationTuple(False, **{ori.name: True}))
    iotiles[ori] = builder.fill( (1., 1.) ).auto_connect().commit()

# -- BRAM tile ---------------------------------------------------------------
bramtile = ctx.build_tile(bram).fill( (0.15, 0.25) ).auto_connect().commit()

# -- PICO tile ---------------------------------------------------------------
picotile = ctx.build_tile(bpico, disallow_segments_passthru = True,
        ).fill( (0.15, 0.25) ).auto_connect().commit()

# ============================================================================
# -- Subarrays ---------------------------------------------------------------
# ============================================================================
# use single-corner cycle-free switch boxes
pattern = SwitchBoxPattern.cycle_free(fill_corners = [Corner.northeast])

# basic type (only CLBs)
builder = ctx.build_array("a_basic", 4, 4, set_as_top = False)
for x, y in product(range(builder.width), range(builder.height)):
    builder.instantiate(clbtile, (x, y))
basic = builder.fill( pattern ).auto_connect().commit()

# advanced type (CLB + BRAM + dffn-CLB)
builder = ctx.build_array("a_advanced", 4, 4, set_as_top = False)
for x, y in product(range(builder.width), range(builder.height)):
    if x == 1:
        if y % 2 == 0:
            builder.instantiate(bramtile, (x, y))
    elif x == 3:
        builder.instantiate(dffntile, (x, y))
    else:
        builder.instantiate(clbtile, (x, y))
advanced = builder.fill( pattern ).auto_connect().commit()

# ============================================================================
# -- Fabric ------------------------------------------------------------------
# ============================================================================
builder = ctx.build_array('top', 18, 18, set_as_top = True)
for x, y in product(range(builder.width), range(builder.height)):
    if x in (0, builder.width - 1) and y in (0, builder.height - 1):
        pass
    elif x == 0:
        builder.instantiate(iotiles[Orientation.west], (x, y))
    elif x == builder.width - 1:
        builder.instantiate(iotiles[Orientation.east], (x, y))
    elif y == 0:
        builder.instantiate(iotiles[Orientation.south], (x, y))
    elif y == builder.height - 1:
        builder.instantiate(iotiles[Orientation.north], (x, y))
    elif x == 5 and y == 5:
        builder.instantiate(picotile, (x, y))
    elif x == 1:
        if y % 4 == 1:
            builder.instantiate(basic, (x, y))
    elif x in (5, 9):
        if y in (1, 13):
            builder.instantiate(basic, (x, y))
    elif x == 13:
        if y % 4 == 1:
            builder.instantiate(advanced, (x, y))
top = builder.fill( pattern ).auto_connect().commit()

# ============================================================================
# -- Workflow ----------------------------------------------------------------
# ============================================================================
Flow(
        Translation(),
        SwitchPathAnnotation(),
        Magic.InsertProgCircuitry(),
        VPRArchGeneration('vpr/arch.xml'),
        VPR_RRG_Generation('vpr/rrg.xml'),
        VerilogCollection('rtl'),
        YosysScriptsCollection('syn'),
        ).run(ctx, Magic.new_renderer(["src"])) # add `src` into file rendering template search path

ctx.pickle("ctx.pkl" if len(sys.argv) < 2 else sys.argv[1])
