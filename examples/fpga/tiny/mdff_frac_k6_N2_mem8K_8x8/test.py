from prga import *
from prga.core.context import *
from prga.passes.test import Tester
ctx = Context.unpickle("ctx.pkl")

flow = Flow(
        TranslationPass(),
        VerilogCollection('rtl'),
        Tester('rtl','unit_tests')
        )
flow.run(ctx, Scanchain.new_renderer())