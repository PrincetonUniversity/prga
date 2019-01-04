# -*- enconding: ascii -*-

"""Tile & Block Instances."""

__all__ = ['BlockPin', 'BlockInstance', 'Tile']

import logging
_logger = logging.getLogger(__name__)

from ..moduleinstance.instance import AbstractInstance
from ..portpin.port import Pin
from ..portpin.common import ConstNet
from ..common import NetType, RoutingNodeType
from ..routing.resource import AbstractRoutingNode
from ...exception import PRGAInternalError, PRGAAPIError
from ..._util.util import DictProxy

from collections import OrderedDict, Mapping, namedtuple

# ----------------------------------------------------------------------------
# -- BlockPin ----------------------------------------------------------------
# ----------------------------------------------------------------------------
class BlockPin(Pin, AbstractRoutingNode):
    """Block pin.

    Args:
        instance (`BlockInstance`): the block instance this pin belongs to
        port (logic/io/routing block port): the port this pin links to
    """

    @property
    def node_type(self):
        """Type of the routing node."""
        if self.is_logical:
            return RoutingNodeType.blockpin
        else:
            raise PRGAInternalError("Block pin '{}' is not a routing node"
                    .format(self))

    @property
    def x(self):
        """The horizontal location of this pin."""
        try:
            return self.parent_instance.x + self.port.xoffset
        except AttributeError:
            return self.parent_instance.x

    @property
    def y(self):
        """The vertical location of this pin."""
        try:
            return self.parent_instance.y + self.port.yoffset
        except AttributeError:
            return self.parent_instance.y

    @property
    def subblock(self):
        """The sub-block ID of the block instance that this pin belongs to."""
        return self.parent_instance.subblock

# ----------------------------------------------------------------------------
# -- BlockInstance -----------------------------------------------------------
# ----------------------------------------------------------------------------
class _DynamicInstancePins(Mapping):
    """A helper class for `BlockInstance::_pins` property."""
    def __init__(self, instance):
        self.__instance = instance

    def __getitem__(self, name):
        try:
            if self.__instance.is_physical:
                return self.__instance._permanent_pins.get(name,
                        BlockPin(self.__instance, self.__instance.model._ports[name]))
            else:
                return BlockPin(self.__instance, self.__instance.model.ports[name])
        except KeyError:
            raise KeyError(name)

    def __iter__(self):
        if self.__instance.is_physical:
            return iter(self.__instance.model._ports)
        else:
            return iter(self.__instance.model.ports)

    def __len__(self):
        if self.__instance.is_physical:
            return len(self.__instance.model._ports)
        else:
            return len(self.__instance.model.ports)

    def iteritems(self):
        """Return an iterator over (key, value) pairs."""
        if self.__instance.is_physical:
            return iter( (name, self.__instance._permanent_pins.get(name, BlockPin(self.__instance, port)))
                    for name, port in self.__instance.model._ports.iteritems())
        else:
            return iter( (name, BlockPin(self.__instance, port))
                    for name, port in self.__instance.model.ports.iteritems())

    def iterkeys(self):
        """Return an iterator over the keys."""
        return iter(self)

    def itervalues(self):
        """Return an iterator over the values."""
        if self.__instance.is_physical:
            return iter(self.__instance._permanent_pins.get(name, BlockPin(self.__instance, port))
                    for name, port in self.__instance.model._ports.iteritems())
        else:
            return iter(BlockPin(self.__instance, port)
                    for name, port in self.__instance.model.ports.iteritems())

class BlockInstance(AbstractInstance):
    """Block instance, optimized for memory usage.
    
    Args:
        block (`AbstractBlock`-subclass): the block to be instantiated
        tile (`Tile`): the tile this block is in
        subblock (:obj:`int`, default=0): if ``block`` is an IO block, which sub-block is this block
    """

    def __init__(self, block, tile, subblock = 0):
        super(BlockInstance, self).__init__(block)
        self.__tile = tile
        self.__subblock = subblock
        self.__is_physical = True
        self.__permanent_pins = {}   # we don't use OrderedDict here because the order is determined by the block

    # -- abstract property implementation ------------------------------------
    @property
    def name(self):
        """Name of this instance."""
        if self.is_io_block:
            return '{}_x{}y{}_{}'.format(self.model.name, self.x, self.y, self.subblock)
        else:
            return '{}_x{}y{}'.format(self.model.name, self.x, self.y)

    @property
    def is_logical(self):
        """Test if this instance is logical."""
        return True

    @property
    def is_physical(self):
        """Test if this instance is physical."""
        return self.__is_physical

    # -- internal API --------------------------------------------------------
    @property
    def _permanent_pins(self):
        """A mapping from name to pins that are permanent."""
        if self.__is_physical:
            return self.__permanent_pins
        else:
            raise PRGAInternalError("Block instance '{}' is not physical"
                    .format(self.name))
    
    @property
    def _pins(self):
        """A mapping from name to pins.

        Note that objects returned by this mapping might be transient. See
        `_AbstractInstance::_get_or_create_pin` for more detail.
        """
        return _DynamicInstancePins(self)

    def _get_or_create_pin(self, name, permanent = False):
        """Get or create pin with the given name.

        Args:
            name (:obj:`str`): name of the pin to be created
            permanent (:obj:`bool`, default=False): if the pin should be permanently stored

        Returns:
            `BlockPin`: the created pin

        Raises:
            `PRGAInternalError`: if no port with the given name in the model of this instance

        By default, this method will create temporary pin that should not be used for connections. If ``permanent``
        is set, a permanent pin will be created and stored, so that all future reference to the pin will always return
        the same object, which is safe for connections.
        """
        if permanent and not self.is_physical:
            raise PRGAInternalError("Block instance '{}' is not physical"
                    .format(self.name))
        try:
            if permanent:
                return self.__permanent_pins.setdefault(name, BlockPin(self, self.model._ports[name]))
            else:
                return self.__permanent_pins.get(name, BlockPin(self, self.model._ports[name]))
        except KeyError:
            raise PRGAInternalError("Block '{}' does not have port '{}'"
                    .format(self.model.name, self.name, name))

    def _unset_physical(self):
        """Make this block instance non-physical."""
        if not self.is_io_block or self.is_logic_block:
            raise PRGAInternalError("Trying to set routing block instance '{}' to non-physical"
                    .format(self.name))
        elif len(self.__permanent_pins) > 0:
            raise PRGAInternalError("Trying to set block instance '{}' with permanent pins to non-physical"
                    .format(self.name))
        self.__is_physical = False

    # -- exposed API ---------------------------------------------------------
    @property
    def tile(self):
        """The tile that this instance belongs to."""
        return self.__tile

    @property
    def x(self):
        """The horizontal location of this block."""
        return self.__tile.x

    @property
    def y(self):
        """The veritical location of this block."""
        return self.__tile.y

    @property
    def subblock(self):
        """The sub-block index if this is an instance of an IO block."""
        return self.__subblock

    @property
    def block(self):
        """An alias for 'model'."""
        return self.model

# ----------------------------------------------------------------------------
# -- Tile --------------------------------------------------------------------
# ----------------------------------------------------------------------------
class Tile(object):
    """A tile in the block array.

    Args:
        x, y (:obj:`int`): the location of this tile
        xoffset, yoffset (:obj:`int`, default=0): the offset from the root of this tile

    Note that there are actually two types of tiles: root tile & dummy tile. For logic/io block no larger than 1x1,
    root tiles are used; for logic/io block larger than 1x1, the tile at the left-bottom corner is the root tile,
    while all other tiles covered by the block are dummy tiles. A simple criteria is: ``is_root = xoffset == 0 and
    yoffset == 0``.
    """

    def __init__(self, x, y, xoffset = 0, yoffset = 0):
        self.__x = x
        self.__y = y

        self.__block_instances = tuple()
        self.__hconn_instance = None
        self.__vconn_instance = None
        self.__switch_instance = None

        self.xoffset = xoffset
        self.yoffset = yoffset

        self.space_decx = 0
        self.space_incx = 0
        self.space_decy = 0
        self.space_incy = 0

    # -- exposed API ---------------------------------------------------------
    @property
    def x(self):
        """The horizontal location of this tile."""
        return self.__x

    @property
    def y(self):
        """The veritical location of this tile."""
        return self.__y

    @property
    def xoffset(self):
        """The offset from the root of this tile in horizontal direction."""
        try:
            return self.__xoffset
        except AttributeError:
            return 0

    @xoffset.setter
    def xoffset(self, xoffset):
        if xoffset == 0:
            try:
                del self.__xoffset
            except AttributeError:
                pass
        else:
            self.__xoffset = xoffset

    @property
    def yoffset(self):
        """The offset from the root of this tile in vertical direction."""
        try:
            return self.__yoffset
        except AttributeError:
            return 0

    @yoffset.setter
    def yoffset(self, yoffset):
        if yoffset == 0:
            try:
                del self.__yoffset
            except AttributeError:
                pass
        else:
            self.__yoffset = yoffset

    @property
    def block(self):
        """The logic/io block placed in this tile."""
        if len(self.__block_instances) > 0:
            return self.__block_instances[0].block
        else:
            return None
    
    @block.setter
    def block(self, block):
        if block is self.block:
            pass
        elif block is None:
            self.__block_instances = tuple()
        else:
            self.__block_instances = tuple(BlockInstance(block, self, i) for i in xrange(block.capacity))

    @property
    def block_instances(self):
        """The logic/io block instances in this tile."""
        return self.__block_instances

    @property
    def hconn(self):
        """The horizontal connection block in this tile."""
        if self.__hconn_instance is None:
            return None
        else:
            return self.__hconn_instance.block

    @hconn.setter
    def hconn(self, block):
        if block is None:
            self.__hconn_instance = None
        else:
            self.__hconn_instance = BlockInstance(block, self)

    @property
    def hconn_instance(self):
        """The horizontal connection block instance in this tile."""
        return self.__hconn_instance

    @property
    def vconn(self):
        """The vertical connection block in this tile."""
        if self.__vconn_instance is None:
            return None
        else:
            return self.__vconn_instance.block

    @vconn.setter
    def vconn(self, block):
        if block is None:
            self.__vconn_instance = None
        else:
            self.__vconn_instance = BlockInstance(block, self)

    @property
    def vconn_instance(self):
        """The vertical connection block instance in this tile."""
        return self.__vconn_instance

    @property
    def switch(self):
        """The switch block in this tile."""
        if self.__switch_instance is None:
            return None
        else:
            return self.__switch_instance.block

    @switch.setter
    def switch(self, block):
        if block is None:
            self.__switch_instance = None
        else:
            self.__switch_instance = BlockInstance(block, self)

    @property
    def switch_instance(self):
        """The switch block instance in this tile."""
        return self.__switch_instance

    @property
    def is_root(self):
        """Test if this is the root tile."""
        return self.xoffset == 0 and self.yoffset == 0

    @property
    def is_right_edge(self):
        """Test if this is the right most dummy tile of a large tile."""
        return self.xoffset == self.width - 1

    @property
    def is_top_edge(self):
        """Test if this is the top most dummy tile of a large tile."""
        return self.yoffset == self.height - 1

    @property
    def width(self):
        """Width of this tile."""
        if self.block is None:
            return 1
        else:
            return self.block.width

    @property
    def height(self):
        """Height of this tile."""
        if self.block is None:
            return 1
        else:
            return self.block.height
