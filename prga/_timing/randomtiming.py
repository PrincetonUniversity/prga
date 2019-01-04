# -*- enconding: ascii -*-

__all__ = ['RandomTimingEngine']

import logging
_logger = logging.getLogger(__name__)

from common import AbstractTimingEngine
from .._context.flow import AbstractPass
from .._util.util import uno

import random

# ----------------------------------------------------------------------------
# -- _RandomTimingEngine -----------------------------------------------------
# ----------------------------------------------------------------------------
class _RandomTimingEngine(AbstractTimingEngine):
    """Random-generated fake timing values.
    
    Args:
        max (:obj:`tuple`\(:obj:`float`, :obj:`float`\)): the min/max value for randomly-generated max timing
            constraints
        min (:obj:`tuple`\(:obj:`float`, :obj:`float`\), default=None): the min/max value for randomly-generated min
            timing constraints. If not set, min timing constraint will always be zero
    """

    def __init__(self, max, min = None):
        self._max_min, self._max_max = max
        self._min_min, self._min_max = uno(min, (0.0, 0.0))

    def _query_block_timing(self, type, src_net, sink_net):
        return random.uniform(self._min_min, self._min_max), random.uniform(self._max_min, self._max_max)

    def _query_edge_timing(self, src_node, src_index, sink_node, sink_index):
        return random.uniform(self._min_min, self._min_max), random.uniform(self._max_min, self._max_max)

# ----------------------------------------------------------------------------
# -- RandomTimingEngine ------------------------------------------------------
# ----------------------------------------------------------------------------
class RandomTimingEngine(AbstractPass):
    """Random-generated fake timing values.
    
    Args:
        max (:obj:`tuple`\(:obj:`float`, :obj:`float`\)): the min/max value for randomly-generated max timing
            constraints
        min (:obj:`tuple`\(:obj:`float`, :obj:`float`\), default=None): the min/max value for randomly-generated min
            timing constraints. If not set, min timing constraint will always be zero
    """
    def __init__(self, max, min = None):
        self._max_min, self._max_max = max
        self._min_min, self._min_max = uno(min, (0.0, 0.0))

    @property
    def key(self):
        """Key of this pass."""
        return "timing.random"

    @property
    def dependences(self):
        """Passes this pass depends on."""
        return ("rtl", )

    @property
    def conflicts(self):
        """Passes conflicting with this pass."""
        return ("timing", )

    def run(self, context):
        context._timing_engine = _RandomTimingEngine(
                (self._max_min, self._max_max),
                (self._min_min, self._min_max))
