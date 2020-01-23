# -*- encoding: ascii -*-

from prga.compatible import *

from prga.api.context import *
from prga.api.flow import *
from prga.api.config import *

from prga.config.packetizedchain.algorithm.injection import ConfigPacketizedChainInjectionAlgorithms as ia

from itertools import product

def run():
    # Note: region_width must be odd, region_height must be even
    region_width, region_height = 5, 6
    if not (region_width % 2 == 1 and region_height % 2 == 0):
        raise RuntimeError("'region_width' must be odd and 'region_width' must be even")

    # Note: regioncount_x must be even, regioncount_y must be larger than 2
    regioncount_x, regioncount_y = 6, 8
    if not (regioncount_x % 2 == 0 and regioncount_y > 2):
        raise RuntimeError("'regioncount_x' must be even and 'regioncount_y' must be larger than 2")

    context = ArchitectureContext('top',
            regioncount_x * region_width + 2,
            regioncount_y * region_height,
            PacketizedChainConfigCircuitryDelegate, config_width = 8)

    # 1. routing stuff
    clk = context.create_global('clk', is_clock = True, bind_to_position = (1, regioncount_y * region_height - 1))
    context.create_segment('L1', 32, 1)
    context.create_segment('L2', 16, 2)
    context.create_segment('L4', 16, 4)

    # 2. create IOB
    iob = context.create_io_block('iob', 16)
    while True:
        outpad = iob.create_input('outpad', 1)
        inpad = iob.create_output('inpad', 1)
        ioinst = iob.instances['io']
        iob.connect(ioinst.pins['inpad'], inpad)
        iob.connect(outpad, ioinst.pins['outpad'])
        break

    # 3. create tile
    iotile = context.create_tile('io_tile', iob, Orientation.north)

    # 4. create CLB
    clb = context.create_logic_block('clb')
    while True:
        clkport = clb.create_global(clk, Orientation.south)
        ceport = clb.create_input('ce', 1, Orientation.south)
        srport = clb.create_input('sr', 1, Orientation.south)
        cin = clb.create_input('cin', 1, Orientation.north)
        for i, ori in enumerate(Orientation):
            if ori.is_auto:
                continue
            inst = clb.instantiate(context.primitives['fraclut6sffc'], 'cluster{}'.format(i))
            clb.connect(clkport, inst.pins['clk'])
            clb.connect(ceport, inst.pins['ce'])
            clb.connect(srport, inst.pins['sr'])
            clb.connect(clb.create_input('ia' + str(i), 6, ori), inst.pins['ia'])
            clb.connect(clb.create_input('ib' + str(i), 2, ori), inst.pins['ib'])
            clb.connect(cin, inst.pins['cin'], pack_pattern = 'carrychain')
            cin = inst.pins['cout']
            clb.connect(inst.pins['oa'], clb.create_output('oa' + str(i), 1, ori.opposite))
            clb.connect(inst.pins['ob'], clb.create_output('ob' + str(i), 1, ori.opposite))
            clb.connect(inst.pins['q'], clb.create_output('q' + str(i), 1, ori.opposite))
        clb.connect(cin, clb.create_output('cout', 1, Orientation.south), pack_pattern = 'carrychain')
        break

    # 5. create direct inter-block tunnels
    context.create_direct_tunnel('carrychain', clb.ports['cout'], clb.ports['cin'], (0, 1))

    # 6. create CLB tile
    clbtile = context.create_tile('clb_tile', clb)

    # 7. create BRAM block
    bram = context.create_logic_block('bram', 1, 2)
    while True:
        clkport = bram.create_global(clk, Orientation.south, position = (0, 0))
        addrport1 = bram.create_input('addr1', 10, Orientation.west, position = (0, 0))
        dinport1 = bram.create_input('data1', 8, Orientation.west, position = (0, 0))
        weport1 = bram.create_input('we1', 1, Orientation.west, position = (0, 0))
        doutport1 = bram.create_output('out1', 8, Orientation.east, position = (0, 0))
        addrport2 = bram.create_input('addr2', 10, Orientation.west, position = (0, 1))
        dinport2 = bram.create_input('data2', 8, Orientation.west, position = (0, 1))
        weport2 = bram.create_input('we2', 1, Orientation.west, position = (0, 1))
        doutport2 = bram.create_output('out2', 8, Orientation.east, position = (0, 1))
        inst = bram.instantiate(context.primitive_library.get_or_create_memory(10, 8, 
            dualport = True), 'ram')
        bram.auto_connect(inst)
        break

    # 9. create BRAM tile
    bramtile = context.create_tile('bram_tile', bram)

    # 10. region-ize the array
    #   +-----+     +-----+ +-----+        +-----+
    #   |i    |     |    o| |i    |        |    o|
    #   |  A  |   / |  F  | |  G  | \      |  L  |
    #   |    o|  |  |    i| |    o|  |     |    i|
    #   +-----+  |  +-----+ +-----+  |     +-----+
    #   +-----+  |  +-----+ +-----+  |     +-----+
    #   |    i|  |  |    o| |    i|  |     |    o|
    #   |  B  |  |  |  E  | |  H  |  |     |  K  |
    #   |    o|  |  |    i| |    o|  |     |    i|
    #   +-----+  |  +-----+ +-----+  |     +-----+
    #      *     |     *       *     |        *
    #      *    <      *       *      > xN    *
    #      *     |     *       *     |        *
    #   +-----+  |  +-----+ +-----+  |     +-----+
    #   |    i|  |  |    o| |    i|  |     |    o|
    #   |  B  |  |  |  E  | |  H  |  |     |  K  |
    #   |    o|  |  |    i| |    o|  |     |    i|
    #   +-----+  |  +-----+ +-----+  |     +-----+
    #   +-----+  |  +-----+ +-----+  |     +-----+
    #   |    i|  |  |    o| |    i|  |     |    o|
    #   |  C  |   \ |  D  | |  I  | /      |  J  |
    #   |    o|     |i    | |    o|        |i    |
    #   +-----+     +-----+ +-----+        +-----+
    regions = {}
    # region A, F, G, L:
    for r in ('A', 'F', 'G', 'L'):
        region = regions[r] = context.create_array('region_' + r, region_width, region_height,
                ChannelCoverage(south = True, east = True, west = r == 'A'),
                ChannelCoverage(south = True, east = True, west = True))
        for x, y in product(range(region_width), range(region_height)):
            if y == region_height - 1:  # top row: IO tiles
                region.instantiate_element(iotile, (x, y))
            else:
                region.instantiate_element(clbtile, (x, y))

    # region B, E, H, K:
    for r in ('B', 'E', 'H', 'K'):
        region = regions[r] = context.create_array('region_' + r, region_width, region_height,
                ChannelCoverage(south = True, east = True, west = r == 'B'))
        for x, y in product(range(region_width), range(region_height)):
            if x == region_width // 2:
                if y % 2 == 0:
                    region.instantiate_element(bramtile, (x, y))
            else:
                region.instantiate_element(clbtile, (x, y))

    # region C, D, I, J:
    for r in ('C', 'D', 'I', 'J'):
        region = regions[r] = context.create_array('region_' + r, region_width, region_height,
                ChannelCoverage(east = True, west = r == 'C'),
                ChannelCoverage(north = True, east = True, west = True))
        for x, y in product(range(region_width), range(region_height)):
            if y == 0: # bottom row: leave empty
                continue
            else:
                region.instantiate_element(clbtile, (x, y))

    # 11. fill top-level array
    for x, y in product(range(regioncount_x), range(regioncount_y)):
        if x == 0:
            if y == 0:                      # C
                context.top.instantiate_element(regions['C'], (x * region_width + 1, y * region_height))
            elif y == regioncount_y - 1:    # A
                context.top.instantiate_element(regions['A'], (x * region_width + 1, y * region_height))
            else:                           # B
                context.top.instantiate_element(regions['B'], (x * region_width + 1, y * region_height))
        elif x == regioncount_x - 1:
            if y == 0:                      # J
                context.top.instantiate_element(regions['J'], (x * region_width + 1, y * region_height))
            elif y == regioncount_y - 1:    # L
                context.top.instantiate_element(regions['L'], (x * region_width + 1, y * region_height))
            else:                           # K
                context.top.instantiate_element(regions['K'], (x * region_width + 1, y * region_height))
        elif x % 2 == 1:
            if y == 0:                      # D
                context.top.instantiate_element(regions['D'], (x * region_width + 1, y * region_height))
            elif y == regioncount_y - 1:    # F
                context.top.instantiate_element(regions['F'], (x * region_width + 1, y * region_height))
            else:                           # E
                context.top.instantiate_element(regions['E'], (x * region_width + 1, y * region_height))
        else:
            if y == 0:                      # I
                context.top.instantiate_element(regions['I'], (x * region_width + 1, y * region_height))
            elif y == regioncount_y - 1:    # G
                context.top.instantiate_element(regions['G'], (x * region_width + 1, y * region_height))
            else:                           # H
                context.top.instantiate_element(regions['H'], (x * region_width + 1, y * region_height))

    class MyGuide(PacketizedChainInjectionGuide):
    
        def inject_ctrl(self, module):
            return module.module_class.is_array and module.name.startswith("region")
    
        def iter_instances(self, module):
            if module.module_class.is_array:
                if module.name == "top":
                    for x in range(regioncount_x):
                        for y in reversed(range(regioncount_y)) if x % 2 == 0 else range(regioncount_y):
                            yield module.element_instances[(x * region_width + 1, y * region_height)]
                elif module.name in ('region_A', 'region_G'):
                    for x in range(region_width):
                        if x % 2 == 0:
                            for y in reversed(range(region_height)):
                                elem = module.element_instances.get( (x, y) )
                                if elem is not None:
                                    yield elem
                                if x == 0:
                                    sbox = module.sbox_instances.get( (-1, y - 1) )
                                    if sbox is not None:
                                        yield sbox
                                sbox = module.sbox_instances.get( (x, y - 1) )
                                if sbox is not None:
                                    yield sbox
                        else:
                            for y in range(region_height):
                                sbox = module.sbox_instances.get( (x, y - 1) )
                                if sbox is not None:
                                    yield sbox
                                elem = module.element_instances.get( (x, y) )
                                if elem is not None:
                                    yield elem
                elif module.name in ('region_D', 'region_J'):
                    for x in range(region_width):
                        if x % 2 == 0:
                            for y in range(region_height):
                                if x == 0:
                                    sbox = module.sbox_instances.get( (-1, y - 1) )
                                    if sbox is not None:
                                        yield sbox
                                sbox = module.sbox_instances.get( (x, y - 1) )
                                if sbox is not None:
                                    yield sbox
                                elem = module.element_instances.get( (x, y) )
                                if elem is not None:
                                    yield elem
                        else:
                            for y in reversed(range(region_height)):
                                elem = module.element_instances.get( (x, y) )
                                if elem is not None:
                                    yield elem
                                sbox = module.sbox_instances.get( (x, y - 1) )
                                if sbox is not None:
                                    yield sbox
                elif module.name in ('region_B', 'region_C', 'region_H', 'region_I'):
                    for y in reversed(range(region_height)):
                        if y % 2 == 0:
                            for x in range(region_width):
                                if x == 0:
                                    sbox = module.sbox_instances.get( (-1, y - 1) )
                                    if sbox is not None:
                                        yield sbox
                                elem = module.element_instances.get( (x, y) )
                                if elem is not None:
                                    yield elem
                                sbox = module.sbox_instances.get( (x, y - 1) )
                                if sbox is not None:
                                    yield sbox
                        else:
                            for x in reversed(range(region_width)):
                                sbox = module.sbox_instances.get( (x, y - 1) )
                                if sbox is not None:
                                    yield sbox
                                elem = module.element_instances.get( (x, y) )
                                if elem is not None:
                                    yield elem
                                if x == 0:
                                    sbox = module.sbox_instances.get( (-1, y - 1) )
                                    if sbox is not None:
                                        yield sbox
                else:
                    for y in range(region_height):
                        if y % 2 == 0:
                            for x in reversed(range(region_width)):
                                sbox = module.sbox_instances.get( (x, y - 1) )
                                if sbox is not None:
                                    yield sbox
                                elem = module.element_instances.get( (x, y) )
                                if elem is not None:
                                    yield elem
                                if x == 0:
                                    sbox = module.sbox_instances.get( (-1, y - 1) )
                                    if sbox is not None:
                                        yield sbox
                        else:
                            for x in range(region_width):
                                if x == 0:
                                    sbox = module.sbox_instances.get( (-1, y - 1) )
                                    if sbox is not None:
                                        yield sbox
                                elem = module.element_instances.get( (x, y) )
                                if elem is not None:
                                    yield elem
                                sbox = module.sbox_instances.get( (x, y - 1) )
                                if sbox is not None:
                                    yield sbox
            else:
                for instance in itervalues(module.logical_instances):
                    yield instance

    # 11. flow
    flow = Flow((
        CompleteRoutingBox(BlockFCValue(BlockPortFCValue(0.25), BlockPortFCValue(0.5)),
            {'clb': BlockFCValue(BlockPortFCValue(0.25), BlockPortFCValue(0.5),
                {'cin': BlockPortFCValue(0), 'cout': BlockPortFCValue(0)})}),
        CompleteSwitch(),
        CompleteConnection(),
        GenerateVerilog('rtl'),
        InjectPacketizedChainConfigCircuitry(MyGuide()),
        GenerateVPRXML('vpr'),
        ZeroingBRAMWriteEnable(),
        CompletePhysical(),
        ZeroingBlockPins(),
        GenerateYosysResources('syn'),
            ))

    # 11. run flow
    flow.run(context)

    # 12. create a pickled version
    context.pickle('ctx.pickled')

if __name__ == '__main__':
    run()
