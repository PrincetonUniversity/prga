# Python 2 and 3 compatible
from prga.compatible import *

from prga._context.flow import AbstractPass
from prga._context.vpr.delegate import DelegateImpl

import sys

_py3 = sys.version_info >= (3, )

# ----------------------------------------------------------------------------
# -- VPR XML Input Generator -------------------------------------------------
# ----------------------------------------------------------------------------
class VPRXMLGenerator(AbstractPass):
    """VPR's archdef.xml and rrg.xml generation tool.

    Args:
        arch_filename (:obj:`str`): name of the output archdef.xml
        rrg_filename (:obj:`str`): name of the output rrg.xml
    """
    def __init__(self, arch_filename = 'arch.vpr.xml', rrg_filename = 'rrg.vpr.xml'):
        self._arch_filename = arch_filename
        self._rrg_filename = rrg_filename

    @property
    def key(self):
        """Key of this pass."""
        return "vpr.xml"

    @property
    def dependences(self):
        """Passes that this pass depends on."""
        return ("vpr.id", )

    def run(self, context):
        delegate = DelegateImpl(context)
        delegate.gen_arch_xml(open(self._arch_filename, 'wb' if _py3 else 'w'), True)
        delegate.gen_rrg_xml(open(self._rrg_filename, 'wb' if _py3 else 'w'), True)
