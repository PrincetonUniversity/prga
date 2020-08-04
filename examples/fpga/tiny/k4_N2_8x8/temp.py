from prga import *
from prga.core.context import *
from prga.netlist.net.util import NetUtils
from prga.compatible import *
from itertools import chain
from bitarray import bitarray
from prga.passes.test import Tester
from prga.core.builder.box.sbox import _SwitchBoxKey
ctx = Context.unpickle("ctx.pkl")
top = ctx._database[0,"top"]
clb= ctx._database[0,"clb"]
cluster= ctx._database[0,"cluster"]
sbox = ctx._database[1,(9,3)]
subarray= ctx._database[0,"subarray"]
tile_clb= ctx._database[0,"tile_clb"]
cluster_i0 = clb._instances[('cluster',0)]
sw20 = ctx._database[1,(9,20)]
ff = cluster_i0.model._instances['ff']
D = ff.pins['D']


# for sink_bus in chain(iter(oport for oport in itervalues(sw20.ports) if oport.direction.is_output),
#                 iter(ipin for instance in itervalues(sw20.instances) for ipin in itervalues(instance.pins) if ipin.model.direction.is_input and not ipin.model.is_clock)):
#         for sink_net in sink_bus:
#                 for src_net in NetUtils.get_multisource(sink_net):
#                         if src_net.net_type == 0:
#                                 continue
                        # print(src_net,sink_net)
                        # src_var_name = "" 
                        # sink_var_name = "" 
                        # if src_net.value is not None:
                        # if src_net.bus.net_type == 1:
                        #         print(src_net.bus.name,src_net.index.start,src_net.bus.name)
                        #         src_var_name = src_net.bus.model.name+ "_" + str(src_net.index.start) + "_src"
                        # else:
                        #         print(src_net.bus.model.name,src_net.index.start,src_net.bus.instance.name,src_net.bus.model.name)
                        #         src_var_name = src_net.bus.model.name+ "_" + str(src_net.index.start) + "_" + src_net.bus.instance.name

                        # if sink_net.bus.net_type == 1:
                        #         sink_var_name = sink_net.bus.name+ "_" + str(sink_net.index.start) + "_sink"
                        #         print(sink_net.bus.name,sink_net.index.start,sink_net.bus.name)
                        # else:
                        #         sink_var_name = sink_net.bus.model.name+ "_" + str(sink_net.index.start) + "_"+ sink_net.bus.instance.name
                        #         print(sink_net.bus.model.name,sink_net.index.start,sink_net.bus.instance.name,sink_net.bus.model.name)
                        # print("Conn: ",src_net," -> ",sink_net)
                        # print("Conn: ",src_net.bus," -> ",sink_net)
                        # print()



# for x in itervalues(clb._instances):
#     if x.model.module_class.is_primitive and x.model.primitive_class.is_lut:
#         print(x)
#         print(x.cfg_bitoffset)
#         print(x.model.cfg_bitcount)

flow = Flow(
        Tester('rtl','unit_tests')
        )
flow.run(ctx, Scanchain.new_renderer())