from prga import *
from itertools import product, chain

import logging
logging.getLogger("prga").setLevel(logging.DEBUG)

N = 10                      # FLE8 per CLB
CHAIN_WIDTH, PHIT_WIDTH = 1, 8
W_LOGIC, H_LOGIC = 10, 10   # logic region size
MEM_COL = 5
NUM_IOB_PER_TILE = 8

# DO NOT CHANGE `N_LOGIC` (#subarrays vertically)
M_LOGIC, N_LOGIC = 4, 4     # regions in each dimension

try:
    # read from cached context if possible
    ctx = Context.unpickle("ctx.tmp.pkl")

except FileNotFoundError:
    ctx = Context()

    # ============================================================================
    # -- Routing Resources -------------------------------------------------------
    # ============================================================================
    glb_clk = ctx.create_global("clk", is_clock = True)
    glb_clk.bind((0, 21), 0)
    ctx.create_segment("L4", 32, 4)
    ctx.create_segment("L16", 1, 16)

    # ============================================================================
    # -- Primitives --------------------------------------------------------------
    # ============================================================================

    # multi-mode memory: 512x64b, 1K32b, 2K16b, 4K8b
    memory = ctx.create_multimode_memory(9, 64, addr_width = 12)

    # ============================================================================
    # -- Blocks ------------------------------------------------------------------
    # ============================================================================

    # -- CLB ---------------------------------------------------------------------
    builder = ctx.build_logic_block("clb")

    clk = builder.create_global(glb_clk,                            Orientation.south)
    in_ = builder.create_input ("in",
            N * len(ctx.primitives["grady18"].ports["in"]) // 2,    Orientation.east)
    ce = builder.create_input  ("ce",   1,                          Orientation.east)
    ci  = builder.create_input ("ci",   1,                          Orientation.south)
    out = builder.create_output("out",  N * 2,                      Orientation.east)
    co  = builder.create_output("co",   1,                          Orientation.north)

    xbar_i, xbar_o = [], []
    xbar_i.extend(in_)

    for i, inst in enumerate(builder.instantiate(ctx.primitives["grady18"], "i_cluster", N)):
        builder.connect(clk,                inst.pins['clk'])
        builder.connect(ce,                 inst.pins["ce"])
        builder.connect(inst.pins['out'],   out[(l := len(inst.pins["out"])) * i: l * (i + 1)])
        builder.connect(ci,                 inst.pins["cin"],
                vpr_pack_patterns = ["carrychain"])

        xbar_i.extend(inst.pins["out"])
        xbar_o.extend(inst.pins["in"])
        ci = inst.pins["cout"]

    builder.connect(ci, co, vpr_pack_patterns = ["carrychain"])

    # crossbar: 50% connectivity
    for i, sink in enumerate(xbar_o):
        for j, src in enumerate(xbar_i):
            if j % 2 == i % 2:
                builder.connect(src, sink)

    clb = builder.commit()
    ctx.create_tunnel("carrychain", clb.ports["co"], clb.ports["ci"], (0, -1))

    # -- IOB ---------------------------------------------------------------------
    builder = ctx.build_io_block("iob")

    o = builder.create_input("outpad", 1)
    i = builder.create_output("inpad", 1)

    builder.connect(builder.instances['io'].pins['inpad'],  i)
    builder.connect(o,                                      builder.instances['io'].pins['outpad'])

    iob = builder.commit()

    # -- BRAM --------------------------------------------------------------------
    builder = ctx.build_logic_block("bram", 1, 2)
    inst = builder.instantiate(memory, "i_ram")

    builder.connect(
            builder.create_global(glb_clk, Orientation.south),
            inst.pins["clk"])
    builder.connect(
            builder.create_input("we", len(inst.pins["we"]), Orientation.east, (0, 0)),
            inst.pins["we"])

    # interleave block inputs/outputs to improve routability
    for y in range(2):
        for p in ["raddr", "waddr", "din"]:
            bits = [b for i, b in enumerate(inst.pins[p]) if i % 2 == y]
            builder.connect(
                    builder.create_input("{}x{}".format(p, y), len(bits), Orientation.east, (0, y)),
                    bits)
        bits = [b for i, b in enumerate(inst.pins["dout"]) if i % 2 == y]
        builder.connect(
                bits,
                builder.create_output("doutx{}".format(y), len(bits), Orientation.east, (0, y)))

    bram = builder.commit()

    # ============================================================================
    # -- Tiles -------------------------------------------------------------------
    # ============================================================================
    iotiles = {}
    for edge in Orientation:
        iotiles[edge] = ctx.build_tile(iob, NUM_IOB_PER_TILE,
                edge = OrientationTuple(False, **{edge.name: True}),
                name = "tile_iob_{}".format(edge.name),
                ).fill( (.15, .15) ).auto_connect().commit()
    clbtile = ctx.build_tile(clb).fill( (0.055, 0.1) ).auto_connect().commit()
    bramtile = ctx.build_tile(bram).fill( (0.15, 0.15) ).auto_connect().commit()

    # ============================================================================
    # -- Subarrays ---------------------------------------------------------------
    # ============================================================================
    pattern = SwitchBoxPattern.cycle_free

    # -- LOGIC Subarray ----------------------------------------------------------
    builder = ctx.build_array("subarray", W_LOGIC, H_LOGIC, set_as_top = False)
    for x, y in product(range(builder.width), range(builder.height)):
        if x == MEM_COL:
            if y % 2 == 0:
                builder.instantiate(bramtile, (x, y))
        elif not (x == 0 and y == 0):   # reserved for pktchain router
            builder.instantiate(clbtile, (x, y))
    logic = builder.fill( pattern ).auto_connect().commit()

    # ============================================================================
    # -- Fabric ------------------------------------------------------------------
    # ============================================================================
    builder = ctx.build_array("top", M_LOGIC * W_LOGIC + 2, N_LOGIC * H_LOGIC + 2, set_as_top = True)
    for x, y in product(range(M_LOGIC), range(N_LOGIC)):
        builder.instantiate(logic, (x * W_LOGIC + 1, y * H_LOGIC + 1))
    for x in range(M_LOGIC * W_LOGIC):
        builder.instantiate(iotiles[Orientation.south], (x + 1, 0))
        builder.instantiate(iotiles[Orientation.north], (x + 1, N_LOGIC * H_LOGIC + 1))
    for y in range(N_LOGIC * H_LOGIC):
        builder.instantiate(iotiles[Orientation.west],  (0,                     y + 1))
        builder.instantiate(iotiles[Orientation.east],  (M_LOGIC * W_LOGIC + 1, y + 1))
    top = builder.fill( pattern ).auto_connect().commit()

    Flow(
        VPRArchGeneration("vpr/arch.xml"),
        VPR_RRG_Generation("vpr/rrg.xml"),
        YosysScriptsCollection("syn"),
        ).run(ctx)

    ctx.pickle("ctx.tmp.pkl")

# ============================================================================
# -- Configuration Chain Injection -------------------------------------------
# ============================================================================
def iter_instances(module):
    if module.name == "tile_clb":
        yield module.instances[0]
        yield module.instances[Orientation.east, 0]
    elif module.name.startswith("tile_iob_"):
        for i in range(NUM_IOB_PER_TILE):
            yield module.instances[i]
        for ori in Orientation:
            if i := module.instances.get( (ori, 0) ):
                yield i
    elif module.name == "tile_bram":
        yield module.instances[Orientation.east, 0]
        yield module.instances[Orientation.east, 1]
        yield module.instances[0]
    elif module.name == "subarray":
        for y in range(module.height):
            for x in range(module.width):
                if x > 0 and (i := module.instances.get( ((x, y), Corner.southwest) )): yield i
                if i := module.instances.get( (x, y) ): yield i
                if i := module.instances.get( ((x, y), Corner.southeast) ): yield i
            for x in reversed(range(module.width)):
                if i := module.instances.get( ((x, y), Corner.northeast) ): yield i
                if x > 0 and (i := module.instances.get( ((x, y), Corner.northwest) )): yield i
        for y in reversed(range(module.height)):
            if (i := module.instances.get( ((0, y), Corner.northwest) )): yield i
            if (i := module.instances.get( ((0, y), Corner.southwest) )): yield i
        yield Pktchain.TERMINATE_LEAF
    elif module.name == "top":
        # go in a circle to program all IOBs and their neighbouring switch boxes
        if i:= module.instances.get( ((0, 0), Corner.northeast) ): yield i
        for y in range(1, N_LOGIC * H_LOGIC + 1):
            if i := module.instances.get( ((0, y), Corner.southeast) ): yield i
            if i := module.instances.get(  (0, y)                    ): yield i
            if i := module.instances.get( ((0, y), Corner.northeast) ): yield i
        # wrap up and insert leaf router
        yield Pktchain.TERMINATE_LEAF
        if i:= module.instances.get( ((0, N_LOGIC * H_LOGIC + 1), Corner.southeast) ): yield i
        for x in range(1, M_LOGIC * W_LOGIC + 1):
            if i := module.instances.get( ((x, N_LOGIC * H_LOGIC + 1), Corner.southwest) ): yield i
            if i := module.instances.get(  (x, N_LOGIC * H_LOGIC + 1)                    ): yield i
            if i := module.instances.get( ((x, N_LOGIC * H_LOGIC + 1), Corner.southeast) ): yield i
        # wrap up and insert leaf router
        yield Pktchain.TERMINATE_LEAF
        if i:= module.instances.get( ((M_LOGIC * W_LOGIC + 1, N_LOGIC * H_LOGIC + 1), Corner.southwest) ): yield i
        for y in reversed(range(1, N_LOGIC * H_LOGIC + 1)):
            if i := module.instances.get( ((M_LOGIC * W_LOGIC + 1, y), Corner.northwest) ): yield i
            if i := module.instances.get(  (M_LOGIC * W_LOGIC + 1, y)                    ): yield i
            if i := module.instances.get( ((M_LOGIC * W_LOGIC + 1, y), Corner.southwest) ): yield i
        # wrap up and insert leaf router
        yield Pktchain.TERMINATE_LEAF
        if i:= module.instances.get( ((M_LOGIC * W_LOGIC + 1, 0), Corner.northwest) ): yield i
        for x in reversed(range(1, M_LOGIC * W_LOGIC + 1)):
            if i := module.instances.get( ((x, 0), Corner.northeast) ): yield i
            if i := module.instances.get(  (x, 0)                    ): yield i
            if i := module.instances.get( ((x, 0), Corner.northwest) ): yield i
        # wrap up and insert leaf router
        yield Pktchain.TERMINATE_LEAF
        # wrap up branches and attach to the main chunk
        yield Pktchain.TERMINATE_BRANCH

        for x in range(M_LOGIC):
            yield module.instances[ x * W_LOGIC + 1, 0 * H_LOGIC + 1 ]
            yield module.instances[ x * W_LOGIC + 1, 2 * H_LOGIC + 1 ]
            yield module.instances[ x * W_LOGIC + 1, 3 * H_LOGIC + 1 ]
            yield module.instances[ x * W_LOGIC + 1, 1 * H_LOGIC + 1 ]
            yield Pktchain.TERMINATE_BRANCH
    else:
        for i in module.instances.values():
            yield i

Flow(
        Materialization('pktchain',
            chain_width = CHAIN_WIDTH,
            phit_width = PHIT_WIDTH,
            router_fifo_depth_log2 = 8),
        Translation(),
        SwitchPathAnnotation(),
        ProgCircuitryInsertion(iter_instances = iter_instances),
        VerilogCollection("rtl", "include"),
        ).run(ctx)

ctx.pickle("ctx.pkl")
