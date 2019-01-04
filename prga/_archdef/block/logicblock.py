# -*- encoding: ascii -*-

"""Logic block: the major logic-implementing blocks containing LUTs, FFs, and/or hard macros."""

__all__ = ['LogicBlock']

import logging
_logger = logging.getLogger(__name__)

from ..common import BlockType, Side
from port import LogicBlockInputPort, LogicBlockOutputPort, LogicBlockClockPort
from abstractblock import AbstractLogicalBlock
from ...exception import PRGAInternalError, PRGAAPIError

# ----------------------------------------------------------------------------
# -- LogicBlock --------------------------------------------------------------
# ----------------------------------------------------------------------------
class LogicBlock(AbstractLogicalBlock):
    """Logic block, also called CLB, slice, etc.
    
    Args:
        context (`ArchitectureContext`): the architecture context this model belongs to
        name (:obj:`str`): name of this block
        width (:obj:`int`, default=1): width of this block
        height (:obj:`int`, default=1): height of this block
    """
    def __init__(self, context, name, width = 1, height = 1):
        super(LogicBlock, self).__init__(context, name)
        self.__width = width
        self.__height = height

    # -- private helper ------------------------------------------------------
    def __validate_position_and_side(self, x, y, side):
        """Check if the given position and side are valid in the block."""
        if not ((side is Side.left and x == 0 and y >= 0 and y < self.height) or
                (side is Side.right and x == self.width - 1 and y >= 0 and y < self.height) or
                (side is Side.bottom and y == 0 and x >= 0 and x < self.width) or
                (side is Side.top and y == self.height - 1 and x >= 0 and x < self.width)):
            raise PRGAAPIError("Offset ({}, {}) is not at the {} side of block '{}'"
                    .format(x, y, side.name, self.name))

    # -- abstract property implementation ------------------------------------
    @property
    def block_type(self):
        """Type of this block."""
        return BlockType.logic

    # -- exposed API --------------------------------------------------------
    @property
    def width(self):
        """Width of this block."""
        return self.__width

    @property
    def height(self):
        """Width of this block."""
        return self.__height

    def add_input(self, name, width, side, global_ = None, xoffset = 0, yoffset = 0):
        """Add a block input port.

        Args:
            name (:obj:`str`): name of this port
            width (:obj:`int`): width of this port
            side (`Side`): on which side of the block is this port
            global_ (:obj:`str`, default=None): name of the non-clock global wire this port is hard-wired to
            xoffset (:obj:`int`, default=0): if the block is larger than 1 tile, specify detailed X-dimension position
                of this port
            yoffset (:obj:`int`, default=0): if the block is larger than 1 tile, specify detailed Y-dimension position
                of this port

        Raises:
            `PRGAAPIError`: if the logic block already has a port with the same name, or the name conflicts with
                reserved port names, or the position and side values don't match
        """
        try:
            self._validate_port_name(name)
            self.__validate_position_and_side(xoffset, yoffset, side)
        except PRGAAPIError:
            raise
        if global_ is not None:
            if global_ not in self._context.globals:
                raise PRGAAPIError("Global wire '{}' does not exist in architecture context '{}'"
                        .format(global_, self._context.name))
            if width != 1:
                raise PRGAAPIError("Block input '{}' that's hard-wired to a global wire must be 1-bit wide"
                        .format(name))
        self._add_port(LogicBlockInputPort(self, name, width, side, global_, xoffset, yoffset))

    def add_output(self, name, width, side, xoffset = 0, yoffset = 0):
        """Add a block output port.

        Args:
            name (:obj:`str`): name of this port
            width (:obj:`int`): width of this port
            side (`Side`): on which side of the block is this port
            xoffset (:obj:`int`, default=0): if the block is larger than 1 tile, specify detailed X-dimension position
                of this port
            yoffset (:obj:`int`, default=0): if the block is larger than 1 tile, specify detailed Y-dimension position
                of this port

        Raises:
            `PRGAAPIError`: if the logic block already has a port with the same name, or the name conflicts with
                reserved port names.
        """
        try:
            self._validate_port_name(name)
            self.__validate_position_and_side(xoffset, yoffset, side)
        except PRGAAPIError:
            raise
        self._add_port(LogicBlockOutputPort(self, name, width, side, xoffset, yoffset))

    def add_clock(self, name, side, global_, xoffset = 0, yoffset = 0):
        """Add a block clock port.

        Args:
            name (:obj:`str`): name of this port
            side (`Side`): on which side of the block is this port
            global_ (:obj:`str`): name of the global clock wire this port is hard-wired to
            xoffset (:obj:`int`, default=0): if the block is larger than 1 tile, specify detailed X-dimension position
                of this port
            yoffset (:obj:`int`, default=0): if the block is larger than 1 tile, specify detailed Y-dimension position
                of this port

        Raises:
            `PRGAAPIError`: if the logic block already has a port with the same name, or the name conflicts with
                reserved port names.
        """
        try:
            self._validate_port_name(name)
            self.__validate_position_and_side(xoffset, yoffset, side)
        except PRGAAPIError:
            raise
        if global_ not in self._context.globals:
            raise PRGAAPIError("Global wire '{}' does not exist in architecture context '{}'"
                        .format(global_, self._context.name))
        elif not self._context.globals[global_].is_clock:
            raise PRGAAPIError("Global wire '{}' is not a clock".format(global_))
        self._add_port(LogicBlockClockPort(self, name, side, global_, xoffset, yoffset))
