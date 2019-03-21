# Python 2 and 3 compatible
from prga.compatible import *

from prga._archdef.common import TileType
from prga._archdef.portpin.common import NetBundle, ConstNet
from prga._context.flow import AbstractPass
from prga._context.vpr.idgen import calculate_node_id_in_array
from prga._util.util import uno
from prga.exception import PRGAInternalError

from proto import common as proto_common, bitchain as proto_bitchain
from prga._configcircuitry.common import AbstractConfigProtoSerializer

import sys
from itertools import chain

import logging
_logger = logging.getLogger(__name__)
_logger.setLevel(logging.INFO)

_py3 = sys.version_info >= (3, )

# ----------------------------------------------------------------------------
# -- _BitchainConfigProtoSerializer ------------------------------------------
# ----------------------------------------------------------------------------
class _BitchainConfigProtoSerializer(AbstractConfigProtoSerializer):
    def _new_header(self):
        """Create a new ``Header`` object."""
        return proto_common.Header()

    def _new_packet(self):
        """Create a new ``Packet`` object."""
        return proto_common.Packet()

# ----------------------------------------------------------------------------
# -- BitchainConfigProtoSerializer -------------------------------------------
# ----------------------------------------------------------------------------
class BitchainConfigProtoSerializer(AbstractPass):
    """Bitchain style configuration circuitry protobuf message serializer.
    
    Args:
        filename (:obj:`str`): the name of the output file
    """
    def __init__(self, filename = 'config.db'):
        self._filename = filename

    @property
    def key(self):
        """Key of this pass."""
        return "config.proto.bitchain"

    @property
    def dependences(self):
        "Passes that this pass dependes on."""
        return ("vpr.id", "config.circuitry.bitchain")

    def __bit_name_with_parent(self, bit):
        if bit.is_port:
            return '{}.{}[{}]'.format(bit.parent.name, bit.bus.name, bit.index)
        else:
            return '{}[0].{}[{}]'.format(bit.parent.name, bit.bus.name, bit.index)

    def __serialize_set_value_actions(self, msglist, bitlist, value, offset = 0):
        """Serialize a list of ``SetValueAction``.

        Args:
            msglist: the protobuf repeated field of type ``SetValueAction``
            bitlist (:obj:`Iterable` [`PortOrPinBit` ]): list of bit to be set
            value (:obj:`int`): value to be set
            offset (:obj:`int`): additional offset added on top of the bitlist indices
        """
        low, high, begin = None, None, 0
        for end, bit in enumerate(bitlist):
            idx = (bit.physical_source.parent._ext["cfg_bit"] if bit.physical_source.is_pin else
                    bit.physical_source.index)
            if high is None:
                low, high = idx, idx + 1
            elif idx == high:
                high += 1
            else:
                action = msglist.add()
                action.offset = offset + low
                action.width = high - low
                action.value = (value & ((1 << end) - 1)) >> begin
                low, high, begin = idx, idx + 1, end
        if low is not None:
            action = msglist.add()
            action.offset = offset + low
            action.width = high - low
            action.value = (value & ((1 << len(bitlist)) - 1)) >> begin

    def __serialize_path_set_value_actions(self, msglist, path, offset = 0):
        for muxbit in path:
            self.__serialize_set_value_actions(msglist, muxbit.parent.physical_pins["cfg_d"],
                    muxbit.index, offset)

    def __serialize_copy_value_actions(self, msglist, bitlist):
        """Serialize a list of ``CopyValueAction``.
        
        Args:
            msglist: the protobuf repeated field of type ``CopyValueAction``
            bitlist (:obj:`Iterable` [:obj:`PortOrPinBit` ]): list of bit to be copied to
        """
        low, high = None, None
        begin = 0
        for bit in bitlist:
            idx = (bit.physical_source.parent._ext["cfg_bit"] if bit.physical_source.is_pin else
                    bit.physical_source.index)
            if high is None:
                low = idx
                high = idx + 1
            elif idx == high:
                high += 1
            else:
                action = msglist.add()
                action.offset = low
                action.width = high - low
                action.begin = begin
                begin += action.width
        if low is not None:
            action = msglist.add()
            action.offset = low
            action.width = high - low
            action.begin = begin
            begin += action.width
        assert begin == len(bitlist)

    def __serialize_port(self, msg, port, block):
        # 1. basic info
        msg.name = port.name
        # 2. iterate through bits
        for sink in port:
            # 2.1 create a new bit message
            bitmsg = msg.bits.add()
            # 2.2 find all physical paths implementing "open" connections
            open_handled = False
            for source, path in block.dfs_physical_paths(uno(sink.physical_cp, sink),
                    (ConstNet.open, ConstNet.zero, ConstNet.one)):
                if path is None:
                    continue
                elif open_handled:
                    raise PRGAInternalError("'{}' has multiple connections that may implement 'open' in VPR"
                            .format(sink))
                open_handled = True
                connmsg = bitmsg.connections.add()
                connmsg.input = 'open'
                self.__serialize_path_set_value_actions(
                        connmsg.action.Extensions[proto_bitchain.Ext.connection_actions], path)
            # 2.3 find all logical source bits and the physical paths implementing these logical connections
            for source in sink.logical_sources:
                _, path = block.dfs_physical_paths(uno(sink.physical_cp, sink),
                        (uno(source.physical_cp, source),))[0]
                if path is None:
                    raise PRGAInternalError("No path from '{}' to '{}'"
                            .format(source, sink))
                connmsg = bitmsg.connections.add()
                connmsg.input = self.__bit_name_with_parent(source)
                self.__serialize_path_set_value_actions(
                        connmsg.action.Extensions[proto_bitchain.Ext.connection_actions], path)

    def __serialize_block(self, msg, block):
        # 1. basic info
        msg.name = block.name
        msg.action.Extensions[proto_bitchain.Ext.config_size] = block._ext["cfg_bits"]
        # 2. output ports
        for port in filter(lambda x: x.is_output, itervalues(block.ports)):
            self.__serialize_port(msg.ports.add(), port, block)
        # 3. sub-instances
        for instance in itervalues(block.instances):
            instmsg = None
            if instance.is_slice: # intermediate pb_type
                instmsg = block.blocks.add()
                self.__serialize_block(instmsg, instance.model)
                # copy-value actions
                self.__serialize_copy_value_actions(
                        instmsg.action.Extensions[proto_bitchain.Ext.subblock_actions],
                        instance.physical_pins.get("cfg_d", tuple()))
            else: # leaf pb_type
                instmsg = msg.instances.add()
                instmsg.name = instance.name
                if instance.is_lut_primitive:
                    instmsg.type = proto_common.Instance.LUT
                    # copy-value actions
                    self.__serialize_copy_value_actions(
                            instmsg.action.Extensions[proto_bitchain.Ext.lut_actions],
                            instance.physical_pins.get("cfg_d", tuple()))
                elif instance.is_iopad_primitive:
                    instmsg.type = proto_common.Instance.MULTIMODE
                    cfg_bit = block._ports['extio_oe']
                    for name, sel in (('extio_i', 0), ('extio_o', 1)):
                        modemsg = instmsg.modes.add()
                        modemsg.name = name
                        self.__serialize_set_value_actions(
                                modemsg.action.Extensions[proto_bitchain.Ext.mode_actions],
                                block._ports["extio_oe"], sel)
                else:
                    assert not instance.is_multimode_primitive
                    instmsg.type = proto_common.Instance.NON_CONFIGURABLE
            for pin in filter(lambda x: x.is_input, itervalues(instance.pins)):
                self.__serialize_port(instmsg.ports.add(), pin, block)

    def __find_bridge(self, array, node, index, global_cfg = 0):
        assert node.is_segment
        pin = array.get_segment(node)
        if pin is None:
            # the spot might be covered by an array
            instance = array.get_root_block(node.position, node.dimension.select(TileType.xchan, TileType.ychan))
            if instance is None or not instance.is_array:
                return None, 0
            else:
                return self.__find_bridge(instance.model, node._replace(position = node.position - instance.position),
                    index, global_cfg + instance._ext["cfg_offset"])
        elif pin.parent.is_array:
            return self.__find_bridge(pin.parent.model, node._replace(position = node.position - pin.parent.position),
                    index, global_cfg + pin.parent._ext["cfg_offset"])
        else:
            block, local_node = pin.parent.model, node._replace(position = node.position - pin.parent.position)
            src_bus = block.bridges.get(local_node, None)
            sink_bus = block.nodes.get(local_node, None)
            if src_bus is None or not src_bus.is_input or sink_bus is None or not sink_bus.is_output:
                return None, 0
            _, path = block.dfs_physical_paths(uno(sink_bus[index].physical_cp, sink_bus[index]),
                    (uno(src_bus[index].physical_cp, src_bus[index]), ))[0]
            if path is None:
                return None, 0
            else:
                return path, global_cfg + pin.parent._ext["cfg_offset"]

    def __process_routing(self, context, block, ds, global_x, global_y, global_cfg):
        for sink in filter(lambda x: x.is_output, chain(itervalues(block.nodes), itervalues(block.bridges))):
            sink_node = sink.node._replace(position = sink.node.position + (global_x, global_y))
            for sink_bit in sink:
                sink_id = calculate_node_id_in_array(context.top, sink_node, sink_bit.index)
                if sink_id is None:
                    _logger.debug("Unable to find node '{}'".format(sink_node))
                    continue
                # is this a bridge?
                brg_path, brg_offset = (self.__find_bridge(context.top, sink_node, sink_bit.index)
                        if sink.is_bridge else (tuple(), 0))
                if brg_path is None:
                    raise PRGAInternalError("Bridge left unconnected: {}"
                            .format(sink_node))
                for src_bit in sink_bit.logical_sources:
                    src_node = src_bit.bus.node._replace(position = src_bit.bus.node.position + (global_x, global_y))
                    # process bridges when driven
                    if (sink_node.is_segment and src_bit.bus.is_bridge and
                            sink_node.origin_equivalent == src_node.origin_equivalent):
                        _logger.debug("Skipping bridge: {}".format(sink_node))
                        continue
                    src_id = calculate_node_id_in_array(context.top, src_node, src_bit.index)
                    if src_id is None:
                        _logger.debug("Unable to find node '{}'".format(src_node))
                        continue
                    with ds.add_edge() as msg:
                        msg.src = src_id
                        msg.sink = sink_id
                        _, path = block.dfs_physical_paths(uno(sink_bit.physical_cp, sink_bit),
                                (uno(src_bit.physical_cp, src_bit), ))[0]
                        if path is None:
                            raise PRGAInternalError("No path from '{}' to '{}'"
                                    .format(src_bit, sink_bit))
                        self.__serialize_path_set_value_actions(
                                msg.action.Extensions[proto_bitchain.Ext.edge_actions], path, global_cfg)
                        self.__serialize_path_set_value_actions(
                                msg.action.Extensions[proto_bitchain.Ext.edge_actions], brg_path, brg_offset)
                        _logger.debug("Serializing edge: {}[{}]{}, {}[{}]{}".format(src_node, src_bit.index,
                            ' (bridge)' if src_bit.bus.is_bridge else '', sink_node, sink_bit.index,
                            ' (bridge)' if sink.is_bridge else ''))
                        _logger.debug(str(msg))

    def __process_array(self, context, array, ds,
            global_x = 0, global_y = 0, global_cfg = 0, global_node = 0):
        for instance in itervalues(array.instances):
            if not instance.is_root:
                continue
            elif instance.is_io_block or instance.is_logic_block:
                # placement
                with ds.add_placement() as msg:
                    msg.x = global_x + instance.position.x
                    msg.y = global_y + instance.position.y
                    msg.subblock = instance.position.subblock
                    if instance.is_physical and instance.model._ext["cfg_bits"] > 0:
                        action = msg.action.Extensions[proto_bitchain.Ext.placement_actions].add()
                        action.offset = global_cfg + instance._ext["cfg_offset"]
                        action.width = instance.model._ext["cfg_bits"]
                        action.begin = 0
                    _logger.debug("Serializing placement:")
                    _logger.debug(str(msg))
                # logical-physical pin edge data
                logical_base = global_node + instance._ext["node_id"]
                physical_base = logical_base + instance.model._ext["num_nodes"]
                for pin in itervalues(instance.pins):
                    for bit in pin:
                        phys_node = physical_base + pin.port._ext["ptc"] + bit.index
                        logi_node = logical_base + pin.port._ext["ptc"] + bit.index
                        with ds.add_edge() as msg:
                            msg.src = phys_node if pin.is_input else logi_node
                            msg.sink = logi_node if pin.is_input else phys_node
            elif instance.is_array:
                self.__process_array(context, instance.model, ds,
                        global_x + instance.position.x, global_y + instance.position.y,
                        global_cfg + instance._ext["cfg_offset"], global_node + instance._ext["node_id"])
            else:
                assert instance.is_routing_block
                self.__process_routing(context, instance.model, ds,
                        global_x + instance.position.x, global_y + instance.position.y,
                        global_cfg + instance._ext["cfg_offset"])

    def run(self, context):
        with _BitchainConfigProtoSerializer(open(self._filename, 'wb' if _py3 else 'w')) as ds:
            with ds.add_header() as header:
                header.signature = 0xaf27dbd3ad76bbdd # first 64 bits of sha1("bitchain")
                header.width = context.top.width
                header.height = context.top.height
                header.node_size = context.top._ext["num_nodes"]
                header.action.Extensions[proto_bitchain.Ext.total_size] = context.top._ext["cfg_bits"]
            # 1. block configuration data
            for block in itervalues(context.blocks):
                with ds.add_block() as msg:
                    self.__serialize_block(msg, block)
            # 2. placement & edge data
            self.__process_array(context, context.top, ds)
