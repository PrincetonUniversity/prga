# -*- encoding: ascii -*-

"""IO block: blocks for external I/Os."""

__all__ = ['IOBlock']

import logging
_logger = logging.getLogger(__name__)

from port import (IOBlockInputPort, IOBlockOutputPort, IOBlockClockPort, PhysicalBlockInputPort,
        PhysicalBlockOutputPort)
from abstractblock import AbstractLogicalBlock
from ..common import BlockType
from ..moduleinstance.instance import LogicalInstance
from ..portpin.port import PhysicalInputPort, PhysicalOutputPort
from ...exception import PRGAInternalError, PRGAAPIError

# ----------------------------------------------------------------------------
# -- IOBlock -----------------------------------------------------------------
# ----------------------------------------------------------------------------
class IOBlock(AbstractLogicalBlock):
    """IO block, also called IOB, etc.

    Args:
        context (`ArchitectureContext`): the architecture context this model belongs to
        name (:obj:`str`): name of this block
        capacity (:obj:`int`, default=1): number of blocks placed in one tile
    """
    def __init__(self, context, name, capacity = 1):
        super(IOBlock, self).__init__(context, name)
        self.__capacity = capacity

    # -- internal API --------------------------------------------------------
    def _add_external(self, input = True, output = True):
        """Add an external I/O to this IO block.

        Args:
            input (:obj:`bool`, default=True): if this IO block contains an input
            output (:obj:`bool`, default=True): if this IO block contains an output

        Raises:
            `PRGAInternalError`: if an external I/O is already present, or both `input` and `output` are set to False.

        Seting both `input` and `output` to True will create a bi-directional I/O with an output enable signal.
        """
        if 'extio' in self._instances:
            raise PRGAInternalError("IO block '{}' already has an external I/O".format(self.name))
        elif not input and not output:
            raise PRGAInternalError("At least one of 'input' and 'output' must be 'True'")
        # 1. add the logical instance
        instance = LogicalInstance(self._context._get_model(
            'inout' if input and output else 'input' if input else 'output'), 'extio')
        self._add_instance(instance)
        # 2. add the external ports
        if input:
            l = instance._pins['inpad']
            p = PhysicalBlockInputPort(self, 'extio_i', 1, is_external=True)
            p[0]._logical_cp, l[0]._physical_cp = l[0], p[0]
            self._add_port(p)
        if output:
            l = instance._pins['outpad']
            p = PhysicalBlockOutputPort(self, 'extio_o', 1, is_external=True)
            p[0]._logical_cp, l[0]._physical_cp = l[0], p[0]
            self._add_port(p)
        if input and output:
            self._add_port(PhysicalBlockOutputPort(self, 'extio_oe', 1, is_external=True))

    # -- abstract property implementation ------------------------------------
    @property
    def block_type(self):
        """Type of this block."""
        return BlockType.io

    # -- exposed API --------------------------------------------------------
    @property
    def capacity(self):
        """Number of blocks placed in one tile."""
        return self.__capacity

    def add_input(self, name, width, side, global_ = None):
        """Add a block input port.

        Args:
            name (:obj:`str`): name of this port
            width (:obj:`int`): width of this port
            side (`Side`): on which side of the block is this port
            global_ (:obj:`str`, default=None): name of the non-clock global wire this port is hard-wired to

        Raises:
            `PRGAAPIError`: if the logic block already has a port with the same name, or the name conflicts with
                reserved port names.
        """
        try:
            self._validate_port_name(name)
        except PRGAAPIError:
            raise
        if global_ is not None:
            if global_ not in self._context.globals:
                raise PRGAAPIError("Global wire '{}' does not exist in architecture context '{}'"
                        .format(global_, self._context.name))
            if width != 1:
                raise PRGAAPIError("Block input '{}' that's hard-wired to a global wire must be 1-bit wide"
                        .format(name))
        self._add_port(IOBlockInputPort(self, name, width, side, global_))

    def add_output(self, name, width, side):
        """Add a block output port.

        Args:
            name (:obj:`str`): name of this port
            width (:obj:`int`): width of this port
            side (`Side`): on which side of the block is this port

        Raises:
            `PRGAAPIError`: if the logic block already has a port with the same name, or the name conflicts with
                reserved port names.
        """
        try:
            self._validate_port_name(name)
        except PRGAAPIError:
            raise
        self._add_port(IOBlockOutputPort(self, name, width, side))

    def add_clock(self, name, side, global_):
        """Add a block clock port.

        Args:
            name (:obj:`str`): name of this port
            side (`Side`): on which side of the block is this port
            global_ (:obj:`str`): name of the global clock wire this port is hard-wired to

        Raises:
            `PRGAAPIError`: if the logic block already has a port with the same name, or the name conflicts with
                reserved port names.
        """
        try:
            self._validate_port_name(name)
        except PRGAAPIError:
            raise
        if global_ not in self._context.globals:
            raise PRGAAPIError("Global wire '{}' does not exist in architecture context '{}'"
                        .format(global_, self._context.name))
        elif not self._context.globals[global_].is_clock:
            raise PRGAAPIError("Global wire '{}' is not a clock".format(global_))
        self._add_port(IOBlockClockPort(self, name, side, global_))
