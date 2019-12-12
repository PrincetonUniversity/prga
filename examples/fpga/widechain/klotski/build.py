# -*- encoding: ascii -*-

from prga.api.context import *
from prga.api.flow import *
from prga.api.config import *

from itertools import chain, product

class MyHelper(WidechainInjectionHelper):

    def __init__(self, M, N, m, n):
        # array = 2M x (2N + 1) regions
        # region = m x (2n + 1) tiles
        self.M = M
        self.N = N
        self.m = m
        self.n = n

    def inject_fifo(self, module):
        return module.name.startswith("region")

    def inject_chain(self, module):
        return module.module_class.is_tile or module.module_class.is_array

    def __iterate_row(self, module, y, inc_dir):
        if inc_dir:
            for x in range(module.width):
                tile = module.element_instances.get((x, y))
                if tile is not None:
                    yield tile
                sbox = module.sbox_instances.get((x, y - 1))
                if sbox is not None:
                    yield sbox
        else:
            for x in reversed(range(module.width)):
                sbox = module.sbox_instances.get((x, y - 1))
                if sbox is not None:
                    yield sbox
                tile = module.element_instances.get((x, y))
                if tile is not None:
                    yield tile

    def iterate_instances(self, module):
        if module.name in ("region_A", "region_B"):
            # Region A/B: m x (2n + 1)
            #           channel coverage: east, west, south
            #           config chain: northeast in, southeast out
            for y in reversed(range(module.height)):
                for x in reversed(range(module.width)):
                    tile = module.element_instances.get((x, y))
                    if tile is not None:
                        yield tile
                for x in range(-1, module.width):
                    sbox = module.sbox_instances.get((x, y - 1))
                    if sbox is not None:
                        yield tile
        elif module.name in ("region_C1", "region_D1"):
            # Region C1/D1: m x (2n + 1)
            #           channel coverage: east, south
            #           config chain: southwest in, northeast out
            for y in range(module.height):
                for m in self.__iterate_row(module, y, y % 2 == 0):
                    yield m
        elif module.name in ("region_C2", "region_D2"):
            # Region C2/D2: m x (2n + 1)
            #           channel coverage: east, south
            #           config chain: northwest in, southeast out
            for y in reversed(range(module.height)):
                for m in self.__iterate_row(module, y, y % 2 == 0):
                    yield m
        elif module.name == "region_C3":
            # Region C3: m x (2n + 1)
            #           channel coverage: east, south
            #           config chain: southeast in, northwest out
            for y in range(module.height):
                for m in self.__iterate_row(module, y, y % 2 == 1):
                    yield m
        elif module.name == "region_C4":
            # Region C4: m x (2n + 1)
            #           channel coverage: east, south
            #           config chain: northeast in, southwest out
            for y in reversed(range(module.height)):
                for m in self.__iterate_row(module, y, y % 2 == 1):
                    yield m
        elif module.name == "top":
            M, N, m, n = self.M, self.N, self.m, self.n
            region_width, region_height = m, 2 * n + 1
            # 1. region A
            yield module.element_instances[1, 2 * N * region_height + 1]
            # 2. region B
            for y in reversed(range(2 * N)):
                yield module.element_instances[1, y * region_height + 1]
            # 3. region C1, C2, C3, C4
            for y in range(N):
                for x in range(1, 2 * M):
                    yield module.element_instances[x * m + 1, 2 * y * region_height + 1]
                for x in range(2 * M - 1, 0, -1):
                    yield module.element_instances[x * m + 1, (2 * y + 1) * region_height + 1]
            # 4. region D1, D2
            for x in range(1, 2 * M):
                yield module.element_instances[x * m + 1, 2 * N * region_height + 1]
        else:
            return None

def run():
    M, N, m, n = 2, 2, 6, 3
    region_width, region_height = m, 2 * n + 1
    width, height = 2 * M * region_width + 2, (2 * N + 1) * region_height + 1
    context = ArchitectureContext('top', width, height, WidechainConfigCircuitryDelegate)

    # 1. routing stuff
    clk = context.create_global('clk', is_clock = True, bind_to_position = (1, height - 1))
    context.create_segment('L1', 48, 1)
    # context.create_segment('L2', 16, 2)
    # context.create_segment('L4', 8, 4)

    # 2. create IOB
    iob = context.create_io_block('iob', 8)
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
    coverage_AB = ChannelCoverage(south = True, east = True, west = True)
    coverage_CD = ChannelCoverage(south = True, west = True)
    region_A = context.create_array("region_A", region_width, region_height, coverage_AB)
    region_B = context.create_array("region_B", region_width, region_height, coverage_AB)
    region_C1 = context.create_array("region_C1", region_width, region_height, coverage_CD)
    region_C2 = context.create_array("region_C2", region_width, region_height, coverage_CD)
    region_C3 = context.create_array("region_C3", region_width, region_height, coverage_CD)
    region_C4 = context.create_array("region_C4", region_width, region_height, coverage_CD)
    region_D1 = context.create_array("region_D1", region_width, region_height, coverage_CD)
    region_D2 = context.create_array("region_D2", region_width, region_height, coverage_CD)

    # 7.1 region A, D:
    for x in range(region_width):
        region_A.instantiate_element(iotile, (x, region_height - 1))
        region_D1.instantiate_element(iotile, (x, region_height - 1))
        region_D2.instantiate_element(iotile, (x, region_height - 1))
    for pos in product(range(region_width), range(region_height - 1)):
        region_A.instantiate_element(clbtile, pos)
        region_D1.instantiate_element(clbtile, pos)
        region_D2.instantiate_element(clbtile, pos)

    # 7.2 region B, C:
    for pos in product(range(region_width), range(region_height)):
        region_B.instantiate_element(clbtile, pos)
        region_C1.instantiate_element(clbtile, pos)
        region_C2.instantiate_element(clbtile, pos)
        region_C3.instantiate_element(clbtile, pos)
        region_C4.instantiate_element(clbtile, pos)

    # 8. fill top-level array
    context.top.instantiate_element(region_A, (1, 2 * N * region_height + 1))
    for y in range(2 * N):
        context.top.instantiate_element(region_B, (1, y * region_height + 1))
    for x, y in product(range(1, 2 * M), range(2 * N)):
        if y % 2 == 0:
            if x % 2 == 1:
                context.top.instantiate_element(region_C1, (x * region_width + 1, y * region_height + 1))
            else:
                context.top.instantiate_element(region_C2, (x * region_width + 1, y * region_height + 1))
        else:
            if x % 2 == 0:
                context.top.instantiate_element(region_C3, (x * region_width + 1, y * region_height + 1))
            else:
                context.top.instantiate_element(region_C4, (x * region_width + 1, y * region_height + 1))
    for x in range(1, 2 * M):
        if x % 2 == 1:
            context.top.instantiate_element(region_D1, (x * region_width + 1, 2 * N * region_height + 1))
        else:
            context.top.instantiate_element(region_D2, (x * region_width + 1, 2 * N * region_height + 1))

    # 12. flow
    flow = Flow((
        CompleteRoutingBox(BlockFCValue(BlockPortFCValue(0.25), BlockPortFCValue(0.1))),
        CompleteSwitch(),
        CompleteConnection(),
        GenerateVerilog('rtl'),
        # InjectBitchainConfigCircuitry(),
        InjectWidechainConfigCircuitry(MyHelper(M, N, m, n)),
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
