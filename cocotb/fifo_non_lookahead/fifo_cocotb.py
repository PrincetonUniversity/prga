import cocotb
from cocotb.triggers import Timer,RisingEdge,Join
from cocotb.clock import Clock
import random
from cocotb.result import TestFailure

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

    cocotb.fork(c.start(test_time//clock_period))
    
    cocotb.fork(reset_signal(dut))
    data_width = int(dut.DATA_WIDTH.value)
    
    # DECLARATIONS
    len_src = 8
    src=[]
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
    for i in range(len_src):
        dut._log.info("src["+str(i)+"]="+str(src[i]))

    for index in range(100):
        yield RisingEdge(dut.clk)
        # dut._log.info(str(dut.rst.value))
        if(int(dut.rst.value) == 1 ):
            curr_pos_rd = 0
            curr_pos_wr = 0
            valid = 0
            rd <= 0
        else:
            if(~int(full.value) and (curr_pos_wr+1)<len_src):
                curr_pos_wr += 1
                din <= src[curr_pos_wr]

            yield RisingEdge(dut.clk)
            valid = (~int(empty.value) and int(rd.value))
            if (valid):
                yield RisingEdge(dut.clk)            
                if (src[curr_pos_rd] != int(dout.value)):
                    error = 1;
                    raise TestFailure("[ERROR] output No. %d 0x%08x != 0x%08x", curr_pos_rd, int(dout.value), src[curr_pos_rd]);
                curr_pos_rd += 1
                

            rd <= random.choice([0,1])

            if(curr_pos_rd > 8):
                break