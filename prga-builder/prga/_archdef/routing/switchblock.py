# Python 2 and 3 compatible
from prga.compatible import *

from prga._archdef.common import BlockType, Direction, Dimension, SideTuple, PortDirection
from prga._archdef.routing.common import Position, Segment
from prga._archdef.routing.block import AbstractRoutingBlock
from prga._util.util import uno

from collections import namedtuple
from itertools import product, chain, cycle

# ----------------------------------------------------------------------------
# -- Switch Block Environment ------------------------------------------------
# ----------------------------------------------------------------------------
class SwitchBlockEnvironment(SideTuple):
    """Tuple used to define the environment of a switch block.

    Args:
        top (:obj:`bool`): if routing channel exists above this block
        right (:obj:`bool`): if routing channel exists to the right of this block
        bottom (:obj:`bool`): if routing channel exists below this block
        left (:obj:`bool`): if routing channel exists to the left of this block
    """
    def __new__(cls, top = True, right = True, bottom = True, left = True):
        return super(SwitchBlockEnvironment, cls).__new__(cls, top, right, bottom, left)

    def has_inputs(self, direction, dimension):
        """Check if this switch block has inputs on the given ``dimension`` in the given ``direction``."""
        return dimension.select(direction.select(self.left, self.right), direction.select(self.bottom, self.top))

    def has_outputs(self, direction, dimension):
        """Check if this switch block has outputs on the given ``dimension`` in the given ``direction``."""
        return dimension.select(direction.select(self.right, self.left), direction.select(self.top, self.bottom))

# ----------------------------------------------------------------------------
# -- Switch Block ------------------------------------------------------------
# ----------------------------------------------------------------------------
class SwitchBlock(AbstractRoutingBlock):
    """Stand alone switch block.

    Args:
        name (:obj:`str`): name of this block
    """
    # == internal methods ====================================================
    def _innode(self, sgmt, direction, dimension, pos = None):
        offset = direction.select(Position(0, 0), dimension.select(Position(1, 0), Position(0, 1)))
        pos = offset if pos is None else (offset + pos)
        return Segment(pos, sgmt, direction, dimension)
    
    def _outnode(self, sgmt, direction, dimension, pos = None):
        offset = direction.select(dimension.select(Position(1, 0), Position(0, 1)), Position(0, 0))
        pos = offset if pos is None else (offset + pos)
        return Segment(pos, sgmt, direction, dimension)

    def _implement_wilton_quarter(self, segments, direction, dimension, pos = None):
        pos = uno(pos, Position(0, 0))
        assert pos.section == 0
        for from_dir, from_dim in product(Direction.all(), Dimension.all()):
            if from_dim is dimension and from_dir is direction.opposite:
                continue
            elif from_dim is dimension and from_dir is direction:
                for sgmt in segments:
                    source = self._get_node(self._innode(sgmt, from_dir, from_dim,
                        pos._replace(subblock_or_section = sgmt.length - 1)), PortDirection.input)
                    sink = self._get_node(self._outnode(sgmt, direction, dimension, pos), PortDirection.output)
                    if source is not None and source.is_physical and sink is not None:
                        self.add_connections(source, sink)
                continue
            # turning direction
            iskip = direction.select(dimension.select(False, True),
                    dimension.select(from_dir.select(False, True), from_dir.select(True, False)))
            orev = from_dir is direction
            # input nodes iterator
            inodes = iter(port[idx] for sgmt in segments
                    for (idx, section) in product(range(sgmt.width), range(sgmt.length))
                    for port in (self._get_node(self._innode(sgmt, from_dir, from_dim,
                        pos._replace(subblock_or_section = section)), PortDirection.input), )
                    if port is not None and port.is_physical)
            try:
                head = next(inodes)
            except StopIteration:
                continue
            if iskip:
                inodes = chain(inodes, iter((head, )))
            else:
                inodes = chain(iter((head, )), inodes)
            # output nodes iterator
            onodes = cycle(port[idx] for sgmt in (reversed(segments) if orev else segments)
                    for idx in (reversed(range(sgmt.width)) if orev else range(sgmt.width))
                    for section in (reversed(range(sgmt.length)) if orev else range(sgmt.length))
                    for port in (self._get_node(self._outnode(sgmt, direction, dimension,
                        pos._replace(subblock_or_section = section)), PortDirection.output), )
                    if port is not None)
            try:
                head = next(onodes)
            except StopIteration:
                continue
            if iskip:
                onodes = chain(iter((head, )), onodes)
            # add connections
            for inode in inodes:
                self.add_connections(inode, next(onodes))

    # == low-level API =======================================================
    @property
    def block_type(self):
        """Type of this routing block."""
        return BlockType.switch

    def populate_segments(self, segments, env = None, drive_truncated = True, bridge_from_connectionblock = False):
        """Populate the switch block with segment nodes.

        Args:
            segments (:obj:`list` [`SegmentPrototype` ]):
            env (`SwitchBlockEnvironment`): environment of this switch block. `SwitchBlockEnvironment()` by default
            drive_truncated (:obj:`bool`): if truncated segments should be driven by this switch block
            bridge_from_connectionblock (:obj:`bool`): if the segment driver from the switch block and this connection
                block should merge in the connection block
        """
        env = uno(env, SwitchBlockEnvironment())
        for sgmt, dir_, dim in product(iter(segments), Direction.all(), Dimension.all()):
            if env.has_outputs(dir_, dim):
                node = self._outnode(sgmt, dir_, dim)
                self._get_or_create_node(node, PortDirection.input, bridge_from_connectionblock,
                        not bridge_from_connectionblock)
                self._get_or_create_node(node, PortDirection.output, not bridge_from_connectionblock)
                if drive_truncated and not env.has_inputs(dir_, dim):
                    for section in range(1, sgmt.length):
                        node = self._outnode(sgmt, dir_, dim, (0, 0, section))
                        self._get_or_create_node(node, PortDirection.input, is_logical_source = True)
                        self._get_or_create_node(node, PortDirection.output)
            if env.has_inputs(dir_, dim):
                for section in range(sgmt.length):
                    self._get_or_create_node(self._innode(sgmt, dir_, dim, (0, 0, section)), PortDirection.input)

    def implement_wilton(self, segments):
        """Implement Wilton-style switch block.

        Args:
            segments (:obj:`list` [`SegmentPrototype` ]):
        """
        for to_dir, to_dim in product(Direction.all(), Dimension.all()):
            self._implement_wilton_quarter(segments, to_dir, to_dim)
