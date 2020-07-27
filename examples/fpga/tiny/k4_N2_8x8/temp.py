from prga import *
from prga.core.context import *
from prga.netlist.net.util import NetUtils
from prga.compatible import *
from itertools import chain
from bitarray import bitarray
from prga.passes.test import Tester
import networkx as nx
ctx = Context.unpickle("ctx.pkl")
top = ctx._database[0,"top"]
clb= ctx._database[0,"clb"]
cluster= ctx._database[0,"cluster"]
subarray= ctx._database[0,"subarray"]
tile_clb= ctx._database[0,"tile_clb"]
cluster_i0 = clb._instances[('cluster',0)]
ff = cluster_i0.model._instances['ff']
D = ff.pins['D']

options = {
    "node_color": "black",
    "node_size": 50,
    "linewidths": 1,
    "width": 0.1,
    "arrowsize": 10,
}

# for sink_bus in chain(iter(oport for oport in itervalues(cluster.ports) if oport.direction.is_output),
#                      iter(ipin for instance in itervalues(cluster.instances) for ipin in itervalues(instance.pins) if ipin.model.direction.is_input)):
#     for sink_net in sink_bus:
#         for src_net in NetUtils.get_multisource(sink_net):
#             conn = NetUtils.get_connection(src_net,sink_net)
#             cfg_bits = conn.get("cfg_bits",tuple())
#             print("Conn::",src_net,"->",sink_net,"::",cfg_bits)

# for x in itervalues(clb._instances):
#     if x.model.module_class.is_primitive and x.model.primitive_class.is_lut:
#         print(x)
#         print(x.cfg_bitoffset)
#         print(x.model.cfg_bitcount)

flow = Flow(
        TranslationPass(),
        VerilogCollection('rtl'),
        Tester('rtl','unit_tests')
        )
flow.run(ctx, Scanchain.new_renderer())
