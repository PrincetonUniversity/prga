# Python 2 and 3 compatible
from prga.compatible import *

__all__ = ['Pin', 'DynamicPin']

from prga._archdef.common import NetType
from prga._archdef.portpin.bus import AbstractPortOrPinBus, PortOrPinBus, DynamicPortOrPinBus

# ----------------------------------------------------------------------------
# -- Abstract Pin ------------------------------------------------------------
# ----------------------------------------------------------------------------
class AbstractPin(AbstractPortOrPinBus):
    """Abstract base class for pins of an instance.

    Args:
        parent (`AbstractInstance`-subclass): the instance this pin belongs to
        port (`AbstractPort`-subclass): the port in the module that the instance instantiates
    """
    def __init__(self, parent, port):
        super(AbstractPin, self).__init__()
        self._parent = parent
        self._port = port

    @property
    def _default_physical_source(self):
        if self._port.is_global:
            return self.parent.parent.physical_ports.get(self._port.global_,
                    super(AbstractPin, self)._default_physical_source)
        else:
            return super(AbstractPin, self)._default_physical_source

    # == low-level API =======================================================
    @property
    def type(self):
        """Type of this net."""
        return NetType.pin

    @property
    def name(self):
        """Name of this pin."""
        return self._port.name

    @property
    def parent(self):
        """Parent instance of this pin."""
        return self._parent

    @property
    def key(self):
        """Key of this pin in the mapping of the parent."""
        return self._port.key

    @property
    def direction(self):
        """Direction of this pin."""
        return self._port.direction

    @property
    def is_clock(self):
        """Test if this is a clock pin."""
        return self._port.is_clock

    @property
    def width(self):
        """Width of this pin."""
        return self._port.width

    @property
    def port(self):
        """The port in the module that the instance instantiates."""
        return self._port

    @property
    def is_physical(self):
        """Test if this is a physical pin."""
        return self._parent.is_physical and self._port.is_physical

    @property
    def is_logical(self):
        """Test if this is a logical pin."""
        return self._parent.is_logical and self._port.is_logical

    @property
    def is_source(self):
        """Test if this is a physical/logical source."""
        return self._port.is_sink

    @property
    def is_sink(self):
        """Test if this is a physical/logical sink."""
        return self._port.is_source

    @property
    def is_external(self):
        """Test if this pin is connected all the way to outside the top-level module."""
        return self._port.is_external

    @property
    def is_global(self):
        """Test if this port is connected to a global wire."""
        return self._port.is_global

    @property
    def global_(self):
        """The global wire this port is connected to."""
        return self._port.global_

# ----------------------------------------------------------------------------
# -- Pin ---------------------------------------------------------------------
# ----------------------------------------------------------------------------
class Pin(AbstractPin, PortOrPinBus):
    """Pin of an instance.

    Args:
        parent (`AbstractInstance`-subclass): the instance this pin belongs to
        port (`AbstractPort`-subclass): the port in the module that the instance instantiates
    """
    pass

# ----------------------------------------------------------------------------
# -- Dynamic Pin -------------------------------------------------------------
# ----------------------------------------------------------------------------
class DynamicPin(AbstractPin, DynamicPortOrPinBus):
    """A dynamic pin of an instance.

    Args:
        parent (`AbstractInstance`-subclass): the instance this pin belongs to
        port (`AbstractPort`-subclass): the port in the module that the instance instantiates
    """
    def get_static_cp(self, create = False):
        if create:
            return self.parent._static_pins.setdefault(self.key, self.parent._create_static_pin(self.port))
        else:
            return self.parent._static_pins.get(self.key, None)
