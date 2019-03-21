# Python 2 and 3 compatible
from prga.compatible import *

from prga._archdef.portpin.common import ConstNet, AbstractPortOrPin
from prga._util.util import uno
from prga.exception import PRGAInternalError

from abc import abstractproperty, abstractmethod

# ----------------------------------------------------------------------------
# -- Abstract Port/Pin bit ---------------------------------------------------
# ----------------------------------------------------------------------------
class AbstractPortOrPinBit(AbstractPortOrPin):
    """Abstract base class for a single bit of a port/pin.

    Args:
        bus (port/pin): the STATIC bus this bit belongs to
        index (:obj:`int`): which bit this bit is in the bus
    """
    def __init__(self, bus, index):
        super(AbstractPortOrPin, self).__init__()
        self._bus = bus
        self._index = index

    # == internal methods ====================================================
    @property
    def _default_physical_source(self):
        return ConstNet.open

    # == low-level API =======================================================
    @property
    def is_physical(self):
        """Test if this port/pin is a physical port/pin."""
        return self._bus.is_physical

    @property
    def is_logical(self):
        """Test if this port/pin is a logical port/pin."""
        return self._bus.is_logical

    @property
    def is_source(self):
        """Test if this port/pin is a logical and/or physical source."""
        return self._bus.is_source

    @property
    def is_sink(self):
        """Test if this port/pin is a logical and/or physical sink."""
        return self._bus.is_sink

    @property
    def direction(self):
        """The direction of this port/pin bit."""
        return self._bus.direction

    @property
    def is_clock(self):
        """Test if this is a clock bit."""
        return self._bus.is_clock

    @property
    def parent(self):
        """The parent module/instance of this port/pin bit."""
        return self._bus.parent

    @property
    def type(self):
        """The type of this net."""
        return self._bus.type

    @property
    def bus(self):
        """Bus of this bit."""
        return self._bus

    @property
    def index(self):
        """Index of this bit."""
        return self._index

    @abstractproperty
    def logical_sources(self):
        """The logical sources of this bit."""
        raise NotImplementedError

    @abstractmethod
    def add_logical_sources(self, sources):
        """Add logical sources to this bit.

        Args:
            sources (`PortOrPinBit` or :obj:`list` [`PortOrPinBit` ] or `AbstractPortOrPinBus`-subclass): the logical
                sources to be added

        Raises:
            `PRGAInternalError`: if ``sources`` is not a valid logical source, or this bit is not a logical sink.
        """
        raise NotImplementedError

    @abstractmethod
    def remove_logical_sources(self, sources = None):
        """Remove logical sources of this bit.

        Args:
            sources (`PortOrPinBit` or :obj:`list` [`PortOrPinBit` ] or `AbstractPortOrPinBus`-subclass): the logical
                sources to be removed. If None is passed, all logic sources will be removed.
        """
        raise NotImplementedError

    # == high-level API ======================================================
    def __str__(self):
        return '{}[{}]'.format(self._bus, self._index)

# ----------------------------------------------------------------------------
# -- Port/Pin bit ------------------------------------------------------------
# ----------------------------------------------------------------------------
class PortOrPinBit(AbstractPortOrPinBit):
    """A single bit of a port/pin.

    Args:
        bus (port/pin): the STATIC bus this bit belongs to
        index (:obj:`int`): which bit this bit is in the bus
    """

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
        elif source.is_const:
            self.__physical_source = source
        else:
            self._validate_source(source, physical = True)
            self.__physical_source = source.get_static_cp(create = True)

    # == low-level API =======================================================
    # -- physical counterpart mechanism --------------------------------------
    @property
    def physical_cp(self):
        """The physical counterpart of this bit."""
        # 1. try return the physical counterpart defined in this bit
        if self._physical_cp:
            return self._physical_cp
        # 2. try return the physical counterpart defined in the bus
        elif self.bus._physical_cp:
            return self.bus._physical_cp[self.index]
        # 3. if self.bus._physical_cp is None, return default value
        else:
            return None

    @physical_cp.setter
    def physical_cp(self, cp):
        # 1. if ``cp`` is the same as the current physical counterpart, take the shortcut and return
        if cp is self.physical_cp:
            return
        # 2. ungroup the physical counterpart of the bus before updating myself
        if self.bus._physical_cp:
            self.bus._physical_cp._make_static_bits()
            for b, c in zip(self.bus, self.bus._physical_cp):
                b._physical_cp = c
            self.bus._physical_cp = None
        # 3. assign new physical counterpart value
        self._physical_cp = cp

    # -- physical source mechanism -------------------------------------------
    @property
    def physical_source(self):
        """The physical source of this bit.

        You can assign `ConstNet` or `PortOrPinBit` or :obj:`list` [`PortOrPinBit` ] or a physical source port to this
        property. If :obj:`list` [`PortOrPinBit` ] or a physical source port is used, the number of bits must be 1.
        """
        # 1. verify that this bit is a physical sink
        if not self.is_physical_sink:
            raise PRGAInternalError("'{}' is not a physical sink".format(self))
        # 2. try return the physical source defined in this bit
        elif self._physical_source is not None:
            return self._physical_source
        # 3. try return the physical source defined in the bus
        elif self.bus._physical_source is not None:
            return self.bus._physical_source[self.index]
        # 4. return default value
        else:
            return self._default_physical_source

    @physical_source.setter
    def physical_source(self, source):
        # 1. if ``source`` is the same as the current physical source, take the shortcut and return
        if source is self.physical_source: # this will verify that this bit is a physical sink, too
            return
        # 2. ungroup the physical source of the bus before updating myself
        if self.bus._physical_source is not None:
            self.bus._physical_source._make_static_bits()
            for b, s in zip(self.bus, self.bus._physical_source):
                b._physical_source = s
            self.bus._physical_source = None
        # 3. in case a :obj:`list` is passed in
        if isinstance(source, Sequence):
            if len(source) != 1:
                raise PRGAInternalError("'{}' contains more than 1 bit".format(source))
            source = source[0]
        # 4. assign new physical source value
        self._physical_source = source

    # -- logical source mechanism --------------------------------------------
    @property
    def logical_sources(self):
        """The logical sources of this bit.

        Note that the list returned by this property is not modifiable. Use `PortOrPinBit.add_logical_sources` and
        `PortOrPinBit.remove_logical_sources` to modify the logical sources instead."""
        if not self.is_logical_sink:
            raise PRGAInternalError("'{}' is not a logical sink".format(self))
        try:
            return tuple(iter(self.__logical_sources))
        except AttributeError:
            return tuple()

    def add_logical_sources(self, sources):
        if not self.is_logical_sink:
            raise PRGAInternalError("'{}' is not a logical sink".format(self))
        try:
            it = iter(sources)
        except TypeError:
            it = iter((sources, ))
        for s in it:
            self._validate_source(s, logical = True)
            try:
                if s not in self.__logical_sources:
                    self.__logical_sources.append(s.get_static_cp(True))
            except AttributeError:
                self.__logical_sources = [s.get_static_cp(True)]

    def remove_logical_sources(self, sources = None):
        if not self.is_logical_sink:
            raise PRGAInternalError("'{}' is not a logical sink".format(self))
        if sources is None:
            try:
                del self.__logical_sources
            except AttributeError:
                return
        try:
            it = iter(sources)
        except TypeError:
            it = iter((sources, ))
        for s in it:
            try:
                self.__logical_sources.remove(uno(s.get_static_cp(), s))
            except KeyError:
                pass
            except AttributeError:
                return
        if len(self.__logical_sources) == 0:
            del self.__logical_sources

# ----------------------------------------------------------------------------
# -- Dynamic Port/Pin bit ----------------------------------------------------
# ----------------------------------------------------------------------------
class DynamicPortOrPinBit(AbstractPortOrPinBit):
    """A single dynamic bit of a port/pin.

    Args:
        bus (port/pin): the static or dynamic bus this bit belongs to
        index (:obj:`int`): which bit this bit is in the bus
    """

    # == low-level API =======================================================
    def get_static_cp(self, create = False):
        bus = uno(self.bus.get_static_cp(create), self.bus)
        if bus._static_bits or create:
            bus._make_static_bits()
            return bus._static_bits[self.index]
        else:
            return None

    @property
    def is_dynamic(self):
        """Test if this is a dynamic net."""
        return True

    # -- physical counterpart mechanism --------------------------------------
    @property
    def physical_cp(self):
        """The physical counterpart of this bit."""
        # 1. get the static counterpart of the bit
        cp = self.bus.get_static_cp()
        if cp:
            return cp.physical_cp[self.index]
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
        """The physical source of this bit."""
        # 1. get the static counterpart of the bit
        cp = self.bus.get_static_cp()
        if cp:
            return cp.physical_source[self.index]
        # 2. verify that this bit is a physical sink
        elif not self.is_physical_sink:
            raise PRGAInternalError("'{}' is not a physical sink".format(self))
        # 3. no static counterpart
        else:
            return self._default_physical_source

    @physical_source.setter
    def physical_source(self, source):
        # this is easy. Just hand off to the static counterpart of this bit
        self.get_static_cp(True).physical_source = source

    # -- logical source mechanism --------------------------------------------
    @property
    def logical_sources(self):
        """The logical sources of this bit."""
        if not self.is_logical_sink:
            raise PRGAInternalError("'{}' is not a logical sink".format(self))
        if self.get_static_cp():
            return self.get_static_cp().logical_sources
        else:
            return tuple()

    def add_logical_sources(self, sources):
        if not self.is_logical_sink:
            raise PRGAInternalError("'{}' is not a logical sink".format(self))
        self.get_static_cp(True).add_logical_sources(sources)

    def remove_logical_sources(self, sources = None):
        if not self.is_logical_sink:
            raise PRGAInternalError("'{}' is not a logical sink".format(self))
        if self.get_static_cp():
            self.get_static_cp().remove_logical_sources(sources)
