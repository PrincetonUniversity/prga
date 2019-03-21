from prga.compatible import *

from prga._archdef.common import Side
from prga._archdef.block.block import IOBlock
from prga._archdef.primitive.builtin import IopadPrimitive

class TestIOBlock(object):
    def test_io_block(self):
        block = IOBlock('mock', IopadPrimitive(), 2)
        assert 'extio' in block.instances
        assert set(block._ports) == set(('extio_i', 'extio_o', 'extio_oe'))
        assert block.instances['extio'].pins['inpad'].physical_cp is block._ports['extio_i']
        assert block.instances['extio'].pins['outpad'].physical_cp is block._ports['extio_o']
        block.add_input('in', 4, Side.left)
        block.add_output('out', 1, Side.right)
        block.add_clock('clk', Side.bottom)
        # block.add_instance('inst0', 'lut4')
        # block.add_instance('inst1', 'flipflop')
        # assert all(x._is_dynamic for x in block.instances['inst0'].pins.values())
        # assert all(x._is_dynamic for x in block.instances['inst1'].pins.values())
        # assert all(x._is_dynamic for port in block.ports.values() for x in port)
        # block.add_connections(block.ports['in'], block.instances['inst0'].pins['in'])
        # block.add_connections(block.ports['clk'], block.instances['inst1'].pins['clk'])
        # block.add_connections(block.instances['inst0'].pins['out'], block.instances['inst1'].pins['D'],
        #         pack_pattern=True)
        # block.add_connections(block.instances['inst0'].pins['out'], block.ports['out'])
        # block.add_connections(block.instances['inst1'].pins['Q'], block.ports['out'])
        # assert all(not x._is_dynamic for x in block.instances['inst0'].pins.values())
        # assert all(not x._is_dynamic for x in block.instances['inst1'].pins.values())
        # assert all(not x._is_dynamic for port in block.ports.values() for x in port)
