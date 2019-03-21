from prga._archdef.block.slice import Slice

class TestSlice(object):
    def test_slice(self):
        lut = Slice('lut')
        lut.add_input('i', 4)
        lut.add_output('o', 1)

        ff = Slice('ff')
        ff.add_input('d', 1)
        ff.add_output('q', 1)
        ff.add_clock('clk')

        n = Slice('mock')
        n.add_input('i', 4)
        n.add_output('o', 1)
        n.add_clock('clk')
        n.add_instance('lut', lut)
        n.add_instance('ff', ff)
        n.add_connections(n.ports['i'], n.instances['lut'].pins['i'])
        n.add_connections(n.instances['lut'].pins['o'], n.instances['ff'].pins['d'], pack_pattern = True)
        n.add_connections(n.ports['clk'], n.instances['ff'].pins['clk'])
        n.add_connections((n.instances['lut'].pins['o'], n.instances['ff'].pins['q']),
                n.ports['o'], fully_connected = True)

        assert len(n.ports) == 3
        assert len(n.instances) == 2
        assert len(n._pack_patterns) == 1
        assert n._pack_patterns[0] == (n.instances['lut'].pins['o'][0], n.instances['ff'].pins['d'][0])
        assert n.ports['o'][0].logical_sources == (n.instances['lut'].pins['o'][0], n.instances['ff'].pins['q'][0])
