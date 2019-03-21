# Python 2 and 3 compatible
from prga.compatible import *

__all__ = ['LogicalSegmentSource', 'RoutingNodeInputPort', 'RoutingNodeOutputPort', 'RoutingNodeInputBridge',
        'RoutingNodeOutputBridge']

from prga._archdef.common import PortDirection
from prga._archdef.portpin.bus import PortOrPinBus
from prga._archdef.portpin.port import AbstractPort
from prga._archdef.routing.common import AbstractRoutingNode, Segment, BlockPin
from prga.exception import PRGAInternalError

from abc import abstractproperty

# ----------------------------------------------------------------------------
# -- Abstract Routing Node Port ----------------------------------------------
# ----------------------------------------------------------------------------
class AbstractRoutingNodePort(AbstractPort, AbstractRoutingNode):
    """Abstract base class for routing node ports.

    Args:
        parent (`AbstractRoutingBlock`): the routing block this port belongs to
        node (`Segment` or `BlockPin`): the routing node this port represents
    """
    def __init__(self, parent, node):
        super(AbstractRoutingNodePort, self).__init__(parent)
        self._node = node

    @property
    def name(self):
        """Name of this port."""
        if self._node.is_segment:
            if self._node.prototype.length > 1:
                return '{}_{}_{}_{}{}{}{}_{}{}_{}'.format('brg' if self.is_bridge else 'sgmt',
                        self.direction.select('i', 'o'), self._node.name,
                        'u' if self._node.position.x < 0 else 'x', abs(self._node.position.x),
                        'v' if self._node.position.y < 0 else 'y', abs(self._node.position.y),
                        self._node.direction.name, self._node.dimension.name, self._node.position.section)
            else:
                return '{}_{}_{}_{}{}{}{}_{}{}'.format('brg' if self.is_bridge else 'sgmt',
                        self.direction.select('i', 'o'), self._node.name,
                        'u' if self._node.position.x < 0 else 'x', abs(self._node.position.x),
                        'v' if self._node.position.y < 0 else 'y', abs(self._node.position.y),
                        self._node.direction.name, self._node.dimension.name)
        else:
            if self._node.prototype.parent.capacity > 1:
                return 'blkpin_{}_{}_{}{}{}{}_{}_{}'.format(self.direction.select('i', 'o'), self._node.block,
                        'u' if self._node.position.x < 0 else 'x', abs(self._node.position.x),
                        'v' if self._node.position.y < 0 else 'y', abs(self._node.position.y),
                        self._node.position.subblock, self._node.port)
            else:
                return 'blkpin_{}_{}_{}{}{}{}_{}'.format(self.direction.select('i', 'o'), self._node.block,
                        'u' if self._node.position.x < 0 else 'x', abs(self._node.position.x),
                        'v' if self._node.position.y < 0 else 'y', abs(self._node.position.y),
                        self._node.port)

    @abstractproperty
    def is_bridge(self):
        """Test if this is a bridge port."""
        raise NotImplementedError

    @property
    def key(self):
        """Key of this port in the mapping of the parent."""
        return (self._node, self.direction)

    @property
    def node(self):
        """The routing node that this port represents."""
        return self._node

    @property
    def node_type(self):
        """Type of this routing node."""
        return self._node.node_type

    @property
    def width(self):
        """Width of this port."""
        return self._node.prototype.width

    @property
    def is_clock(self):
        """Test if this is a clock."""
        return False

    @property
    def is_logical(self):
        """Test if this is a logical port."""
        return True

# ----------------------------------------------------------------------------
# -- Routing Node Port -------------------------------------------------------
# ----------------------------------------------------------------------------
class LogicalSegmentSource(AbstractRoutingNodePort, PortOrPinBus):
    """Logical-only segment source.

    Args:
        parent (`AbstractRoutingBlock`): the routing block this port belongs to
        node (`Segment` or `BlockPin`): the routing node this port represents
    """
    @property
    def direction(self):
        """Direction of this port."""
        return PortDirection.input

    @property
    def is_bridge(self):
        """Test if this is a bridge port."""
        return False

class RoutingNodeInputPort(LogicalSegmentSource):
    """Input port for routing nodes.

    Args:
        parent (`AbstractRoutingBlock`): the routing block this port belongs to
        node (`Segment` or `BlockPin`): the routing node this port represents
    """
    @property
    def is_physical(self):
        """Test if this is a physical port."""
        return True

class RoutingNodeInputBridge(RoutingNodeInputPort):
    """Input bridge for routing nodes.

    Args:
        parent (`AbstractRoutingBlock`): the routing block this port belongs to
        node (`Segment` or `BlockPin`): the routing node this port represents
    """
    @property
    def is_bridge(self):
        """Test if this is a bridge port."""
        return True

class RoutingNodeOutputPort(AbstractRoutingNodePort, PortOrPinBus):
    """Output port for routing nodes.

    Args:
        parent (`RoutingBlock`): the routing block this port belongs to
        node (`Segment` or `BlockPin`): the routing node this port represents
    """
    @property
    def direction(self):
        """Direction of this port."""
        return PortDirection.output

    @property
    def is_physical(self):
        """Test if this is a physical port."""
        return True

    @property
    def is_bridge(self):
        """Test if this is a bridge port."""
        return False

class RoutingNodeOutputBridge(RoutingNodeOutputPort):
    """Output bridge for routing nodes.

    Args:
        parent (`AbstractRoutingBlock`): the routing block this port belongs to
        node (`Segment` or `BlockPin`): the routing node this port represents
    """
    @property
    def is_bridge(self):
        """Test if this is a bridge port."""
        return True
