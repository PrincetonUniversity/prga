# -*- enconding: ascii -*-

"""Abstract base classes for all modules."""

__all__ = []

import logging
_logger = logging.getLogger(__name__)

from common import AbstractModuleOrInstance
from ..portpin.common import ConstNet
from ..portpin.port import PhysicalInputPort, PhysicalOutputPort
from ...exception import PRGAInternalError, PRGAAPIError
from ..._util.util import DictProxy, uno

from abc import abstractproperty
from collections import OrderedDict

# ----------------------------------------------------------------------------
# -- AbstractLeafModule ------------------------------------------------------
# ----------------------------------------------------------------------------
class AbstractLeafModule(AbstractModuleOrInstance):
    """Abstract leaf module with no sub-instances."""

    def __init__(self, context, name):
        super(AbstractLeafModule, self).__init__()
        self.__context = context
        self.__name = name

    # -- properties/methods to be overriden by subclasses --------------------
    @abstractproperty
    def _ports(self):
        """:obj:`abstractproperty`: A mapping from name to all ports."""
        raise NotImplementedError

    # -- abstract property implementation ------------------------------------
    @property
    def name(self):
        """Name of this module."""
        return self.__name

    @property
    def is_logical(self):
        """Test if this is a logical module."""
        return False

    @property
    def is_physical(self):
        """Test if this is a physical module."""
        return False

    # -- internal API --------------------------------------------------------
    @property
    def _context(self):
        """The `ArchitectureContext` this module belongs to."""
        return self.__context

    @property
    def _physical_ports(self):
        """`DictProxy`: A mapping from name to physical ports.
        
        Raises:
            `PRGAAPIError`: if this is not a physical module.
        """
        if not self.is_physical:
            raise PRGAAPIError("'{}' is not a physical module".format(self))
        return DictProxy(self._ports, lambda (_, port): port.is_physical)

    # -- exposed API --------------------------------------------------------
    @property
    def ports(self):
        """`DictProxy`: A mapping from name to logical ports.
        
        Raises:
            `PRGAAPIError`: if this is not a logical module.
        """
        if not self.is_logical:
            raise PRGAAPIError("'{}' is not a logical module".format(self))
        return DictProxy(self._ports, lambda (_, port): port.is_logical)

# ----------------------------------------------------------------------------
# -- MutableLeafModule -------------------------------------------------------
# ----------------------------------------------------------------------------
class MutableLeafModule(AbstractLeafModule):
    """Abstract leaf module that is edditable."""
    
    def __init__(self, context, name):
        super(MutableLeafModule, self).__init__(context, name)
        self.__ports = OrderedDict()

    # -- internal API --------------------------------------------------------
    @property
    def _ports(self):
        """A mapping from name to all ports."""
        return self.__ports

    def _add_port(self, port, force = False):
        """Add a port to this module.

        Args:
            port (``Port``):
            force (:obj:`bool`, default=False): force adding the port (overwrite any port with the same name)

        Raises:
            `PRGAInternalError`: if a port with the same name already exists, or a logical port is added to a physical
                module, or a physical port is added to a logical module
        """
        if port.parent_module is not self:
            raise PRGAInternalError("Module '{}' is not the parent module of port '{}'"
                    .format(self.name, port.name))
        elif not force and port.name in self._ports:
            raise PRGAInternalError("Module '{}' already has a port named '{}'"
                    .format(self.name, port.name))
        elif port.is_logical and not self.is_logical:
            raise PRGAInternalError("Logical port '{}' cannot be added to non-logical module '{}'"
                    .format(port.name, self.name))
        elif port.is_physical and not self.is_physical:
            raise PRGAInternalError("Physical port '{}' cannot be added to non-physical module '{}'"
                    .format(port.name, self.name))
        self._ports[port.name] = port

# ----------------------------------------------------------------------------
# -- AbstractNonLeafModule ---------------------------------------------------
# ----------------------------------------------------------------------------
class AbstractNonLeafModule(AbstractLeafModule):
    """Abstract module which may contain sub-instances."""

    # -- properties/methods to be overriden by subclasses --------------------
    @abstractproperty
    def _instances(self):
        """:obj:`abstractproperty`: A mapping from name to all instances."""
        raise NotImplementedError

    # -- internal API --------------------------------------------------------
    @property
    def _physical_instances(self):
        """`DictProxy`: A mapping from name to physical instances.
        
        Raises:
            `PRGAAPIError`: if this module is not a physical module.
        """
        if not self.is_physical:
            raise PRGAAPIError("'{}' is not a physical module".format(self))
        return DictProxy(self._instances, lambda (_, instance): instance.is_physical)

    # -- exposed API --------------------------------------------------------
    @property
    def instances(self):
        """`DictProxy`: A mapping from name to logical instances.
        
        Raises:
            `PRGAAPIError`: if this module is not a logical module.
        """
        if not self.is_logical:
            raise PRGAAPIError("'{}' is not a logical module".format(self))
        return DictProxy(self._instances, lambda (_, instance): instance.is_logical)

# ----------------------------------------------------------------------------
# -- MutableNonLeafModule ----------------------------------------------------
# ----------------------------------------------------------------------------
class MutableNonLeafModule(AbstractNonLeafModule, MutableLeafModule):
    """Abstract module that is edditable."""

    def __init__(self, context, name):
        super(MutableNonLeafModule, self).__init__(context, name)
        self.__instances = OrderedDict()

    # -- internal API --------------------------------------------------------
    @property
    def _instances(self):
        """A mapping from name to all instances."""
        return self.__instances

    def _add_instance(self, instance, force = False):
        """Add a sub-instance to this module.

        Args:
            instance (``Instance``):
            force (:obj:`bool`, default=False): force adding the instance (overwrite any instance with the same name)

        Raises:
            `PRGAInternalError`: if an instance with the same name already exists, or a logical instance is added to a
                non-logical module, or a physical instance is added to a non-physical module
        """
        if not force and instance.name in self._instances:
            raise PRGAInternalError("Module '{}' already has a sub-instance named '{}'"
                    .format(self.name, instance.name))
        elif instance.is_logical and not self.is_logical:
            raise PRGAInternalError("Logical instance '{}' cannot be added to non-logical module '{}'"
                    .format(instance.name, self.name))
        elif instance.is_physical and not self.is_physical:
            raise PRGAInternalError("Physical instance '{}' cannot be added to non-physical module '{}'"
                    .format(instance.name, self.name))
        self._instances[instance.name] = instance
