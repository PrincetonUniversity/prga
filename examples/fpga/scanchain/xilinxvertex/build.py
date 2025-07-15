from prga import *
from itertools import product

import sys
ctx = Context()
gbl_clk = ctx.create_global("clk",is_clock = 'True')
gbl_clk.bind((0,1),0)

ctx.create_segment('L2',20,2)


# describing an iob
builder = ctx.build_io_block("iob")
o = builder.create_input("outpad",1)
i = builder.create_output("inpad",1)
builder.connect(builder.instances['io'].pins['inpad'],i)
builder.connect(o,builder.instances['io'].pins['outpad'])
iob = builder.commit()


ub = ctx.build_primitive("xilinxvertex6.mux", 
                                     verilog_template="builtin/mux.lib.tmpl.v", 
                                     abstract_only = True,vpr_model ="m_mux2") 
inputs1 = [ 
          ub.create_input("i0",1), 
          ub.create_input("i1",1), 
          ub.create_input("sel",1) 
      ] 
output1 = ub.create_output("y",1) 
for i in inputs1: 
      ub.create_timing_arc(TimingArcType.comb_matrix, i, output1) 
mux22 = ub.commit() 
ubd = ctx.build_primitive("xilinxvertex6.xor2", 
                                     verilog_template="builtin/adder.lib.tmpl.v", 
                                     techmap_template="builtin/adder.techmap.tmpl.v",
                                     abstract_only = True,vpr_model ="m_xor2") 
inputs = [ 
          ubd.create_input("a",1), 
          ubd.create_input("b",1) 
      ]  
outputs = ubd.create_output("c",1)
for i in inputs: 
            ubd.create_timing_arc(TimingArcType.comb_matrix, i,outputs) 
xor2 = ubd.commit() 

# describing the inputs and outputs in the CLB
builder = ctx.build_slice("slice")
clk = builder.create_clock("clk")

ina = builder.create_input("ina",6)
ax =  builder.create_input("ax",1)
cin = builder.create_input("cin",1)
amux = builder.create_output("amux",1)   #modelling the first ble
a = builder.create_output("a",1)
aq =  builder.create_output("aq",1)
cout = builder.create_output("cout",1)
ce = builder.create_input("ce",1)

inb = builder.create_input("inb",6)
bx =  builder.create_input("bx",1)
bmux = builder.create_output("bmux",1)   #modelling the second ble
b = builder.create_output("b",1)
bq =  builder.create_output("bq",1)


mux0 = builder.instantiate(ctx.primitives["xilinxvertex6.mux"], "i_mux_8")
mux6 = builder.instantiate(ctx.primitives["xilinxvertex6.mux"], "i_mux_9")
lut3 = builder.instantiate(ctx.primitives["lut5"], "i_lut5_3")
lut4 = builder.instantiate(ctx.primitives["lut5"], "i_lut5_4")

builder.connect(builder.ports["inb"][4:0], lut3.pins["in"])  #modelling the lut 6
builder.connect(builder.ports["inb"][4:0], lut4.pins["in"]) 
builder.connect(lut3.pins["out"], mux6.pins["i0"])
builder.connect(lut4.pins["out"], mux6.pins["i1"])            #lut4.pins[:out]  represent o5
builder.connect(builder.ports["inb"][5], mux6.pins["sel"])   #mux6.pins["y"]  represent o6 (lut3)
                                                             

mux = builder.instantiate(ctx.primitives["xilinxvertex6.mux"], "i_mux")
mux1 = builder.instantiate(ctx.primitives["xilinxvertex6.mux"], "i_mux_1")
adder = builder.instantiate(ctx.primitives["adder"], "i_adder")
lut1 = builder.instantiate(ctx.primitives["lut5"], "i_lut5")
lut2 = builder.instantiate(ctx.primitives["lut5"], "i_lut5_1")

builder.connect(builder.ports["ina"][4:0], lut1.pins["in"])
builder.connect(builder.ports["ina"][4:0], lut2.pins["in"])
builder.connect(lut1.pins["out"], mux.pins["i0"])
builder.connect(lut2.pins["out"], mux.pins["i1"])
builder.connect(builder.ports["ina"][5], mux.pins["sel"])

# implementing xor gate
xor = builder.instantiate(ctx.primitives["xilinxvertex6.xor2"], "i_xor2")
builder.connect(builder.ports["cin"], adder.pins["cin"], vpr_pack_patterns=["carrychain"])
builder.connect(builder.ports["ax"], mux1.pins["i1"])
builder.connect(lut2.pins["out"], mux1.pins["i1"])  #lut2.pins["out represent o5"]
builder.connect(builder.ports["ax"], mux1.pins["i0"])
builder.connect(builder.ports["cin"], mux1.pins["i0"])
builder.connect(mux.pins["y"], mux1.pins["sel"])         #mux.pins["y"]  represent o6


builder.connect(builder.ports["ax"], xor.pins["a"])
builder.connect(builder.ports["cin"], xor.pins["a"])
builder.connect(mux.pins["y"], xor.pins["b"])
builder.connect(xor.pins["c"], builder.ports["amux"])

ff1 = builder.instantiate(ctx.primitives["dffe"], "i_flipflop")
builder.connect(builder.ports["ax"], ff1.pins["D"])
builder.connect(lut2.pins["out"], ff1.pins["D"])
builder.connect(ff1.pins["Q"], builder.ports["amux"])
builder.connect(mux1.pins["y"], builder.ports["amux"])
builder.connect(mux6.pins["y"], builder.ports["amux"])
builder.connect(lut2.pins["out"], builder.ports["amux"])
builder.connect(mux.pins["y"], builder.ports["amux"])

ff2 = builder.instantiate(ctx.primitives["dffe"], "i_flipflop1")
builder.connect(builder.ports["clk"], ff2.pins["C"])
builder.connect(builder.ports["ce"], ff2.pins["E"])
builder.connect(lut2.pins["out"], ff2.pins["D"])
builder.connect(mux.pins["y"], ff2.pins["D"])
builder.connect(xor.pins["c"], ff2.pins["D"])
builder.connect(builder.ports["ax"], ff2.pins["D"])
builder.connect(ff2.pins["Q"], builder.ports["aq"])
builder.connect(mux.pins["y"], builder.ports["a"])


xor1 = builder.instantiate(ctx.primitives["xilinxvertex6.xor2"], "i_xor2_1")
builder.connect(builder.ports["bx"], mux0.pins["i1"])
builder.connect(lut4.pins["out"], mux0.pins["i1"])  
builder.connect(builder.ports["bx"], mux0.pins["i0"])
builder.connect(mux1.pins["y"], mux0.pins["i0"])
builder.connect(mux6.pins["y"], mux0.pins["sel"])        
builder.connect(mux0.pins["y"], builder.ports["cout"])

builder.connect(builder.ports["bx"], xor1.pins["a"])
builder.connect(mux1.pins["y"], xor1.pins["a"])
builder.connect(mux6.pins["y"], xor1.pins["b"])
builder.connect(xor1.pins["c"], builder.ports["bmux"])

ff3 = builder.instantiate(ctx.primitives["dffe"], "i_flipflop_3")
builder.connect(builder.ports["bx"], ff3.pins["D"])
builder.connect(lut4.pins["out"], ff3.pins["D"])
builder.connect(ff3.pins["Q"], builder.ports["bmux"])
builder.connect(mux6.pins["y"], builder.ports["bmux"])
builder.connect(lut4.pins["out"], builder.ports["bmux"])
builder.connect(mux0.pins["y"], builder.ports["bmux"])

ff4 = builder.instantiate(ctx.primitives["dffe"], "i_flipflop_4")
builder.connect(builder.ports["clk"], ff4.pins["C"])
builder.connect(builder.ports["ce"], ff4.pins["E"])
builder.connect(lut4.pins["out"], ff4.pins["D"])
builder.connect(mux6.pins["y"], ff4.pins["D"])
builder.connect(xor1.pins["c"], ff4.pins["D"])
builder.connect(builder.ports["bx"], ff4.pins["D"])
builder.connect(ff4.pins["Q"], builder.ports["bq"])
builder.connect(mux6.pins["y"], builder.ports["b"])


clust=builder.commit()


# connecting the inupts and outputs in the CLB
builder=ctx.build_logic_block("clb")
clk= builder.create_global(gbl_clk,Orientation.south)
ina  = builder.create_input("ina", 6,Orientation.west)
ax   = builder.create_input("ax", 1,Orientation.west)
cin = builder.create_input("cin",1,Orientation.south)
ce   = builder.create_input("ce", 1,Orientation.west)

amux = builder.create_output("amux", 1,Orientation.east)
a    = builder.create_output("a", 1,Orientation.east)
aq   = builder.create_output("aq", 1,Orientation.east)


inb  = builder.create_input("inb", 6,Orientation.west)
bx   = builder.create_input("bx", 1,Orientation.west)
bmux = builder.create_output("bmux", 1,Orientation.east)
b    = builder.create_output("b", 1,Orientation.east)
bq   = builder.create_output("bq", 1,Orientation.east)
cout = builder.create_output("cout", 1,Orientation.north)
inst = builder.instantiate(clust,"clust")
builder.connect(clk,inst.pins['clk'])
builder.connect(ina,inst.pins['ina'])
builder.connect(ax,inst.pins['ax'])
builder.connect(cin,inst.pins['cin'])
builder.connect(inst.pins['amux'],amux)
builder.connect(inst.pins['a'],a)
builder.connect(inst.pins['aq'],aq)

builder.connect(inb,inst.pins['inb'])
builder.connect(bx,inst.pins['bx'])
builder.connect(inst.pins['bmux'],amux)
builder.connect(inst.pins['b'],b)
builder.connect(inst.pins['bq'],bq)

builder.connect(inst.pins['cout'],cout,vpr_pack_patterns = ["carrychain"])
clb = builder.commit()

ctx.create_tunnel("carrychain",clb.ports["cout"],clb.ports["cin"],(0,-1))
clbtile = ctx.build_tile(clb).fill((0.4,0.25)).auto_connect().commit()

iotiles = {}
for ori in Orientation:
    builder =  ctx.build_tile(iob, 4, name = "t_io_{}".format(ori.name[0]), 
                              edge = OrientationTuple(False, **{ori.name: True}))
    iotiles[ori] = builder.fill((1.,1.)).auto_connect().commit()

builder = ctx.build_array('top', 8, 8, set_as_top = True)
for x,y in product(range(8),range(8)):
    if x in (0,7) and y in (0,7):
        pass
    elif x == 0:
        builder.instantiate(iotiles[Orientation.west], (x,y))
    elif x == 7:
        builder.instantiate(iotiles[Orientation.east], (x,y))
    elif y == 0:
        builder.instantiate(iotiles[Orientation.south], (x,y))
    elif y == 7:
        builder.instantiate(iotiles[Orientation.north], (x,y))
    else :
        builder.instantiate(clbtile, (x,y))
top = builder.fill( SwitchBoxPattern.cycle_free ).auto_connect().commit()

Flow(
        VPRArchGeneration('vpr/arch.xml'),
        VPR_RRG_Generation('vpr/rrg.xml'),
        YosysScriptsCollection('syn'),
         Materialization('scanchain'),
        
       
        
        ).run(ctx)

ctx.pickle("ctx.pkl" if len(sys.argv) < 2 else sys.argv[1])
