# -*- enconding: ascii -*-

"""Abstract base classes for all instances."""

__all__ = ['LogicalInstance', 'PhysicalInstance', 'Instance']

import logging
_logger = logging.getLogger(__name__)

from common import AbstractModuleOrInstance
from ..portpin.port import Pin
from ...exception import PRGAInternalError, PRGAAPIError
from ..._util.util import DictProxy

from abc import abstractmethod, abstractproperty
from collections import OrderedDict

# ----------------------------------------------------------------------------
# -- AbstractInstance --------------------------------------------------------
# ----------------------------------------------------------------------------
class AbstractInstance(AbstractModuleOrInstance):
    """Abstract base class for instances.
    
    Args:
        model (`AbstractLeafModule` or `AbstractNonLeafModule`-subclass): the model to be instantiated
    """

    def __init__(self, model):
        super(AbstractInstance, self).__init__()
        self.__model = model

    # -- internal API --------------------------------------------------------
    @abstractproperty
    def _pins(self):
        """A mapping from name to pins."""
        raise NotImplementedError

    # -- exposed API ---------------------------------------------------------
    @property
    def model(self):
        """The module that this instance instantiates."""
        return self.__model

    @property
    def type(self):
        """The type of this module."""
        return self.__model.type

    @property
    def switch_type(self):
        """The type of this switch. Only valid if this is indeed an instance of a switch."""
        return self.__model.switch_type

    @property
    def block_type(self):
        """The type of this block. Only valid if this is indeed an instance of a block."""
        return self.__model.block_type

    @property
    def pins(self):
        """`DictProxy`: A mapping from name to logical pins.

        Raises:
            `PRGAAPIError`: if this instance is not a logical instance.
        
        This :obj:`property` only works after linking.
        """
        if not self.is_logical:
            raise PRGAAPIError("'{}' is not a logical instance".format(self))
        return DictProxy(self._pins, lambda (_, pin): pin.is_logical)

    @property
    def _physical_pins(self):
        """`DictProxy`: A mapping from name to physical pins.

        Raises:
            `PRGAAPIError`: if this instance is not a physical instance.
        
        This :obj:`property` only works after linking.
        """
        if not self.is_physical:
            raise PRGAAPIError("'{}' is not a physical instance".format(self))
        return DictProxy(self._pins, lambda (_, pin): pin.is_physical)

# ----------------------------------------------------------------------------
# -- _AbstractLeafInstance ---------------------------------------------------
# ----------------------------------------------------------------------------
class _AbstractLeafInstance(AbstractInstance):
    """Base class for all leaf-level instances in logic/io blocks.
    
    Args:
        model (`AbstractLeafModule` or `AbstractNonLeafModule`-subclass): the model to be instantiated
        name (:obj:`str`): name of the instance
    """

    def __init__(self, model, name):
        super(_AbstractLeafInstance, self).__init__(model)
        self.__name = name

    @property
    def name(self):
        """Name of this instance."""
        return self.__name

    @property
    def is_logical(self):
        """Test if this is a logical instance."""
        return False

    @property
    def is_physical(self):
        """Test if this is a physical instance."""
        return False

# ----------------------------------------------------------------------------
# -- LogicalInstance ---------------------------------------------------------
# ----------------------------------------------------------------------------
class LogicalInstance(_AbstractLeafInstance):
    """Basic type of logical instance.
    
    Args:
        model (`AbstractLeafModule` or `AbstractNonLeafModule`-subclass): the model to be instantiated
        name (:obj:`str`): name of the instance
    """

    def __init__(self, model, name):
        if not model.is_logical:
            raise PRGAAPIError("Model '{}' is not a logical model".format(model.name))
        super(LogicalInstance, self).__init__(model, name)
        self.__pins = OrderedDict((name, Pin(self, port)) for name, port in model.ports.iteritems())

    # -- derived properties --------------------------------------------------
    @property
    def is_logical(self):
        """Test if this is a logical instance."""
        return True

    # -- internal properties -------------------------------------------------
    @property
    def _pins(self):
        """A mapping from name to pins."""
        return self.__pins

# ----------------------------------------------------------------------------
# -- PhysicalInstance --------------------------------------------------------
# ----------------------------------------------------------------------------
class PhysicalInstance(_AbstractLeafInstance):
    """Basic type of logical instance.
    
    Args:
        model (`AbstractLeafModule` or `AbstractNonLeafModule`-subclass): the model to be instantiated
        name (:obj:`str`): name of the instance
    """

    def __init__(self, model, name):
        if not model.is_physical:
            raise PRGAAPIError("Model '{}' is not a physical model".format(model.name))
        super(PhysicalInstance, self).__init__(model, name)
        self.__pins = OrderedDict((name, Pin(self, port)) for name, port in model._physical_ports.iteritems())

    # -- properties/methods to be overriden by subclasses --------------------
    @property
    def is_physical(self):
        """Test if this is a physical instance."""
        return True

    # -- internal properties -------------------------------------------------
    @property
    def _pins(self):
        """A mapping from name to pins."""
        return self.__pins

# ----------------------------------------------------------------------------
# -- Instance ----------------------------------------------------------------
# ----------------------------------------------------------------------------
class Instance(_AbstractLeafInstance):
    """Basic type of instance used in CLB/IOBs.

    Args:
        model (`AbstractLeafModule` or `AbstractNonLeafModule`-subclass): the model to be instantiated
        name (:obj:`str`): name of the instance
    """

    def __init__(self, model, name):
        if not model.is_physical or not model.is_logical:
            raise PRGAAPIError("Model '{}' is not both logical and physical".format(model.name))
        super(Instance, self).__init__(model, name)
        self.__pins = OrderedDict((name, Pin(self, port)) for name, port in model._ports.iteritems())

    # -- properties/methods to be overriden by subclasses --------------------
    @property
    def is_physical(self):
        """Test if this is a physical instance."""
        return True

    @property
    def is_logical(self):
        """Test if this is a logical instance."""
        return True

    # -- internal properties -------------------------------------------------
    @property
    def _pins(self):
        """A mapping from name to pins."""
        return self.__pins
