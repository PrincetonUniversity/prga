import cocotb
from cocotb.triggers import Timer,RisingEdge,Edge,First
from cocotb.clock import Clock
import random
import math
from cocotb.result import TestFailure
from cocotb.binary import BinaryValue
from cocotb.scoreboard import Scoreboard
import queue
@cocotb.test()
def prga_fifo_test(dut):
    """Test bench from scratch for 4 input LUT"""
    
    clock_period = 10 #This must be an even number
    test_time = 10000
    
    clk = dut.cfg_clk
    c= Clock(clk,clock_period)

    cocotb.fork(c.start(test_time//clock_period,start_high = False))
    
    # cocotb.fork(reset_signal(dut))
    # cocotb.fork(always_star(dut))

    # Signals
    input = dut.bits_in
    out = dut.out
    cfg_e = dut.cfg_e
    cfg_we = dut.cfg_we
    cfg_i = dut.cfg_i
    cfg_o = dut.cfg_o
    cfg_d = dut.cfg_d
    
    # No. of input bits
    n_input = 4

    # Setting up LUT
    # Set the value of cfd
    cfg_e <= 1;
    cfg_we <= 1;
    cfd = []
    n_bits = 2**n_input
    for _ in range(n_bits):
        bit = random.choice([0,1])
        cfd.append(bit)
        cfg_i <= bit
        yield RisingEdge(clk)
    cfd.reverse()
    
    cfg_e <= 0;
    cfg_we <= 0;
    yield RisingEdge(clk)

    output = []
    for i in range(n_bits):
        input <= i
        yield RisingEdge(clk)
        output.append(out.value.integer)
    
    if output != cfd:
        # dut._log.info("[ERROR]")
        raise TestFailure("[ERROR]")