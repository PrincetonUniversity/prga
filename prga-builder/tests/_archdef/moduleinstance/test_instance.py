from prga._archdef.common import ModuleType
from prga._archdef.moduleinstance.module import MutableNonLeafModule, MutableLeafModule
from prga._archdef.moduleinstance.instance import PhysicalInstance, LogicalInstance, Instance
from prga._archdef.portpin.bus import PortOrPinBus
from prga._archdef.portpin.port import AbstractInputPort, AbstractOutputPort, PhysicalInputPort, PhysicalOutputPort

import pytest

class MockInput(AbstractInputPort, PortOrPinBus):
    @property
    def is_logical(self):
        return True

    @property
    def is_physical(self):
        return True

class MockOutput(AbstractOutputPort, PortOrPinBus):
    @property
    def is_logical(self):
        return True

    @property
    def is_physical(self):
        return True

class MockModule(MutableNonLeafModule, MutableLeafModule):
    @property
    def is_logical(self):
        return True

    @property
    def is_physical(self):
        return True

    @property
    def type(self):
        return ModuleType.block

class TestInstance(object):
    def test_instance(self):
        module = MockModule('mock')
        module.add_port(MockInput(module, 'in', 4))
        module.add_port(MockOutput(module, 'out', 2))
        module.add_port(PhysicalInputPort(module, 'cfg_d', 2))
        lut = MockModule('lut')
        lut.add_port(MockInput(lut, 'in', 4))
        lut.add_port(MockOutput(lut, 'out', 1))
        # 1. instantiate
        inst = Instance(module, lut, 'lut_inst')
        assert inst.pins['in'].is_dynamic
        assert len(inst.pins) == 2
        module.add_instance_raw(inst)
        # 2. connect
        inst.pins['in'].physical_source = module.ports['in']
        assert not inst.pins['in'].is_dynamic
        assert inst.pins['out'].is_dynamic
        assert inst.pins['in'][0].is_dynamic
        assert module.ports['in'][0].is_dynamic
        for i in range(4):
            inst.pins['in'][i].add_logical_sources(module.ports['in'][i])
        assert not inst.pins['in'][0].is_dynamic
        assert not module.ports['in'][0].is_dynamic
        module.ports['out'][0].add_logical_sources(inst.pins['out'])
        assert not inst.pins['out'].is_dynamic
        assert not module.ports['out'][0].is_dynamic
        assert inst._static_pins.get('in')
        assert inst._static_pins.get('out')
        # 3. instantiate a logical instance
        inst2 = LogicalInstance(None, module, 'inst')
        assert len(inst2.pins) == 2
        assert len(inst2._pins) == 2
        with pytest.raises(KeyError):
            assert inst2._pins['cfg_d']
