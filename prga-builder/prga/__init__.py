from prga._archdef.common import PrimitivePortClass, Side
from prga._context.context import ArchitectureContext

import logging
_logger = logging.getLogger(__name__)

import sys

_hdl = logging.StreamHandler(sys.stdout)
_fmt = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
_hdl.setFormatter(_fmt)
_logger.addHandler(_hdl)

_logger.setLevel(logging.INFO)

__all__ = ["PrimitivePortClass", "Side", "ArchitectureContext"]
