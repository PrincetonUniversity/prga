# Python 2 and 3 compatible
from prga.compatible import *

from prga._archdef.common import NetType
from prga._archdef.portpin.common import NetBundle
from prga._util.util import uno, register_extension
from prga._context.flow import AbstractPass

import jinja2
import os
import sys

_py3 = sys.version_info >= (3, )

register_extension("verilog_template", __name__)
register_extension("verilog_template_search_paths", __name__)

# ----------------------------------------------------------------------------
# -- Verilog Generator -------------------------------------------------------
# ----------------------------------------------------------------------------
class VerilogGenerator(AbstractPass):
    """Verilog generator.

    Args:
        output_dir (:obj:`str`): the directory where all generated verilog files will be put in
    """
    def __init__(self, output_dir = 'rtl'):
        self.__output_dir = output_dir
        self._env = None

    @property
    def key(self):
        """Key of this pass."""
        return "rtl.verilog"

    def __bundle2verilog(self, bundle):
        """Convert to Verilog string.
        
        Args:
            bundle (`NetBundle`): bundled net bits

        Returns:
            :obj:`str`:
        """
        if bundle.type is NetType.open:
            return "{}'bx".format(bundle.high)
        elif bundle.type is NetType.zero:
            return "{}'b0".format(bundle.high)
        elif bundle.type is NetType.one:
            return "{}'b1".format(bundle.high)
        elif bundle.type is NetType.port:
            if bundle.low == 0 and bundle.high == bundle.bus.width - 1:
                return bundle.bus.name
            elif bundle.low == bundle.high:
                return '{}[{}]'.format(bundle.bus.name, bundle.low)
            else:
                return '{}[{}:{}]'.format(bundle.bus.name, bundle.high, bundle.low)
        else:
            if bundle.low == 0 and bundle.high == bundle.bus.width - 1:
                return '{}__{}'.format(bundle.bus.parent.name, bundle.bus.name)
            elif bundle.low == bundle.high:
                return '{}__{}[{}]'.format(bundle.bus.parent.name, bundle.bus.name, bundle.low)
            else:
                return '{}__{}[{}:{}]'.format(bundle.bus.parent.name, bundle.bus.name,
                        bundle.high, bundle.low)

    def __bits2verilog(self, bits):
        """Convert a sequence of bits to a verilog string."""
        if bits is None:
            return ''
        bundled = NetBundle.Bundle(bits)
        if len(bundled) == 1:
            if bundled[0].is_open:
                return ''
            else:
                return self.__bundle2verilog(bundled[0])
        else:
            return '{{{}}}'.format(', '.join(map(self.__bundle2verilog, reversed(bundled))))

    def run(self, context):
        if not os.path.isdir(self.__output_dir):
            os.mkdir(self.__output_dir)
        search_paths = context._ext.get("verilog_template_search_paths", [])
        search_paths.append(os.path.join(os.path.abspath(os.path.dirname(__file__)),
            'verilog_templates'))
        self._env = jinja2.Environment(loader=jinja2.FileSystemLoader(search_paths))
        for module in itervalues(context._modules):
            if not module.is_physical:
                continue
            template = module._ext.get("verilog_template", "module.tmpl.v")
            f = open(os.path.join(self.__output_dir, module.name + '.v'), 'wb' if _py3 else 'w')
            f.write(self._env.get_template(template).render({
                'module': module, 'bits2verilog': self.__bits2verilog,
                'itervalues': itervalues, 'iteritems': iteritems,
                }).encode('ascii'))
