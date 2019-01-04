# -*- enconding: ascii -*-

from prga.context import *
from prga.flow import *

import os

def run():
    ##########################################################################
    ##                  Describe custom FPGA architecture                   ##
    ##########################################################################

    # Create an ArchitectureContext
    #   ArchitectureContext is the entrance to all architecture description APIs, and the container of all data of a
    #   custom FPGA
    width, height = 8, 8
    arch = ArchitectureContext(width = width, height = height)
    
    # Create some wire segments
    arch.create_segment(name = 'L1', width = 12, length = 1)
    
    # Create a global wire
    clk = arch.create_global(name = 'clk', is_clock = True)
    
    # Create one CLB type
    clb = arch.create_logic_block(name = 'CLB')
    # Add ports to this CLB
    clb.add_input (name = 'I',   width = 8, side = Side.left)
    clb.add_output(name = 'O',   width = 2, side = Side.right)
    clb.add_clock (name = 'CLK',            side = Side.bottom, global_ = 'clk')
    for i in xrange(2):
        # Add logic elements (primitives) to this CLB
        clb.add_instance(name = 'LUT'+str(i), model = 'lut4')
        clb.add_instance(name = 'FF'+str(i),  model = 'flipflop')
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
    
    # Create some IOBs
    for side in Side.all():
        io = arch.create_io_block(name = 'IO_{}'.format(side.name.upper()), capacity = 2)
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
    
    # Create FPGA layout by placing blocks
    arch.array.place_blocks(block = 'CLB',       x = 1,         y = 1,          endx = width - 1, endy = height - 1)
    arch.array.place_blocks(block = 'IO_LEFT',   x = 0,         y = 1,                            endy = height - 1)
    arch.array.place_blocks(block = 'IO_RIGHT',  x = width - 1, y = 1,                            endy = height - 1)
    arch.array.place_blocks(block = 'IO_BOTTOM', x = 1,         y = 0,          endx = width - 1                   )
    arch.array.place_blocks(block = 'IO_TOP',    x = 1,         y = height - 1, endx = width - 1                   )

    # Bind global wire to a specific IOB
    clk.bind(x = 0, y = 1, subblock = 0)
    
    # Automatically populate the routing channels using the segments defined above
    arch.array.populate_routing_channels()

    # Automatically populates connections blocks and switch blocks
    #   FC value describes the connectivity between block ports and wire segments
    arch.array.populate_routing_switches(default_fc = (0.25, 0.5))

    ##########################################################################
    ##                          Run PRGA Builder Flow                       ##
    ##########################################################################

    # Create a Flow that operates on the architecture context
    flow = Flow(context = arch)

    # Add passes
    #   There are no "required" passes, but dependences, conflicts, and/or ordering constraints may exist between
    #   passes. The Flow reports missing dependences or conflicting passes, and orders the passes in a correct order

    # 1. ArchitectureFinalization: automatically creates configurable muxes, validate CLB structures, etc.
    flow.add_pass(ArchitectureFinalization())

    # 2. [optional] InsertOpenMuxForLutInputOptimization: add one additional connection from logic zero (ground) to
    #   LUT inputs. This is useful when some LUTs are used as smaller LUTs
    flow.add_pass(InsertOpenMuxForLutInputOptimization())

    # 3. VPRExtension: Forward declaration of some VPR-related data
    flow.add_pass(VPRExtension())

    # 4. BitchainConfigGenerator: generate flip-flop style configuration circuitry
    flow.add_pass(BitchainConfigGenerator(width = 1))

    # 5. [optional] DisableExtioDuringConfigOptimization: insert buffers before chip-level outputs. These buffers are
    #   disabled while the FPGA is being programmed
    flow.add_pass(DisableExtioDuringConfigOptimization())

    # 6. VerilogGenerator: generate Verilog for the FPGA
    try:
        os.mkdir('rtl')
    except OSError:
        pass
    flow.add_pass(VerilogGenerator(output_dir = 'rtl'))

    # 7. launch the flow
    flow.run()

    # For real FPGAs, users may want to stop here and start the ASIC flow. In this case, the ArchitectureContext can
    # be serialized and dumped onto disk using Python's pickle module, then deserialized and resumed 
    #   arch.pickle(f = open("arch.pickled", 'w'))
    #   arch = ArchitectureContext.unpickle(f = open("archdef.pickled"))

    # 8. RandomTimingEngine: generate random fake timing values for the FPGA
    flow.add_pass(RandomTimingEngine(max = (100e-12, 250e-12)))

    # 9. VPRArchdefGenerator, VPRRRGraphGenerator: generates VPR input files
    flow.add_pass(VPRArchdefGenerator(f = open('archdef.vpr.xml', 'w')))
    flow.add_pass(VPRRRGraphGenerator(f = open('rrgraph.vpr.xml', 'w'),
        switches = [100e-12, 150e-12, 200e-12]))

    # 10. BitchainConfigProtoSerializer: generate a database of the configuration circuitry that will be used by the
    #   bitgen
    flow.add_pass(BitchainConfigProtoSerializer(open('config.pb', 'w')))

    # 11. launch the flow
    flow.run()

if __name__ == '__main__':
    run()
