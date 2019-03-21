# Python 2 and 3 compatible
from prga.compatible import *

from hdlparse.verilog_parser import VerilogExtractor as Vex
from hdlparse.verilog_parser import VerilogModule

def find_verilog_top(files, top):
    """Find and parse the top-level module in a list of Verilog files.

    Args:
        files (:obj:`list` [:obj:`str` ]): Verilog files
        top (:obj:`str`, or None): the name of the top-level module if there are more than one modules in the Verilog
            files

    Returns:
        `VerilogModule
        <https://kevinpt.github.io/hdlparse/apidoc/hdlparse.html#hdlparse.verilog_parser.VerilogModule>`_:
    """
    mods = {x.name : x for f in files for x in Vex().extract_objects(f)}
    if top is not None:
        try:
            return mods[top]
        except KeyError:
            raise RuntimeError("Module '{}' is not found in the file(S)")
    elif len(mods) > 1:
        raise RuntimeError('Multiple modules found in the file(s) but no top is specified')
    else:
        return next(iter(itervalues(mods)))

def parse_io_bindings(io_bindings):
    """Parse the IO binding constraint file.

    Args:
        io_bindings (:obj:`str`): the IO binding constraint file

    Returns:
        :obj:`dict`: a mapping from \(x, y, subblock\) to pin name
    """
    reverse_bindings = {}
    for line in open(io_bindings):
        if line.strip().startswith('#') or line.strip() == '':
            continue
        name, x, y, subblock = line.strip().split()
        reverse_bindings[tuple(map(int, (x, y, subblock)))] = name
    return reverse_bindings

def parse_parameters(parameters):
    """Parse the parameters defined via command-line arguments.

    Args:
        parameters (:obj:`list` [:obj:`str` ]): a list of 'PARAMETER=VALUE' strings

    Returns:
        :obj:`dict`: a mapping from parameter name to value
    """
    mapping = {}
    for p in parameters:
        k, v = p.split('=')
        mapping[k] = v
    return mapping
