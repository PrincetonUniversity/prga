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
  * Use Protobuf 3.7 if Python 3 is used
  * Use Protobuf 2.5 if Python 2 is used
* `Verilog-to-Routing <https://verilogtorouting.org/>`_
* `Yosys <http://www.clifford.at/yosys/>`_
* `Icarus Verilog <http://iverilog.icarus.com/>`_

Python
^^^^^^

PRGA works with Python 2.7.x and Python 3.7.x. Required Python modules are:

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

Examples are provided in the ``examples/`` directory. FPGA building examples are
provided in the ``fpga/`` directory, and FPGA using examples are provided in the
``target/`` directory. Follow the commands below to run an example:

.. code-block:: bash
    
    cd /path/to/prga                        # cd to the root folder of PRGA
    source envscr/general.settings.sh       # set up environment
    cd examples/bcd2bin/k4_N2_8x8           # cd to one of the using example directories
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
    
    from prga import *

    ctx = ArchitectureContext()

After creating the ``ArchitectureContext``, we can start to describe our desired
FPGA. The first step is to describe the routing resources in the desired FPGA.
Use ``ctx.create_segment`` to create routing wire segments. Use
``ctx.create_global`` to create global wires.

.. code-block:: python
    
    ctx.create_segment(name = 'L1', width = 8, length = 1)
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
    clb.add_input (name = 'I',   width = 8, side = Side.left)
    clb.add_output(name = 'O',   width = 2, side = Side.right)
    clb.add_clock (name = 'CLK',            side = Side.bottom, global_ = 'clk')

    for i in range(2):
        # Add logic elements (primitives) to this CLB
        clb.add_instance(name = 'LUT'+str(i), model = ctx.primitives['lut4'])
        clb.add_instance(name = 'FF'+str(i),  model = ctx.primitives['flipflop'])

        # Add configurable intra-block connections to this CLB
        clb.add_connections(
                sources = clb.instances['LUT'+str(i)].pins['out'],
                sinks = clb.instances['FF'+str(i)].pins['D'],
                pack_pattern = True)
        clb.add_connections(
                sources = clb.instances['LUT'+str(i)].pins['out'],
                sinks = clb.ports['O'][i])
        clb.add_connections(
                sources = clb.ports['CLK'],
                sinks = clb.instances['FF'+str(i)].pins['clk'])
        clb.add_connections(
                sources = clb.instances['FF'+str(i)].pins['Q'],
                sinks = clb.ports['O'][i])

    clb.add_connections(
            sources = clb.ports['I'],
            sinks = [clb.instances['LUT0'].pins['in'], clb.instances['LUT1'].pins['in']])

Similar to creating CLBs, use ``ctx.create_io_block`` to create ``IOBlock``.
Typically, four types of IOBs are needed on four sides of the top-level gate
array.

.. code-block:: python
    
    # Create some IOBs
    for side in Side.all():
        io = ctx.create_io_block(name = 'IO_{}'.format(side.name.upper()), capacity = 2)

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

After creating the CLB/IOBs, use ``ctx.create_array`` to create top-level or
sub-arrays. The method returns an ``Array`` object. Use ``Array.add_block``
to place blocks or sub-arrays into an array. Be careful when the same sub-array
is placed into different locations in an array: either make the sub-array
**NOT** including the routing channels around it (which is the default
behavior), or make sure all blocks/sub-arrays adjacent to each instance of the
same sub-array are exactly the same.

.. code-block:: python

    mt_width, mt_height = 3, 3      # macro-tile width and height
    mt_count_x, mt_count_y = 2, 2   # number of macro-tiles

    macro = ctx.create_array(name = "macrotile", width = mt_width, height = mt_height)
    for x in range(mt_width):
        for y in range(mt_height):
            macro.add_block(clb, x, y)
    
    width, height = mt_width * mt_count_x + 2, mt_height * mt_count_y + 2
    top = ctx.create_array(name = 'top', width = width, height = height, replace_top = True)
    for y in range(1, height - 1):
        top.add_block(block = ctx.blocks["IO_LEFT"],   x = 0,         y = y)
        top.add_block(block = ctx.blocks["IO_RIGHT"],  x = width - 1, y = y)
    for x in range(1, width - 1):
        top.add_block(block = ctx.blocks["IO_BOTTOM"], x = x,         y = 0)
        top.add_block(block = ctx.blocks["IO_TOP"],    x = x,         y = height - 1)
    for x in range(1, width - 2, mt_width):
        for y in range(1, height - 2, mt_height):
            top.add_block(block = macro,               x = x,         y = y)

After creating the layout, use ``ctx.bind_global`` to bind the global wire to
a specific IOB.

.. code-block:: python

    # Bind global wire to a specific IOB
    ctx.bind_global('clk', (0, 1))

This concludes the description of an FPGA in a **logical** level. No routing
channels, switches, or configuration circuitry are added to it yet. It's
possible to add all these manually, but various automatic completion procedures
are available as ``Pass`` es in the building flow. 

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

.. code-block:: python

    # Create a Flow that operates on the architecture context
    flow = Flow(context = ctx)

    # Add passes
    #   There are no "required" passes, but dependences, conflicts, and/or ordering constraints may exist between
    #   passes. The Flow reports missing dependences or conflicting passes, and orders the passes in a correct order

    # 1. RoutingResourceCompleter: automatically create and place routing blocks
    flow.add_pass(RoutingResourceCompleter((0.25, 0.5)))

    # 2. PhysicalCompleter: automatically create and place muxes
    flow.add_pass(PhysicalCompleter())

    # 3. [optional] InsertOpenMuxForLutInputOptimization: add one additional connection from logic zero (ground) to
    #   LUT inputs. This is useful when some LUTs are used as smaller LUTs
    flow.add_pass(InsertOpenMuxForLutInputOptimization())

    # 4. VPRIDGenerator: Forward declaration of some VPR-related data
    flow.add_pass(VPRIDGenerator())

    # 5. BitchainConfigInjector: generate flip-flop style configuration circuitry
    flow.add_pass(BitchainConfigInjector())

    # 6. VerilogGenerator: generate Verilog for the FPGA
    flow.add_pass(VerilogGenerator())

    # 7. launch the flow
    flow.run()

    # For real FPGAs, users may want to stop here and start the ASIC flow. In this case, the ArchitectureContext can
    # be serialized and dumped onto disk using Python's pickle module, then deserialized and resumed 

    # 9. VPRXMLGenerator: generates VPR input files
    flow.add_pass(VPRXMLGenerator())

    # 10. BitchainConfigProtoSerializer: generate a database of the configuration circuitry that will be used by the
    #   bitgen
    flow.add_pass(BitchainConfigProtoSerializer())

    # 11. launch the flow
    flow.run()

The ``ArchitectureContext`` can be serialized and stored by calling
``ctx.pickle``, and deserialized later by calling
``ArchitectureContext.unpickle()``.

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
