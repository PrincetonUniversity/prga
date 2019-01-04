# -*- encoding: ascii -*-

"""Top-level module for the FPGA."""

__all__ = ['Array']

from tile import Tile
from ..common import ModuleType, Dimension, PortDirection, SegmentDirection
from ..routing.resource import SegmentReference, SegmentNode
from ..portpin.common import ConstNet, NetType
from ..portpin.port import PhysicalInputPort, PhysicalOutputPort
from ..moduleinstance.module import MutableNonLeafModule
from ..._util.util import uno, DictProxy
from ...exception import PRGAInternalError, PRGAAPIError

from itertools import product
from collections import OrderedDict, Mapping

# ----------------------------------------------------------------------------
# -- Array -------------------------------------------------------------------
# ----------------------------------------------------------------------------
class Array(MutableNonLeafModule):
    """The top-level module containing the 2D array of tiles.

    Args:
        context (`ArchitectureContext`): the architecture context this array belongs to
        name (:obj:`str`): name of the top-level module
        width, height (:obj:`int`): size of the array

    Notes:
        ``_instances`` attribute of an `Array` object should only be used for non-block top-level instances, and be
        careful of naming conflicts.
    """
    def __init__(self, context, name, width, height):
        super(Array, self).__init__(context, name)
        self.__width = width
        self.__height = height
        self.__array = [[Tile(x, y) for y in xrange(height)] for x in xrange(width)]
        self.__globals = {}

    # -- internal API --------------------------------------------------------
    @property
    def type(self):
        """Type of this module."""
        return ModuleType.array

    @property
    def _array(self):
        """The actual array of blocks."""
        return self.__array

    @property
    def _globals(self):
        """Mapping from global wire names to block output pins or array input ports."""
        return self.__globals

    def _iter_tiles(self):
        """Returns an iterator over all tiles."""
        return iter(tile for col in self.__array for tile in col)

    @property
    def is_physical(self):
        """Test if this is a physical module."""
        return True

    def _get_tile(self, x, y):
        """Get the tile at the given position.

        Args:
            x, y (:obj:`int`):

        Returns:
            `Tile` or None: the tile at the given position

        It's OK to pass in values that are beyond the size of the array, e.g. negative x/y, positive x/y larger than
        the width/height of the array, etc. In this case, None will be returned.
        """
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return None
        else:
            return self.__array[x][y]

    def _get_root_tile(self, x, y):
        """Get the root tile at the given position.

        Args:
            x, y (:obj:`int`):

        Returns:
            tile (`Tile`): the root tile at the given position

        Raises:
            `PRGAInternalError`: if the position is beyond the size of the array, or there is no root tile at the
                given position 

        Different with `_get_tile`, invalid position values will cause this method to throw exceptions.
        """
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            raise PRGAInternalError("({}, {}) is beyond the array ({} x {})"
                    .format(x, y, self.width, self.height))
        tile = self.__array[x][y]
        if tile.is_root:
            return tile
        xx, yy = x - tile.xoffset, y - tile.yoffset
        tile = self._get_tile(xx, yy)
        if tile is None or not tile.is_root:
            raise PRGAInternalError("Tile({}, {}) is a dummy tile whose root should be at ({}, {}) but is not there"
                    .format(x, y, xx, yy))
        return tile

    def _dereference_blockpin(self, x, y, ref, permanent = False):
        """Dereference a block pin reference.

        Args:
            x, y (:obj:`int`): the absolute position that ``ref`` is relative to
            ref (`BlockPinReference`): the reference
            permanent (:obj:`bool`, default=False): if the returned pin must be permanent

        Returns:
            `BlockPin`: the dereferenced node.
        """
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            raise PRGAInternalError("({}, {}) is beyond the array ({} x {})"
                    .format(x, y, self.width, self.height))
        x_root, y_root = x + ref.xoffset, y + ref.yoffset
        tile = self._get_tile(x_root, y_root)
        if tile is None or not tile.is_root or tile.block is None or tile.block.name != ref.block:
            return None
        try:
            instance = tile.block_instances[ref.subblock]
        except IndexError:
            raise PRGAInternalError("Sub-block '{}' exceeds logic/io block '{}' capacity '{}'"
                    ,format(ref.subblock, ref.block, tile.block.capacity))
        return instance._get_or_create_pin(ref.port, permanent)

    def _dereference_segment(self, x, y, ref):
        """Dereference a segment reference.

        Args:
            x, y (:obj:`int`): the absolute position that ``ref`` is relative to
            ref (`SegmentReference`): the reference

        Returns:
            `SegmentNode`: the dereferenced node
        """
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            raise PRGAInternalError("({}, {}) is beyond the array ({} x {})"
                    .format(x, y, self.width, self.height))
        x_orig, y_orig, section = x, y, ref.section
        try:
            prototype = self._context.segments[ref.name]
        except KeyError:
            raise PRGAInternalError("Segment '{}' does not exist in architecture context '{}'"
                    .format(ref.name, self._context.name))
        if ref.dimension is Dimension.horizontal:
            if ref.direction is SegmentDirection.inc:
                section = max(0, ref.section - self.__array[x][y].space_decx)
                x_orig, y_orig = x - ref.section + section, y
            else:
                section = max(0, ref.section - self.__array[x][y].space_incx)
                x_orig, y_orig = x + ref.section - section, y
            tile = self._get_tile(x_orig, y_orig)
            if tile is None or not tile.is_top_edge:
                return None
        else:
            if ref.direction is SegmentDirection.inc:
                section = max(0, ref.section - self.__array[x][y].space_decy)
                x_orig, y_orig = x, y - ref.section + section
            else:
                section = max(0, ref.section - self.__array[x][y].space_incy)
                x_orig, y_orig = x, y + ref.section - section
            tile = self._get_tile(x_orig, y_orig)
            if tile is None or not tile.is_right_edge:
                return None
        return SegmentNode(prototype, x_orig, y_orig, ref.dimension, ref.direction, section)

    def _dereference_routing_node(self, x, y, ref):
        """Dereference a routing node.

        Args:
            x, y (:obj:`int`): the absolute position that ``ref`` is relative to
            ref (`SegmentReference` or `BlockPinReference`): the reference

        Returns:
            `SegmentNode` or `BlockPin`: the dereferenced node.
        """
        if ref.is_blockpin:
            return self._dereference_blockpin(x, y, ref)
        else:
            return self._dereference_segment(x, y, ref)

    def _dereference_routing_node_from_pin(self, pin):
        """Dereference the ``node_reference`` of the given ``pin``.

        Args:
            pin (`BlockPin`): the pin of a routing block instance

        Returns:
            `SegmentNode` or `BlockPin`
        """
        try:
            node = pin.port.node_reference
        except AttributeError:
            raise PRGAInternalError("Pin '{}' is not a logical routing block pin"
                    .format(pin))
        if ( node.is_blockpin or not pin.parent_instance.is_switch_block or
                (pin.is_input and node.direction is SegmentDirection.inc) or
                (pin.is_output and node.direction is SegmentDirection.dec) ):
            return self._dereference_routing_node(pin.x, pin.y, node)
        elif node.dimension is Dimension.horizontal:
            return self._dereference_routing_node(pin.x + 1, pin.y, node)
        else:
            return self._dereference_routing_node(pin.x, pin.y + 1, node)

    def _find_switch_block_pin_driving_segment(self, segment, permanent = False):
        """Find the switch block pin (if any) driving the given segment.

        Args:
            segment (`SegmentNode`):
            permanent (:obj:`bool`, default=False): if the returned pin must be permanent

        Returns:
            `BlockPin`:
        """
        prototype, x, y, dimension, direction, section = segment
        tile = (self._get_tile(x, y) if direction is SegmentDirection.dec else
                self._get_tile(x - 1, y) if dimension is Dimension.horizontal else
                self._get_tile(x, y - 1))
        if tile is None or tile.switch is None:
            return None
        port = tile.switch._nodes.get( (SegmentReference(prototype.name, dimension, direction, section),
            PortDirection.output), None)
        if port is None:
            return None
        return tile.switch_instance._get_or_create_pin(port.name, permanent)

    def _find_connection_block_pin_driving_segment(self, segment, permanent = False):
        """Find the connection block pin (if any) driving the given segment.

        Args:
            segment (`SegmentNode`):
            permanent (:obj:`bool`, default=False): if the returned pin must be permanent

        Returns:
            `BlockPin`:
        """
        prototype, x, y, dimension, direction, section = segment
        tile = self._get_tile(x, y)
        if tile is None:
            return None
        instance = tile.hconn_instance if dimension is Dimension.horizontal else tile.vconn_instance
        if instance is None:
            return None
        port = instance.model._nodes.get( (SegmentReference(prototype.name, dimension, direction, section),
            PortDirection.output), None)
        if port is None:
            return None
        return instance._get_or_create_pin(port.name, permanent)

    def _is_bridge_needed(self, segment):
        """Checks if a routing bridge is needed for the segment at the given position.

        Args:
            segment (`SegmentNode`):
        """
        return (self._find_switch_block_pin_driving_segment(segment) is not None and
                self._find_connection_block_pin_driving_segment(segment) is not None)

    def _get_or_create_physical_input(self, name, width, is_global = False):
        """Get or create physical input port with the given name & width.

        Args:
            name (:obj:`str`):
            width (:obj:`int`):
            is_global (:obj:`bool`, default=False): if the created input is a global wire

        Returns:
            `PhysicalInputPort`:

        Raises:
            `PRGAInternalError`: if a port with the given name already exists but the width does not match
        """
        port = self._ports.get(name, None)
        if port is not None:
            if not (port.is_input and port.width == width):
                raise PRGAInternalError("Port '{}' is not a {}-bit physical input"
                        .format(name, width))
        else:
            port = self._ports[name] = PhysicalInputPort(self, name, width)
        if is_global and name not in self.__globals:
            self.__globals[name] = port
        return port

    def _get_or_create_physical_output(self, name, width):
        """Get or create physical output port with the given name & width.

        Args:
            name (:obj:`str`):
            width (:obj:`int`):

        Returns:
            `PhysicalOutputPort`:

        Raises:
            `PRGAInternalError`: if a port with the given name already exists but the width does not match
        """
        port = self._ports.get(name, None)
        if port is not None:
            if not (port.is_output and port.width == width):
                raise PRGAInternalError("Port '{}' is not a {}-bit physical output"
                        .format(name, width))
        else:
            port = self._ports[name] = PhysicalOutputPort(self, name, width)
        return port

    # -- exposed API ---------------------------------------------------------
    @property
    def width(self):
        """Width of the 2D array."""
        return self.__width

    @property
    def height(self):
        """Height of the 2D array."""
        return self.__height

    def place_blocks(self, block, x, y, endx = None, endy = None, stepx = None, stepy = None):
        """Place blocks at the specific positions.

        Args:
            block (:obj:`str`): the name of the logic/io block to be placed
            x, y (:obj:`int`): placement position
            endx, endy (:obj:`int`, default=x+1, y+1): stop position for repeated placement
            stepx, stepy (:obj:`int`, default=block.width, block.height): increment value for repeated placement

        Raises:
            `PRGAAPIError`: if the position is invalid

        If only ``x`` and ``y`` are given, only one block will be placed at the given position. If ``endx`` and
        ``endy`` are also given, blocks will be repeatedly placed in the region one next to another. If ``stepx`` and
        ``stepy`` are given, the placement interval will be overriden.

        Examples:
            >>> array = Array(10, 10)
            # fill the middle of the array with 'clb'
            >>> array.place_blocks('clb', 1, 1, 9, 9)
            # put io blocks at the edges
            >>> array.place_blocks('io_left', 0, 1, endy=9)
            >>> array.place_blocks('io_right', 9, 1, endy=9)
            >>> array.place_blocks('io_bottom', 1, 0, endx=9)
            >>> array.place_blocks('io_top', 1, 9, endx=9)
            # put 1x2 dsp blocks at some places
            >>> array.place_blocks('dsp', 3, 2, 7, 7, 3, 4)
        """
        if block is not None:
            try:
                block = self._context._blocks[block]
            except PRGAInternalError as e:
                raise PRGAAPIError(str(e))
        width = 1 if block is None else block.width
        height = 1 if block is None else block.height
        startx, starty = x, y
        endx, endy = uno(endx, x + 1), uno(endy, y + 1)
        stepx, stepy = uno(stepx, width), uno(stepy, height)
        if stepx < width or stepy < height:
            raise PRGAAPIError("Invalid 'stepx' and/or 'stepy'")
        for x, y in product(xrange(startx, endx, stepx), xrange(starty, endy, stepy)):
            if x < 0 or x + width > self.width or y < 0 or y + height > self.height:
                raise PRGAAPIError(("Invalid placement of block '{}' (size: {} x {}) at ({}, {}) is beyond the "
                    "array ({} x {})").format('EMPTY' if block is None else block.name, width, height, x, y,
                        self.width, self.height))
            # remove conflicting blocks
            for xx, yy in product(xrange(x, x + width), xrange(y, y + height)):
                root = self._get_root_tile(xx, yy)
                for xof, yof in product(xrange(root.width), xrange(root.height)):
                    self.__array[root.x + xof][root.y + yof].xoffset = 0
                    self.__array[root.x + xof][root.y + yof].yoffset = 0
                    self.__array[root.x + xof][root.y + yof].block = None
            # place the block
            self.__array[x][y].block = block
            # modify offsets
            for xof, yof in product(xrange(width), xrange(height)):
                self.__array[x + xof][y + yof].xoffset = xof
                self.__array[x + xof][y + yof].yoffset = yof

    def populate_routing_channels(self):
        """Populate all routing channels using the given definition of segments.

        This method should be called **only once** after you've done placing the blocks. In addition to create all the
        routing channels, this method will also create & place empty connection blocks and switch blocks at the
        correct positions.
        """
        # init space
        for x, y in product(xrange(self.width), xrange(self.height)):
            tile = self.__array[x][y]
            tile.space_decx = max(0, x - 1)
            tile.space_incx = max(0, self.width - x - 2)
            tile.space_decy = max(0, y - 1)
            tile.space_incy = max(0, self.height - y - 2)
        # update space
        for x, y in product(xrange(self.width), xrange(self.height)):
            tile = self.__array[x][y]
            if tile.xoffset < tile.width - 1:
                if tile.yoffset == 0:
                    for yy in xrange(y):
                        self.__array[x][yy].space_incy = min(self.__array[x][yy].space_incy, y - yy - 1)
                if tile.yoffset == tile.height - 1:
                    for yy in xrange(y + 1, self.height):
                        self.__array[x][yy].space_decy = min(self.__array[x][yy].space_decy, yy - y - 1)
            if tile.yoffset < tile.height - 1:
                if tile.xoffset == 0:
                    for xx in xrange(x):
                        self.__array[xx][y].space_incx = min(self.__array[xx][y].space_incx, x - xx - 1)
                if tile.xoffset == tile.width - 1:
                    for xx in xrange(x + 1, self.width):
                        self.__array[xx][y].space_decx = min(self.__array[xx][y].space_decx, xx - x - 1)
        # place connection blocks & switch blocks
        connblocks = {}
        switchblocks = {}
        for x, y in product(xrange(self.width - 1), xrange(self.height - 1)):
            tile = self.__array[x][y]
            if x > 0 and tile.is_top_edge:
                above = self.__array[x][y+1]
                key_conn = (Dimension.horizontal,
                        None if tile.block is None else tile.block.name,
                        None if above.block is None else above.block.name,
                        tile.xoffset, above.xoffset)
                tile.hconn = connblocks.setdefault(key_conn,
                        self._context._get_or_create_connection_block(*key_conn))
            if y > 0 and tile.is_right_edge:
                right = self.__array[x+1][y]
                key_conn = (Dimension.vertical,
                        None if tile.block is None else tile.block.name,
                        None if right.block is None else right.block.name,
                        tile.yoffset, right.yoffset)
                tile.vconn = connblocks.setdefault(key_conn,
                        self._context._get_or_create_connection_block(*key_conn))
            if tile.is_top_edge or tile.is_right_edge:
                key_switch = (x > 0 and tile.is_top_edge,
                        x < self.width - 1 and tile.space_incx > 0,
                        y > 0 and tile.is_right_edge,
                        y < self.height - 1 and tile.space_incy > 0)
                tile.switch = switchblocks.setdefault(key_switch,
                        self._context._get_or_create_switch_block(*key_switch))

    def populate_routing_switches(self, default_fc, block_map = None):
        """Populate all routing blocks with switches.

        Args:
            default_fc (`BlockFCValue`): the default FC value for all blocks
            block_map (:obj:`dict` [:obj:`str` -> `BlockFCValue` ], default=None): override the FC value for some
                blocks

        This method should be called **only once** after `populate_routing_channels`. This method will call
        `ConnectionBlock.implement_fc` and `SwitchBlock.implement_wilton` methods to populate all routing switches.
        """
        block_map = uno(block_map, {})
        for block in self._context._switch_blocks:
            block.implement_wilton()
        for block in self._context._connection_blocks:
            block.implement_fc(block_map.get(block.environment.block_lb, default_fc),
                    block_map.get(block.environment.block_rt, default_fc))
