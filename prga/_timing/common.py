# -*- enconding: ascii -*-

__all__ = ['TimingConstraintType', 'AbstractTimingEngine']

import logging
_logger = logging.getLogger(__name__)

from enum import Enum
from abc import ABCMeta, abstractmethod

import contextlib

# ----------------------------------------------------------------------------
# -- TimingConstraintType ----------------------------------------------------
# ----------------------------------------------------------------------------
class TimingConstraintType(Enum):
    """Timing constraint types."""
    delay = 0       #: combinational delay
    setup = 1       #: flop set-up time
    hold = 2        #: flop hold time
    clk2q = 3       #: flop clk-to-q time
    
# ----------------------------------------------------------------------------
# -- AbstractTimingEngine ----------------------------------------------------
# ----------------------------------------------------------------------------
class AbstractTimingEngine(object):
    """Abstract base class for a timing engine."""
    __metaclass__ = ABCMeta

    class TimingEngineContextManager(object):
        """Context manager specifically for timing engines.
        
        Args:
            engine (`AbstractTimingEngine`-subclass): the engine to be managed
            block (`AbstractLogicalBlock`-subclass, default=None): the block to be inspected, or the top-level module
                if ``block`` is None
        """
        def __init__(self, engine, block = None):
            self._engine = engine
            self._block = block

        def __enter__(self):
            self._engine._start(self._block)

        def __exit__(self, exc_type, exc_value, traceback):
            if exc_type is not None:
                return
            self._engine._end()

    def _open(self, block = None):
        """Create and return a context manager for the timing engine.

        Args:
            block (`AbstractLogicalBlock`-subclass, default=None): the block to be inspected, or the top-level module
                if ``block`` is None
        """
        return self.TimingEngineContextManager(self, block)

    def _start(self, block = None):
        """Start the timing engine.

        Args:
            block (`AbstractLogicalBlock`-subclass, default=None): the block to be inspected, or the top-level module
                if ``block`` is None

        Some timing engines may need to access external file/processes. The handlers for these external stuff are not
        serializable by ``pickle``. ``_start`` should create and store such handlers, and ``_end`` should destroy such
        hanlders.
        """
        pass

    def _end(self):
        """End the timing engine. Refer to `AbstractTimingEngine._start` for more info."""
        pass

    @abstractmethod
    def _query_block_timing(self, type, src_net, sink_net):
        """Query the timing constraint of the given type for the given path.

        Args:
            type (`TimingConstraintType`): type of the timing constraint queried
            src_net, sink_net (`PortOrPinBit`): a port or pin in a logic/io block

        Returns:
            min, max (:obj:`float`): the minimum and maximum timing values
        """
        raise NotImplementedError

    @abstractmethod
    def _query_edge_timing(self, src_node, src_index, sink_node, sink_index):
        """Query the delay from a specific routing node to another.

        Args:
            src_node (`SegmentNode` or `BlockPin`): the source routing node set
            src_index (:obj:`int`): the bit in the source routing node set
            sink_node (`SegmentNode` or `BlockPin`): the sink routing node set
            sink_index (:obj:`int`): the bit in the sink routing node set

        Returns:
            min, max (:obj:`float`): the minimum and maximum timing values
        """
        raise NotImplementedError
