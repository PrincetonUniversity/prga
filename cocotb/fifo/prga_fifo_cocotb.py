import cocotb
from cocotb.triggers import Timer,RisingEdge,Join
from cocotb.clock import Clock
from cocotb.binary import BinaryValue
from random import randint
from cocotb import log

@cocotb.coroutine
def always_block(dut):
	while True:
		yield Timer(1000)
		yield RisingEdge(dut.clk)
		if(dut.rst.value == 1):
			dut._log.info("This is if statement in coroutine")
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
			dut._log.info(str(len(dut.src)))
			dut._log.info(str(len(dut.src[0])))
			dut._log.info(str(len(dut.src[1])))
			dut._log.info(str(len(dut.src[2])))
			dut._log.info(str(len(dut.src[3])))
			dut._log.info(str(len(dut.src[4])))
			dut._log.info(str(len(dut.src[5])))
			dut._log.info(str(len(dut.src[6])))
			dut._log.info(str(len(dut.src[7])))
			if(dut.A_full.value==0 and dut.A_rd_cnt == len(dut.src)):
					dut.A_wr_cnt <= (int(dut.A_wr_cnt.value) + 1)

			if (dut.B_full.value==0 and dut.B_rd_cnt == len(dut.src)):
				dut.B_wr_cnt <= dut.B_wr_cnt + 1
			
			if (dut.C_full.value==0 and dut.C_rd_cnt == len(dut.src)):
				dut.C_wr_cnt <= dut.C_wr_cnt + 1

			if (dut.D_full.value==0 and dut.D_rd_cnt == len(dut.src)):
				dut.D_wr_cnt <= dut.D_wr_cnt + 1

			# dut.A_valid <= (~dut.A_empty & dut.A_rd)
			dut.A_valid <= 1

			if (dut.A_valid.value):
				if (dut.src[dut.A_rd_cnt] != dut.A_dout):
					error = 1
				dut.A_rd_cnt <= dut.A_rd_cnt + 1
			dut.A_wr_cnt <= 0

			dut.B_valid <= 1
			# dut.B_valid <= (~dut.B_empty & dut.B_rd)

			if (dut.B_valid.value):
				if (dut.src[dut.B_rd_cnt] != dut.B_dout):
					error = 1
				dut.B_rd_cnt <= dut.B_rd_cnt + 1

			# if (~dut.C_empty.value and dut.C_rd):
			# 	if (dut.src[dut.C_rd_cnt] != dut.C_dout):
			# 		error = 1
			# 	dut.C_rd_cnt <= dut.C_rd_cnt + 1

			# if (~dut.D_empty.value and dut.D_rd):
			# 	if (dut.src[dut.D_rd_cnt] != dut.D_dout):
			# 		error = 1
			# 	dut.D_rd_cnt <= dut.D_rd_cnt + 1

			dut.A_rd.value = (randint(0,2) == 0)
			dut.B_rd.value = (randint(0,2) == 0)
			dut.C_rd.value = (randint(0,2) == 0)
			dut.D_rd.value = (randint(0,2) == 0)

			# if (dut.A_rd_cnt == len(dut.src) and dut.B_rd_cnt == len(dut.src) and dut.C_rd_cnt == len(dut.src) and	dut.D_rd_cnt == len(dut.src) ):
			# 	if (error):
			# 		cocotb.log.info("FAIL")
			# 	else:
			# 		cocotb.log.info("PASS")
			if (error):
				cocotb.log.info("FAIL")
			else:
				cocotb.log.info("PASS")


@cocotb.coroutine
def reset_signal(dut):
    dut.rst <= 1
    yield Timer(10)
    dut.rst <= 0
    
@cocotb.test()
def prga_fifo_test(dut):

	# Initial block in prga_fifo_tb.v
	# vec = BinaryValue()
	# vec.integer =190 
	# print(dut.src.value[0].binstr)
	dut.src.value[1] <= 246
	dut.src.value[2] <= 9
	dut.src.value[3] <= 196
	dut.src.value[4] <= 129
	dut.src.value[5] <= 226
	dut.src.value[6] <= 160
	dut.src.value[7] <= 122
	print(len(dut.src))
	dut._log.info(str(len(dut.src)))
	# Start clock
	clock_period = 10 #This must be an even number
	# test_time = 10000
	c= Clock(dut.clk,clock_period)
	
	# cocotb.fork(c.start(test_time//clock_period))
	cocotb.fork(c.start(1000))

	yield Timer(1000)
	cocotb.fork(reset_signal(dut))
	yield always_block(dut)
