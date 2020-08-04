from prga import *
from prga.core.context import *
from prga.netlist.net.util import NetUtils
from prga.compatible import *
from itertools import chain
from bitarray import bitarray
from prga.passes.test import Tester
from prga.core.builder.box.sbox import _SwitchBoxKey
ctx = Context.unpickle("ctx.pkl")

flow = Flow(
        Tester('rtl','unit_tests')
        )
flow.run(ctx, Scanchain.new_renderer())
