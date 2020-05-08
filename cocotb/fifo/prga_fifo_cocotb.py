import cocotb
from cocotb.triggers import Timer

class prga_fifo_instantiation(object):
	"""docstring for prga_fifo_instantiation"""
	def __init__(self, dut):
		self.dut = dut
	
@cocotb.test()
def prga_fifo_test(dut):

	dut._log.info("Starting Test")

	# Initial block in prga_fifo_tb.v
	rst = 0
	src = [90,246,9,196,129,226,160,122]

	yield Timer(3,"ns")
	dut.rst <= 1

	yield Timer(10,"ns")
	dut.rst <= 0

	# Start clock
	clock_period = 10 #This must be an even number
	test_time = 10000
	c= Clock(dut.clk,clock_period,'sec')
	cocotb.fork(c.start(test_time/clock_period))