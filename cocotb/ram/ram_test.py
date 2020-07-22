"""
Example of a simple testbench for a RAM block
"""
import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import Timer, RisingEdge, ReadOnly
from cocotb.result import TestFailure, ReturnValue

@cocotb.coroutine
def write_ram(dut, address, value):
    """This coroutine performs a write of the RAM"""
    yield RisingEdge(dut.clk_write)              # Synchronise to the read clock
    dut.address_write = address                  # Drive the values
    dut.data_write    = value
    dut.write_enable  = 1
    yield RisingEdge(dut.clk_write)              # Wait 1 clock cycle
    dut.write_enable  = 0                        # Disable write

@cocotb.coroutine
def read_ram(dut, address):
    """This coroutine performs a read of the RAM and returns a value"""
    yield RisingEdge(dut.clk_read)               # Synchronise to the read clock
    dut.address_read = address                   # Drive the value onto the signal
    yield RisingEdge(dut.clk_read)               # Wait for 1 clock cycle
    yield ReadOnly()                             # Wait until all events have executed for this timestep
    raise ReturnValue(int(dut.data_read.value))  # Read back the value


@cocotb.test()
def test_ram(dut):
    """Try writing values into the RAM and reading back"""
    RAM = {}
    
    # Read the parameters back from the DUT to set up our model
    width = dut.D_WIDTH.value.integer
    depth = 2**dut.A_WIDTH.value.integer
    dut._log.info("Found %d entry RAM by %d bits wide" % (depth, width))

    # Set up independent read/write clocks
    cocotb.fork(Clock(dut.clk_write, 3200).start())
    cocotb.fork(Clock(dut.clk_read, 5000).start())
    
    dut._log.info("Writing in random values")
    for i in range(depth):
        RAM[i] = int(random.getrandbits(width))
        yield write_ram(dut, i, RAM[i])

    dut._log.info("Reading back values and checking")
    for i in range(depth):
        value = yield read_ram(dut, i)
        if value != RAM[i]:
            dut._log.error("RAM[%d] expected %d but got %d" % (i, RAM[i], dut.data_read.value.value))
            raise TestFailure("RAM contents incorrect")
    dut._log.info("RAM contents OK")
