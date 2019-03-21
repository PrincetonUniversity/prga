# Python 2 and 3 compatible
from prga.compatible import *

from prga._util.util import uno
from prga.exception import PRGAAPIError

from collections import OrderedDict
from abc import ABCMeta, abstractproperty, abstractmethod
import networkx as nx

import logging
_logger = logging.getLogger(__name__)

import time

# ----------------------------------------------------------------------------
# -- Flow --------------------------------------------------------------------
# ----------------------------------------------------------------------------
class Flow(object):
    """The flow manager of PRGA.

    Args:
        context (`ArchitectureContext`): the context which holds all the internal data. `AbstractPass`-subclasses
            will operate on this object
    """
    def __init__(self, context):
        self.__context = context
        self.__passes_pending = []

    def __key_is_prefix(self, key, other):
        """Check if ``key`` is a prefix of the ``other`` key.
        
        Args:
            key, other (:obj:`str`):
        """
        key, other = map(lambda x: x.split('.'), (key, other))
        if len(key) > len(other):
            return False
        for s, o in zip(key, other):
            if s != o:
                return False
        return True

    def __key_is_irrelevent(self, key, other):
        """Check if the two keys are irrelevent to each other."""
        return not self.__key_is_prefix(key, other) and not self.__key_is_prefix(other, key)

    def add_pass(self, pass_):
        """Add one pass to the flow.

        Args:
            pass_ (`AbstractPass`-subclass):
        """
        self.__passes_pending.append(pass_)

    def run_pass(self, pass_):
        """Run one pass immediately.

        Args:
            pass_ (`AbstractPass`-subclass):
        """
        self.add_pass(pass_)
        self.run()

    def run(self):
        """Run the flow."""
        # 1. resolve dependences/conflicts
        passes = OrderedDict()
        while self.__passes_pending:
            updated = None
            for i, pass_ in enumerate(self.__passes_pending):
                # 1.1 is the exact same pass already run?
                if not pass_.is_repeatable:
                    if pass_.key in self.__context._passes_applied:
                        raise PRGAAPIError("Pass '{}' is already applied".format(pass_.key))
                    if pass_.key in passes:
                        raise PRGAAPIError("Pass '{}' is added twice".format(pass_.key))
                # 1.2 is there any invalid pass keys?
                try:
                    duplicate = next(key for key in self.__context._passes_applied if not
                            self.__key_is_irrelevent(pass_.key, key))
                    raise PRGAAPIError("Applied pass '{}' and '{}' are duplicate, or one is the sub-pass of another"
                            .format(duplicate, pass_.key))
                except StopIteration:
                    pass
                try:
                    duplicate = next(key for key in passes if not self.__key_is_irrelevent(pass_.key, key))
                    raise PRGAAPIError("Pass '{}' and '{}' are duplicate, or one is the sub-pass of another"
                            .format(duplicate, pass_.key))
                except StopIteration:
                    pass
                # 1.3 is any pass key in conflict with this key?
                try:
                    conflict = next(key for key in self.__context._passes_applied if any(self.__key_is_prefix(rule, key)
                        for rule in pass_.conflicts))
                    raise PRGAAPIError("Applied pass '{}' conflicts with '{}'".format(conflict, pass_.key))
                except StopIteration:
                    pass
                try:
                    conflict = next(key for key in passes if any(self.__key_is_prefix(rule, key) for rule in pass_.conflicts))
                    raise PRGAAPIError("Pass '{}' conflicts with '{}'".format(conflict, pass_.key))
                except StopIteration:
                    pass
                # 1.4 are all the dependences satisfied?
                if all((any(self.__key_is_prefix(rule, key) for key in self.__context._passes_applied) or
                    any(self.__key_is_prefix(rule, key) for key in passes)) for rule in pass_.dependences):
                    passes[pass_.key] = pass_
                    updated = i
                    break
            if updated is None:
                pass_ = self.__passes_pending[0]
                missing = next(rule for rule in pass_.dependences
                        if all(not self.__key_is_prefix(rule, key) for key in self.__context._passes_applied) and
                        all(not self.__key_is_prefix(rule, key) for key in passes))
                raise PRGAAPIError("Missing pass '{}' required by '{}'".format(missing, pass_.key))
            else:
                del self.__passes_pending[i]
        passes = list(itervalues(passes))
        # 2. order passes
        # 2.1 build a graph
        g = nx.DiGraph()
        g.add_nodes_from(range(len(passes)))
        for i, pass_ in enumerate(passes):
            for j, other in enumerate(passes):
                if i == j:
                    continue
                if (any(self.__key_is_prefix(rule, other.key) for rule in pass_.passes_before_self) or
                        any(self.__key_is_prefix(rule, other.key) for rule in pass_.dependences)):
                    # ``other`` should be executed before ``pass_``
                    g.add_edge(j, i)
                if any(self.__key_is_prefix(rule, other.key) for rule in pass_.passes_after_self):
                    # ``other`` should be executed after ``pass_``
                    g.add_edge(i, j)
        try:
            passes = [passes[i] for i in nx.topological_sort(g)]
        except nx.exception.NetworkXUnfeasible:
            raise PRGAAPIError("Cannot determine a feasible order of the passes")
        # 3. run passes
        for pass_ in passes:
            _logger.info("running pass '%s'", pass_.key)
            t = time.time()
            pass_.run(self.__context)
            self.__context._passes_applied.add(pass_.key)
            _logger.info("pass '%s' took %f seconds", pass_.key, time.time() - t)

# ----------------------------------------------------------------------------
# -- AbstractPass ------------------------------------------------------------
# ----------------------------------------------------------------------------
class AbstractPass(with_metaclass(ABCMeta, object)):
    """One pass of the flow."""

    @abstractproperty
    def key(self):
        """Key of this pass."""
        raise NotImplementedError

    @property
    def is_repeatable(self):
        """If this pass is repeatable."""
        return False

    @property
    def dependences(self):
        """Passes that this pass depend on."""
        return tuple()

    @property
    def conflicts(self):
        """Passes that should not be used with this pass."""
        return tuple()

    @property
    def passes_before_self(self):
        """Passes that should be executed before this pass."""
        return tuple()

    @property
    def passes_after_self(self):
        """Passes that should be executed after this pass."""
        return tuple()

    @abstractmethod
    def run(self, context):
        """Run this pass.

        Args:
            context (`ArchitectureContext`): the context which holds all the internal data
            \*args, \*\*kwargs: other arguments
        """
        raise NotImplementedError
