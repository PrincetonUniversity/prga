# -*- encoding: ascii -*-

"""VPR's rrgraph.xml generation tool."""

__all__ = ['VPRRRGraphGenerator']

import logging
_logger = logging.getLogger(__name__)

from .._archdef.routing.resource import SegmentNode
from .._archdef.common import SegmentDirection, Dimension
from .._context.flow import AbstractPass
from .._util.util import uno
from .._util.xml import XMLGenerator

import itertools

# ----------------------------------------------------------------------------
# -- VPRRRGraphGenerator -----------------------------------------------------
# ----------------------------------------------------------------------------
class VPRRRGraphGenerator(AbstractPass):
    """VPR's rrgraph.xml generation tool.

    Args:
        f (file-like object): the output stream
        switches (:obj:`list` [:obj:`float` ], default=None): an ascending list of values for quantilizing routing
            edge delays. All switches will be classified into ``len(switches) + 2`` classes: delay == 0, 0 < delay <=
            switches[0], ..., switches[i] < delay <= switches[i+1], ..., switches[-1] < delay <= max-delay
    """
    def __init__(self, f, switches = None):
        self.__f = f
        switches = uno(switches, [])
        self._switches = [0.0] + switches + [0.0 if len(switches) == 0 else switches[-1]]

    @property
    def key(self):
        """Key of this pass."""
        return "vpr.rrgraph"

    @property
    def dependences(self):
        """Passes that this pass depends on."""
        return ("vpr.extension", "timing")

    def __get_switch_id(self, delay):
        for id_, max_ in enumerate(self._switches):
            if delay <= max_:
                return id_
        self._switches[-1] = delay
        return len(self._switches) - 1

    def __generate_block(self, xg, block, block_ext):
        with xg.element('block_type', {'id': block_ext.id, 'name': block.name,
            'width': block.width, 'height': block.height}):
            if block.capacity == 1:
                for port in block.ports.itervalues():
                    ptc = block_ext.pin_id[port.name]
                    for i in xrange(port.width):
                        xg.element_leaf('pin_class', {'type': port.direction.name.upper(),
                            '@pin': {'ptc': ptc + i, '#text': '{}.{}[{}]'.format(block.name, port.name, i)}})
            else:
                for sub, port in itertools.product(xrange(block.capacity), block.ports.itervalues()):
                    ptc = sub * block_ext.pin_size + block_ext.pin_id[port.name]
                    for i in xrange(port.width):
                        xg.element_leaf('pin_class', {'type': port.direction.name.upper(),
                            '@pin': {'ptc': ptc + i, '#text': '{}[{}].{}[{}]'.format(block.name, sub, port.name, i)}})

    def run(self, context):
        with XMLGenerator(self.__f) as xg, xg.element('rr_graph'):
            ext = context._vpr_extension
            # 1. print channels
            with xg.element('channels'):
                chw = ext.channel_width
                xg.element_leaf('channel', {'chan_width_max': chw,
                    'x_min': chw, 'x_max': chw, 'y_min': chw, 'y_max': chw})
                for x in xrange(context.array.width):
                    xg.element_leaf('x_list', {'index': x, 'info': chw})
                for y in xrange(context.array.height):
                    xg.element_leaf('y_list', {'index': y, 'info': chw})
            # 2. print segments
            with xg.element('segments'):
                for segment in context.segments.itervalues():
                    xg.element_leaf('segment', {'id': ext.segments[segment.name].id, 'name': segment.name,
                        '@timing': {'C_per_meter': 0, 'R_per_meter': 0}})
            # 3. print block_types
            with xg.element('block_types'):
                xg.element_leaf('block_type', {'id': 0, 'name': 'EMPTY', 'width': 1, 'height': 1})
                for block in context.blocks.itervalues():
                    self.__generate_block(xg, block, ext.blocks[block.name])
            # 4. print grids
            with xg.element('grid'):
                for tile in context.array._iter_tiles():
                    if tile.is_root:
                        if tile.block is None:
                            xg.element_leaf('grid_loc', {'block_type_id': 0,
                                'x': tile.x, 'y': tile.y, 'width_offset': 0, 'height_offset': 0})
                        else:
                            xg.element_leaf('grid_loc', {'block_type_id': ext.blocks[tile.block.name].id,
                                'x': tile.x, 'y': tile.y, 'width_offset': 0, 'height_offset': 0})
                    else:
                        root = context.array._get_root_tile(tile.x, tile.y)
                        xg.element_leaf('grid_loc', {'block_type_id': ext.blocks[root.block.name].id,
                            'x': tile.x, 'y': tile.y, 'width_offset': tile.xoffset, 'height_offset': tile.yoffset})
            # 5. print routing nodes
            with xg.element('rr_nodes'):
                for tile in context.array._iter_tiles():
                    # 5.1 block pins
                    if tile.is_root:
                        for instance in tile.block_instances:
                            for pin in instance.pins.itervalues():
                                for i in xrange(pin.width):
                                    xg.element_leaf('node', {'type': 'SINK' if pin.is_input else 'SOURCE',
                                        'capacity': 1, 'id': ext.get_node_id(pin, i, False),
                                        '@loc': {'ptc': ext.get_node_ptc(pin, i),
                                            'xlow': pin.x, 'xhigh': pin.x, 'ylow': pin.y, 'yhigh': pin.y, },
                                        '@timing': {'R': 0, 'C': 0}})
                        # 5.1.2 physical block pins
                        for instance in tile.block_instances:
                            for pin in instance.pins.itervalues():
                                for i in xrange(pin.width):
                                    xg.element_leaf('node', {'type': 'IPIN' if pin.is_input else 'OPIN',
                                        'capacity': 1, 'id': ext.get_node_id(pin, i, True),
                                        '@loc': {'ptc': ext.get_node_ptc(pin, i), 'side': pin.port.side.name.upper(),
                                            'xlow': pin.x, 'xhigh': pin.x, 'ylow': pin.y, 'yhigh': pin.y, },
                                        '@timing': {'R': 0, 'C': 0}})
                    if tile.x == context.array.width - 1 or tile.y == context.array.height - 1:
                        continue
                    # 5.2 horinzontal segments
                    if tile.x > 0 and tile.is_top_edge:
                        for sgmt in context.segments.itervalues():
                            segment_id = ext.segments[sgmt.name].id
                            for sec in xrange(sgmt.length if tile.space_decx == 0 else 1):
                                node = SegmentNode(sgmt, tile.x, tile.y,
                                        Dimension.horizontal, SegmentDirection.inc, sec)
                                xhigh = min(tile.x + sgmt.length - sec - 1, context.array.width - 2)
                                for i in xrange(sgmt.width):
                                    xg.element_leaf('node', {'type': 'CHANX', 'capacity': 1,
                                        'direction': 'INC_DIR', 'id': ext.get_node_id(node, i),
                                        '@loc': {'xlow': tile.x, 'ylow': tile.y, 'xhigh': xhigh, 'yhigh': tile.y,
                                            'ptc': ext.get_node_ptc(node, i)},
                                        '@segment': {'segment_id': segment_id},
                                        '@timing': {'R': 0, 'C': 0}})
                            for sec in xrange(sgmt.length if tile.space_incx == 0 else 1):
                                node = SegmentNode(sgmt, tile.x, tile.y,
                                        Dimension.horizontal, SegmentDirection.dec, sec)
                                xlow = max(tile.x - sgmt.length + sec + 1, 1)
                                for i in xrange(sgmt.width):
                                    xg.element_leaf('node', {'type': 'CHANX', 'capacity': 1,
                                        'direction': 'DEC_DIR', 'id': ext.get_node_id(node, i),
                                        '@loc': {'xlow': xlow, 'ylow': tile.y, 'xhigh': tile.x, 'yhigh': tile.y,
                                            'ptc': ext.get_node_ptc(node, i)},
                                        '@segment': {'segment_id': segment_id},
                                        '@timing': {'R': 0, 'C': 0}})
                    # 5.3 vertical segments
                    if tile.y > 0 and tile.is_right_edge:
                        for sgmt in context.segments.itervalues():
                            segment_id = ext.segments[sgmt.name].id
                            for sec in xrange(sgmt.length if tile.space_decy == 0 else 1):
                                node = SegmentNode(sgmt, tile.x, tile.y,
                                        Dimension.vertical, SegmentDirection.inc, sec)
                                yhigh = min(tile.y + sgmt.length - sec - 1, context.array.height - 2)
                                for i in xrange(sgmt.width):
                                    xg.element_leaf('node', {'type': 'CHANY', 'capacity': 1,
                                        'direction': 'INC_DIR', 'id': ext.get_node_id(node, i),
                                        '@loc': {'xlow': tile.x, 'ylow': tile.y, 'xhigh': tile.x, 'yhigh': yhigh,
                                            'ptc': ext.get_node_ptc(node, i)},
                                        '@segment': {'segment_id': segment_id},
                                        '@timing': {'R': 0, 'C': 0}})
                            for sec in xrange(sgmt.length if tile.space_incy == 0 else 1):
                                node = SegmentNode(sgmt, tile.x, tile.y,
                                        Dimension.vertical, SegmentDirection.dec, sec)
                                ylow = max(tile.y - sgmt.length + sec + 1, 1)
                                for i in xrange(sgmt.width):
                                    xg.element_leaf('node', {'type': 'CHANY', 'capacity': 1,
                                        'direction': 'DEC_DIR', 'id': ext.get_node_id(node, i),
                                        '@loc': {'xlow': tile.x, 'ylow': ylow, 'xhigh': tile.x, 'yhigh': tile.y,
                                            'ptc': ext.get_node_ptc(node, i)},
                                        '@segment': {'segment_id': segment_id},
                                        '@timing': {'R': 0, 'C': 0}})
            # 6. print routing edges
            with xg.element('rr_edges'), context._timing_engine._open():
                for tile in context.array._iter_tiles():
                    # 6.1 logical-physical pin virtucal connections
                    if tile.is_root and tile.block is not None:
                        for instance in tile.block_instances:
                            for pin in instance.pins.itervalues():
                                for i in xrange(pin.width):
                                    if pin.is_input:
                                        xg.element_leaf('edge', {'switch_id': 0,
                                            'src_node': ext.get_node_id(pin, i, True),
                                            'sink_node': ext.get_node_id(pin, i, False)})
                                    else:
                                        xg.element_leaf('edge', {'switch_id': 0,
                                            'src_node': ext.get_node_id(pin, i, False),
                                            'sink_node': ext.get_node_id(pin, i, True)})
                    # 6.2 touting block edges
                    for instance in (tile.hconn_instance, tile.vconn_instance, tile.switch_instance):
                        if instance is None:
                            continue
                        for pin in itertools.ifilter(lambda x: x.is_output, instance.pins.itervalues()):
                            sink_node = context.array._dereference_routing_node_from_pin(pin)
                            if sink_node is None: # or (sink_node.is_blockpin and not sink_node.is_physical):
                                continue
                            for i in xrange(pin.width):
                                sink_id = ext.get_node_id(sink_node, i)
                                for src_bit in itertools.imap(
                                        lambda bit: instance.pins[bit.parent.name][bit.index],
                                        pin.port[i]._logical_sources):
                                    if (not instance.is_switch_block and 
                                            pin.port.node_reference == src_bit.parent.port.node_reference):
                                        continue
                                    src_node = context.array._dereference_routing_node_from_pin(src_bit.parent)
                                    if src_node is None: # or (src_node.is_blockpin and not src_node.is_physical):
                                        continue
                                    src_id = ext.get_node_id(src_node, src_bit.index)
                                    min_, max_ = context._timing_engine._query_edge_timing(
                                            src_node, src_bit.index, sink_node, i)
                                    xg.element_leaf('edge', {'switch_id': self.__get_switch_id(max_),
                                        'src_node': ext.get_node_id(src_node, src_bit.index),
                                        'sink_node': ext.get_node_id(sink_node, i)})
            # 7. print switches
            with xg.element('switches'):
                for id_, delay in enumerate(self._switches):
                    xg.element_leaf('switch', {'buffered': 1, 'configurable': 1, 'type': 'mux',
                        'id': id_, 'name': 'muxsw{}'.format(id_),
                        '@timing': {'R': 0, 'Cin': 0, 'Cout': 0, 'Tdel': '{:g}'.format(delay)},
                        '@sizing': {'mux_trans_size': 0, 'buf_size': 0}})
