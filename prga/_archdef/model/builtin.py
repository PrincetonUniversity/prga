# -*- enconding: ascii -*-

"""Built-in models: lut2-lut8, flipflop."""

__all__ = ['LUTModel', 'FlipflopModel', 'InputModel', 'OutputModel', 'InoutModel']

import logging
_logger = logging.getLogger(__name__)

from ..common import ModelPortClass, ModuleType
from port import LogicalModelInputPort, LogicalModelOutputPort, ModelInputPort, ModelOutputPort, ModelClockPort
from ..portpin.port import PhysicalInputPort
from ..moduleinstance.module import AbstractLeafModule
from ...exception import PRGAInternalError
from ..._util.util import DictProxy

from collections import OrderedDict

# ----------------------------------------------------------------------------
# -- LUTModel ----------------------------------------------------------------
# ----------------------------------------------------------------------------
class LUTModel(AbstractLeafModule):
    """Built-in model for LUTs.
    
    Args:
        context (`ArchitectureContext`): the architecture context this model belongs to
        width (:obj:`int`): number of inputs of the LUT. Valid numbers are 2 <= width <= 8

    Raises:
        `PRGAInternalError`: if the number of inputs is not valid.
    """
    def __init__(self, context, width):
        if width < 2 or width > 8:
            raise PRGAInternalError("Only LUTs with 2 <= number of inputs <= 8 are supported")
        super(LUTModel, self).__init__(context, 'lut{}'.format(width))
        self.__width = width
        self.__ports = OrderedDict((
            ('in', ModelInputPort(self, name='in', width=width, port_class=ModelPortClass.lut_in)),
            ('out', ModelOutputPort(self, name='out', width=1, sources=('in', ),
                port_class=ModelPortClass.lut_out)),
            ('cfg_e', PhysicalInputPort(self, name='cfg_e', width=1)),
            ('cfg_d', PhysicalInputPort(self, name='cfg_d', width=2**width)),
            ))

    @property
    def _ports(self):
        """A mapping from name to all ports."""
        return DictProxy(self.__ports)

    @property
    def width(self):
        """Number of inputs of this LUT."""
        return self.__width

    @property
    def type(self):
        """Type of this module."""
        return ModuleType.lut

    @property
    def is_logical(self):
        """Test if this is a logical module."""
        return True

    @property
    def is_physical(self):
        """Test if this is a physical module."""
        return True

# ----------------------------------------------------------------------------
# -- FlipflopModel -----------------------------------------------------------
# ----------------------------------------------------------------------------
class FlipflopModel(AbstractLeafModule):
    """Built-in model for Flipflops.
    
    Args:
        context (`ArchitectureContext`): the architecture context this model belongs to
    """
    def __init__(self, context):
        super(FlipflopModel, self).__init__(context, 'flipflop')
        self.__ports = OrderedDict((
            ('clk', ModelClockPort(self, name='clk', port_class=ModelPortClass.clock)),
            ('D', ModelInputPort(self, name='D', width=1, clock='clk', port_class=ModelPortClass.D)),
            ('Q', ModelOutputPort(self, name='Q', width=1, clock='clk', port_class=ModelPortClass.Q)),
            ))

    @property
    def _ports(self):
        """A mapping from name to all ports."""
        return DictProxy(self.__ports)

    @property
    def type(self):
        """Type of this module."""
        return ModuleType.flipflop

    @property
    def is_logical(self):
        """Test if this is a logical module."""
        return True

    @property
    def is_physical(self):
        """Test if this is a physical module."""
        return True

# ----------------------------------------------------------------------------
# -- IO pad models -----------------------------------------------------------
# ----------------------------------------------------------------------------
class InputModel(AbstractLeafModule):
    """Built-in input pad. This is a logical-only model.
    
    Args:
        context (`ArchitectureContext`): the architecture context this model belongs to
    """
    def __init__(self, context):
        super(InputModel, self).__init__(context, 'input')
        self.__ports = OrderedDict((
            ('inpad', LogicalModelOutputPort(self, name='inpad', width=1)),
            ))

    @property
    def _ports(self):
        """A mapping from name to all ports."""
        return DictProxy(self.__ports)

    @property
    def type(self):
        """Type of this module."""
        return ModuleType.inpad

    @property
    def is_logical(self):
        """Test if this is a logical module."""
        return True

class OutputModel(AbstractLeafModule):
    """Built-in output pad. This is a logical-only model.
    
    Args:
        context (`ArchitectureContext`): the architecture context this model belongs to
    """
    def __init__(self, context):
        super(OutputModel, self).__init__(context, 'output')
        self.__ports = OrderedDict((
            ('outpad', LogicalModelInputPort(self, name='outpad', width=1)),
            ))

    @property
    def _ports(self):
        """A mapping from name to all ports."""
        return DictProxy(self.__ports)

    @property
    def type(self):
        """Type of this module."""
        return ModuleType.outpad

    @property
    def is_logical(self):
        """Test if this is a logical module."""
        return True

class InoutModel(AbstractLeafModule):
    """Built-in inout pad. This is a logical-only model.
    
    Args:
        context (`ArchitectureContext`): the architecture context this model belongs to
    """
    def __init__(self, context):
        super(InoutModel, self).__init__(context, 'inout')
        self.__ports = OrderedDict((
            ('inpad', LogicalModelOutputPort(self, name='inpad', width=1)),
            ('outpad', LogicalModelInputPort(self, name='outpad', width=1)),
            ))

    @property
    def _ports(self):
        """A mapping from name to all ports."""
        return DictProxy(self.__ports)

    @property
    def type(self):
        """Type of this module."""
        return ModuleType.iopad

    @property
    def is_logical(self):
        """Test if this is a logical module."""
        return True
