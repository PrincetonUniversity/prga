# -*- encoding: ascii -*-

"""This module defines `ArchitectureContext`, the main interface to PRGA architecture description."""

__all__ = ['ArchitectureContext']

import logging
_logger = logging.getLogger(__name__)

from .._archdef.array.array import Array
from .._archdef.model.custom import CustomModel
from .._archdef.model.builtin import LUTModel, FlipflopModel, InputModel, OutputModel, InoutModel
from .._archdef.model.switch import MuxModel
from .._archdef.common import Side, Dimension, SegmentDirection, BlockType
from .._archdef.block.logicblock import LogicBlock 
from .._archdef.block.ioblock import IOBlock
from .._archdef.routing.resource import SegmentPrototype, Global, SegmentReference, BlockPinReference
from .._archdef.routing.connectionblock import ConnectionBlockEnvironment, ConnectionBlock
from .._archdef.routing.switchblock import SwitchBlockEnvironment, SwitchBlock
from .._util.util import regex, DictProxy, uno
from ..exception import PRGAAPIError

import itertools
import re
import os
from collections import OrderedDict

try:
    import cPickle as pickle
except ImportError:
    import pickle

# ----------------------------------------------------------------------------
# -- ArchitectureContext -----------------------------------------------------
# ----------------------------------------------------------------------------
class ArchitectureContext(object):
    """The main interface to PRGA architecture description.

    Args:
        width (:obj:`int`): the width of this architecture
        height (:obj:`int`): the height of this architecture 
        name (:obj:`str`, default='top'): the name of this architecture

    Architecture context manages all resources created/added to the FPGA, including all built-in models, switches,
    blocks, routing blocks, tiles, configuration circuitry etc.
    """
    def __init__(self, width, height, name = 'top'):
        if width < 3 or height < 3:
            raise PRGAAPIError("The architecture must be at least 4 x 4")
        # data
        self.__array = Array(self, name, width, height)
        self.__globals = OrderedDict()
        self.__segments = OrderedDict()
        self.__models = OrderedDict()
        self.__blocks = OrderedDict()
        self.__connection_blocks = []
        self.__switch_blocks = []

        # below are fields reserved for passes
        # vpr
        self._vpr_extension = None      # reserved for VPR extension
        # config
        self._config_extension = None   # reserved for conifiguration circuitry extension
        # verilog backend
        self._verilog_template_search_paths = []
        self._verilog_files = []        # a list of generated verilog files
        # timing
        self._timing_engine = None      # reserved for timing engine
        # flow manager
        self._passes_applied = set()    # passes applied to this context

    def __validate_module_name(self, name):
        if (name.startswith('lut') or name.startswith('cmux') or name.startswith('cfg_') or
                name.startswith('adn_') or name.startswith('cb_') or name.startswith('sb_') or
                name.startswith('sgmt_') or name in ('flipflop', 'input', 'output', 'inout', 'EMPTY')): 
            raise PRGAAPIError("Name '{}' is reserved"
                    .format(name))
        elif name == self.name:
            raise PRGAAPIError("Name '{}' conflicts with name of the architecture"
                    .format(name))
        elif name in self.__models:
            raise PRGAAPIError("Name '{}' conflicts with name of existing custom/built-in model"
                    .format(name))
        elif name in self.__blocks:
            raise PRGAAPIError("Name '{}' conflicts with name of existing logic/io block"
                    .format(name))

    # -- top-level -----------------------------------------------------------
    # ------------------------------------------------------------------------

    # -- internal API --------------------------------------------------------
    def _iter_physical_blocks(self):
        """Returns an iterator over all physical blocks."""
        return itertools.chain(self.__blocks.itervalues(),
                iter(self.__connection_blocks),
                iter(self.__switch_blocks))

    # -- exposed API ---------------------------------------------------------
    @property
    def name(self):
        """Name of this architecture."""
        return self.__array.name

    @property
    def array(self):
        """The encapsulated array of blocks."""
        return self.__array

    # -- model-related -------------------------------------------------------
    # ------------------------------------------------------------------------

    # -- internal API --------------------------------------------------------
    @property
    def _models(self):
        """Returns a mapping from model name to all models."""
        return self.__models

    def _get_user_model(self, name):
        """Get user-instantiable model with the given name.

        Args:
            name (:obj:`str`): name of the model

        Raises:
            `PRGAInternalError`: if no such model found
        """
        model = self.__models.get(name, None)
        if model is not None:
            if model.is_user_model:
                return model
            else:
                raise PRGAInternalError("{} model '{}' is not user-instantiable"
                        .format(model.type.name.capitalize(), name))
        if name == 'flipflop':
            return self.__models.setdefault(name, FlipflopModel(self))
        matched = re.match("^lut(?P<width>\d+)$", name)
        if matched:
            return self.__models.setdefault(name, LUTModel(self, int(matched.group('width'))))
        raise PRGAInternalError("Model '{}' does not exist in architecture context '{}'"
                .format(name, self.name))

    def _get_model(self, name):
        """Get the model with the given name.

        Args:
            name (:obj:`str`): name of the model

        Raises:
            `PRGAInternalError`: if no such model found

        This method is for internal use only. Compared to `ArchitectureContext._get_user_model`, this method can also
        find physical-only and/or logical-only models.
        """
        model = self.__models.get(name, None)
        if model is not None:
            return model
        if name == 'flipflop':
            return self.__models.setdefault(name, FlipflopModel(self))
        elif name == 'input':
            return self.__models.setdefault(name, InputModel(self))
        elif name == 'output':
            return self.__models.setdefault(name, OutputModel(self))
        elif name == 'inout':
            return self.__models.setdefault(name, InoutModel(self))
        matched = re.match("^lut(?P<width>\d+)$", name)
        if matched:
            return self.__models.setdefault(name, LUTModel(self, int(matched.group('width'))))
        matched = re.match("^cmux(?P<width>\d+)$", name)
        if matched:
            return self.__models.setdefault(name, MuxModel(self, int(matched.group('width'))))
        raise PRGAInternalError("Model '{}' does not exist in architecture context '{}'"
                .format(name, self.name))

    # -- exposed API ---------------------------------------------------------
    @property
    def models(self):
        """Returns a mapping from model name to `CustomModel` and built-in models."""
        return DictProxy(self.__models, lambda x: x.is_user_model)

    def create_model(self, name):
        """Create a `CustomModel` with the given name.

        Args:
            name (:obj:`str`): name of the created model

        Raises:
            `PRGAAPIError`: if the name is invalid or conflicts with other RTL modules.

        Returns:
            `CustomModel`: the created model
        """
        self.__validate_module_name(name)
        return self.__models.setdefault(name, CustomModel(self, name))

    # -- block-related -------------------------------------------------------
    # ------------------------------------------------------------------------

    # -- internal API --------------------------------------------------------
    @property
    def _blocks(self):
        """Returns a mapping from logic/io block names to all logic/io blocks."""
        return self.__blocks

    @regex('^(?P<m>(?:cfg_[\w\d]*)|(?:adn_[\w\d]*)|(?:extio_i)|(?:extio_o)|(?:extio_oe))$')
    def _validate_block_port_name(self, d, s, e):
        """Validate if the given name can be used as a block port name.

        Args:
            name (:obj:`str`): name of the port

        Raises:
            `PRGAAPIError`: if the name is not a valid block port name.
        """
        if d is not None:
            raise PRGAAPIError("'{}' is a reserved block port name".format(s))

    @regex('^(?P<m>(?:cfg_[\w\d]*)|(?:adn_[\w\d]*)|(?:extio)|(?:cmux_\d+))$')
    def _validate_block_instance_name(self, d, s, e):
        """Validate if the given name can be used as a block sub-instance name.

        Args:
            name (:obj:`str`): name of the sub-instance

        Raises:
            `PRGAAPIError`: if the name is not a valid block sub-instance name.
        """
        if d is not None:
            raise PRGAAPIError("'{}' is a reserved block instance name".format(s))

    # -- exposed API ---------------------------------------------------------
    @property
    def blocks(self):
        """Returns a mapping from block name to `LogicBlock` or `IOBlock`."""
        return DictProxy(self.__blocks)

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
        self.__validate_module_name(name)
        return self.__blocks.setdefault(name, LogicBlock(self, name, width, height))

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
        self.__validate_module_name(name)
        io = self.__blocks[name] = IOBlock(self, name, capacity)
        if not input and not output:
            raise PRGAAPIError("At least one of 'input' and 'output' must be 'True'")
        io._add_external(input, output)
        return io

    # -- routing-related -----------------------------------------------------
    # ------------------------------------------------------------------------

    # -- internal API --------------------------------------------------------
    @property
    def _connection_blocks(self):
        """A list of connection blocks."""
        return self.__connection_blocks

    @property
    def _switch_blocks(self):
        """A list of switch blocks."""
        return self.__switch_blocks

    def _get_or_create_connection_block(self, dimension, block_lb, block_rt, offset_lb, offset_rt):
        """Get or create the connection block given the environment.

        Args:
            dimension (`Dimension`): the dimension of this connection block
            block_lb (:obj:`str`, default=None): name of the block to the left if this is a vertical connection
                block, or the block to the bottom if this is a horizontal connection block
            block_rt (:obj:`str`, default=None): name of the block to the right if this is a vertical connection
                block, or the block to the top if this is a horizontal connection block
            offset_lb (:obj:`int`, default=0): if ``block_lb`` is larger than 1x1, where is this connection block
                relative to the root tile of ``block_lb``. This offset value is the X-dimensional offset if this is a
                horizontal connection block, or the Y-dimensional offset if this is a vertical connection block
            offset_rt (:obj:`int`, default=0): see ``offset_lb``
        """
        env = ConnectionBlockEnvironment(dimension, block_lb, block_rt, offset_lb, offset_rt)
        try:
            return next(block for block in self.__connection_blocks if block.environment == env)
        except StopIteration:
            block_lb = self._blocks[block_lb] if block_lb is not None else block_lb
            block_rt = self._blocks[block_rt] if block_rt is not None else block_rt
            block = ConnectionBlock(self, 'cb_' + str(len(self.__connection_blocks)),
                    dimension, block_lb, block_rt, offset_lb, offset_rt)
            self.__connection_blocks.append(block)
            return block

    def _get_or_create_switch_block(self, decx, incx, decy, incy):
        """Get or create the switch block given the environment.

        Args:
            decx, incx, decy, incy (:obj:`bool`): if there are segments at the side of this switch block
        """
        env = SwitchBlockEnvironment(decx, incx, decy, incy)
        try:
            return next(block for block in self.__switch_blocks if block.environment == env)
        except StopIteration:
            block = SwitchBlock(self, 'sb_' + str(len(self.__switch_blocks)), *env)
            self.__switch_blocks.append(block)
            return block

    # -- exposed API ---------------------------------------------------------
    @property
    def globals(self):
        """Returns a mapping from global wire name to `Global`."""
        return DictProxy(self.__globals)

    @property
    def segments(self):
        """Returns a mapping from segment name to `SegmentPrototype`."""
        return DictProxy(self.__segments)

    def create_segment(self, name, width, length = 1):
        """Create a `SegmentPrototype` with the given name, width and length.

        Args:
            name (:obj:`str`): name of the created segment
            width (:obj:`str`): number of wire segment originating from one tile in one direction
            length (:obj:`int`, default=1): length of the created segment

        Raises:
            `PRGAAPIError`: if a segment with the same name is already created

        Returns:
            `SegmentPrototype`: the created segment
        """
        if name in self.__segments:
            raise PRGAAPIError("Name '{}' conflicts with name of existing segment".format(name))
        return self.__segments.setdefault(name, SegmentPrototype(name, width, length))

    def create_global(self, name, is_clock = False):
        """Create a `Global` wire with the given name.

        Args:
            name (:obj:`str`): name of the created global wire
            is_clock (:obj:`bool`, default=False): if this global wire is a clock wire

        Raises:
            `PRGAAPIError`: if a global wire with the same name is already created

        Returns:
            `Global`: the created global wire
        """
        if name in self.__globals:
            raise PRGAAPIError("Name '{}' conflicts with name of existing global wire".format(name))
        return self.__globals.setdefault(name, Global(self, name, is_clock))

    # -- serialization -------------------------------------------------------
    # ------------------------------------------------------------------------

    # -- exposed API ---------------------------------------------------------
    def pickle(self, f):
        """Pickle the architecture context into a file-like object.

        Args:
            f (file-like object):
        """
        pickle.dump(self, f, 2)

    @staticmethod
    def unpickle(f):
        """Unpickle a pickled architecture context.

        Args:
            f (file-like object):
        """
        return pickle.load(f)
