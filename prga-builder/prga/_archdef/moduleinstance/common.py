# Python 2 and 3 compatible
from prga.compatible import *

from prga._archdef.common import ModuleType, PrimitiveType, SwitchType, BlockType
from prga._util.util import ExtensibleObject
from prga.exception import PRGAInternalError

from abc import ABCMeta, abstractproperty, abstractmethod

# ----------------------------------------------------------------------------
# -- AbstractModuleOrInstance ------------------------------------------------
# ----------------------------------------------------------------------------
class AbstractModuleOrInstance(with_metaclass(ABCMeta, ExtensibleObject)):
    """Abstract base class for module & instance."""

    # == low-level API =======================================================
    # -- properties/methods to be overriden by subclasses --------------------
    @abstractproperty
    def name(self):
        """Name of this module/instance."""
        raise NotImplementedError

    @abstractproperty
    def type(self):
        """Type of this module/instance."""
        raise NotImplementedError

    @property
    def is_logical(self):
        """Test if this is a logical module/instance."""
        return False

    @property
    def is_physical(self):
        """Test if this is a physical module/instance."""
        return False

    # -- derived properties --------------------------------------------------
    @property
    def is_primitive(self):
        """Test if this module/instance is a primitive."""
        return self.type is ModuleType.primitive

    @property
    def is_switch(self):
        """Test if this module/instance is a configurable switch."""
        return self.type is ModuleType.switch

    @property
    def is_config(self):
        """Test if this module/instance is a configuration circuitry."""
        return self.type is ModuleType.config

    @property
    def is_shadow(self):
        """Test if this module/instance is a shadow module."""
        return self.type is ModuleType.shadow

    @property
    def is_slice(self):
        """Test if this module/instance is an intermediate slice in a logic/io block."""
        return self.type is ModuleType.slice_

    @property
    def is_block(self):
        """Test if this module/instance is a block."""
        return self.type is ModuleType.block

    # -- properties if this module/instance is a switch ----------------------
    @property
    def primitive_type(self):
        """Type of this primitive (if it is a primitive)."""
        raise PRGAInternalError("'{}' is not a primitive".format(self))

    @property
    def is_user_primitive(self):
        """Test if this is a user-instantiable primitive."""
        return self.primitive_type in (PrimitiveType.custom, PrimitiveType.lut, PrimitiveType.flipflop,
                PrimitiveType.memory, PrimitiveType.multimode)

    @property
    def is_configurable_primitive(self):
        """Test if this is a configurable primitive."""
        return self.primitive_type in (PrimitiveType.lut, PrimitiveType.iopad, PrimitiveType.multimode)

    @property
    def is_custom_primitive(self):
        """Test if this is a user-defined primitive."""
        return self.primitive_type is PrimitiveType.custom

    @property
    def is_lut_primitive(self):
        """Test if this is a built-in LUT."""
        return self.primitive_type is PrimitiveType.lut

    @property
    def is_flipflop_primitive(self):
        """Test if this is a built-in D-flipflop."""
        return self.primitive_type is PrimitiveType.flipflop

    @property
    def is_inpad_primitive(self):
        """Test if this is the built-in external input."""
        return self.primitive_type is PrimitiveType.inpad

    @property
    def is_outpad_primitive(self):
        """Test if this is the built-in external output."""
        return self.primitive_type is PrimitiveType.outpad

    @property
    def is_iopad_primitive(self):
        """Test if this is the built-in external inout."""
        return self.primitive_type is PrimitiveType.iopad

    @property
    def is_memory_primitive(self):
        """Test if this is a memory primitive."""
        return self.primitive_type is PrimitiveType.memory

    @property
    def is_multimode_primitive(self):
        """Test if this is a multimode primitive."""
        return self.primitive_type is PrimitiveType.multimode

    # -- properties if this module/instance is a switch ----------------------
    @property
    def switch_type(self):
        """Type of this switch (if this is a switch)."""
        raise PRGAInternalError("'{}' is not a switch".format(self))

    @property
    def is_mux_switch(self):
        """Test if this is a configurable mux."""
        return self.switch_type is SwitchType.mux

    @property
    def is_buf_switch(self):
        """Test if this is a configurable buffer."""
        return self.switch_type is SwitchType.buf

    # -- properties if this module/instance is a block -----------------------
    @property
    def block_type(self):
        """Type of this module/instance if this is a block."""
        raise PRGAInternalError("'{}' is not a block".format(self))

    @property
    def tile_type(self):
        """Type of this tile."""
        return self.block_type.tile_type

    @property
    def is_logic_block(self):
        """Test if this is a logic block."""
        return self.block_type is BlockType.logic

    @property
    def is_io_block(self):
        """Test if this is an IO block."""
        return self.block_type is BlockType.io

    @property
    def is_routing_block(self):
        """Test if this is a routing block."""
        return self.block_type in (BlockType.xconn, BlockType.yconn, BlockType.switch,
                BlockType.xroute, BlockType.yroute)

    @property
    def is_xconn_block(self):
        """Test if this is a X-dimensional connection block."""
        return self.block_type is BlockType.xconn

    @property
    def is_yconn_block(self):
        """Test if this is a Y-dimensional connection block."""
        return self.block_type is BlockType.yconn

    @property
    def is_switch_block(self):
        """Test if this is a switch block."""
        return self.block_type is BlockType.switch

    @property
    def is_xroute_block(self):
        """Test if this is a X-dimensional connection block w/ combined switch block."""
        return self.block_type is BlockType.xroute

    @property
    def is_yroute_block(self):
        """Test if this is a Y-dimensional connection block w/ combined switch block."""
        return self.block_type is BlockType.yroute

    @property
    def is_array(self):
        """Test if this module/instance is an array."""
        return self.block_type is BlockType.array

    # == high-level API ======================================================
    @abstractmethod
    def __str__(self):
        raise NotImplementedError
