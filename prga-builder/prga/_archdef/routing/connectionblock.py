# Python 2 and 3 compatible
from prga.compatible import *

from prga._archdef.common import Direction, Side, BlockType, PortDirection
from prga._archdef.routing.common import Position, Segment, BlockPin
from prga._archdef.routing.block import AbstractRoutingBlock
from prga._util.util import uno
from prga.exception import PRGAInternalError

from collections import namedtuple
from itertools import product
from math import ceil

# ----------------------------------------------------------------------------
# -- Block FC ----------------------------------------------------------------
# ----------------------------------------------------------------------------
class BlockPinFCValue(namedtuple('BlockPinFCValue', 'default segment_map')):
    """A named tuple used for defining FC values for a specific block pin.

    Args:
        default (:obj:`int` or :obj:`float`): the default FC value for this pin
        segment_map (:obj:`dict` [:obj:`str` -> :obj:`int` or :obj:`float` ], default=None): the FC value for a
            specific segment type

    It's also acceptable to pass in a single :obj:`list` with 1-2 elements. The elements will then be treated as the
    arguments to the constructor
    """
    def __new__(cls, default, segment_map = None):
        if segment_map is None and isinstance(default, Sequence):
            return super(BlockPinFCValue, cls).__new__(cls, default[0], default[1] if len(default) > 1 else {})
        else:
            return super(BlockPinFCValue, cls).__new__(cls, default, uno(segment_map, {}))

    def segment_fc(self, segment, all_sections = False):
        """Get the FC value for a specific segment.

        Args:
            segment (`SegmentPrototype`):
            all_sections (:obj:`bool`): if all sections of a segment longer than 1 should be taken into consideration

        Returns:
            :obj:`int`: the calculated FC value
        """
        multiplier = segment.length if all_sections else 1
        fc = self.segment_map.get(segment.name, self.default)
        if isinstance(fc, int):
            if fc < 0 or fc >= segment.width:
                raise PRGAInternalError("Invalid FC value ({}) for segment '{}'".format(fc, segment.name))
            return fc * multiplier
        elif isinstance(fc, float):
            if fc < 0 or fc > 1:
                raise PRGAInternalError("Invalid FC value ({}) for segment '{}'".format(fc, segment.name))
            return int(ceil(fc * segment.width * multiplier))
        else:
            raise RuntimeError

class BlockFCValue(namedtuple('BlockFCValue', 'default_in default_out pin_map')):
    """A named tuple used for defining FC values for a specific block.

    Args:
        default_in (`BlockPinFCValue`): the default FC value for all input pins
        default_out (`BlockPinFCValue`, default=None): the default FC value for all output pins. Same as
            the default value for input pins if not set
        pin_map (:obj:`dict` [:obj:`str` -> `BlockPinFCValue` ], default=None): the FC value for a specific segment
        type

    For each argument that is of type `BlockPinFCValue`, it's also acceptable to pass in any argument that's valid to
    the `BlockPinFCValue` constructor. For `BlockFCValue`, it's also acceptable to pass in a single :obj:`list` with
    1-3 elements. The elements will then be treated as the arguments to the constructor.
    """
    def __new__(cls, default_in, default_out = None, pin_map = None):
        if default_out is None and pin_map is None and isinstance(default_in, Sequence):
            return super(BlockFCValue, cls).__new__(cls, BlockPinFCValue(default_in[0]),
                    BlockPinFCValue(default_in[1] if len(default_in) > 1 else default_in[0]),
                    dict( (k, BlockPinFCValue(v)) for k, v in iteritems(default_in[2] if len(default_in) > 2 else {}) ))
        else:
            return super(BlockFCValue, cls).__new__(cls, BlockPinFCValue(default_in),
                    BlockPinFCValue(uno(default_out, default_in)),
                    dict( (k, BlockPinFCValue(v)) for k, v in iteritems(uno(pin_map, {})) ))

    def port_fc(self, port, segment, all_sections = False):
        """Get the FC value for a specific port and a specific segment.

        Args:
            port (Logic/IO block port): 
            segment (`SegmentPrototype`):
            all_sections (:obj:`bool`): if all sections of a segment longer than 1 should be taken into consideration

        Returns:
            :obj:`int`: the calculated FC value
        """
        return self.pin_map.get(port.name, self.default_in if port.is_input else self.default_out).segment_fc(segment,
                all_sections)

# ----------------------------------------------------------------------------
# -- Connection Block w/o Combined Switch Block ------------------------------
# ----------------------------------------------------------------------------
class ConnectionBlock(AbstractRoutingBlock):
    """Connection block without combined switch block.

    Args:
        name (:obj:`str`): name of this block
        dimension (`Dimension`): dimension of this connection block
    """
    def __init__(self, name, dimension):
        super(ConnectionBlock, self).__init__(name)
        self._dimension = dimension
        
    # == low-level API =======================================================
    @property
    def block_type(self):
        """Type of this routing block."""
        return self._dimension.select(BlockType.xconn, BlockType.yconn)

    @property
    def dimension(self):
        """Dimension of this connection block."""
        return self._dimension

    def populate_segments(self, segments, bridge_from_switchblock = False):
        """Populate the routing block with segment nodes as if this is a combined connection/switch block.

        Args:
            segments (:obj:`list` [`SegmentPrototype` ]):
            bridge_from_switchblock (:obj:`bool`): if the segment driver from the switch block and this connection
                block should merge here
        """
        for sgmt, direction in product(iter(segments), Direction.all()):
            node = Segment((0, 0), sgmt, direction, self._dimension)
            self._get_or_create_node(node, PortDirection.input, bridge_from_switchblock, not bridge_from_switchblock)
            self._get_or_create_node(node, PortDirection.output, not bridge_from_switchblock)
            for section in range(1, sgmt.length):
                self._get_or_create_node(node._replace(position = Position(0, 0, section)), PortDirection.input)

    def implement_fc(self, segments, direction, block, fc, offset = 0):
        """Add pin-track connections using FC values.

        Args:
            segments (:obj:`list` [`SegmentPrototype` ]): all segment prototypes
            direction (`Direction`): on which side of this connection block is the block
            block (`LogicBlock` or `IOBlock`): the block on the given side of this connection block
            fc (`BlockFCValue`): the FC value
            offset (:obj:`int`): the offset of this connection block relative to ``block``

        Note that this method will NOT add nodes for the segments.
        """
        fc = BlockFCValue(fc)
        dim = self._dimension # short alias
        side = dim.select(direction.select(Side.bottom, Side.top), direction.select(Side.left, Side.right))
        xoffset, yoffset = dim.select(offset, 0), dim.select(0, offset)
        # iterators
        itic = [0 for _ in segments] # input-to-track index counter
        otic = [0 for _ in segments] # output-to-track index counter
        for port in itervalues(block.ports):
            if port.is_global or not (port.side is side and port.xoffset == xoffset and port.yoffset == yoffset):
                continue
            for sgmt_idx, sgmt in enumerate(segments):
                nconn = fc.port_fc(port, sgmt, port.is_input)   # number of connections
                if nconn == 0:
                    continue
                imax = port.direction.select(sgmt.length * sgmt.width, sgmt.width)
                istep = max(1, imax // nconn)  # index step
                for _, pin_idx in product(range(nconn), range(port.width)):
                    # get the section and track id to be connected
                    section = port.direction.select(itic[sgmt_idx] % sgmt.length, 0)
                    track_idx = port.direction.select(itic[sgmt_idx] // sgmt.length, otic[sgmt_idx])
                    for subblock, sgmt_dir in product(range(block.capacity), Direction.all()):
                        # get the bits
                        sgmt_node = Segment((0, 0, section), sgmt, sgmt_dir, dim)
                        sgmt_port = self._get_node(sgmt_node, port.direction)
                        if sgmt_port is None:
                            raise PRGAInternalError("No segment {} for node '{}' in block '{}'"
                                    .format(port.direction.name, sgmt_node, self))
                        sgmt_bit = sgmt_port[track_idx]
                        pin_bit = self._get_or_create_node(BlockPin((1 if side is Side.left else 0,
                            1 if side is Side.bottom else 0, subblock), port), port.direction.opposite)[pin_idx]
                        # make connection
                        if port.is_input:
                            self.add_connections(sgmt_bit, pin_bit)
                        else:
                            self.add_connections(pin_bit, sgmt_bit)
                    nic = port.direction.select(itic, otic)[sgmt_idx] + istep # next index
                    if istep > 1 and nic >= imax:
                        nic += 1
                    port.direction.select(itic, otic)[sgmt_idx] = nic % imax
