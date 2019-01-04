# -*- enconding: ascii -*-

"""Block port classes."""

__all__ = ['LogicBlockInputPort', 'LogicBlockOutputPort', 'LogicBlockClockPort',
        'IOBlockInputPort', 'IOBlockOutputPort', 'IOBlockClockPort',
        'PhysicalBlockInputPort', 'PhysicalBlockOutputPort']

import logging
_logger = logging.getLogger(__name__)

from ..common import Side
from ..portpin.port import (AbstractInputPort, AbstractOutputPort, AbstractClockPort, PhysicalInputPort,
        PhysicalOutputPort)
from ...exception import PRGAInternalError

# ----------------------------------------------------------------------------
# -- IO Block Ports ----------------------------------------------------------
# ----------------------------------------------------------------------------
class IOBlockInputPort(AbstractInputPort):
    """IO block input port.

    Args:
        block (`IOBlock`): the block this port belongs to
        name (:obj:`str`): name of this port
        width (:obj:`int`): width of this port
        side (`Side`): on which side of the block is this port
        global_ (:obj:`str`, default=None): name of the non-clock global wire this port is hard-wired to
    """
    def __init__(self, block, name, width, side, global_ = None):
        super(IOBlockInputPort, self).__init__(block, name, width)
        if global_ is not None and width != 1:
            raise PRGAInternalError("Block input that's hard-wired to a non-clock global wire must be 1 bit wide""")
        self.__side = side
        self.__global = global_

    @property
    def side(self):
        """On which side of the block is this port."""
        return self.__side

    @property
    def is_global(self):
        """Test if this port is hard-wired to a non-clock global wire."""
        return self.__global is not None

    @property
    def global_(self):
        """Name of the non-clock global wire this port is hard-wired to."""
        return self.__global

    @property
    def xoffset(self):
        """If the block is larger than 1 tile, specify detailed X-dimension position of this port."""
        return 0

    @property
    def yoffset(self):
        """If the block is larger than 1 tile, specify detailed Y-dimension position of this port."""
        return 0

    @property
    def is_logical(self):
        """Test if this is a logical port."""
        return True

    @property
    def is_physical(self):
        """Test if this is a physical port."""
        return True

class IOBlockOutputPort(AbstractOutputPort):
    """IO block output port.

    Args:
        block (`IOBlock`): the block this port belongs to
        name (:obj:`str`): name of this port
        width (:obj:`int`): width of this port
        side (`Side`): on which side of the block is this port
    """
    def __init__(self, block, name, width, side):
        super(IOBlockOutputPort, self).__init__(block, name, width)
        self.__side = side

    @property
    def side(self):
        """On which side of the block is this port."""
        return self.__side

    @property
    def xoffset(self):
        """If the block is larger than 1 tile, specify detailed X-dimension position of this port."""
        return 0

    @property
    def yoffset(self):
        """If the block is larger than 1 tile, specify detailed Y-dimension position of this port."""
        return 0

    @property
    def is_logical(self):
        """Test if this is a logical port."""
        return True

    @property
    def is_physical(self):
        """Test if this is a physical port."""
        return True

class IOBlockClockPort(AbstractClockPort):
    """IO block clock port.

    Args:
        block (`IOBlock`): the block this port belongs to
        name (:obj:`str`): name of this port
        side (`Side`): on which side of the block is this port
        global_ (:obj:`str`): name of the global clock wire this port is hard-wired to
    """
    def __init__(self, block, name, side, global_):
        super(IOBlockClockPort, self).__init__(block, name)
        self.__side = side
        self.__global = global_

    @property
    def side(self):
        """On which side of the block is this port."""
        return self.__side

    @property
    def global_(self):
        """Name of the global clock wire this port is hard-wired to."""
        return self.__global

    @property
    def xoffset(self):
        """If the block is larger than 1 tile, specify detailed X-dimension position of this port."""
        return 0

    @property
    def yoffset(self):
        """If the block is larger than 1 tile, specify detailed Y-dimension position of this port."""
        return 0

    @property
    def is_logical(self):
        """Test if this is a logical port."""
        return True

    @property
    def is_physical(self):
        """Test if this is a physical port."""
        return True

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
        global_ (:obj:`str`, default=None): name of the non-clock global wire this port is hard-wired to
        xoffset (:obj:`int`, default=0): if the block is larger than 1 tile, specify detailed X-dimension position
            of this port
        yoffset (:obj:`int`, default=0): if the block is larger than 1 tile, specify detailed Y-dimension position
            of this port

    Raises:
        `PRGAInternalError`: if this port is hard-wired to a non-clock global wire but the width is not 1
    """
    def __init__(self, block, name, width, side, global_ = None, xoffset = 0, yoffset = 0):
        super(LogicBlockInputPort, self).__init__(block, name, width, side, global_)
        self.__xoffset = xoffset
        self.__yoffset = yoffset

    @property
    def xoffset(self):
        """If the block is larger than 1 tile, specify detailed X-dimension position of this port."""
        return self.__xoffset

    @property
    def yoffset(self):
        """If the block is larger than 1 tile, specify detailed Y-dimension position of this port."""
        return self.__yoffset

class LogicBlockOutputPort(IOBlockOutputPort):
    """Logic block output port.

    Args:
        block (`LogicBlock`): the block this port belongs to
        name (:obj:`str`): name of this port
        width (:obj:`int`): width of this port
        side (`Side`): on which side of the block is this port
        xoffset (:obj:`int`, default=0): if the block is larger than 1 tile, specify detailed X-dimension position
            of this port
        yoffset (:obj:`int`, default=0): if the block is larger than 1 tile, specify detailed Y-dimension position
            of this port
    """
    def __init__(self, block, name, width, side, xoffset = 0, yoffset = 0):
        super(LogicBlockOutputPort, self).__init__(block, name, width, side)
        self.__xoffset = xoffset
        self.__yoffset = yoffset

    @property
    def xoffset(self):
        """If the block is larger than 1 tile, specify detailed X-dimension position of this port."""
        return self.__xoffset

    @property
    def yoffset(self):
        """If the block is larger than 1 tile, specify detailed Y-dimension position of this port."""
        return self.__yoffset

class LogicBlockClockPort(IOBlockClockPort):
    """Logic block clock port.

    Args:
        block (`LogicBlock`): the block this port belongs to
        name (:obj:`str`): name of this port
        side (`Side`): on which side of the block is this port
        global_ (:obj:`str`): name of the global clock wire this port is hard-wired to
        xoffset (:obj:`int`, default=0): if the block is larger than 1 tile, specify detailed X-dimension position
            of this port
        yoffset (:obj:`int`, default=0): if the block is larger than 1 tile, specify detailed Y-dimension position
            of this port
    """
    def __init__(self, block, name, side, global_, xoffset = 0, yoffset = 0):
        super(LogicBlockClockPort, self).__init__(block, name, side, global_)
        self.__xoffset = xoffset
        self.__yoffset = yoffset

    @property
    def xoffset(self):
        """If the block is larger than 1 tile, specify detailed X-dimension position of this port."""
        return self.__xoffset

    @property
    def yoffset(self):
        """If the block is larger than 1 tile, specify detailed Y-dimension position of this port."""
        return self.__yoffset

# ----------------------------------------------------------------------------
# -- Physical Block Ports ----------------------------------------------------
# ----------------------------------------------------------------------------
class PhysicalBlockInputPort(PhysicalInputPort):
    """Physical input port for block.

    Args:
        block (`AbstractBlock`-subclass): the block this port belongs to
        name (:obj:`str`): name of this port
        width (:obj:`int`): width of this port
        global_ (:obj:`str`, default=None): array's physical input wire driving this port
        is_external (:obj:`bool`, default=False): if this port is directly connected to outside the top-level module
    """
    def __init__(self, block, name, width, global_ = None, is_external = False):
        super(PhysicalBlockInputPort, self).__init__(block, name, width)
        self.__global = global_
        self.__is_external = is_external

    @property
    def global_(self):
        """The default driver."""
        return self.__global

    @global_.setter
    def global_(self, global_):
        self.__global = global_

    @property
    def is_external(self):
        """Test if this port is directly connected to outside the top-level module."""
        return self.__is_external

class PhysicalBlockOutputPort(PhysicalOutputPort):
    """Physical output port for block.

    Args:
        block (`AbstractBlock`-subclass): the block this port belongs to
        name (:obj:`str`): name of this port
        width (:obj:`int`): width of this port
        is_external (:obj:`bool`, default=False): if this port is directly connected to outside the top-level module
    """
    def __init__(self, block, name, width, is_external = False):
        super(PhysicalBlockOutputPort, self).__init__(block, name, width)
        self.__is_external = is_external

    @property
    def is_external(self):
        """Test if this port is directly connected to outside the top-level module."""
        return self.__is_external
