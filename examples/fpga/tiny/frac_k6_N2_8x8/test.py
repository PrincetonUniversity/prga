from prga import *
from prga.core.context import *
from prga.passes.test import Tester
ctx = Context.unpickle("ctx.pkl")

flow = Flow(
        Tester('rtl','unit_tests')
        )
flow.run(ctx, Scanchain.new_renderer())