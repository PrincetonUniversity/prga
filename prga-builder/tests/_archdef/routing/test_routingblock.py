from prga.compatible import *

from prga._archdef.common import Side, Dimension, Direction
from prga._archdef.primitive.builtin import IopadPrimitive
from prga._archdef.block.block import IOBlock, LogicBlock
from prga._archdef.routing.common import Position, SegmentPrototype, Segment, BlockPin
from prga._archdef.routing.switchblock import SwitchBlockEnvironment
from prga._archdef.routing.routingblock import RoutingBlock

class TestRoutingBlock(object):
    def test_routing_block(self):
        l1 = SegmentPrototype('l1', 4, 1)
        l2 = SegmentPrototype('l2', 2, 2)
        segments = [l1, l2]

        clb = LogicBlock('clb')
        clb.add_input('in', 4, Side.left)
        clb.add_output('out', 1, Side.right)
        clb.add_clock('clk', Side.bottom)

        iob = IOBlock('iob', IopadPrimitive(), 2)
        iob.add_input('gpi', 1, Side.right)
        iob.add_output('gpo', 1, Side.right)

        block = RoutingBlock('hrb', Dimension.y)
        block.populate_segments(segments)
        block.implement_wilton(segments)
        block.implement_fc(segments, Direction.pos, clb, (0.5, 0.25))
        block.implement_fc(segments, Direction.neg, iob, 0.5)
        sinks = [
                # node,                                               bridge, phys,  input
                (Segment((0, 0),     l1, Direction.pos, Dimension.y), False,  False, True),
                (Segment((0, 0),     l1, Direction.pos, Dimension.y), False,  True,  False),
                (Segment((0, 0),     l2, Direction.pos, Dimension.y), False,  False, True),
                (Segment((0, 0),     l2, Direction.pos, Dimension.y), False,  True,  False),
                (Segment((0, -1),    l1, Direction.pos, Dimension.x), False,  True,  True),
                (Segment((0, -1),    l1, Direction.pos, Dimension.y), False,  True,  True),
                (Segment((1, -1),    l1, Direction.neg, Dimension.x), False,  True,  True),
                (Segment((0, -1),    l2, Direction.pos, Dimension.x), False,  True,  True),
                (Segment((0, -1, 1), l2, Direction.pos, Dimension.x), False,  True,  True),
                (Segment((0, -1),    l2, Direction.pos, Dimension.y), False,  True,  True),
                (Segment((0, -1, 1), l2, Direction.pos, Dimension.y), False,  True,  True),
                (Segment((1, -1),    l2, Direction.neg, Dimension.x), False,  True,  True),
                (Segment((1, -1, 1), l2, Direction.neg, Dimension.x), False,  True,  True),

                (Segment((0, 0),     l1, Direction.neg, Dimension.y), False,  False, True),
                (Segment((0, 0),     l1, Direction.neg, Dimension.y), False,  True,  False),
                (Segment((0, 0),     l2, Direction.neg, Dimension.y), False,  False, True),
                (Segment((0, 0),     l2, Direction.neg, Dimension.y), False,  True,  False),
                (Segment((0, 0),     l1, Direction.pos, Dimension.x), False,  True,  True),
                (Segment((1, 0),     l1, Direction.neg, Dimension.x), False,  True,  True),
                (Segment((0, 1),     l1, Direction.neg, Dimension.y), False,  True,  True),
                (Segment((0, 0),     l2, Direction.pos, Dimension.x), False,  True,  True),
                (Segment((0, 0, 1),  l2, Direction.pos, Dimension.x), False,  True,  True),
                (Segment((1, 0),     l2, Direction.neg, Dimension.x), False,  True,  True),
                (Segment((1, 0, 1),  l2, Direction.neg, Dimension.x), False,  True,  True),
                (Segment((0, 1),     l2, Direction.neg, Dimension.y), False,  True,  True),
                (Segment((0, 1, 1),  l2, Direction.neg, Dimension.y), False,  True,  True),

                (BlockPin((1, 0),    clb.ports['in']),                False,  True,  False),
                (BlockPin((0, 0),    iob.ports['gpi']),               False,  True,  False),
                (BlockPin((0, 0, 1), iob.ports['gpi']),               False,  True,  False),
                (BlockPin((0, 0),    iob.ports['gpo']),               False,  True,  True),
                (BlockPin((0, 0, 1), iob.ports['gpo']),               False,  True,  True),
                ]
        for (expected_node, exp_is_brg, exp_is_phys, exp_is_input), ((node, _), port) in zip(sinks, iteritems(block.ports)):
            assert node == expected_node
            assert exp_is_brg is port.is_bridge
            assert exp_is_phys is port.is_physical
            assert exp_is_input is port.is_input
        nodes = map(lambda t: (t[0], t[3]), filter(lambda t: not t[1] and t[2], sinks))
        for (expected_node, exp_is_input), (node, port) in zip(nodes, iteritems(block.nodes)):
            assert expected_node == node
            assert exp_is_input is port.is_input
            assert port.is_physical
            assert not port.is_bridge
        bridges = map(lambda t: (t[0], t[3]), filter(lambda t: t[1] and t[2], sinks))
        for (expected_node, exp_is_input), (node, port) in zip(bridges, iteritems(block.bridges)):
            assert expected_node == node
            assert exp_is_input is port.is_input
            assert port.is_physical
            assert port.is_bridge
