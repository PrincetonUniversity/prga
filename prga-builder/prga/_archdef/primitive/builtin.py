# Python 2 and 3 compatible
from prga.compatible import *

from prga._archdef.common import PrimitivePortClass, ModuleType, PrimitiveType
from prga._archdef.portpin.port import PhysicalInputPort, GlobalPhysicalInputPort
from prga._archdef.moduleinstance.module import AbstractLeafModule
from prga._archdef.primitive.port import (LogicalPrimitiveInputPort, LogicalPrimitiveOutputPort,
        LogicalPrimitiveClockPort, PrimitiveInputPort, PrimitiveOutputPort, PrimitiveClockPort)
from prga._util.util import DictDelegate

from collections import OrderedDict

# ----------------------------------------------------------------------------
# -- LUT Primitive -----------------------------------------------------------
# ----------------------------------------------------------------------------
class LUTPrimitive(AbstractLeafModule):
    """Built-in primitive for LUTs.
    
    Args:
        width (:obj:`int`): number of inputs of the LUT. Valid numbers are 2 <= width <= 8

    Raises:
        `PRGAInternalError`: if the number of inputs is not valid.
    """
    def __init__(self, width):
        if width < 2 or width > 8:
            raise PRGAInternalError("Only LUTs with 2 <= number of inputs <= 8 are supported")
        super(LUTPrimitive, self).__init__('lut{}'.format(width))
        self.__width = width
        self.__ports = OrderedDict((
            ('in', PrimitiveInputPort(self, name='in', width=width, port_class=PrimitivePortClass.lut_in)),
            ('out', PrimitiveOutputPort(self, name='out', width=1, sources=('in', ),
                port_class=PrimitivePortClass.lut_out)),
            ('cfg_e', GlobalPhysicalInputPort(self, name='cfg_e', width=1)),
            ('cfg_d', PhysicalInputPort(self, name='cfg_d', width=2**width)),
            ))

    @property
    def _ports(self):
        return DictDelegate(self.__ports)

    @property
    def _fixed_ext(self):
        return {"verilog_template": "lut.builtin.tmpl.v"}

    @property
    def is_logical(self):
        return True

    @property
    def is_physical(self):
        return True

    @property
    def type(self):
        return ModuleType.primitive

    @property
    def primitive_type(self):
        return PrimitiveType.lut

    @property
    def width(self):
        """Number of inputs of this LUT."""
        return self.__width

# ----------------------------------------------------------------------------
# -- Flip-flop Primitive -----------------------------------------------------
# ----------------------------------------------------------------------------
class FlipflopPrimitive(AbstractLeafModule):
    """Built-in primitive for Flipflops. """
    def __init__(self):
        super(FlipflopPrimitive, self).__init__('flipflop')
        self.__ports = OrderedDict((
            ('clk', PrimitiveClockPort(self, name='clk', port_class=PrimitivePortClass.clock)),
            ('D', PrimitiveInputPort(self, name='D', width=1, clock='clk', port_class=PrimitivePortClass.D)),
            ('Q', PrimitiveOutputPort(self, name='Q', width=1, clock='clk', port_class=PrimitivePortClass.Q)),
            ))

    @property
    def _ports(self):
        return DictDelegate(self.__ports)

    @property
    def _fixed_ext(self):
        return {"verilog_template": "ff.builtin.tmpl.v"}

    @property
    def is_logical(self):
        return True

    @property
    def is_physical(self):
        return True

    @property
    def type(self):
        return ModuleType.primitive

    @property
    def primitive_type(self):
        return PrimitiveType.flipflop

# ----------------------------------------------------------------------------
# -- IO pad primitives -------------------------------------------------------
# ----------------------------------------------------------------------------
class InpadPrimitive(AbstractLeafModule):
    """Built-in input pad. This is a logical-only primitive."""
    def __init__(self):
        super(InputPrimitive, self).__init__('inpad')
        self.__ports = OrderedDict((
            ('inpad', LogicalPrimitiveOutputPort(self, name = 'inpad', width = 1)),
            ))

    @property
    def _ports(self):
        """A mapping from port names to all ports."""
        return DictDelegate(self.__ports)

    @property
    def is_logical(self):
        """Test if this is a logical module."""
        return True

    @property
    def type(self):
        """Type of this module."""
        return ModuleType.primitive

    @property
    def primitive_type(self):
        """Type of this primitive."""
        return PrimitiveType.inpad

class OutpadPrimitive(AbstractLeafModule):
    """Built-in output pad. This is a logical-only primitive."""
    def __init__(self):
        super(OutpadPrimitive, self).__init__('outpad')
        self.__ports = OrderedDict((
            ('outpad', LogicalPrimitiveInputPort(self, name = 'outpad', width = 1)),
            ))

    @property
    def _ports(self):
        """A mapping from port names to all ports."""
        return DictDelegate(self.__ports)

    @property
    def is_logical(self):
        """Test if this is a logical module."""
        return True

    @property
    def type(self):
        """Type of this module."""
        return ModuleType.primitive

    @property
    def primitive_type(self):
        """Type of this primitive."""
        return PrimitiveType.outpad

class IopadPrimitive(AbstractLeafModule):
    """Built-in input/output pad. This is a logical-only primitive.
    
    Note:
        After we support multi-mode primitives, redesign this with the multi-mode mechanism.
    """
    def __init__(self):
        super(IopadPrimitive, self).__init__('iopad')
        self.__ports = OrderedDict((
            ('inpad', LogicalPrimitiveOutputPort(self, name = 'inpad', width = 1)),
            ('outpad', LogicalPrimitiveInputPort(self, name = 'outpad', width = 1)),
            ))

    @property
    def _ports(self):
        """A mapping from port names to all ports."""
        return DictDelegate(self.__ports)

    @property
    def is_logical(self):
        """Test if this is a logical module."""
        return True

    @property
    def type(self):
        """Type of this module."""
        return ModuleType.primitive

    @property
    def primitive_type(self):
        """Type of this primitive."""
        return PrimitiveType.iopad
