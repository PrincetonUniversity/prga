# -*- encoding: ascii -*-

"""Routing resource definitions & references."""

__all__ = ['SegmentPrototype', 'Global', 'SegmentReference', 'BlockPinReference', 'SegmentNode']

import logging
_logger = logging.getLogger(__name__)

from ..common import Dimension, SegmentDirection, RoutingNodeType
from ...exception import PRGAInternalError, PRGAAPIError
from ..._util.util import DictProxy

from collections import namedtuple
from abc import ABCMeta, abstractproperty

# ----------------------------------------------------------------------------
# -- SegmentPrototype --------------------------------------------------------
# ----------------------------------------------------------------------------
class SegmentPrototype(namedtuple('SegmentPrototype_namedtuple', 'name width length')):
    """Defining a segment prototype.
    
    Args:
        name (:obj:`str`): name of this segment
        width (:obj:`str`): number of wire segment originating from one tile in one direction
        length (:obj:`int`, default=1): length of this segment
    """
    def __new__(cls, name, width, length = 1):
        return super(SegmentPrototype, cls).__new__(cls, name, width, length)

# ----------------------------------------------------------------------------
# -- Global ------------------------------------------------------------------
# ----------------------------------------------------------------------------
class GlobalBinding(namedtuple('GlobalBinding_namedtuple', 'x y subblock')):
    """Bind a global wire to a specific subblock of a IO block.

    Args:
        x, y (:obj:`int`): position of the IO block
        subblock (:obj:`int`): the sub-block ID if multiple IO blocks are placed in one tile
    """
    pass

class Global(object):
    """Defining a global wire.

    Args:
        context (`ArchitectureContext`): the architecture context this global wire belongs to
        name (:obj:`str`): name of this global wire
        is_clock (:obj:`bool`, default=False): if this global wire is a clock wire
    """
    def __init__(self, context, name, is_clock = False):
        self.__context = context
        self.__name = name
        self.__binding = None
        self.__is_clock = is_clock

    # -- internal api -------------------------------------------------------
    @property
    def _context(self):
        """The `ArchitectureContext` this module belongs to."""
        return self.__context

    # -- exposed api --------------------------------------------------------
    @property
    def name(self):
        """Name of this global wire."""
        return self.__name

    @property
    def is_clock(self):
        """Test if this global wire is a clock wire."""
        return self.__is_clock

    @property
    def binding(self):
        """The sub-block that drives this global wire."""
        if self.__binding is None:
            raise PRGAAPIError("Global wire '{}' is not bound yet".format(self.name))
        return self.__binding

    def bind(self, x, y, subblock = 0):
        """Bind a global wire to a specific subblock of a IO block.

        Args:
            x, y (:obj:`int`): position of the IO block
            subblock (:obj:`int`, default=0): the sub-block ID if multiple IO blocks are placed in one tile

        Raises:
            `PRGAAPIError`: if the specific subblock is not an IO block
        """
        tile = self.__context.array._get_tile(x, y)
        if (tile is None or tile.block is None or not tile.block.is_io_block or subblock < 0 or
                subblock >= tile.block.capacity or not tile.block_instances[subblock].is_physical):
            raise PRGAAPIError("Cannot bind global wire '{}' to subblock ({}, {}, {})"
                    .format(self.name, x, y, subblock))
        tile.block_instances[subblock]._unset_physical()
        self.__context.array._globals[self.name] = self.__context.array._get_or_create_physical_input(self.name, 1)
        self.__binding = GlobalBinding(x, y, subblock)

# ----------------------------------------------------------------------------
# -- Routing Node Reference --------------------------------------------------
# ----------------------------------------------------------------------------
class AbstractRoutingNode(object):
    """Abstract base class for all routing node types."""
    __metaclass__ = ABCMeta

    @abstractproperty
    def node_type(self):
        """:obj:`abstractproperty`: Type of the routing node."""
        raise NotImplementedError

    @property
    def is_blockpin(self):
        """Test if this routing node reference is a block pin."""
        return self.node_type is RoutingNodeType.blockpin

    @property
    def is_segment(self):
        """Test if this routing node reference is a routing wire segment."""
        return self.node_type is RoutingNodeType.segment

class SegmentReference(namedtuple('SegmentReference_namedtuple', 'name dimension direction section'),
        AbstractRoutingNode):
    """Reference to a set of wire segments.
    
    Args:
        name (:obj:`str`): name of the referenced wire segment
        dimension (:obj:`Dimension`): dimension of the referenced wire segment
        direction (:obj:`SegmentDirection`): direction of the referenced wire segment
        section (:obj:`int`, default=0): if the segment is longer than 1, which section is being referenced
    """
    def __new__(cls, name, dimension, direction, section = 0):
        return super(SegmentReference, cls).__new__(cls, name, dimension, direction, section)

    @property
    def node_type(self):
        """Type of the routing node."""
        return RoutingNodeType.segment

class BlockPinReference(namedtuple('BlockPinReference_namedtuple', 'block port xoffset yoffset subblock'),
        AbstractRoutingNode):
    """Reference to a block pin.

    Args:
        block (:obj:`str`): name of the referenced block
        port (:obj:`str`): name of the referenced port 
        xoffset, yoffset (:obj:`int`, default=0): offset from the current tile
        subblock (:obj:`int`, default=0): if the referenced block is an IO block and multiple blocks are placed in a
            tile, which sub-block is being referenced
    """
    def __new__(cls, block, port, xoffset = 0, yoffset = 0, subblock = 0):
        return super(BlockPinReference, cls).__new__(cls, block, port, xoffset, yoffset, subblock)

    @property
    def node_type(self):
        """Type of the routing node."""
        return RoutingNodeType.blockpin

# ----------------------------------------------------------------------------
# -- Routing Node ------------------------------------------------------------
# ----------------------------------------------------------------------------
class SegmentNode(namedtuple('SegmentNode_namedtuple', 'prototype x y dimension direction section'),
        AbstractRoutingNode):
    """A specific segment at a specific location.

    Args:
        prototype (`SegmentPrototype`): the prototype of this segment node
        x, y (:obj:`int`): the position of this segment
        dimension (`Dimension`): the dimension of this segment
        direction (`SegmentDirection`): the direction of this segment
        section (:obj:`int`, default=0): the section of this segment
    """
    def __new__(cls, prototype, x, y, dimension, direction, section = 0):
        return super(SegmentNode, cls).__new__(cls, prototype, x, y, dimension, direction, section)

    @property
    def name(self):
        """Name of this segment."""
        return self.prototype.name

    @property
    def node_type(self):
        """Type of the routing node."""
        return RoutingNodeType.segment
