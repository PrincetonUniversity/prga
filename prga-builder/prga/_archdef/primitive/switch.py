# Python 2 and 3 compatible
from prga.compatible import *

from prga._archdef.common import ModuleType, SwitchType
from prga._archdef.portpin.port import GlobalPhysicalInputPort, PhysicalInputPort, PhysicalOutputPort
from prga._archdef.moduleinstance.configurable import AbstractSwitchModule
from prga._util.util import DictDelegate

from collections import OrderedDict
from math import log, ceil

# ----------------------------------------------------------------------------
# -- Default Configurable Mux ------------------------------------------------
# ----------------------------------------------------------------------------
class CMUXSwitch(AbstractSwitchModule):
    """Default configurable mux module.

    Args:
        width (:obj:`int`): number of inputs of the CMUX. Valid numbers are width >= 2 

    Raises:
        `PRGAInternalError`: if the number of inputs is not valid.
    """
    def __init__(self, width):
        if width < 2:
            raise PRGAInternalError("Only MUXes with number of inputs >= 2 are supported")
        super(CMUXSwitch, self).__init__('cmux{}'.format(width))
        self.__width = width
        self.__width_sel = int(ceil(log(width, 2)))
        self.__ports = OrderedDict((
            ('i', PhysicalInputPort(self, name='i', width = width)),
            ('o', PhysicalOutputPort(self, name='o', width=1)),
            ('cfg_e', GlobalPhysicalInputPort(self, name='cfg_e', width=1)),
            ('cfg_d', PhysicalInputPort(self, name='cfg_d', width=self.__width_sel)),
            ))

    @property
    def _ports(self):
        return DictDelegate(self.__ports)

    @property
    def width(self):
        """Number of inputs of this configurable mux."""
        return self.__width

    @property
    def width_sel(self):
        """Width of the 'sel' port of this mux."""
        return self.__width_sel

    @property
    def switch_type(self):
        return SwitchType.mux

    @property
    def inputs(self):
        return self.__ports['i']

    @property
    def output(self):
        return self.__ports['o'][0]

    @property
    def _fixed_ext(self):
        return {"verilog_template": "cmux.builtin.tmpl.v"}
