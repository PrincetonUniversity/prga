# Python 2 and 3 compatible
from prga.compatible import *

from prga._archdef.common import ModuleType, TileType
from prga._archdef.moduleinstance.module import AbstractLeafModule
from prga._archdef.moduleinstance.instance import PhysicalInstance
from prga._archdef.portpin.port import GlobalPhysicalInputPort, PhysicalInputPort, PhysicalOutputPort
from prga._archdef.routing.common import Position
from prga._context.flow import AbstractPass
from prga._util.util import DictDelegate, uno, register_extension
from prga.exception import PRGAInternalError

from collections import OrderedDict
from itertools import product, chain
import os

import logging
_logger = logging.getLogger(__name__)
_logger.setLevel(logging.INFO)

register_extension("cfg_bits", __name__)
register_extension("cfg_offset", __name__)

# ----------------------------------------------------------------------------
# -- Bitchain Configuration Bit ----------------------------------------------
# ----------------------------------------------------------------------------
class BitchainConfigBitPrimitive(AbstractLeafModule):
    """A single bit of configuration."""
    def __init__(self):
        super(BitchainConfigBitPrimitive, self).__init__("cfg_bit")
        self.__ports = OrderedDict((
            ('cfg_clk', GlobalPhysicalInputPort(self, 'cfg_clk', 1)),
            ('cfg_e', GlobalPhysicalInputPort(self, 'cfg_e', 1)),
            ('i', PhysicalInputPort(self, 'i', 1)),
            ('o', PhysicalOutputPort(self, 'o', 1)),
            ))

    @property
    def type(self):
        return ModuleType.config

    @property
    def _ports(self):
        return DictDelegate(self.__ports)

    @property
    def _fixed_ext(self):
        return {"verilog_template": "cfg_bit.bitchain.tmpl.v"}

    @property
    def is_physical(self):
        return True

# ----------------------------------------------------------------------------
# -- Bitchain Configuration Circuitry Injector -------------------------------
# ----------------------------------------------------------------------------
class BitchainConfigInjector(AbstractPass):
    """Bitchain-style configuration circuitry injector."""
    @property
    def key(self):
        """Key of this pass."""
        return "config.circuitry.bitchain"

    @property
    def conflicts(self):
        """Passes conflicting with this pass."""
        return ("config.circuitry", )

    @property
    def passes_after_self(self):
        """Passes that should be executed after this pass."""
        return ("rtl", )

    def __process_slice(self, slice_):
        if "cfg_bits" in slice_._ext:
            return
        bits = []
        for instance in itervalues(block.physical_instances):
            if (instance.is_primitive and instance.is_lut_primitive) or instance.is_switch:
                bits.extend(instance.physical_pins["cfg_d"])
            elif instance.is_slice:
                self.__process_slice(instance.model)
                bits.extend(instance.physical_pins["cfg_d"])
        slice_._ext["cfg_bits"] = len(bits)
        _logger.debug("slice '{}' has '{}' cfg bits".format(slice_.name, len(bits)))
        if len(bits) == 0:
            return
        slice_.get_or_create_physical_input("cfg_e", 1, is_global = True)
        cfg_d = slice_.get_or_create_physical_input("cfg_d", len(bits))
        for d, bit in zip(iter(cfg_d), iter(bits)):
            bit.physical_source = d

    def __process_block(self, block):
        if "cfg_bits" in block._ext:
            return
        bits = []
        for instance in itervalues(block.physical_instances):
            if (instance.is_primitive and instance.is_lut_primitive) or instance.is_switch:
                bits.extend(instance.physical_pins["cfg_d"])
            elif instance.is_slice:
                self.__process_slice(instance.model)
                bits.extend(instance.physical_pins["cfg_d"])
        if block.is_io_block:
            oe = block.physical_ports.get("extio_oe", None)
            if oe is not None:
                bits.append(oe)
        block._ext["cfg_bits"] = len(bits)
        _logger.debug("block '{}' has '{}' cfg bits".format(block.name, len(bits)))
        if len(bits) == 0:
            return
        block.get_or_create_physical_input("cfg_clk", 1, is_global = True)
        block.get_or_create_physical_input("cfg_e", 1, is_global = True)
        prev = block.get_or_create_physical_input("cfg_i", 1)
        for i, bit in enumerate(bits):
            cfg_bit = PhysicalInstance(block, self._cfg_bit_primitive, 'cfg_bit_{}'.format(i))
            block.add_instance_raw(cfg_bit)
            cfg_bit._ext["cfg_bit"] = i
            cfg_bit.physical_pins["i"].physical_source = prev
            prev = bit.physical_source = cfg_bit.physical_pins["o"]
        block.get_or_create_physical_output("cfg_o", 1).physical_source = prev

    def __process_block_instance(self, instance, prev, cfg_bits):
        # skip this instance if it's already process
        if "cfg_offset" in instance._ext:
            return prev, cfg_bits
        # process the model if not yet processed
        if instance.is_array:
            self.__process_array(instance.model)
        elif instance.is_block:
            self.__process_block(instance.model)
        elif instance.is_slice:
            self.__process_slice(instance.model)
        else:
            assert False
        # update cfg_bits and cfg_offset
        instance._ext["cfg_offset"] = cfg_bits
        _logger.debug("block instance '{}', cfg = [{} +: {}]".format(instance.name, cfg_bits,
            instance.model._ext["cfg_bits"]))
        # update physical connection
        if instance.model._ext["cfg_bits"] == 0:
            return prev, cfg_bits
        else:
            instance.physical_pins["cfg_i"].physical_source = prev
            return instance.physical_pins["cfg_o"], cfg_bits + instance.model._ext["cfg_bits"]

    def __process_array(self, array):
        if "cfg_bits" in array._ext:
            return
        prev, cfg_bits = None, 0
        for x in range(-1, array.width):
            for y, type_ in chain(product(range(-1, array.height), (TileType.logic, TileType.xchan)),
                    product(reversed(range(-1, array.height)), (TileType.switch, TileType.ychan))):
                block = array.get_block(Position(x, y), type_)
                if block is None:
                    continue
                for subblock in range(block.model.capacity):
                    instance = array.get_root_block(Position(x, y, subblock), type_)
                    if instance is None:
                        continue
                    prev, cfg_bits = self.__process_block_instance(instance,
                            uno(prev, array.get_or_create_physical_input('cfg_i', 1)), cfg_bits)
        if cfg_bits > 0:
            array.get_or_create_physical_input('cfg_clk', 1, is_global = True)
            array.get_or_create_physical_input('cfg_e', 1, is_global = True)
            array.get_or_create_physical_output('cfg_o', 1).physical_source = prev
        array._ext["cfg_bits"] = cfg_bits
        _logger.debug("array '{}' has '{}' cfg bits".format(array.name, cfg_bits))

    def run(self, context):
        if context.top is None:
            raise PRGAInternalError("No top-level array pointed")
        self._cfg_bit_primitive = context._modules["cfg_bit"] = BitchainConfigBitPrimitive()
        search_paths = context._ext.setdefault("verilog_template_search_paths", [])
        search_paths.append(os.path.join(os.path.dirname(__file__), "verilog_templates"))
        # top-down BFS, inject config bits at block level
        self.__process_array(context.top)
