# -*- encoding: ascii -*-

"""Generate simulation testbench."""

from prga._configcircuitry.common import ConfigurationCircuitryType
from prga._util.util import uno

import jinja2 as jj
import os
import itertools as it
from collections import OrderedDict as od
from hdlparse.verilog_parser import VerilogExtractor as Vex 
import re

def generate_testbench(context, output, target, host, io_bindings,
        host_portmap = None, clk_period = 10.0, 
        **kwargs):
    """Generate simluation testbench.

    Args:
        context (`ArchitectureContext`): the architecture context of the custom FPGA
        output (:obj:`str`): the name of the output file
        target (:obj:`str`): the name of the target Verilog file
        host (:obj:str`): the name of the test host verilog file
        io_bindings (:obj:`str`): the name of the IO binding constraints file
        host_portmap (:obj:`dict`, default={}): a mapping from target verilog's port name to host verilog's port name
        clk_period (:obj:`float`, default=10.0): the testing clock period
        **kwargs: optional key-value arguments specific to a configuration circuitry type
    """
    # check configuration circuitry type
    cfg_ext = context._config_extension
    if cfg_ext is None:
        raise RuntimeError("Configuration circuitry has not been injected into the architecture")

    # get verilog template
    env = jj.Environment(loader=jj.FileSystemLoader(
        os.path.join(os.path.abspath(os.path.dirname(__file__)), 'verilog_templates')))

    # build reverse IO binding map
    reverse_bindings = {}
    for line in open(io_bindings):
        if line.strip().startswith('#') or line.strip() == '':
            continue
        name, x, y, subblock = line.strip().split()
        reverse_bindings[tuple(map(int, (x, y, subblock)))] = name
    
    # extract target information
    target_mod = Vex().extract_objects(target)
    if len(target_mod) != 1:
        raise RuntimeError('Only one module is allowed in TARGET.v')
    target_mod = target_mod[0]
    width_reprog = re.compile('^.*?\[(?P<start>\d+):(?P<end>\d+)\].*?$')

    target = {'name': target_mod.name}
    target_ports = target['ports'] = {}
    for port in target_mod.ports:
        matched = width_reprog.match(port.data_type)
        if matched is None:
            target_ports[port.name] = 1
        else:
            target_ports[port.name] = abs(int(matched.group('start')) - int(matched.group('end'))) + 1

    # extract host information
    host_mod = Vex().extract_objects(host)
    if len(host_mod) != 1:
        raise RuntimeError('Only one module is allowed in HOST.v')
    host_mod = host_mod[0]

    if cfg_ext.type is ConfigurationCircuitryType.bitchain:
        ports = od()
        # 1. global wires
        for global_ in context.globals.itervalues():
            bound = reverse_bindings.pop(global_.binding, '')
            if bound.startswith('out:'):
                ports[global_.name] = bound[4:]
            else:
                ports[global_.name] = bound
        # 2. IOs
        for tile in context.array._iter_tiles():
            if tile.is_root:
                for subblock, instance in enumerate(tile.block_instances):
                    if not instance.is_physical:
                        continue
                    bound = reverse_bindings.pop((tile.x, tile.y, subblock), '')
                    for pin in it.ifilter(lambda x: not x.is_logical and x.port.is_external,
                            instance._physical_pins.itervalues()):
                        if (pin.port[0]._logical_cp is None or
                                ((pin.port[0]._logical_cp.parent.name == 'inpad') ==
                                    bound.startswith('out:'))):
                            ports['{}_{}'.format(instance.name, pin.name)] = ''
                        elif bound.startswith('out:'):
                            ports['{}_{}'.format(instance.name, pin.name)] = bound[4:]
                        else:
                            ports['{}_{}'.format(instance.name, pin.name)] = bound
        if reverse_bindings:
            raise RuntimeError('{} is not connected'.format(next(reverse_bindings.keys())))
        open(output, 'w').write(env.get_template('bitchain.tmpl.v').render({
            'target': target,
            'config': { 'width': cfg_ext.width,
                        'bs_size': cfg_ext._bitstream_size,
                        'bs_wordsize': kwargs.get('bs_wordsize', 16),
                        },
            'host': {   'name': host_mod.name,
                        'portmap': uno(host_portmap, {}),
                        },
            'guest': {  'name': context.name,
                        'ports': ports,
                        },
            'clk_period': clk_period,
            }).encode('ascii'))
    else:
        raise RuntimeError("Unknown configuration circuitry type: {}".format(
            cfg_ext.type.name))
