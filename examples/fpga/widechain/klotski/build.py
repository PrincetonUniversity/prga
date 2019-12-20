# -*- encoding: ascii -*-
from prga.compatible import *

from prga.api.context import *
from prga.api.flow import *
from prga.api.config import *

from itertools import chain, product

class MyGuide(ConfigWidechainInjectionGuide):

    def __init__(self, M, N, m, n):
        # array = M x N regions
        # region = m x n tiles
        self.M = M
        self.N = N
        self.m = m
        self.n = n

    def __iterate_region_column(self, module, x, sbox = False):
        if sbox:
            for y in range(module.height):
                sbox = module.sbox_instances.get( (x, y - 1) )
                if sbox is not None:
                    yield None, sbox
        else:
            for y in reversed(range(module.height)):
                tile = module.element_instances.get( (x, y) )
                if tile is not None:
                    yield None, tile
                if x > 0 or not module.channel_coverage.west:
                    continue
                sbox = module.sbox_instances.get( (-1, y - 1) )
                if sbox is not None:
                    yield None, sbox

    def __iterate_top(self, module):
        for X, x in product(range(self.M), range(self.m)):
            for Y in reversed(range(self.N)):
                pos = (1 + X * self.m, 1 + Y * self.n)
                instance = module.element_instances.get( pos )
                if instance is not None:
                    yield 2 * x, instance
            for Y in range(self.N):
                pos = (1 + X * self.m, 1 + Y * self.n)
                instance = module.element_instances.get( pos )
                if instance is not None:
                    yield 2 * x + 1, instance

    def chain_groups(self, module):
        if module.module_class.is_array:
            if module.name.startswith("region"):
                for x in range(module.width):
                    yield 2 * x, self.__iterate_region_column(module, x)
                    yield 2 * x + 1, self.__iterate_region_column(module, x, True)
            else:
                assert module.name == "top"
                yield None, self.__iterate_top(module)
        else:
            yield None, iter( (None, instance) for instance in itervalues(module.logical_instances))

    def injection_level(self, module):
        if module.module_class.is_array:
            if module.name.startswith("region"):
                return 1
            else:
                assert module.name == "top"
                return 2
        else:
            return 0

def run():
    M, N, m, n = 3, 3, 2, 2
    region_width, region_height = m, n
    width, height = M * m + 2, N * n + 1
    context = ArchitectureContext('top', width, height, WidechainConfigCircuitryDelegate, config_width = 4)

    # 1. routing stuff
    clk = context.create_global('clk', is_clock = True, bind_to_position = (1, height - 1))
    context.create_segment('L1', 16, 1)
    # context.create_segment('L2', 16, 2)
    # context.create_segment('L4', 8, 4)

    # 2. create IOB
    iob = context.create_io_block('iob', 4)
    while True:
        outpad = iob.create_input('outpad', 1)
        inpad = iob.create_output('inpad', 1)
        ioinst = iob.instances['io']
        iob.connect(ioinst.pins['inpad'], inpad)
        iob.connect(outpad, ioinst.pins['outpad'])
        break

    # 3. create tile
    iotile = context.create_tile('io_tile', iob, Orientation.north)

    # 4. create cluster
    cluster = context.create_cluster('cluster')
    while True:
        clkport = cluster.create_input('clk', 1)
        inport = cluster.create_input('in', 4)
        outport = cluster.create_output('out', 1)
        lut = cluster.instantiate(context.primitives['lut4'], 'lutinst')
        ff = cluster.instantiate(context.primitives['flipflop'], 'ffinst')
        cluster.connect(inport, lut.pins['in'])
        cluster.connect(lut.pins['out'], outport)
        cluster.connect(clkport, ff.pins['clk'])
        cluster.connect(lut.pins['out'], ff.pins['D'])
        cluster.connect(ff.pins['Q'], outport)
        break

    # 5. create CLB
    clb = context.create_logic_block('clb')
    while True:
        clkport = clb.create_global(clk, Orientation.south)
        inport = clb.create_input('in', 16, Orientation.west)
        outport = clb.create_output('out', 4, Orientation.east)
        for i in range(4):
            clusterinst = clb.instantiate(cluster, 'cluster{}'.format(i))
            clb.connect(inport[i*4:(i+1)*4], clusterinst.pins['in'])
            clb.connect(clkport, clusterinst.pins['clk'])
            clb.connect(clusterinst.pins['out'], outport[i])
        break

    # 6. create tile
    clbtile = context.create_tile('clb_tile', clb)

    # 7. regions
    coverage_wes = ChannelCoverage(south = True, east = True, west = True)
    coverage_es = ChannelCoverage(south = True, east = True)
    regions = {
            "A": context.create_array("region_A", region_width, region_height, coverage_wes, coverage_wes),
            "B": context.create_array("region_B", region_width, region_height, coverage_wes),
            "C": context.create_array("region_C", region_width, region_height, coverage_wes),
            "D": context.create_array("region_D", region_width, region_height, coverage_es, coverage_wes),
            "E": context.create_array("region_E", region_width, region_height, coverage_es),
            "F": context.create_array("region_F", region_width, region_height, coverage_es),
            "G": context.create_array("region_G", region_width, region_height, coverage_es, coverage_wes),
            "H": context.create_array("region_H", region_width, region_height, coverage_es),
            "I": context.create_array("region_I", region_width, region_height, coverage_es),
            }

    # 7.1 region A, D, F:
    for r in ("A", "D", "G"):
        for x in range(region_width):
            regions[r].instantiate_element(iotile, (x, region_height - 1))
        for pos in product(range(region_width), range(region_height - 1)):
            regions[r].instantiate_element(clbtile, pos)

    # 7.2 other regions:
    for r in ("B", "C", "E", "F", "H", "I"):
        for pos in product(range(region_width), range(region_height)):
            regions[r].instantiate_element(clbtile, pos)

    # 8. fill top-level array
    for x, y in product(range(M), range(N)):
        if x == 0:
            if y == 0:
                context.top.instantiate_element(regions["C"], (x * m + 1, y * n + 1))
            elif y == N - 1:
                context.top.instantiate_element(regions["A"], (x * m + 1, y * n + 1))
            else:
                context.top.instantiate_element(regions["B"], (x * m + 1, y * n + 1))
        elif x == M - 1:
            if y == 0:
                context.top.instantiate_element(regions["I"], (x * m + 1, y * n + 1))
            elif y == N - 1:
                context.top.instantiate_element(regions["G"], (x * m + 1, y * n + 1))
            else:
                context.top.instantiate_element(regions["H"], (x * m + 1, y * n + 1))
        else:
            if y == 0:
                context.top.instantiate_element(regions["F"], (x * m + 1, y * n + 1))
            elif y == N - 1:
                context.top.instantiate_element(regions["D"], (x * m + 1, y * n + 1))
            else:
                context.top.instantiate_element(regions["E"], (x * m + 1, y * n + 1))
    # context.top.instantiate_element(regions["A"], (1, (2 * N - 1) * region_height + 1))
    # for y in range(1, 2 * N - 1):
    #     context.top.instantiate_element(regions["B"], (1, y * region_height + 1))
    # context.top.instantiate_element(regions["C"], (1, 1))
    # for x in range(1, 2 * M - 1):
    #     if x % 2 == 1:
    #         context.top.instantiate_element(regions["D"], (x * region_width + 1, 1))
    #     else:
    #         context.top.instantiate_element(regions["E"], (x * region_width + 1, 1))
    #     for y in range(1, 2 * N - 1):
    #         if y % 2 == 1:
    #             if x % 2 == 1:
    #                 context.top.instantiate_element(regions["I"], (x * region_width + 1, y * region_height + 1))
    #             else:
    #                 context.top.instantiate_element(regions["H"], (x * region_width + 1, y * region_height + 1))
    #         else:
    #             if x % 2 == 1:
    #                 context.top.instantiate_element(regions["J"], (x * region_width + 1, y * region_height + 1))
    #             else:
    #                 context.top.instantiate_element(regions["K"], (x * region_width + 1, y * region_height + 1))
    #     if x % 2 == 1:
    #         context.top.instantiate_element(regions["O"], (x * region_width + 1, (2 * N - 1) * region_height + 1))
    #     else:
    #         context.top.instantiate_element(regions["N"], (x * region_width + 1, (2 * N - 1) * region_height + 1))
    # context.top.instantiate_element(regions["F"], ((2 * M - 1) * region_width + 1, 1))
    # for y in range(1, 2 * N - 1):
    #     if y % 2 == 1:
    #         context.top.instantiate_element(regions["G"], ((2 * M - 1) * region_width + 1, y * region_height + 1))
    #     else:
    #         context.top.instantiate_element(regions["L"], ((2 * M - 1) * region_width + 1, y * region_height + 1))
    # context.top.instantiate_element(regions["M"], ((2 * M - 1) * region_width + 1, (2 * N - 1) * region_height + 1))

    # 12. flow
    flow = Flow((
        CompleteRoutingBox(BlockFCValue(BlockPortFCValue(0.25), BlockPortFCValue(0.1))),
        CompleteSwitch(),
        CompleteConnection(),
        GenerateVerilog('rtl'),
        # InjectBitchainConfigCircuitry(),
        InjectWidechainConfigCircuitry(MyGuide(M, N, m, n)),
        # GenerateVPRXML('vpr'),
        CompletePhysical(),
        # ZeroingBRAMWriteEnable(),
        ZeroingBlockPins(),
        # GenerateYosysResources('syn'),
            ))

    # 13. run flow
    flow.run(context)

    # 14. create a pickled version
    context.pickle('ctx.pickled')

if __name__ == '__main__':
    run()
