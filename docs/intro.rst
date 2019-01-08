Introduction
============

Princeton Reconfigurable Gate Array (PRGA) is a customizable, scalable,
versatile, extensible open-source framework for building and using custom
FPGAs.

Prerequisites
-------------

Tools
^^^^^

PRGA is dependent on the following third-party tools:

* `CMake <https://cmake.org/>`_ >= 3.5
* `Google Proto Buffer <https://developers.google.com/protocol-buffers/>`_
* `Verilog-to-Routing <https://verilogtorouting.org/>`_
* `Yosys <http://www.clifford.at/yosys/>`_
* `Icarus Verilog <http://iverilog.icarus.com/>`_

Python
^^^^^^

PRGA works with Python 2.7.x. Required Python modules are:

* `networkx <https://networkx.github.io/>`_
* `jinja2 <http://jinja.pocoo.org/docs/2.10/>`_
* `protobuf <http:https://pypi.org/project/protobuf/>`_
* `mmh3 <https://pypi.org/project/mmh3/>`_
* `lxml <https://lxml.de/>`_
* `enum34 <https://pypi.org/project/enum34/>`_
* `xmltodict <https://github.com/martinblech/xmltodict>`_
* `hdlparse <https://kevinpt.github.io/hdlparse/>`_

Libraries
^^^^^^^^^

The PRGA Bitgen is dependent on the following libraries:

* `Boost Graph Library
  <https://www.boost.org/doc/libs/1_69_0/libs/graph/doc/index.html>`_
* `Expat <https://libexpat.github.io/>`_

Installation
------------

Note that the PRGA repo contains sub-modules. Run the following commands after
cloning the git repo to download the sub-modules:

.. code-block:: bash

    cd /path/to/prga                        # cd to the root folder of PRGA
    git submodule update --init --recursive # fetch sub-modules

After downloading the sub-modules and meeting the prerequisites, run the
following commands to build PRGA:

.. code-block:: bash
    
    cd /path/to/prga                        # cd to the root folder of PRGA
    mkdir build && cd build                 # that's where we will build everything
    cmake3 ..                               # run CMake
    make                                    # run Make

Examples
--------

Examples are provided in the ``examples/`` directory. Each example is a
complete use case of PRGA, including building a custom FPGA, running
Verilog-to-bitstream flow for a target design, then verifying the implemented
target design by simulating the RTL of the FPGA with the generated bitstream.
Each example is organized in the following hierarchy:

* ``build.py``: the Python script for building the FPGA
* ``{example}.v``: the target design
* ``{example}_host.v``: the test host for the target design
* ``io.pads``: the IO binding file
* ``build/``:
    * ``Makefile``: the Make script

Follow the commands below to run an example:

.. code-block:: bash
    
    cd /path/to/prga                        # cd to the root folder of PRGA
    source envscr/general.settings.sh       # set up environment
    cd examples/small/build                 # cd to one of the example directories
    make                                    # this will run all the way to post-implementation simulation

PRGA Builder
------------

The PRGA Builder is the front end of PRGA. It consists of two parts, the
architecture description API, and the building flow.

Architecture description API
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The PRGA Builder uses a central ``ArchitectureContext`` object to wrap all
APIs for describing the custom FPGA, as well as hold all data relevent to the
custom FPGA. In most cases where a Python script only builds one custom FPGA,
a single ``ArchitectureContext`` object is enough. However, using multiple
``ArchitectureContext`` objects in one script is supported.

.. code-block:: python
    
    from prga.context import *

    width = 12
    height = 12
    ctx = ArchitectureContext(width = width, height = height)

After creating the ``ArchitectureContext``, we can start to describe our desired
FPGA. The first step is to describe the routing resources in the desired FPGA.
Use ``ctx.create_segment`` to create routing wire segments. Use
``ctx.create_global`` to create global wires.

.. code-block:: python
    
    ctx.create_segment(name = 'L1', width = 10, length = 1)
    ctx.create_segment(name = 'L2', width = 2, length = 2)

    ctx.create_global(name = 'clk', is_clock = True)

The second step is to describe the CLB/IOB structures. Use
``ctx.create_logic_block`` to create CLBs. This method returns a
``LogicBlock`` object, which wraps all APIs for describing the created CLBs.

.. code-block:: python

    clb = ctx.create_logic_block(name = 'CLB')

After creating the CLB, use ``clb.add_input``, ``clb.add_output``, and
``clb.add_clock`` to add ports; use ``clb.add_instance`` to add logic elements
(also called primitives); use ``clb.add_connections`` to add configurable
intra-block connections. Note that all CLBs are rectangle-shaped, so we need
to use enum class ``Side`` to describe which side of the rectangle the ports
are on.

.. code-block:: python

    # Add ports to this CLB
    clb.add_input (name = 'I',   width = 2, side = Side.left)
    clb.add_output(name = 'O',   width = 1, side = Side.right)
    clb.add_clock (name = 'CLK',            side = Side.bottom, global_ = 'clk')

    # Add logic elements (primitives) to this CLB
    clb.add_instance(name = 'LUT', model = 'lut2')
    clb.add_instance(name = 'FF',  model = 'flipflop')

    # Add configurable intra-block connections to this CLB
    clb.add_connections(
            sources = clb.instances['LUT'].pins['out'],
            sinks = clb.instances['FF'].pins['D'],
            pack_pattern = True)
    clb.add_connections(
            sources = clb.instances['LUT'].pins['out'],
            sinks = clb.ports['O'])
    clb.add_connections(
            sources = clb.ports['CLK'],
            sinks = clb.instances['FF'].pins['clk'])
    clb.add_connections(
            sources = clb.instances['FF'].pins['Q'],
            sinks = clb.ports['O'])
    clb.add_connections(
            sources = clb.ports['I'],
            sinks = clb.instances['LUT'].pins['in'])

Similar to creating CLBs, use ``ctx.create_io_block`` to create IOBs.
Typically, four types of IOBs are needed on four sides of the top-level gate
array.

.. code-block:: python

    # Create some IOBs
    for side in Side.all():
        io = ctx.create_io_block(name = 'IO_{}'.format(side.name.upper()),
                capacity = 1)

        # Add ports to this IOB
        io.add_input (name = 'GPO', width = 1, side = side.opposite)
        io.add_output(name = 'GPI', width = 1, side = side.opposite)

        # Add configurable intra-block connections to this IOB
        io.add_connections(
                sources = io.ports['GPO'],
                sinks = io.instances['extio'].pins['outpad'])
        io.add_connections(
                sources = io.instances['extio'].pins['inpad'],
                sinks = io.ports['GPI'])

After creating the CLB/IOBs, use ``ctx.array.place_blocks`` to place the blocks
into the array.

.. code-block:: python
    
    # Create FPGA layout by placing blocks
    ctx.array.place_blocks(block = 'CLB', x = 1, endx = width - 1, y = 1, endy = height - 1)
    ctx.array.place_blocks(block = 'IO_LEFT', x = 0, y = 1, endy = height - 1)
    ctx.array.place_blocks(block = 'IO_RIGHT', x = width - 1, y = 1, endy = height - 1)
    ctx.array.place_blocks(block = 'IO_BOTTOM', x = 1, endx = width - 1, y = 0)
    ctx.array.place_blocks(block = 'IO_TOP', x = 1, y = height - 1, endx = width - 1)

After creating the layout, use ``{global wire}.bind`` to bind the global wire to
a specific IOB.

.. code-block:: python

    # Bind global wire to a specific IOB
    ctx.globals['clk'].bind(x = 0, y = 1, subblock = 0)

Use ``ctx.array.populate_routing_channels`` to populate all the routing channels
using the routing resources described above. Then use
``ctx.array.populate_routing_switches`` to create switches in all the connection
blocks and switch blocks.

.. code-block:: python
    
    # Automatically populate the routing channels using the segments defined above
    ctx.array.populate_routing_channels()

    # Automatically populates connections blocks and switch blocks
    #   FC value describes the connectivity between block ports and wire segments
    ctx.array.populate_routing_switches(default_fc = (0.25, 0.5))

Building Flow
^^^^^^^^^^^^^

The PRGA Builder uses a ``Flow`` object to manage the building flow. One
``Flow`` object only works on one ``ArchitectureContext``, but
``ArchitectureContext`` remembers what ``Pass`` es have been applied to it, so
multiple ``Flow`` objects can be used.

.. code-block:: python

    from prga.flow import *

    # Create a Flow that operates on the architecture context
    flow = Flow(context = ctx)

The building flow is organized as ``Pass`` es. A ``Pass`` may modify
``ArchitectureContext``, add some annotations to ``ArchitectureContext``, or
generate files based on the data stored in the ``ArchitectureContext``.

The following ``Pass`` es are required to enable mapping target RTLs onto the
custom FPGA:

* ``ArchitectureFinalization``: automatically create configurable muxes,
  validate CLB structures, etc.
* ``VPRExtension``: forward computation of some VPR-related data
* ``{C}ConfigGenerator``: automatically insert ``{C}``-type configuration
  circuitry to the custom FPGA. Currently the only configuration circuitry type
  supported is ``Bitchain``, which is simply a long chain of flipflops
* ``VerilogGenerator``: automatically generate Verilog files for the custom FPGA
* ``{T}TimingEngine``: ``{T}``-type timing engine. Currently the only available
  timing engine is a random value generator
* ``VPRArchdefGenerator``: automatically generate VPR's architecture description
  XML
* ``VPRRRGraphGenerator``: automatically generate VPR's routing resource graph
  XML
* ``{C}ConfigProtoSerializer``: dump ``{C}``-type configuration database

Besides these ``Pass`` es, there are optional optimization ``Pass`` es such as
``InsertOpenMuxForLutInputOptimization``,
``DisableExtioDuringConfigOptimization``, etc.

.. code-block:: python

    import os

    # 1. ArchitectureFinalization: automatically creates configurable muxes,
    #   validate CLB structures, etc.
    flow.add_pass(ArchitectureFinalization())

    # 2. [optional] InsertOpenMuxForLutInputOptimization: add one additional
    #   connection from logic zero (ground) to LUT inputs. This is useful when
    #   some LUTs are used as smaller LUTs
    flow.add_pass(InsertOpenMuxForLutInputOptimization())

    # 3. VPRExtension: Forward declaration of some VPR-related data
    flow.add_pass(VPRExtension())

    # 4. BitchainConfigGenerator: generate flip-flop style configuration
    #   circuitry
    flow.add_pass(BitchainConfigGenerator(width = 1))

    # 5. [optional] DisableExtioDuringConfigOptimization: insert buffers before
    #   chip-level outputs. These buffers are disabled while the FPGA is being
    #   programmed
    flow.add_pass(DisableExtioDuringConfigOptimization())

    # 6. VerilogGenerator: generate Verilog for the FPGA
    flow.add_pass(VerilogGenerator())

    # 7. launch the flow
    flow.run()

    # For real FPGAs, users may want to stop here and start the ASIC flow. In
    # this case, the ArchitectureContext can be serialized and dumped onto disk
    # using Python's pickle module. After ASIC flow, the pickled file can be
    # unpickled, and the building flow can be resumed by creating a new Flow.
    #
    #   ctx.pickle(f = open("arch.pickled", 'w'))
    #   ctx = ArchitectureContext.unpickle(f = open("archdef.pickled"))

    # 8. RandomTimingEngine: generate random fake timing values for the FPGA
    flow.add_pass(RandomTimingEngine(max = (100e-12, 250e-12)))

    # 9. VPRArchdefGenerator, VPRRRGraphGenerator: generates VPR input files
    flow.add_pass(VPRArchdefGenerator())
    flow.add_pass(VPRRRGraphGenerator(switches = [100e-12, 150e-12, 200e-12]))

    # 10. BitchainConfigProtoSerializer: generate a database of the
    #   configuration circuitry that will be used by the bitgen
    flow.add_pass(BitchainConfigProtoSerializer())

    # 11. launch the flow
    flow.run()

PRGA Tool Chain
---------------

The PRGA Tool Chain is the back end of PRGA. It uses `Yosys
<http://www.clifford.at/yosys/>`_ for synthesis, and `VPR
<https://verilogtorouting.org/>`_ for pack, place & route.

Notably, unlike its predecessors and other similar projects, the PRGA Tool Chain
does not modify VPR, but only uses it via command line arguments. In this way,
PRGA is always ready to use the latest commits and new features of VPR.

PRGA Bitgen
-----------

The PRGA Bitgen is a C++ framework for creating bitstream generators which are
able to process all the VPR outputs using the configuration database generated
by the PRGA Builder.

Currently a bitstream generator for ``Bitchain``-type configuration circuitry is
implemented. The command line arguments for this bitstream generator are:

``-b, --blif FILE``

    The synthesized target designe in BLIF format.

``-c, --config_db FILE``

    The configuration database.

``-n, --net FILE``

    The packing result from VPR.

``-p, --place FILE``

    The placing result from VPR.

``-r, --route FILE``

    The routing result from VPR.

``-v, --verbose {trace|debug|info|warn|err|critical|off}``

    Verbosity level.

``--output_memh FILE``

    Output bitstream in ``.memh`` format (for simulation).
