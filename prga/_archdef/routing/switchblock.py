# -*- encoding: ascii -*-

"""Switch blocks."""

__all__ = ['SwitchBlockEnvironment', 'SwitchBlock']

import logging
_logger = logging.getLogger(__name__)

from resource import SegmentReference, BlockPinReference
from abstractblock import AbstractRoutingBlock
from ..common import Dimension, SegmentDirection, PortDirection, Side, BlockType

from itertools import product, cycle, chain, compress
from collections import namedtuple

# ----------------------------------------------------------------------------
# -- SwitchBlock -------------------------------------------------------------
# ----------------------------------------------------------------------------
class SwitchBlockEnvironment(namedtuple('SwitchBlockEnvironment_namedtuple', 'decx incx decy incy')):
    """The environment that a certain switch block fits in.

    Args:
        decx, incx, decy, incy (:obj:`bool`): if routing channel exists in these directions
    """
    pass

class SwitchBlock(AbstractRoutingBlock):
    """Switch block.

    Args:
        context (`ArchitectureContext`): the architecture context this model belongs to
        name (:obj:`str`): name of this block
        decx, incx, decy, incy (:obj:`bool`): if there're segments running at the given side

    The constructor will only create an empty switch block with no port and thus no connections. Use
    `SwitchBlock.implement_wilton` and other switch pattern implementation methods to complete the switch block.
    """
    def __init__(self, context, name, decx, incx, decy, incy):
        super(SwitchBlock, self).__init__(context, name)
        self.__environment = SwitchBlockEnvironment(decx, incx, decy, incy)

    # by default, using wilton rule for switchblock generation
    #               from side,     to side,         i+1,   -o,    o+1
    __wilton = {    (Side.left,     Side.top):      (True,  True,  False),
                    (Side.left,     Side.bottom):   (True,  False, False),
                    (Side.top,      Side.left):     (True,  True,  False),
                    (Side.top,      Side.right):    (False, False, True),
                    (Side.right,    Side.top):      (True,  False, False),
                    (Side.right,    Side.bottom):   (False, True,  True),
                    (Side.bottom,   Side.left):     (False, False, True),
                    (Side.bottom,   Side.right):    (False, True,  True), }

    __side2dir = {  (Side.left,   PortDirection.input):  (Dimension.horizontal, SegmentDirection.inc),
                    (Side.left,   PortDirection.output): (Dimension.horizontal, SegmentDirection.dec),
                    (Side.top,    PortDirection.input):  (Dimension.vertical,   SegmentDirection.dec),
                    (Side.top,    PortDirection.output): (Dimension.vertical,   SegmentDirection.inc),
                    (Side.right,  PortDirection.input):  (Dimension.horizontal, SegmentDirection.dec),
                    (Side.right,  PortDirection.output): (Dimension.horizontal, SegmentDirection.inc),
                    (Side.bottom, PortDirection.input):  (Dimension.vertical,   SegmentDirection.inc),
                    (Side.bottom, PortDirection.output): (Dimension.vertical,   SegmentDirection.dec) }

    # -- internal API --------------------------------------------------------
    def _validate_reference(self, reference, direction = None):
        super(SwitchBlock, self)._validate_reference(reference, direction)
        if reference.is_blockpin:
            raise PRGAAPIError("Cannot refer to block pins in switch blocks")

    # -- exposed API ---------------------------------------------------------
    @property
    def block_type(self):
        """Type of this block."""
        return BlockType.switch

    @property
    def environment(self):
        """The environment this switch block sits in."""
        return self.__environment

    def implement_wilton(self, drive_truncated = True):
        """Implement Wilton-style switch block.

        Args:
            drive_truncated (:obj:`bool`, default=True): if this switch block is used at the edges/corners of the
                whole block array, theere will be no wire segments on one or two sides of this switch block. If some
                segment types are longer than 1 tile, there will be truncated segments of these types at one or two
                sides of this switch block. This flag controls if the switch block should drive such truncated wire
                segments in this case
        """
        if len(self._nodes) > 0:
            raise PRGAAPIError("`implement_wilton` should never be used after custom connections are added")
        sides = tuple(compress((Side.left, Side.right, Side.bottom, Side.top), self.__environment))
        for from_side, to_side in product(iter(sides), iter(sides)):
            if from_side is to_side:
                continue
            from_dim, from_dir = self.__side2dir[from_side, PortDirection.input]
            to_dim,   to_dir   = self.__side2dir[to_side,   PortDirection.output]
            if from_side is to_side.opposite:
                for sgmt in self._context.segments.itervalues():
                    sources = (self._RoutingNodeReferenceBit(
                            SegmentReference(sgmt.name, from_dim, from_dir, sgmt.length-1), i)
                            for i in xrange(sgmt.width))
                    sinks = (self._RoutingNodeReferenceBit(
                            SegmentReference(sgmt.name, to_dim, to_dir, 0), i)
                            for i in xrange(sgmt.width))
                    self.add_connections(sources, sinks)
                continue
            iskip, orev, oskip = self.__wilton[(from_side, to_side)]
            trunc = drive_truncated and (to_side.opposite not in sides) 
            # input nodes iterator
            inodes = iter(self._RoutingNodeReferenceBit(SegmentReference(
                    sgmt.name, from_dim, from_dir, section), index)
                for sgmt in self._context.segments.itervalues()
                for index in xrange(sgmt.width)
                for section in xrange(sgmt.length))
            if iskip:
                head = next(inodes)
                inodes = chain(inodes, iter((head,)))
            # output nodes iterator
            onodes = None
            if orev: 
                onodes = iter(self._RoutingNodeReferenceBit(SegmentReference(
                        sgmt.name, to_dim, to_dir, section), index)
                    for sgmt in reversed(self._context.segments.values())
                    for index in xrange(sgmt.width-1, -1, -1)
                    for section in (xrange(sgmt.length-1, -1, -1) if trunc else (0,)))
            else:
                onodes = iter(self._RoutingNodeReferenceBit(SegmentReference(
                        sgmt.name, to_dim, to_dir, section), index)
                    for sgmt in self._context.segments.itervalues()
                    for index in xrange(sgmt.width)
                    for section in (xrange(sgmt.length) if trunc else (0,)))
            if oskip:
                head = next(onodes)
                onodes = chain(onodes, iter((head,)))
            onodes = cycle(onodes)
            # create logical connections
            for inode in inodes:
                self.add_connections(inode, next(onodes))
