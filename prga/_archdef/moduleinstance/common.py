# -*- enconding: ascii -*-

"""Abstract base class for all modules and instances."""

__all__ = []

import logging
_logger = logging.getLogger(__name__)

from ..common import ModuleType, SwitchType, BlockType
from ...exception import PRGAInternalError

from abc import ABCMeta, abstractproperty, abstractmethod

# ----------------------------------------------------------------------------
# -- AbstractModuleOrInstance -----------------------------------------------
# ----------------------------------------------------------------------------
class AbstractModuleOrInstance(object):
    """Abstract base class for module & instance."""
    __metaclass__ = ABCMeta

    # -- properties/methods to be overriden by subclasses --------------------
    @abstractproperty
    def name(self):
        """:obj:`abstractproperty`: Type of this module."""
        raise NotImplementedError

    @abstractproperty
    def type(self):
        """:obj:`abstractproperty`: Type of this module."""
        raise NotImplementedError

    # -- derived properties --------------------------------------------------
    @property
    def is_user_model(self):
        """Test if this module is a user-instantiable model type."""
        return self.type in (ModuleType.custom, ModuleType.flipflop, ModuleType.lut, ModuleType.memory,
                ModuleType.multimode)

    @property
    def is_custom_model(self):
        """Test if this module is a user-defined model type."""
        return self.type is ModuleType.custom

    @property
    def is_flipflop(self):
        """Test if this module is the built-in flipflop."""
        return self.type is ModuleType.flipflop

    @property
    def is_lut(self):
        """Test if this module is a built-in LUT."""
        return self.type is ModuleType.lut

    @property
    def is_inpad(self):
        """Test if this module is the built-in external input."""
        return self.type is ModuleType.inpad

    @property
    def is_outpad(self):
        """Test if this module is the built-in external output."""
        return self.type is ModuleType.outpad

    @property
    def is_iopad(self):
        """Test if this module is the built-in external inout."""
        return self.type is ModuleType.iopad

    @property
    def is_memory(self):
        """Test if this module is a memory type."""
        return self.type is ModuleType.memory

    @property
    def is_multimode(self):
        """Test if this module is a multimode type."""
        return self.type is ModuleType.multimode

    @property
    def is_config(self):
        """Test if this module is a configuration circuitry type."""
        return self.type is ModuleType.config

    @property
    def is_switch(self):
        """Test if this module is a configurable switch type."""
        return self.type is ModuleType.switch

    @property
    def is_addon(self):
        """Test if this module is an add-on module type."""
        return self.type is ModuleType.addon

    @property
    def is_block(self):
        """Test if this module is a block module type."""
        return self.type is ModuleType.block

    # -- properties if this module is a switch -------------------------------
    @property
    def switch_type(self):
        """Type of this module if this is a switch."""
        raise PRGAInternalError("Module '{}' is not a switch".format(self.name))

    @property
    def is_mux_switch(self):
        """Test if this is a configurable mux."""
        return self.switch_type is SwitchType.mux

    # -- properties if this module is a block --------------------------------
    @property
    def block_type(self):
        """Type of this module if this is a block."""
        raise PRGAInternalError("Module '{}' is not a block".format(self.name))

    @property
    def is_logic_block(self):
        """Test if this is a logic block."""
        return self.block_type is BlockType.logic

    @property
    def is_io_block(self):
        """Test if this is an IO block."""
        return self.block_type is BlockType.io

    @property
    def is_horizontal_connection_block(self):
        """Test if this is a horizontal connection block."""
        return self.block_type is BlockType.horizontalconnection

    @property
    def is_vertical_connection_block(self):
        """Test if this is a vertical connection block."""
        return self.block_type is BlockType.verticalconnection

    @property
    def is_switch_block(self):
        """Test if this is a switch block."""
        return self.block_type is BlockType.switch
