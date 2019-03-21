# Python 2 and 3 compatible
from prga.compatible import *

__all__ = ['IOBlock', 'LogicBlock']

from prga._archdef.common import BlockType, Side, TileType
from prga._archdef.moduleinstance.instance import LogicalInstance
from prga._archdef.routing.common import BlockPin
from prga._archdef.routing.block import AbstractBlock
from prga._archdef.block.slice import Slice
from prga._archdef.block.port import (IOBlockInputPort, IOBlockOutputPort, IOBlockClockPort,
        LogicBlockInputPort, LogicBlockOutputPort, LogicBlockClockPort)
from prga._util.util import uno
from prga.exception import PRGAInternalError, PRGAAPIError

from collections import OrderedDict
from itertools import chain

# ----------------------------------------------------------------------------
# -- AbstractLogicBlock ------------------------------------------------------
# ----------------------------------------------------------------------------
class BlockNodesDelegate(Mapping):
    """A helper class for `AbstractLogicBlock.nodes` property."""
    def __init__(self, ports):
        self.__ports = ports

    def __getitem__(self, key):
        if isinstance(key, BlockPin):
            port = self.__ports.get(key.port, None)
            if port is not None and port.node == key:
                return port
        raise KeyError(key)

    def __iter__(self):
        return iter(x.node for x in itervalues(self.__ports))

    def __len__(self):
        return len(self.__ports)

class AbstractLogicBlock(AbstractBlock, Slice):
    """Abstract base class for LogicBlock and IOBlock.

    Args:
        name (:obj:`str`): name of this block
    """
    # == low-level API =======================================================
    @property
    def nodes(self):
        """A mapping from node references to routing nodes."""
        return BlockNodesDelegate(self.ports)

    def reorder_ports(self):
        """Reorder ports to meet VPR's ordering requirements."""
        inputs, outputs, clocks, others = [], [], [], []
        for port in itervalues(self._ports):
            if not port.is_logical:
                others.append(port)
            elif port.is_clock:
                clocks.append(port)
            elif port.is_input:
                inputs.append(port)
            else:
                outputs.append(port)
        self._ports = OrderedDict()
        for port in chain(sorted(inputs, key=lambda x: x.name),
                sorted(outputs, key=lambda x: x.name),
                sorted(clocks, key=lambda x: x.name),
                others):
            self._ports[port.name] = port

    def covers_tile(self, x, y, type_):
        xok = (0 <= x < self.width - 1 or (x == self.width - 1 and type_ in (TileType.logic, TileType.xchan)))
        yok = (0 <= y < self.height - 1 or (y == self.height - 1 and type_ in (TileType.logic, TileType.ychan)))
        return xok and yok

# ----------------------------------------------------------------------------
# -- IOBlock -----------------------------------------------------------------
# ----------------------------------------------------------------------------
class IOBlock(AbstractLogicBlock):
    """IO block, also called IOB, etc.

    Args:
        name (:obj:`str`): name of this block
        io_primitive (`InpadPrimitive`, `OutpadPrimitive` or `IopadPrimitive`): the IO primitive
        capacity (:obj:`int`): number of blocks placed in one tile
    """
    def __init__(self, name, io_primitive, capacity = 1):
        super(IOBlock, self).__init__(name)
        self._capacity = capacity
        instance = LogicalInstance(self, io_primitive, 'extio')
        self.add_instance_raw(instance)
        if instance.is_iopad_primitive or instance.is_inpad_primitive:
            instance.pins['inpad'].physical_cp = self.get_or_create_physical_input('extio_i', 1, is_external = True)
        if instance.is_iopad_primitive or instance.is_outpad_primitive:
            instance.pins['outpad'].physical_cp = self.get_or_create_physical_output('extio_o', 1, is_external = True)
        if instance.is_iopad_primitive:
            self.get_or_create_physical_output('extio_oe', 1, is_external = True)

    # == low-level API =======================================================
    @property
    def block_type(self):
        """Type of this block."""
        return BlockType.io

    # == high-level API ======================================================
    @property
    def capacity(self):
        """Number of blocks placed in one tile."""
        return self._capacity

    def add_input(self, name, width, side, global_ = None):
        """Add a block input port.

        Args:
            name (:obj:`str`): name of this port
            width (:obj:`int`): width of this port
            side (`Side`): on which side of the block is this port
            global_ (:obj:`str`): name of the non-clock global wire this port is hard-wired to
        """
        try:
            self.add_port(IOBlockInputPort(self, name, width, side, global_))
        except PRGAInternalError as e:
            raise_from(PRGAAPIError(e.message), e)

    def add_output(self, name, width, side):
        """Add a block output port.

        Args:
            name (:obj:`str`): name of this port
            width (:obj:`int`): width of this port
            side (`Side`): on which side of the block is this port
        """
        try:
            self.add_port(IOBlockOutputPort(self, name, width, side))
        except PRGAInternalError as e:
            raise_from(PRGAAPIError(e.message), e)

    def add_clock(self, name, side, global_ = None):
        """Add a block clock port.

        Args:
            name (:obj:`str`): name of this port
            side (`Side`): on which side of the block is this port
            global_ (:obj:`str`): name of the global clock wire this port is hard-wired to. If None is given, the name
                of this port will be used
        """
        try:
            self.add_port(IOBlockClockPort(self, name, side, uno(global_, name)))
        except PRGAInternalError as e:
            raise_from(PRGAAPIError(e.message), e)

# ----------------------------------------------------------------------------
# -- LogicBlock --------------------------------------------------------------
# ----------------------------------------------------------------------------
class LogicBlock(AbstractLogicBlock):
    """Logic block, also called CLB, slice, etc.

    Args:
        name (:obj:`str`): name of this block
        width (:obj:`int`): width of this block
        height (:obj:`int`): height of this block
    """
    def __init__(self, name, width = 1, height = 1):
        super(LogicBlock, self).__init__(name)
        self._width = width
        self._height = height

    # == internal methods ====================================================
    def __validate_position_and_side(self, x, y, side):
        """Check if the given position and side are valid in the block."""
        if not ((side is Side.left and x == 0 and y >= 0 and y < self.height) or
                (side is Side.right and x == self.width - 1 and y >= 0 and y < self.height) or
                (side is Side.bottom and y == 0 and x >= 0 and x < self.width) or
                (side is Side.top and y == self.height - 1 and x >= 0 and x < self.width)):
            raise PRGAAPIError("Offset ({}, {}) is not at the {} side of block '{}'"
                    .format(x, y, side.name, self.name))

    # == low-level API =======================================================
    @property
    def block_type(self):
        """Type of this block."""
        return BlockType.logic

    # == high-level API ======================================================
    @property
    def width(self):
        """Width of this block."""
        return self._width

    @property
    def height(self):
        """Height of this block."""
        return self._height

    def add_input(self, name, width, side, global_ = None, xoffset = 0, yoffset = 0):
        """Add a block input port.

        Args:
            name (:obj:`str`): name of this port
            width (:obj:`int`): width of this port
            side (`Side`): on which side of the block is this port
            global_ (:obj:`str`): name of the non-clock global wire this port is hard-wired to
            xoffset (:obj:`int`): if the block is larger than 1 tile, specify X-dimension position of this port
            yoffset (:obj:`int`): if the block is larger than 1 tile, specify Y-dimension position of this port
        """
        self.__validate_position_and_side(xoffset, yoffset, side)
        try:
            self.add_port(LogicBlockInputPort(self, name, width, side, global_, xoffset, yoffset))
        except PRGAInternalError as e:
            raise_from(PRGAAPIError(e.message), e)

    def add_output(self, name, width, side, xoffset = 0, yoffset = 0):
        """Add a block output port.

        Args:
            name (:obj:`str`): name of this port
            width (:obj:`int`): width of this port
            side (`Side`): on which side of the block is this port
            xoffset (:obj:`int`): if the block is larger than 1 tile, specify X-dimension position of this port
            yoffset (:obj:`int`): if the block is larger than 1 tile, specify Y-dimension position of this port
        """
        self.__validate_position_and_side(xoffset, yoffset, side)
        try:
            self.add_port(LogicBlockOutputPort(self, name, width, side, xoffset, yoffset))
        except PRGAInternalError as e:
            raise_from(PRGAAPIError(e.message), e)

    def add_clock(self, name, side, global_ = None, xoffset = 0, yoffset = 0):
        """Add a block clock port.

        Args:
            name (:obj:`str`): name of this port
            side (`Side`): on which side of the block is this port
            global_ (:obj:`str`): name of the global clock wire this port is hard-wired to
            xoffset (:obj:`int`): if the block is larger than 1 tile, specify X-dimension position of this port
            yoffset (:obj:`int`): if the block is larger than 1 tile, specify Y-dimension position of this port
        """
        self.__validate_position_and_side(xoffset, yoffset, side)
        try:
            self.add_port(LogicBlockClockPort(self, name, side, uno(global_, name), xoffset, yoffset))
        except PRGAInternalError as e:
            raise_from(PRGAAPIError(e.message), e)
