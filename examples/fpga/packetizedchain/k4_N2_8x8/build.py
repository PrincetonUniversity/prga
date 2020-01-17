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
        inport = clb.create_input('in', 8, Orientation.west)
        outport = clb.create_output('out', 2, Orientation.east)
        for i in range(2):
            clusterinst = clb.instantiate(cluster, 'cluster{}'.format(i))
            clb.connect(inport[i*4:(i+1)*4], clusterinst.pins['in'])
            clb.connect(clkport, clusterinst.pins['clk'])
            clb.connect(clusterinst.pins['out'], outport[i])
        break

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
        CompleteRoutingBox(BlockFCValue(BlockPortFCValue(0.25), BlockPortFCValue(0.5))),
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
