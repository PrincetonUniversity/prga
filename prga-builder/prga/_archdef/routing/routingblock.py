# Python 2 and 3 compatible
from prga.compatible import *

from prga._archdef.common import BlockType, Direction, Dimension, Direction, PortDirection
from prga._archdef.routing.common import Position
from prga._archdef.routing.connectionblock import ConnectionBlock
from prga._archdef.routing.switchblock import SwitchBlockEnvironment, SwitchBlock
from prga._util.util import uno

from itertools import product

# ----------------------------------------------------------------------------
# -- Routing Block = Connection Block + Quarter Switch Blocks ----------------
# ----------------------------------------------------------------------------
class RoutingBlock(ConnectionBlock, SwitchBlock):
    """Connecion block with quarter switch blocks.

    Args:
        name (:obj:`str`): name of this block
        dimension (`Dimension`): dimension of this connection block
    """

    # == low-level API =======================================================
    @property
    def block_type(self):
        """Type of this routing block."""
        return self.dimension.select(BlockType.xroute, BlockType.yroute)

    def populate_segments(self, segments, pos_env = None, neg_env = None, drive_truncated = True):
        """Populate the routing block with segments.

        Args:
            segments (:obj:`list` [`SegmentPrototype` ]):
            pos_env (`SwitchBlockEnvironment`): environment of the quarter switch block in the positive direction of
                this block. `SwitchBlockEnvironment` by default
            neg_env (`SwitchBlockEnvironment`): environment of the quarter switch block in the negative direction of
                this block. `SwitchBlockEnvironment` by default
            drive_truncated (:obj:`bool`): if truncated segments should be driven by this switch block
        """
        dim = self.dimension # short alias
        for dir_ in Direction.all(): # dir_ is the direction of the output segments
            env = uno(dir_.select(neg_env, pos_env), SwitchBlockEnvironment())
            env = dir_.select(dim.select(env._replace(right = True), env._replace(top = True)),
                    dim.select(env._replace(left = True), env._replace(bottom = True)))
            pos = dir_.select(dim.select(Position(-1, 0), Position(0, -1)), Position(0, 0))
            for sgmt in segments:
                for section in range(sgmt.length if drive_truncated and not env.has_inputs(dir_, dim) else 1):
                    node = self._outnode(sgmt, dir_, dim, pos._replace(subblock_or_section = section))
                    self._get_or_create_node(node, PortDirection.input, is_logical_source = True)
                    self._get_or_create_node(node, PortDirection.output)
            for sgmt, from_dir, from_dim in product(iter(segments), Direction.all(), Dimension.all()):
                if from_dir is dir_.opposite and from_dim is dim:
                    continue
                if env.has_inputs(from_dir, from_dim):
                    for section in range(sgmt.length):
                        self._get_or_create_node(self._innode(sgmt, from_dir, from_dim,
                            pos._replace(subblock_or_section = section)), PortDirection.input)

    def implement_wilton(self, segments):
        for dir_ in Direction.all(): # dir_ is the direction of the output segments
            pos = dir_.select(self.dimension.select(Position(-1, 0), Position(0, -1)), Position(0, 0))
            self._implement_wilton_quarter(segments, dir_, self.dimension, pos)
