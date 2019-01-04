# -*- encoding: ascii -*-

"""VPR's archdef.xml generation tool."""

__all__ = ['VPRArchdefGenerator']

import logging
_logger = logging.getLogger(__name__)

from .._timing.common import TimingConstraintType
from .._archdef.common import Side
from .._context.flow import AbstractPass
from .._util.xml import XMLGenerator
from ..exception import PRGAInternalError

import itertools

# ----------------------------------------------------------------------------
# -- VPRArchdefGenerator -----------------------------------------------------
# ----------------------------------------------------------------------------
class VPRArchdefGenerator(AbstractPass):
    """VPR's archdef.xml generation tool.

    Args:
        f (file-like object): the output stream
    """
    def __init__(self, f):
        self.__f = f

    @property
    def key(self):
        """Key of this pass."""
        return "vpr.archdef"

    @property
    def dependences(self):
        """Passes that this pass depends on."""
        return ("vpr.extension", "timing")

    def __bit_name_with_parent(self, bit):
        if bit.is_port:
            return bit.parent_module.name + '.' + bit.name
        else:
            return bit.parent_instance.name + '.' + bit.name

    def __generate_model(self, xg, model):
        """Generate the <model> element in VPR's archdef.xml

        Args:
            xg (`XMLGenerator`): the XML generator
            model (`CustomModel`): user-defined model to be generated
        """
        with xg.element('model', {'name': model.name}):
            with xg.element('input_ports'):
                for port in itertools.ifilter(lambda x: x.is_input, model.ports.itervalues()):
                    attrs = {'name': port.name}
                    if port.is_clock:
                        attrs['is_clock'] = '1'
                    elif port.clock is not None:
                        attrs['clock'] = port.clock
                    sinks = [sink.name for sink in model.ports.itervalues()
                            if sink.is_output and port.name in sink.sources]
                    if len(sinks) > 0:
                        attrs['combinational_sink_ports'] = ' '.join(sinks)
                    xg.element_leaf('port', attrs)
            with xg.element('output_ports'):
                for port in itertools.ifilter(lambda x: x.is_output, model.ports.itervalues()):
                    attrs = {'name': port.name}
                    if port.clock is not None:
                        attrs['clock'] = port.clock
                    xg.element_leaf('port', attrs)

    def __generate_instance(self, xg, instance, engine):
        """Generate the <pb_type> element in VPR's archdef.xml for an instance

        Args:
            xg (`XMLGenerator`): the XML generator
            instance (`Instance`): 
            engine (`AbstractTimingEngine`-subclass): the timing engine
        """
        attrs = {'name': instance.name, 'num_pb': '1'}
        if instance.is_flipflop:
            attrs['blif_model'] = '.latch'
            attrs['class'] = 'flipflop'
        elif instance.is_lut:
            attrs['blif_model'] = '.names'
            attrs['class'] = 'lut'
        elif instance.is_inpad:
            attrs['blif_model'] = '.input'
        elif instance.is_outpad:
            attrs['blif_model'] = '.output'
        elif instance.is_memory:
            attrs['blif_model'] = '.subckt {}'.format(instance.model.name)
            attrs['class'] = 'memory'
        elif instance.is_custom_model:
            attrs['blif_model'] = '.subckt {}'.format(instance.model.name)
        with xg.element('pb_type', attrs):
            for pin in instance.pins.itervalues():
                attrs = {'name': pin.name, 'num_pins': pin.width}
                if instance.is_user_model and pin.port.port_class is not None:
                    attrs['port_class'] = pin.port.port_class.name
                xg.element_leaf('clock' if pin.is_clock else 'output' if pin.is_output else 'input', attrs)
            if instance.is_iopad:
                # TODO: when 'inout' is treated as a multi-mode model, replace the code below with generic multi-mode
                # xml generation
                xg.element_leaf('mode', {'name': 'extio_i',
                    '@pb_type': {'name': 'extio_i', 'num_pb': 1, 'blif_model': '.input',
                        '@output': {'name': 'inpad', 'num_pins': 1}},
                    '@interconnect': {
                        '@direct': {'name': 'inpad', 'input': 'extio_i.inpad', 'output': instance.name + '.inpad',
                            '@delay_constant': {'in_port': 'extio_i.inpad', 'out_port': instance.name + '.inpad',
                                'max': 0, 'min': 0}}}})
                xg.element_leaf('mode', {'name': 'extio_o',
                    '@pb_type': {'name': 'extio_o', 'num_pb': 1, 'blif_model': '.output',
                        '@input': {'name': 'outpad', 'num_pins': 1}},
                    '@interconnect': {
                        '@direct': {'name': 'outpad', 'output': 'extio_o.outpad', 'input': instance.name + '.outpad',
                            '@delay_constant': {'out_port': 'extio_o.outpad', 'in_port': instance.name + '.outpad',
                                'max': 0, 'min': 0}}}})
            else:
                for pin in instance.pins.itervalues():
                    if pin.is_clock:
                        continue
                    elif pin.is_input:
                        if pin.port.clock is None:
                            continue
                        clock = instance.pins[pin.port.clock]
                        for bit in pin:
                            min, max = engine._query_block_timing(TimingConstraintType.setup, clock[0], bit)
                            xg.element_leaf('T_setup', {'value': '{:g}'.format(max),
                                'clock': clock.name, 'port': self.__bit_name_with_parent(bit)})
                        continue
                    if pin.port.clock is not None:
                        clock = instance.pins[pin.port.clock]
                        for bit in pin:
                            min, max = engine._query_block_timing(TimingConstraintType.clk2q, clock[0], bit)
                            xg.element_leaf('T_clock_to_Q', {'min': '{:g}'.format(min), 'max': '{:g}'.format(max),
                                'clock': clock.name, 'port': self.__bit_name_with_parent(bit)})
                        if len(pin.port.sources) == 0:
                            continue
                        for bit in pin:
                            min, max = engine._query_block_timing(TimingConstraintType.setup, clock[0], bit)
                            xg.element_leaf('T_setup', {'value': '{:g}'.format(max),
                                'clock': clock.name, 'port': self.__bit_name_with_parent(bit)})
                    for source in itertools.imap(lambda x: instance.pins[x], pin.port.sources):
                        for src, sink in itertools.product(iter(source), iter(pin)):
                            min, max = engine._query_block_timing(TimingConstraintType.delay, src, sink)
                            xg.element_leaf('delay_constant', {'min': '{:g}'.format(min), 'max': '{:g}'.format(max),
                                'in_port': self.__bit_name_with_parent(src),
                                'out_port': self.__bit_name_with_parent(sink)})

    def __generate_block(self, xg, block, engine):
        """Generate the <pb_type> element in VPR's archdef.xml for a logic/io block

        Args:
            xg (`XMLGenerator`): the XML generator
            block (`LogicBlock` or `IOBlock`): 
            engine (`AbstractTimingEngine`-subclass): the timing engine
        """
        attrs = {'name': block.name}
        if block.is_io_block:
            attrs['capacity'] = block.capacity
        else:
            attrs['width'] = block.width
            attrs['height'] = block.height
        with xg.element('pb_type', attrs), engine._open(block):
            for port in block.ports.itervalues():
                attrs = {'name': port.name, 'num_pins': port.width}
                if not port.is_clock and port.is_input and port.is_global:
                    attrs['is_non_clock_global'] = 'true'
                xg.element_leaf('clock' if port.is_clock else 'output' if port.is_output else 'input', attrs)
            xg.element_leaf('fc', {'in_type': 'frac', 'in_val': '1.0', 'out_type': 'frac', 'out_val': '1.0'})
            with xg.element('pinlocations', {'pattern': 'custom'}):
                locations = {}
                for x, y, side in itertools.product(xrange(block.width), xrange(block.height), Side.all()):
                    ports = filter(lambda port: port.side is side and port.xoffset == x and port.yoffset == y,
                            block.ports.itervalues())
                    if len(ports) == 0:
                        continue
                    xg.element_leaf('loc', {'side': side.name, 'xoffset': x, 'yoffset': y,
                        '#text': ' '.join(block.name + '.' + port.name for port in ports)})
            for instance in block.instances.itervalues():
                self.__generate_instance(xg, instance, engine)
            with xg.element('interconnect'):
                itx = itertools.count()
                pat = itertools.count()
                for port in itertools.chain(itertools.ifilter(lambda x: x.is_output, block.ports.itervalues()),
                        iter(pin for instance in block.instances.itervalues()
                            for pin in instance.pins.itervalues() if pin.is_input)):
                    for logical_sink in port:
                        if len(logical_sink._logical_sources) == 0:
                            continue
                        with xg.element('mux' if len(logical_sink._logical_sources) > 1 else 'direct',
                                {'name': 'itx' + str(next(itx)),
                                    'input': ' '.join(self.__bit_name_with_parent(bit) for bit in
                                        logical_sink._logical_sources),
                                    'output': self.__bit_name_with_parent(logical_sink)}):
                            for logical_src in logical_sink._logical_sources:
                                min, max = engine._query_block_timing(TimingConstraintType.delay,
                                        logical_src._physical_cp, logical_sink._physical_cp)
                                xg.element_leaf('delay_constant',
                                        {'min': '{:g}'.format(min), 'max': '{:g}'.format(max),
                                            'in_port': self.__bit_name_with_parent(logical_src),
                                            'out_port': self.__bit_name_with_parent(logical_sink)})
                                if (logical_src, logical_sink) in block._pack_patterns:
                                    xg.element_leaf('pack_pattern', {'name': 'pack' + str(next(pat)),
                                        'in_port': self.__bit_name_with_parent(logical_src),
                                        'out_port': self.__bit_name_with_parent(logical_sink)})

    def run(self, context):
        with XMLGenerator(self.__f) as xg, xg.element('architecture'):
            xg.element_leaf('switchlist', {'@switch': {'type': 'mux', 'name': 'default_mux', 'R': 0,
                    'Cout': 0, 'Cin': 0, 'Tdel': 1e-11, 'mux_trans_size': 0, 'buf_size': 0}})
            xg.element_leaf('device', {
                '@sizing': {'R_minW_nmos': 0, 'R_minW_pmos': 0},
                '@area': {'grid_logic_tile_area': 0},
                '@switch_block': {'type': 'wilton', 'fs': 3},
                '@connection_block': {'input_switch_name': 'default_mux'},
                '@chan_width_distr': {  '@x': {'distr': 'uniform', 'peak': 1.0},
                                        '@y': {'distr': 'uniform', 'peak': 1.0}}})
            with xg.element('segmentlist'):
                for segment in context.segments.itervalues():
                    xg.element_leaf('segment', {'name': segment.name, 'length': str(segment.length),
                        'type': 'unidir', 'Rmetal': 0.0, 'Cmetal': 0.0, 'freq': 1,
                        '@mux': {'name': 'default_mux'},
                        '@sb': {'type': 'pattern', '#text': ' '.join(('1', ) * (segment.length + 1))},
                        '@cb': {'type': 'pattern', '#text': ' '.join(('1', ) * segment.length)}})
            with xg.element('models'):
                for model in itertools.ifilter(lambda x: x.is_custom_model and x.is_logical,
                        context._models.itervalues()):
                    self.__generate_model(xg, model)
            with xg.element('complexblocklist'):
                for block in context.blocks.itervalues():
                    self.__generate_block(xg, block, context._timing_engine)
            with xg.element('layout'), xg.element('fixed_layout', {'name': context.array.name,
                'width': context.array.width, 'height': context.array.height}):
                for x, col in enumerate(context.array._array):
                    for y, tile in enumerate(col):
                        if tile.is_root and tile.block is not None:
                            xg.element_leaf('single', {'type': tile.block.name,
                                'x': x, 'y': y, 'priority': 1})
