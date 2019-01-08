# -*- encoding: ascii -*-

"""Common classes and helpers for configuration circuitry generator/serializer."""

__all__ = ['ConfigurationCircuitryType', 'AbstractConfigProtoSerializer']

import logging
_logger = logging.getLogger(__name__)

import struct
from abc import ABCMeta, abstractmethod
from enum import Enum

# ----------------------------------------------------------------------------
# -- Configuration Circuitry Type --------------------------------------------
# ----------------------------------------------------------------------------
class ConfigurationCircuitryType(Enum):
    """Configuration circuitry types."""
    bitchain = 0

# ----------------------------------------------------------------------------
# -- AbstractConfigProtoSerializer -------------------------------------------
# ----------------------------------------------------------------------------
class AbstractConfigProtoSerializer(object):
    """Abstract base class for config proto serializer.

    Args:
        f (file-like object): the output stream

    """
    __metaclass__ = ABCMeta

    def __init__(self, f, packet_size = 4096):
        self._f = f
        self._f.write(struct.pack('<8s', 'prgacfgm'.encode('ascii')))
        self._packet_size = packet_size
        self._packet = None

    @abstractmethod
    def _new_header(self):
        """:obj:`abstractmethod`: create a new ``Header`` object."""
        raise NotImplementedError

    @abstractmethod
    def _new_packet(self):
        """:obj:`abstractmethod`: create a new ``Packet`` object."""
        raise NotImplementedError

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, trackback):
        if exc_type is not None:
            return
        if self._packet is not None:
            self._serialize(self._packet)
        self._f.write(struct.pack('<I', 0))

    def _serialize(self, obj):
        """Serialize one proto packet or header.

        Args:
            obj (``Packet`` or ``Header``):
        """
        self._f.write(struct.pack('<I', obj.ByteSize()))
        self._f.write(obj.SerializeToString())

    class _HeaderContextManager(object):
        def __init__(self, serializer):
            self._serializer = serializer

        def __enter__(self):
            self._header = self._serializer._new_header()
            return self._header

        def __exit__(self, exc_type, exc_value, trackback):
            if exc_type is not None:
                return
            self._serializer._serialize(self._header)

    def add_header(self):
        """Return a context manager object which manages a ``Header`` object."""
        return self._HeaderContextManager(self)

    def _emit_if_necessary(self):
        if self._packet.ByteSize() < self._packet_size:
            return
        self._serialize(self._packet)
        self._packet = None

    class _PacketDataContextManager(object):
        def __init__(self, serializer, obj):
            self._serializer = serializer
            self._obj = obj

        def __enter__(self):
            return self._obj

        def __exit__(self, exc_type, exc_value, trackback):
            self._serializer._emit_if_necessary()

    def add_block(self):
        """Return a context manager object which manages a ``proto.Block`` object."""
        if self._packet is None:
            self._packet = self._new_packet()
        return self._PacketDataContextManager(self, self._packet.blocks.add())

    def add_placement(self):
        """Return a context manager object which manages a ``proto.Placement`` object."""
        if self._packet is None:
            self._packet = self._new_packet()
        return self._PacketDataContextManager(self, self._packet.placements.add())

    def add_edge(self):
        """Returns a context manager object which manages a ``Edge`` object."""
        if self._packet is None:
            self._packet = self._new_packet()
        return self._PacketDataContextManager(self, self._packet.edges.add())

    def add_attachment(self):
        """Returns a context manager object which manages a ``proto.Attachment`` object."""
        if self._packet is None:
            self._packet = self._new_packet()
        return self._PacketDataContextManager(self, self._packet.attachments.add())
