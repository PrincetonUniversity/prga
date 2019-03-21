# Python 2 and 3 compatible
from prga.compatible import *

"""Generate simulation testbench."""

from prga._util.util import uno

import jinja2 as jj
import os
from collections import OrderedDict
import re
from copy import deepcopy
import sys

_py3 = sys.version_info >= (3, )

def _update_progs(progs, array, prefix = '', global_base = 0):
    for instance in itervalues(array.physical_instances):
        if instance.is_array:
            _update_progs(progs, instance.model, prefix + instance.name + '.',
                    global_base + instance._ext["cfg_offset"])
        else:
            progs.append( (prefix + instance.name, global_base + instance._ext["cfg_offset"],
                instance.model._ext["cfg_bits"]) )

def generate_testbench(context, output, target, host, reverse_bindings,
        target_parameters = None, host_parameters = None, clk_period = 10.0, post_synthesis_sim = False,
        **kwargs):
    """Generate simluation testbench.

    Args:
        context (`ArchitectureContext`): the architecture context of the custom FPGA
        output (:obj:`str`): the name of the output file
        target (``VerilogModule``):
            the top-level module of the target
        host (``VerilogModule``):
            the top-level module of the test host
        reverse_bindings (:obj:`dict`): a mapping from \(x, y, subbblock\) to pin name
        target_parameters (:obj:`dict`): a mapping from parameter name to value
        host_parameters (:obj:`dict`): a mapping from parameter name to value
        clk_period (:obj:`float`): the testing clock period
        post_synthesis_sim (:obj:`bool`): if set, code is injected for post-synthesis simulation
        **kwargs: optional key-value arguments specific to a configuration circuitry type

    See `hdlparse <//kevinpt.github.io/hdlparse/apidoc/hdlparse.html#hdlparse.verilog_parser.VerilogModule>`_ for info
    on ``VerilogModule``.
    """
    # get verilog template
    env = jj.Environment(loader=jj.FileSystemLoader(
        os.path.join(os.path.abspath(os.path.dirname(__file__)), 'verilog_templates')))

    # extract target information
    width_reprog = re.compile('^.*?\[\s*(?P<start>\d+)\s*:\s*(?P<end>\d+)\s*\].*?$')

    target_info = {'name': target.name, 'parameters': uno(target_parameters, {})}
    target_ports = target_info['ports'] = {}
    for port in target.ports:
        matched = width_reprog.match(port.data_type)
        if matched is None:
            target_ports[port.name] = None
        else:
            target_ports[port.name] = abs(int(matched.group('start')) - int(matched.group('end'))) + 1

    host_info = {'name': host.name, 'parameters': uno(host_parameters, {})}

    reverse_bindings = deepcopy(reverse_bindings)
    ports = OrderedDict()
    # 1. global wires
    for global_ in itervalues(context.globals):
        bound = reverse_bindings.pop(global_.binding, '')
        if bound.startswith('out:'):
            ports[global_.name] = bound[4:]
        else:
            ports[global_.name] = bound
    # 2. IOs
    for tile in itervalues(context.top.physical_instances):
        if tile.is_io_block:
            bound = reverse_bindings.pop(tile.position, '')
            i = tile.physical_pins['extio_i']
            o = tile.physical_pins['extio_o']
            if bound.startswith('out:'):
                ports['{}_{}'.format(tile.name, i.name)] = ''
                ports['{}_{}'.format(tile.name, o.name)] = bound[4:]
            else:
                ports['{}_{}'.format(tile.name, i.name)] = bound
                ports['{}_{}'.format(tile.name, o.name)] = ''
    if reverse_bindings:
        raise RuntimeError('{} is not connected'.format(next(reverse_bindings.keys())))

    progs = []
    _update_progs(progs, context.top)

    bs_size = context.top._ext["cfg_bits"]
    bs_wordsize = kwargs.get('bs_wordsize', 16)
    open(output, 'wb' if _py3 else 'w').write(env.get_template('bitchain.tmpl.v').render({
        'target': target_info,
        'host': host_info,
        'config': { 'bs_size': bs_size,
                    'bs_wordsize': bs_wordsize,
                    'bs_num_words': (bs_size // bs_wordsize + (1 if bs_size % bs_wordsize else 0)),
                    },
        'guest': {  'name': context.top.name,
                    'ports': ports,
                    'progs': progs,
                    },
        'clk_period': clk_period,
        'iteritems': iteritems,
        'post_synthesis_sim': post_synthesis_sim,
        }).encode('ascii'))
