# Python 2 and 3 compatible
from prga.compatible import *

from prga._archdef.common import TileType, Side, SideTuple, BlockType, PortDirection
from prga._archdef.routing.common import Position
from prga._archdef.routing.block import AbstractRoutingBlockOrArray
from prga._archdef.routing.port import (RoutingNodeInputPort, RoutingNodeInputBridge, RoutingNodeOutputPort,
        RoutingNodeOutputBridge)
from prga._archdef.array.instance import BlockInstance, IOBlockInstance, TilePlaceholder
from prga._util.util import uno
from prga.exception import PRGAInternalError

from collections import namedtuple, OrderedDict
from itertools import product, chain

# ----------------------------------------------------------------------------
# -- Routing Channel Coverage ------------------------------------------------
# ----------------------------------------------------------------------------
class RoutingChannelCoverage(SideTuple):
    """A tuple describing if adjacent routing channels are covered."""
    def __new__(cls, top = False, right = False, bottom = False, left = False):
        return super(RoutingChannelCoverage, cls).__new__(cls, top, right, bottom, left)

# ----------------------------------------------------------------------------
# -- Tile --------------------------------------------------------------------
# ----------------------------------------------------------------------------
class Tile(namedtuple('Tile', 'logic xchan ychan switch')):
    """A single tile."""
    def __new__(cls, logic = None, xchan = None, ychan = None, switch = None):
        return super(Tile, cls).__new__(cls, logic, xchan, ychan, switch)

    def __getitem__(self, type_):
        if type_ is TileType.logic:
            return self.logic
        elif type_ is TileType.xchan:
            return self.xchan
        elif type_ is TileType.ychan:
            return self.ychan
        elif type_ is TileType.switch:
            return self.switch
        else:
            return super(Tile, self).__getitem__(type_)

    @property
    def _block_count(self):
        return ((0 if self.logic is None else len(self.logic)) +
                sum(0 if self[type_] is None else 1 for type_ in TileType.all_routing()))

    def replace_routing(self, block):
        if block.tile_type is TileType.xchan:
            return self._replace(xchan = block)
        elif block.tile_type is TileType.ychan:
            return self._replace(ychan = block)
        elif block.tile_type is TileType.switch:
            return self._replace(switch = block)
        else:
            assert False

# ----------------------------------------------------------------------------
# -- Array Ports -------------------------------------------------------------
# ----------------------------------------------------------------------------
class ArrayOutputPort(RoutingNodeOutputPort):
    """Array output ports.

    Args:
        parent (`Array`): the array this port belongs to
        node (`Segment` or `BlockPin`): the routing node this port represents
    """
    @property
    def _default_physical_source(self):
        node = self.parent.get_node_source(self.node, self.is_bridge)
        if node is not None:
            if not node.is_physical_source:
                raise PRGAInternalError("'{}' is not a physical source".format(node))
            else:
                return node
        else:
            return super(AbstractArrayOutputPort, self)._default_physical_source

class ArrayOutputBridge(RoutingNodeOutputBridge, ArrayOutputPort):
    """Array output bridges.

    Args:
        parent (`Array`): the array this port belongs to
        node (`Segment` or `BlockPin`): the routing node this port represents
    """
    pass

# ----------------------------------------------------------------------------
# -- Array Instances Delegate ------------------------------------------------
# ----------------------------------------------------------------------------
class ArrayInstanceDelegate(Mapping):
    """A helper class for `Array._instances` property."""
    def __init__(self, array):
        self.__array = array

    def __getitem__(self, key):
        try:
            pos, type_ = key
            pos = Position(*pos)
            value = self.__array.get_block(pos, type_)
        except (TypeError, ValueError):
            value = self.__array._physical_instances.get(key, None)
        if value is None:
            raise KeyError(key)
        else:
            return value

    def __gen(self):
        """Generator method for ``ArrayInstanceDelegate.__iter__``."""
        # 1. iterate through blocks
        width, height = self.__array._tiles_index(self.__array._width, self.__array._height)
        for x, y, type_ in product(range(width), range(height), TileType.all()):
            block = self.__array._tiles[x][y][type_]
            if block is None:
                continue
            elif type_ is TileType.logic:
                for subblock, _ in enumerate(block):
                    yield (Position(x, y, subblock), type_)
            else:
                yield (Position(x, y), type_)
        # 2. iterate through physical instances
        for key in self.__array._physical_instances:
            yield key

    def __iter__(self):
        return iter(self.__gen())

    def __len__(self):
        return (sum(tile._block_count for col in self.__array._tiles for tile in col) +
                len(self.__array._physical_instances))

# ----------------------------------------------------------------------------
# -- Array -------------------------------------------------------------------
# ----------------------------------------------------------------------------
class Array(AbstractRoutingBlockOrArray):
    """An array of blocks, sub-arrays and routing blocks.

    Args:
        name (:obj:`str`): name of this array
        width (:obj:`int`): width of this array
        height (:obj:`int`): height of this array
        channel_coverage (`RoutingChannelCoverage`): if this array covers the routing channels around it. By default,
            no routing channels around this array are covered
    """
    def __init__(self, name, width, height, channel_coverage = None):
        super(Array, self).__init__(name)
        self._width = width
        self._height = height
        self._coverage = uno(channel_coverage, RoutingChannelCoverage())
        self._physical_instances = OrderedDict()
        width, height = self._tiles_index(width, height)
        self._tiles = [[Tile() for _0 in range(height)] for _1 in range(width)]

    # == internal methods ====================================================
    @property
    def _instances(self):
        return ArrayInstanceDelegate(self)

    def _tiles_index(self, x, y):
        """Converts ``x``, ``y`` to indices into ``Array._tiles``."""
        return (x + 1) if self._coverage[Side.left] else x, (y + 1) if self._coverage[Side.bottom] else y

    def _create_node(self, node, port_direction, is_bridge, is_logical_source):
        assert not is_logical_source
        PortCls = None
        if node.is_blockpin:
            PortCls = port_direction.select(RoutingNodeInputPort, ArrayOutputPort)
        else:
            PortCls = port_direction.select(
                    RoutingNodeInputBridge if is_bridge else RoutingNodeInputPort,
                    ArrayOutputBridge if is_bridge else ArrayOutputPort)
        return PortCls(self, node)

    # == low-level API =======================================================
    @property
    def block_type(self):
        """Type of this block."""
        return BlockType.array

    @property
    def width(self):
        """The width of this array."""
        return self._width

    @property
    def height(self):
        """The height of this array."""
        return self._height

    @property
    def channel_coverage(self):
        """The coverage of routing channels around this array."""
        return self._coverage

    def covers_tile(self, x, y, type_):
        coverage = self.channel_coverage
        xok = (0 <= x < self.width - 1 or
                ((x == -1) and type_ in (TileType.switch, TileType.ychan) and coverage[Side.left]) or
                ((x == self.width - 1) and (type_ in (TileType.logic, TileType.xchan) or coverage[Side.right])))
        yok = (0 <= y < self.height - 1 or
                ((y == -1) and type_ in (TileType.switch, TileType.xchan) and coverage[Side.bottom]) or
                ((y == self.height - 1) and (type_ in (TileType.logic, TileType.ychan) or coverage[Side.top])))
        return xok and yok

    # -- block instance API --------------------------------------------------
    def get_block(self, position, type_):
        """Get the ``type`` block at ``position``. Returns ``None`` if no block found, or the given parameters are
        invalid."""
        if not self.covers_tile(position.x, position.y, type_):
            return None
        x, y = self._tiles_index(position.x, position.y)
        block = self._tiles[x][y][type_]
        if block is not None and type_ is TileType.logic:
            return block[position.subblock]
        else:
            return block

    def get_root_block(self, position, type_):
        """Get the physical root block for ``type`` block at ``position``. Returns ``None`` if no block found, or the
        given parameters are invalid."""
        block = self.get_block(position, type_)
        if block is None:
            return None
        elif block.is_root:
            return block if block.is_physical else None
        else:
            block = self.get_block(Position(position.x - block.xoffset, position.y - block.yoffset), TileType.logic)
            assert block.is_root
            return block

    def add_block(self, block, x, y):
        """Add instance of ``block`` at tile \\(``x``, ``y``\\).

        Args:
            block (`AbstractBlock`):
            x (:obj:`int`): the X-dimensional position in the array
            y (:obj:`int`): the Y-dimensional position in the array
        """
        # 1. place root tile
        # 1.1 validate position
        if not self.covers_tile(x, y, block.tile_type):
            raise PRGAInternalError(
                    "Invalid {} tile at ({}, {}) in array '{}' when placing block '{}' at ({}, {})"
                    .format(block.tile_type.name, x, y, self, block, x, y))
        # 1.2 check confliction
        instance = self.get_root_block(Position(x, y), block.tile_type)
        if instance is not None:
            raise PRGAInternalError(
                    "Conflicting block '{}' at tile ({}, {}) in array '{}' when placing block '{}' at ({}, {})"
                    .format(instance.model, instance.position.x, instance.position.y, self, block, x, y))
        # 1.3 place block
        xx, yy = self._tiles_index(x, y)
        if block.is_routing_block:
            self._tiles[xx][yy] = self._tiles[xx][yy].replace_routing(BlockInstance(self, block, Position(x, y)))
            return
        elif block.is_io_block:
            self._tiles[xx][yy] = self._tiles[xx][yy]._replace(logic =
                    tuple(IOBlockInstance(self, block, Position(x, y, subblock)) for subblock in range(block.capacity)))
        else:
            self._tiles[xx][yy] = self._tiles[xx][yy]._replace(logic =
                    tuple(BlockInstance(self, block, Position(x, y, subblock)) for subblock in range(block.capacity)))
        # 2. place placeholders
        for xx, yy, type_ in product(range(-1, block.width), range(-1, block.height), TileType.all()):
            if (xx == 0 and yy == 0 and type_ is TileType.logic) or not block.covers_tile(xx, yy, type_):
                continue
            pos = Position(x + xx, y + yy)
            # 2.1 validate position
            if not self.covers_tile(pos.x, pos.y, type_):
                raise PRGAInternalError(
                        "Invalid {} tile at ({}, {}) in array '{}' when placing block '{}' at ({}, {})"
                        .format(type_.name, pos.x, pos.y, self, block, x, y))
            # 2.2 check confliction
            instance = self.get_root_block(pos, type_)
            if instance is not None:
                raise PRGAInternalError(
                        "Conflicting block '{}' at tile ({}, {}) in array '{}' when placing block '{}' at ({}, {})"
                        .format(instance.model, instance.position.x, instance.position.y, self, block, x, y))
            # 2.3 place placeholder
            xi, yi = self._tiles_index(pos.x, pos.y)
            if type_ is TileType.logic:
                self._tiles[xi][yi] = self._tiles[xi][yi]._replace(logic =
                        (TilePlaceholder(self, block, pos, type_, xx, yy), ))
            else:
                self._tiles[xi][yi] = self._tiles[xi][yi].replace_routing(
                        TilePlaceholder(self, block, pos, type_, xx, yy))

    # -- routing node API ----------------------------------------------------
    def get_blockpin(self, node, error_if_not_found = False):
        """Get the endpoint port/pin for ``node``."""
        assert node.is_blockpin
        # 1. find the block
        block = self.get_root_block(node.position, TileType.logic)
        if block is None: # no block in the position
            if error_if_not_found:
                raise PRGAInternalError(("No logic block found at tile ({}, {}) in array '{}' "
                    "when searching for node '{}'").format(node.position.x, node.position.y, self, node))
            else:
                return None
        # 2. find node
        pin = block.nodes.get(node._replace(position = node.position - block.position), None)
        if pin is None:
            if error_if_not_found:
                raise PRGAInternalError("Node '{}' not found from block '{}' in array '{}'"
                        .format(node, block, self))
            else:
                return None
        return pin

    def get_segment(self, node, is_bridge = False, error_if_not_found = False):
        """Get the segment source node for ``node``."""
        assert node.is_segment
        # 1. check if ``node`` is driven by the switch-block ahead of it
        switch = self.get_root_block(node.position - node.direction.select(
            (0, 0), node.dimension.select((1, 0), (0, 1))), TileType.switch)
        if switch is not None:
            pin = (switch.bridges if is_bridge else switch.nodes).get(
                    node._replace(position = node.position - switch.position), None)
            if pin is not None and pin.is_source:
                return pin
        for equiv in chain(iter((node, )), node.iter_prev_equivalents()):
            # 2. find other blocks that may drive ``node``
            conn = self.get_root_block(equiv.position, node.dimension.select(TileType.xchan, TileType.ychan))
            switch = self.get_root_block(equiv.position - equiv.direction.select(
                equiv.dimension.select((1, 0), (0, 1)), (0, 0)), TileType.switch)
            # 3. check if any block drives ``node``
            for block in (conn, switch):
                if block is None:
                    continue
                pin = (block.bridges if is_bridge else block.nodes).get(
                        equiv._replace(position = equiv.position - block.position), None)
                if pin is not None and pin.is_source:
                    return pin
        if error_if_not_found:
            raise PRGAInternalError("{} '{}' not found in array '{}'"
                    .format("Bridge node" if is_bridge else "Node", node, self))
        else:
            return None

    def get_node_source(self, node, is_bridge = False):
        """Get the source port/pin for ``node``."""
        assert not (node.is_blockpin and is_bridge)
        # 1. check `nodes` or `bridges` to see if `node` is connected to outside this array
        port = (self.bridges if is_bridge else self.nodes).get(node, None)
        if port and port.is_source:
            return port
        # 2. if node is a segment
        if node.is_segment:
            return self.get_segment(node, is_bridge)
        assert node.is_blockpin
        # 3. if node is a block pin
        # 3.1 if node is an output
        if node.prototype.is_output:
            return self.get_blockpin(node)
        # 3.2 a bit more complicated if `node` is an input
        #   TODO: if `node` is directly connected to another block pin
        # 3.2.1 find the connection/routing block
        type_ = TileType.ychan if node.prototype.side in (Side.left, Side.right) else TileType.xchan
        pos = node.position - ((1, 0) if node.prototype.side is Side.left else
                (0, 1) if node.prototype.side is Side.bottom else (0, 0))
        block = self.get_root_block(pos, type_)
        if block is None: # no block in the position
            return None
        # 3.2.2 find node
        pin = block.nodes.get(node._replace(position = node.position - block.position), None)
        if pin is None:
            return None
        # 3.3 verify it is a source
        assert pin.is_source
        return pin

    def auto_complete_ports(self, external_only = True, use_combined_routing_block = False):
        """Automatically create and add ports for routing nodes and bridges into and out from this array."""
        # iterate through all block instances
        for block in itervalues(self.physical_instances):
            # create and connect external ports
            for pin in filter(lambda x: x.is_external, itervalues(block.physical_pins)):
                if pin.is_input:
                    pin.physical_source = self.get_or_create_physical_input('{}_{}'.format(block.name, pin.name),
                            pin.width, is_external = True)
                else:
                    self.get_or_create_physical_output('{}_{}'.format(block.name, pin.name),
                            pin.width, is_external = True).physical_source = pin
        if external_only:
            return
        # iterate through all block instances
        for block in itervalues(self.physical_instances):
            # iterate through all nodes and bridges
            for pin in chain(itervalues(block.nodes), itervalues(block.bridges)):
                if pin.is_sink: # for sinks, check if the corresponding sources are already present
                    source = self.get_node_source(pin.node, pin.is_bridge)
                    if source is not None: # the corresponding source is already present
                        continue
                if pin.node.is_blockpin: # for block pins, check if they are at the edges of the array
                    if pin.is_global:
                        continue
                    if ( (pin.node.prototype.side is Side.left and pin.node.position.x == 0 and
                        not self.covers_tile(-1, pin.node.position.y, TileType.ychan)) or
                        (pin.node.prototype.side is Side.top and pin.node.position.y == self.height - 1 and
                            not self.covers_tile(pin.node.position.x, pin.node.position.y, TileType.xchan)) or
                        (pin.node.prototype.side is Side.right and pin.node.position.x == self.width - 1 and
                            not self.covers_tile(pin.node.position.x, pin.node.position.y, TileType.ychan)) or
                        (pin.node.prototype.side is Side.bottom and pin.node.position.y == 0 and
                            not self.covers_tile(pin.node.position.x, -1, TileType.xchan)) ):
                        self._get_or_create_node(pin.node, pin.direction)
                elif pin.is_sink:   # segment sink
                    # check if the source of this node could be outside this array
                    sec = pin.node.position.section # short alias
                    reach = pin.node.position + pin.node.direction.select(
                            pin.node.dimension.select((-1 - sec, 0), (0, -1 - sec)),
                            pin.node.dimension.select((     sec, 0), (0,      sec)))
                    if not self.covers_tile(reach.x, reach.y, TileType.switch):
                        self._get_or_create_node(pin.node, PortDirection.input, pin.is_bridge)
                elif pin.is_bridge:     # process segment bridge sources later
                    continue
                else: # for segments, check if they expand to outside or the edges of the array
                    diff = pin.node.prototype.length - 1 - pin.node.position.section # short alias
                    reach = pin.node.position + pin.node.direction.select(
                            pin.node.dimension.select((     diff, 0), (0,      diff)),
                            pin.node.dimension.select((-1 - diff, 0), (0, -1 - diff)))
                    if use_combined_routing_block: # expose more
                        if not (self.covers_tile(    reach.x,     reach.y, TileType.xchan) and
                                self.covers_tile(    reach.x,     reach.y, TileType.ychan) and
                                self.covers_tile(    reach.x, 1 + reach.y, TileType.ychan) and
                                self.covers_tile(1 + reach.x,     reach.y, TileType.xchan)):
                            self._get_or_create_node(pin.node, PortDirection.output)
                    elif not self.covers_tile(reach.x, reach.y, TileType.switch):
                        self._get_or_create_node(pin.node, PortDirection.output)
        # iterate through all block instances and bridges
        for block in itervalues(self.physical_instances):
            for pin in itervalues(block.bridges):
                if not pin.is_source or self._get_node(pin.node, PortDirection.output):
                    continue    # node already created
                diff = pin.node.prototype.length - 1 - pin.node.position.section # short alias
                reach = pin.node.position + pin.node.direction.select(
                        pin.node.dimension.select((     diff, 0), (0,      diff)),
                        pin.node.dimension.select((-1 - diff, 0), (0, -1 - diff)))
                if not self.covers_tile(reach.x, reach.y, TileType.switch):
                    self._get_or_create_node(pin.node, PortDirection.output, True)
