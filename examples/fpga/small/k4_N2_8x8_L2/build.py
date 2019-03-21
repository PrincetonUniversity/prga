# -*- enconding: ascii -*-

from prga import *
from prga.flow import *

import os

def run():
    ##########################################################################
    ##                  Describe custom FPGA architecture                   ##
    ##########################################################################

    # Create an ArchitectureContext
    #   ArchitectureContext is the entrance to all architecture description APIs, and the container of all data of a
    #   custom FPGA
    ctx = ArchitectureContext()
    
    # Create some wire segments
    ctx.create_segment(name = 'L1', width = 8, length = 1)
    ctx.create_segment(name = 'L2', width = 2, length = 2)
    
    # Create a global wire
    clk = ctx.create_global(name = 'clk', is_clock = True)
    
    # Create one CLB type
    clb = ctx.create_logic_block(name = 'CLB')
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
    
    # Create FPGA layout by placing blocks
    width, height = 8, 8
    top = ctx.create_array(name = 'top', width = width, height = height)
    for y in range(1, height - 1):
        top.add_block(block = ctx.blocks["IO_LEFT"],   x = 0,         y = y)
        top.add_block(block = ctx.blocks["IO_RIGHT"],  x = width - 1, y = y)
    for x in range(1, width - 1):
        top.add_block(block = ctx.blocks["IO_BOTTOM"], x = x,         y = 0)
        top.add_block(block = ctx.blocks["IO_TOP"],    x = x,         y = height - 1)
        for y in range(1, height - 1):
            top.add_block(block = clb,                 x = x,         y = y)

    # Bind global wire to a specific IOB
    ctx.bind_global('clk', (width - 2, height - 1))
    # ctx.bind_global('clk', (0, 1))
    
    ##########################################################################
    ##                          Run PRGA Builder Flow                       ##
    ##########################################################################

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

    # pickle the architecture context
    ctx.pickle('ctx.pickled')

if __name__ == '__main__':
    run()
