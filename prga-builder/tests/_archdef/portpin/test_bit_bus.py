# Python 2 and 3 compatible
from prga.compatible import *

from prga._archdef.common import PortDirection, NetType
from prga._archdef.portpin.bit import PortOrPinBit, DynamicPortOrPinBit
from prga._archdef.portpin.bus import AbstractPortOrPinBus, PortOrPinBus, DynamicPortOrPinBus

import pytest

class MockParent(object):
    def __init__(self):
        self.dyn = {}
        self.buses = {}

    def get_net(self, name, *args, **kwargs):
        return self.buses.get(name, self.dyn.setdefault(name,
            MockDynamicBus(self, name, *args, **kwargs)))

    def get_static_net(self, dynamic_net, create = False):
        if create:
            ref = self.dyn[dynamic_net.name]
            return self.buses.setdefault(dynamic_net.name,
                    MockStaticBus(self, dynamic_net.name, ref.width, ref.direction,
                ref.is_logical, ref.is_physical, ref.is_source, ref.is_sink))
        else:
            return self.buses.get(dynamic_net.name, None)

    def __str__(self):
        return 'mock_parent'

class MockBus(AbstractPortOrPinBus):
    def __init__(self, parent, name, width, direction,
        logical = False, physical = False, source = False, sink = False):
        self.__parent = parent
        self.__name = name
        self.__width = width
        self.__direction = direction
        self.__logical = logical
        self.__physical = physical
        self.__source = source
        self.__sink = sink

    @property
    def width(self):
        return self.__width

    @property
    def name(self):
        return self.__name

    @property
    def direction(self):
        return self.__direction

    @property
    def is_clock(self):
        return self.__is_clock

    @property
    def type(self):
        return NetType.port

    @property
    def parent(self):
        return self.__parent

    @property
    def is_clock(self):
        return False

    @property
    def is_logical(self):
        return self.__logical

    @property
    def is_physical(self):
        return self.__physical

    @property
    def is_source(self):
        return self.__source

    @property
    def is_sink(self):
        return self.__sink

class MockStaticBus(MockBus, PortOrPinBus):
    pass

class MockDynamicBus(MockBus, DynamicPortOrPinBus):
    def get_static_cp(self, create = False):
        return self.parent.get_static_net(self, create)

class TestBusAndBit(object):
    def test_counterpart(self):
        parent = MockParent()
        # 1. preparation
        ds = [parent.get_net('src' + str(i), 3, PortDirection.input, True, True, True)
                for i in range(8)]
        # 2.1 check that everything is dynamic and static counterparts are not created
        for p in ds:
            assert p.is_dynamic
            assert p.get_static_cp() is None
            # 2.2 check the physical counterpart of the bus
            assert p.physical_cp is None
            # 2.3 check all bits are dynamic now, too
            for b in p:
                assert b.is_dynamic
                assert b._bus is p
                # 2.4 check the physical counterpart of each bit
                assert b.physical_cp is None
        # 3.1 set a dynamic bus as the physical counterpart of another dynamic bus
        ds[0].physical_cp = ds[1]
        # 3.2 and it should only make the buses static, not the bits
        ss = list(map(lambda x: x.get_static_cp(), (ds[0], ds[1])))
        for p in ss:
            assert p is not None
            assert not p.is_dynamic
            for b in p:
                assert b.is_dynamic
                assert b._bus is p
        # 3.3 all the dynamic bits in the dynamic bus should point to the static bus now
        assert all(b._bus is ss[0] for b in ds[0])
        assert all(b._bus is ss[1] for b in ds[1])
        # 3.4 check the physical counterpart of the bus
        assert ss[0].physical_cp is ss[1]
        assert ds[0].physical_cp is ss[1]
        # 4.1 set a dynamic bus (with static counterpart) as the physical counterpart of a dynamic bus
        ds[2].physical_cp = ds[1]
        ss.append(ds[2].get_static_cp())
        # 4.2 and the static counterpart should not be created again
        assert ds[1].get_static_cp() is ss[1]
        assert ds[2].physical_cp is ss[1]
        # 5 now, set a dynamic bus as the physical counterpart of a dynamic bus (with static counterpart)
        ds[2].physical_cp = ds[3]
        ss.append(ds[3].get_static_cp())
        assert ds[2].get_static_cp() is ss[2]
        assert ds[2].physical_cp is ss[3]
        # 6 set a dynamic bus w/ static cp as the physical cp of a dynamic bus w/ static cp
        ds[2].physical_cp = ds[1]
        assert ds[2].get_static_cp() is ss[2]
        assert ds[1].get_static_cp() is ss[1]
        assert ds[2].physical_cp is ss[1]
        assert ss[2].physical_cp is ss[1]
        # 7 set a static bus as the physical counterpart of another static bus
        ss[2].physical_cp = ss[3]
        assert ds[2].physical_cp is ss[3]
        assert ss[2].physical_cp is ss[3]
        # 8.1 set a dynamic bus as the physical counterpart of a static bus
        ss[3].physical_cp = ds[4]
        ss.append(ds[4].get_static_cp())
        # 8.2 check physical cp
        assert ds[3].physical_cp is ss[4]
        assert ss[3].physical_cp is ss[4]
        # 8.3 up to now, no static bits should be created
        for p in ss:
            for b in p:
                assert b.is_dynamic
                assert b._bus is p
        # 9 preparation: keep a few dynamic bits for later use
        db = [x[0] for x in ds]
        # 10.1 dynamic bit in dynamic bus w/o static cp -> dynamic bit
        ds[5][0].physical_cp = ds[6][0]
        assert not ds[5][0].physical_cp.is_dynamic
        # 10.2 static counterparts should be created
        assert ds[5].get_static_cp() is not None
        assert ds[6].get_static_cp() is not None
        ss.extend((ds[5].get_static_cp(), ds[6].get_static_cp()))
        # 10.3 static bits should also be created
        for p in (ss[5], ss[6]):
            for b in p:
                assert not b.is_dynamic
                assert b._bus is p
        # 10.4 indexing into dynamic buses should also return static bits
        for d, s in zip((ds[5], ds[6]), (ss[5], ss[6])):
            for u, v in zip(d, s):
                assert not u.is_dynamic
                assert u is v
        # 10.5 check the values
        assert ds[5].physical_cp == (ds[6][0], None, None)
        # 11.1 static bit -> dynamic bit
        db[6].physical_cp = ds[0][0]
        # 11.2 the static bit/bus should not be broken
        assert ss[0].physical_cp is ss[1]
        for b in ss[0]:
            assert not b.is_dynamic
        # 11.3 the static counterpart of the dynamic bit should also see this modification
        assert ds[6][0].physical_cp is ss[0][0]
        # 12 what if I set the physical counterpart of the bus again
        ds[5].physical_cp = ds[3]
        assert ds[5].physical_cp is ss[3]
        assert db[5].physical_cp._bus is ss[3]
        assert db[5].physical_cp.is_dynamic
