# -*- encoding: ascii -*-

"""Remap IO block type in VPR's packing result to match the IO bindings."""

from xmltodict import parse, unparse
import sys
import argparse
import re

parser = argparse.ArgumentParser(description="Fix VPR's IO block packing")
parser.add_argument('-x', '--width', metavar='WIDTH', type=int, dest='x', required=True,
        help='Width of the architecture')
parser.add_argument('-y', '--height', metavar='HEIGHT', type=int, dest='y', required=True,
        help='height of the architecture')
parser.add_argument('-b', '--binding', metavar='io.pads', type=str, dest='binding', required=True,
        help='The IO binding file')
parser.add_argument('-i', '--input', metavar='*.net', type=str, dest='net', required=True,
        help='VPR\'s packing result')
parser.add_argument('-o', '--output', metavar='output.net', type=str, dest='output', default='output.net',
        help="Output file name. 'output.net' by default")

def fix_io(d, old, new):
    if isinstance(d, basestring):
        return d.replace(old, new)
    elif isinstance(d, list):
        return map(lambda x: fix_io(x, old, new), d)
    elif isinstance(d, dict):
        return dict( (k, fix_io(v, old, new)) for k, v in d.iteritems())
    else:
        return d

def fix(block, blocks):
    if block['@name'] in blocks:
        old = re.match('^(?P<old>.*?)\[\d+\]$', block['@instance']).groupdict()['old']
        return fix_io(block, old, blocks[block['@name']])
    else:
        return block

if __name__ == '__main__':
    args = parser.parse_args()
    blocks = {}
    for line in open(args.binding):
        line = line.strip()
        if line.startswith('#'):
            continue
        name, x, y, _ = line.split()
        x, y = map(int, (x, y))
        blocks[name] = ('IO_LEFT' if x == 0 else
                'IO_RIGHT' if x == args.x - 1 else
                'IO_BOTTOM' if y == 0 else
                'IO_TOP' if y == args.y - 1 else None)
        if blocks[name] is None:
            raise RuntimeError("'{}' is None".format(name))
    d = parse(open(args.net))
    d['block']['@name'] = args.output
    d['block']['block'] = map(lambda x: fix(x, blocks), d['block']['block'])
    unparse(d, open(args.output, 'w'), full_document=True, pretty=True)
