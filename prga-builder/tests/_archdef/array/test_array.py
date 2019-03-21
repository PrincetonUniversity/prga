from prga.compatible import *

from prga._archdef.common import Side, Dimension, Direction
from prga._archdef.primitive.builtin import IopadPrimitive
from prga._archdef.routing.common import SegmentPrototype
from prga._archdef.routing.switchblock import SwitchBlockEnvironment
from prga._archdef.routing.routingblock import RoutingBlock
from prga._archdef.block.block import IOBlock, LogicBlock
from prga._archdef.array.array import RoutingChannelCoverage, Array

class TestArray(object):
    def test_array(self):
        segments = [SegmentPrototype('l1', 4, 1), SegmentPrototype('l2', 2, 2)]

        iob = IOBlock('iob', IopadPrimitive(), 2)
        iob.add_input('gpi', 1, Side.right)
        iob.add_output('gpo', 1, Side.right)

        clb = LogicBlock('clb')
        clb.add_input('in', 4, Side.left)
        clb.add_output('out', 1, Side.right)
        clb.add_clock('clk', Side.bottom)

        dsp = LogicBlock('dsp', 1, 2)
        dsp.add_input('a', 4, Side.left)
        dsp.add_input('b', 4, Side.left, yoffset = 1)
        dsp.add_output('c0', 4, Side.right)
        dsp.add_output('c1', 4, Side.right, yoffset = 1)

        yrb0 = RoutingBlock('yrb0', Dimension.y)
        yrb0.populate_segments(segments, SwitchBlockEnvironment(left = False),
                SwitchBlockEnvironment(left = False))
        yrb0.implement_wilton(segments)
        yrb0.implement_fc(segments, Direction.pos, clb, (0.5, 0.25))
        yrb0.implement_fc(segments, Direction.neg, iob, 0.5)

        yrb1 = RoutingBlock('yrb1', Dimension.y)
        yrb1.populate_segments(segments)
        yrb1.implement_wilton(segments)
        yrb1.implement_fc(segments, Direction.pos, clb, (0.5, 0.25))
        yrb1.implement_fc(segments, Direction.neg, clb, (0.5, 0.25))

        yrb2 = RoutingBlock('yrb2', Dimension.y)
        yrb2.populate_segments(segments, SwitchBlockEnvironment(right = False))
        yrb2.implement_wilton(segments)
        yrb2.implement_fc(segments, Direction.pos, dsp, (0.5, 0.25))
        yrb2.implement_fc(segments, Direction.neg, clb, (0.5, 0.25))

        yrb3 = RoutingBlock('yrb3', Dimension.y)
        yrb3.populate_segments(segments, neg_env = SwitchBlockEnvironment(right = False))
        yrb3.implement_wilton(segments)
        yrb3.implement_fc(segments, Direction.pos, dsp, (0.5, 0.25), 1)
        yrb3.implement_fc(segments, Direction.neg, clb, (0.5, 0.25))

        xrb0 = RoutingBlock('xrb0', Dimension.x)
        xrb0.populate_segments(segments)
        xrb0.implement_wilton(segments)
        xrb0.implement_fc(segments, Direction.pos, clb, (0.5, 0.25))
        xrb0.implement_fc(segments, Direction.neg, clb, (0.5, 0.25))

        xrb1 = RoutingBlock('xrb1', Dimension.x)
        xrb1.populate_segments(segments, pos_env = SwitchBlockEnvironment(right = False))
        xrb1.implement_wilton(segments)
        xrb1.implement_fc(segments, Direction.pos, clb, (0.5, 0.25))
        xrb1.implement_fc(segments, Direction.neg, clb, (0.5, 0.25))

        xrb2 = RoutingBlock('xrb2', Dimension.x)
        xrb2.populate_segments(segments)
        xrb2.implement_wilton(segments)
        xrb2.implement_fc(segments, Direction.pos, clb, (0.5, 0.25))
        xrb2.implement_fc(segments, Direction.neg, dsp, (0.5, 0.25))

        xrb3 = RoutingBlock('xrb3', Dimension.x)
        xrb3.populate_segments(segments)
        xrb3.implement_wilton(segments)
        xrb3.implement_fc(segments, Direction.neg, clb, (0.5, 0.25))
        xrb3.implement_fc(segments, Direction.pos, dsp, (0.5, 0.25))

        array0 = Array('array0', 2, 4)
        for y in range(4):
            array0.add_block(clb, 0, y)
        array0.add_block(clb, 1, 0)
        array0.add_block(clb, 1, 3)
        array0.add_block(dsp, 1, 1)

        array0.add_block(xrb0, 0, 0)
        array0.add_block(xrb1, 0, 1)
        array0.add_block(xrb0, 0, 2)
        array0.add_block(xrb3, 1, 0)
        array0.add_block(xrb2, 1, 2)
        array0.add_block(yrb1, 0, 0)
        array0.add_block(yrb2, 0, 1)
        array0.add_block(yrb3, 0, 2)
        array0.add_block(yrb1, 0, 3)
        array0.auto_complete_ports(True)

        assert len(array0.instances) == 18
        assert len(array0.physical_instances) == 16

        array1 = Array('array1', 1, 4, RoutingChannelCoverage(right = True))
        for y in range(4):
            array1.add_block(iob, 0, y)
            array1.add_block(yrb0, 0, y)
        array1.auto_complete_ports(True)

        array2 = Array('array2', 3, 4)
        array2.add_block(array1, 0, 0)
        array2.add_block(array0, 1, 0)
        array2.auto_complete_ports(True)

        assert False
