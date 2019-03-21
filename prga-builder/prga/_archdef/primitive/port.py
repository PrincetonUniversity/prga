# Python 2 and 3 compatible
from prga.compatible import *

from prga._archdef.common import PrimitivePortClass
from prga._archdef.portpin.bus import PortOrPinBus
from prga._archdef.portpin.port import AbstractInputPort, AbstractClockPort, AbstractOutputPort
from prga._util.util import uno
from prga.exception import PRGAInternalError

# ----------------------------------------------------------------------------
# -- Logical Primitive Ports -------------------------------------------------
# ----------------------------------------------------------------------------
class LogicalPrimitiveInputPort(AbstractInputPort, PortOrPinBus):
    """Logical primitive input port.

    Args:
        primitive (`AbstractLeafModule`-subclass): the primitive this port belongs to
        name (:obj:`str`): name of this port
        width (:obj:`int`): width of this port
        clock (:obj:`str`): name of the clock port if this port is a sequential endpoint
        port_class (`PrimitivePortClass`): [TODO: add explanation]
    """
    def __init__(self, primitive, name, width, clock = None, port_class = None):
        super(LogicalPrimitiveInputPort, self).__init__(primitive, name, width)
        self._clock = clock
        self._port_class = port_class

    @property
    def clock(self):
        """Name of the clock port if this is a sequential endpoint."""
        return self._clock

    @property
    def port_class(self):
        """The 'port_class' of this primitive port."""
        return self._port_class

    @property
    def is_logical(self):
        return True

class LogicalPrimitiveOutputPort(AbstractOutputPort, PortOrPinBus):
    """Logical primitive output port.

    Args:
        primitive (`AbstractLeafModule`-subclass): the primitive this port belongs to
        name (:obj:`str`): name of this port
        width (:obj:`int`): width of this port
        clock (:obj:`str`): name of the clock port if this port is a sequential startpoint/endpoint
        sources (:obj:`list` [:obj:`str` ]): names of the source ports of the combinational paths to this port
        port_class (`PrimitivePortClass`): [TODO: add explanation]
    """
    def __init__(self, primitive, name, width, clock = None, sources = None, port_class = None):
        super(LogicalPrimitiveOutputPort, self).__init__(primitive, name, width)
        self._clock = clock
        self._sources = uno(sources, tuple())
        self._port_class = port_class

    @property
    def clock(self):
        """Name of the clock port if this is a sequential startpoint/endpoint."""
        return self._clock

    @property
    def sources(self):
        """Names of the source ports of the combinational paths to this port."""
        return self._sources

    @property
    def port_class(self):
        """The 'port_class' of this primitive port."""
        return self._port_class

    @property
    def is_logical(self):
        return True

class LogicalPrimitiveClockPort(AbstractClockPort, PortOrPinBus):
    """Logical primitive clock port.

    Args:
        primitive (`AbstractLeafModule`-subclass): the primitive this port belongs to
        name (:obj:`str`): name of this port
        port_class (`PrimitivePortClass`): [TODO: add explanation]
    """
    def __init__(self, primitive, name, port_class = None):
        super(LogicalPrimitiveClockPort, self).__init__(primitive, name)
        self._port_class = port_class

    @property
    def port_class(self):
        """The 'port_class' of this primitive port."""
        return self._port_class

    @property
    def is_logical(self):
        return True

# ----------------------------------------------------------------------------
# -- Logical & Physical Primitive Ports --------------------------------------
# ----------------------------------------------------------------------------
class PrimitiveInputPort(LogicalPrimitiveInputPort):
    """Logical & physical primitive input port.

    Args:
        primitive (`AbstractLeafModule`-subclass): the primitive this port belongs to
        name (:obj:`str`): name of this port
        width (:obj:`int`): width of this port
        clock (:obj:`str`): name of the clock port if this port is a sequential endpoint
        port_class (`PrimitivePortClass`): [TODO: add explanation]
    """

    @property
    def is_physical(self):
        return True

class PrimitiveOutputPort(LogicalPrimitiveOutputPort):
    """Logical & physical primitive output port.

    Args:
        primitive (`AbstractLeafModule`-subclass): the primitive this port belongs to
        name (:obj:`str`): name of this port
        width (:obj:`int`): width of this port
        clock (:obj:`str`): name of the clock port if this port is a sequential startpoint/endpoint
        sources (:obj:`list` [:obj:`str` ]): names of the source ports of the combinational paths to this port
        port_class (`PrimitivePortClass`): [TODO: add explanation]
    """

    @property
    def is_physical(self):
        return True

class PrimitiveClockPort(LogicalPrimitiveClockPort):
    """Logical & physical primitive clock port.

    Args:
        primitive (`AbstractLeafModule`-subclass): the primitive this port belongs to
        name (:obj:`str`): name of this port
        port_class (`PrimitivePortClass`): [TODO: add explanation]
    """

    @property
    def is_physical(self):
        return True
