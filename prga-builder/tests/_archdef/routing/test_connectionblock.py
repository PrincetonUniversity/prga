from prga.compatible import *

from prga._archdef.common import Side, Dimension, Direction
from prga._archdef.primitive.builtin import IopadPrimitive
from prga._archdef.block.block import IOBlock, LogicBlock
from prga._archdef.routing.common import Position, SegmentPrototype, Segment, BlockPin
from prga._archdef.routing.connectionblock import ConnectionBlock

from collections import OrderedDict

class MockContext(object):
    def __init__(self):
        self.segments = OrderedDict([
                ('l1', SegmentPrototype('l1', 4, 1)),
                ('l2', SegmentPrototype('l2', 2, 2)),
                ])

        clb = LogicBlock('clb')
        clb.add_input('in', 4, Side.left)
        clb.add_output('out', 1, Side.right)
        clb.add_clock('clk', Side.bottom)

        iob = IOBlock('iob', IopadPrimitive(), 2)
        iob.add_input('gpi', 1, Side.right)
        iob.add_output('gpo', 1, Side.right)

        dsp = LogicBlock('dsp', 1, 2)
        dsp.add_input('a', 4, Side.left)
        dsp.add_input('b', 4, Side.left, yoffset = 1)
        dsp.add_output('c0', 4, Side.right)
        dsp.add_output('c1', 4, Side.right, yoffset = 1)

        self.blocks = OrderedDict([
                ('clb', clb),
                ('iob', iob),
                ])

class TestConnectionBlock(object):
    def test_horizontal_connection_block(self):
        context = MockContext()
        hcb = ConnectionBlock('hcb', Dimension.x)
        hcb.populate_segments(context.segments.values(), bridge_from_switchblock = False)
        l1, l2 = context.segments['l1'], context.segments['l2']
        sinks = [
                # node,                                              bridge, phys,  input
                (Segment((0, 0),    l1, Direction.pos, Dimension.x), False,  False, True),
                (Segment((0, 0),    l1, Direction.pos, Dimension.x), True,   True,  False),
                (Segment((0, 0),    l1, Direction.neg, Dimension.x), False,  False, True),
                (Segment((0, 0),    l1, Direction.neg, Dimension.x), True,   True,  False),
                (Segment((0, 0),    l2, Direction.pos, Dimension.x), False,  False, True),
                (Segment((0, 0),    l2, Direction.pos, Dimension.x), True,   True,  False),
                (Segment((0, 0, 1), l2, Direction.pos, Dimension.x), False,  True,  True),
                (Segment((0, 0),    l2, Direction.neg, Dimension.x), False,  False, True),
                (Segment((0, 0),    l2, Direction.neg, Dimension.x), True,   True,  False),
                (Segment((0, 0, 1), l2, Direction.neg, Dimension.x), False,  True,  True),
                ]
        for (expected_node, exp_is_brg, exp_is_phys, exp_is_input), ((node, _), port) in zip(sinks, iteritems(hcb.ports)):
            assert node == expected_node
            assert exp_is_brg is port.is_bridge
            assert exp_is_phys is port.is_physical
            assert exp_is_input is port.is_input
        nodes = map(lambda t: (t[0], t[3]), filter(lambda t: not t[1] and t[2], sinks))
        for (expected_node, exp_is_input), (node, port) in zip(nodes, iteritems(hcb.nodes)):
            assert expected_node == node
            assert exp_is_input is port.is_input
            assert port.is_physical
            assert not port.is_bridge
        bridges = map(lambda t: (t[0], t[3]), filter(lambda t: t[1] and t[2], sinks))
        for (expected_node, exp_is_input), (node, port) in zip(bridges, iteritems(hcb.bridges)):
            assert expected_node == node
            assert exp_is_input is port.is_input
            assert port.is_physical
            assert port.is_bridge

    def test_vertical_connection_block(self):
        context = MockContext()
        vcb = ConnectionBlock('vcb', Dimension.y)
        vcb.populate_segments(context.segments.values(), bridge_from_switchblock = True)
        l1, l2 = context.segments['l1'], context.segments['l2']
        clb, iob = context.blocks['clb'], context.blocks['iob']
        vcb.implement_fc(context.segments.values(), Direction.pos, context.blocks['clb'], (0.5, 0.25))
        vcb.implement_fc(context.segments.values(), Direction.neg, context.blocks['iob'], 0.5)
        sinks = [
                # node,                                              bridge, phys,  input
                (Segment((0, 0),    l1, Direction.pos, Dimension.y), True,   True,  True),
                (Segment((0, 0),    l1, Direction.pos, Dimension.y), False,  True,  False),
                (Segment((0, 0),    l1, Direction.neg, Dimension.y), True,   True,  True),
                (Segment((0, 0),    l1, Direction.neg, Dimension.y), False,  True,  False),
                (Segment((0, 0),    l2, Direction.pos, Dimension.y), True,   True,  True),
                (Segment((0, 0),    l2, Direction.pos, Dimension.y), False,  True,  False),
                (Segment((0, 0, 1), l2, Direction.pos, Dimension.y), False,  True,  True),
                (Segment((0, 0),    l2, Direction.neg, Dimension.y), True,   True,  True),
                (Segment((0, 0),    l2, Direction.neg, Dimension.y), False,  True,  False),
                (Segment((0, 0, 1), l2, Direction.neg, Dimension.y), False,  True,  True),

                # node,                                 bridge, phys,  input
                (BlockPin((1, 0),    clb.ports['in']),  False,  True,  False),
                (BlockPin((0, 0),    iob.ports['gpi']), False,  True,  False),
                (BlockPin((0, 0, 1), iob.ports['gpi']), False,  True,  False),
                (BlockPin((0, 0),    iob.ports['gpo']), False,  True,  True),
                (BlockPin((0, 0, 1), iob.ports['gpo']), False,  True,  True),
                ]
        for (expected_node, exp_is_brg, exp_is_phys, exp_is_input), ((node, _), port) in zip(sinks, iteritems(vcb.ports)):
            assert node == expected_node
            assert exp_is_brg is port.is_bridge
            assert exp_is_phys is port.is_physical
            assert exp_is_input is port.is_input
        nodes = map(lambda t: (t[0], t[3]), filter(lambda t: not t[1] and t[2], sinks))
        for (expected_node, exp_is_input), (node, port) in zip(nodes, iteritems(vcb.nodes)):
            assert expected_node == node
            assert exp_is_input is port.is_input
            assert port.is_physical
            assert not port.is_bridge
        bridges = map(lambda t: (t[0], t[3]), filter(lambda t: t[1] and t[2], sinks))
        for (expected_node, exp_is_input), (node, port) in zip(bridges, iteritems(vcb.bridges)):
            assert expected_node == node
            assert exp_is_input is port.is_input
            assert port.is_physical
            assert port.is_bridge
        # TODO: verify the connection generated is as desired
        # for sink in itervalues(vcb.ports):
        #     if sink.is_input:
        #         continue
        #     print('> {} node: {}'.format('physical' if sink.is_physical else 'logical', sink))
        #     for bit in sink:
        #         print('\t> bit {}:'.format(bit._index))
        #         for source in bit.logical_sources:
        #             print('\t\t> {}[{}]'.format(source._bus, source._index))
        # assert False
