# -*- enconding: ascii -*-

"""Built-in switches: configurable muxes."""

__all__ = ['MuxModel']

import logging
_logger = logging.getLogger(__name__)

from ..portpin.port import PhysicalInputPort, PhysicalOutputPort
from ..common import ModuleType, SwitchType
from ..moduleinstance.module import AbstractLeafModule
from ...exception import PRGAInternalError
from ..._util.util import DictProxy

from math import ceil, log
from collections import OrderedDict

# ----------------------------------------------------------------------------
# -- MuxModel ----------------------------------------------------------------
# ----------------------------------------------------------------------------
class MuxModel(AbstractLeafModule):
    """Built-in model for configurable muxes.
    
    Args:
        context (`ArchitectureContext`): the architecture context this model belongs to
        width (:obj:`int`): number of inputs of the mux. Valid numbers are 2 <= width.

    Raises:
        `PRGAInternalError`: if the number of inputs is not valid.
    """
    def __init__(self, context, width):
        if width < 2:
            raise PRGAInternalError("Only muxes with number of inputs >= 2 are supported")
        super(MuxModel, self).__init__(context, 'cmux{}'.format(width))
        self.__width = width
        self.__width_sel = int(ceil(log(self.__width, 2)))
        self.__ports = OrderedDict((
            ('i', PhysicalInputPort(self, name='i', width=width)),
            ('o', PhysicalOutputPort(self, name='o', width=1)),
            ('cfg_e', PhysicalInputPort(self, name='cfg_e', width=1)),
            ('cfg_d', PhysicalInputPort(self, name='cfg_d', width=self.width_sel)),
            ))

    @property
    def _ports(self):
        """A mapping from name to all ports."""
        return DictProxy(self.__ports)

    @property
    def width(self):
        """Number of inputs of this configurable mux."""
        return self.__width

    @property
    def width_sel(self):
        """Width of the 'sel' port of this mux."""
        return self.__width_sel

    @property
    def type(self):
        """Type of this module."""
        return ModuleType.switch

    @property
    def switch_type(self):
        """Type of this switch."""
        return SwitchType.mux

    @property
    def is_physical(self):
        """Test if this is a physical module."""
        return True
