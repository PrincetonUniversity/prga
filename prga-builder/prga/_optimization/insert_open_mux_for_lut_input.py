# Python 2 and 3 compatible
from prga.compatible import *

__all__ = ['InsertOpenMuxForLutInputOptimization']

from prga._context.flow import AbstractPass
from prga._archdef.portpin.common import ConstNet
from prga._archdef.primitive.switch import CMUXSwitch
from prga._archdef.moduleinstance.configurable import SwitchInstance
from prga._util.util import uno

from itertools import chain

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
    def passes_before_self(self):
        """Passes that should be executed before this pass."""
        return ("completer", )

    @property
    def passes_after_self(self):
        """Passes that should be executed after this pass."""
        return ("config", "rtl")

    def run(self, context):
        switch_cache = {}
        for module in chain(itervalues(context.blocks), itervalues(context.slices)):
            muxes = []
            for lut in filter(lambda x: x.is_lut_primitive, itervalues(module.instances)):
                for bit in lut.pins['in']:
                    instance_name = 'cmux_{}_{}_{}'.format(bit.parent.name, bit.bus.name, bit.index)
                    bit = uno(bit.physical_cp, bit)
                    sources = [ConstNet.zero]
                    if bit.physical_source.is_port:
                        sources.append(bit.physical_source)
                    elif bit.physical_source.is_pin:
                        if bit.physical_source.parent.is_switch:
                            mux = bit.physical_source.parent
                            assert mux.name == instance_name
                            assert mux.is_mux_switch
                            sources.extend(x.physical_source for x in mux.inputs)
                        else:
                            sources.append(bit.physical_source)
                    else:
                        pass
                    if len(sources) == 1:
                        continue
                    primitive_name = 'cmux{}'.format(len(sources))
                    instance = SwitchInstance(module, context._modules.get(primitive_name,
                        switch_cache.setdefault(primitive_name, CMUXSwitch(len(sources)))),
                        instance_name)
                    for src, i in zip(sources, instance.inputs):
                        i.physical_source = src
                    muxes.append( (instance, bit) )
            for mux, sink_bit in muxes:
                sink_bit.physical_source = mux.output
                module.add_instance_raw(mux, force=True)
        context._modules.update(switch_cache)
