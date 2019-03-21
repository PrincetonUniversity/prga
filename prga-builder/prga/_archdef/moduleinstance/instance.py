# Python 2 and 3 compatible
from prga.compatible import *

__all__ = ['PhysicalInstance', 'LogicalInstance', 'Instance']

from prga._archdef.moduleinstance.common import AbstractModuleOrInstance
from prga._archdef.portpin.pin import Pin, DynamicPin
from prga._util.util import DictDelegate, uno
from prga.exception import PRGAInternalError, PRGAAPIError

from abc import abstractproperty

# ----------------------------------------------------------------------------
# -- Instance Pins Delegate --------------------------------------------------
# ----------------------------------------------------------------------------
class PinsDelegate(Mapping):
    """A helper class for `AbstractInstance._pins` property."""
    def __init__(self, instance):
        self.__instance = instance

    def __getitem__(self, key):
        try:
            return self.__instance._static_pins.get(key,
                    self.__instance._create_dynamic_pin(self.__instance._model_ports[key]))
        except KeyError:
            raise KeyError(key)

    def __iter__(self):
        return iter(self.__instance._model_ports)

    def __len__(self):
        return len(self.__instance._model_ports)

# ----------------------------------------------------------------------------
# -- AbstractInstance --------------------------------------------------------
# ----------------------------------------------------------------------------
class AbstractInstance(AbstractModuleOrInstance):
    """Abstract base class for instances.
    
    Args:
        parent (`AbstractNonLeafModule`-subclass): the module this instance belongs to
        model (`AbstractLeafModule`-subclass): the module to be instantiated
        name (:obj:`str`): the name of the instance
    """
    def __init__(self, parent, model):
        super(AbstractInstance, self).__init__()
        self._parent = parent
        self._model = model
        self._static_pins = {}

    # == internal methods ====================================================
    # -- properties/methods to be overriden by subclasses --------------------
    @abstractproperty
    def _model_ports(self):
        """The ports in the module that this instance instantiates."""
        raise NotImplementedError

    def _create_static_pin(self, port):
        """Create a static pin for ``port``."""
        return Pin(self, port)

    def _create_dynamic_pin(self, port):
        """Create a dynamic pin for ``port``."""
        return DynamicPin(self, port)

    # -- internal API --------------------------------------------------------
    @property
    def _pins(self):
        """A mapping from pin names to all pins."""
        return PinsDelegate(self)

    # == low-level API =======================================================
    @property
    def key(self):
        """Key of this instance in the mapping of the parent."""
        return self.name

    def get_or_create_static_pin(self, port):
        """Get or create a static pin for ``port``."""
        return self._static_pins.setdefault(port.key, self._create_static_pin(port))

    # -- abstract property implementation ------------------------------------
    @property
    def physical_pins(self):
        """`DictDelegate`: a mapping from pin names to physical pins."""
        if not self.is_physical:
            raise PRGAAPIError("'{}' is not a physical instance".format(self))
        return DictDelegate(self._pins, lambda kv: kv[1].is_physical)

    # == high-level API ======================================================
    @property
    def parent(self):
        """The parent module this instance belongs to."""
        return self._parent

    @property
    def model(self):
        """The module that this instance instantiates."""
        return self._model

    @property
    def type(self):
        """Type of this instance."""
        return self._model.type

    @property
    def primitive_type(self):
        """Type of this primitive (if it is a primitive)."""
        return self._model.primitive_type

    @property
    def switch_type(self):
        """Type of this switch (if it is a switch)."""
        return self._model.switch_type

    @property
    def block_type(self):
        """Type of this block (if it is a block)."""
        return self._model.block_type

    @property
    def pins(self):
        """`DictDelegate`: a mapping from pin names to logical pins."""
        if not self.is_logical:
            raise PRGAAPIError("'{}' is not a logical instance".format(self))
        return DictDelegate(self._pins, lambda kv: kv[1].is_logical)

    def __str__(self):
        return '{}/{}'.format(self._parent, self.name)

# ----------------------------------------------------------------------------
# -- PhysicalInstance --------------------------------------------------------
# ----------------------------------------------------------------------------
class PhysicalInstance(AbstractInstance):
    """A physical-only instance.
    
    Args:
        parent (`AbstractNonLeafModule`-subclass): the module this instance belongs to
        model (`AbstractLeafModule`-subclass): the model to be instantiated
        name (:obj:`str`): the name of the instance
    """
    def __init__(self, parent, model, name):
        if not model.is_physical:
            raise PRGAInternalError("'{}' is not a physical module".format(model))
        super(PhysicalInstance, self).__init__(parent, model)
        self._name = name

    @property
    def _model_ports(self):
        return self.model.physical_ports

    @property
    def name(self):
        """Name of this instance."""
        return self._name

    @property
    def is_physical(self):
        return True

# ----------------------------------------------------------------------------
# -- LogicalInstance --------------------------------------------------------
# ----------------------------------------------------------------------------
class LogicalInstance(AbstractInstance):
    """A logical-only instance.

    Args:
        parent (`AbstractNonLeafModule`-subclass): the module this instance belongs to
        model (`AbstractLeafModule`-subclass): the model to be instantiated
        name (:obj:`str`): the name of the instance
    """
    def __init__(self, parent, model, name):
        if not model.is_logical:
            raise PRGAInternalError("'{}' is not a logical module".format(model))
        super(LogicalInstance, self).__init__(parent, model)
        self._name = name

    @property
    def _model_ports(self):
        return self.model.ports

    @property
    def name(self):
        """Name of this instance."""
        return self._name

    @property
    def is_logical(self):
        return True

# ----------------------------------------------------------------------------
# -- Instance ----------------------------------------------------------------
# ----------------------------------------------------------------------------
class Instance(AbstractInstance):
    """A logical and physical instance.

    Args:
        parent (`AbstractNonLeafModule`-subclass): the module this instance belongs to
        model (`AbstractLeafModule`-subclass): the model to be instantiated
        name (:obj:`str`): the name of the instance
    """
    def __init__(self, parent, model, name):
        if not model.is_logical or not model.is_physical:
            raise PRGAInternalError("'{}' is not a logical & physical module".format(model))
        super(Instance, self).__init__(parent, model)
        self._name = name

    @property
    def _model_ports(self):
        return self.model._ports

    @property
    def name(self):
        """Name of this instance."""
        return self._name

    @property
    def is_logical(self):
        return True

    @property
    def is_physical(self):
        return True
