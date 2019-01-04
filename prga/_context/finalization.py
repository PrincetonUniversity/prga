# -*- encoding: ascii -*-

"""The pass for finalizing architecture context."""

__all__ = ['ArchitectureFinalization']

import logging
_logger = logging.getLogger(__name__)

from flow import AbstractPass

import itertools

# ----------------------------------------------------------------------------
# -- ArchitectureFinalization ------------------------------------------------
# ----------------------------------------------------------------------------
class ArchitectureFinalization(AbstractPass):
    """Finalize architecture context."""
    @property
    def key(self):
        """Key of this pass."""
        return "finalization"

    def run(self, context):
        # 1. remove empty routing blocks
        conn, switch = [], []
        removed = set()
        while len(context._connection_blocks) > 0:
            block = context._connection_blocks.pop()
            if len(block._nodes) > 0:
                conn.append(block)
            else:
                removed.add(block.name)
        context._connection_blocks.extend(conn)
        while len(context._switch_blocks) > 0:
            block = context._switch_blocks.pop()
            if len(block._nodes) > 0:
                switch.append(block)
            else:
                removed.add(block.name)
        context._connection_blocks.extend(switch)
        # 2. remove empty routing block instances
        for x, y in itertools.product(xrange(context.array.width), xrange(context.array.height)):
            tile = context.array._array[x][y]
            if tile.hconn is not None and tile.hconn.name in removed:
                tile.hconn = None
            if tile.vconn is not None and tile.vconn.name in removed:
                tile.vconn = None
            if tile.switch is not None and tile.switch.name in removed:
                tile.switch = None
        # 3. reorder logic/io block pins
        for block in context.blocks.itervalues():
            block._reorder_ports()
        # 4. materialize connections
        for block in context._iter_physical_blocks():
            block._materialize_connections()
