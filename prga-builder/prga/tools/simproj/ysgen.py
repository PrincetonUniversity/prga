# Python 2 and 3 compatible
from prga.compatible import *

"""Generate the simluation project's synthesis script."""

import jinja2 as jj
import os
import sys

_py3 = sys.version_info >= (3, )

def generate_yosys(context, output, target, target_sources, target_includes, target_defines, target_parameters):
    """"Generate the simluation project's synthesis script.

    Args:
        context (`ArchitectureContext`): the architecture context of the custom FPGA
        output (:obj:`str`): the name of the output file
        target (:obj:`str`): the name of the top-level module of the target
        target_sources (:obj:`list` [:obj:`str` ]): a list of target source files
        target_includes (:obj:`list` [:obj:`str` ]): a list of include directories
        target_defines (:obj:`list` [:obj:`str` ]): a list of macros
        target_parameters (:obj:`dict` [:obj:`str` -> :obj:`str` ]): a mapping from parameter names to values
    """
    # get template
    env = jj.Environment(loader=jj.FileSystemLoader(
        os.path.join(os.path.abspath(os.path.dirname(__file__)), 'yosys_templates')))

    # find the max lut size
    max_lut_size = max(lut.width for lut in itervalues(context.primitives) if lut.is_lut_primitive)

    # generate the synthesis script
    open(output, 'wb' if _py3 else 'w').write(env.get_template('synth.tmpl.ys').render({
        'max_lut_size': max_lut_size,
        'verilog_top': target,
        'verilog_sources': target_sources,
        'verilog_includes': target_includes,
        'verilog_defines': target_defines,
        'verilog_parameters': target_parameters,
        }).encode('ascii'))
