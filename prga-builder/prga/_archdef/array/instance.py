# Python 2 and 3 compatible
from prga.compatible import *

__all__ = ['BlockInstance', 'IOBlockInstance', 'TilePlaceholder']

from prga._archdef.portpin.pin import AbstractPin, Pin, DynamicPin
from prga._archdef.moduleinstance.instance import AbstractInstance
from prga._archdef.routing.common import AbstractRoutingNode
from prga._util.util import uno
from prga.exception import PRGAInternalError

# ----------------------------------------------------------------------------
# -- Abstract Routing Node Pin -----------------------------------------------
# ----------------------------------------------------------------------------
class AbstractRoutingNodePin(AbstractPin, AbstractRoutingNode):
    """Abstract base class for routing node pins.

    Args:
        parent (`AbstractBlockInstance`): the instance this pin belongs to
        port (`AbstractRoutingNodePort` or `AbstractBlockPort`): the port in the module that the instance instantiates
    """
    @property
    def _default_physical_source(self):
        node = self.parent.parent.get_node_source(self.node, self.port.is_bridge)
        if node is not None:
            if not node.is_physical_source:
                raise PRGAInternalError("'{}' is not a physical source".format(node))
            else:
                return node
        else:
            return super(AbstractRoutingNodePin, self)._default_physical_source

    @property
    def node(self):
        """The node that this pin represents."""
        return self.port.node._replace(position = self.port.node.position + self.parent.position)

    @property
    def node_type(self):
        """Type of this node."""
        return self.port.node_type

    @property
    def is_bridge(self):
        """Test if this is a routing node bridge."""
        return self.port.is_bridge

class RoutingNodePin(Pin, AbstractRoutingNodePin):
    """Static routing node pins.

    Args:
        parent (`AbstractBlockInstance`): the instance this pin belongs to
        port (`AbstractRoutingNodePort` or `AbstractBlockPort`): the port in the module that the instance instantiates
    """
    pass

class DynamicRoutingNodePin(DynamicPin, AbstractRoutingNodePin):
    """Dynamic routing node pins.

    Args:
        parent (`AbstractBlockInstance`): the instance this pin belongs to
        port (`AbstractRoutingNodePort` or `AbstractBlockPort`): the port in the module that the instance instantiates
    """
    pass

# ----------------------------------------------------------------------------
# -- AbstractBlockInstance ---------------------------------------------------
# ----------------------------------------------------------------------------
class NodePinsDelegate(Mapping):
    """Helper class for `AbstractBlockInstance.nodes` and `AbstractBlockInstance.bridges` property."""
    def __init__(self, inst, d):
        self.__inst = inst
        self.__d = d

    def __getitem__(self, key):
        try:
            item = self.__d[key]
        except KeyError:
            raise
        return self.__inst.pins[item.key]

    def __iter__(self):
        return iter(self.__d)

    def __len__(self):
        return len(self.__d)

class AbstractBlockInstance(AbstractInstance):
    """Abstract base class for block instances.

    Args:
        array (`Array`): the array that this instance belongs to
        block (`AbstractBlock`): the block that this instance instantiates
        position (`Position`): the position of this instance in the ``array``
    """
    def __init__(self, array, block, position):
        super(AbstractBlockInstance, self).__init__(array, block)
        self._position = position

    # == internal methods ====================================================
    def _create_static_pin(self, port):
        if port.is_logical:
            return RoutingNodePin(self, port)
        else:
            return Pin(self, port)

    def _create_dynamic_pin(self, port):
        if port.is_logical:
            return DynamicRoutingNodePin(self, port)
        else:
            return DynamicPin(self, port)

    # == low-level API =======================================================
    # -- properties to be overriden by sub-classes ---------------------------
    @property
    def nodes(self):
        """A mapping from node references to routing node pins."""
        return NodePinsDelegate(self, self.model.nodes)

    @property
    def bridges(self):
        """A mapping from node references to routing node bridge pins."""
        return NodePinsDelegate(self, self.model.bridges)

    @property
    def width(self):
        """Width of this block."""
        return self.model.width

    @property
    def height(self):
        """Height of this block."""
        return self.model.height
    
    @property
    def xoffset(self):
        """X-dimensional offset relative to the root block."""
        return 0

    @property
    def yoffset(self):
        """Y-dimensional offset relative to the root block."""
        return 0

    @property
    def is_root(self):
        """Test if this instance is the root block."""
        return True

    # -- derived properties --------------------------------------------------
    @property
    def position(self):
        """Position of this instance in the array."""
        return self._position

    @property
    def name(self):
        """Name of this instance."""
        if self.model.capacity > 1:
            return '{}_x{}y{}_{}'.format(self.model.name, self._position.x, self._position.y, self._position.subblock)
        else:
            return '{}_x{}y{}'.format(self.model.name, self._position.x, self._position.y)

    @property
    def is_logical(self):
        """Test if this is a logical instance."""
        return True

    @property
    def is_top_edge(self):
        """Test if this is the top edge of a big block."""
        return self.tile_type is TileType.logic and self.yoffset == self.height - 1

    @property
    def is_right_edge(self):
        """Test if this is the right edge of a big block."""
        return self.tile_type is TileType.logic and self.xoffset == self.width - 1

# ----------------------------------------------------------------------------
# -- BlockInstance -----------------------------------------------------------
# ----------------------------------------------------------------------------
class BlockInstance(AbstractBlockInstance):
    """Routing block and array instances.

    Args:
        array (`Array`): the array that this instance belongs to
        block (`RoutingBlock`): the routing block that this instance instantiates
        position (`Position`): the position of this instance in the ``array``
    """
    # == internal methods ====================================================
    @property
    def _model_ports(self):
        return self.model.physical_ports

    # == low-level API =======================================================
    @property
    def is_physical(self):
        """Test if this is a physical instance."""
        return True

# ----------------------------------------------------------------------------
# -- IO Block Instance -------------------------------------------------------
# ----------------------------------------------------------------------------
class IOBlockInstance(AbstractBlockInstance):
    """Root io block instance.

    Args:
        array (`Array`): the array that this instance belongs to
        block (`IOBlock`): the block that this instance instantiates
        position (`Position`): the position of this `BlockInstance` in the ``array``
    """
    def __init__(self, array, block, position):
        super(IOBlockInstance, self).__init__(array, block, position)
        self._binding = None

    # == internal methods ====================================================
    @property
    def _model_ports(self):
        if self.is_physical:
            return self.model._ports
        else:
            return self.model.ports

    def _bind_global(self, global_):
        """Bind this IOB to ``global_``."""
        if self._binding is not None:
            raise PRGAInternalError("IOB '{}' is already bound to global wire '{}'"
                    .format(self, self._binding.name))
        elif len(self._static_pins) > 0:
            raise PRGAInternalError("IOB '{}' already has physical connections so can't be replaced by global driver"
                    .format(self))
        self._binding = global_

    # == low-level API =======================================================
    @property
    def is_physical(self):
        """Test if this is a physical instance."""
        return self._binding is None

    @property
    def binding(self):
        """The global driver bound to this IOB."""
        return self._binding

# ----------------------------------------------------------------------------
# -- Tile Placeholder --------------------------------------------------------
# ----------------------------------------------------------------------------
class TilePlaceholder(AbstractBlockInstance):
    """Tile placeholder.

    Args:
        array (`Array`): the array that this instance belongs to
        block (`AbstractRoutingBlock`, `AbstractBlock`, `Array`): the block that this instance instantiates
        position (`Position`): the position of this instance in the ``array``
        type (`TileType`): type of the tile to be placeheld
        xoffset (:obj:`int`): the X-dimensional position relative to the root block
        yoffset (:obj:`int`): the Y-dimensional position relative to the root block
    """
    def __init__(self, array, block, position, type, xoffset, yoffset):
        super(TilePlaceholder, self).__init__(array, block, position)
        self._type = type
        self._xoffset = xoffset
        self._yoffset = yoffset

    # == internal methods ====================================================
    @property
    def _model_ports(self):
        return {}

    # == low-level API =======================================================
    @property
    def nodes(self):
        return {}

    @property
    def bridges(self):
        return {}

    @property
    def xoffset(self):
        """X-dimensional offset relative to the root block."""
        return self._xoffset

    @property
    def yoffset(self):
        """X-dimensional offset relative to the root block."""
        return self._yoffset

    @property
    def is_root(self):
        """Test if this instance is the root block."""
        return False

    @property
    def tile_type(self):
        """Type of this tile."""
        return self._type
