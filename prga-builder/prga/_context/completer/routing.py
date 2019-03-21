# Python 2 and 3 compatible
from prga.compatible import *

"""Routing resource and connections completer."""

from prga._archdef.common import TileType, Dimension, Direction
from prga._archdef.routing.common import Position
from prga._archdef.routing.connectionblock import BlockFCValue, ConnectionBlock
from prga._archdef.routing.switchblock import SwitchBlockEnvironment, SwitchBlock
from prga._context.flow import AbstractPass
from prga.exception import PRGAInternalError
from prga._util.util import uno, register_extension

from itertools import product
from enum import Enum

import logging
_logger = logging.getLogger(__name__)
_logger.setLevel(logging.INFO)

register_extension("routing_environments", __name__)

_errinfo_multifit = ("Connection block '{}' fits multiple environments. This is probably because "
        "instances of the same array are neighboring different blocks. This will result in "
        "less optimal connection block structure.")

# ----------------------------------------------------------------------------
# -- Routing Block Style -----------------------------------------------------
# ----------------------------------------------------------------------------
class RoutingBlockStyle(Enum):
    """How routing blocks are generated and used."""
    bridged_s2c = 0 #: bridges from switch blocks to connection blocks
    bridged_c2s = 1 #: bridges from connection blocks to switch blocks
    combined = 2    #: combined C/S blocks

# ----------------------------------------------------------------------------
# -- Routing Resource Completer ----------------------------------------------
# ----------------------------------------------------------------------------
class RoutingResourceCompleter(AbstractPass):
    """Routing resource and connections completer."""
    def __init__(self, default_fc, style = RoutingBlockStyle.bridged_s2c, block_fc = None):
        if style is not RoutingBlockStyle.bridged_s2c:
            raise NotImplementedError(("Auto completer currently only supports bridges from connection blocks to "
                "switch blocks"))
        self._default_fc = BlockFCValue(default_fc)
        self._style = style
        self._block_fc = uno(block_fc, {})

    @property
    def key(self):
        """Key of this pass."""
        return "completer.routing"

    @property
    def passes_after_self(self):
        """Passes that shoul be run after this pass."""
        return ("completer.physical", "vpr", "config")

    def _update_grids(self, grid, array, xoffset, yoffset):
        for x, y in product(range(array.width), range(array.height)):
            instance = array.instances.get((Position(x, y), TileType.logic), None)
            if instance is None or not instance.is_root:
                continue
            elif instance.is_array:
                self._update_grids(grid, instance.model, x + xoffset, y + yoffset)
            else:
                block = instance.model
                for xx, yy in product(range(block.width), range(block.height)):
                    grid[xoffset + x + xx][yoffset + y + yy] = (block, xx, yy)
                            # xx == block.width - 1, yy == block.height - 1)

    def _place_routing_block(self, array, x, y, block):
        inst = array.get_root_block(Position(x, y), block.tile_type)
        if inst is None:
            array.add_block(block, x, y)
            return block
        elif inst.is_array:
            return self._place_routing_block(inst.model,
                    x - inst.position.x, y - inst.position.y, block)
        else:
            return inst.model

    def _complete_ports(self, array, top, memo = None):
        memo = uno(memo, set())
        for instance in itervalues(array.instances):
            if instance.is_root and instance.is_array and instance.model.name not in memo:
                self._complete_ports(instance.model, False, memo)
        array.auto_complete_ports(top, self._style is RoutingBlockStyle.combined)
        memo.add(array.name)

    def run(self, context):
        # 1.0 validate
        if context.top is None:
            raise PRGAInternalError("No top-level array pointed")
        # 1.1 init databases
        xcbs = {}
        ycbs = {}
        sbs = {}
        segments = list(itervalues(context._segments))
        # 1.2 flatten the hierarchy, create and place routing blocks
        #         block, xoffset, yoffset
        grid = [[(None,  0,       0) for y in range(context.top.height)]
                for x in range(context.top.width)]
        self._update_grids(grid, context.top, 0, 0)
        # 1.3 scan switch block environments
        environments = [[None for y in range(context.top.height - 1)]
                for x in range(context.top.width - 1)]
        for x, y in product(range(context.top.width - 1), range(context.top.height - 1)):
            block, xoffset, yoffset = grid[x][y]
            is_right_edge = block is None or xoffset == block.width - 1
            is_top_edge = block is None or yoffset == block.height - 1
            if not is_right_edge and not is_top_edge: # no switch block at this position
                continue
            env = SwitchBlockEnvironment()
            # what is left to this switch block?
            if x == 0 or not is_top_edge:
                env = env._replace(left = False)
            # what is bottom to this switch block?
            if y == 0 or not is_right_edge:
                env = env._replace(bottom = False)
            # what is right to this switch block?
            if x == context.top.width - 2:
                env = env._replace(right = False)
            else:
                right, _, yoffset = grid[x+1][y]
                if right is not None and yoffset < right.height - 1:
                    env = env._replace(right = False)
            # what is top to this switch block?
            if y == context.top.height - 2:
                env = env._replace(top = False)
            else:
                top, xoffset, _ = grid[x][y+1]
                if top is not None and xoffset < top.width - 1:
                    env = env._replace(top = False)
            environments[x][y] = env
        # 2. create routing blocks and place them into the grids
        for x, y in product(range(context.top.width - 1), range(context.top.height - 1)):
            neg, xofs_neg, yofs_neg = grid[x][y]
            # 2.1 xconn
            if x > 0 and (neg is None or yofs_neg == neg.height - 1):
                pos, xofs_pos, _ = grid[x][y+1]
                env = (neg.name if neg else None, xofs_neg, pos.name if pos else None, xofs_pos)
                _logger.debug("Try fulfilling location ({}, {}, x), env: bottom({}, {}), top({}, {})"
                        .format(x, y, env[0], env[1], env[2], env[3]))
                xconn = xcbs.get(env, None)
                if xconn is None:
                    xconn = ConnectionBlock('xcb_{}'.format(len(xcbs)), Dimension.x)
                xconn = self._place_routing_block(context.top, x, y, xconn)
                xcbs.setdefault(env, xconn)
                context._modules.setdefault(xconn.name, xconn)
                if env in xconn._ext.get("routing_environments", []):
                    _logger.debug("Reusing connection block: {}".format(xconn.name))
                else:
                    _logger.debug("Updating connection block: {}".format(xconn.name))
                    xconn._ext.setdefault("routing_environments", []).append(env)
                    if len(xconn._ext["routing_environments"]) > 1:
                        _logger.warning(_errinfo_multifit.format(xconn.name))
                    xconn.populate_segments(segments, True)
                    xconn.implement_fc(segments, Direction.neg, neg,
                            self._block_fc.get(neg.name if neg else None, self._default_fc))
                    xconn.implement_fc(segments, Direction.pos, pos,
                            self._block_fc.get(pos.name if pos else None, self._default_fc))
            # 2.2 yconn
            if y > 0 and (neg is None or xofs_neg == neg.width - 1):
                pos, _, yofs_pos = grid[x+1][y]
                env = (neg.name if neg else None, yofs_neg, pos.name if pos else None, yofs_pos)
                _logger.debug("Try fulfilling location ({}, {}, y), env: left({}, {}), right({}, {})"
                        .format(x, y, env[0], env[1], env[2], env[3]))
                yconn = ycbs.get(env, None)
                if yconn is None:
                    yconn = ConnectionBlock('ycb_{}'.format(len(ycbs)), Dimension.y)
                yconn = self._place_routing_block(context.top, x, y, yconn)
                ycbs.setdefault(env, yconn)
                context._modules.setdefault(yconn.name, yconn)
                if env in yconn._ext.get("routing_environments", []):
                    _logger.debug("Reusing connection block: {}".format(yconn.name))
                else:
                    _logger.debug("Updating connection block: {}".format(yconn.name))
                    yconn._ext.setdefault("routing_environments", []).append(env)
                    if len(yconn._ext["routing_environments"]) > 1:
                        _logger.warning(_errinfo_multifit.format(yconn.name))
                    yconn.populate_segments(segments, True)
                    yconn.implement_fc(segments, Direction.neg, neg,
                            self._block_fc.get(neg.name if neg else None, self._default_fc))
                    yconn.implement_fc(segments, Direction.pos, pos,
                            self._block_fc.get(pos.name if pos else None, self._default_fc))
            # 2.3 switch
            if neg is None or xofs_neg == neg.width - 1 or yofs_neg == neg.height - 1:
                env = environments[x][y]
                _logger.debug("Try fulfilling location ({}, {}, s), env: {}"
                        .format(x, y, env))
                switch = sbs.get(env, None)
                if switch is None:
                    switch = SwitchBlock('sb_{}'.format(len(sbs)))
                switch = self._place_routing_block(context.top, x, y, switch)
                sbs.setdefault(env, switch)
                context._modules.setdefault(switch.name, switch)
                if env in switch._ext.get("routing_environments", []):
                    _logger.debug("Reusing switch block: {}".format(switch.name))
                else:
                    _logger.debug("Updating switch block: {}".format(switch.name))
                    switch._ext.setdefault("routing_environments", []).append(env)
                    if len(switch._ext["routing_environments"]) > 1:
                        _logger.warning(_errinfo_multifit.format(switch.name))
                    switch.populate_segments(segments, env, True)
                    switch.implement_wilton(segments)
        self._complete_ports(context.top, True)
