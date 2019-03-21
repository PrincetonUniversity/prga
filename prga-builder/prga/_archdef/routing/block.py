# Python 2 and 3 compatible
from prga.compatible import *

from prga._archdef.common import ModuleType, PortDirection
from prga._archdef.moduleinstance.module import (AbstractNonLeafModule,
        MutableLeafModule, MutableNonLeafModule, LogicallyConnectableModule)
from prga._archdef.moduleinstance.configurable import ConfigurableNonLeafModule
from prga._archdef.routing.port import (LogicalSegmentSource, RoutingNodeInputPort, RoutingNodeOutputPort,
        RoutingNodeInputBridge, RoutingNodeOutputBridge)
from prga._util.util import DictDelegate
from prga.exception import PRGAInternalError, PRGAAPIError

from abc import abstractproperty, abstractmethod
from collections import namedtuple
from itertools import chain

# ----------------------------------------------------------------------------
# -- Abstract Block ----------------------------------------------------------
# ----------------------------------------------------------------------------
class AbstractBlock(AbstractNonLeafModule):
    """Abstract base class for all blocks including arrays.

    Args:
        name (:obj:`str`): name of this block
    """
    # == low-level API =======================================================
    @property
    def type(self):
        """Type of this module."""
        return ModuleType.block

    @abstractproperty
    def block_type(self):
        """Type of this block."""
        raise NotImplementedError

    @abstractproperty
    def nodes(self):
        """A mapping from node references to routing nodes."""
        raise NotImplementedError

    @property
    def bridges(self):
        """A mapping from node references to routing node bridges."""
        return {}

    @property
    def is_physical(self):
        """Test if this is a physical module."""
        return True

    @property
    def is_logical(self):
        """Test if this is a logical module."""
        return True

    @property
    def width(self):
        """Width of this block."""
        return 1

    @property
    def height(self):
        """Height of this block."""
        return 1

    @property
    def capacity(self):
        """How many block instances can be placed in one tile."""
        return 1

    @abstractmethod
    def covers_tile(self, x, y, type_):
        """Test if a position is in the array.

        Args:
            x (:obj:`int`): the X-dimensional position
            y (:obj:`int`): the Y-dimensional position
            type\_ (`TileType`): type\_ of the tile
        """
        raise NotImplementedError

# ----------------------------------------------------------------------------
# -- Internal Node Key -------------------------------------------------------
# ----------------------------------------------------------------------------
class NodeKey(namedtuple('NodeKey', 'node port_direction')):
    """Internal index for nodes in a block."""
    pass

# ----------------------------------------------------------------------------
# -- Node Mapping Delegate ---------------------------------------------------
# ----------------------------------------------------------------------------
class NodesDelegate(Mapping):
    """A helper class for mapping from node references to port/pins."""
    def __init__(self, d):
        self.__d = d

    def __getitem__(self, key):
        if key.is_blockpin:
            item = self.__d.get(NodeKey(key, PortDirection.input),
                    self.__d.get(NodeKey(key, PortDirection.output), None))
            if item is not None:
                return item
        else:
            for node in key.iter_all_equivalents():
                item = self.__d.get(NodeKey(node, PortDirection.input),
                        self.__d.get(NodeKey(node, PortDirection.output), None))
                if item is not None:
                    return item
        raise KeyError(key)

    def __iter__(self):
        return iter(node for node, _ in self.__d)

    def __len__(self):
        return len(self.__d)

# ----------------------------------------------------------------------------
# -- Abstract Routing Block or Array -----------------------------------------
# ----------------------------------------------------------------------------
class AbstractRoutingBlockOrArray(AbstractBlock, MutableLeafModule):
    """Abstract base class for routing blocks and arrays.
    
    Args:
        name (:obj:`str`): name of this block
    """
    # == internal methods ====================================================
    def _validate_node(self, node):
        """Validate if ``node`` should be added to this routing block or array."""
        pass

    def _get_node(self, node, port_direction):
        """Get the port for ``node`` in ``port_direction``."""
        # 1. search equivalent port
        if node.is_blockpin:
            return self._ports.get(NodeKey(node, port_direction), None)
        else:
            for equiv in node.iter_all_equivalents():
                try:
                    return self._ports[NodeKey(equiv, port_direction)]
                except KeyError:
                    pass
            return None

    def _create_node(self, node, port_direction, is_bridge, is_logical_source):
        PortCls = None
        if node.is_blockpin:
            PortCls = port_direction.select(RoutingNodeInputPort, RoutingNodeOutputPort)
        else:
            PortCls = port_direction.select(RoutingNodeInputBridge if is_bridge else
                    LogicalSegmentSource if is_logical_source else RoutingNodeInputPort,
                    RoutingNodeOutputBridge if is_bridge else RoutingNodeOutputPort)
        return PortCls(self, node)

    def _get_or_create_node(self, node, port_direction, is_bridge = False, is_logical_source = False):
        """Get or create a port for ``node``.

        Args:
            node (`BlockPin` or `Segment`):
            port_direction (`PortDirection`):
            is_bridge (:obj:`bool`):
            is_logical_source (:obj:`bool`):
        """
        self._validate_node(node)
        # 1. search equivalent port
        port = self._get_node(node, port_direction)
        # 2. validate the port found
        if port is not None:
            if is_bridge != port.is_bridge:
                raise PRGAInternalError("Node '{}' in block '{}' is {}a bridge"
                        .format(node, self, "not " if is_bridge else ""))
            elif is_logical_source == port.is_physical:
                raise PRGAInternalError("Node '{}' in block '{}' is {}physical"
                        .format(node, self, "" if is_logical_source else "not "))
            return port
        # 3. create and add port
        return self._ports.setdefault(NodeKey(node, port_direction),
                self._create_node(node, port_direction, is_bridge, is_logical_source))

    # == low-level API =======================================================
    @property
    def nodes(self):
        """Mapping from `Segment` or `BlockPin` to routing node ports."""
        return NodesDelegate(DictDelegate(self._ports,
            lambda kv: kv[1].is_logical and kv[1].is_physical and not kv[1].is_bridge))

    @property
    def bridges(self):
        """Mapping from `Segment` or `BlockPin` to routing node bridges."""
        return NodesDelegate(DictDelegate(self._ports,
            lambda kv: kv[1].is_logical and kv[1].is_physical and kv[1].is_bridge))

# ----------------------------------------------------------------------------
# -- Abstract Routing Block --------------------------------------------------
# ----------------------------------------------------------------------------
class AbstractRoutingBlock(AbstractRoutingBlockOrArray, LogicallyConnectableModule, ConfigurableNonLeafModule):
    """Abstract routing blocks.

    Args:
        name (:obj:`str`): name of this block
    """
    # == internal methods ====================================================
    def _remap_logical_bit(self, bit, is_sink = False):
        """Remap ``bit`` to the correct logical bit.

        Args:
            bit (`AbstractRoutingNodePort`-subclass): a routing node bit 
            is_sink (:obj:`bool`): if set to True, map to the sink of a routing node
        """
        if bit.bus.is_blockpin:
            return bit
        assert bit.bus.is_segment
        if bit.bus.direction.select(not is_sink, is_sink):
            return bit
        port = self._get_node(bit.bus.node, PortDirection.output if is_sink else PortDirection.input)
        if port is not None:
            return port[bit.index]
        else:
            raise PRGAAPIError("Routing block '{}' does not have node '{}' as a {}"
                    .format(self, bit.node, 'sink' if is_sink else 'source'))

    # == low-level API =======================================================
    def covers_tile(self, x, y, type_):
        return x == 0 and y == 0 and type_ is self.block_type.tile_type

    # == high-level API ======================================================
    def add_connections(self, sources, sinks, fully_connected = False):
        """Add configurable connections between routing nodes.

        Args:
            sources: a bit, a list of bits, a port, a list of ports, etc.
            sinks: a bit, a list of bits, a port, a list of ports, etc.
            fully_connected (:obj:`bool`): by default, the connections are created in a bit-wise pairing manner. If
                set to ``True``, a full connection will be created between the ``sources`` and ``sinks``
        """
        # 1. create the list of sources
        sources_ = []
        try:
            for src in sources:
                try:
                    for s in src:
                        sources_.append(self._remap_logical_bit(s))
                except TypeError:
                    sources_.append(self._remap_logical_bit(src))
        except TypeError:
            sources_.append(self._remap_logical_bit(sources))
        # 2. create the list of sinks
        sinks_ = []
        try:
            for sink in sinks:
                try:
                    for s in sink:
                        sinks_.append(self._remap_logical_bit(s, True))
                except TypeError:
                    sinks_.append(self._remap_logical_bit(sink, True))
        except TypeError:
            sinks_.append(self._remap_logical_bit(sinks, True))
        super(AbstractRoutingBlock, self).add_connections(sources_, sinks_, fully_connected)
