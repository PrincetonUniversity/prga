# -*- enconding: ascii -*-

"""Some common classes for nets."""

__all__ = ['ConstNet']

import logging
_logger = logging.getLogger(__name__)

from ..common import NetType, PortDirection
from ...exception import PRGAInternalError

from abc import ABCMeta, abstractproperty

# ----------------------------------------------------------------------------
# -- AbstractNet -------------------------------------------------------------
# ----------------------------------------------------------------------------
class AbstractNet(object):
    """Abstract base class defining a few test properties."""
    __metaclass__ = ABCMeta

    @abstractproperty
    def type(self):
        """:obj:`abstractproperty`: Type of this net."""
        raise NotImplementedError

    @property
    def is_open(self):
        """Test if this net is left unconnected."""
        return self.type is NetType.open

    @property
    def is_const(self):
        """Test if this net is tied to a constant value."""
        return self.type in (NetType.zero, NetType.one)

    @property
    def is_port(self):
        """Test if this net is a port."""
        return self.type is NetType.port

    @property
    def is_pin(self):
        """Test if this net is a pin."""
        return self.type is NetType.pin

# ----------------------------------------------------------------------------
# -- ConstNet ----------------------------------------------------------------
# ----------------------------------------------------------------------------
class ConstNet(AbstractNet):
    """A single-bit constant net.
    
    Args:
        type (`NetType`): the type of this constant net. Only `NetType.open`, `NetType.zero` and
            `NetType.one` are valid
    """
    __cache = {}
    def __new__(cls, type):
        return cls.__cache.setdefault(type, super(ConstNet, cls).__new__(cls, type))

    def __init__(self, type):
        self._type = type

    @property
    def type(self):
        """Type of this net."""
        return self._type

    @property
    def reference(self):
        """Return a reference to this net."""
        return ConstNetReference(self.type, 1)

    def __deepcopy__(self, memo):
        return self

    def __getnewargs__(self):
        return (self._type, )
