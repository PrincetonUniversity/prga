# Python 2 and 3 compatible
from prga.compatible import *

"""This module contains common classes for nets.

In PRGA, we only model ports & pins, and no wires are modeled, with the exemption of constant nets. 'Port' is the
connection point of a 'module'. 'Pin' is the connection point of a 'instance' and always corresponding to a 'port'
in the 'module' that the 'instance' instantiates.

A port/pin can be a 'source' or a 'sink'. As the names suggest, 'source's are the drivers while 'sink's are the
drivees in uni-directional connections. For example, an input port is a 'source'. However, an input pin is a 'sink'. A
physical 'sink' can only have one 'source', while a logical 'sink' may have multiple 'source's. All connections are
stored at the 'sink' side, that is, you can only track the 'source's of a 'sink', but not the other way around.
"""

__all__ = ['ConstNet', 'NetBundle']

from prga._archdef.common import NetType, PortDirection
from prga.exception import PRGAInternalError

from abc import ABCMeta, abstractproperty
from collections import namedtuple

# ----------------------------------------------------------------------------
# -- AbstractNet -------------------------------------------------------------
# ----------------------------------------------------------------------------
class AbstractNet(with_metaclass(ABCMeta, object)):
    """Abstract base class defining a few test properties."""

    # == low-level API =======================================================
    # -- properties/methods to be overriden by subclasses --------------------
    @abstractproperty
    def type(self):
        """Type of this net."""
        raise NotImplementedError

    # -- derived test properties ---------------------------------------------
    @property
    def is_open(self):
        """Test if this net is left unconnected."""
        return self.type is NetType.open

    @property
    def is_zero(self):
        """Test if this net is connected to constant zero."""
        return self.type is NetType.zero

    @property
    def is_one(self):
        """Test if this net is connected to constant one."""
        return self.type is NetType.one

    @property
    def is_const(self):
        """Test if this net is tied to a constant value."""
        return self.type in (NetType.open, NetType.zero, NetType.one)

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
        return cls.__cache.setdefault(type, super(ConstNet, cls).__new__(cls))

    def __init__(self, type):
        self.__type = type

    def __deepcopy__(self, memo):
        return self

    def __getnewargs__(self):
        return (self.__type, )

    @property
    def type(self):
        """Type of this net."""
        return self.__type

    @classmethod
    def Binarize(cls, value, width):
        """Create a list of `ConstNet` of ``width`` representing the given value in big endian.

        Args:
            value (:obj:`int`): the unsigned integer value
            width (:obj:`int`): the width of the array to be created

        Endianness: the first element in the created list will be the MSB of the value.
        """
        return tuple(cls.one if (value & (1 << i)) else cls.zero for i in reversed(range(width)))

ConstNet.open = ConstNet(NetType.open)
ConstNet.zero = ConstNet(NetType.zero)
ConstNet.one = ConstNet(NetType.one)

# ----------------------------------------------------------------------------
# -- Abstract Port/Pin -------------------------------------------------------
# ----------------------------------------------------------------------------
class AbstractPortOrPin(AbstractNet):
    """Abstract base class defining a few test properties"""

    # == internal methods ====================================================
    def _validate_physical_cp(self, cp):
        """Check if ``cp`` is a valid physical cp.

        Args:
            cp (`AbstractPortOrPin`-subclass):
        """
        if not cp.is_physical:
            raise PRGAInternalError("'{}' is not a physical net ".format(cp) +
                    "thus can not be set as the physical counterpart of '{}'".format(self))
        elif self.is_source != cp.is_source or self.is_sink != cp.is_sink:
            raise PRGAInternalError("The source/sink attributes of '{}' and '{}' do not match"
                    .format(cp, self))

    def _validate_source(self, source, logical = False, physical = False):
        """Check if ``source`` is a valid logical/physical source.

        Args:
            source (`AbstractPortOrPin`-subclass):
            logical (:obj:`bool`): if ``source`` is expected to be a logical source
            physical (:obj:`bool`): if ``source`` is expected to be a physical source
        """
        if logical and not source.is_logical_source:
            raise PRGAInternalError("'{}' is not a logical source".format(source))
        if physical and not source.is_physical_source:
            raise PRGAInternalError("'{}' is not a physical source".format(source))

    # == low-level API =======================================================
    # -- properties/methods to be overriden by subclasses --------------------
    @abstractproperty
    def direction(self):
        """Direction of this port/pin."""
        raise NotImplementedError

    @abstractproperty
    def is_clock(self):
        """Test if this port/pin is a clock."""
        raise NotImplementedError

    @abstractproperty
    def parent(self):
        """The module(instance) this port(pin) belongs to."""
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

    # -- low-level API methods -----------------------------------------------
    def get_static_cp(self, create = False):
        """Get or create the static counterpart of this net.
        
        Args:
            create (:obj:`bool`): if set to True, a static counterpart will be created if not present.
        """
        return self

    @property
    def is_dynamic(self):
        """Test if this is a dynamic net."""
        return False

# ----------------------------------------------------------------------------
# -- NetBundle ---------------------------------------------------------------
# ----------------------------------------------------------------------------
class NetBundle(namedtuple('NetBundle', 'type bus low high'), AbstractNet):
    """Helper class used to bundle individual port/pin bits back to bus slices.

    Args:
        type (`NetType`): type of this reference
        bus (Port or `Pin`): the original bus to be sliced
        low, high (:obj:`int`): the LSB and MSB of the slice
    """

    # == low-level API =======================================================
    @classmethod
    def Create(cls, bit):
        """Create a bundle from a single bit.

        Args:
            bit (`PortOrPinBit` or `ConstNet`):

        Returns:
            `NetBundle`:
        """
        if bit.is_const:
            return cls(bit.type, None, None, 1)
        else:
            return cls(bit.type, bit.bus, bit.index, bit.index)

    @classmethod
    def Bundle(cls, bits):
        """Create a list of bundles for a list of bits.

        Args:
            bits (:obj:`list` [`PortOrPinBit` or `ConstNet` ]):

        Returns:
            :obj:`list` [`NetBundle` ]:
        """
        list_, bundle = [], None
        for bit in bits:
            if bundle is None:
                bundle = cls.Create(bit)
            elif bundle.type is bit.type:
                if bit.is_const or (bit.index == bundle.high + 1 and bit.bus is bundle.bus):
                    bundle = bundle._replace(high = bundle.high + 1)
                else:
                    list_.append(bundle)
                    bundle = cls.Create(bit)
            else:
                list_.append(bundle)
                bundle = cls.Create(bit)
        list_.append(bundle)
        return list_

    @property
    def is_entire_bus(self):
        """Test if this bundle is an entire bus."""
        return self.type in (NetType.port, NetType.pin) and self.low == 0 and self.high == self.bus.width - 1
