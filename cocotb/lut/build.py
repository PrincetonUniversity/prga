from prga.core.common import ModuleView
from prga.cfg.scanchain.lib import Scanchain
from prga.passes.rtl import VerilogCollection
ctx = Scanchain.new_context(1)
r = Scanchain.new_renderer()
p = VerilogCollection(r, "rtl")
p._process_module(ctx.database[ModuleView.logical, "lut4"])
r.render()