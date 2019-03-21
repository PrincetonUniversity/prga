# Python 2 and 3 compatible
from prga.compatible import *

from prga._archdef.common import PortDirection
from prga._archdef.primitive.switch import CMUXSwitch
from prga._archdef.moduleinstance.configurable import SwitchInstance
from prga._archdef.routing.block import NodeKey
from prga._context.flow import AbstractPass
from prga._util.util import uno
from prga.exception import PRGAInternalError, PRGAAPIError

from enum import Enum
from itertools import chain

# ----------------------------------------------------------------------------
# -- Physical Switch Implementation Style ------------------------------------
# ----------------------------------------------------------------------------
class PhysicalSwitchImplementationStyle(Enum):
    """How physical switches are generated and used."""
    flattened = 0       #: flattened switches are used
    hierarchical = 1    #: hierarchical switches are used in connection blocks

# ----------------------------------------------------------------------------
# -- Physical Completer ------------------------------------------------------
# ----------------------------------------------------------------------------
class PhysicalCompleter(AbstractPass):
    """Physical connections and switches completer."""
    def __init__(self, style = PhysicalSwitchImplementationStyle.flattened):
        if style is not PhysicalSwitchImplementationStyle.flattened:
            raise PRGAAPIError("Auto completer currently only supports flattened switches")
        self._style = style
        self._context = None
        self._switch_cache = {}

    @property
    def key(self):
        """Key of this pass."""
        return "completer.physical"

    @property
    def passes_after_self(self):
        """Passes that should be run after this pass."""
        return ("vpr", "config")

    def _get_switch(self, width):
        name = 'cmux{}'.format(width)
        return self._context._modules.get(name, self._switch_cache.setdefault(name, CMUXSwitch(width)))

    def _instantiate_cmux(self, module, sources, sink):
        """Instantiate a `SwitchInstance` of a configurable mux between the given ``sources`` and ``sink``.

        Args:
            module (`LogicallyConnectableModule`): 
            sources (:obj:`list` [`ConstNet` or `PortOrPinBit` ]):
            sink (`PortOrPinBit`):

        Returns:
            `SwitchInstance`:

        The created `SwitchInstance` will neither be added to the block nor connected to the ``sink``, because the
        muxes might be created when iterating through instances. However, the ``sources`` are connected, because
        connections are always stored in the drivee, which will not affect the ``sources``.
        """
        instance = SwitchInstance(module, self._get_switch(len(sources)), 
                'cmux_{}_{}_{}'.format(sink.parent.name, sink.bus.name, sink.index))
        for src, i in zip(sources, instance.inputs):
            i.physical_source = src
        return instance

    def _process_module(self, module):
        """Implement all logical connections in a slice or a block."""
        muxes = []  # (cmux_instance, sink_bit)
        for sinkbus in filter(lambda x: x.is_sink, chain(itervalues(module.ports),
            iter(pin for instance in itervalues(module.instances) for pin in itervalues(instance.pins)))):
            for bit in sinkbus:
                sink_bit = uno(bit.physical_cp, bit)
                if not sink_bit.is_physical_sink:
                    raise PRGAInternalError("Bit '{}' in module '{}' is not a physical sink"
                            .format(module, sink_bit))
                source_bits = tuple(uno(x.physical_cp, x) for x in bit.logical_sources)
                try:
                    dangling = next(x for x in source_bits if not x.is_physical_source)
                    raise PRGAInternalError("Bit '{}' in module '{}' is not a physical source"
                            .format(module, dangling))
                except StopIteration:
                    pass
                if len(source_bits) > 1: # a mux is needed
                    muxes.append((self._instantiate_cmux(module, source_bits, sink_bit), sink_bit))
                elif len(source_bits) == 1: # a direct connection is needed
                    sink_bit.physical_source = source_bits[0]
        for mux, sink_bit in muxes:
            sink_bit.physical_source = mux.output
            module.add_instance_raw(mux)

    def _process_routing(self, block):
        """Implement all logical connections in a routing block."""
        # 1. implement blockpin/segment -> segment first
        for sinkbus in filter(lambda x: x.is_sink and x.is_segment, itervalues(block.nodes)):
            sourcebus = block.ports.get(NodeKey(sinkbus.node, PortDirection.input), None)
            for bit in sinkbus:
                source_bits = []
                # 1.1 if a bridge is used
                if sourcebus is not None and sourcebus.is_physical_source:
                    source_bits.append(sourcebus[bit.index])
                # 1.2 flattened switch insertion
                source_bits.extend(bit.logical_sources)
                if len(source_bits) > 1: # a mux is needed
                    mux = self._instantiate_cmux(block, source_bits, bit)
                    bit.physical_source = mux.output
                    block.add_instance_raw(mux)
                elif len(source_bits) == 1: # a direct connection is needed
                    bit.physical_source = source_bits[0]
                # 1.3 logical segment source?
                if sourcebus is not None:
                    sourcebus[bit.index].physical_cp = bit.physical_source
        # 2. implement other connections
        for sinkbus in filter(lambda x: x.is_sink and (not x.is_segment or x.is_bridge),
                chain(itervalues(block.nodes), itervalues(block.bridges))):
            for bit in sinkbus:
                source_bits = tuple(uno(x.physical_cp, x) for x in bit.logical_sources)
                try:
                    dangling = next(x for x in source_bits if not x.is_physical_source)
                    raise PRGAInternalError("Bit '{}' in routing block '{}' is not a physical source"
                            .format(block, dangling))
                except StopIteration:
                    pass
                if len(source_bits) > 1: # a mux is needed
                    mux = self._instantiate_cmux(block, source_bits, bit)
                    bit.physical_source = mux.output
                    block.add_instance_raw(mux)
                elif len(source_bits) == 1: # a direct connection is needed
                    bit.physical_source = source_bits[0]

    def run(self, context):
        self._context = context
        self._switch_cache = {}
        for module in chain(itervalues(context.slices), itervalues(context.blocks)):
            self._process_module(module)
        for block in itervalues(context.routing_blocks):
            self._process_routing(block)
        context._modules.update(self._switch_cache)
