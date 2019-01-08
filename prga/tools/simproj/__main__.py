# -*- encoding: ascii -*-

"""PRGA tool for generating a simulation project for a target design."""

from tbgen import generate_testbench
from mkgen import generate_makefile
from ysgen import generate_yosys

from prga.context import ArchitectureContext
import argparse as ap

if __name__ == '__main__':
    parser = ap.ArgumentParser(prog='simproj',
            description='Generating a project for simulating TARGET using GUEST fpga')
    parser.add_argument('ctx', type=str, metavar='CTX.pickled',
            help='The pickled architecture context')
    parser.add_argument('target', type=str, metavar='TARGET.v',
            help='The top-level target Verilog module to be implemented on the FPGA')
    parser.add_argument('host', type=str, metavar='HOST.v',
            help='The test host Verilog module')
    parser.add_argument('iob', type=str, metavar='IO.pads',
            help='Pin binding constraints')
    parser.add_argument('-t', '--testbench', type=str, metavar='FILE_NAME', dest='testbench', default='testbench.v',
            help='The output testbench Verilog module. Default = testbench.v')
    parser.add_argument('-m', '--makefile', type=str, metavar='FILE_NAME', dest='makefile', default='Makefile',
            help='The output Makefile. Default = Makefile')
    parser.add_argument('-y', '--yosys', type=str, metavar='FILE_NAME', dest='yosys', default='synth.ys',
            help='The output yosys script. Default = synth.ys')
    parser.add_argument('--clk_period', type=float, metavar='PERIOD', default=10.0,
            help='Clock period. Defaut = 10.0')
    parser.add_argument('--bs_wordsize', type=int, metavar='SIZE', default=16,
            help='Bitstream word size. Default = 16')

    args = parser.parse_args()

    # context
    ctx = ArchitectureContext.unpickle(args.ctx)

    # generate testbench
    generate_testbench(ctx, args.testbench, args.target, args.host, args.iob,
            clk_period = args.clk_period, bs_wordsize = args.bs_wordsize)

    # generate synthesis script
    generate_yosys(ctx, args.yosys)

    # generate Makefile
    generate_makefile(ctx, args.makefile, args.target, args.host, args.iob, args.testbench, args.yosys,
            bs_wordsize = args.bs_wordsize)
