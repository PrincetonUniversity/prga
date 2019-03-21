# Python 2 and 3 compatible
from prga.compatible import *

from prga._archdef.common import ModuleType
from prga._archdef.moduleinstance.module import MutableLeafModule, LogicallyConnectableModule
from prga._archdef.moduleinstance.configurable import ConfigurableNonLeafModule
from prga._archdef.moduleinstance.instance import Instance
from prga._archdef.portpin.port import PhysicalInputPort, PhysicalOutputPort
from prga._archdef.block.port import SliceInputPort, SliceOutputPort, SliceClockPort
from prga.exception import PRGAInternalError, PRGAAPIError

# ----------------------------------------------------------------------------
# -- Slice -------------------------------------------------------------------
# ----------------------------------------------------------------------------
class Slice(LogicallyConnectableModule, ConfigurableNonLeafModule, MutableLeafModule):
    """Intermediate non-leaf pb_type inside a logic/io block.

    Args:
        name (:obj:`str`): name of this module
    """
    def __init__(self, name):
        super(Slice, self).__init__(name)
        self._pack_patterns = []   # a pair of (source, sink) pin/port bits

    # == low-level API =======================================================
    @property
    def type(self):
        """Type of this module."""
        return ModuleType.slice_

    @property
    def is_physical(self):
        """Test if this is a physical module."""
        return True

    @property
    def is_logical(self):
        """Test if this is a logical module."""
        return True

    # == high-level API ======================================================
    def add_input(self, name, width):
        """Add an input port.
        
        Args:
            name (:obj:`str`): name of the port
            width (:obj:`int`): width of the port
        """
        try:
            self.add_port(SliceInputPort(self, name, width))
        except PRGAInternalError as e:
            raise_from(PRGAAPIError(e.message), e)

    def add_output(self, name, width):
        """Add an output port.

        Args:
            name (:obj:`str`): name of the port
            width (:obj:`int`): width of the port
        """
        try:
            self.add_port(SliceOutputPort(self, name, width))
        except PRGAInternalError as e:
            raise_from(PRGAAPIError(e.message), e)

    def add_clock(self, name):
        """Add a clock port.

        Args:
            name (:obj:`str`): name of the port
        """
        try:
            self.add_port(SliceClockPort(self, name))
        except PRGAInternalError as e:
            raise_from(PRGAAPIError(e.message), e)

    def add_instance(self, name, model):
        """Add an instance to this module.

        Args:
            name (:obj:`str`): name of the instance
            model (`AbstractLeafModule`-subclass): the module to be instantiated
        """
        if not (model.is_slice or model.is_user_primitive):
            raise PRGAAPIError("Cannot instantiate '{}' in slice or block '{}'"
                    .format(model, self))
        try:
            self.add_instance_raw(Instance(self, model, name))
        except PRGAInternalError as e:
            raise_from(PRGAAPIError(e.message), e)
