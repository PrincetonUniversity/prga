# Python 2 and 3 compatible
from prga.compatible import *

"""All enum types and const/static stuff."""

__all__ = ['ModuleType', 'PrimitiveType', 'SwitchType', 'BlockType', 'TileType', 'NetType', 'PortDirection',
        'PrimitivePortClass', 'Side', 'SideTuple', 'Dimension', 'Direction', 'RoutingNodeType']

from enum import Enum
from collections import namedtuple

# ----------------------------------------------------------------------------
# -- ModuleType --------------------------------------------------------------
# ----------------------------------------------------------------------------
class ModuleType(Enum):
    """Module types."""
    primitive = 0   #: primitive (also called logic element)
    switch = 1      #: configurable switch: mux, etc.
    config = 2      #: configuration circuitry
    shadow = 3      #: physical-only shadow components
    slice_ = 4      #: intermediate module type inside logic/io blocks
    block = 5       #: logic/io block, routing block

# ----------------------------------------------------------------------------
# -- PrimitiveType -----------------------------------------------------------
# ----------------------------------------------------------------------------
class PrimitiveType(Enum):
    """Primitive types."""
    custom = 0      #: user-defined, non-configurable custom primitive. Flipflop also belongs to this category because
                    #   it is not configurable
    lut = 1         #: built-in look-up table
    flipflop = 2    #: built-in D-flipflop
    inpad = 3       #: built-in input pad
    outpad = 4      #: built-in output pad
    iopad = 5       #: built-in I/O pad
    memory = 6      #: user-defined memory
    multimode = 7   #: user-defined multi-mode primitive

# ----------------------------------------------------------------------------
# -- SwitchType --------------------------------------------------------------
# ----------------------------------------------------------------------------
class SwitchType(Enum):
    """Switch types."""
    buf = 0         #: configurable buffer
    mux = 1         #: configurable mux

# ----------------------------------------------------------------------------
# -- TileType ----------------------------------------------------------------
# ----------------------------------------------------------------------------
class TileType(Enum):
    """Sub-tile types."""
    logic = 0       #: logic/io/array block tile
    xchan = 1       #: X-dimensinoal routing channel
    ychan = 2       #: Y-dimensional routing channel
    switch = 3      #: switch block tile

    @classmethod
    def all(self):
        return (TileType.logic, TileType.xchan, TileType.ychan, TileType.switch)

    @classmethod
    def all_routing(self):
        return (TileType.xchan, TileType.ychan, TileType.switch)

# ----------------------------------------------------------------------------
# -- BlockType ---------------------------------------------------------------
# ----------------------------------------------------------------------------
class BlockType(Enum):
    """Block types."""
    logic = 0       #: logic block
    io = 1          #: io block
    xconn = 2       #: X-dimensional connection block
    yconn = 3       #: Y-dimensional connection block
    switch = 4      #: switch block
    xroute = 5      #: X-dimensional connection block w/ combined switch block
    yroute = 6      #: Y-dimensional connection block w/ combined switch block
    array = 7       #: an array of blocks

    @property
    def tile_type(self):
        """The tile type corresponding to this block type."""
        return (TileType.logic if self in (BlockType.logic, BlockType.io, BlockType.array) else
                TileType.xchan if self in (BlockType.xconn, BlockType.xroute) else
                TileType.ychan if self in (BlockType.yconn, BlockType.yroute) else
                TileType.switch)

# ----------------------------------------------------------------------------
# -- NetType -----------------------------------------------------------------
# ----------------------------------------------------------------------------
class NetType(Enum): 
    """Enum type for nets.

    In PRGA, only ports/pins are modeled. Wires are only created during RTL generation, and not modeled in our
    in-memory data structure.
    """
    open = 0    #: unconnected net
    zero = 1    #: constant logic 0
    one = 2     #: constant logic 1
    port = 3    #: ports of a module
    pin = 4     #: ports of an instantiated sub-module

# ----------------------------------------------------------------------------
# -- PortDirection -----------------------------------------------------------
# ----------------------------------------------------------------------------
class PortDirection(Enum):
    """Enum type for port/pin directions."""
    input = 0   #: input direction
    output = 1  #: output direction

    @property
    def opposite(self):
        """The opposite of the this direction.

        Returns:
            `PortDirection`: the enum value of the opposite direction.
        """
        if self is PortDirection.output:
            return PortDirection.input
        elif self is PortDirection.input:
            return PortDirection.output
        else:
            raise RuntimeError("{} does not have opposite PortDirection".format(self))

    def select(self, input, output):
        """Select value based on this enum."""
        return input if self is PortDirection.input else output

# ----------------------------------------------------------------------------
# -- PrimitivePortClass ------------------------------------------------------
# ----------------------------------------------------------------------------
class PrimitivePortClass(Enum):
    """Enum types for VPR's 'port_class' attributes.

    These 'port_class'es are only used for VPR inputs generation.
    """
    clock       = 0     #: clock for flipflop and memory
    lut_in      = 1     #: lut input
    lut_out     = 2     #: lut output
    D           = 3     #: flipflop data input
    Q           = 4     #: flipflop data output
    address     = 5     #: address input for single-port memory
    write_en    = 6     #: write enable for single-port memory
    data_in     = 7     #: data input for single-port memory
    data_out    = 8     #: data output for single-port memory
    address1    = 9     #: 1st address input for dual-port memory
    write_en1   = 10    #: 1st write enable for single-port memory
    data_in1    = 11    #: 2st data input for dual-port memory
    data_out1   = 12    #: 1st data output for dual-port memory
    address2    = 13    #: 2nd address input for dual-port memory
    write_en2   = 14    #: 2nd write enable for single-port memory
    data_in2    = 15    #: 2nd data input for dual-port memory
    data_out2   = 16    #: 2nd data output for dual-port memory

# ----------------------------------------------------------------------------
# -- Side --------------------------------------------------------------------
# ----------------------------------------------------------------------------
class Side(Enum):
    """Enum types for the 4 sides of a block."""
    top = 0
    right = 1
    bottom = 2
    left = 3

    @property
    def opposite(self):
        """The opposite of the this side."""
        if self is Side.top:
            return Side.bottom
        elif self is Side.right:
            return Side.left
        elif self is Side.bottom:
            return Side.top
        elif self is Side.left:
            return Side.right
        else:
            raise RuntimeError("'{}' does not have an opposite Side".format(self))

    @classmethod
    def all(cls):
        """A tuple of all sides."""
        return (cls.top, cls.right, cls.bottom, cls.left)

# ----------------------------------------------------------------------------
# -- SideTuple ---------------------------------------------------------------
# ----------------------------------------------------------------------------
class SideTuple(namedtuple('SideTuple', 'top right bottom left')):
    """A tuple with one value for each side."""
    def __new__(cls, top = None, right = None, bottom = None, left = None):
        return super(SideTuple, cls).__new__(cls, top, right, bottom, left)

    def __getitem__(self, key):
        if isinstance(key, Side):
            return self[key.value]
        return super(SideTuple, self).__getitem__(key)

# ----------------------------------------------------------------------------
# -- Dimension ---------------------------------------------------------------
# ----------------------------------------------------------------------------
class Dimension(Enum):
    """Segment/connection block dimensions."""
    x = 0   #: X-dimension
    y = 1   #: Y-dimension

    @classmethod
    def all(cls):
        """Iterate through all dimensions."""
        return (cls.x, cls.y)

    @property
    def perpendicular(self):
        """The perpendicular dimension of this dimension."""
        if self is Dimension.x:
            return Dimension.y
        elif self is Dimension.y:
            return Dimension.x
        else:
            raise RuntimeError("{} does not have a perpendicular Dimension".format(self))

    def select(self, x, y):
        """Select value based on this enum."""
        return x if self is Dimension.x else y

# ----------------------------------------------------------------------------
# -- Direction ---------------------------------------------------------------
# ----------------------------------------------------------------------------
class Direction(Enum):
    """Segment/relative directions."""
    pos = 0         #: positive direction
    neg = 1         #: negative direction
    bidir = 2       #: bidirectional wire segment (not supported yet)

    @classmethod
    def all(cls):
        """Iterate through all uni-directional segment directions."""
        return (cls.pos, cls.neg)

    @property
    def opposite(self):
        """The opposite direction of this direction."""
        if self is Direction.pos:
            return Direction.neg
        elif self is Direction.neg:
            return Direction.pos
        else:
            raise RuntimeError("{} does not have an opposite Direction".format(self))

    def select(self, pos, neg):
        """Select value based on this enum."""
        if self is Direction.bidir:
            raise PRGAInternalError("Cannot call Direction.select on Direction.bidir")
        return pos if self is Direction.pos else neg

# ----------------------------------------------------------------------------
# -- RoutingNodeType ---------------------------------------------------------
# ----------------------------------------------------------------------------
class RoutingNodeType(Enum):
    """Type of routing nodes."""
    blockpin    = 0 #: logic/io block pins
    segment     = 1 #: wire segments

    @classmethod
    def all(cls):
        """Iterate through all node types."""
        return (cls.blockpin, cls.segment)
