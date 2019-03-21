# Python 2 and 3 compatible
from prga.compatible import *

from prga._archdef.moduleinstance.common import AbstractModuleOrInstance
from prga._archdef.portpin.port import (PhysicalInputPort, PhysicalOutputPort,
        ExternalPhysicalInputPort, ExternalPhysicalOutputPort, GlobalPhysicalInputPort)
from prga._util.util import DictDelegate, uno
from prga.exception import PRGAInternalError, PRGAAPIError

from abc import abstractproperty
from collections import OrderedDict

# ----------------------------------------------------------------------------
# -- AbstractLeafModule ------------------------------------------------------
# ----------------------------------------------------------------------------
class AbstractLeafModule(AbstractModuleOrInstance):
    """Abstract leaf module with no sub-instances.

    Args:
        name (:obj:`str`): name of this module
    """
    def __init__(self, name):
        super(AbstractLeafModule, self).__init__()
        self._name = name

    # == internal methods ====================================================
    # -- properties/methods to be overriden by subclasses --------------------
    @abstractproperty
    def _ports(self):
        """A mapping from port keys (could be names, routing node references) to all ports."""
        raise NotImplementedError

    # == low-level API =======================================================
    # -- abstract property implementation ------------------------------------
    @property
    def name(self):
        """Name of the module."""
        return self._name

    # -- internal API --------------------------------------------------------
    @property
    def physical_ports(self):
        """`DictDelegate`: A mapping from port keys to physical ports.
        
        Raises:
            `PRGAAPIError`: if this is not a physical module.
        """
        if not self.is_physical:
            raise PRGAAPIError("'{}' is not a physical module".format(self))
        return DictDelegate(self._ports, lambda kv: kv[1].is_physical)

    # == high-level API ======================================================
    @property
    def ports(self):
        """`DictDelegate`: A mapping from port keys to logical ports.
        
        Raises:
            `PRGAAPIError`: if this is not a logical module.
        """
        if not self.is_logical:
            raise PRGAAPIError("'{}' is not a logical module".format(self))
        return DictDelegate(self._ports, lambda kv: kv[1].is_logical)

    def __str__(self):
        return self._name

# ----------------------------------------------------------------------------
# -- MutableLeafModule -------------------------------------------------------
# ----------------------------------------------------------------------------
class MutableLeafModule(AbstractLeafModule):
    """Abstract leaf module that is edditable.

    Args:
        name (:obj:`str`): name of this module
    """

    def __init__(self, name):
        super(MutableLeafModule, self).__init__(name)
        self.__ports = OrderedDict()

    # == internal methods ====================================================
    @property
    def _ports(self):
        """A mapping from port keys to all ports."""
        return self.__ports

    @_ports.setter
    def _ports(self, v):
        self.__ports = v

    # == low-level API =======================================================
    def add_port(self, port, force = False):
        """Add a port to this module.

        Args:
            port (`AbstractPort`-subclass):
            force (:obj:`bool`): force adding the port (overwrite any port with the same key)

        Raises:
            `PRGAInternalError`: if a port with the same key already exists, or a logical port is added to a
                non-logical module, or a physical port is added to a non-physical module
        """
        if port.parent is not self:
            raise PRGAInternalError("Module '{}' is not the parent module of port '{}'".format(self, port))
        elif not force and port.key in self._ports:
            raise PRGAInternalError("Module '{}' already has a port with key '{}'".format(self, port.key))
        elif port.is_logical and not self.is_logical:
            raise PRGAInternalError("Logical port '{}' cannot be added to non-logical module '{}'"
                    .format(port, self))
        elif port.is_physical and not self.is_physical:
            raise PRGAInternalError("Physical port '{}' cannot be added to non-physical module '{}'"
                    .format(port, self))
        self._ports[port.key] = port

    def get_or_create_physical_input(self, name, width, is_external = False, is_global = False):
        """Get or create physical input port with the given name & width.

        Args:
            name (:obj:`str`):
            width (:obj:`int`):
            is_external (:obj:`bool`):
            is_global (:obj:`bool`):

        Returns:
            `PhysicalInputPort`:

        Raises:
            `PRGAInternalError`: if a port with the given name already exists but the type/direction does not match
        """
        if not self.is_physical:
            raise PRGAInternalError("Module '{}' is not physical".format(self))
        port = self._ports.get(name, None)
        if port is not None:
            if not (port.is_input and port.is_physical and port.width == width and port.is_external == is_external and
                    port.is_global == is_global):
                raise PRGAInternalError("Port '{}' is not {} {}-bit physical input"
                        .format(port, 'an external' if is_external else 'a global' if is_global else 'a', width))
        else:
            PortCls = (ExternalPhysicalInputPort if is_external else GlobalPhysicalInputPort if is_global else
                    PhysicalInputPort)
            port = self._ports[name] = PortCls(self, name, width)
        return port

    def get_or_create_physical_output(self, name, width, is_external = False):
        """Get or create physical output port with the given name & width.

        Args:
            name (:obj:`str`):
            width (:obj:`int`):
            is_external (:obj:`bool`):

        Returns:
            `PhysicalOutputPort`:

        Raises:
            `PRGAInternalError`: if a port with the given name already exists but the type/direction does not match
        """
        if not self.is_physical:
            raise PRGAInternalError("Module '{}' is not physical".format(self))
        port = self._ports.get(name, None)
        if port is not None:
            if not (port.is_output and port.is_physical and port.width == width and port.is_external == is_external):
                raise PRGAInternalError("Port '{}' is not {} {}-bit physical output"
                        .format(port, 'an external' if is_external else 'a', width))
        else:
            PortCls = ExternalPhysicalOutputPort if is_external else PhysicalOutputPort
            port = self._ports[name] = PortCls(self, name, width)
        return port

# ----------------------------------------------------------------------------
# -- AbstractNonLeafModule ---------------------------------------------------
# ----------------------------------------------------------------------------
class AbstractNonLeafModule(AbstractLeafModule):
    """Abstract module which may contain sub-instances.

    Args:
        name (:obj:`str`): name of this module
    """
    # == internal methods ====================================================
    # -- properties/methods to be overriden by subclasses --------------------
    @abstractproperty
    def _instances(self):
        """A mapping from instance keys to all instances."""
        raise NotImplementedError

    # == low-level API =======================================================
    @property
    def physical_instances(self):
        """`DictDelegate`: A mapping from instance keys (could be names, subblock-ids) to physical instances.

        Raises:
            `PRGAAPIError`: if this module is not a physical module
        """
        if not self.is_physical:
            raise PRGAAPIError("'{}' is not a physical module".format(self))
        return DictDelegate(self._instances, lambda kv: kv[1].is_physical)

    # == high-level API ======================================================
    @property
    def instances(self):
        """`DictDelegate`: A mapping from instance keys to logical instances.
        
        Raises:
            `PRGAAPIError`: if this is not a logical module.
        """
        if not self.is_logical:
            raise PRGAAPIError("'{}' is not a logical module".format(self))
        return DictDelegate(self._instances, lambda kv: kv[1].is_logical)

# ----------------------------------------------------------------------------
# -- MutableNonLeafModule ----------------------------------------------------
# ----------------------------------------------------------------------------
class MutableNonLeafModule(AbstractNonLeafModule):
    """Abstract module that is edditable.

    Args:
        name (:obj:`str`): name of this module
    """

    def __init__(self, name):
        super(MutableNonLeafModule, self).__init__(name)
        self.__instances = OrderedDict()

    # == internal methods ====================================================
    @property
    def _instances(self):
        """A mapping from instance keys to all instances."""
        return self.__instances

    @_instances.setter
    def _instances(self, v):
        self.__instances = v

    # == low-level API =======================================================
    def add_instance_raw(self, instance, force = False):
        """Add a sub-instance to this module.

        Args:
            instance (`Instance`):
            force (:obj:`bool`): force adding the instance (overwrite any instance with the same key)

        Raises:
            `PRGAInternalError`: if an instance with the same key already exists, or a logical instance is added to a
                non-logical module, or a physical instance is added to a non-physical module
        """
        if instance.parent is not self:
            raise PRGAInternalError("Module '{}' is not the parent module of instance '{}'".format(self, instance))
        elif not force and instance.key in self._instances:
            raise PRGAInternalError("Module '{}' already has a sub-instance with key '{}'".format(self, instance.key))
        elif instance.is_logical and not self.is_logical:
            raise PRGAInternalError("Logical instance '{}' cannot be added to non-logical module '{}'"
                    .format(instance, self))
        elif instance.is_physical and not self.is_physical:
            raise PRGAInternalError("Physical instance '{}' cannot be added to non-physical module '{}'"
                    .format(instance, self))
        self._instances[instance.key] = instance

# ----------------------------------------------------------------------------
# -- LogicallyConnectableModule ----------------------------------------------
# ----------------------------------------------------------------------------
class LogicallyConnectableModule(MutableNonLeafModule):
    """Modules that support logical connections.

    Args:
        name (:obj:`str`): name of this module
    """

    def __init__(self, name):
        super(LogicallyConnectableModule, self).__init__(name)
        self._pack_patterns = []

    # == low-level API =======================================================
    @property
    def pack_patterns(self):
        """Logical connections marked as packed patterns."""
        return self._pack_patterns

    # == high-level API ======================================================
    def add_connections(self, sources, sinks, fully_connected = False, pack_pattern = False):
        """Add configurable connections between logical ports/pins inside the block.

        Args:
            sources: a bit, a list of bits, a port, a list of ports, etc.
            sinks: a bit, a list of bits, a port, a list of ports, etc.
            fully_connected (:obj:`bool`): by default, the connections are created in a bit-wise pairing manner. If
                set to ``True``, a full connection will be created between the ``sources`` and ``sinks``
            pack_pattern (:obj:`bool`): this is an advanced feature for VPR only. Set this to True will mark all
                created connections as `pack_pattern
                <http://docs.verilogtorouting.org/en/latest/arch/reference/#tag-interconnect-pack_pattern>`_

        Raises:
            `PRGAAPIError`: if not fully connected and the number of source bits and the number of sink bits don't
                match, or any of the sources is not a logical source, or any of the sinks is not a logical sink

        Examples:
            >>> block = ... # assume a block is created somehow
            # set up ports & instances
            >>> block.add_input("A", 8, Side.left)
            >>> block.add_input("AX", 1, Side.left)
            >>> block.add_output("O", 2, Side.right)
            >>> block.add_output("OX", 1, Side.right)
            >>> block.add_clock("C", Side.bottom)
            >>> block.add_instance("lut_inst0", lut4)
            >>> block.add_instance("lut_inst1", lut4)
            >>> block.add_instance("ff_inst0", flipflop)
            >>> block.add_instance("ff_inst1", flipflop)
            >>> block.add_instance("mux_inst0", MUX2) # MUX2 is a user-defined mux
            # add connections by port/pin
            >>> block.add_connections(block.instances['mux_inst0'].pins['out'], block.ports['OX'])
            # add connections by bits
            >>> block.add_connections(block.ports['AX'], block.instances['mux_inst0'].pins['sel'][0])
            # use fully_connected
            >>> block.add_connections(block.ports['C'],
                    [block.instances['ff_inst0'].pins['c'], block.instances['ff_inst1'].pins['c']],
                    fully_connected = True)
            # add connections by mixing port slices, lists and non-lists
            >>> block.add_connections(block.ports['A'][0:3], block.instances['lut_inst0'].pins['i'])
            >>> block.add_connections(block.ports['A'][4:7], block.instances['lut_inst1'].pins['i'])
            >>> block.add_connections(
                    [block.instances['lut_inst0'].pins['o'], block.instances['lut_inst1'].pins['o']],
                    block.instances['mux_inst0'].pins['i'])
            # use pack_pattern
            >>> block.add_connections(
                    [block.instances['lut_inst0'].pins['o'], block.instances['lut_inst1'].pins['o']],
                    [block.instances['ff_inst0'].pins['d'], block.instances['ff_inst0'].pins['d']],
                    pack_pattern = True)
            # add multiple connections to the same port/pin will cause a programmable mux to be created later
            >>> block.add_connections(
                    [block.instances['lut_inst0'].pins['o'], block.instances['lut_inst1'].pins['o']],
                    block.ports['O'])
            >>> block.add_connections(
                    [block.instances['ff_inst0'].pins['q'], block.instances['ff_inst1'].pins['q']],
                    block.ports['O'])
        """
        # 1. create the list of sources
        sources_ = []
        try:
            for src in sources:
                try:
                    for s in src:
                        sources_.append(s.get_static_cp(True))
                except TypeError:
                    sources_.append(src.get_static_cp(True))
        except TypeError:
            sources_.append(sources.get_static_cp(True))
        for source in sources_:
            if not source.is_logical_source:
                raise PRGAAPIError("'{}' is not a logical source".format(source))
        # 2. create the list of sinks
        sinks_ = []
        try:
            for sink in sinks:
                try:
                    for s in sink:
                        sinks_.append(s.get_static_cp(True))
                except TypeError:
                    sinks_.append(sink.get_static_cp(True))
        except TypeError:
            sinks_.append(sinks.get_static_cp(True))
        for sink in sinks_:
            if not sink.is_logical_sink:
                raise PRGAAPIError("'{}' is not a logical sink".format(sink))
        # 3. create the actual connections
        if fully_connected:
            for sink in sinks_:
                sink.add_logical_sources(sources_)
                if pack_pattern:
                    for source in sources_:
                        self._pack_patterns.append( (source.get_static_cp(True), sink.get_static_cp(True)) )
        else:
            if len(sources_) != len(sinks_):
                raise PRGAAPIError("The number of source bits ({}) does not match with the number of sink bits ({})"
                        .format(len(sources_), len(sinks_)))
            for source, sink in zip(iter(sources_), iter(sinks_)):
                sink.add_logical_sources(source)
                if pack_pattern:
                    self._pack_patterns.append( (source.get_static_cp(True), sink.get_static_cp(True)) )
