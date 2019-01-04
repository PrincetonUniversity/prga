# -*- encoding: ascii -*-

"""Optimization: insert configuraion-enabled buffers for external IO."""

__all__ = ['DisableExtioDuringConfigOptimization']

import logging
_logger = logging.getLogger(__name__)

from ..._context.flow import AbstractPass
from ..._archdef.model.physical import AbstractAddonModel
from ..._archdef.portpin.port import PhysicalInputPort, PhysicalOutputPort
from ..._archdef.moduleinstance.instance import PhysicalInstance
from ..._util.util import phash, DictProxy

import itertools
import os
from collections import OrderedDict

# ----------------------------------------------------------------------------
# -- ZbufModel ---------------------------------------------------------------
# ----------------------------------------------------------------------------
class ZbufModel(AbstractAddonModel):
    """Built-in model for configurable buffers that outputs zero if not enabled.

    Args:
        context (`ArchitectureContext`): the architecture context this model belongs to
    """
    def __init__(self, context):
        super(ZbufModel, self).__init__(context, 'adn_zbuf')
        self.__ports = OrderedDict((
            ('i', PhysicalInputPort(self, 'i', 1)),
            ('o', PhysicalOutputPort(self, 'o', 1)),
            ('cfg_e', PhysicalInputPort(self, 'cfg_e', 1)),
            ))

    @property
    def _ports(self):
        """A mapping from name to all ports."""
        return DictProxy(self.__ports)

    def _find_equivalent_pin(self, bit):
        if bit.parent_instance.model is not self:
            raise PRGAInternalError("'{}' is not an instance of model '{}'"
                    .format(bit.parent_instance.name, self.name))
        elif bit.parent.name == 'i':
            return bit.parent_instance._pins['o'][0]
        elif bit.parent.name == 'o':
            return bit.parent_instance._pins['i'][0]
        else:
            return super(ZbufModel, self)._find_equivalent_pin(bit)

# ----------------------------------------------------------------------------
# -- DisableExtioDuringConfigOptimization ------------------------------------
# ----------------------------------------------------------------------------
class DisableExtioDuringConfigOptimization(AbstractPass):
    """Insert configuration-enabled buffers for external IO so they are disabled during configuration."""
    @property
    def key(self):
        """Key of this pass."""
        return "opt.disable_extio_during_config"

    @property
    def passes_before_self(self):
        """Passes that should be executed before this pass."""
        return ("config.circuitry", )

    @property
    def passes_after_self(self):
        """Passes that should be executed after this pass."""
        return ("rtl", )

    def __insert_zbuf_before_bit(self, block, bit, model):
        instance = PhysicalInstance(model, 'adn_zbuf_{:x}'.format(phash(bit.reference)))
        instance._pins['i']._physical_source = bit._physical_source
        instance._pins['cfg_e']._physical_source = block._get_or_create_physical_input("cfg_e", 1)
        bit._physical_source = instance._pins['o']
        block._add_instance(instance)

    def run(self, context):
        # 1. add the zbuf model to the context
        zbuf = context._models.setdefault('adn_zbuf', ZbufModel(context))
        # 2. update verilog template search paths
        context._verilog_template_search_paths.append(
                os.path.join(os.path.abspath(os.path.dirname(__file__)), 'verilog_templates'))
        # 3. modify blocks
        for block in itertools.ifilter(lambda x: x.is_io_block, context.blocks.itervalues()):
            for port in itertools.ifilter(lambda x: x.is_output and not x.is_logical and x.is_external,
                    block._ports.itervalues()):
                for bit in port:
                    self.__insert_zbuf_before_bit(block, bit, zbuf)
