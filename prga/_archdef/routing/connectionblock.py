# -*- encoding: ascii -*-

"""Connection blocks."""

__all__ = ['ConnectionBlockEnvironment', 'BlockPinFCValue', 'BlockFCValue', 'ConnectionBlock']

import logging
_logger = logging.getLogger(__name__)

from resource import SegmentReference, BlockPinReference
from abstractblock import AbstractRoutingBlock
from ..common import Dimension, SegmentDirection, PortDirection, BlockType, Side
from ...exception import PRGAAPIError
from ..._util.util import uno

from collections import namedtuple, Sequence
from itertools import izip, product, imap, ifilter
import math

# ----------------------------------------------------------------------------
# -- ConnectionBlockEnvironment ----------------------------------------------
# ----------------------------------------------------------------------------
class ConnectionBlockEnvironment(namedtuple('ConnectionBlockEnvironment_namedtuple',
    'dimension block_lb block_rt offset_lb offset_rt')):
    """The environment that a certain connection block fits in.

    Args:
        dimension (`Dimension`): the dimension of the channel that the connection block sits upon
        block_lb block_rt (:obj:`str`): the name of the blocks adjacent to this connection block
        offset_lb offset_rt (:obj:`int`): if any of the adjacent block is larger than 1x1, an offset shows where the
            connection block is relative to the adjacent block
    """
    pass

# ----------------------------------------------------------------------------
# -- Block FC ----------------------------------------------------------------
# ----------------------------------------------------------------------------
class BlockPinFCValue(namedtuple('BlockPinFCValue_namedtuple', 'default segment_map')):
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
            return int(math.ceil(fc * segment.width * multiplier))
        else:
            raise RuntimeError

class BlockFCValue(namedtuple('BlockFCValue_namedtuple', 'default_in default_out pin_map')):
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
                    dict( (k, BlockPinFCValue(v)) for k, v in (default_in[2] if len(default_in) > 2 else {}).iteritems() ))
        else:
            return super(BlockFCValue, cls).__new__(cls, BlockPinFCValue(default_in),
                    BlockPinFCValue(uno(default_out, default_in)),
                    dict( (k, BlockPinFCValue(v)) for k, v in uno(pin_map, {}).iteritems() ))

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
# -- ConnectionBlock ---------------------------------------------------------
# ----------------------------------------------------------------------------
class ConnectionBlock(AbstractRoutingBlock):
    """Horizontal and vertical connection block.

    Args:
        context (`ArchitectureContext`): the architecture context this model belongs to
        name (:obj:`str`): name of this block
        dimension (`Dimension`): the dimension of this connection block
        block_lb (`LogicBlock` or `IOBlock`, default=None): the block to the left if this is a vertical connection
            block, or the block to the bottom if this is a horizontal connection block
        block_rt (`LogicBlock` or `IOBlock`, default=None): the block to the right if this is a vertical connection
            block, or the block to the top if this is a horizontal connection block
        offset_lb (:obj:`int`, default=0): if ``block_lb`` is larger than 1x1, where is this connection block relative
            to the root tile of ``block_lb``. This offset value is the X-dimensional offset if this is a horizontal
            connection block, or the Y-dimensional offset if this is a vertical connection block
        offset_rt (:obj:`int`, default=0): see ``offset_lb``

    The constructor will only create an empty connection block with no port and thus no connections. However, the
    adjacent blocks are all encapsulated, so that invalid connections cannot be added to this connection block.
    """
    def __init__(self, context, name, dimension, block_lb = None, block_rt = None, offset_lb = 0, offset_rt = 0):
        super(ConnectionBlock, self).__init__(context, name)
        self.__dimension = dimension
        self.__block_lb = block_lb
        self.__block_rt = block_rt
        self.__offset_lb = offset_lb
        self.__offset_rt = offset_rt

    def __get_block(self, side):
        """Get the block at the given side of this connection block.

        Args:
            side (`Side`):

        Raises:
            `PRGAAPIError`: if accessing left/right block of a horizontal connection block, or accessing top/bottom
                block of a vertical connection block

        Returns:
            `LogicBlock` or `IOBlock`:
        """
        if ( (self.dimension is Dimension.horizontal and side in (Side.left, Side.right)) or
                (self.dimension is Dimension.vertical and side in (Side.top, Side.bottom)) ):
            raise PRGAAPIError("Cannot access the logic/io block at the {} of {} connection block '{}'"
                    .format(side.name, self.dimension.name))
        elif side in (Side.left, Side.bottom):
            return self.__block_lb
        elif side in (Side.right, Side.top):
            return self.__block_rt
        else:
            raise RuntimeError

    def __get_offset(self, side):
        """Get the offset at the given side of this connection block.

        Args:
            side (`Side`):

        Raises:
            `PRGAAPIError`: if accessing left/right offset of a horizontal connection block, or accessing top/bottom
                offset of a vertical connection block

        Returns:
            xoffset, yoffset (:obj:`int`): the offset of this connection block relative to the logic/io block sitting
                at the given side
        """
        if ( (self.dimension is Dimension.horizontal and side in (Side.left, Side.right)) or
                (self.dimension is Dimension.vertical and side in (Side.top, Side.bottom)) ):
            raise PRGAAPIError("Cannot access the offset at the {} of {} connection block '{}'"
                    .format(side.name, self.dimension.name))
        elif side is Side.left:
            return 0 if self.__block_lb is None else (self.__block_lb.width - 1), self.__offset_lb
        elif side is Side.right:
            return -1, self.__offset_rt
        elif side is Side.top:
            return self.__offset_rt, -1
        elif side is Side.bottom:
            return self.__offset_lb, 0 if self.__block_lb is None else (self.__block_lb.height - 1)
        else:
            raise RuntimeError

    # -- internal API --------------------------------------------------------
    def _validate_reference(self, reference, direction = None):
        # """Check if the reference could be present in the current block.
        # 
        # Args:
        #     reference (`SegmentReference` or `BlockPinReference`):
        #     direction (`PortDirection`, default = None): if given, it's also checked if the reference and the
        #         direction match

        # Raises:
        #     `PRGAAPIError`: if the reference should not be present in the current block.
        # """
        super(ConnectionBlock, self)._validate_reference(reference, direction)
        if reference.is_segment:
            if reference.dimension is not self.dimension:
                raise PRGAAPIError("Cannot refer to {} segments in {} connection block '{}'"
                        .format(reference.dimension, self.dimension, self.name))

    def _add_node(self, reference, direction):
        super(ConnectionBlock, self)._add_node(reference, direction)
        if reference.is_segment and direction is PortDirection.output:
            self.add_connections(self.nodes[reference], self.nodes[reference])

    def _materialize_connections(self):
        # 1. pin/seg -> seg connections
        for port in ifilter(lambda port: port.is_output and port.node_reference.is_segment, self.ports.itervalues()):
            input_ = self._nodes[port.node_reference, PortDirection.input]
            for logical, sink in izip(input_, port):
                sources = tuple(x._physical_cp for x in sink._logical_sources)
                sink = sink._physical_cp
                if len(sources) > 1: # a mux is needed
                    instance = self._instantiate_configurable_mux(sources, sink)
                    p = sink._physical_source = instance._pins['o'][0]
                    logical._physical_cp, p._logical_cp = p, logical
                    self._add_instance(instance)
                elif len(sources) == 1: # a direct connection
                    sink._physical_source = sources[0]
        # 2. seg -> pin connections
        for port in ifilter(lambda port: port.is_output and port.node_reference.is_blockpin, self.ports.itervalues()):
            for sink in port:
                sources = tuple(x._physical_cp for x in sink._logical_sources)
                sink = sink._physical_cp
                if len(sources) > 1: # a mux is needed
                    instance = self._instantiate_configurable_mux(sources, sink)
                    sink._physical_source = instance._pins['o'][0]
                    self._add_instance(instance)
                elif len(sources) == 1: # a direction connection
                    sink._physical_source = sources[0]

    # -- exposed API ---------------------------------------------------------
    @property
    def block_type(self):
        """Type of this block."""
        return (BlockType.horizontalconnection if self.dimension is Dimension.horizontal else
                BlockType.verticalconnection)

    @property
    def dimension(self):
        """Dimension of this connection block."""
        return self.__dimension

    @property
    def environment(self):
        """The environment this connection block sits in."""
        return ConnectionBlockEnvironment(self.dimension,
                None if self.__block_lb is None else self.__block_lb.name,
                None if self.__block_rt is None else self.__block_rt.name,
                self.__offset_lb, self.__offset_rt)

    def implement_fc(self, fc_lb, fc_rt):
        """Fill the connection block using FC values. [TODO: add explanation on FC values]

        Args:
            fc_lb, fc_rt (`BlockFCValue`): the FC value for each block adjacent to this connection block

        Raises:
            `PRGAAPIError`: if an invalid FC value is passed in

        For each argument that's of type `BlockFCValue`, it's also acceptable to pass in any argument that is valid to
        the `BlockFCValue` constructor.
        """
        if len(self._nodes) > 0:
            raise PRGAAPIError("`implement_fc` should never be used after custom connections are added")
        for side, fc in izip(
                iter((Side.left, Side.right) if self.dimension is Dimension.vertical else (Side.bottom, Side.top)),
                imap(BlockFCValue, (fc_lb, fc_rt))):
            block = self.__get_block(side)
            if block is None:
                continue
            xoffset, yoffset = self.__get_offset(side)      # this is the offset of the CB relative to the CLB
            pxofs = 0 if side is Side.right else xoffset    # this is the port offset
            pyofs = 0 if side is Side.top else yoffset
            isic = {name : 0 for name in self._context.segments} # input-to-segment index counter
            osic = {name : 0 for name in self._context.segments} # output-to-segment index counter
            for port in block.ports.itervalues():
                if not (port.side is side.opposite and port.xoffset == pxofs and port.yoffset == pyofs):
                    continue
                if port.is_clock or (port.is_input and port.is_global):
                    continue
                if port.is_input:
                    for sgmt in self._context.segments.itervalues():
                        nconn = fc.port_fc(port, sgmt, True)                # number of connections
                        if nconn == 0:
                            continue
                        istep = max(1, sgmt.length * sgmt.width / nconn)    # index step
                        for _, pin_idx in product(xrange(nconn), xrange(port.width)):
                            section = isic[sgmt.name] % sgmt.length
                            sgmt_idx = isic[sgmt.name] / sgmt.length
                            for subblock, sgmt_dir in product(xrange(block.capacity), SegmentDirection.all()):
                                source = self._RoutingNodeReferenceBit(
                                        SegmentReference(sgmt.name, self.dimension, sgmt_dir, section),
                                        sgmt_idx)
                                sink = self._RoutingNodeReferenceBit(
                                        BlockPinReference(block.name, port.name, -xoffset, -yoffset, subblock),
                                        pin_idx)
                                self.add_connections(source, sink)
                            nic = isic[sgmt.name] + istep   # next index counter value
                            if istep > 1 and nic >= sgmt.width * sgmt.length:
                                nic += 1
                            isic[sgmt.name] = nic % (sgmt.width * sgmt.length)
                elif port.is_output:
                    for sgmt in self._context.segments.itervalues():
                        nconn = fc.port_fc(port, sgmt, False)
                        if nconn == 0:
                            continue
                        istep = max(1, sgmt.width / nconn)
                        for _, pin_idx in product(xrange(nconn), xrange(port.width)):
                            sgmt_idx = osic[sgmt.name]
                            for subblock, sgmt_dir in product(xrange(block.capacity), SegmentDirection.all()):
                                source = self._RoutingNodeReferenceBit(
                                        BlockPinReference(block.name, port.name, -xoffset, -yoffset, subblock),
                                        pin_idx)
                                sink = self._RoutingNodeReferenceBit(
                                        SegmentReference(sgmt.name, self.dimension, sgmt_dir, 0),
                                        sgmt_idx)
                                self.add_connections(source, sink)
                            nic = osic[sgmt.name] + istep
                            if istep > 1 and nic >= sgmt.width:
                                nic += 1
                            osic[sgmt.name] = nic % sgmt.width
