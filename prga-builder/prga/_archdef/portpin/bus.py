# Python 2 and 3 compatible
from prga.compatible import *

from prga._archdef.portpin.common import AbstractPortOrPin, ConstNet
from prga._archdef.portpin.bit import PortOrPinBit, DynamicPortOrPinBit
from prga._util.util import uno, ExtensibleObject
from prga.exception import PRGAInternalError

from abc import abstractproperty, abstractmethod

# ----------------------------------------------------------------------------
# -- Abstract Port/Pin Bus ---------------------------------------------------
# ----------------------------------------------------------------------------
class AbstractPortOrPinBus(AbstractPortOrPin, ExtensibleObject, Sequence):
    """Abstract base class for multi-bit port/pin."""

    # == internal methods ====================================================
    @property
    def _default_physical_source(self):
        return tuple(ConstNet.open for _ in range(self.width))

    # == low-level API =======================================================
    # -- properties/methods to be overriden by subclasses --------------------
    @abstractproperty
    def name(self):
        """Name of this bus."""
        raise NotImplementedError

    @abstractproperty
    def parent(self):
        """Parent module/instance of this bus."""
        raise NotImplementedError

    @abstractproperty
    def width(self):
        """Number of bits in this bus."""
        raise NotImplementedError

    @property
    def key(self):
        """Key of this port/pin in the mapping of the parent."""
        return self.name

    # == high-level API ======================================================
    def __len__(self):
        return self.width

    def __str__(self):
        return '{}/{}'.format(self.parent, self.name)

# ----------------------------------------------------------------------------
# -- Static Port/Pin Bus -----------------------------------------------------
# ----------------------------------------------------------------------------
class PortOrPinBus(AbstractPortOrPinBus):
    """Static multi-bit port/pin."""

    # == internal methods ====================================================
    # -- physical counterpart mechanism --------------------------------------
    @property
    def _physical_cp(self):
        try:
            return self.__physical_cp
        except AttributeError:
            return None

    @_physical_cp.setter
    def _physical_cp(self, cp):
        if cp is None:
            try:
                del self.__physical_cp
            except AttributeError:
                pass
        else:
            self._validate_physical_cp(cp)
            self.__physical_cp = cp.get_static_cp(create = True)

    # -- physical source mechanism -------------------------------------------
    @property
    def _physical_source(self):
        try:
            return self.__physical_source
        except AttributeError:
            return None

    @_physical_source.setter
    def _physical_source(self, source):
        if source is None:
            try:
                del self.__physical_source
            except AttributeError:
                pass
        else:
            self._validate_source(source, physical = True)
            self.__physical_source = source.get_static_cp(create = True)

    # -- helper functions ----------------------------------------------------
    @property
    def _static_bits(self):
        """Static bits of this bus."""
        try:
            return self.__static_bits
        except AttributeError:
            return None

    def _make_static_bits(self):
        """Make static bits of this bus."""
        if self._static_bits:
            return
        self.__static_bits = tuple(PortOrPinBit(self, i) for i in range(self.width))

    # == low-level API =======================================================
    # -- physical counterpart mechanism --------------------------------------
    @property
    def physical_cp(self):
        """The physical counterpart of this bus."""
        # 1. try return the physical counterpart defined in the bits
        if self._static_bits and any(x._physical_cp is not None for x in self._static_bits):
            return tuple(x._physical_cp for x in self._static_bits)
        # 2. try return the physical counterpart defined in the bus
        elif self._physical_cp:
            return self._physical_cp
        # 3. if self._static_bits is not defined, return default value
        else:
            return None

    @physical_cp.setter
    def physical_cp(self, cp):
        if cp is None: # clear all counterpart definitions
            if self._static_bits:
                for b in self._static_bits:
                    b._physical_cp = None
            self._physical_cp = None
        elif isinstance(cp, Sequence):
            if len(self) != len(cp):
                raise PRGAInternalError("The width of '{}' and '{}' do not match".format(cp, self))
            elif isinstance(cp, AbstractPortOrPinBus):
                if self._static_bits:
                    for b in self._static_bits:
                        b._physical_cp = None
                self._physical_cp = cp
            else:
                self._physical_cp = None
                self._make_static_bits()
                for b, c in zip(iter(self._static_bits), iter(cp)):
                    b._physical_cp = c
        elif self.width != 1:
            raise PRGAInternalError("The width of '{}' is not 1".format(self))
        else:
            self._physical_cp = None
            self._make_static_bits()
            self[0]._physical_cp = cp

    # -- physical source mechanism -------------------------------------------
    @property
    def physical_source(self):
        """A :obj:`list` of bits that are the physical sources of the bits in this bus.

        You can assign `ConstNet` or `PortOrPinBit` or :obj:`list` [`PortOrPinBit` ] or a physical source
        port to this bus. The number of bits must match the width of this bus.
        """
        # 1. verify that this bus is a physical sink
        if not self.is_physical_sink:
            raise PRGAInternalError("'{}' is not a physical sink".format(self))
        # 2. try return the physical source defined in the bits
        elif self._static_bits and any(x._physical_source is not None for x in self._static_bits):
            return tuple(x._physical_source for x in self._static_bits)
        # 3. try return the physical source defined in this bus
        elif self._physical_source:
            return self._physical_source
        # 4. return default value
        else:
            return self._default_physical_source

    @physical_source.setter
    def physical_source(self, source):
        if not self.is_physical_sink:
            raise PRGAInternalError("'{}' is not a physical sink".format(self))
        elif isinstance(source, Sequence):
            if len(self) != len(source):
                raise PRGAInternalError("The width of '{}' and '{}' do not match".format(source, self))
            elif isinstance(source, AbstractPortOrPinBus):
                if self._static_bits:
                    for b in self._static_bits:
                        b._physical_source = None
                self._physical_source = source
            else:
                self._physical_source = None
                self._make_static_bits()
                for b, s in zip(iter(self._static_bits), iter(source)):
                    b._physical_source = s
        elif self.width != 1:
            raise PRGAInternalError("The width of '{}' is not 1".format(self))
        else:
            self._physical_source = None
            self._make_static_bits()
            self[0]._physical_source = source

    # == high-level API ======================================================
    def __getitem__(self, idx):
        if self._static_bits:
            return self._static_bits[idx]
        elif idx < 0 or idx >= self.width:
            raise IndexError(idx)
        else:
            return DynamicPortOrPinBit(self, idx)

# ----------------------------------------------------------------------------
# -- Dynamic Port/Pin Bus ----------------------------------------------------
# ----------------------------------------------------------------------------
class DynamicPortOrPinBus(AbstractPortOrPinBus):
    """A dynamic multi-bit port/pin."""

    # == low-level API =======================================================
    @abstractmethod
    def get_static_cp(self, create = False):
        raise NotImplementedError

    @property
    def is_dynamic(self):
        """Test if this is a dynamic net."""
        return True

    # -- physical counterpart mechanism --------------------------------------
    @property
    def physical_cp(self):
        """The physical counterpart of this bus."""
        # 1. get the static counterpart of the bus
        cp = self.get_static_cp()
        if cp:
            return cp.physical_cp
        # 2. no static counterpart
        else:
            return None

    @physical_cp.setter
    def physical_cp(self, cp):
        # this is easy. Just hand off to the static counterpart of this bit
        self.get_static_cp(True).physical_cp = cp

    # -- physical source mechanism -------------------------------------------
    @property
    def physical_source(self):
        """The physical source of this bus."""
        # 1. get the static counterpart of the bus
        cp = self.get_static_cp()
        if cp:
            return cp.physical_source
        # 2. verify that this bus is a physical sink
        elif not self.is_physical_sink:
            raise PRGAInternalError("'{}' is not a physical sink".format(self))
        # 3. no static counterpart
        else:
            return self._default_physical_source

    @physical_source.setter
    def physical_source(self, source):
        # this is easy. Just hand off to the static counterpart of this bit
        self.get_static_cp(True).physical_source = source

    # == high-level API ======================================================
    def __getitem__(self, idx):
        cp = self.get_static_cp()
        if cp and cp._static_bits:
            return cp._static_bits[idx]
        elif idx < 0 or idx >= self.width:
            raise IndexError(idx)
        else:
            return DynamicPortOrPinBit(uno(cp, self), idx)
