# -*- encoding: ascii -*-

"""VPR extensions to the architecture context."""

__all__ = ['VPRExtension']

import logging
_logger = logging.getLogger(__name__)

from .._archdef.common import SegmentDirection, Dimension
from .._context.flow import AbstractPass

import itertools
from collections import namedtuple

# ----------------------------------------------------------------------------
# -- _VPRSegmentExtension ----------------------------------------------------
# ----------------------------------------------------------------------------
class _VPRSegmentExtension(namedtuple('_VPRSegmentExtension_namedtuple', 'id ptc track_id')):
    """VPR's extension to `SegmentPrototype`.
    
    Args:
        id (:obj:`int`): the ``segment_id`` of this segment prototype
        ptc (:obj:`int`): the base PTC of the segments of this prototype
        track_id (:obj:`dict` [:obj:`tuple` \(:obj:`bool`, :obj:`bool`, `SegmentDirection`\) -> :obj:`int` ]): A
            mapping from \(if there is channel to the left/bottom of this channel, if there is channel to the
            right/top of this channel, the direction of this channel\) to the ID offset
    """
    pass

# ----------------------------------------------------------------------------
# -- _VPRBlockExtension ------------------------------------------------------
# ----------------------------------------------------------------------------
class _VPRBlockExtension(namedtuple('_VPRBlockExtension_namedtuple', 'id pin_id pin_size')):
    """VPR's extension to `LogicBlock` and `IOBlock`.

    Args:
        id (:obj:`int`): the ``block_type_id`` of this block
        pin_id (:obj:`dict` [:obj:`str` -> :obj:`int` ]): a mapping from port name to base PTC
        pin_size (:obj:`int`): total number of pins of this block
    """
    pass

# ----------------------------------------------------------------------------
# -- _VPRTileExtension -------------------------------------------------------
# ----------------------------------------------------------------------------
class _VPRTileExtension(namedtuple('_VPRTileExtension_namedtuple', 'logical_pin physical_pin hchan vchan')):
    """VPR's extension to `Tile`.
    
    Args:
        logical_pin, physical_pin, hchan, vchan (:obj:`int`): based rouing node ID for pins and segments

    Logical/physical pin IDs are stored in the root tile.
    """
    pass

# ----------------------------------------------------------------------------
# -- _VPRExtension -----------------------------------------------------------
# ----------------------------------------------------------------------------
class _VPRExtension(object):
    """VPR's top-level extension to `ArchitectureContext`."""
    def __init__(self, context):
        self.__context = context
        # 1. assign segment id & PTC
        self.__segments = {}
        ptc = 0
        for idx, segment in enumerate(context.segments.itervalues()):
            self.__segments[segment.name] = _VPRSegmentExtension(idx, ptc, {})
            ptc += 2 * segment.width * segment.length
        self.__channel_width = ptc
        # 2. assign segment node id (different than PTC)
        for space_dec, space_inc in itertools.product(iter((False, True)), iter((False, True))):
            id_ = 0
            for segment in context.segments.itervalues():
                self.__segments[segment.name].track_id[space_dec, space_inc, SegmentDirection.inc] = id_
                id_ += segment.width * (segment.length if not space_dec else 1)
                self.__segments[segment.name].track_id[space_dec, space_inc, SegmentDirection.dec] = id_
                id_ += segment.width * (segment.length if not space_inc else 1)
        # 3. assign block id
        self.__blocks = {}
        for idx, block in enumerate(context.blocks.itervalues()):
            ptc, pins = 0, {}
            for port in block.ports.itervalues():
                pins[port.name] = ptc
                ptc += port.width
            self.__blocks[block.name] = _VPRBlockExtension(idx + 1, pins, ptc)
        # 4. assign node id
        node_id = 0
        array = context.array
        self.__array = [[None for _ in xrange(array.height)] for _ in xrange(array.width)]
        for tile in array._iter_tiles():
            logical_pin, physical_pin, hchan, vchan = (None, ) * 4
            if tile.is_root and tile.block is not None:
                logical_pin = node_id
                node_id += self.__blocks[tile.block.name].pin_size * tile.block.capacity
                physical_pin = node_id
                node_id += self.__blocks[tile.block.name].pin_size * tile.block.capacity
            if tile.x < array.width - 1 and tile.y < array.height - 1:
                if tile.x > 0 and tile.is_top_edge:
                    hchan = node_id
                    node_id += sum(segment.width * ((segment.length if tile.space_decx == 0 else 1) +
                        (segment.length if tile.space_incx == 0 else 1))
                        for segment in context.segments.itervalues())
                if tile.y > 0 and tile.is_right_edge:
                    vchan = node_id
                    node_id += sum(segment.width * ((segment.length if tile.space_decy == 0 else 1) +
                        (segment.length if tile.space_incy == 0 else 1))
                        for segment in context.segments.itervalues())
            self.__array[tile.x][tile.y] = _VPRTileExtension(logical_pin, physical_pin, hchan, vchan)
        self.__node_size = node_id
        # 4. other data
        self.__common_arguments = {'constant_net_method': 'route'}
        self.__pack_arguments = {}
        self.__place_arguments = {}
        self.__route_arguments = {'route_chan_width': self.__channel_width}

    @property
    def context(self):
        """The `ArchitectureContext` this extension extends to."""
        return self.__context

    @property
    def segments(self):
        """Extensions for segments."""
        return self.__segments

    @property
    def blocks(self):
        """Extensions for blocks."""
        return self.__blocks

    @property
    def channel_width(self):
        """Channel width."""
        return self.__channel_width

    @property
    def array(self):
        """Extensions for tiles."""
        return self.__array

    @property
    def node_size(self):
        """Total number of routing nodes."""
        return self.__node_size

    @property
    def common_arguments(self):
        """CLI arguments for VPR."""
        return self.__common_arguments

    @property
    def pack_arguments(self):
        """CLI arguments for VPR packer."""
        return self.__pack_arguments

    @property
    def place_arguments(self):
        """CLI arguments for VPR placer."""
        return self.__place_arguments

    @property
    def route_arguments(self):
        """CLI arguments for VPR router."""
        return self.__route_arguments

    def get_node_ptc(self, node, index):
        """Get the PTC for the given routing node.

        Args:
            node (`SegmentNode` or `BlockPin`): the segment/block pin node
            index (:obj:`int`): the index of the track/bit in the bus

        Returns:
            :obj:`int`:
        """
        if node.is_blockpin:
            ext = self.__blocks[node.parent_instance.block.name]
            return ext.pin_size * node.subblock + ext.pin_id[node.name] + index
        else:
            ptc = self.__segments[node.name].ptc
            if node.direction is SegmentDirection.inc:
                offset = ( (node.x if node.dimension is Dimension.horizontal else node.y)
                        + node.prototype.length - node.section - 1) % node.prototype.length
                return ptc + 2 * (node.prototype.width * offset + index)
            else:
                offset = ( (node.x if node.dimension is Dimension.horizontal else node.y)
                        + node.section) % node.prototype.length
                return ptc + 2 * (node.prototype.width * offset + index) + 1

    def get_node_id(self, node, index, physical = True):
        """Get the routing node ID for the given routing node.

        Args:
            node (`SegmentNode` or `BlockPin`): the segment/block pin node
            index (:obj:`int`): the index of the track/bit in the bus
            physical (:obj:`bool`, default=True): this flag only works if ``node`` is a block pin. If set to True, the
                physical node ID will be returned, otherwise the logical node ID will be returned.

        Returns:
            :obj:`int`:
        """
        if node.is_blockpin:
            tile = self.__array[node.parent_instance.x][node.parent_instance.y]
            return (tile.physical_pin if physical else tile.logical_pin) + self.get_node_ptc(node, index)
        else:
            tile = self.context.array._array[node.x][node.y]
            id_ = node.section * node.prototype.width + index
            if node.dimension is Dimension.horizontal:
                key = (tile.space_decx > 0, tile.space_incx > 0, node.direction)
                track_id = self.__segments[node.name].track_id[key]
                return self.__array[node.x][node.y].hchan + track_id + id_
            else:
                key = (tile.space_decy > 0, tile.space_incy > 0, node.direction)
                track_id = self.__segments[node.name].track_id[key]
                return self.__array[node.x][node.y].vchan + track_id + id_

# ----------------------------------------------------------------------------
# -- VPRExtension ------------------------------------------------------------
# ----------------------------------------------------------------------------
class VPRExtension(AbstractPass):
    """Add VPR's extensions to the architecture context."""
    @property
    def key(self):
        """Key of this pass."""
        return "vpr.extension"

    @property
    def dependences(self):
        """Passes that this pass depends on."""
        return ("finalization", )

    def run(self, context):
        context._vpr_extension = _VPRExtension(context)
