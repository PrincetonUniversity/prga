# -*- encoding: ascii -*-

"""Generate the simluation project's synthesis script."""

import jinja2 as jj
import os

def generate_yosys(context, output):
    """"Generate the simluation project's synthesis script.

    Args:
        context (`ArchitectureContext`): the architecture context of the custom FPGA
        output (:obj:`str`): the name of the output file
    """
    # get template
    env = jj.Environment(loader=jj.FileSystemLoader(
        os.path.join(os.path.abspath(os.path.dirname(__file__)), 'yosys_templates')))

    # find the max lut size
    max_lut_size = max(lut.width for lut in context._models.itervalues()
            if lut.is_lut)

    # generate the synthesis script
    open(output, 'w').write(env.get_template('synth.tmpl.ys').render({
        'max_lut_size': max_lut_size}).encode('ascii'))
