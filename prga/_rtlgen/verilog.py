# -*- encoding: ascii -*-

"""Verilog generator."""

__all__ = ['VerilogGenerator']

import logging
_logger = logging.getLogger(__name__)

from .._archdef.common import NetType, SwitchType, Dimension, SegmentDirection, PortDirection
from .._archdef.portpin.reference import NetBundle
from .._archdef.routing.resource import SegmentReference, SegmentNode
from .._context.flow import AbstractPass
from ..exception import PRGAAPIError

import jinja2 as jj
import os
import itertools

# ----------------------------------------------------------------------------
# -- VerilogGenerator --------------------------------------------------------
# ----------------------------------------------------------------------------
class VerilogGenerator(AbstractPass):
    """Verilog generator.
    
    Args:
        output_dir (:obj:`str`, default='rtl'): the directory where all generated verilog files will be put in

    Raises:
        `PRGAAPIError`:
    """
    def __init__(self, output_dir = 'rtl'):
        self.__output_dir = output_dir
        self.__env = None

    @property
    def key(self):
        """Key of this pass."""
        return "rtl.verilog"

    @property
    def dependences(self):
        """Passes this pass depends on."""
        return ("finalization", )

    def __bundle2verilog(self, bundle):
        """Convert to Verilog string.
        
        Args:
            bundle (`NetBundle`): bundled net bits

        Returns:
            :obj:`str`:
        """
        if bundle.type is NetType.open:
            return "{}'bx".format(bundle.high)
        elif bundle.type is NetType.zero:
            return "{}'b0".format(bundle.high)
        elif bundle.type is NetType.one:
            return "{}'b1".format(bundle.high)
        elif bundle.type is NetType.port:
            if bundle.low == 0 and bundle.high == bundle.bus.width - 1:
                return bundle.bus.name
            elif bundle.low == bundle.high:
                return '{}[{}]'.format(bundle.bus.name, bundle.low)
            else:
                return '{}[{}:{}]'.format(bundle.bus.name, bundle.high, bundle.low)
        else:
            if bundle.low == 0 and bundle.high == bundle.bus.width - 1:
                return '{}_{}'.format(bundle.bus.parent_instance.name, bundle.bus.name)
            elif bundle.low == bundle.high:
                return '{}_{}[{}]'.format(bundle.bus.parent_instance.name, bundle.bus.name, bundle.low)
            else:
                return '{}_{}[{}:{}]'.format(bundle.bus.parent_instance.name, bundle.bus.name,
                        bundle.high, bundle.low)

    def __bits2verilog(self, bits):
        """Convert a sequence of bits to a verilog string."""
        if bits is None:
            return ''
        bundled = NetBundle._Bundle(bits)
        if len(bundled) == 1:
            if bundled[0].is_open:
                return ''
            else:
                return self.__bundle2verilog(bundled[0])
        else:
            return '{{{}}}'.format(', '.join(itertools.imap(self.__bundle2verilog, reversed(bundled))))

    def __segment2verilog(self, segment, is_bridge = False):
        """Convert a `SegmentNode` to a verilog string."""
        if segment is None:
            return ''
        return 'sgmt_{}_{}{}_x{}y{}_{}{}'.format(segment.name, segment.direction.name,
                'x' if segment.dimension is Dimension.horizontal else 'y',
                segment.x, segment.y, segment.section, 'b' if is_bridge else '')

    def _generate_module(self, f, module):
        """Generate verilog for ``module`` and write to output stream ``f``.

        Args:
            f (file-like object): the output stream
            module (Model or Block):

        Raises:
            `PRGAAPIError`: if the given module is not generatable
        """
        if module.is_flipflop:
            f.write(self.__env.get_template('flipflop.v').render({}).encode('ascii'))
        elif module.is_lut:
            f.write(self.__env.get_template('lut.tmpl.v').render({'width': module.width}).encode('ascii'))
        elif module.is_switch:
            if module.is_mux_switch:
                f.write(self.__env.get_template('cmux.tmpl.v').render(
                    {'width': module.width, 'width_sel': module.width_sel}).encode('ascii'))
            else:
                raise PRGAInternalError("Switches other than MUX are not supported yet")
        elif module.is_addon or module.is_config:
            if module.template is not None:
                f.write(self.__env.get_template(module.template + '.tmpl.v')
                        .render(module.rtlgen_parameters).encode('ascii')) 
            else:
                f.write(self.__env.get_template(module.name + '.v').render({}).encode('ascii')) 
        elif module.is_block:
            block = {'name': module.name,
                    'ports': [{'dir': port.direction.name,
                        'width': port.width,
                        'name': port.name} for port in module._physical_ports.itervalues()],
                    'wires': [{'name': "{}_{}".format(instance.name, pin.name),
                        'width': pin.width} for instance in module._physical_instances.itervalues()
                        for pin in instance._physical_pins.itervalues() if pin.is_output],
                    'instances': [{'name': instance.name,
                        'model': instance.model.name,
                        'pins': [{'name': pin.name,
                            'connection': (self.__bits2verilog(pin._physical_source)
                                if pin.is_input else '{}_{}'.format(instance.name, pin.name))}
                            for pin in instance._physical_pins.itervalues()]}
                        for instance in module._physical_instances.itervalues()],
                    'assignments': [{'to': port.name, 'from': from_}
                        for port in module._physical_ports.itervalues() if port.is_output
                        for from_ in (self.__bits2verilog(port._physical_source), )
                        if from_] }
            f.write(self.__env.get_template('block.tmpl.v').render({'block': block}).encode('ascii'))
        else:
            raise PRGAAPIError("Unable to generate verilog for module '{}'"
                    .format(module.name))

    def _generate_array(self, f, array):
        """Generate the top-level array and write to an output stream.

        Args:
            f (file-like object): the output stream
            array (`Array`): the top-level array
        """
        # 1. module declaration
        f.write(self.__env.get_template('moduledecl.top.tmpl.v').render({'name': array.name}).encode('ascii'))
        # 2. ports
        comma = False
        # 2.1 physical inputs/outputs
        for port in array._ports.itervalues():
            f.write(self.__env.get_template('port.top.tmpl.v').render(
                {'comma': comma, 'dir': port.direction.name, 'width': port.width, 'name': port.name}).encode('ascii'))
            comma = True
        # 2.2 IOBlock external ports
        for x, y in itertools.product(xrange(array.width), xrange(array.height)):
            tile = array._get_tile(x, y)
            if tile.is_root:
                for subblock, instance in enumerate(tile.block_instances):
                    if not instance.is_physical:
                        continue
                    for pin in itertools.ifilter(lambda x: not x.is_logical and x.port.is_external,
                            instance._physical_pins.itervalues()):
                        f.write(self.__env.get_template('port.top.tmpl.v').render(
                            {'comma': comma, 'dir': pin.direction.name, 'width': 1,
                                'name': '{}_{}'.format(instance.name, pin.name)}).encode('ascii'))
                        comma = True
        # 3. port list ends
        f.write(self.__env.get_template('portend.top.tmpl.v').render({}).encode('ascii'))
        # 4. wires
        for tile in array._iter_tiles():
            # 4.1 logical block ports and non-logical block outputs
            if tile.is_root:
                for subblock, instance in enumerate(tile.block_instances):
                    if not instance.is_physical:
                        continue
                    for pin in instance._pins.itervalues():
                        if ( (pin.is_logical and (pin.is_output or not (pin.is_clock or pin.port.is_global))) or
                                (not pin.is_logical and pin.is_output and not pin.port.is_external) ):
                            f.write(self.__env.get_template('wire.top.tmpl.v').render({'width': pin.width,
                                'name': '{}_{}'.format(instance.name, pin.name)}).encode('ascii'))
            # 4.2 non-logical routing block outputs
            for instance in (tile.hconn_instance, tile.vconn_instance, tile.switch_instance):
                if instance is None:
                    continue
                for port in itertools.ifilter(lambda x: not x.is_logical and x.is_output and not x.port.is_external,
                        instance._pins.itervalues()):
                    f.write(self.__env.get_template('wire.top.tmpl.v').render({'width': port.width,
                        'name': '{}_{}'.format(instance.name, port.name)}).encode('ascii'))
            if tile.x == array.width - 1 or tile.y == array.height - 1:
                continue
            # 4.3 routing wire segments (and bridges)
            for sgmt in array._context.segments.itervalues():
                segments = []
                if tile.x > 0 and tile.is_top_edge:
                    segments.extend(SegmentNode(sgmt, tile.x, tile.y, Dimension.horizontal, SegmentDirection.inc, sec)
                            for sec in xrange(sgmt.length if tile.space_decx == 0 else 1))
                    segments.extend(SegmentNode(sgmt, tile.x, tile.y, Dimension.horizontal, SegmentDirection.dec, sec)
                            for sec in xrange(sgmt.length if tile.space_incx == 0 else 1))
                if tile.y > 0 and tile.is_right_edge:
                    segments.extend(SegmentNode(sgmt, tile.x, tile.y, Dimension.vertical, SegmentDirection.inc, sec)
                            for sec in xrange(sgmt.length if tile.space_decy == 0 else 1))
                    segments.extend(SegmentNode(sgmt, tile.x, tile.y, Dimension.vertical, SegmentDirection.dec, sec)
                            for sec in xrange(sgmt.length if tile.space_incy == 0 else 1))
                for s in segments:
                    f.write(self.__env.get_template('wire.top.tmpl.v').render({'width': s.prototype.width,
                        'name': self.__segment2verilog(s), }).encode('ascii'))
                    if array._is_bridge_needed(s):
                        f.write(self.__env.get_template('wire.top.tmpl.v').render({'width': s.prototype.width,
                            'name': self.__segment2verilog(s, True), }).encode('ascii'))
        # 5. instances
        f.write('\n')
        for tile in array._iter_tiles():
            # 5.1 logic/io instances
            if tile.is_root:
                for subblock, instance in enumerate(tile.block_instances):
                    if not instance.is_physical:
                        continue
                    pins = []
                    for pin in instance._physical_pins.itervalues():
                        if pin.is_input and any(not bit._physical_source.is_open for bit in pin):
                            pins.append({'name': pin.name, 'connection': self.__bits2verilog(pin._physical_source)})
                        elif pin.is_logical and (pin.is_clock or (pin.is_input and pin.port.is_global)):
                            pins.append({'name': pin.name,
                                'connection': self.__bits2verilog(array._globals.get(pin.port.global_, None))})
                        elif pin.is_logical or pin.is_output or pin.port.is_external:
                            pins.append({'name': pin.name, 'connection': '{}_{}'.format(instance.name, pin.name)})
                        elif pin.port.global_ is not None:
                            pins.append({'name': pin.name,
                                'connection': self.__bits2verilog(array._globals.get(pin.port.global_, None))})
                        else:
                            pins.append({'name': pin.name, 'connection': ''})
                    f.write(self.__env.get_template('instance.top.tmpl.v').render({'model': instance.block.name,
                        'name': instance.name, 'pins': pins}).encode('ascii'))
            # 5.2 routing block instances
            for instance in (tile.hconn_instance, tile.vconn_instance, tile.switch_instance):
                if instance is None:
                    continue
                pins = []
                for pin in instance._physical_pins.itervalues():
                    if pin.is_input and any(not bit._physical_source.is_open for bit in pin):
                        pins.append({'name': pin.name, 'connection': self.__bits2verilog(pin._physical_source)})
                    elif pin.is_logical:
                        if pin.port.node_reference.is_blockpin:
                            node = array._dereference_routing_node(tile.x, tile.y, pin.port.node_reference)
                            pins.append({'name': pin.name,
                                'connection': self.__bits2verilog(node) if node.is_physical else ''})
                        else:
                            node = array._dereference_routing_node_from_pin(pin)
                            bridge = (node is not None and (
                                (instance.is_switch_block and pin.is_output and
                                    array._find_connection_block_pin_driving_segment(node) is not None) or
                                (not instance.is_switch_block and pin.is_input and
                                    (pin.port.node_reference, PortDirection.output) in instance.block._nodes) ))
                            pins.append({'name': pin.name, 'connection': self.__segment2verilog(node, bridge)})
                    elif pin.is_output or pin.port.is_external:
                        pins.append({'name': pin.name, 'connection': '{}_{}'.format(instance.name, pin.name)})
                    elif pin.port.global_ is not None:
                        pins.append({'name': pin.name,
                            'connection': self.__bits2verilog(array._globals.get(pin.port.global_, None))})
                    else:
                        pins.append({'name': pin.name, 'connection': ''})
                f.write(self.__env.get_template('instance.top.tmpl.v').render({'model': instance.block.name,
                    'name': instance.name, 'pins': pins}).encode('ascii'))
        # 6. end module
        f.write(self.__env.get_template('moduleend.top.tmpl.v').render({}).encode('ascii'))

    def run(self, context):
        if not os.path.isdir(self.__output_dir):
            os.mkdir(self.__output_dir)
        search_paths = context._verilog_template_search_paths
        search_paths.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'verilog_templates'))
        self.__env = jj.Environment(loader=jj.FileSystemLoader(search_paths))
        for module in itertools.chain(context._iter_physical_blocks(),
                itertools.ifilter(lambda x: x.is_flipflop or x.is_lut or x.is_switch or x.is_config or x.is_addon,
                    context._models.itervalues())):
            filename = os.path.join(self.__output_dir, module.name + '.v')
            self._generate_module(open(filename, 'w'), module)
            context._verilog_files.append(filename)
        filename = os.path.join(self.__output_dir, context.array.name + '.v')
        self._generate_array(open(filename, 'w'), context.array)
        context._verilog_files.append(filename)
