# Python 2 and 3 compatible
from prga.compatible import *

"""This module defines `ArchitectureContext`, the main interface to PRGA architecture description."""

from prga._archdef.common import TileType
from prga._archdef.primitive.builtin import (LUTPrimitive, FlipflopPrimitive,
        IopadPrimitive, InpadPrimitive, OutpadPrimitive)
from prga._archdef.primitive.custom import CustomPrimitive
from prga._archdef.routing.common import Position, SegmentPrototype, Global
from prga._archdef.block.block import LogicBlock, IOBlock
from prga._archdef.array.array import Array, RoutingChannelCoverage
from prga._util.util import DictDelegate, regex, ExtensibleObject
from prga.exception import PRGAInternalError, PRGAAPIError

from collections import OrderedDict
from enum import Enum
import re
import sys

try:
    import cPickle as pickle
except ImportError:
    import pickle

_py3 = sys.version_info >= (3, )

class PrimitivesDelegate(Mapping):
    """Helper class for `ArchitectureContext.primitives` property."""
    def __init__(self, context):
        self.__context = context

    def __getitem__(self, key):
        module = self.__context._modules.get(key, None)
        if module is not None:
            if module.is_primitive and module.is_user_primitive:
                return module
            else:
                raise KeyError(key)
        if key == 'flipflop':
            return self.__context._modules.setdefault(key, FlipflopPrimitive())
        matched = re.match('^lut(?P<width>[2-8])$', key)
        if matched:
            return self.__context._modules.setdefault(key, LUTPrimitive(int(matched.group('width'))))
        raise KeyError(key)

    def __iter__(self):
        return iter(DictDelegate(self.__context._modules,
            lambda kv: kv[1].is_primitive and kv[1].is_user_primitive))

    def __len__(self):
        return len(DictDelegate(self.__context._modules,
            lambda kv: kv[1].is_primitive and kv[1].is_user_primitive))

# ----------------------------------------------------------------------------
# -- ArchitectureContext -----------------------------------------------------
# ----------------------------------------------------------------------------
class ArchitectureContext(ExtensibleObject):
    """The main interface to PRGA architecture description.

    Architecture context manages all resources created/added to the FPGA, including all built-in models, switches,
    blocks, routing blocks, tiles, configuration circuitry etc.
    """
    def __init__(self):
        # routing resources
        self._globals = OrderedDict()
        self._segments = OrderedDict()
        # modules
        self._modules = OrderedDict()
        # top-level array
        self._top = None
        # extensions
        self._passes_applied = set()

    # == primitive-related ===================================================
    @property
    def primitives(self):
        """A mapping from primitive names to primitives."""
        return PrimitivesDelegate(self)

    def create_primitive(self, name):
        """Create a `CustomPrimitive` with the given name.

        Args:
            name (:obj:`str`): name of the created model

        Raises:
            `PRGAAPIError`: if the name is invalid or conflicts with other RTL modules.

        Returns:
            `CustomPrimitive`: the created model
        """
        raise NotImplementedError

    # == routing-related =====================================================
    @property
    def globals(self):
        """A mapping from names to global wires."""
        return DictDelegate(self._globals)

    def create_global(self, name, is_clock = False):
        """Create a `Global` wire with the given name.

        Args:
            name (:obj:`str`): name of the created global wire
            is_clock (:obj:`bool`): if this global wire is a clock wire

        Raises:
            `PRGAAPIError`: if a global wire with the same name is already created

        Returns:
            `Global`: the created global wire
        """
        if name in self._globals:
            raise PRGAAPIError("Name '{}' conflicts with existing global wires".format(name))
        return self._globals.setdefault(name, Global(name, is_clock))

    def bind_global(self, name, position):
        """Bind global wire ``name`` to the IOB at ``position``.

        Args:
            name (:obj:`str`): name of the global wire to be bound. The global wire must be created by calling
                `ArchitectureContext.create_global` first
            position (`Position`): the position of the IOB in the top-level array

        Raises:
            `PRGAAPIError`: if no global wire is named ``name``, or the global wire is already bound, or no IOB found
                at ``position``

        Be careful if the IOB is inside a sub-array. If multiple instances of the sub-array exist, all the instances
        will be affected, resulting in wrong behavior.
        """
        global_, position = self._globals.get(name, None), Position(*position)
        # 1. validate
        if global_ is None:
            raise PRGAAPIError("No global wire named '{}'".format(name))
        elif global_._binding is not None:
            raise PRGAAPIError("Global wire '{}' already bound at IOB ({}, {}, {})"
                    .format(name, global_._binding.x, global_._binding.y, global_._binding.subblock))
        global_._binding = position
        # 2. find the block
        array, pos = self.top, position
        if array is None:
            raise PRGAAPIError("No top-level array pointed")
        while True:
            instance = array.get_root_block(position, TileType.logic)
            if instance is None:
                raise PRGAAPIError("No block found at position ({}, {}, {})"
                        .format(position.x, position.y, position.subblock))
            elif instance.is_array:
                array, pos = instance.model, pos - instance.position
                continue
            elif instance.is_io_block:
                try:
                    instance._bind_global(global_)
                    return
                except PRGAInternalError as e:
                    raise_from(PRGAAPIError(e.message), e)
            else:
                raise PRGAAPIError("Block '{}' found at position ({}, {}, {}) is not an IOB"
                        .format(instance.name, position.x, position.y, position.subblock))

    @property
    def segments(self):
        """A mapping from names to wire segments."""
        return DictDelegate(self._segments)

    def create_segment(self, name, width, length = 1):
        """Create a `SegmentPrototype` with the given name, width and length.

        Args:
            name (:obj:`str`): name of the created segment
            width (:obj:`str`): number of wire segment originating from one tile in one direction
            length (:obj:`int`): length of the created segment

        Raises:
            `PRGAAPIError`: if a segment with the same name is already created

        Returns:
            `SegmentPrototype`: the created segment
        """
        if name in self._segments:
            raise PRGAAPIError("Name '{}' conflicts with existing segments".format(name))
        return self._segments.setdefault(name, SegmentPrototype(name, width, length))

    # == block-related =======================================================
    @property
    def slices(self):
        """A mapping from names to slices."""
        return DictDelegate(self._modules, lambda kv: kv[1].is_slice)

    @property
    def blocks(self):
        """A mapping from names to logic/io blocks."""
        return DictDelegate(self._modules,
                lambda kv: kv[1].is_block and (kv[1].is_logic_block or kv[1].is_io_block))

    def create_logic_block(self, name, width = 1, height = 1):
        """Create a `LogicBlock` with the given name.

        Args:
            name (:obj:`str`): name of the created block
            width (:obj:`int`, default=1): width of the created block
            height (:obj:`int`, default=1): height of the created block

        Raises:
            `PRGAAPIError`: if the name is invalid or conflicts with other RTL modules.

        Returns:
            `LogicBlock`: the created block
        """
        if name in self._modules:
            raise PRGAAPIError("Name '{}' conflicts with existing modules".format(name))
        return self._modules.setdefault(name, LogicBlock(name, width, height))

    def create_io_block(self, name, capacity = 1, input = True, output = True):
        """Create a `IOBlock` with the given name.

        Args:
            name (:obj:`str`): name of the created block
            capacity (:obj:`int`, default=1): number of blocks placed in one tile
            input, output (:obj:`bool`, default=True): if this IO block can be used as an external input/output

        Raises:
            `PRGAAPIError`: if the name is invalid or conflicts with other RTL modules.

        Returns:
            `IOBlock`: the created block
        """
        if name in self._modules:
            raise PRGAAPIError("Name '{}' conflicts with existing modules".format(name))
        if not input and not output:
            raise PRGAAPIError("At least one of 'input' and 'output' must be 'True'")
        model = (self._modules.setdefault('iopad', IopadPrimitive()) if input and output else
                self._modules.setdefault('inpad', InpadPrimitive()) if input else
                self._modules.setdefault('outpad', OutpadPrimitive()))
        return self._modules.setdefault(name, IOBlock(name, model, capacity))

    # == routing block-related ===============================================
    @property
    def routing_blocks(self):
        """A mapping from names to routing blocks."""
        return DictDelegate(self._modules,
                lambda kv: kv[1].is_block and kv[1].is_routing_block)

    def create_connection_block(self):
        raise NotImplementedError

    def create_switch_block(self):
        raise NotImplementedError

    def create_routing_block(self):
        raise NotImplementedError

    # == array-related =======================================================
    @property
    def arrays(self):
        """A mapping from names to arrays."""
        return DictDelegate(self._modules, lambda kv: kv[1].is_block and kv[1].is_array)

    def create_array(self, name, width, height, replace_top = False,
            covers_top_routing_channel = False, covers_right_routing_channel = False,
            covers_bottom_routing_channel = False, covers_left_routing_channel = False):
        """Create an `Array` with the given ``name``, ``width`` and ``height``.

        Args:
            name (:obj:`str`): name of the created array
            width (:obj:`int`): number of tiles in the X dimension
            height (:obj:`int`): number of tiles in the Y dimension
            replace_top (:obj:`bool`): if set, the created array will be set as the top-level array. Note that even if
                not set, the created array will be set as the top-level array if currently no array is set as the top
            covers_top_routing_channel (:obj:`bool`): if set, the array will also include the routing channels to the
                top of this array
            covers_right_routing_channel (:obj:`bool`): if set, the array will also include the routing channels to
                the right of this array
            covers_bottom_routing_channel (:obj:`bool`): if set, the array will also include the routing channels to
                the bottom of this array
            covers_left_routing_channel (:obj:`bool`): if set, the array will also include the routing channels to the
                left of this array

        Raises:
            `PRGAAPIError`: if the name is invalid or conflicts with other RTL modules.

        Returns:
            `Array`: the created array
        """
        if name in self._modules:
            raise PRGAAPIError("Name '{}' conflicts with existing modules".format(name))
        array = self._modules.setdefault(name, Array(name, width, height,
            RoutingChannelCoverage(covers_top_routing_channel, covers_right_routing_channel,
                covers_bottom_routing_channel, covers_left_routing_channel)))
        for global_ in itervalues(self._globals):
            array.get_or_create_physical_input(global_.name, 1, is_global = True)
        if self._top is None or replace_top:
            self._top = array
        return array

    @property
    def top(self):
        """The top-level array in this context."""
        return self._top

    # == serialization =======================================================
    def pickle(self, filename):
        """Pickle the architecture context into a file.

        Args:
            filename (:obj:`str`): the name of the output file
        """
        pickle.dump(self, open(filename, 'wb' if _py3 else 'w'), 2)

    @staticmethod
    def unpickle(filename):
        """Unpickle a pickled architecture context.

        Args:
            filename (:obj:`str`): the name of the pickled file
        """
        return pickle.load(open(filename, 'rb' if _py3 else 'r'))
