import cocotb
from cocotb.triggers import Timer,RisingEdge,Join
from cocotb.clock import Clock
import random
import math
from cocotb.result import TestFailure
from cocotb.binary import BinaryValue

valid = 0

@cocotb.coroutine
def reset_signal(dut):
    dut.rst <= 1
    yield Timer(100)
    dut.rst <= 0

@cocotb.test()
def prga_fifo_test(dut):
    """Test bench from scratch for non-lookahead buffer"""
    
    clock_period = 10 #This must be an even number
    test_time = 10000
    c= Clock(dut.clk,clock_period)

    cocotb.fork(c.start(test_time//clock_period,start_high = False))
    
    cocotb.fork(reset_signal(dut))
    data_width = int(dut.DATA_WIDTH.value)
    
    # DECLARATIONS
    len_src = 2**int(dut.DEPTH_LOG2.value)
    src=[]
    curr_pos_wr = 0 
    curr_pos_wr = 0
    curr_pos_rd = 0
    valid = 0
    error = 0
    # The following are simulation objects
    empty = dut.empty # output from DUT
    full = dut.full # output from DUT
    wr = dut.wr
    rd = dut.rd
    din = dut.din
    dout = dut.dout # output from DUT

    # Initialize src array
    src = random.sample(range(0, 2**data_width -1), len_src)
    # src = [i for i in range(1,len_src+1)]
    for i in range(len_src):
        dut._log.info("src["+str(i)+"]="+str(src[i]))

    din <= 0
    wr <= 0
    rd <= 0

    for index in range(100):
        yield RisingEdge(dut.clk)
        # dut._log.info(str(dut.rst.value))
        if(int(dut.rst.value) == 1 ):
            curr_pos_rd = 0
            curr_pos_wr = 0
            valid = 0
            rd <= 0
            din <= src[curr_pos_wr]
            dut.wr <= (curr_pos_wr < len_src)
            error = 0
        else:
            if(~int(full.value) and (curr_pos_wr+1)<len_src):
                curr_pos_wr += 1
                dut.wr <= (curr_pos_wr < len_src)
                din <= src[curr_pos_wr]

            valid = (~int(empty.value) & int(rd.value))
            
            if (valid):
                dut._log.info(str(src[curr_pos_rd]))
                dut._log.info("Inside Valid "+str(dout.value.integer))
                if(src[curr_pos_rd] != dout.value.integer):
                    error = 1
                    dut._log.info("[ERROR] output No." +str(curr_pos_rd) + " "+ str(dout.value.integer)+ " != "+ str(src[curr_pos_rd]))
                    # raise TestFailure("[ERROR] output No." +str(curr_pos_rd) + " "+ str(dout.value.integer)+ " != "+ str(src[curr_pos_rd]))
                curr_pos_rd += 1
                
            rd <= random.choice([0,1])

            if(curr_pos_rd == len_src):
                break