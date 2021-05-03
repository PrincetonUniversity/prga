from prga import *
from itertools import product

import logging, sys
logging.getLogger("prga").setLevel(logging.DEBUG)

# -- Meta Parameters ---------------------------------------------------------
N = 10      # number of BLEs per CLB
IOB_CAP = 8 # number of IOBs per IOB Tile
W, H = 8, 8 # 8x8 subarrays
RAM_COL = 6 # BRAM column
X, Y = 5, 4 # number of subarrays in the top-level array
            # top-level size = (X * W + 2) x (Y * H + 2)

# -- Recover from cache if possible ------------------------------------------
try:
    ctx = Context.unpickle("ctx.tmp.pkl")

except FileNotFoundError:
    ctx = Context()

    # -- Routing Resources ---------------------------------------------------
    gbl_clk = ctx.create_global("clk", is_clock = True)
    gbl_clk.bind((0, 1), 0)
    l1 = ctx.create_segment('L1', 64, 1)
    l4 = ctx.create_segment('L4', 24, 4)
    # l16 = ctx.create_segment('L16', 2, 16)

    # -- CLB -----------------------------------------------------------------
    builder = ctx.build_logic_block("clb")
    ble = ctx.primitives["grady18"]

    lin  = len(ble.ports["in"])
    lout = len(ble.ports["out"])

    clk = builder.create_global(gbl_clk,         "south")
    ce  = builder.create_input ("ce",  1,        "west")
    in_ = builder.create_input ("in",  lin * N,  "west")
    out = builder.create_output("out", lout * N, "east")
    cin = builder.create_input ("cin", 1,        "south")

    for i, inst in enumerate(builder.instantiate(ble, "i_ble", N)):
        builder.connect(clk,                         inst.pins["clk"])
        builder.connect(ce,                          inst.pins["ce"])
        builder.connect(in_[lin * i: lin * (i + 1)], inst.pins["in"])
        builder.connect(inst.pins["out"],            out[lout * i: lout * (i + 1)])
        builder.connect(cin,                         inst.pins["cin"],
                vpr_pack_patterns = ["carrychain"])
        cin = inst.pins["cout"]

    cout = builder.create_output("cout", 1, "north")
    builder.connect(cin, cout, vpr_pack_patterns = ["carrychain"])

    clb = builder.commit()
    ctx.create_tunnel("carrychain", cout, clb.ports["cin"], (0, -1))

    # -- IOB -----------------------------------------------------------------
    builder = ctx.build_io_block("iob")
    o = builder.create_input("outpad", 1)
    i = builder.create_output("inpad", 1)
    builder.connect(builder.instances['io'].pins['inpad'], i)
    builder.connect(o, builder.instances['io'].pins['outpad'])
    iob = builder.commit()

    # -- BRAM ----------------------------------------------------------------
    builder = ctx.build_logic_block("bram", 1, 2)
    inst = builder.instantiate(
            ctx.create_multimode_memory(
                9, 64,              # 512x64 RAM IP
                addr_width = 12),   # up to 4K x 8b configuration
            "i_ram")
    builder.connect(builder.create_global(gbl_clk, "south"), inst.pins["clk"])
    builder.connect(builder.create_input("we", 1, "west", (0, 0)), inst.pins["we"])
    builder.connect(builder.create_input("din", len(inst.pins["din"]), "east", (0, 0)), inst.pins["din"])
    builder.connect(builder.create_input("waddr", len(inst.pins["waddr"]), "west", (0, 0)), inst.pins["waddr"])
    builder.connect(builder.create_input("raddr", len(inst.pins["waddr"]), "west", (0, 1)), inst.pins["raddr"])
    builder.connect(inst.pins["dout"], builder.create_output("dout", len(inst.pins["dout"]), "east", (0, 1)))
    bram = builder.commit()

    # -- Tiles ---------------------------------------------------------------
    iotiles = {ori: ctx.build_tile(iob, IOB_CAP, name = "tile_io_{}".format(ori.name[0]),
            edge = OrientationTuple(False, **{ori.name: True})).fill( (0.5, 0.5) ).auto_connect().commit()
            for ori in Orientation}
    clbtile = ctx.build_tile(clb).fill( (0.15, 0.25) ).auto_connect().commit()
    bramtile = ctx.build_tile(bram).fill( (0.15, 0.25) ).auto_connect().commit()

    # -- Sub-Arrays ----------------------------------------------------------
    pattern = SwitchBoxPattern.cycle_free
    
    builder = ctx.build_array('subarray', W, H, set_as_top = False)
    for x, y in product(range(builder.width), range(builder.height)):
        if x == RAM_COL:
            if y % 2 == 0:
                builder.instantiate(bramtile, (x, y))
        else:
            builder.instantiate(clbtile, (x, y))
    subarray = builder.fill( pattern ).auto_connect().commit()

    top_width, top_height = X * W + 2, Y * H + 2
    builder = ctx.build_array("top", top_width, top_height, set_as_top = True)
    for x, y in product(range(top_width), range(top_height)):
        if x in (0, top_width - 1) and y in (0, top_height - 1):
            pass
        elif (x in (0, top_width - 1) and 0 < y < top_height - 1) or (y in (0, top_height - 1) and 0 < x < top_width - 1):
            builder.instantiate(
                    iotiles[Orientation.west if x == 0
                        else Orientation.east if x == top_width - 1
                        else Orientation.south if y == 0
                        else Orientation.north],
                    (x, y))
        elif 0 < x < top_width - 1 and 0 < y < top_height - 1 and x % W == 1 and y % H == 1:
            builder.instantiate(subarray, (x, y))
    top = builder.fill( pattern ).auto_connect().commit()

    # -- Generate VPR/Yosys scripts ------------------------------------------
    Flow(
            VPRArchGeneration('vpr/arch.xml'),
            VPR_RRG_Generation('vpr/rrg.xml'),
            YosysScriptsCollection('syn'),
            ).run(ctx)
    ctx.pickle("ctx.tmp.pkl")

# -- Implement Programming Circuitry -----------------------------------------
Flow(
        Materialization('frame', word_width = 8),
        Translation(),
        SwitchPathAnnotation(),
        ProgCircuitryInsertion(),
        VerilogCollection('rtl'),
        ).run(ctx)

ctx.pickle("ctx.pkl" if len(sys.argv) < 2 else sys.argv[1])
