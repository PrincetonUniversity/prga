import cocotb
from cocotb.triggers import Timer,RisingEdge,Join
from cocotb.clock import Clock
from cocotb.binary import BinaryValue
from random import randint
from cocotb.result import TestFailure

@cocotb.coroutine
def reset_signal(dut):
	dut.rst <= 1
	yield Timer(100)
	dut.rst <= 0
	
@cocotb.test()
def prga_fifo_test(dut):
	"""Add a description line"""
	
	clock_period = 10 #This must be an even number
	test_time = 10000
	c= Clock(dut.clk,clock_period)
	cocotb.fork(c.start(test_time//clock_period))
	
	reset_thread = cocotb.fork(reset_signal(dut))

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

	yield reset_thread.join()
	
	for _ in range(100):
		yield Timer(20)
		yield RisingEdge(dut.clk)
		dut._log.info(str(dut.rst.value))
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