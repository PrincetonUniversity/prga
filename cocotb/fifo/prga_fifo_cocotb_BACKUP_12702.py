import cocotb
from cocotb.triggers import Timer,RisingEdge
from cocotb.clock import Clock
from cocotb.binary import BinaryValue
from random import randint
from cocotb.result import TestFailure

@cocotb.coroutine
<<<<<<< HEAD
def reset_signal(dut):
=======
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
>>>>>>> 794312d8fcdd3e4257812c82cbaf7eb65a1889de
	dut.rst <= 1
	yield Timer(10)
	dut.rst <= 0

@cocotb.test()
def prga_fifo_test(dut):
<<<<<<< HEAD
	"""Add a description line"""
	
	clock_period = 10 #This must be an even number
	test_time = 10000
	c= Clock(dut.clk,clock_period)
	cocotb.fork(c.start(test_time//clock_period))
	cocotb.fork(reset_signal(dut))

	yield Timer(100)
	yield RisingEdge(dut.clk)

	dut.src[0] <= 90
	dut.src[1] <= 246
	dut.src[2] <= 9
	dut.src[3] <= 196
	dut.src[4] <= 129
	dut.src[5] <= 226
	dut.src[6] <= 160
	dut.src[7] <= 122
	
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

	yield RisingEdge(dut.clk)

	dut._log.info(str(int(dut.src[0].value)))
	dut._log.info(str(int(dut.src[1].value)))
	dut._log.info(str(int(dut.src[2].value)))
	dut._log.info(str(int(dut.src[3].value)))
	dut._log.info(str(int(dut.src[4].value)))
	dut._log.info(str(int(dut.src[5].value)))
	dut._log.info(str(int(dut.src[6].value)))
	dut._log.info(str(int(dut.src[7].value)))

	error=0
	for _ in range(20):
		yield Timer(20)
		yield RisingEdge(dut.clk)
		if(int(dut.rst.value) == 1):
			dut._log.info("This is if statement in coroutine")
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
			dut._log.info("This is in else statement in coroutine")

			if(int(dut.A_full.value) ==0 and int(dut.A_rd_cnt.value) == 8):
			    dut.A_wr_cnt <= (int(dut.A_wr_cnt.value) + 1)
			if(int(dut.B_full.value) ==0 and int(dut.B_rd_cnt.value) == 8):
				dut.B_wr_cnt <= (int(dut.B_wr_cnt.value) + 1)
			if(int(dut.C_full.value) ==0 and int(dut.C_rd_cnt.value) == 8):
				dut.C_wr_cnt <= (int(dut.C_wr_cnt.value) + 1)
			if(int(dut.D_full.value) ==0 and int(dut.D_rd_cnt.value) == 8):
				dut.D_wr_cnt <= (int(dut.D_wr_cnt.value) + 1)
			
			dut.A_valid <= (not int(dut.A_empty.value) and int(dut.A_rd.value))
			if (int(dut.A_valid.value)):
			    if (dut.src[int(dut.A_rd_cnt.value)] != int(dut.A_dout.value)):
			        error = 1
			    dut.A_rd_cnt <= int(dut.A_rd_cnt.value) + 1

			dut.B_valid <= (not int(dut.B_empty.value) and int(dut.B_rd.value))
			if (int(dut.B_valid.value)):
			    if (dut.src[int(dut.B_rd_cnt.value)] != int(dut.B_dout.value)):
			        error = 1
			    dut.B_rd_cnt <= int(dut.B_rd_cnt.value) + 1

			if (not int(dut.C_empty.value) and int(dut.C_rd.value)):
			    if (dut.src[int(dut.C_rd_cnt.value)] != int(dut.C_dout.value)):
			        error = 1
			    dut.C_rd_cnt <= int(dut.C_rd_cnt.value) + 1

			if (not int(dut.D_empty.value) and int(dut.D_rd.value)):
			    if (dut.src[int(dut.D_rd_cnt.value)] != int(dut.D_dout.value)):
			        error = 1
			    dut.D_rd_cnt <= int(dut.D_rd_cnt.value) + 1

			dut.A_rd.value <= (randint(0,2) == 0)
			dut.B_rd.value <= (randint(0,2) == 0)
			dut.C_rd.value <= (randint(0,2) == 0)
			dut.D_rd.value <= (randint(0,2) == 0)
			
			if (int(dut.A_rd_cnt.value) >8  and int(dut.B_rd_cnt.value) > 8 and int(dut.C_rd_cnt.value) > 8 and int(dut.D_rd_cnt.value) > 8):
				if (error):
					raise TestFailure("FAIL")
=======

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
>>>>>>> 794312d8fcdd3e4257812c82cbaf7eb65a1889de
