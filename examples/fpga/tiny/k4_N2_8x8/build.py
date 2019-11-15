# -*- encoding: ascii -*-

from prga.api.context import *
from prga.api.flow import *
from prga.api.config import *

from itertools import product

def run():
    context = ArchitectureContext('top', 8, 8, BitchainConfigCircuitryDelegate)

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

    # 7. fill top-level array
    for x, y in product(range(8), range(8)):
        if x == 0:
            if y > 0 and y < 7:
                context.top.instantiate_element(iotiles[Orientation.west], (x, y))
        elif x == 7:
            if y > 0 and y < 7:
                context.top.instantiate_element(iotiles[Orientation.east], (x, y))
        elif y == 0:
            context.top.instantiate_element(iotiles[Orientation.south], (x, y))
        elif y == 7:
            context.top.instantiate_element(iotiles[Orientation.north], (x, y))
        else:
            context.top.instantiate_element(clbtile, (x, y))

    # 11. flow
    flow = Flow((
        CompleteRoutingBox(BlockFCValue(BlockPortFCValue(0.25), BlockPortFCValue(0.5))),
        CompleteSwitch(),
        CompleteConnection(),
        GenerateVerilog('rtl'),
        InjectBitchainConfigCircuitry(),
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
