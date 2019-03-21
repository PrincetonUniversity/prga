# Python 2 and 3 compatible
from prga.compatible import *

from prga._archdef.common import Side, RoutingNodeType
from prga._archdef.portpin.bus import PortOrPinBus
from prga._archdef.portpin.port import AbstractPort, AbstractInputPort, AbstractOutputPort, AbstractClockPort
from prga._archdef.routing.common import BlockPin, AbstractRoutingNode
from prga.exception import PRGAInternalError

# ----------------------------------------------------------------------------
# -- Slice Ports -------------------------------------------------------------
# ----------------------------------------------------------------------------
class SliceInputPort(AbstractInputPort, PortOrPinBus):
    """Slice input port.

    Args:
        slice (`Slice`): the slice this port belongs to
        name (:obj:`str`): name of this port
        width (:obj:`int`): width of this port
    """
    @property
    def is_physical(self):
        """Test if this is a physical port."""
        return True

    @property
    def is_logical(self):
        """Test if this is a logical port."""
        return True

class SliceOutputPort(AbstractOutputPort, PortOrPinBus):
    """Slice output port.

    Args:
        slice (`Slice`): the slice this port belongs to
        name (:obj:`str`): name of this port
        width (:obj:`int`): width of this port
    """
    @property
    def is_physical(self):
        """Test if this is a physical port."""
        return True

    @property
    def is_logical(self):
        """Test if this is a logical port."""
        return True

class SliceClockPort(AbstractClockPort, PortOrPinBus):
    """Slice clock port.

    Args:
        slice (`Slice`): the slice this port belongs to
        name (:obj:`str`): name of this port
    """
    @property
    def is_physical(self):
        """Test if this is a physical port."""
        return True

    @property
    def is_logical(self):
        """Test if this is a logical port."""
        return True

# ----------------------------------------------------------------------------
# -- Abstract Block Ports ----------------------------------------------------
# ----------------------------------------------------------------------------
class AbstractBlockPort(AbstractPort, AbstractRoutingNode):
    """Abstract base class for block ports.

    Args:
        block (`LogicBlock` or `IOBlock`): the block that this port belongs to
    """
    # == low-level API =======================================================
    @property
    def xoffset(self):
        """If the block is larger than 1 tile, specify X-dimension position of this port."""
        return 0

    @property
    def yoffset(self):
        """If the block is larger than 1 tile, specify Y-dimension position of this port."""
        return 0

    @property
    def node_type(self):
        """Type of this routing node."""
        return RoutingNodeType.blockpin

    @property
    def node(self):
        """The routing node that this port represents."""
        return BlockPin((self.xoffset, self.yoffset), self)

    @property
    def prototype(self):
        """Prototype of this routing node."""
        return self

    @property
    def is_bridge(self):
        """Test if this is a routing node bridge."""
        return False

# ----------------------------------------------------------------------------
# -- IO Block Ports ----------------------------------------------------------
# ----------------------------------------------------------------------------
class IOBlockInputPort(SliceInputPort, AbstractBlockPort):
    """IO block input port.

    Args:
        block (`IOBlock`): the block this port belongs to
        name (:obj:`str`): name of this port
        width (:obj:`int`): width of this port
        side (`Side`): on which side of the block is this port
        global_ (:obj:`str`): name of the non-clock global wire this port is hard-wired to
    """
    def __init__(self, block, name, width, side, global_ = None):
        super(IOBlockInputPort, self).__init__(block, name, width)
        if global_ is not None and width != 1:
            raise PRGAInternalError("Block input that's hard-wired to a non-clock global wire must be 1 bit wide""")
        self._side = side
        self._global = global_

    @property
    def side(self):
        """On which side of the block is this port."""
        return self._side

    @property
    def global_(self):
        """Name of the global wire this port is hard-wired to."""
        return self._global

class IOBlockOutputPort(SliceOutputPort, AbstractBlockPort):
    """IO block output port.

    Args:
        block (`IOBlock`): the block this port belongs to
        name (:obj:`str`): name of this port
        width (:obj:`int`): width of this port
        side (`Side`): on which side of the block is this port
    """
    def __init__(self, block, name, width, side):
        super(IOBlockOutputPort, self).__init__(block, name, width)
        self._side = side

    @property
    def side(self):
        """On which side of the block is this port."""
        return self._side

class IOBlockClockPort(SliceClockPort, AbstractBlockPort):
    """IO block clock port.

    Args:
        block (`IOBlock`): the block this port belongs to
        name (:obj:`str`): name of this port
        side (`Side`): on which side of the block is this port
        global_ (:obj:`str`): name of the global clock wire this port is hard-wired to
    """
    def __init__(self, block, name, side, global_):
        super(IOBlockClockPort, self).__init__(block, name)
        self._side = side
        self._global = global_

    @property
    def side(self):
        """On which side of the block is this port."""
        return self._side

    @property
    def global_(self):
        """Name of the global wire this port is hard-wired to."""
        return self._global

# ----------------------------------------------------------------------------
# -- Logic Block Ports -------------------------------------------------------
# ----------------------------------------------------------------------------
class LogicBlockInputPort(IOBlockInputPort):
    """Logic block input port.

    Args:
        block (`LogicBlock`): the block this port belongs to
        name (:obj:`str`): name of this port
        width (:obj:`int`): width of this port
        side (`Side`): on which side of the block is this port
        global_ (:obj:`str`): name of the non-clock global wire this port is hard-wired to
        xoffset (:obj:`int`): if the block is larger than 1 tile, specify X-dimension position of this port
        yoffset (:obj:`int`): if the block is larger than 1 tile, specify Y-dimension position of this port

    Raises:
        `PRGAInternalError`: if this port is hard-wired to a non-clock global wire but the width is not 1
    """
    def __init__(self, block, name, width, side, global_ = None, xoffset = 0, yoffset = 0):
        super(LogicBlockInputPort, self).__init__(block, name, width, side, global_)
        self._xoffset = xoffset
        self._yoffset = yoffset

    @property
    def xoffset(self):
        """If the block is larger than 1 tile, specify X-dimension position of this port."""
        return self._xoffset

    @property
    def yoffset(self):
        """If the block is larger than 1 tile, specify Y-dimension position of this port."""
        return self._yoffset

class LogicBlockOutputPort(IOBlockOutputPort):
    """Logic block output port.

    Args:
        block (`LogicBlock`): the block this port belongs to
        name (:obj:`str`): name of this port
        width (:obj:`int`): width of this port
        side (`Side`): on which side of the block is this port
        xoffset (:obj:`int`): if the block is larger than 1 tile, specify X-dimension position of this port
        yoffset (:obj:`int`): if the block is larger than 1 tile, specify Y-dimension position of this port
    """
    def __init__(self, block, name, width, side, xoffset = 0, yoffset = 0):
        super(LogicBlockOutputPort, self).__init__(block, name, width, side)
        self._xoffset = xoffset
        self._yoffset = yoffset

    @property
    def xoffset(self):
        """If the block is larger than 1 tile, specify X-dimension position of this port."""
        return self._xoffset

    @property
    def yoffset(self):
        """If the block is larger than 1 tile, specify Y-dimension position of this port."""
        return self._yoffset

class LogicBlockClockPort(IOBlockClockPort):
    """Logic block clock port.

    Args:
        block (`LogicBlock`): the block this port belongs to
        name (:obj:`str`): name of this port
        side (`Side`): on which side of the block is this port
        global_ (:obj:`str`): name of the global clock wire this port is hard-wired to
        xoffset (:obj:`int`): if the block is larger than 1 tile, specify X-dimension position of this port
        yoffset (:obj:`int`): if the block is larger than 1 tile, specify Y-dimension position of this port
    """
    def __init__(self, block, name, side, global_, xoffset = 0, yoffset = 0):
        super(LogicBlockClockPort, self).__init__(block, name, side, global_)
        self._xoffset = xoffset
        self._yoffset = yoffset

    @property
    def xoffset(self):
        """If the block is larger than 1 tile, specify X-dimension position of this port."""
        return self._xoffset

    @property
    def yoffset(self):
        """If the block is larger than 1 tile, specify Y-dimension position of this port."""
        return self._yoffset
