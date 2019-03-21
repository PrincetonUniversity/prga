# -*- encoding: ascii -*-

"""PRGA tool for generating a simulation project for a target design."""

from prga.tools.simproj._util import find_verilog_top, parse_io_bindings, parse_parameters
from prga.tools.simproj.tbgen import generate_testbench
from prga.tools.simproj.mkgen import generate_makefile
from prga.tools.simproj.ysgen import generate_yosys

from prga import ArchitectureContext
import argparse as ap

if __name__ == '__main__':
    parser = ap.ArgumentParser(prog='simproj',
            description=('Generating a project for simulating TARGET using GUEST fpga. '
                'Currently only works for bitchain-style FPGA in which all IO blocks are instantiated in the '
                'top-level array'))

    parser.add_argument('-c', '--compiler', type=str, metavar='COMP', default='iverilog', choices=['iverilog', 'vcs'],
            dest='compiler', help='required: The compiler for simulation. Default = iverilog')

    parser.add_argument('-a', '--context', type=str, metavar='CTX.pickled', dest='ctx',
            help='required: The pickled architecture context')

    parser.add_argument('--fpga_prefix', type=str, metavar='FPGA', dest='fpga_prefix',
            help='optional: The prefix of all FPGA files. Default = "."')

    parser.add_argument('--rtl_dir', type=str, metavar='RTL', dest='rtl', default='rtl',
            help='optional: The folder containing all RTL files. Default = rtl')

    parser.add_argument('--config_db', type=str, metavar='CONFIG.db', dest='config_db', default='config.db',
            help='optional: The configuration database. Default = config.db')

    parser.add_argument('--vpr_archdef', type=str, metavar='ARCHDEF.xml', dest='vpr_archdef',
            default='arch.vpr.xml', help='optional: The VPR architecture definition XML. Default = arch.vpr.xml')

    parser.add_argument('--vpr_rrgraph', type=str, metavar='RRGRAPH.xml', dest='vpr_rrgraph',
            default='rrg.vpr.xml', help='optional: The VPR routing resource graph XML. Default = rrg.vpr.xml')

    parser.add_argument('-b', '--io_bindings', type=str, metavar='IO.pads', dest='iob',
            help='required: Pin binding constraints')

    parser.add_argument('-v', '--target', type=str, nargs='*', metavar='TARGET1.v TARGET2.v ...', dest='targets',
            help='required, multiple: Target design to be implemented on the FPGA')

    parser.add_argument('--target_top', type=str, metavar='TARGET', dest='target_top',
            help='optional: The name of the top-level module. Required if the target design has hierarchy')

    parser.add_argument('--target_include', type=str, nargs='*', metavar='DIR1 DIR2 ...', dest='target_includes',
            default=[], help='optional, multiple: Include dir for the target design')

    parser.add_argument('--target_define', type=str, nargs='*', metavar='MACRO1 MACRO2=VALUE ...',
            default=[], dest='target_defines', help='optional, multiple: Macros to be defined for the target design')

    parser.add_argument('--target_parameter', type=str, nargs='*', metavar='PARAMETER1=VALUE PARAMTER2=VALUE ...',
            default=[], dest='target_parameters', help='optional, multiple: Parameters to be set in the target design')

    parser.add_argument('-x', '--host', type=str, nargs='*', metavar='HOST1.v HOST2.v ...', dest='hosts',
            help='required, multiple: Target design to be implemented on the FPGA')

    parser.add_argument('--host_top', type=str, metavar='HOST', dest='host_top',
            help='optional: The name of the top-level module. Required if the host has hierarchy')

    parser.add_argument('--host_include', type=str, nargs='*', metavar='DIR1 DIR2 ...', dest='host_includes',
            default=[], help='optional, multiple: Include dir for the host')

    parser.add_argument('--host_define', type=str, nargs='*', metavar='MACRO1 MACRO2=VALUE ...', dest='host_defines',
            default=[], help='optional, multiple: Macros to be defined for the host')

    parser.add_argument('--host_parameter', type=str, nargs='*', metavar='PARAMETER1=VALUE PARAMTER2=VALUE ...',
            default=[], dest='host_parameters', help='optional, multiple: Parameters to be set in the host design')

    parser.add_argument('--host_args', type=str, nargs='*', metavar='ARG1 ARG2 ...', dest='host_args',
            default=[], help='optional, multiple: +Args for running the host simulation')

    parser.add_argument('-t', '--testbench', type=str, metavar='TESTBENCH.v', dest='testbench', default='testbench.v',
            help='optional: The output testbench Verilog module. Default = testbench.v')

    parser.add_argument('-m', '--makefile', type=str, metavar='MAKEFILE', dest='makefile', default='Makefile',
            help='optional: The output Makefile. Default = Makefile')

    parser.add_argument('-y', '--yosys', type=str, metavar='SYNTH.ys', dest='yosys', default='synth.ys',
            help='optional: The output yosys script. Default = synth.ys')

    parser.add_argument('--clk_period', type=float, metavar='PERIOD', default=10.0,
            help='optional: Simulation clock period. Defaut = 10.0')

    parser.add_argument('--enable_fake_prog', action='store_true', dest='fake_prog', default=False,
            help='optional: Enable fast programming in simulation')

    parser.add_argument('--bs_wordsize', type=int, metavar='SIZE', default=16,
            help='optional: Bitstream word size. Default = 16')

    parser.add_argument('--enable_post_synthesis_simulation', action='store_true', dest='post_synthesis_sim', default=False,
            help='optional: Enable post-synthesis simulation.')

    args = parser.parse_args()

    if args.ctx is None:
        parser.print_help()
        raise RuntimeError("Missing required argument: -a/--context")

    if args.rtl is None:
        parser.print_help()
        raise RuntimeError("Missing required argument: -r/--rtl_dir")

    if args.iob is None:
        parser.print_help()
        raise RuntimeError("Missing required argument: -b/--io_bindings")

    if not args.targets:
        parser.print_help()
        raise RuntimeError("Missing required argument: -v/--target")

    if not args.hosts:
        parser.print_help()
        raise RuntimeError("Missing required argument: -x/--host")

    # context
    ctx = ArchitectureContext.unpickle(args.ctx)

    # top-level module of the target
    target = find_verilog_top(args.targets, args.target_top)

    # target parameters
    target_parameters = parse_parameters(args.target_parameters)

    # top-level module of the host
    host = find_verilog_top(args.hosts, args.host_top)

    # host parameters
    host_parameters = parse_parameters(args.host_parameters)

    # reverse io bindings
    reverse_bindings = parse_io_bindings(args.iob)

    # generate testbench
    generate_testbench(ctx, args.testbench, target, host, reverse_bindings, target_parameters, host_parameters,
            clk_period = args.clk_period, bs_wordsize = args.bs_wordsize, post_synthesis_sim = args.post_synthesis_sim)

    # generate synthesis script
    generate_yosys(ctx, args.yosys, target.name, args.targets,
            args.target_includes, args.target_defines, target_parameters)

    # generate Makefile
    generate_makefile(ctx, args.makefile, target.name,
            args.targets, args.target_includes, args.target_defines,
            args.hosts, args.host_includes, args.host_defines,
            args.host_args, args.iob, args.testbench, args.yosys, args.compiler,
            bs_wordsize = args.bs_wordsize, fpga_prefix = args.fpga_prefix,
            fake_prog = args.fake_prog, post_synthesis_sim = args.post_synthesis_sim)
