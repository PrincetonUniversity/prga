from prga.compatible import *

from prga._archdef.common import Dimension, Direction
from prga._archdef.routing.common import Position, SegmentPrototype, Segment, BlockPin
from prga._archdef.routing.switchblock import SwitchBlock, SwitchBlockEnvironment

class TestSwitchBlock(object):
    def test_switch_block(self):
        l1 = SegmentPrototype('l1', 4, 1)
        l2 = SegmentPrototype('l2', 2, 2)
        segments = [l1, l2]
        block = SwitchBlock('sb')
        block.populate_segments(segments)
        block.implement_wilton(segments)
        sinks = [
                # node,                                              bridge, phys,  input
                (Segment((1, 0),    l1, Direction.pos, Dimension.x), False,  False, True),
                (Segment((1, 0),    l1, Direction.pos, Dimension.x), True,   True,  False),
                (Segment((0, 0),    l1, Direction.pos, Dimension.x), False,  True,  True),
                (Segment((0, 1),    l1, Direction.pos, Dimension.y), False,  False, True),
                (Segment((0, 1),    l1, Direction.pos, Dimension.y), True,   True,  False),
                (Segment((0, 0),    l1, Direction.pos, Dimension.y), False,  True,  True),
                (Segment((0, 0),    l1, Direction.neg, Dimension.x), False,  False, True),
                (Segment((0, 0),    l1, Direction.neg, Dimension.x), True,   True,  False),
                (Segment((1, 0),    l1, Direction.neg, Dimension.x), False,  True,  True),
                (Segment((0, 0),    l1, Direction.neg, Dimension.y), False,  False, True),
                (Segment((0, 0),    l1, Direction.neg, Dimension.y), True,   True,  False),
                (Segment((0, 1),    l1, Direction.neg, Dimension.y), False,  True,  True),

                (Segment((1, 0),    l2, Direction.pos, Dimension.x), False,  False, True),
                (Segment((1, 0),    l2, Direction.pos, Dimension.x), True,   True,  False),
                (Segment((0, 0),    l2, Direction.pos, Dimension.x), False,  True,  True),
                (Segment((0, 0, 1), l2, Direction.pos, Dimension.x), False,  True,  True),
                (Segment((0, 1),    l2, Direction.pos, Dimension.y), False,  False, True),
                (Segment((0, 1),    l2, Direction.pos, Dimension.y), True,   True,  False),
                (Segment((0, 0),    l2, Direction.pos, Dimension.y), False,  True,  True),
                (Segment((0, 0, 1), l2, Direction.pos, Dimension.y), False,  True,  True),
                (Segment((0, 0),    l2, Direction.neg, Dimension.x), False,  False, True),
                (Segment((0, 0),    l2, Direction.neg, Dimension.x), True,   True,  False),
                (Segment((1, 0),    l2, Direction.neg, Dimension.x), False,  True,  True),
                (Segment((1, 0, 1), l2, Direction.neg, Dimension.x), False,  True,  True),
                (Segment((0, 0),    l2, Direction.neg, Dimension.y), False,  False, True),
                (Segment((0, 0),    l2, Direction.neg, Dimension.y), True,   True,  False),
                (Segment((0, 1),    l2, Direction.neg, Dimension.y), False,  True,  True),
                (Segment((0, 1, 1), l2, Direction.neg, Dimension.y), False,  True,  True),
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

    def test_truncated(self):
        l1 = SegmentPrototype('l1', 4, 1)
        l2 = SegmentPrototype('l2', 2, 2)
        segments = [l1, l2]
        block = SwitchBlock('sb')
        block.populate_segments(segments, SwitchBlockEnvironment(left = False, bottom = False))
        block.implement_wilton(segments)
        sinks = [
                # node,                                              bridge, phys,  input
                (Segment((1, 0),    l1, Direction.pos, Dimension.x), False,  False, True),
                (Segment((1, 0),    l1, Direction.pos, Dimension.x), True,   True,  False),
                (Segment((0, 1),    l1, Direction.pos, Dimension.y), False,  False, True),
                (Segment((0, 1),    l1, Direction.pos, Dimension.y), True,   True,  False),
                (Segment((1, 0),    l1, Direction.neg, Dimension.x), False,  True,  True),
                (Segment((0, 1),    l1, Direction.neg, Dimension.y), False,  True,  True),

                (Segment((1, 0),    l2, Direction.pos, Dimension.x), False,  False, True),
                (Segment((1, 0),    l2, Direction.pos, Dimension.x), True,   True,  False),
                (Segment((1, 0, 1), l2, Direction.pos, Dimension.x), False,  False, True),
                (Segment((1, 0, 1), l2, Direction.pos, Dimension.x), False,  True,  False),
                (Segment((0, 1),    l2, Direction.pos, Dimension.y), False,  False, True),
                (Segment((0, 1),    l2, Direction.pos, Dimension.y), True,   True,  False),
                (Segment((0, 1, 1), l2, Direction.pos, Dimension.y), False,  False, True),
                (Segment((0, 1, 1), l2, Direction.pos, Dimension.y), False,  True,  False),
                (Segment((1, 0),    l2, Direction.neg, Dimension.x), False,  True,  True),
                (Segment((1, 0, 1), l2, Direction.neg, Dimension.x), False,  True,  True),
                (Segment((0, 1),    l2, Direction.neg, Dimension.y), False,  True,  True),
                (Segment((0, 1, 1), l2, Direction.neg, Dimension.y), False,  True,  True),
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
