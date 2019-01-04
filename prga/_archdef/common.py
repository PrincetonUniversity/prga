# -*- enconding: ascii -*-

"""All enum types and const/static stuff."""

__all__ = ['ModuleType', 'SwitchType', 'BlockType', 'NetType', 'PortDirection', 'ModelPortClass', 'Side',
        'Dimension', 'SegmentDirection', 'RoutingNodeType']

import logging
_logger = logging.getLogger(__name__)

from enum import Enum

# ----------------------------------------------------------------------------
# -- ModuleType --------------------------------------------------------------
# ----------------------------------------------------------------------------
class ModuleType(Enum):
    """Module types."""
    # logical modules
    custom = 0      #: user-defined custom model
    flipflop = 1    #: built-in flip-flop
    lut = 2         #: built-in LUT
    inpad = 3       #: built-in input pad
    outpad = 4      #: built-in output pad
    iopad = 5       #: built-in inout pad
    memory = 6      #: user-defined memory
    multimode = 7   #: user-defined multi-mode model
    # physical modules
    config = 8      #: configuration circuitry
    switch = 9      #: switch: mux, etc.
    addon = 10      #: add-on physical-only components
    # placeholder
    block = 11      #: blocks
    mode = 12       #: mode of multi-mode models
    array = 13      #: top-level module

# ----------------------------------------------------------------------------
# -- SwitchType --------------------------------------------------------------
# ----------------------------------------------------------------------------
class SwitchType(Enum):
    """Switch types."""
    mux = 0         #: configurable mux

# ----------------------------------------------------------------------------
# -- BlockType ---------------------------------------------------------------
# ----------------------------------------------------------------------------
class BlockType(Enum):
    """Block types."""
    # logical blocks
    logic = 0                   #: logic blocks
    io = 1                      #: IO blocks
    # physical blocks
    horizontalconnection = 2    #: X-dimensional connection blocks
    verticalconnection = 3      #: Y-dimensional connection blocks
    switch = 4                  #: switch blocks

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
    inout = 2   #: inout direction (only supported in certain situations)

    @property
    def opposite(self):
        """The opposite of the this direction.

        `PortDirection.inout` direction does not have an opposite.

        Returns:
            `PortDirection`: the enum value of the opposite direction.

        Raises:
            `PRGAInternalError`: if this property is used on `PortDirection.inout` direction.
        """
        if self is PortDirection.output:
            return PortDirection.input
        elif self is PortDirection.input:
            return PortDirection.output
        else:
            raise RuntimeError("{} does not have opposite PortDirection"
                    .format(self))

# ----------------------------------------------------------------------------
# -- ModelPortClass ----------------------------------------------------------
# ----------------------------------------------------------------------------
class ModelPortClass(Enum):
    """Enum types for VPR's 'port_class' attributes.

    These 'port_class'es are only used for VPR inputs generation.
    """
    clock       = 0     #: clock for flipflop and memory
    lut_in      = 1     #: lut input
    lut_out     = 2     #: lut output
    D           = 3     #: flipflop data input
    Q           = 4     #: flipflop data output
    address     = 5     #: address input for single-port memory
    data_in     = 6     #: data input for single-port memory
    data_out    = 7     #: data output for single-port memory
    address1    = 8     #: 1st address input for dual-port memory
    data_in1    = 9     #: 1st data input for dual-port memory
    data_out1   = 10    #: 1st data output for dual-port memory
    address2    = 11    #: 2nd address input for dual-port memory
    data_in2    = 12    #: 2nd data input for dual-port memory
    data_out2   = 13    #: 2nd data output for dual-port memory

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
        else:
            return Side.right

    @classmethod
    def all(cls):
        """A tuple of all sides."""
        return (cls.top, cls.right, cls.bottom, cls.left)

# ----------------------------------------------------------------------------
# -- Dimension ---------------------------------------------------------------
# ----------------------------------------------------------------------------
class Dimension(Enum):
    """Segment/connection block dimensions."""
    horizontal = 0  #: X-dimension
    vertical = 1    #: Y-dimension

    @classmethod
    def all(cls):
        """Iterate through all dimensions."""
        return (cls.horizontal, cls.vertical)

# ----------------------------------------------------------------------------
# -- SegmentDirection --------------------------------------------------------
# ----------------------------------------------------------------------------
class SegmentDirection(Enum):
    """Direction of wire segments."""
    inc = 0         #: increasing direction
    dec = 1         #: decreasing direction
    bidir = 2       #: bidirectional wire segment

    @classmethod
    def all(cls):
        """Iterate through all uni-directional segment directions."""
        return (cls.inc, cls.dec)

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
