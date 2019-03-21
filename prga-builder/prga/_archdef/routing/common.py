# Python 2 and 3 compatible
from prga.compatible import *

__all__ = ['Position', 'SegmentPrototype', 'Global', 'Segment', 'BlockPin']

from prga._archdef.common import RoutingNodeType, Direction, Dimension
from prga._util.util import uno, ExtensibleObject
from prga.exception import PRGAAPIError

from abc import ABCMeta, abstractproperty
from collections import namedtuple
from itertools import chain

# ----------------------------------------------------------------------------
# -- Position ----------------------------------------------------------------
# ----------------------------------------------------------------------------
class Position(namedtuple('Position', 'x y subblock_or_section')):
    """A tuple specifying a position in an array.

    Args:
        x (:obj:`int`): the X-dimensional position
        y (:obj:`int`): the Y-dimensional position
        subblock_or_section (:obj:`int`): the sub-block ID of an IOBlock instance, or the section of a long wire
            segment
    """
    def __new__(cls, x, y, subblock_or_section = 0):
        return super(Position, cls).__new__(cls, x, y, subblock_or_section)

    @property
    def subblock(self):
        """The sub-block ID of an IOBlock instance."""
        return self.subblock_or_section

    @property
    def section(self):
        """The section of a long wire."""
        return self.subblock_or_section

    def __add__(self, position):
        return Position(self.x + position[0], self.y + position[1],
                self.subblock + (0 if len(position) < 3 else position[2]))

    def __sub__(self, position):
        return Position(self.x - position[0], self.y - position[1],
                self.subblock - (0 if len(position) < 3 else position[2]))

# ----------------------------------------------------------------------------
# -- SegmentPrototype --------------------------------------------------------
# ----------------------------------------------------------------------------
class SegmentPrototype(ExtensibleObject):
    """Defining a segment prototype.
    
    Args:
        name (:obj:`str`): name of this segment
        width (:obj:`str`): number of wire segment originating from one tile in one direction
        length (:obj:`int`): length of this segment
    """
    def __init__(self, name, width, length):
        self._name = name
        self._width = width
        self._length = length

    @property
    def name(self):
        """Name of this segment."""
        return self._name

    @property
    def width(self):
        """Width of this segment."""
        return self._width

    @property
    def length(self):
        """Length of thie segment."""
        return self._length

# ----------------------------------------------------------------------------
# -- Global ------------------------------------------------------------------
# ----------------------------------------------------------------------------
class Global(object):
    """Defining a global wire.

    Args:
        name (:obj:`str`): name of this global wire
        is_clock (:obj:`bool`): if this global wire is a clock wire
    """
    def __init__(self, name, is_clock = False):
        self._name = name
        self._is_clock = is_clock
        self._binding = None

    @property
    def name(self):
        """Name of this global wire."""
        return self._name

    @property
    def is_clock(self):
        """Test if this global wire is a clock wire."""
        return self._is_clock

    @property
    def binding(self):
        """The sub-block that drives this global wire."""
        if self._binding is None:
            raise PRGAAPIError("Global wire '{}' is not bound yet".format(self.name))
        return self._binding

# ----------------------------------------------------------------------------
# -- Routing Node ------------------------------------------------------------
# ----------------------------------------------------------------------------
class AbstractRoutingNode(with_metaclass(ABCMeta, object)):
    """Abstract base class for all routing nodes."""

    @abstractproperty
    def node_type(self):
        """Type of the routing node."""
        raise NotImplementedError

    @property
    def is_blockpin(self):
        """Test if this is a block pin."""
        return self.node_type is RoutingNodeType.blockpin

    @property
    def is_segment(self):
        """Test if this is a wire segment."""
        return self.node_type is RoutingNodeType.segment

class Segment(namedtuple('Segment', 'position prototype direction dimension'),
        AbstractRoutingNode):
    """A set of wire segments.
    
    Args:
        position (`Position`): position of the referred segment
        prototype (`SegmentPrototype`): prototype of the segment
        direction (`Direction`): direction of the referenced wire segment
        dimension (`Dimension`): dimension of the referenced wire segment
    """
    def __new__(cls, position, prototype, direction, dimension):
        return super(Segment, cls).__new__(cls, Position(*position), prototype, direction, dimension)

    @property
    def node_type(self):
        """Type of the routing node."""
        return RoutingNodeType.segment

    def __hash__(self):
        return hash( (self.position, self.prototype.name, self.direction, self.dimension) )

    def __str__(self):
        return 'Segment({}, {}, {}{})'.format(tuple(self.position), self.prototype.name, self.direction.name,
                self.dimension.name)

    def iter_prev_equivalents(self):
        """Iterate through equivalent `Segment` from view points that are closer to the origin."""
        for i in range(1, self.position.section + 1):
            yield self._replace(position = self.position + self.direction.select(
                self.dimension.select((-i, 0, -i), (0, -i, -i)),
                self.dimension.select((i, 0, -i), (0, i, -i))))

    def iter_next_equivalents(self):
        """Iterate through equivalent `Segment` from view points that are further to the origin."""
        for i in range(1, self.prototype.length - self.position.section):
            yield self._replace(position = self.position + self.direction.select(
                self.dimension.select((i, 0, i), (0, i, i)),
                self.dimension.select((-i, 0, i), (0, -i, i))))

    def iter_all_equivalents(self):
        """Iterate through all equivalent `Segment` including self."""
        return chain(iter((self, )), self.iter_prev_equivalents(), self.iter_next_equivalents())

    @property
    def name(self):
        """Name of the segment."""
        return self.prototype.name

    @property
    def origin_equivalent(self):
        """Equivalent `Segment` from the view point of the origin."""
        s = self.position.section
        return self._replace(position = self.position + self.direction.select(
            self.dimension.select((-s, 0, -s), (0, -s, -s)),
            self.dimension.select((s, 0, -s), (0, s, -s))))

class BlockPin(namedtuple('BlockPin', 'position prototype'),
        AbstractRoutingNode):
    """A block pin.

    Args:
        position (`Position`): position of the referred pin
        prototype (block port): the prototype port
    """
    def __new__(cls, position, prototype):
        return super(BlockPin, cls).__new__(cls, Position(*position), prototype)

    @property
    def node_type(self):
        """Type of the routing node."""
        return RoutingNodeType.blockpin

    @property
    def block(self):
        """Name of he block."""
        return self.prototype.parent.name

    @property
    def port(self):
        """Name of the port."""
        return self.prototype.name

    def __hash__(self):
        return hash( (self.position, self.prototype.parent.name, self.prototype.name) )

    def __str__(self):
        return "BlockPin({}, {}.{})".format(tuple(self.position), self.prototype.parent.name, self.prototype.name)
