import cocotb
from cocotb.triggers import Timer,RisingEdge
from cocotb.clock import Clock
from cocotb.binary import BinaryValue
from random import randint
from cocotb.result import TestFailure

@cocotb.coroutine
def always_block(dut):
	cocotb.fork(clock_gen(dut.clk, period=10))
	cocotb.fork(reset_signal(dut))
	yield Timer(100)
	yield RisingEdge(dut.clk)
	dut.src[0] <= 1
	# dut.src[1].value <= 0
	# dut.src[2].value <= 1
	# dut.src[3].value <= 0
	# dut.src[4].value <= 1
	# dut.src[5].value <= 0
	# dut.src[6].value <= 0
	# dut.src[7].value <= 1
	
	while True:
		yield Timer(10)
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
			error=0
			dut._log.info("This is in else statement in coroutine")

			# if(dut.A_full.value==0 and dut.A_rd_cnt.value == len(dut.src)):
			#     dut.A_wr_cnt <= (int(dut.A_wr_cnt.value) + 1)
			# if (dut.B_full.value==0 and dut.B_rd_cnt.value == len(dut.src)):
			#     dut.B_wr_cnt <= (int(dut.B_wr_cnt.value) + 1)
			# if (dut.C_full.value==0 and dut.C_rd_cnt.value == len(dut.src)):
			#     dut.C_wr_cnt <= (int(dut.C_wr_cnt.value) + 1)
			# if (dut.D_full.value==0 and dut.D_rd_cnt.value == len(dut.src)):
			#     dut.D_wr_cnt <= (int(dut.D_wr_cnt.value) + 1)
			# dut.A_valid <= (~dut.A_empty & dut.A_rd)
			# dut.A_valid <= 1
			error = 0
			# if (dut.A_valid.value):
			#     if (dut.src[dut.A_rd_cnt] != dut.A_dout):
			#         error = 1
			#     dut.A_rd_cnt <= dut.A_rd_cnt + 1
			# dut.A_wr_cnt <= 0
			# dut.B_valid <= 1
			# dut.B_valid <= (~dut.B_empty & dut.B_rd)
			# if (dut.B_valid.value):
			#     if (dut.src[dut.B_rd_cnt] != dut.B_dout):
			#         error = 1
			#     dut.B_rd_cnt <= dut.B_rd_cnt + 1
			# if (~dut.C_empty.value and dut.C_rd):
			#   if (dut.src[dut.C_rd_cnt] != dut.C_dout):
			#       error = 1
			#   dut.C_rd_cnt <= dut.C_rd_cnt + 1
			# if (~dut.D_empty.value and dut.D_rd):
			#   if (dut.src[dut.D_rd_cnt] != dut.D_dout):
			#       error = 1
			#   dut.D_rd_cnt <= dut.D_rd_cnt + 1
			dut.A_rd.value = (randint(0,2) == 0)
			dut.B_rd.value = (randint(0,2) == 0)
			dut.C_rd.value = (randint(0,2) == 0)
			dut.D_rd.value = (randint(0,2) == 0)
			# if (dut.A_rd_cnt == len(dut.src) and dut.B_rd_cnt == len(dut.src) and dut.C_rd_cnt == len(dut.src) and    dut.D_rd_cnt == len(dut.src) ):
			#   if (error):
			#       cocotb.log.info("FAIL")
			#   else:
			#       cocotb.log.info("PASS")
			if (error == 1):
				raise TestFailure("FAIL")
				
@cocotb.coroutine
def reset_signal(dut):
	dut.rst <= 1
	yield Timer(10)
	dut.rst <= 0

@cocotb.coroutine
def clock_gen(signal, period=10):
	while True:
		signal <= 0
		yield Timer(period/2)
		signal <= 1
		yield Timer(period/2)

@cocotb.test()
def prga_fifo_test(dut):
	"""Add a description line"""
	
	# clock_period = 10 #This must be an even number
	# # test_time = 10000
	# c= Clock(dut.clk,clock_period)
	# # cocotb.fork(c.start(test_time//clock_period))
	# cocotb.fork(c.start(1000))
	

	yield always_block(dut)