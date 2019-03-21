from prga._archdef.common import ModuleType
from prga._archdef.moduleinstance.module import MutableLeafModule
from prga._archdef.portpin.bus import PortOrPinBus
from prga._archdef.portpin.port import AbstractInputPort, AbstractOutputPort, PhysicalInputPort, PhysicalOutputPort

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

class MockModule(MutableLeafModule):
    @property
    def is_logical(self):
        return True

    @property
    def is_physical(self):
        return True

    @property
    def type(self):
        return ModuleType.block

class TestModule(object):
    def test_add_port(self):
        module = MockModule('mock')
        module.add_port(MockInput(module, 'in', 2))
        module.add_port(MockOutput(module, 'out', 2))
        module.add_port(PhysicalInputPort(module, 'cfg_d', 2))
        assert len(module._ports) == 3
        assert len(module.ports) == 2
        assert len(module.physical_ports) == 3
