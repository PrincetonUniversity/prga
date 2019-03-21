# Python 2 and 3 compatible
from prga.compatible import *

from prga._archdef.common import TileType
from prga._archdef.routing.common import Position
from prga._context.vpr.idgen import calculate_node_id_in_array

from vprgen.abstractbased import ArchitectureDelegate
from vprgen.abstractbased.impl.namedtuplebased import *

from random import uniform
from itertools import product, count, chain

# ----------------------------------------------------------------------------
# -- Architecture Delegate Imlementation -------------------------------------
# ----------------------------------------------------------------------------
class DelegateImpl(ArchitectureDelegate):
    def __init__(self, context):
        self.__context = context

    # -- implemented properties ----------------------------------------------
    @property
    def name(self):
        return self.__context.top.name

    @property
    def width(self):
        return self.__context.top.width

    @property
    def height(self):
        return self.__context.top.height

    @property
    def x_channel_width(self):
        return self.__context._ext["channel_width"]

    @property
    def y_channel_width(self):
        return self.__context._ext["channel_width"]

    @property
    def models(self):
        for model in itervalues(self.__context.primitives):
            if model.is_custom_primitive or model.is_memory_primitive:
                yield Model(model.name,
                        tuple(ModelInputPort(port.name, port.is_clock, port.clock,
                            [o.name for o in itervalues(model.ports) if o.is_output and port.name in o.sources])
                            for port in itervalues(model.ports) if port.is_input),
                        tuple(ModelOutputPort(port.name, clock=port.clock)
                            for port in itervalues(model.ports) if port.is_output))

    @property
    def complex_blocks(self):
        for block in itervalues(self.__context.blocks):
            yield self._create_top_pb(block)

    @property
    def segments(self):
        for segment in itervalues(self.__context.segments):
            yield Segment(segment.name, segment._ext["segment_id"], segment.length, "default")

    @property
    def switches(self):
        yield Switch('default', 0, uniform(0.0, 1e-10))

    @property
    def nodes(self):
        return self._gen_nodes_in_array(self.__context.top, 0, 0, 0,
                self.__context.top.width, self.__context.top.height)

    @property
    def edges(self):
        return self._gen_edges_in_array(self.__context.top, 0, 0, 0)

    def get_tile(self, x, y):
        return self._get_tile_in_array(self.__context.top, x, y)

    # -- private methods -----------------------------------------------------
    def _bit_name(self, bit):
        return '{}.{}[{}]'.format(bit.parent.name, bit.bus.name, bit.index)

    def _create_leaf_pb(self, instance):
        if instance.is_iopad_primitive:
            return IntermediatePbType(instance.name,
                    inputs = (PbTypePort('outpad', 1), ),
                    outputs = (PbTypePort('inpad', 1), ),
                    modes = (Mode('extio_i',
                        pb_types = (LeafPbType('extio_i', '.input',
                            outputs = (LeafPbTypePort('inpad', 1), )), ),
                        directs = (InterconnectItem('inpad', ('extio_i.inpad', ), (instance.name + '.inpad', ),
                            delay_constants = (DelayConstant('extio_i.inpad', instance.name + '.inpad', min_ = 0.0), )), )),
                            Mode('extio_o',
                        pb_types = (LeafPbType('extio_o', '.output',
                            inputs = (LeafPbTypePort('outpad', 1), )), ),
                        directs = (InterconnectItem('outpad', (instance.name + '.outpad', ), ('extio_o.outpad', ),
                            delay_constants = (DelayConstant(instance.name + '.outpad', 'extio_o.outpad', min_ = 0.0), )), )),
                        ))
        else:
            delay_constants = []
            T_setups = []
            T_clock_to_Qs = []
            # engine = self.__context._ext.get('timing_engine', None)
            for pin in itervalues(instance.pins):
                if pin.is_clock:
                    continue
                elif pin.is_input:
                    if pin.port.clock is None:
                        continue
                    clock = instance.pins[pin.port.clock]
                    for bit in pin:
                        T_setups.append(TSetupOrHold(self._bit_name(bit), clock.name,
                            uniform(0.0, 1e-10)))
                    continue
                if pin.port.clock is not None:
                    clock = instance.pins[pin.port.clock]
                    for bit in pin:
                        T_clock_to_Qs.append(TClockToQ(self._bit_name(bit), clock.name,
                            max_ = uniform(0.0, 1e-10)))
                    if len(pin.port.sources) == 0:
                        continue
                    for bit in pin:
                        T_setups.append(TSetupOrHold(self._bit_name(bit), clock.name,
                            uniform(0.0, 1e-10)))
                for source in map(lambda x: instance.pins[x], pin.port.sources):
                    for src, sink in product(iter(source), iter(pin)):
                        delay_constants.append(DelayConstant(self._bit_name(src), self._bit_name(sink),
                            max_ = uniform(0.0, 1e-10)))
            return LeafPbType(instance.name,
                    ('.latch' if instance.is_flipflop_primitive else
                        '.names' if instance.is_lut_primitive else
                        '.input' if instance.is_inpad_primitive else
                        '.output' if instance.is_outpad_primitive else
                        ('.subckt ' + instance.model.name)),
                    class_ = (LeafPbTypeClass.flipflop if instance.is_flipflop_primitive else
                        LeafPbTypeClass.lut if instance.is_lut_primitive else
                        LeafPbTypeClass.memory if instance.is_memory_primitive else
                        None),
                    inputs = tuple(LeafPbTypePort(pin.name, pin.width,
                        LeafPbTypePortClass[pin.port.port_class.name] if pin.port.port_class else None)
                        for pin in itervalues(instance.pins) if pin.is_input and not pin.is_clock),
                    outputs = tuple(LeafPbTypePort(pin.name, pin.width,
                        LeafPbTypePortClass[pin.port.port_class.name] if pin.port.port_class else None)
                        for pin in itervalues(instance.pins) if pin.is_output),
                    clocks = tuple(LeafPbTypePort(pin.name, pin.width,
                        LeafPbTypePortClass[pin.port.port_class.name] if pin.port.port_class else None)
                        for pin in itervalues(instance.pins) if pin.is_clock),
                    delay_constants = delay_constants,
                    T_setups = T_setups,
                    T_clock_to_Qs = T_clock_to_Qs)

    def _create_interconnects(self, module):
        itx, pat = count(), count()
        directs, muxes = [], []
        for port in chain(filter(lambda x: x.is_output, itervalues(module.ports)),
                iter(pin for instance in itervalues(module.instances)
                    for pin in itervalues(instance.pins) if pin.is_input)):
            for logical_sink in port:
                if len(logical_sink.logical_sources) == 0:
                    continue
                pack_patterns = tuple(PackPattern('pack' + str(next(pat)),
                    self._bit_name(logical_source), self._bit_name(logical_sink))
                    for logical_source in logical_sink.logical_sources
                    if (logical_source, logical_sink) in module.pack_patterns)
                delay_constants = tuple(DelayConstant(self._bit_name(logical_source),
                    self._bit_name(logical_sink), max_ = uniform(0.0, 1e-10))
                    for logical_source in logical_sink.logical_sources)
                itx_item = InterconnectItem('itx' + str(next(itx)),
                        map(self._bit_name, logical_sink.logical_sources),
                        (self._bit_name(logical_sink), ),
                        pack_patterns = pack_patterns,
                        delay_constants = delay_constants)
                if len(logical_sink.logical_sources) == 1:
                    directs.append(itx_item)
                else:
                    muxes.append(itx_item)
        return directs, muxes

    def _create_intermediate_pb(self, instance):
        directs, muxes = self._create_interconnects(instance.model)
        return IntermediatePbType(instance.name,
                inputs = tuple(PbTypePort(pin.name, pin.width)
                    for pin in itervalues(instance.pins) if pin.is_input and not pin.is_clock),
                outputs = tuple(PbTypePort(pin.name, pin.width)
                    for pin in itervalues(instance.pins) if pin.is_output),
                clocks = tuple(PbTypePort(pin.name, pin.width)
                    for pin in itervalues(instance.pins) if pin.is_clock),
                pb_types = tuple((self._create_intermediate_pb(sub) if sub.is_slice else self._create_leaf_pb(sub))
                    for sub in itervalues(instance.model.instances)),
                directs = directs,
                muxes = muxes)

    def _create_top_pb(self, block):
        directs, muxes = self._create_interconnects(block)
        pinlocations = {}
        for port in itervalues(block.ports):
            pinlocations.setdefault((port.side, port.xoffset, port.yoffset), []).append(
                    '{}.{}'.format(block.name, port.name))
        return TopPbType(block.name, block._ext["block_type_id"], block.capacity, block.width, block.height,
                inputs = tuple(TopPbTypeInputPort(port.name, port.width, is_non_clock_global = port.is_global)
                    for port in itervalues(block.ports) if port.is_input and not port.is_clock),
                outputs = tuple(TopPbTypeOutputOrClockPort(port.name, port.width)
                    for port in itervalues(block.ports) if port.is_output),
                clocks = tuple(TopPbTypeOutputOrClockPort(port.name, port.width)
                    for port in itervalues(block.ports) if port.is_clock),
                pb_types = tuple((self._create_intermediate_pb(sub) if sub.is_slice else self._create_leaf_pb(sub))
                    for sub in itervalues(block.instances)),
                directs = directs,
                muxes = muxes,
                pinlocations = PinLocations(PinLocationsPattern.custom,
                    tuple(PinLocationsLoc(Side[side.name], ports, xoffset, yoffset)
                        for (side, xoffset, yoffset), ports in iteritems(pinlocations)))
                    )

    def _get_tile_in_array(self, array, x, y):
        tile = array.get_block(Position(x, y), TileType.logic)
        if tile is None:
            return None
        elif not tile.is_root or tile.model.is_array:
            tile = array.get_root_block(Position(x, y), TileType.logic)
            return self._get_tile_in_array(tile.model, x - tile.position.x, y - tile.position.y)
        else:
            return Tile(tile.model.name, tile.model._ext["block_type_id"], tile.xoffset, tile.yoffset)

    def _gen_nodes_in_array(self, array, global_base, global_x, global_y, global_width, global_height):
        for instance in itervalues(array.instances):
            if not instance.is_root:
                continue
            elif instance.is_io_block or instance.is_logic_block:
                local_base = global_base + instance._ext["node_id"]
                for pin in itervalues(instance.pins):
                    x = global_x + pin.node.position.x
                    y = global_y + pin.node.position.y
                    for bit in pin:
                        ptc = pin.port._ext["ptc"] + bit.index
                        yield Node(local_base + ptc,
                                NodeType.SOURCE if pin.is_output else NodeType.SINK,
                                NodeLoc(x, y, instance.position.subblock * instance.model._ext["num_nodes"] + ptc))
                local_base += instance.model._ext["num_nodes"]
                for pin in itervalues(instance.pins):
                    x = global_x + pin.node.position.x
                    y = global_y + pin.node.position.y
                    for bit in pin:
                        ptc = pin.port._ext["ptc"] + bit.index
                        yield Node(local_base + ptc,
                                NodeType.OPIN if pin.is_output else NodeType.IPIN,
                                NodeLoc(x, y, instance.position.subblock * instance.model._ext["num_nodes"] + ptc,
                                    side = Side[pin.port.side.name]))
            elif instance.is_routing_block:
                local_base = global_base + instance._ext["node_id"]
                for pin in filter(lambda pin: pin.is_segment and pin.is_output, itervalues(instance.nodes)):
                    x = global_x + pin.node.position.x
                    y = global_y + pin.node.position.y
                    span = pin.node.prototype.length - pin.node.position.section - 1
                    xlow = pin.node.dimension.select(
                            max(1, pin.node.direction.select(x, x - span)),
                            x)
                    xhigh = pin.node.dimension.select(
                            min(global_width - 2, pin.node.direction.select(x + span, x)),
                            x)
                    ylow = pin.node.dimension.select(y,
                            max(1, pin.node.direction.select(y, y - span)))
                    yhigh = pin.node.dimension.select(y,
                            min(global_height - 2, pin.node.direction.select(y + span, y)))
                    sec = pin.node.direction.select(
                            pin.node.dimension.select(x - 1, y - 1) - pin.node.position.section,
                            pin.node.dimension.select(x - 1, y - 1) + pin.node.position.section)
                    ptc = (pin.node.prototype._ext["ptc"] + pin.node.direction.select(0, 1) +
                            2 * (sec % pin.node.prototype.length) * pin.node.prototype.width)
                    for bit in pin:
                        yield Node(local_base + pin.port._ext["node_id"] + bit.index,
                                pin.node.dimension.select(NodeType.CHANX, NodeType.CHANY),
                                NodeLoc(xlow, ylow, ptc + 2 * bit.index, xhigh, yhigh),
                                pin.node.direction.select(SegmentDirection.INC_DIR, SegmentDirection.DEC_DIR),
                                pin.node.prototype._ext["segment_id"])
            else:
                assert instance.is_array
                for node in self._gen_nodes_in_array(instance.model,
                        global_base + instance._ext["node_id"],
                        global_x + instance.position.x,
                        global_y + instance.position.y,
                        global_width,
                        global_height):
                    yield node

    def _gen_edges_in_array(self, array, global_base, global_x, global_y):
        for instance in itervalues(array.instances):
            if not instance.is_root:
                continue
            elif instance.is_io_block or instance.is_logic_block:
                logical_base = global_base + instance._ext["node_id"]
                physical_base = logical_base + instance.model._ext["num_nodes"]
                for pin in itervalues(instance.pins):
                    for bit in pin:
                        phys_node = physical_base + pin.port._ext["ptc"] + bit.index
                        logi_node = logical_base + pin.port._ext["ptc"] + bit.index
                        if pin.is_input:
                            yield Edge(phys_node, logi_node, 0)
                        else:
                            yield Edge(logi_node, phys_node, 0)
            elif instance.is_routing_block:
                base = instance.position + (global_x, global_y)
                for port in filter(lambda x: x.is_output, chain(itervalues(instance.model.nodes),
                    itervalues(instance.model.bridges))):
                    sink_node = port.node._replace(position = port.node.position + base)
                    for bit in port:
                        sink_id = calculate_node_id_in_array(self.__context.top, sink_node, bit.index)
                        if sink_id is None:
                            continue
                        for source in bit.logical_sources:
                            src_node = source.bus.node._replace(position = source.bus.node.position + base)
                            src_id = calculate_node_id_in_array(self.__context.top, src_node, source.index)
                            if src_id is not None:
                                yield Edge(src_id, sink_id, 0)
            else:
                assert instance.is_array
                for edge in self._gen_edges_in_array(instance.model, global_base + instance._ext["node_id"],
                        global_x + instance.position.x, global_y + instance.position.y):
                    yield edge
