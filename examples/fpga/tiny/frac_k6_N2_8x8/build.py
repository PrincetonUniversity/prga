# -*- encoding: ascii -*-

from prga.api.context import *
from prga.api.flow import *
from prga.api.config import *

def run():
    context = ArchitectureContext('top', 8, 8, BitchainConfigCircuitryDelegate)

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

    # 5. create CLB
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
            clb.connect(clb.create_input('ib' + str(i), 1, Orientation.west), inst.pins['ib'])
            clb.connect(cin, inst.pins['cin'], pack_pattern = 'carrychain')
            cin = inst.pins['cout']
            clb.connect(inst.pins['oa'], clb.create_output('oa' + str(i), 1, Orientation.east))
            clb.connect(inst.pins['ob'], clb.create_output('ob' + str(i), 1, Orientation.east))
            clb.connect(inst.pins['q'], clb.create_output('q' + str(i), 1, Orientation.east))
        clb.connect(cin, clb.create_output('cout', 1, Orientation.south), pack_pattern = 'carrychain')
        break

    # 6. create direct inter-block tunnels
    context.create_direct_tunnel('carrychain', clb.ports['cout'], clb.ports['cin'], (0, 1))

    # 7. create tile
    clbtile = context.create_tile('clb_tile', clb)

    # 8. fill top-level array
    for x in range(8):
        for y in range(8):
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

    # 9. flow
    flow = Flow((
        CompleteRoutingBox(BlockFCValue(BlockPortFCValue(0.25), BlockPortFCValue(0.5)),
            {'clb': BlockFCValue(BlockPortFCValue(0.25), BlockPortFCValue(0.25),
                {'cin': BlockPortFCValue(0), 'cout': BlockPortFCValue(0)})}),
        CompleteSwitch(),
        CompleteConnection(),
        GenerateVerilog('rtl'),
        InjectBitchainConfigCircuitry(),
        GenerateVPRXML('vpr'),
        CompletePhysical(),
        ZeroingBRAMWriteEnable(),
        ZeroingBlockPins(),
        GenerateYosysResources('syn'),
            ))

    # 10. run flow
    flow.run(context)

    # 11. create a pickled version
    context.pickle('ctx.pickled')

if __name__ == '__main__':
    run()
