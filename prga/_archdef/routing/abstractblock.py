# -*- encoding: ascii -*-

"""Abstract base class for routing blocks."""

__all__ = ['AbstractRoutingBlock']

import logging
_logger = logging.getLogger(__name__)

from port import RoutingBlockInputPort, RoutingBlockOutputPort
from ..common import Dimension, PortDirection
from ..block.abstractblock import AbstractBlock
from ...exception import PRGAAPIError, PRGAInternalError
from ..._util.util import uno

from collections import namedtuple, Mapping, Sequence
from abc import abstractmethod
from itertools import izip

# ----------------------------------------------------------------------------
# -- AbstractRoutingBlock ----------------------------------------------------
# ----------------------------------------------------------------------------
class AbstractRoutingBlock(AbstractBlock):
    """Abstract base class for both connection block and switch block."""
    def __init__(self, context, name):
        super(AbstractRoutingBlock, self).__init__(context, name)
        self.__nodes = {}   # (reference, port direction) -> port

    # -- internal API --------------------------------------------------------
    class _RoutingNodeReferenceBit(namedtuple('_RoutingNodeReferenceBit_namedtuple', 'reference index')):
        """One bit of routing node references.

        Args:
            reference (`SegmentReference` or `BlockPinReference`): 
            index (:obj:`int`):
        """
        pass

    class __RoutingNodeDictProxy(Mapping):
        """A helper class which wraps the node mapping of a routing block."""
        def __init__(self, routing_block):
            self.__block = routing_block

        def __getitem__(self, reference):
            """Return the node referenced."""
            try:
                self.__block._validate_reference(reference)
            except PRGAInternalError as e:
                raise PRGAAPIError(str(e))
            if reference.is_segment:
                return tuple(AbstractRoutingBlock._RoutingNodeReferenceBit(reference, i)
                        for i in xrange(self.__block._context.segments[reference.name].width))
            elif reference.is_blockpin:
                return tuple(AbstractRoutingBlock._RoutingNodeReferenceBit(reference, i)
                        for i in xrange(self.__block._context.blocks[reference.block].ports[reference.port].width))
            else:
                raise RuntimeError

        def __iter__(self):
            """Returns an iterators over all keys to the nodes mapping."""
            return iter(self.__block._nodes)

        def __len__(self):
            """Returns the number of keys in the nodes mapping."""
            return len(self.__block._nodes)

    @property
    def _nodes(self):
        """A mapping from routing node references to ports of this block.
        
        Specifically: (`SegmentReference` or `BlockPinReference`, `PortDirection`) -> `RoutingBlockInputPort` or
        `RoutingBlockOutputPort`
        """
        return self.__nodes

    def _validate_reference(self, reference, direction = None):
        """Check if the reference could be present in the current block.
        
        Args:
            reference (`SegmentReference` or `BlockPinReference`):
            direction (`PortDirection`, default = None): if given, it's also checked if the reference matches the
                direction

        Raises:
            `PRGAAPIError`: if the reference should not be present in the current block.
        """
        if reference.is_segment:
            try:
                prototype = self._context.segments[reference.name]
            except KeyError:
                raise PRGAAPIError("Segment '{}' does not exist in architecture context '{}'"
                        .format(reference.name, self._context.name))
            if reference.section < 0 or reference.section >= prototype.length:
                raise PRGAAPIError("Segment '{}' is {}-tile long, but section '{}' is requested"
                        .format(reference.name, prototype.length, reference.section))
        elif reference.is_blockpin:
            try:
                block = self._context.blocks[reference.block]
            except KeyError:
                raise PRGAAPIError("Logic/IO block '{}' does not exist in architecture context '{}'"
                        .format(reference.block, self._context.name))
            try:
                port = block.ports[reference.port]
            except KeyError:
                raise PRGAAPIError("Logic/IO block '{}' does not have port '{}'"
                        .format(reference.block, reference.port))
            if port.is_clock or (port.is_input and port.is_global):
                raise PRGAAPIError(("Block port '{}.{}' is hard-wired to a global wire and cannot be "
                    "used as a routing node").format(reference.block, reference.port))
            if direction is not None and port.direction is not direction.opposite:
                raise PRGAAPIError("Block port '{}.{}' is {}"
                        .format(reference.block, reference.port, direction.name))
        else:
            raise RuntimeError

    def _query_port_name(self, reference, direction):
        """Query the port name given the reference and port direction."""
        if reference.is_segment:
            return 'sgmt_{}_{}{}_{}_{}'.format(reference.name, reference.direction.name,
                    'x' if reference.dimension is Dimension.horizontal else 'y',
                    reference.section, 'i' if direction is PortDirection.input else 'o')
        elif reference.is_blockpin:
            return 'pin_{}_{}_{}{}_{}'.format(reference.block, reference.subblock,
                    ('l' if reference.xoffset <= 0 else 'r') + str(abs(reference.xoffset)),
                    ('b' if reference.yoffset <= 0 else 't') + str(abs(reference.yoffset)),
                    reference.port)
        else:
            raise RuntimeError

    def _add_node(self, reference, direction):
        """Add a set of routing nodes to this block.

        Args:
            reference (`SegmentReference`, `BlockPinReference`):
            direction (`PortDirection`): direction of the port to be created

        Raises:
            `PRGAInternalError`: if the reference and the direction does not match

        This method will also create a port for the added node reference.
        """
        self._validate_reference(reference, direction)
        PortClass = RoutingBlockInputPort if direction is PortDirection.input else RoutingBlockOutputPort
        if reference.is_segment:
            prototype = self._context.segments[reference.name]
            port = self.__nodes[(reference, direction)] = PortClass(self,
                    self._query_port_name(reference, direction), prototype.width, reference)
            self._add_port(port)
        elif reference.is_blockpin:
            prototype = self._context.blocks[reference.block].ports[reference.port]
            port = self.__nodes[(reference, direction)] = PortClass(self,
                    self._query_port_name(reference, direction), prototype.width, reference)
            self._add_port(port)
        else:
            raise RuntimeError

    def _get_port(self, reference, direction, no_create = False):
        """Get the port for the givein reference and direction."""
        self._validate_reference(reference, direction)
        try:
            return self.__nodes[(reference, direction)]
        except KeyError:
            if no_create:
                return None
            else:
                self._add_node(reference, direction)
                return self.__nodes[(reference, direction)]

    # -- exposed API ---------------------------------------------------------
    @property
    def nodes(self):
        """A mapping from routing node references to routing nodes."""
        return self.__RoutingNodeDictProxy(self)

    def add_connections(self, sources, sinks, fully_connected = False):
        """Add configurable connections between routing nodes.

        Args:
            sources, sinks: a routing node, a bit of a routing node, a list of routing nodes, a list of bits of
                routing nodes, etc.
            fully_connected (:obj:`bool`, default=``False``): by default, the connections are created in a bit-wise
                pairing manner. If set to ``True``, a full connection will be created between the sources and sinks

        Raises:
            `PRGAAPIError`: if not fully connected and the number of source bits and the number of sink bits don't
                match, or any of the sources is not a logical source, or any of the sinks is not a logical sink

        Examples:
            >>> block = ... # assume a *vertical connection* block is created somehow
            # Assumptions:
            #   1. this vertical block sits between two 'clb' logic blocks which are identical
            #   2. 'clb' logic block is 1x1, with a 4-bit input 'in' on the left, a 1-bit output 'out' on the right,
            #       other information is irrelevent
            #   3. there are 4 'L1' segments running in each direction that are 1-tile long 
            # create a full connection between a block port and a set a segments
            >>> block.add_connections(block.nodes[BlockPinReference('clb', 'out')],
                    [block.nodes[SegmentReference('L1', Dimension.vertical, Direction.inc)][0],
                        block.nodes[SegmentReference('L1', Dimension.vertical, Direction.inc)][2],
                        block.nodes[SegmentReference('L1', Dimension.vertical, Direction.dec)][0],
                        block.nodes[SegmentReference('L1', Dimension.vertical, Direction.dec)][2]],
                    fully_connected = True)
            # create a bit-wise connection between a set of segments to a block port 
            >>> block.add_connections(block.nodes[SegmentReference('L1', Dimension.vertical, Direction.inc)],
                    block.nodes[BlockPinReference('clb', 'in', xoffset=1)])
            >>> block.add_connections(block.nodes[SegmentReference('L1', Dimension.vertical, Direction.dec)],
                    block.nodes[BlockPinReference('clb', 'in', xoffset=1)])
        """
        # 1. create the list of sources
        sources_ = []
        try:
            if isinstance(sources, self._RoutingNodeReferenceBit):
                sources_.append(self._get_port(sources.reference, PortDirection.input)[sources.index])
            else:
                for src in sources:
                    if isinstance(src, self._RoutingNodeReferenceBit):
                        sources_.append(self._get_port(src.reference, PortDirection.input)[src.index])
                    else:
                        for s in src:
                            sources_.append(self._get_port(s.reference, PortDirection.input)[s.index])
        except PRGAInternalError:
            raise PRGAAPIError(str(PRGAInternalError))
        # 2. create the list of sinks
        sinks_ = []
        try:
            if isinstance(sinks, self._RoutingNodeReferenceBit):
                sinks_.append(self._get_port(sinks.reference, PortDirection.output)[sinks.index])
            else:
                for sink in sinks:
                    if isinstance(sink, self._RoutingNodeReferenceBit):
                        sinks_.append(self._get_port(sink.reference, PortDirection.output)[sink.index])
                    else:
                        for s in sink:
                            sinks_.append(self._get_port(s.reference, PortDirection.output)[s.index])
        except PRGAInternalError:
            raise PRGAAPIError(str(PRGAInternalError))
        # 3. create the actual connections
        if fully_connected:
            for sink in sinks_:
                sink._add_logical_sources(sources_)
        else:
            if len(sources_) != len(sinks_):
                raise PRGAAPIError("The number of source bits ({}) does not match with the number of sink bits ({})"
                        .format(len(sources_), len(sinks_)))
            for source, sink in izip(iter(sources_), iter(sinks_)):
                sink._add_logical_sources(source)
