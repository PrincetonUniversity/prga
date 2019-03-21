# Python 2 and 3 compatible
from prga.compatible import *

from prga._archdef.common import NetType, PortDirection
from prga._archdef.portpin.bus import AbstractPortOrPinBus, PortOrPinBus

# ----------------------------------------------------------------------------
# -- Abstract Ports ----------------------------------------------------------
# ----------------------------------------------------------------------------
class AbstractPort(AbstractPortOrPinBus):
    """Abstract base class for input/output/clock ports.
    
    Args:
        parent (`AbstractLeafModule`-subclass): the module this port belongs to
    """
    def __init__(self, parent):
        super(AbstractPort, self).__init__()
        self._parent = parent

    # == low-level API =======================================================
    @property
    def type(self):
        """Type of this net."""
        return NetType.port

    @property
    def parent(self):
        """Parent module of this port."""
        return self._parent

    @property
    def is_source(self):
        """Test if this is a logical/physical source."""
        return self.is_input

    @property
    def is_sink(self):
        """Test if this is a logical/physical sink."""
        return self.is_output

    @property
    def is_external(self):
        """Test if this port is connected all the way to outside the top-level module."""
        return False

    @property
    def global_(self):
        """The global wire this port is connected to."""
        return None

    @property
    def is_global(self):
        """Test if this port is connected to a global wire."""
        return self.global_ is not None

class AbstractInputPort(AbstractPort):
    """Abstract base class for input ports.

    Args:
        parent (`AbstractLeafModule`-subclass): the module this port belongs to
        name (:obj:`str`): name of this port
        width (:obj:`int`): width of this port
    """
    def __init__(self, parent, name, width):
        super(AbstractInputPort, self).__init__(parent)
        self._name = name
        self._width = width

    # == low-level API =======================================================
    @property
    def name(self):
        """Name of this port."""
        return self._name

    @property
    def width(self):
        """Width of this port."""
        return self._width

    @property
    def direction(self):
        """Direction of this port."""
        return PortDirection.input

    @property
    def is_clock(self):
        """Test if this is a clock port."""
        return False

class AbstractOutputPort(AbstractPort):
    """Abstract base class for output ports.

    Args:
        parent (`AbstractLeafModule`-subclass): the module this port belongs to
        name (:obj:`str`): name of this port
        width (:obj:`int`): width of this port
    """
    def __init__(self, parent, name, width):
        super(AbstractOutputPort, self).__init__(parent)
        self._name = name
        self._width = width

    # == low-level API =======================================================
    @property
    def name(self):
        """Name of this port."""
        return self._name

    @property
    def width(self):
        """Width of this port."""
        return self._width

    @property
    def direction(self):
        """Direction of this port."""
        return PortDirection.output

    @property
    def is_clock(self):
        """Test if this is a clock port."""
        return False

class AbstractClockPort(AbstractPort):
    """Abstract base class for clock ports.

    Args:
        parent (`AbstractLeafModule`-subclass): the module this port belongs to
        name (:obj:`str`): name of this port
    """
    def __init__(self, parent, name):
        super(AbstractClockPort, self).__init__(parent)
        self._name = name

    # == low-level API =======================================================
    @property
    def name(self):
        """Name of this port."""
        return self._name

    @property
    def width(self):
        """Width of this port."""
        return 1

    @property
    def direction(self):
        """Direction of this port."""
        return PortDirection.input

    @property
    def is_clock(self):
        """Test if this is a clock port."""
        return True

# ----------------------------------------------------------------------------
# -- Physical Ports ----------------------------------------------------------
# ----------------------------------------------------------------------------
class PhysicalInputPort(AbstractInputPort, PortOrPinBus):
    """Physical-only input port.

    Args:
        parent (`AbstractLeafModule`-subclass): the module this port belongs to
        name (:obj:`str`): name of this port
        width (:obj:`int`): width of this port
    """
    @property
    def is_physical(self):
        return True

class PhysicalOutputPort(AbstractOutputPort, PortOrPinBus):
    """Physical-only output port.

    Args:
        parent (`AbstractLeafModule`-subclass): the module this port belongs to
        name (:obj:`str`): name of this port
        width (:obj:`int`): width of this port
    """
    @property
    def is_physical(self):
        return True

class ExternalPhysicalInputPort(PhysicalInputPort):
    """Physical-only external input port.

    Args:
        parent (`AbstractLeafModule`-subclass): the module this port belongs to
        name (:obj:`str`): name of this port
        width (:obj:`int`): width of this port
    """
    @property
    def is_external(self):
        """Test if this is an external port that is connected all the way to outside the top-level module."""
        return True

class ExternalPhysicalOutputPort(PhysicalOutputPort):
    """Physical-only external output port.

    Args:
        parent (`AbstractLeafModule`-subclass): the module this port belongs to
        name (:obj:`str`): name of this port
        width (:obj:`int`): width of this port
    """
    @property
    def is_external(self):
        """Test if this is an external port that is connected all the way to outside the top-level module."""
        return True

class GlobalPhysicalInputPort(PhysicalInputPort):
    """Physical-only global input port.

    Args:
        parent (`AbstractLeafModule`-subclass): the module this port belongs to
        name (:obj:`str`): name of this port
        width (:obj:`int`): width of this port
    """
    @property
    def global_(self):
        return self.name
