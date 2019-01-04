# -*- encoding: ascii -*-

"""Bit-chain-style Configuration circuitry protobuf message serializer."""

__all__ = ['BitchainConfigProtoSerializer']

from .proto.common_pb2 import Header, Instance, Packet
from .proto.bitchain_pb2 import SetValueAction, CopyValueAction, Ext
from ..common import AbstractConfigProtoSerializer
from ..._archdef.portpin.common import ConstNet
from ..._archdef.portpin.reference import NetBundle
from ..._archdef.routing.resource import SegmentReference
from ..._archdef.common import SegmentDirection, Dimension, PortDirection, NetType
from ..._context.flow import AbstractPass
from ...exception import PRGAInternalError
from ..._util.util import uno

import itertools

# ----------------------------------------------------------------------------
# -- _BitchainConfigProtoSerializer ------------------------------------------
# ----------------------------------------------------------------------------
class _BitchainConfigProtoSerializer(AbstractConfigProtoSerializer):
    def _new_header(self):
        """Create a new ``Header`` object."""
        return Header()

    def _new_packet(self):
        """Create a new ``Packet`` object."""
        return Packet()

# ----------------------------------------------------------------------------
# -- BitchainConfigProtoSerializer -------------------------------------------
# ----------------------------------------------------------------------------
class BitchainConfigProtoSerializer(AbstractPass):
    """Bitchain style configuration circuitry protobuf message serializer.
    
    Args:
        f (file-like object): the output stream
    """
    def __init__(self, f):
        self._f = f

    @property
    def key(self):
        """Key of this pass."""
        return "config.proto.bitchain"

    @property
    def dependences(self):
        """Passes that this pass depends on."""
        return ("vpr", "config.circuitry.bitchain")

    def __bit_name_with_parent(self, bit):
        if bit.is_port:
            return bit.parent_module.name + '.' + bit.name
        else:
            return bit.parent_instance.name + '[0].' + bit.name

    def __serialize_set_value_actions(self, msglist, bundle, value, offset = 0):
        """Serialize a list of ``SetValueAction``

        Args:
            msglist: the protobuf repeated field of type ``SetValueAction``
            bundle (:obj:`list` [`NetBundle` ]): bundled nets
            value (:obj:`int`): the value to be serialized
            offset (:obj:`int`, default=0): additional offset added on top of the slice offset
        """
        for slice_ in bundle:
            msg = msglist.add()
            msg.offset = offset + slice_.low
            msg.width = slice_.high - slice_.low + 1
            msg.value = value & ((1 << msg.width) - 1)
            value = value >> msg.width

    def __serialize_copy_value_actions(self, msglist, bundle):
        """Serialize a list of ``CopyValueAction``

        Args:
            msglist: the protobuf repeated field of type ``CopyValueAction``
            bundle (:obj:`list` [`NetBundle` ]): bundled nets
        """
        begin = 0
        for slice_ in bundle:
            msg = msglist.add()
            msg.offset = slice_.low
            msg.width = slice_.high - slice_.low + 1
            msg.begin = begin
            begin += msg.width

    def __serialize_path_actions(self, msglist, path, offset = 0):
        """Serialize a list of ``SetValueAction`` for a mux-input path

        Args:
            msglist: the protobuf repeated field of type ``SetValueAction``
            path (:obj:`list` [`PortOrPinBit` ]): a list of mux input bits
            offset (:obj:`int`, default=0): additional offset added on top of the slice offset
        """
        for muxbit in path:
            bundle = NetBundle._Bundle(muxbit.parent_instance._pins['cfg_d']._physical_source)
            self.__serialize_set_value_actions(msglist, bundle, muxbit.index, offset)

    def __serialize_port(self, msg, port, block):
        """Serialize the configuration circuitry data of the given ``port`` into the protobuf message ``msg``.

        Args:
            msg (``Port``): the protobuf message
            port (`LogicBlockOutputPort` or `IOBlockOutputPort` or `Pin`): the port/pin
        """
        # 1. basic information
        msg.name = port.name
        # 2. iterate through bits
        for sink in port:
            # 2.1 create a new bit message
            bitmsg = msg.bits.add()
            # 2.2 find all logical source bits and the physical paths implementing these logical connections
            open_handled = False
            for source, path in block._dfs_physical_paths(sink._physical_cp._physical_source,
                    tuple(x._physical_cp for x in sink._logical_sources) +
                    (ConstNet(NetType.open), ConstNet(NetType.zero), ConstNet(NetType.one))):
                if source.is_const or source.is_open:
                    if path is None:
                        continue
                    elif open_handled:
                        raise PRGAInternalError("'{}' has multiple connections that may implement 'open' in VPR"
                                .format(sink))
                    connmsg = bitmsg.connections.add()
                    connmsg.input = 'open'
                    self.__serialize_path_actions(connmsg.action.Extensions[Ext.connection_actions], path)
                elif path is None:
                    raise PRGAInternalError("No path from '{}' to '{}'"
                            .format(source._logical_cp, sink))
                else:
                    connmsg = bitmsg.connections.add()
                    connmsg.input = self.__bit_name_with_parent(source._logical_cp)
                    self.__serialize_path_actions(connmsg.action.Extensions[Ext.connection_actions], path)

    def __serialize_block(self, msg, block):
        """Serialize the configuration circuitry data of the given ``block`` into the protobuf message ``msg``.

        Args:
            msg (``Block``): the protobuf message
            block (`LogicBlock` or `IOBlock`): the block
        """
        # 1. basic information
        msg.name = block.name
        try:
            msg.action.Extensions[Ext.config_size] = block._instances['cfg_btc_inst']._pins['d'].width
        except KeyError:
            msg.action.Extensions[Ext.config_size] = 0
        # 2. output ports
        for port in itertools.ifilter(lambda x: x.is_output, block.ports.itervalues()):
            portmsg = msg.ports.add()
            self.__serialize_port(portmsg, port, block)
        # 3. sub-instances
        for instance in block.instances.itervalues():
            # 3.1 create a new instance message
            instmsg = msg.instances.add()
            # 3.2 basic information
            instmsg.name = instance.name
            # 3.3 pins
            for pin in itertools.ifilter(lambda x: x.is_input, instance.pins.itervalues()):
                pinmsg = instmsg.ports.add()
                self.__serialize_port(pinmsg, pin, block)
            # 3.4 additional information
            if instance.is_lut:
                instmsg.type = Instance.LUT
                bundle = NetBundle._Bundle(instance._pins['cfg_d']._physical_source)
                self.__serialize_copy_value_actions(instmsg.action.Extensions[Ext.lut_actions], bundle)
            elif instance.is_iopad:
                instmsg.type = Instance.MULTIMODE
                bundle = NetBundle._Bundle(block._ports['extio_oe']._physical_source)
                for name, sel in ( ('extio_i', 0), ('extio_o', 1) ):
                    modemsg = instmsg.modes.add()
                    modemsg.name = name
                    self.__serialize_set_value_actions(modemsg.action.Extensions[Ext.mode_actions],
                        bundle, sel)
            else:
                instmsg.type = Instance.CUSTOM

    def run(self, context):
        vpr_ext, cfg_ext = context._vpr_extension, context._config_extension
        with _BitchainConfigProtoSerializer(self._f) as ds:
            with ds.add_header() as header:
                header.signature = 0xaf27dbd3ad76bbdd # first 64 bits of sha1("bitchain")
                header.width = context.array.width
                header.height = context.array.height
                header.node_size = vpr_ext.node_size
                header.action.Extensions[Ext.total_size] = cfg_ext._bitstream_size
            # 1. block configuration data
            for block in context.blocks.itervalues():
                with ds.add_block() as msg:
                    self.__serialize_block(msg, block)
            for tile in context.array._iter_tiles():
                # 2. placement configuration data
                if tile.is_root and tile.block is not None:
                    cfginst = tile.block._instances.get('cfg_btc_inst', None)
                    for subblock, instance in enumerate(tile.block_instances):
                        with ds.add_placement() as msg:
                            msg.x = tile.x
                            msg.y = tile.y
                            msg.subblock = subblock
                            if instance.is_physical and cfginst is not None:
                                action = msg.action.Extensions[Ext.placement_actions].add()
                                action.offset = cfg_ext.array[tile.x][tile.y].blocks[subblock]
                                action.width = len(cfginst._pins['d'])
                                action.begin = 0
                        # 3. logical-physical pin edge data
                        for pin in instance.pins.itervalues():
                            for i in xrange(pin.width):
                                physical = vpr_ext.get_node_id(pin, i, physical=True)
                                logical = vpr_ext.get_node_id(pin, i, physical=False)
                                with ds.add_edge() as msg:
                                    msg.src = physical if pin.is_input else logical
                                    msg.sink = logical if pin.is_input else physical
                # 4. pin-pin/pin-segment/segment-pin/segment-segment edge data
                for instance, offset in ( (tile.hconn_instance, cfg_ext.array[tile.x][tile.y].hconn),
                        (tile.vconn_instance, cfg_ext.array[tile.x][tile.y].vconn),
                        (tile.switch_instance, cfg_ext.array[tile.x][tile.y].switch) ):
                    if instance is None:
                        continue
                    for sink in itertools.ifilter(lambda x: x.is_output, instance.pins.itervalues()):
                        sink_node = context.array._dereference_routing_node_from_pin(sink)
                        if sink_node is None:
                            continue
                        # if this is a switchblock, find the connection block pin that's driving the same segment
                        conn_sink = (None if not instance.is_switch_block else
                            context.array._find_connection_block_pin_driving_segment(sink_node))
                        for sink_index in xrange(sink.width):
                            sink_bit = sink.port[sink_index]
                            sink_id = vpr_ext.get_node_id(sink_node, sink_index)
                            # if this is a switchblock and another connection block is driving the same segment, find
                            # the path in the connection block, too
                            conn_path, conn_offset = [], 0
                            if conn_sink is not None:
                                conn = conn_sink.parent_instance.block
                                psrc = conn._nodes[sink.port.node_reference, PortDirection.input][sink_index]
                                psink = psrc._physical_cp
                                _, conn_path = conn_sink.parent_instance.block._dfs_physical_paths(
                                        psink, (psrc, ))[0]
                                if sink_node.dimension is Dimension.horizontal:
                                    conn_offset = cfg_ext.array[conn_sink.x][conn_sink.y].hconn
                                else:
                                    conn_offset = cfg_ext.array[conn_sink.x][conn_sink.y].vconn
                            for src_bit, path in instance.block._dfs_physical_paths(
                                    sink_bit._physical_cp._physical_source,
                                    tuple(x._physical_cp for x in sink_bit._logical_sources)):
                                if path is None:
                                    raise PRGAInternalError("No physical path fomr '{}' to '{}'"
                                            .format(src_bit._logical_cp, sink_bit))
                                src_bit = src_bit._logical_cp
                                # if src_bit.is_const or src_bit.is_open:
                                #     continue    # TODO: support block pin tie-high/tie-low
                                if (not instance.is_switch_block and
                                        src_bit.parent.node_reference == sink.port.node_reference):
                                    continue    # routing segment bridge will be processed in switch blocks
                                src, src_index = instance.pins[src_bit.parent.name], src_bit.index
                                src_node = context.array._dereference_routing_node_from_pin(src)
                                if src_node is None:
                                    continue
                                src_id = vpr_ext.get_node_id(src_node, src_index)
                                with ds.add_edge() as msg:
                                    msg.src = src_id
                                    msg.sink = sink_id
                                    self.__serialize_path_actions(msg.action.Extensions[Ext.edge_actions],
                                        path, offset)
                                    self.__serialize_path_actions(msg.action.Extensions[Ext.edge_actions],
                                        conn_path, conn_offset)
