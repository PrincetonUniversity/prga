# -*- encoding: ascii -*-

"""Bit-chain-style Configuration circuitry generator."""

__all__ = ['BitchainConfigGenerator']

from ..._archdef.common import BlockType
from ..._archdef.portpin.port import PhysicalInputPort, PhysicalOutputPort
from ..._archdef.model.physical import AbstractConfigModel
from ..._archdef.moduleinstance.instance import PhysicalInstance
from ..._context.flow import AbstractPass
from ...exception import PRGAAPIError
from ..._util.util import DictProxy

from collections import namedtuple, OrderedDict
import itertools
import os

# ----------------------------------------------------------------------------
# -- BitchainConfigModel -----------------------------------------------------
# ----------------------------------------------------------------------------
class BitchainConfigModel(AbstractConfigModel):
    """Built-in model for bit-chain-style configuration circuitry.

    Args:
        context (`ArchitectureContext`): the architecture context this model belongs to
        width (:obj:`int`): the width of the shift-in/out word
        depth (:obj:`int`): the number of words provided by this model
    """
    def __init__(self, context, width, depth):
        super(BitchainConfigModel, self).__init__(context, self.Create_name(width, depth))
        self.__width = width
        self.__depth = depth
        self.__ports = OrderedDict((
            ('i', PhysicalInputPort(self, 'i', width)),
            ('clk', PhysicalInputPort(self, 'clk', 1)),
            ('e', PhysicalInputPort(self, 'e', 1)),
            ('o', PhysicalOutputPort(self, 'o', width)),
            ('d', PhysicalOutputPort(self, 'd', width * depth)),
            ))

    @property
    def _ports(self):
        """A mapping from name to all ports."""
        return DictProxy(self.__ports)

    @property
    def width(self):
        """Width of the shift-in/out port"""
        return self.__width

    @property
    def depth(self):
        """Number of configuration words provided by this model"""
        return self.__depth

    @property
    def template(self):
        """Name of the template if there is one."""
        return 'btc'

    @property
    def rtlgen_parameters(self):
        """Parameters used for RTL generation."""
        return {'width': self.width, 'depth': self.depth}

    @classmethod
    def Create_name(cls, width, depth):
        """Create a bit-chain config model name given the width and depth."""
        return 'btc_w{}_d{}'.format(width, depth) 
 
# ----------------------------------------------------------------------------
# -- _BitchainConfigTileExtension --------------------------------------------
# ----------------------------------------------------------------------------
class _BitchainConfigTileExtension(namedtuple('_BitchainConfigTileExtension_namedtuple', 
    ('blocks', 'hconn', 'vconn', 'switch'))):
    """Bitchain-style configuration circuitry's extension to a tile.

    Args:
        blocks (:obj:`Sequence` [:obj:`int`]): offset of the bitstream segment configuring the CLB/IOBs in this tile
        hconn, vconn, switch (:obj:`int`): offset of the bitstream segment configuration the routing blocks in this
            tile
    """
    pass
 
# ----------------------------------------------------------------------------
# -- _BitchainConfigExtension ------------------------------------------------
# ----------------------------------------------------------------------------
class _BitchainConfigExtension(object):
    """Bitchain-style configuration circuitry's extension to the architecture context.
    
    Args:
        context (`ArchitectureContext`): the `ArchitectureContext` this extension extends to
        width (:obj:`int`): the width of the flip-flop chain
    """
    def __init__(self, context, width):
        self.__context = context
        self.__array = [[_BitchainConfigTileExtension(tuple(), None, None, None)
            for _ in xrange(context.array.height)] for _ in xrange(context.array.width)]
        self.__width = width
        self._bitstream_size = 0

    @property
    def context(self):
        """The `ArchitectureContext` this extension extends to."""
        return self.__context

    @property
    def array(self):
        """Extensions for tiles."""
        return self.__array

    @property
    def width(self):
        """The width of the configuration chain."""
        return self.__width

# ----------------------------------------------------------------------------
# -- BitchainConfigGenerator -------------------------------------------------
# ----------------------------------------------------------------------------
class BitchainConfigGenerator(AbstractPass):
    """Bit-chain-style configuration circuitry generator.

    Args:
        width (:obj:`int`): the width of the bit-chain
    """
    def __init__(self, width):
        self.__width = width

    @property
    def width(self):
        """Width of the bit-chain."""
        return self.__width

    @property
    def key(self):
        """Key of this pass."""
        return "config.circuitry.bitchain"

    @property
    def dependences(self):
        """Passes that this pass depends on."""
        return ("finalization", )

    @property
    def conflicts(self):
        """Passes conflicting with this pass."""
        return ("config.circuitry", )

    @property
    def passes_after_self(self):
        """Passes that should be executed after this pass."""
        return ('rtl', )

    def __inject_config_instances(self, context, block):
        """Inject configuration instances to a block.

        Args:
            context (`ArchitectureContext`):
            block (`AbstractBlock`): logic/io/routing block
        """
        # 1. hook up any 'cfg_e' pin with 'cfg_e' port
        for instance in block._physical_instances.itervalues():
            try:
                cfg_e = instance._physical_pins['cfg_e']
            except KeyError:
                continue
            if cfg_e[0]._physical_source.is_open:
                cfg_e._physical_source = block._get_or_create_physical_input('cfg_e', 1, 'cfg_e')
        # 2. check if configuration instance is needed
        # TODO: allow reordering of these bits
        bits = [bit for inst in block._physical_instances.itervalues() if inst.is_lut or inst.is_switch
                for bit in inst._physical_pins.get('cfg_d', tuple())]
        if block.is_io_block:
            try:
                bits.append(block._ports['extio_oe'][0])
            except:
                pass
        if len(bits) == 0:
            return
        # 3. get the configuration model 
        depth = -((-len(bits)) / self.__width)
        name = BitchainConfigModel.Create_name(self.__width, depth) 
        model = context._models.setdefault(name, BitchainConfigModel(context, self.__width, depth))
        if not isinstance(model, BitchainConfigModel):
            raise PRGAAPIError("Model '{}' already exists in architecture context '{}'"
                    .format(name, context.name))
        # 4. create and add instance
        instance = PhysicalInstance(model, 'cfg_btc_inst')
        block._add_instance(instance)
        for bit, data in itertools.izip(iter(bits), iter(instance._physical_pins['d'])):
            bit._physical_source = data
        # 5. create ports in the block and connect them
        instance._physical_pins['i']._physical_source = block._get_or_create_physical_input('cfg_i', self.__width)
        instance._physical_pins['clk']._physical_source = block._get_or_create_physical_input('cfg_clk', 1, 'cfg_clk')
        instance._physical_pins['e']._physical_source = block._get_or_create_physical_input('cfg_e', 1, 'cfg_e')
        block._get_or_create_physical_output('cfg_o', self.__width)._physical_source = \
                instance._physical_pins['o']

    def run(self, context):
        # 1. add verilog template search path
        context._verilog_template_search_paths.append(
                os.path.join(os.path.abspath(os.path.dirname(__file__)), 'verilog_templates'))
        # 2. create and store config extension
        extension = context._config_extension = _BitchainConfigExtension(context, self.__width)
        # 3. inject config instance to each block
        for block in context._iter_physical_blocks():
            self.__inject_config_instances(context, block)
        # 4. go through each block instance and connect the chain
        context.array._get_or_create_physical_input('cfg_clk', 1, True)
        context.array._get_or_create_physical_input('cfg_e', 1, True)
        prev = context.array._get_or_create_physical_input('cfg_i', self.__width)
        for x, col in enumerate(context.array._array):
            # go upwards first
            for y, tile in enumerate(col):
                # logic/io block
                if tile.is_root and tile.block is not None:
                    inst = tile.block._instances.get('cfg_btc_inst', None)
                    if inst is not None:
                        blocks = []
                        segment_size = len(inst._pins['d'])
                        for instance in tile.block_instances:
                            if not instance.is_physical:
                                blocks.append(None)
                                continue
                            blocks.append(extension._bitstream_size)
                            extension._bitstream_size += segment_size
                            instance._get_or_create_pin('cfg_i', True)._physical_source = prev
                            prev = instance._get_or_create_pin('cfg_o', True)
                        extension.array[x][y] = extension.array[x][y]._replace(blocks=tuple(blocks))
                # horizontal connection block
                if tile.hconn is not None:
                    inst = tile.hconn._instances.get('cfg_btc_inst', None)
                    if inst is not None:
                        extension.array[x][y] = extension.array[x][y]._replace(hconn=extension._bitstream_size)
                        extension._bitstream_size += len(inst._pins['d'])
                        tile.hconn_instance._get_or_create_pin('cfg_i', True)._physical_source = prev
                        prev = tile.hconn_instance._get_or_create_pin('cfg_o', True)
            # go downwards
            for y, tile in enumerate(reversed(col)):
                y = context.array.height - 1 - y
                # switch block
                if tile.switch is not None:
                    inst = tile.switch._instances.get('cfg_btc_inst', None)
                    if inst is not None:
                        extension.array[x][y] = extension.array[x][y]._replace(switch=extension._bitstream_size)
                        extension._bitstream_size += len(inst._pins['d'])
                        tile.switch_instance._get_or_create_pin('cfg_i', True)._physical_source = prev
                        prev = tile.switch_instance._get_or_create_pin('cfg_o', True)
                # vertical connection block
                if tile.vconn is not None:
                    inst = tile.vconn._instances.get('cfg_btc_inst', None)
                    if inst is not None:
                        extension.array[x][y] = extension.array[x][y]._replace(vconn=extension._bitstream_size)
                        extension._bitstream_size += len(inst._pins['d'])
                        tile.vconn_instance._get_or_create_pin('cfg_i', True)._physical_source = prev
                        prev = tile.vconn_instance._get_or_create_pin('cfg_o', True)
