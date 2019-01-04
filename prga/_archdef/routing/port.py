# -*- enconding: ascii -*-

"""Routing block port classes."""

__all__ = ['RoutingBlockInputPort', 'RoutingBlockOutputPort']

import logging
_logger = logging.getLogger(__name__)

from ..portpin.port import AbstractInputPort, AbstractOutputPort

# ----------------------------------------------------------------------------
# -- RoutingBlockInputPort ---------------------------------------------------
# ----------------------------------------------------------------------------
class RoutingBlockInputPort(AbstractInputPort):
    """Routing block input port.

    Args:
        block (`AbstractRoutingBlock`-subclass): the block this port belongs to
        name (:obj:`str`): name of this port
        width (:obj:`int`): width of this port
        reference (`SegmentReference` or `BlockPinReference`): the routing nodes this port references to
    """
    def __init__(self, block, name, width, reference):
        super(RoutingBlockInputPort, self).__init__(block, name, width)
        self.__reference = reference

    @property
    def node_reference(self):
        """A reference to the routing node this port references to."""
        return self.__reference

    @property
    def is_logical(self):
        """Test if this is a logical port."""
        return True

    @property
    def is_physical(self):
        """Test if this is a physical port."""
        return True

# ----------------------------------------------------------------------------
# -- RoutingBlockOutputPort --------------------------------------------------
# ----------------------------------------------------------------------------
class RoutingBlockOutputPort(AbstractOutputPort):
    """Routing block output port.

    Args:
        block (`AbstractRoutingBlock`-subclass): the block this port belongs to
        name (:obj:`str`): name of this port
        width (:obj:`int`): width of this port
        reference (`SegmentReference` or `BlockPinReference`): the routing nodes this port references to
    """
    def __init__(self, block, name, width, reference):
        super(RoutingBlockOutputPort, self).__init__(block, name, width)
        self.__reference = reference

    @property
    def node_reference(self):
        """A reference to the routing node this port references to."""
        return self.__reference

    @property
    def is_logical(self):
        """Test if this is a logical port."""
        return True

    @property
    def is_physical(self):
        """Test if this is a physical port."""
        return True
