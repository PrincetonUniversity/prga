# Python 2 and 3 compatible
from prga.compatible import *

from prga._archdef.common import TileType
from prga._archdef.routing.common import Position
from prga._context.flow import AbstractPass
from prga._util.util import register_extension
from prga.exception import PRGAInternalError

from itertools import product

register_extension("node_id", __name__)
register_extension("ptc", __name__)
register_extension("num_nodes", __name__)
register_extension("channel_width", __name__)
register_extension("segment_id", __name__)
register_extension("block_type_id", __name__)

# ----------------------------------------------------------------------------
# -- VPR ID Assignment -------------------------------------------------------
# ----------------------------------------------------------------------------
class VPRIDGenerator(AbstractPass):
    """VPR's ID assigment."""
    @property
    def key(self):
        """Key of this pass."""
        return "vpr.id"

    def __process_routing(self, block):
        if "num_nodes" in block._ext:
            return
        id_ = 0
        for node in filter(lambda node: node.is_segment and node.is_output,
                itervalues(block.nodes)):
            node._ext["node_id"] = id_
            id_ += node.width
        block._ext["num_nodes"] = id_

    def __process_array(self, array):
        if "num_nodes" in array._ext:
            return
        id_ = 0
        for x, y, type_ in product(range(-1, array.width), range(-1, array.height), TileType.all()):
            block = array.get_block(Position(x, y), type_)
            if block is None or not block.is_root:
                continue
            for subblock in range(block.model.capacity):
                instance = block if subblock == 0 else array.get_block(Position(x, y, subblock), type_)
                if instance.is_io_block or instance.is_logic_block:
                    instance._ext["node_id"] = id_
                    id_ += 2 * instance.model._ext["num_nodes"]
                else:
                    if instance.is_array:
                        self.__process_array(instance.model)
                    elif instance.is_routing_block:
                        self.__process_routing(instance.model)
                    instance._ext["node_id"] = id_
                    id_ += instance.model._ext["num_nodes"]
        array._ext["num_nodes"] = id_

    def run(self, context):
        # 1. validate
        if context.top is None:
            raise PRGAInternalError("No top-level array pointed")
        # 2. assign segment ID & ptc
        ptc = 0
        for id_, segment in enumerate(itervalues(context.segments)):
            segment._ext["segment_id"] = id_
            segment._ext["ptc"] = ptc
            ptc += 2 * segment.width * segment.length
        context._ext["channel_width"] = ptc
        # 3. assign block id & ptc
        for id_, block in enumerate(itervalues(context.blocks)):
            block._ext["block_type_id"] = id_ + 1
            block.reorder_ports()
            ptc = 0
            for port in itervalues(block.ports):
                port._ext["ptc"] = ptc
                ptc += port.width
            block._ext["num_nodes"] = ptc
        # 4. assign node id
        self.__process_array(context.top)

# ----------------------------------------------------------------------------
# -- Helper Functions --------------------------------------------------------
# ----------------------------------------------------------------------------
def calculate_node_id_in_array(array, node, index, base_id = 0, is_logical_node = False):
    """Calculate the node ID of ``node`` in ``array``.

    Args:
        array (`Array`):
        node (`BlockPin` or `Segment`):
        index (:obj:`int`):
        base_id (:obj:`int`):
        is_logical_node (:obj:`bool`):
    """
    pin = array.get_segment(node) if node.is_segment else array.get_blockpin(node)
    if pin is None:
        # the spot might be covered by an array
        instance = array.get_root_block(node.position,
                TileType.logic if node.is_blockpin else node.dimension.select(TileType.xchan, TileType.ychan))
        if instance is None or not instance.is_array:
            return None
        else:
            return calculate_node_id_in_array(instance.model,
                node._replace(position = node.position - instance.position),
                index, base_id + instance._ext["node_id"])
    elif pin.parent.is_array:
        return calculate_node_id_in_array(pin.parent.model,
                node._replace(position = node.position - pin.parent.position),
                index, base_id + pin.parent._ext['node_id'])
    elif node.is_blockpin:
        return (base_id + pin.parent._ext["node_id"] + pin.port._ext["ptc"] + index +
                (pin.parent.model._ext["num_nodes"] if not is_logical_node else 0))
    else:
        return base_id + pin.parent._ext["node_id"] + pin.port._ext["node_id"] + index
