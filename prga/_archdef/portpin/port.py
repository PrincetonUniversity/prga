# -*- enconding: ascii -*-

"""Abstract base classes for ports and pins."""

__all__ = ['PhysicalInputPort', 'PhysicalOutputPort', 'Pin']

import logging
_logger = logging.getLogger(__name__)

from common import AbstractNet, ConstNet
from reference import NetReference
from ..common import NetType, PortDirection
from ...exception import PRGAInternalError
from ..._util.util import uno

from itertools import izip
from abc import abstractproperty, abstractmethod
from collections import Sequence

# ----------------------------------------------------------------------------
# -- Abstract Port/Pin -------------------------------------------------------
# ----------------------------------------------------------------------------
class _AbstractPortOrPin(AbstractNet):
    """Abstract base class defining a few test properties"""

    # -- properties/methods to be overriden by subclasses --------------------
    @abstractproperty
    def direction(self):
        """:obj:`abstractproperty`: Direction of this port/pin."""
        raise NotImplementedError

    @abstractproperty
    def is_clock(self):
        """:obj:`abstractproperty`: Test if this port/pin is a clock."""
        raise NotImplementedError

    @abstractproperty
    def name(self):
        """:obj:`abstractproperty`: Name of this port/pin."""
        raise NotImplementedError

    @property
    def is_logical(self):
        """Test if this port/pin is a logical port/pin."""
        return False

    @property
    def is_physical(self):
        """Test if this port/pin is a physical port/pin."""
        return False

    @property
    def is_source(self):
        """Test if this port/pin is a logical and/or physical source."""
        return False

    @property
    def is_sink(self):
        """Test if this port/pin is a logical and/or physical sink."""
        return False

    # -- derived test properties ---------------------------------------------
    @property
    def is_input(self):
        """Test if this port/pin is input."""
        return self.direction is PortDirection.input

    @property
    def is_output(self):
        """Test if this port/pin is output."""
        return self.direction is PortDirection.output

    @property
    def is_inout(self):
        """Test if this port/pin is inout."""
        return self.direction is PortDirection.inout

    @property
    def is_logical_source(self):
        """Test if this port/pin can be a logical source."""
        return self.is_logical and self.is_source

    @property
    def is_logical_sink(self):
        """Test if this port/pin can be a logical sink."""
        return self.is_logical and self.is_sink

    @property
    def is_physical_source(self):
        """Test if this port/pin can be a physical source."""
        return self.is_physical and self.is_source

    @property
    def is_physical_sink(self):
        """Test if this port/pin can be a physical sink."""
        return self.is_physical and self.is_sink

# ----------------------------------------------------------------------------
# -- Port/Pin bit ------------------------------------------------------------
# ----------------------------------------------------------------------------
class PortOrPinBit(_AbstractPortOrPin):
    """A single bit of a port/pin.

    Args:
        parent (port/pin): the port/pin this bit belongs to
        index (:obj:`int`): which bit this is in the port/pin

    DO NOT INSTANTIATE THIS CLASS. This is intended for internal use only.
    """
    
    def __init__(self, parent, index):
        super(PortOrPinBit, self).__init__()
        self.__parent = parent
        if parent.is_physical_sink:
            self.__physical_source = ConstNet(NetType.open)
        if parent.is_logical_sink:
            self.__logical_sources = []
        self.__index = index

    # -- internal API --------------------------------------------------------
    @property
    def _physical_cp(self):
        """The physical counterpart of this bit if this bit is non physical, or a redirect is needed in some cases."""
        try:
            return self.__physical_cp
        except AttributeError:
            if self.is_physical:
                return self
            else:
                return None

    @_physical_cp.setter
    def _physical_cp(self, cp):
        if cp is self:
            try:
                del self.__physical_cp
            except AttributeError:
                pass
        else:
            if not cp.is_physical:
                raise PRGAInternalError("'{}' is not physical"
                        .format(cp))
            self.__physical_cp = cp

    @_physical_cp.deleter
    def _physical_cp(self):
        try:
            del self.__physical_cp
        except AttributeError:
            pass

    @property
    def _logical_cp(self):
        """The logical counterpart of this bit if this bit is non logical, or a redirect is needed in some cases."""
        try:
            return self.__logical_cp
        except AttributeError:
            if self.is_logical:
                return self
            else:
                return None

    @_logical_cp.setter
    def _logical_cp(self, cp):
        if cp is self:
            try:
                del self.__logical_cp
            except AttributeError:
                pass
        else:
            if not cp.is_logical:
                raise PRGAInternalError("'{}' is not logical"
                        .format(cp))
            self.__logical_cp = cp

    @_logical_cp.deleter
    def _logical_cp(self):
        try:
            del self.__logical_cp
        except AttributeError:
            pass

    @property
    def _physical_source(self):
        """Physical source of this bit.
        
        You can assign None or `ConstNet` or `PortOrPinBit` or :obj:`list` [`PortOrPinBit` ] or a physical source
        port to to this property. If :obj:`list` [`PortOrPinBit` ] or a physical source port is used, the number of
        bits must be 1.
        """
        if not self.is_physical_sink:
            raise PRGAInternalError("'{}' is not a physical sink".format(self))
        return self.__physical_source

    @_physical_source.setter
    def _physical_source(self, src):
        if not self.is_physical_sink:
            raise PRGAInternalError("'{}' is not a physical sink".format(self))
        if src is None:
            self.__physical_source = ConstNet(NetType.open)
        elif isinstance(src, Sequence):
            if len(src) != 1:
                raise PRGAInternalError("'{}' is not a valid physical source".format(src))
            else:
                self.__physical_source = src[0]
        elif src.is_open or src.is_const:
            self.__physical_source = ConstNet(src.type)
        elif src.is_physical_source:
            self.__physical_source = src
        else:
            raise PRGAInternalError("'{}' is not a valid physical source".format(src))

    @property
    def _logical_sources(self):
        """The logical sources of this logical sink."""
        return tuple(x for x in self.__logical_sources)

    def _add_logical_sources(self, src):
        """Add logical sources to this bit.

        Args:
            src (`PortOrPinBit` or :obj:`Sequence` [`PortOrPinBit` ] or a logical source ``Port``:
                the logical sources to be added

        Raises:
            `PRGAInternalError`: if ``src`` is not a valid logical source, or this bit is not a logical sink.
        """
        if not self.is_logical_sink:
            raise PRGAInternalError("'{}' is not a logical sink".format(self))
        try:
            it = iter(src)
        except TypeError:
            it = iter((src, ))
        for s in it:
            if not s.is_logical_source:
                raise PRGAInternalError("'{}' is not a logical source".format(s))
            if s not in self.__logical_sources:
                self.__logical_sources.append(s)

    def _remove_logical_sources(self, src = None):
        """Remove logical sources of this bit.

        Args:
            src (`PortOrPinBit` or :obj:`Sequence` [`PortOrPinBit` ] or a logical source ``Port``, default=
                None): the logical sources to be removed. If None is passed, all logic sources will be
                removed.
        """
        if not self.is_logical_sink:
            raise PRGAInternalError("'{}' is not a logical sink".format(self))
        if src is None:
            self.__logical_sources = []
            return
        try:
            it = iter(src)
        except TypeError:
            it = iter((src, ))
        for s in it:
            try:
                self.__logical_sources.remove(s)
            except KeyError:
                pass

    def _set_source(self, src):
        """Set both the physical source and logical source to this bit.

        Args:
            src (physical & logical source):

        Raises:
            `PRGAInternalError`: if ``src`` is not a valid physical & logical source, or this bit is not a physical &
                logical sink.
        """
        if not (self.is_physical_sink and self.is_logical_sink):
            raise PRGAInternalError("'{}' is not a physical & logical sink".format(src))
        if isinstance(src, Sequence):
            if len(src) == 1:
                self.__logical_sources = [src[0]]
                self.__physical_source = src[0]
            else:
                raise PRGAInternalError("'{}' is not a valid physical & logical source".format(src))
        elif (src.is_port or src.is_pin) and src.is_logical_source and src.is_physical_source:
            self.__logical_sources = [src]
            self.__physical_source = src
        else:
            raise PRGAInternalError("'{}' is not a valid physical & logical source".format(src))

    # -- exposed API ---------------------------------------------------------
    @property
    def parent(self):
        """The port/pin this bit belongs to."""
        return self.__parent

    @property
    def type(self):
        """Type of this net."""
        return self.__parent.type

    @property
    def direction(self):
        """Direction of this port/pin."""
        return self.__parent.direction

    @property
    def is_clock(self):
        """Test if this port/pin is a clock."""
        return self.__parent.is_clock

    @property
    def parent_module(self):
        """The module this port belongs to."""
        return self.__parent.parent_module

    @property
    def parent_instance(self):
        """The instance this pin belongs to."""
        return self.__parent.parent_instance

    @property
    def is_logical(self):
        """Test if this port/pin is a logical port/pin."""
        return self.__parent.is_logical

    @property
    def is_physical(self):
        """Test if this port/pin is a physical port/pin."""
        return self.__parent.is_physical

    @property
    def is_source(self):
        """Test if this port/pin is a logical and/or physical source."""
        return self.__parent.is_source

    @property
    def is_sink(self):
        """Test if this port/pin is a logical and/or physical sink."""
        return self.__parent.is_sink

    @property
    def name(self):
        """Name of this bit."""
        return "{}[{}]".format(self.parent.name, self.index)

    @property
    def index(self):
        """Which bit this bit is in the port/pin."""
        return self.__index

    @property
    def is_bus(self):
        """Test if this is a multi-bit port/pin"""
        return False

    @property
    def reference(self):
        """A `NetReference` object refering to this bit."""
        return NetReference(self.type, self.parent_module.name if self.is_port else self.parent_instance.name,
                self.parent.name, self.index, self.index)

    def __str__(self):
        """Debug string."""
        return '{}[{}]'.format(self.parent, self.index)

# ----------------------------------------------------------------------------
# -- Abstract Port/Pin Bus ---------------------------------------------------
# ----------------------------------------------------------------------------
class AbstractPortOrPinBus(_AbstractPortOrPin, Sequence):
    """A multi-bit port/pin."""
    def __init__(self):
        self.__bits = tuple(PortOrPinBit(self, i) for i in xrange(self.width))

    # -- internal API --------------------------------------------------------
    @property
    def _physical_source(self):
        """A :obj:`Sequence` of bits that are the physical sources of the bits in this bus.

        You can assign None or `ConstNet` or `PortOrPinBit` or :obj:`Sequence` [`PortOrPinBit` ] or a physical source
        port to this bus. The number of bits must match the width of this bus.
        """
        return tuple(x._physical_source for x in self)

    @_physical_source.setter
    def _physical_source(self, src):
        if not self.is_physical_sink:
            raise PRGAInternalError("'{}' is not a physical sink".format(self))
        if src is None:
            for bit in self:
                bit._physical_source = None
        elif isinstance(src, Sequence):
            if len(src) != self.width:
                raise PRGAInternalError("'{}' is not a valid physical source".format(src))
            else:
                for b, s in izip(iter(self), iter(src)):
                    b._physical_source = s
        elif src.is_open or src.is_const:
            if self.width != 1:
                raise PRGAInternalError("'{}' is not a valid physical source".format(src))
            else:
                for b in self:
                    b._physical_source = ConstNet(src.type)
        elif src.is_physical_source:
            if self.width != 1:
                raise PRGAInternalError("'{}' is not a valid physical source".format(src))
            else:
                self[0]._physical_source = src
        else:
            raise PRGAInternalError("'{}' is not a valid physical source"
                    .format(src))

    def _add_logical_sources(self, src):
        """Add sources to every bit of this logical sink.

        Args:
            src (`PortOrPinBit` or :obj:`Sequence` [`PortOrPinBit` ] or a logical source ``Port``):
                the logical sources to be added

        Raises:
            `PRGAInternalError`: if ``src`` is not a valid logical source, or this port/pin is not a logical sink.
        """
        if not self.is_logical_sink:
            raise PRGAInternalError("'{}' is not a logical sink".format(self))
        for bit in self:
            bit._add_logical_sources(src)

    def _remove_logical_sources(self, src = None):
        """Remove sources from every bit of this logical sink.

        Args:
            src (`PortOrPinBit` or :obj:`Sequence` [`PortOrPinBit` ] or a logical source ``Port``, default=
                None): the logical sources to be removed. If None is passed, all logic sources will be
                removed.

        Raises:
            `PRGAInternalError`: if  this port/pin is not a logical sink.
        """
        if not self.is_logical_sink:
            raise PRGAInternalError("'{}' is not a logical sink".format(self))
        for bit in self:
            bit._remove_logical_sources(src)

    def _set_source(self, src):
        """Set both the physical source and logical source to this sink.

        Args:
            src (physical & logical source):

        Raises:
            `PRGAInternalError`: if ``src`` is not a valid physical & logical source, or this port/pin is not a
                physical & logical sink.
        """
        if not (self.is_physical_sink and self.is_logical_sink):
            raise PRGAInternalError("'{}' is not a physical & logical sink".format(src))
        if isinstance(src, Sequence):
            if len(src) == len(self):
                for bit, s in izip(iter(self), iter(src)):
                    bit._set_source(s)
            else:
                raise PRGAInternalError("'{}' is not a valid physical & logical source".format(src))
        elif (src.is_port or src.is_pin) and src.is_logical_source and src.is_physical_source and len(self) == 1:
            for bit in self:
                bit._set_source(src)
        else:
            raise PRGAInternalError("'{}' is not a valid physical & logical source"
                    .format(src))

    # -- exposed API ---------------------------------------------------------
    @abstractproperty
    def width(self):
        """:obj:`abstractproperty`: Width of this port/pin."""
        raise NotImplementedError

    @property
    def is_bus(self):
        """Test if this is a multi-bit port/pin"""
        return True

    @property
    def reference(self):
        """A `NetReference` object refering to this port/pin."""
        return NetReference(self.type, self.parent_module.name if self.is_port else self.parent_instance.name,
                self.name, 0, self.width - 1)

    def __len__(self):
        try:
            return len(self.__bits)
        except AttributeError:
            raise PRGAInternalError("Bits not created yet")

    def __getitem__(self, idx):
        try:
            return self.__bits[idx]
        except AttributeError:
            raise PRGAInternalError("Bits not created yet")

    def __str__(self):
        """Debug string."""
        return self.name

# ----------------------------------------------------------------------------
# -- Abstract Ports ----------------------------------------------------------
# ----------------------------------------------------------------------------
class AbstractInputPort(AbstractPortOrPinBus):
    """Base class for an input port.
    
    Args:
        module (`AbstractLeafModule` or `AbstractNonLeafModule`-subclass): the module this port belongs to
        name (:obj:`str`): name of this port
        width (:obj:`int`): width of this port
    """

    def __init__(self, module, name, width):
        self.__parent_module = module
        self.__name = name
        self.__width = width
        super(AbstractInputPort, self).__init__()

    @property
    def type(self):
        """Type of this net."""
        return NetType.port

    @property
    def direction(self):
        """Direction of this port/pin."""
        return PortDirection.input

    @property
    def is_clock(self):
        """Test if this port/pin is a clock."""
        return False

    @property
    def name(self):
        """Name of this port/pin."""
        return self.__name

    @property
    def parent_module(self):
        """The module this port/pin belongs to."""
        return self.__parent_module

    @property
    def width(self):
        """Width of this port/pin."""
        return self.__width

    @property
    def is_source(self):
        """Test if this port is a logical and/or physical source."""
        return True

class AbstractOutputPort(AbstractPortOrPinBus):
    """Base class for an output port.
    
    Args:
        name (:obj:`str`): name of this port
        width (:obj:`int`): width of this port
        module (`AbstractLeafModule` or `AbstractNonLeafModule`-subclass): the module this port belongs to
    """

    def __init__(self, module, name, width):
        self.__parent_module = module
        self.__name = name
        self.__width = width
        super(AbstractOutputPort, self).__init__()

    @property
    def type(self):
        """Type of this net."""
        return NetType.port

    @property
    def direction(self):
        """Direction of this port/pin."""
        return PortDirection.output

    @property
    def is_clock(self):
        """Test if this port/pin is a clock."""
        return False

    @property
    def name(self):
        """Name of this port/pin."""
        return self.__name

    @property
    def parent_module(self):
        """The module this port/pin belongs to."""
        return self.__parent_module

    @property
    def width(self):
        """Width of this port/pin."""
        return self.__width

    @property
    def is_sink(self):
        """Test if this port is a logical and/or physical sink."""
        return True

class AbstractClockPort(AbstractPortOrPinBus):
    """Base class for a clock port.
    
    Args:
        module (`AbstractLeafModule` or `AbstractNonLeafModule`-subclass): the module this port belongs to
        name (:obj:`str`): name of this port
    """

    def __init__(self, module, name):
        self.__parent_module = module
        self.__name = name
        super(AbstractClockPort, self).__init__()

    @property
    def type(self):
        """Type of this net."""
        return NetType.port

    @property
    def direction(self):
        """Direction of this port/pin."""
        return PortDirection.input

    @property
    def is_clock(self):
        """Test if this port/pin is a clock."""
        return True

    @property
    def name(self):
        """Name of this port/pin."""
        return self.__name

    @property
    def parent_module(self):
        """The module this port/pin belongs to."""
        return self.__parent_module

    @property
    def width(self):
        """Width of this port/pin."""
        return 1

    @property
    def is_source(self):
        """Test if this port is a logical and/or physical source."""
        return True

# ----------------------------------------------------------------------------
# -- Physical Ports ----------------------------------------------------------
# ----------------------------------------------------------------------------
class PhysicalInputPort(AbstractInputPort):
    """Physical-only input port.

    Args:
        module (`AbstractLeafModule`-subclass): the module this port belongs to
        name (:obj:`str`): name of this port
        width (:obj:`int`): width of this port
    """

    @property
    def is_physical(self):
        """Test if this is a physical port/pin."""
        return True

class PhysicalOutputPort(AbstractOutputPort):
    """Physical-only output port.

    Args:
        module (`AbstractLeafModule`-subclass): the module this port belongs to
        name (:obj:`str`): name of this port
        width (:obj:`int`): width of this port
    """

    @property
    def is_physical(self):
        """Test if this is a physical port/pin."""
        return True

# ----------------------------------------------------------------------------
# -- Pin ---------------------------------------------------------------------
# ----------------------------------------------------------------------------
class Pin(AbstractPortOrPinBus):
    """Base class for a pin.
    
    Args:
        instance (`LogicalInstance` or `PhysicalInstance`-subclass): the instance this pin belongs to
        port (``Port``): the port this pin linked to
    """

    def __init__(self, instance, port):
        self.__parent_instance = instance
        self.__port = port
        super(Pin, self).__init__()

    @property
    def type(self):
        """Type of this net."""
        return NetType.pin

    @property
    def port(self):
        """The port this pin links to."""
        return self.__port

    @property
    def name(self):
        """Name of this port/pin."""
        return self.__port.name

    @property
    def direction(self):
        """Direction of this port/pin."""
        return self.__port.direction

    @property
    def is_clock(self):
        """Test if this port/pin is a clock."""
        return self.__port.is_clock

    @property
    def width(self):
        """Width of this port/pin."""
        return self.__port.width

    @property
    def parent_instance(self):
        """The module this port/pin belongs to."""
        return self.__parent_instance

    @property
    def is_logical(self):
        """Test if this pin is a logical pin."""
        return self.__parent_instance.is_logical and self.__port.is_logical

    @property
    def is_physical(self):
        """Test if this pin is a physical pin."""
        return self.__parent_instance.is_physical and self.__port.is_physical

    @property
    def is_source(self):
        """Test if this pin is a logical and/or physical source."""
        return self.__port.is_sink

    @property
    def is_sink(self):
        """Test if this pin is a logical and/or physical sink."""
        return self.__port.is_source

    def __str__(self):
        """Debug string."""
        return '{}.{}'.format(self.parent_instance.name, self.name)
