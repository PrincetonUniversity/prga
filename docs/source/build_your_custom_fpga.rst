Build Your Custom FPGA
======================

This tutorial introduces the process of building a custom FPGA.

Describe the architecture
-------------------------

The entry point of PRGA is an `ArchitectureContext` object. It provides all the
API for customizing CLB/IOB structure, describing FPGA layout, and customizing
routing resources. It also manages all generated modules and resources, which
are later used by the RTL-to-bitstream flow.

To create an `ArchitectureContext` object, the type of configuration circuitry
must be chosen first. PRGA now provides one type of configuration
circuitry: :py:mod:`prga.config.bitchain`.

.. code-block:: python

    from prga.api.context import *
    from prga.api.config import *

    width, height = 42, 34

    # create an FPGA with bitchain-type configuration circuitry
    #  - top-level module is named "top"
    #  - the grid size is 42 tiles wide and 34 tiles high
    context = ArchitectureContext('top', width, height, BitchainConfigCircuitryDelegate)

After creating an `ArchitectureContext` object, we can start to describe our
custom FPGA. The first step is to describe the routing resources: wire segments
and global wires. PRGA only supports uni-directional straight wires.

.. code-block:: python
    
    # create global clock
    # the clock is driven by the I/O at tile (0, 1)
    context.create_global('clk', is_clock = True, bind_to_position = (0, 1))

    # create wire segments: name, width, length
    context.create_segment( 'L1', 48,    1)
    context.create_segment( 'L2', 16,    2)
    context.create_segment( 'L4', 8,     4)

Note that ``width`` is the number of the specific type of wire segments in each
routing channel in one direction.

The second step is to describe the CLB/IOB structures. PRGA supports
hierarchical description of CLB/IOB structures. Use
`ArchitectureContext.create_cluster` to create a sub-block cluster,
`ArchitectureContext.create_logic_block` to create a CLB, and
`ArchitectureContext.create_io_block` to create an IOB.

.. code-block:: python
    
    # create IOB
    iob = context.create_io_block('iob')

    # create ports of the IOB
    clkport = iob.create_global(clk)

    #                         port name, port width
    outpad = iob.create_input('outpad',  1)
    inpad = iob.create_output('inpad',   1)

    # an IOB has a built-in sub-instance io
    ioinst = iob.instances['io']

    # instantiate two D-flipflops: module,                         instance name
    iff = iob.instantiate(         context.primitives['flipflop'], 'iff')
    off = iob.instantiate(         context.primitives['flipflop'], 'off')

    # create configurable connections
    iob.connect(clkport,                iff.pins['clk'])
    iob.connect(ioinst.pins['inpad'],   iff.pins['D'])
    iob.connect(iff.pins['Q'],          inpad)
    iob.connect(ioinst.pins['inpad'],   inpad)
    iob.connect(clkport,                off.pins['clk'])
    iob.connect(off.pins['Q'],          ioinst.pins['outpad'])
    iob.connect(outpad,                 ioinst.pins['outpad'])
    iob.connect(outpad,                 off.pins['D'])

After creating an IOB, one or multiple types of tiles can be created. Each type
of tile encapsulates an IOB/CLB and the connection boxes around it.

.. code-block:: python
    
    # create tiles
    iotiles = {}
    for orientation in iter(Orientation):
        if orientation.is_auto:
            continue
        iotiles[orientation] = context.create_tile(
                'io_tile_{}'.format(orientation.name),  # name of the tile
                iob,            # IOB/CLB in the tile
                8,              # number of IOBs in the tile
                orientation)    # on which side of the FPGA the tile can be placed

`Orientation` is an enum with 5 values: `Orientation.north`, `Orientation.east`,
`Orientation.south`, `Orientation.west`, and `Orientation.auto`. Except for the
last value, each value represents a direction, or a side of a tile/array. The
code above creates 4 different tiles with the same IOB, but to be placed on
different edges of the FPGA.

CLBs are created in a similar way, but there are a few key differences. First of
all, for each port created in the CLB, it must be explicitly specified on which
side of the CLB is the port.

.. code-block:: python

    # create CLB
    clb = context.create_logic_block('clb')

    # create ports of the CLB
    clkport = clb.create_global(clk, Orientation.south)
    ceport = clb.create_input('ce', 1, Orientation.south)
    srport = clb.create_input('sr', 1, Orientation.south)
    cin = clb.create_input('cin', 1, Orientation.north)
    for i in range(4):
        # "fraclut6sffc" is a multi-modal primitive specific to the
        # 'bitchain'-type configuration circuitry. It consists of a fractuable
        # 6-input LUT that can be used as two 5-input LUTs, two D-flipflops, and
        # a look-ahead carry chain
        inst = clb.instantiate(context.primitives['fraclut6sffc'], 'cluster{}'.format(i))
        clb.connect(clkport, inst.pins['clk'])
        clb.connect(ceport, inst.pins['ce'])
        clb.connect(srport, inst.pins['sr'])
        clb.connect(clb.create_input('ia' + str(i), 6, Orientation.west), inst.pins['ia'])
        clb.connect(clb.create_input('ib' + str(i), 1, Orientation.west), inst.pins['ib'])
        clb.connect(cin, inst.pins['cin'], pack_pattern = 'carrychain')
        cin = inst.pins['cout']
        clb.connect(inst.pins['oa'], clb.create_output('oa' + str(i), 1, Orientation.east))
        clb.connect(inst.pins['ob'], clb.create_output('ob' + str(i), 1, Orientation.east))
        clb.connect(inst.pins['q'], clb.create_output('q' + str(i), 1, Orientation.east))
    clb.connect(cin, clb.create_output('cout', 1, Orientation.south), pack_pattern = 'carrychain')

    # create tile
    clbtile = context.create_tile('clb_tile', clb)

Direct inter-block connections (`DirectTunnel` s) can be used to create
shortcuts between block pins, which is great for carry chains or other
latency-sensitive connections.

.. code-block:: python

    context.create_direct_tunnel('carrychain', clb.ports['cout'], clb.ports['cin'], (0, 1))

Another key difference of CLB vs IOB is that CLB may be larger than 1 tile. In
this case, not only the side of the edge but also the position must be specified
for the ports.

.. code-block:: python

    # create BRAM block
    bram = context.create_logic_block('bram', 1, 2)
    bram.create_global(clk, Orientation.south, position = (0, 0))
    bram.create_input('addr1', 10, Orientation.west, position = (0, 0))
    bram.create_input('data1', 8, Orientation.west, position = (0, 0))
    bram.create_input('we1', 1, Orientation.west, position = (0, 0))
    bram.create_output('out1', 8, Orientation.east, position = (0, 0))
    bram.create_input('addr2', 10, Orientation.west, position = (0, 1))
    bram.create_input('data2', 8, Orientation.west, position = (0, 1))
    bram.create_input('we2', 1, Orientation.west, position = (0, 1))
    bram.create_output('out2', 8, Orientation.east, position = (0, 1))
    inst = bram.instantiate(context.primitive_library.get_or_create_memory(10, 8, 
        dualport = True), 'ram')

    # auto-connect according to port/pin names
    bram.auto_connect(inst)

    # create tile
    bramtile = context.create_tile('bram_tile', bram)

After describing all block types, we can layout the FPGA hierarchically. Use
`ArchitectureContext.create_array` to create sub-arrays, then use
`Array.instantiate_element` to instantiate tile/sub-arrays and place them into
the grid.

.. code-block:: python

    # create sub-array
    subarray = context.create_array('subarray', 5, 4)
    for x, y in product(range(5), range(4)):
        if x == 2:
            if y % 2 == 0:
                subarray.instantiate_element(bramtile, (x, y))
        else:
            subarray.instantiate_element(clbtile, (x, y))

    # top-level array
    for x in range(width):
        for y in range(height):
            if x == 0:
                if y > 0 and y < height - 1:
                    context.top.instantiate_element(iotiles[Orientation.west], (x, y))
            elif x == width - 1:
                if y > 0 and y < height - 1:
                    context.top.instantiate_element(iotiles[Orientation.east], (x, y))
            elif y == 0:
                context.top.instantiate_element(iotiles[Orientation.south], (x, y))
            elif y == height - 1:
                context.top.instantiate_element(iotiles[Orientation.north], (x, y))
            elif x % 5 == 1 and y % 4 == 1:
                context.top.instantiate_element(subarray, (x, y))

Auto-complete the architecture, generate RTL and other files
------------------------------------------------------------

All routing resources/connections are fully customizable, but we'll skip that in
this tutorial, and let PRGA auto-complete them.

PRGA adopts a pass-based flow to complete, modify, optimize the FPGA
architecture as well as generate all files for the architecture. A `Flow` object
is used to manage and run all the passes.

.. code-block:: python

    from prga.api.flow import *

    flow = Flow((
        # this pass automatically creates, places and populates connection/switch boxes
        CompleteRoutingBox(BlockFCValue(BlockPortFCValue(0.25), BlockPortFCValue(0.1))),

        # this pass implements the configurable connections with switches
        CompleteSwitch(),

        # this pass automatically connects the pins/ports of blocks, routing
        # boxes, tiles and arrays
        CompleteConnection(),

        # this pass generates the RTL
        GenerateVerilog('rtl'),

        # this pass injects bitchain-style configuration circuitry into the
        # architecture
        InjectBitchainConfigCircuitry(),

        # this pass generates all the files needed to run VPR
        GenerateVPRXML('vpr'),

        # this pass materializes all the modules, connections into physical stuff
        CompletePhysical(),

        # this pass is an optional pass but highly recommended. It makes sure the
        # write-enable is deactivated when a BRAM is not used
        ZeroingBRAMWriteEnable(),

        # this pass is an optional pass but highly recommended, especially if
        # support for post-implementation simulation is needed. It makes sure
        # all block pins are connected to constant-zero when not used,
        # preventing combinational loops during simulation
        ZeroingBlockPins(),

        # this pass generates all the files needed to run Yosys
        GenerateYosysResources('syn'),
        ))

The order of the passes don't matter, because the `Flow` object inspects and
resolves the dependency between the passes and orders them correspondingly.

After creating the `Flow` object and adding all the passes to it, use `Flow.run`
to run the flow on an `ArchitectureContext` object.

.. code-block:: python
    
    # run the flow
    flow.run(context)

In addition, the `ArchitectureContext` object can be serialized and stored on
disk with the Python module
`pickle <https://docs.python.org/3/library/pickle.html>`_ . This serialized
object can be used by other Python scripts to inspect or further improve the
architecture. Some good examples can be found in the :py:mod:`prga_tools`
module.

.. code-block:: python

    # create a pickled object
    context.pickle('ctx.pickled')
