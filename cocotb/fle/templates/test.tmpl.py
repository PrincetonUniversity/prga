import cocotb
from cocotb.triggers import Timer,RisingEdge,Edge,First,ReadOnly,NextTimeStep
from cocotb.clock import Clock
import random
from cocotb.result import TestFailure,TestSuccess
# For handling global variables
import config

def clock_generation(clk,clock_period=10,test_time=10000):
    c= Clock(clk,clock_period)
    cocotb.fork(c.start(test_time//clock_period))

@cocotb.coroutine
def always_posedge(dut):
    while True:
        yield RisingEdge(dut.clk)
        mode = dut.mode.value.integer
        if mode == 0:
            config.internal_ff[0] = config.internal_lut[1] if input//32 else config.internal_lut[0]
            config.internal_ff[1] = 0
        elif mode == 1:
            config.internal_ff = config.internal_lut
        elif mode == 3:
            config.internal_ff = [config.internal_sum%2,config.internal_sum//2]

@cocotb.coroutine
def always_star(dut,cfg_d,LUT5A_DATA,LUT5B_DATA,CIN_FABRIC,ENABLE_FFA,ENABLE_FFB):

    mode = dut.mode.value.integer
    expected_out = [0,0]
    expected_cout = 0

    while True:
        yield Edge(dut.test_clk)
        yield ReadOnly()
        if(dut.internal_in.value.binstr != 'zzzzzz'):
            input = dut.internal_in.value.integer
            config.internal_lut = [cfg_d[input%32+LUT5A_DATA],cfg_d[input%32+LUT5B_DATA]]
            config.internal_sum = config.internal_lut[0] + config.internal_lut[1]+ (input//32 if cfg_d[CIN_FABRIC] else dut.cin.value.integer)


            if mode == 0:

                expected_cout = 0
                
                if cfg_d[ENABLE_FFA]:
                    expected_out[0] = config.internal_ff[0]
                else:
                    expected_out[0] = config.internal_lut[1] if input//32 else config.internal_lut[0]
                
                expected_out[1] = 0

                if (expected_out[0]+2*expected_out[1]) != dut.out.value.integer: 
                    dut._log.info("Mode LUT5X2 given bits_in bits " + str(input)+" expected_out!=out")
                    # raise TestFailure("Mode LUT5X2 given bits_in bits " + str(input)+" expected_out[1]!=out[0]")

                if expected_cout != dut.cout.value.integer:
                    # dut._log.info("Mode LUT6X1 given bits_in bits " + str(input)+" expected_cout!=cout")
                    raise TestFailure("Mode LUT6X1 given bits_in bits " + str(input)+" expected_cout!=cout")
                
                raise TestSuccess("Test Success")

            elif mode == 1:

                if cfg_d[ENABLE_FFA]:
                    expected_out[0] = config.internal_ff[0]
                else:
                    expected_out[0] = config.internal_lut[0]
                
                if cfg_d[ENABLE_FFB]:
                    expected_out[1] = config.internal_ff[1]
                else:
                    expected_out[1] = config.internal_lut[1]
                
                if (expected_out[0]+2*expected_out[1]) != dut.out.value.integer: 
                    dut._log.info("Mode LUT5X2 given bits_in bits " + str(input)+" expected_out!=out")
                    # raise TestFailure("Mode LUT5X2 given bits_in bits " + str(input)+" expected_out[1]!=out[0]")
                                
                if expected_cout != dut.cout.value.integer:
                    dut._log.info("Mode LUT5X2 given bits_in bits " + str(input)+" expected_cout!=cout")
                    # raise TestFailure("Mode LUT5X2 given bits_in bits " + str(input)+" expected_cout!=cout")

            elif mode == 3:

                if cfg_d[ENABLE_FFA]:
                    expected_out[0] = config.internal_ff[0]
                else:
                    expected_out[0] = config.internal_sum%2
                
                if cfg_d[ENABLE_FFB]:
                    expected_out[1] = config.internal_ff[1]
                else:
                    expected_out[1] = config.internal_sum//2                

                expected_cout = config.internal_sum//2
                
                if dut.out.value[0].binstr != 'x' and dut.out.value[1].binstr != 'x':
                    if (expected_out[0]+2*expected_out[1]) != dut.out.value.integer: 
                        dut._log.info("Mode ARITH given bits_in bits " + str(input)+" expected_out!=out")
                        # raise TestFailure("Mode ARITH given bits_in bits " + str(input)+" expected_out[1]!=out[0]")
                
                if expected_cout != dut.cout.value.integer:
                    dut._log.info("Mode ARITH given bits_in bits " + str(input)+" expected_cout!=cout")
                    # raise TestFailure("Mode ARITH given bits_in bits " + str(input)+" expected_cout!=cout")

            else:
                raise TestFailure("Mode Not Supported")  

@cocotb.coroutine
def wrapper(dut,test_mode=0):
    """Wrapper code for test """
    
    clk = dut.clk
    cfg_clk = dut.cfg_clk
    
    clock_generation(cfg_clk)
    clock_generation(clk)
    clock_generation(dut.test_clk,clock_period=2)
    

    # Signals
    bits_in = dut.bits_in
    out = dut.out
    cin = dut.cin
    cout = dut.cout
    cfg_e = dut.cfg_e
    cfg_we = dut.cfg_we
    cfg_i = dut.cfg_i
    cfg_o = dut.cfg_o
    
    # Local Parameters
    LUT5A_DATA_WIDTH = dut.LUT5A_DATA_WIDTH.value.integer
    LUT5B_DATA_WIDTH = dut.LUT5B_DATA_WIDTH.value.integer
    MODE_WIDTH = dut.MODE_WIDTH.value.integer

    LUT5A_DATA = dut.LUT5A_DATA.value.integer
    LUT5B_DATA = dut.LUT5B_DATA.value.integer
    ENABLE_FFA = dut.ENABLE_FFA.value.integer
    ENABLE_FFB = dut.ENABLE_FFB.value.integer
    MODE = dut.MODE.value.integer
    
    CIN_FABRIC = dut.CIN_FABRIC.value.integer
    CFG_BITCOUNT = dut.CFG_BITCOUNT.value.integer

    # No. of input bits
    n_input = {{module.n_input}}

    cfg_d = []

    # Set the value of cfg_d
    cfg_e <= 1;
    cfg_we <= 1;

    yield NextTimeStep()

    dut._log.info("        TEST PARAMETERS         ")
    n_bits = CFG_BITCOUNT
    
    # Set CIN_FABRIC bit
    cin_fabric = random.choice([0,1]) 
    # cin_fabric = 0 
    cfg_d.insert(0,cin_fabric)
    cfg_i <= cin_fabric
    yield RisingEdge(cfg_clk)
    dut._log.info("        CIN_FABRIC "+str(cin_fabric))

    if test_mode == 0:
        dut._log.info("        LUT6 + optional DFF         ")
    elif test_mode == 2:
        dut._log.info("        2x (LUT5 + optional DFF)         ")
    else:
        dut._log.info("        2x LUT => adder => optional DFF for sum & cout_fabric         ")

    for _ in range(MODE_WIDTH):
        cfg_d.insert(0,test_mode%2)
        cfg_i <= test_mode%2
        test_mode//=2 
        yield RisingEdge(cfg_clk)
    
    # Set the ENABLE_FFB
    enable_ffb = random.choice([0,1]) 
    # enable_ffb = 0 
    cfg_d.insert(0,enable_ffb)
    cfg_i <= enable_ffb
    yield RisingEdge(cfg_clk)
    dut._log.info("        enable_ffb "+str(enable_ffb))

    # Set the ENABLE_FFA
    enable_ffa = random.choice([0,1]) 
    # enable_ffa = 0 
    cfg_d.insert(0,enable_ffa)
    cfg_i <= enable_ffa
    yield RisingEdge(cfg_clk)
    dut._log.info("        enable_ffa "+str(enable_ffa))
    
    # Set the LUTB_DATA
    b_data = random.choice(range(2**LUT5B_DATA_WIDTH - 1))
    # b_data =1
    dut._log.info("        b_data is "+str(b_data)+"         ")
    for _ in range(LUT5B_DATA_WIDTH):
        cfg_d.insert(0,b_data%2)
        cfg_i <= b_data%2
        b_data//=2 
        yield RisingEdge(cfg_clk)

    # Set the LUTA_DATA
    a_data = random.choice(range(2**LUT5A_DATA_WIDTH - 1))
    # a_data =1
    dut._log.info("       a_data is "+str(a_data)+"         ")
    for _ in range(LUT5A_DATA_WIDTH):
        cfg_d.insert(0,a_data%2)
        cfg_i <= a_data%2
        a_data//=2 
        yield RisingEdge(cfg_clk)

    cfg_e <= 0;
    cfg_we <= 0;

    yield RisingEdge(cfg_clk)

    cocotb.fork(always_posedge(dut))
    cocotb.fork(always_star(dut,cfg_d,LUT5A_DATA,LUT5B_DATA,CIN_FABRIC,ENABLE_FFA,ENABLE_FFB))


    for i in range(2**n_input):
        bits_in <= i
        cin <= random.choice([0,1])
        yield RisingEdge(clk)

    if test_mode == 3:
        bits_in <= 0
        cin <= random.choice([0,1])
        yield RisingEdge(clk)

# Set the MODE
# 3 modes:
#  a) LUT6 + optional DFF (mode = 0) 
#  b) 2x (LUT5 + optional DFF (mode = 2)
#  c) 2x LUT => adder => optional DFF for sum & cout_fabric (mode = 3)

@cocotb.test()
def test_LUT6X1(dut):
    """  LUT6 + optional DFF (mode = 0) """
    yield wrapper(dut,test_mode=0)

@cocotb.test()
def test_LUT5X2(dut):
    """  2x (LUT5 + optional DFF (mode = 2) """
    yield wrapper(dut,test_mode=2)

@cocotb.test()
def test_ARITH(dut):
    """  2x LUT => adder => optional DFF for sum & cout_fabric (mode = 3) """
    yield wrapper(dut,test_mode=3)