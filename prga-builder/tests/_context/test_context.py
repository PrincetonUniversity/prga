from prga.compatible import *

from prga._archdef.common import Side
from prga._context.context import ArchitectureContext
from prga._context.flow import Flow
from prga._context.completer.routing import RoutingResourceCompleter
from prga._context.completer.physical import PhysicalCompleter
from prga._context.rtlgen.verilog import VerilogGenerator
from prga._context.vpr.idgen import VPRIDGenerator
from prga._context.vpr.xmlgen import VPRXMLGenerator
from prga._configcircuitry.bitchain.injector import BitchainConfigInjector
from prga._configcircuitry.bitchain.serializer import BitchainConfigProtoSerializer
from prga._optimization.insert_open_mux_for_lut_input import InsertOpenMuxForLutInputOptimization

import os

def test_context():
    context = ArchitectureContext()

    context.create_global('clk', True)
    
    context.create_segment('l1', 4, 1)
    context.create_segment('l2', 2, 2)

    for side in Side.all():
        iob = context.create_io_block('IO_{}'.format(side.name.upper()), 2)
        iob.add_input('gpo', 1, side.opposite)
        iob.add_output('gpi', 1, side.opposite)
        iob.add_connections(iob.instances['extio'].pins['inpad'], iob.ports['gpi'])
        iob.add_connections(iob.ports['gpo'], iob.instances['extio'].pins['outpad'])

    clb = context.create_logic_block('CLB')
    clb.add_input('in', 4, Side.left)
    clb.add_output('out', 1, Side.right)
    clb.add_clock('clk', Side.bottom)
    clb.add_instance('lut', context.primitives['lut4'])
    clb.add_instance('ff', context.primitives['flipflop'])
    clb.add_connections(clb.ports['in'], clb.instances['lut'].pins['in'])
    clb.add_connections(clb.ports['clk'], clb.instances['ff'].pins['clk'])
    clb.add_connections(clb.instances['lut'].pins['out'], clb.instances['ff'].pins['D'],
            pack_pattern = True)
    clb.add_connections(clb.instances['lut'].pins['out'], clb.ports['out'])
    clb.add_connections(clb.instances['ff'].pins['Q'], clb.ports['out'])

    array0 = context.create_array('inner', 2, 2)
    for i in range(2):
        for j in range(2):
            array0.add_block(context.blocks['CLB'], i, j)

    array = context.create_array('top', 4, 4, replace_top = True)
    for i in range(1, 3):
        array.add_block(context.blocks['IO_LEFT'], 0, i)
        array.add_block(context.blocks['IO_BOTTOM'], i, 0)
        array.add_block(context.blocks['IO_RIGHT'], 3, i)
        array.add_block(context.blocks['IO_TOP'], i, 3)
    array.add_block(array0, 1, 1)

    context.bind_global('clk', (0, 1))

    flow = Flow(context)
    flow.run_pass(RoutingResourceCompleter((0.25, 0.5)))
    flow.run_pass(PhysicalCompleter())
    flow.run_pass(InsertOpenMuxForLutInputOptimization())
    flow.run_pass(BitchainConfigInjector())
    flow.run_pass(VPRIDGenerator())
    flow.run_pass(VerilogGenerator(os.path.join(os.path.dirname(__file__), 'rtl')))
    flow.run_pass(VPRXMLGenerator())
    flow.run_pass(BitchainConfigProtoSerializer())

    # delegate = DelegateImpl(context)
    # delegate.gen_arch_xml(open('arch.vpr.xml', 'wb' if _py3 else 'w'), True)
    # delegate.gen_rrg_xml(open('rrg.vpr.xml', 'wb' if _py3 else 'w'), True)

    # stream = StringIO()
    # with XMLGenerator(stream, pretty=True, skip_stringify=True) as xg:
    #     with xg.element('root'):
    #         delegate._gen_leaf_pb_type(xg,
    #                 delegate._create_leaf_pb(clb.instances['lut']))
    #         delegate._gen_intermediate_pb_type(xg,
    #                 delegate._create_leaf_pb(context.blocks['IO_LEFT'].instances['extio']))
    # print(stream.getvalue().decode('ascii'))

    # stream = StringIO()
    # with XMLGenerator(stream, pretty=True, skip_stringify=True) as xg:
    #     with xg.element('root'):
    #         delegate._gen_arch_block(xg, delegate._create_top_pb(clb))
    #         delegate._gen_arch_block(xg, delegate._create_top_pb(context.blocks['IO_LEFT']))
    # print(stream.getvalue().decode('ascii'))
    
    assert False
