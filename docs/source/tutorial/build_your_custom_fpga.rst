
Build Your Custom FPGA
======================

This tutorial introduces how to build a custom FPGA. The full script can be
found at
`examples/fpga/scanchain/fle6_N2_mem2K_8x8/build.py`_.

.. _examples/fpga/scanchain/fle6_N2_mem2K_8x8/build.py: https://github.com/PrincetonUniversity/prga/blob/release/examples/fpga/scanchain/fle6_N2_mem2K_8x8/build.py

Describe the architecture
-------------------------

To start building an FPGA, we first need to create a `Context` object. A
`Context` object provides a set of API for describing CLB/IOB structure, FPGA
layout and routing resources. It also stores and manages all created/generated
modules and other information about the FPGA, which are later used by the
RTL-to-bitstream flow.

.. code-block:: python

    from prga import *
    from itertools import product
    
    import sys

    # create a new context
    ctx = Context()

After creating the `Context` object, we can start to describe our custom FPGA.
Here, we first describe the routing resources in the FPGA: the routing wire
segments and the global wires.

.. code-block:: python
    
    # create global clock
    gbl_clk = ctx.create_global("clk", is_clock = True)

    # assign an IOB to drive the clock
    #   the first argument is the position of a tile, and the second argument is
    #   the subtile ID in that tile
    gbl_clk.bind( (0, 1), 0)

    # create wire segments: name, width, length
    ctx.create_segment(     'L2', 20,    2)

Note that ``width`` is the number of the specific type of wire segments in each
routing channel in one direction. In the example above, each horizontal channel
contains 80 tracks:

- 20 ``L2`` tracks that run from west to east, starting from the current tile
- 20 ``L2`` tracks that run from west to east, starting from 1 tiles west to the current tile
- 20 ``L2`` tracks that run from east to west, starting from the current tile
- 20 ``L2`` tracks that run from east to west, starting from 1 tiles east to the current tile

Before describing the CLB/IOBs in our custom FPGA, we can add custom logic
elements (or primitive cells, hardwired IP blocks, etc.) to our `Context` and
use them when we describe CLB/IOBs. For example, PRGA provides an API to create
a memory module:

.. code-block:: python
    
    # create a memory primitive: addr width,   data width
    memory = ctx.create_memory(  8,            8 )

PRGA also provides API for adding and using arbitrary Verilog modules in the FPGA,
for example `Context.build_primitive`. Multi-modal primitives are also supported
by calling `Context.build_multimode`.

::
    
    TODO: Add tutorials for adding custom Verilog modules and multi-modal
    primitives.

Then, we can describe the CLB/IOB structures in our custom FPGA. Use
`Context.build_io_block` or `Context.build_logic_block` to create an
`IOBlockBuilder` or `LogicBlockBuilder` object, then use the builder
object to build the desired block. After describing
the desired block, use the ``commit`` method of the builder to commit
the module into the `Context` database.

In this example we'll be using ``FLE6`` as our basic logic element.
``FLE6`` contains one fracturable LUT6, one hard adder, and two flipflops.
The fracturable LUT6 may be used as two LUT5s with shared inputs.

.. code-block:: python

    # =======================================================================
    # -- CLB ----------------------------------------------------------------
    # =======================================================================

    # create CLB builder
    builder = ctx.build_logic_block("clb")

    # create a block input that is directly connected to a global wire and not
    # routable
    clk = builder.create_global(gbl_clk, Orientation.south)

    # create other block inputs/outputs
    #                         name, width,      on which side of the block is the port
    in_  = builder.create_input ("in",  12, Orientation.west)
    out  = builder.create_output("out",  4, Orientation.east)
    cin  = builder.create_input ("cin",  1, Orientation.south)
    cout = builder.create_output("cout", 1, Orientation.north)

    # Instantiate logic primitives
    #                                            module to be instantiated, name,        number of instances
    for i, inst in enumerate(builder.instantiate(ctx.primitives["fle6"],    "i_cluster", 2)):
        
        # connect nets:  driver (source) nets,  drivee (sink) nets
        builder.connect( clk,                   inst.pins['clk'] )
        builder.connect( in_[6*i : 6*(i+1)],    inst.pins['in']  )
        builder.connect( inst.pins['out'],      out[2*i : 2*(i+1)] )

        # 'vpr_pack_pattern' is a keyword-only argument. See
        # "https://docs.verilogtorouting.org/en/latest/arch/reference/#tag-%3Cpack_patternname="
        # for more information
        builder.connect( cin,                inst.pins['cin'], vpr_pack_patterns = ['carrychain'] )

        cin = inst.pins["cout"]

    builder.connect(cin, cout, vpr_pack_patterns = ["carrychain"])

    # Commit the described CLB. The module is now accessible as `ctx.blocks["clb"]`
    clb = builder.commit()

    # =======================================================================
    # -- IOB ----------------------------------------------------------------
    # =======================================================================

    # create IOB builder
    #   An instance named "io" is automatically added into the IOB. This is the
    #   I/O pad for off-chip connections. By default, a bi-directional pad that
    #   can be configured as input or output is instantiated.
    builder = ctx.build_io_block("iob")

    # create block inputs/outputs
    o = builder.create_input("outpad", 1)
    i = builder.create_output("inpad", 1)

    # connect 
    builder.connect(builder.instances['io'].pins['inpad'], i)
    builder.connect(o, builder.instances['io'].pins['outpad'])

    # Commit the IOB. The module is also accessible as `ctx.blocks["iob"]`
    iob = builder.commit()

    # =======================================================================
    # -- BRAM ---------------------------------------------------------------
    # =======================================================================

    # Here we specify the width and height of this block (in number of tiles)
    builder = ctx.build_logic_block("bram", 1, 2)

    # Instantiate the memory module
    inst = builder.instantiate(memory, "i_ram")

    # create and connect ports/pins
    builder.connect( builder.create_global(gbl_clk, Orientation.south),
                     inst.pins["clk"])
    builder.connect( builder.create_input("we", 1, Orientation.west, (0, 0)),
                     inst.pins["we"])
    builder.connect( builder.create_input("waddr", len(inst.pins["waddr"]), Orientation.west, (0, 0)),
                     inst.pins["waddr"])
    builder.connect( builder.create_input("din", len(inst.pins["din"]), Orientation.east, (0, 0)),
                     inst.pins["din"])
    builder.connect( builder.create_input("raddr", len(inst.pins["raddr"]), Orientation.west, (0, 1)),
                     inst.pins["raddr"])
    builder.connect( inst.pins["dout"],
                     builder.create_output("dout", len(inst.pins["dout"]), Orientation.east, (0, 1)))

    # commit the BRAM block. The module is also accessible as `ctx.blocks["bram"]`
    bram = builder.commit()

Direct inter-block connections (`DirectTunnel`) can be defined using
`Context.create_tunnel`. This is often used for carrychains where connections
are hardwired, i.e., not routable, but faster.

.. code-block:: python

    # Create a direct inter-block connection
    #                 name of the tunnel, from port,         to port,          relative position
    ctx.create_tunnel("carrychain",       clb.ports["cout"], clb.ports["cin"], (0, -1))

    #   "relative position" is the position of the destination port relative to
    #   the source port (not the blocks)

After describing all the blocks we want, we can describe the tiles for each
block. A tile contains one or more block instances and the connection boxes
around them.

PRGA supports full customization of the connection/switch boxes. In this
tutorial, we will let PRGA to generate the connections for us. This is done
by calling `TileBuilder.fill` and `ArrayBuilder.fill` methods.

.. code-block:: python

    # Create 4 different IO tiles, one per edge
    iotiles = {}
    for ori in Orientation:
        builder = ctx.build_tile(iob,                                   # block to be instantiated in this tile
                4,                                                      # number of block instances in this tile
                name = "t_io_{}".format(ori.name[0]),                   # name of the tile
                edge = OrientationTuple(False, **{ori.name: True}))     # on which edge of the FPGA

        # auto-generate connection boxes and fill connection box patterns
        #              default input FC value,  default output FC value
        builder.fill( (1.,                      1.) )

        #   FC values affect how many tracks each block pin is connected to
        #
        #   In this example we use ratio-based FC values, so "1." means 100%
        #   connection, "0.4" means 40% connection. The bigger the FC values,
        #   the more routable the FPGA is. However, bigger FC values also result
        #   in more hardware resources, and may slow down the FPGA itself.

        # automatically connect ports/pins in the tile
        builder.auto_connect()

        # commit the tile
        iotiles[ori] = builder.commit()

    # Concatenate build, fill, auto-connect and commit
    clbtile = ctx.build_tile(clb).fill( (0.4, 0.25) ).auto_connect().commit()
    bramtile = ctx.build_tile(bram).fill( (0.4, 0.25) ).auto_connect().commit()

After describing all the tiles, we can describe arrays/sub-arrays. An array
is a 2D mesh. Each tile in the mesh contains one tile instance and up to four
switch boxes, one per corner. Tiles larger than 1x1 will occupy adjacent tiles
and switch box slots:

.. code-block:: python

    # Select a switch box pattern. Supported values are:
    #   wilton, universal, subset, cycle_free
    pattern = SwitchBoxPattern.wilton
    
    # Create an array builder
    #                         name,       width, height
    builder = ctx.build_array('subarray', 4,     4,     set_as_top = False)
    for x, y in product(range(builder.width), range(builder.height)):
        if x == 2:
            if y % 2 == 0:
                builder.instantiate(bramtile, (x, y))
        else:
            builder.instantiate(clbtile, (x, y))

    # Commit the subarray
    subarray = builder.fill( pattern ).auto_connect().commit()

    # Create the top-level array builder
    builder = ctx.build_array('top', 10, 10, set_as_top = True)
    for x, y in product(range(builder.width), range(top_height)):
        # leave the corners empty
        if x in (0, builder.width - 1) and y in (0, builder.height - 1):
            pass

        # fill edges with IO tiles
        elif x == 0:
            builder.instantiate(iotiles[Orientation.west], (x, y))
        elif x == builder.width - 1:
            builder.instantiate(iotiles[Orientation.east], (x, y))
        elif y == 0:
            builder.instantiate(iotiles[Orientation.south], (x, y))
        elif y == builder.height - 1:
            builder.instantiate(iotiles[Orientation.north], (x, y))

        # subarrays
        elif x % 4 == 1 and y % 4 == 1:
            builder.instantiate(subarray, (x, y))

    # commit the top-level array
    top = builder.fill( pattern ).auto_connect().commit()

Generate Yosys and VPR scripts
------------------------------------------------------------

After describing the desired FPGA architecture, we can generate the scripts for
our RTL-to-bitstream flow.
Specifically, PRGA generates the `Yosys`_ scripts for synthesizing an
application for the custom FPGA, and the `VPR`_ scripts for placing and routing
the synthesized application.

.. _Yosys: http://www.clifford.at/yosys
.. _VPR: https://verilogtorouting.org/

PRGA adopts a pass-based flow to complete, modify, optimize the FPGA
architecture as well as generate all files for the architecture. A `Flow` object
is used to manage and run all the passes. It also checks and resolves the
dependences between the passes.

.. code-block:: python

    flow = Flow(

        # This pass generates the architecture specification for VPR to place
        # and route designs onto this FPGA
        VPRArchGeneration("vpr/arch.xml"),

        # This pass generates the routing resource graph specification for VPR
        # to place and route designs onto this FPGA
        VPR_RRG_Generation("vpr/rrg.xml"),

        # This pass analyzes the primitives in the FPGA and generates synthesis
        # script for Yosys
        YosysScriptsCollection(r, "syn"),
        )

    # Run the flow on our context
    flow.run(ctx)

After this step, PRGA should generate the following files:

.. code-block:: bash

    +- syn/
    |   +- m_adder.lib.v        # behavioral model for logic primitive "adder"
    |   +- m_adder.techmap.v    # technology mapping rules for logic primitve "adder"
    |   |
    |   +- m_ram_1r1w.lib.v     # behavioral model for the block RAM primitive
    |   +- memory.techmap.v     # technology mapping rules for the block RAM primitive
    |   +- bram.rule            # block RAM inference rules for Yosys
    |   |
    |   +- read_lib.tcl         # Yosys script for reading in the primitives as lib cells
    |   +- synth.tcl            # Yosys script for synthesizing an application
    |
    +- vpr/
        +- arch.xml             # VPR's architecture description
        +- rrg.xml              # VPR's routing resource graph

Auto-complete the architecture, generate RTL, and serialize the context
-----------------------------------------------------------------------

.. PRGA uses `Jinja2`_ for generating most files. `Jinja2`_ is a templating
   language/framework for Python. It is fast, lightweight, and also compatible with
   plain text.

.. _Jinja2: https://jinja.palletsprojects.com/en/2.11.x/

We have not yet chosen the programming protocol for the custom FPGA until this
point in our script.
This is intended to facilitate early and fast design-space exploration before
diving into the vast physical optimization space.

To choose the programming protocol and then implement the abstract FPGA
architecture with synthesizable RTL, run the following pases:

.. code-block:: python

    flow = Flow(

        # This pass chooses the programming protocol, and adds protocol-specific
        # designs into the context
        Materialization("scanchain", chain_width = 1),

        # This pass converts user-defined modules to Verilog modules
        Translation(),

        # Analyze how configurable connections are implemented with switches
        SwitchPathAnnotation(),

        # This pass inserts configuration circuitry into the FPGA
        ProgCircuitryInsertion(),

        # This pass create Verilog rendering tasks in the renderer.
        VerilogCollection('rtl'),
        )

    # Run the flow on our context
    flow.run(ctx)

After running the flow, all the models and information about our FPGA are stored
in the context, and all the file are generated. As the final step, we make a
persistent copy of the context by `pickling`_ it onto the disk. This pickled
database will be used by the FPGA implementation toolchain, e.g. the bitstream
assembler.

.. _pickling: https://docs.python.org/3/library/pickle.html

.. code-block:: python

    # Pickle the context
    ctx.pickle("ctx.pkl")

Run the script
--------------

To run this Python script, you first need to enable the PRGA virtual environment
(see :ref:`quickstart:Run a Quick Test`).
Then, you may either run the script directly with Python, or run ``make`` inside
the ``examples/fpga/scanchain/fle6_N2_mem2K_8x8`` directory.
You may also copy the script to any directory you like, and simply execute
``python build.py`` in there.
