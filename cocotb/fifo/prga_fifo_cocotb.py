import cocotb
from cocotb.triggers import Timer,RisingEdge
from cocotb.clock import Clock
from random import randint

@cocotb.coroutine
def always_block(dut):
	yield RisingEdge(dut.clk)
	error = 0
	if(dut.rst.value == 1):
		dut.A_wr_cnt <= 0
		dut.B_wr_cnt <= 0
		dut.C_wr_cnt <= 0
		dut.D_wr_cnt <= 0
		dut.A_rd_cnt <= 0
		dut.B_rd_cnt <= 0
		dut.C_rd_cnt <= 0
		dut.D_rd_cnt <= 0
		dut.A_valid <= 0
		dut.A_rd <= 0
		dut.B_valid <= 0
		dut.B_rd <= 0
		dut.C_rd <= 0
		dut.D_rd <= 0
	else:
		if(dut.A_full.value==0 and dut.A_rd_cnt == len(dut.src)):
				dut.A_wr_cnt <= (int(dut.A_wr_cnt.value) + 1)

		if (dut.B_full.value==0 and dut.B_rd_cnt == len(dut.src)):
			dut.B_wr_cnt <= dut.B_wr_cnt + 1
		
		if (dut.C_full.value==0 and dut.C_rd_cnt == len(dut.src)):
			dut.C_wr_cnt <= dut.C_wr_cnt + 1

		if (dut.D_full.value==0 and dut.D_rd_cnt == len(dut.src)):
			dut.D_wr_cnt <= dut.D_wr_cnt + 1

		dut.A_valid <= ~dut.A_empty and dut.A_rd

		if (dut.A_valid.value):
			if (dut.src[dut.A_rd_cnt] != dut.A_dout):
				error = 1
			dut.A_rd_cnt <= dut.A_rd_cnt + 1

		dut.B_valid <= ~dut.B_empty and dut.B_rd

		if (dut.B_valid.value):
			if (dut.src[dut.B_rd_cnt] != dut.B_dout):
				error = 1
			dut.B_rd_cnt <= dut.B_rd_cnt + 1

		if (~dut.C_empty.value and dut.C_rd):
			if (dut.src[dut.C_rd_cnt] != dut.C_dout):
				error = 1
			dut.C_rd_cnt <= dut.C_rd_cnt + 1

		if (~dut.D_empty.value and dut.D_rd):
			if (dut.src[dut.D_rd_cnt] != dut.D_dout):
				error = 1
			dut.D_rd_cnt <= dut.D_rd_cnt + 1

		dut.A_rd.value = (randint(0,2) == 0)
		dut.B_rd.value = (randint(0,2) == 0)
		dut.C_rd.value = (randint(0,2) == 0)
		dut.D_rd.value = (randint(0,2) == 0)

		if (dut.A_rd_cnt == len(dut.src) and dut.B_rd_cnt == len(dut.src) and dut.C_rd_cnt == len(dut.src) and	dut.D_rd_cnt == len(dut.src) ):
			if (error):
				cocotb.log.info("FAIL")
			else:
				cocotb.log.info("PASS")

@cocotb.coroutine
def reset_signal(dut):
	dut.rst <= 0
	yield Timer(3)
	dut.rst <= 1
	yield Timer(10)
	dut.rst <= 0

@cocotb.test()
def prga_fifo_test(dut):

	dut._log.info("Starting Test")
	# cocotb.log.info(dut.src)
	print("Start")

	# Initial block in prga_fifo_tb.v
	dut.src <= [90,246,9,196,129,226,160,122]

	# Start clock
	clock_period = 10 #This must be an even number
	test_time = 10000
	c= Clock(dut.clk,clock_period)
	
	cocotb.fork(c.start(test_time//clock_period))

	cocotb.fork(always_block(dut))
	cocotb.fork(reset_signal(dut))