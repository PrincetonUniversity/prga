# -*- encoding: ascii -*-

from prga.compatible import *

from prga.api.context import *
from prga.api.flow import *
from prga.api.config import *

from prga.config.packetizedchain.algorithm.injection import ConfigPacketizedChainInjectionAlgorithms as ia

from itertools import product

def run():
    region_width, region_height = 4, 4
    width, height = region_width * 2, region_height * 2
    context = ArchitectureContext('top', width, height, PacketizedChainConfigCircuitryDelegate, config_width = 8)

    # 1. routing stuff
    clk = context.create_global('clk', is_clock = True, bind_to_position = (0, 1))
    context.create_segment('L1', 12, 1)
    context.create_segment('L2', 4, 2)

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
    iotiles = {}
    for orientation in iter(Orientation):
        if orientation.is_auto:
            continue
        iotiles[orientation] = context.create_tile(
                'io_tile_{}'.format(orientation.name), iob, orientation)

    # 4. create CLB
    clb = context.create_logic_block('clb')
    while True:
        clkport = clb.create_global(clk, Orientation.south)
        ceport = clb.create_input('ce', 1, Orientation.south)
        srport = clb.create_input('sr', 1, Orientation.south)
        cin = clb.create_input('cin', 1, Orientation.north)
        for i in range(2):
            inst = clb.instantiate(context.primitives['fraclut6sffc'], 'cluster{}'.format(i))
            clb.connect(clkport, inst.pins['clk'])
            clb.connect(ceport, inst.pins['ce'])
            clb.connect(srport, inst.pins['sr'])
            clb.connect(clb.create_input('ia' + str(i), 6, Orientation.west), inst.pins['ia'])
            clb.connect(clb.create_input('ib' + str(i), 2, Orientation.west), inst.pins['ib'])
            clb.connect(cin, inst.pins['cin'], pack_pattern = 'carrychain')
            cin = inst.pins['cout']
            clb.connect(inst.pins['oa'], clb.create_output('oa' + str(i), 1, Orientation.east))
            clb.connect(inst.pins['ob'], clb.create_output('ob' + str(i), 1, Orientation.east))
            clb.connect(inst.pins['q'], clb.create_output('q' + str(i), 1, Orientation.east))
        clb.connect(cin, clb.create_output('cout', 1, Orientation.south), pack_pattern = 'carrychain')
        break

    # 5. create direct inter-block tunnels
    context.create_direct_tunnel('carrychain', clb.ports['cout'], clb.ports['cin'], (0, 1))

    # 6. create tile
    clbtile = context.create_tile('clb_tile', clb)

    # 7. region-ize the array
    region_nw = context.create_array('region_nw', region_width, region_height,
            ChannelCoverage(south = True, east = True), ChannelCoverage(south = True, east = True))
    for x, y in product(range(region_width), range(region_height)):
        if x == 0:
            if y < region_height - 1:
                region_nw.instantiate_element(iotiles[Orientation.west], (x, y))
        elif y == region_height - 1:
            region_nw.instantiate_element(iotiles[Orientation.north], (x, y))
        else:
            region_nw.instantiate_element(clbtile, (x, y))

    region_ne = context.create_array('region_ne', region_width, region_height,
        ChannelCoverage(south = True), ChannelCoverage(south = True, west = True))
    for x, y in product(range(region_width), range(region_height)):
        if x == region_width - 1:
            if y < region_height - 1:
                region_ne.instantiate_element(iotiles[Orientation.east], (x, y))
        elif y == region_height - 1:
            region_ne.instantiate_element(iotiles[Orientation.north], (x, y))
        else:
            region_ne.instantiate_element(clbtile, (x, y))

    region_sw = context.create_array('region_sw', region_width, region_height,
        ChannelCoverage(east = True), ChannelCoverage(north = True, east = True))
    for x, y in product(range(region_width), range(region_height)):
        if x == 0:
            if y > 0:
                region_sw.instantiate_element(iotiles[Orientation.west], (x, y))
        elif y == 0:
            region_sw.instantiate_element(iotiles[Orientation.south], (x, y))
        else:
            region_sw.instantiate_element(clbtile, (x, y))

    region_se = context.create_array('region_se', region_width, region_height,
        ChannelCoverage(), ChannelCoverage(north = True, west = True))
    for x, y in product(range(region_width), range(region_height)):
        if x == region_width - 1:
            if y > 0:
                region_se.instantiate_element(iotiles[Orientation.east], (x, y))
        elif y == 0:
            region_se.instantiate_element(iotiles[Orientation.south], (x, y))
        else:
            region_se.instantiate_element(clbtile, (x, y))

    # 7. fill top-level array
    context.top.instantiate_element(region_sw, (0,            0))
    context.top.instantiate_element(region_se, (region_width, 0))
    context.top.instantiate_element(region_nw, (0,            region_height))
    context.top.instantiate_element(region_ne, (region_width, region_height))
    # for x, y in product(range(8), range(8)):
    #     if x == 0:
    #         if y > 0 and y < 7:
    #             context.top.instantiate_element(iotiles[Orientation.west], (x, y))
    #     elif x == 7:
    #         if y > 0 and y < 7:
    #             context.top.instantiate_element(iotiles[Orientation.east], (x, y))
    #     elif y == 0:
    #         context.top.instantiate_element(iotiles[Orientation.south], (x, y))
    #     elif y == 7:
    #         context.top.instantiate_element(iotiles[Orientation.north], (x, y))
    #     else:
    #         context.top.instantiate_element(clbtile, (x, y))

    class MyGuide(PacketizedChainInjectionGuide):
    
        def inject_ctrl(self, module):
            return module.module_class.is_array and module.name.startswith("region")
    
        def iter_instances(self, module):
            if module.name == "top":
                yield module.element_instances[(0,            region_height)]
                yield module.element_instances[(0,            0)]
                yield module.element_instances[(region_width, 0)]
                yield module.element_instances[(region_width, region_height)]
            elif module.module_class.is_array and module.name.startswith("region"):
                for pos in ia.iter_positions_same_corner(module, Corner.northwest):
                    x, y = pos
                    elem = module.element_instances.get( pos )
                    if elem is not None:
                        yield elem
                    sbox = module.sbox_instances.get( (x, y - 1) )
                    if sbox is not None:
                        yield sbox
                    if x == 0:
                        sbox = module.sbox_instances.get( (-1, y - 1) )
                        if sbox is not None:
                            yield sbox
                # reversed_ = module.name == "region_nw"
                # for y in (reversed(range(module.height)) if module.name in ("region_nw", "region_sw") else
                #         range(module.height)):
                #     for x in reversed(range(module.width)) if reversed_ else range(module.width):
                #         sbox = module.sbox_instances.get( (x if reversed_ else x - 1, y - 1) )
                #         if sbox is not None:
                #             yield sbox
                #         elem = module.element_instances.get( (x, y) )
                #         if elem is not None:
                #             yield elem
                #         if not reversed_ and x == module.width - 1:
                #             sbox = module.sbox_instances.get( (x, y - 1) )
                #             if sbox is not None:
                #                 yield sbox
                #         elif reversed_ and x == 0:
                #             sbox = module.sbox_instances.get( (x - 1, y - 1) )
                #             if sbox is not None:
                #                 yield sbox
                #     reversed_ = not reversed_
            else:
                for instance in itervalues(module.logical_instances):
                    yield instance

    # 11. flow
    flow = Flow((
        CompleteRoutingBox(BlockFCValue(BlockPortFCValue(0.25), BlockPortFCValue(0.5)),
            {'clb': BlockFCValue(BlockPortFCValue(0.25), BlockPortFCValue(0.25),
                {'cin': BlockPortFCValue(0), 'cout': BlockPortFCValue(0)})}),
        CompleteSwitch(),
        CompleteConnection(),
        GenerateVerilog('rtl'),
        InjectPacketizedChainConfigCircuitry(MyGuide()),
        GenerateVPRXML('vpr'),
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
