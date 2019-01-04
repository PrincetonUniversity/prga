# -*- encoding: ascii -*-

"""Optimization: insert muxes which allow tieing any input pin of a lut instance in logic/io blocks to zero."""

__all__ = ['InsertOpenMuxForLutInputOptimization']

import logging
_logger = logging.getLogger(__name__)

from ..._context.flow import AbstractPass
from ..._archdef.common import NetType, SwitchType
from ..._archdef.portpin.common import ConstNet
from ..._archdef.moduleinstance.instance import PhysicalInstance
from ..._util.util import phash

import itertools

# ----------------------------------------------------------------------------
# -- InsertOpenMuxForLutInputOptimization ------------------------------------
# ----------------------------------------------------------------------------
class InsertOpenMuxForLutInputOptimization(AbstractPass):
    """Insert muxes which allow tieing any input pin of a lut instance in logic/io blocks to zero."""
    @property
    def key(self):
        """Key of this pass."""
        return "opt.insert_open_mux_for_lut_input"

    @property
    def dependences(self):
        """Passes that this pass depends on."""
        return ("finalization", )

    @property
    def passes_after_self(self):
        """Passes that should be executed after this pass."""
        return ("config", "rtl")

    def run(self, context):
        for block in context.blocks.itervalues():
            muxes = []
            for lut in itertools.ifilter(lambda x: x.is_lut, block.instances.itervalues()):
                for bit in lut._pins['in']:
                    bit = bit._physical_cp
                    sources = [ConstNet(NetType.zero)]
                    if bit._physical_source.is_port:
                        sources.append(bit._physical_source)
                    elif bit._physical_source.is_pin:
                        if bit._physical_source.parent_instance.is_switch:
                            mux = bit._physical_source.parent_instance
                            assert mux.is_mux_switch
                            sources.extend(mux._pins['i']._physical_source)
                        else:
                            sources.append(bit._physical_source)
                    else:
                        raise RuntimeError
                    muxes.append((block._instantiate_configurable_mux(sources, bit), bit))
            for mux, sink_bit in muxes:
                sink_bit._physical_source = mux._pins['o']
                block._add_instance(mux, force=True)
