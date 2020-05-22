import cocotb
from cocotb.triggers import Timer,RisingEdge,Join
from cocotb.clock import Clock
from cocotb.binary import BinaryValue
from random import randint
<<<<<<< HEAD
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
=======
from cocotb.result import TestFailure
>>>>>>> 15311bcaf0f8b49a069f91f5503fe2e10501211f


@cocotb.coroutine
def reset_signal(dut):
    dut.rst <= 1
    yield Timer(10)
    dut.rst <= 0
    
@cocotb.test()
def prga_fifo_test(dut):
<<<<<<< HEAD

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
=======
    """Add a description line"""
    
    clock_period = 10 #This must be an even number
    test_time = 10000
    c= Clock(dut.clk,clock_period)
    cocotb.fork(c.start(test_time//clock_period))
    
    reset_thread = cocotb.fork(reset_signal(dut))

    # yield Timer(100)
    # yield reset_signal(dut)

    # yield RisingEdge(dut.clk)

    dut.src[0] <= 90
    dut.src[1] <= 246
    dut.src[2] <= 9
    dut.src[3] <= 196
    dut.src[4] <= 129
    dut.src[5] <= 226
    dut.src[6] <= 160
    dut.src[7] <= 122
    
    # dut.A_wr_cnt <= 0
    # dut.B_wr_cnt <= 0
    # dut.C_wr_cnt <= 0
    # dut.D_wr_cnt <= 0
    # dut.A_rd_cnt <= 0
    # dut.B_rd_cnt <= 0
    # dut.C_rd_cnt <= 0
    # dut.D_rd_cnt <= 0
    # dut.A_valid <= 0
    # dut.A_rd <= 0
    # dut.B_valid <= 0
    # dut.B_rd <= 0
    # dut.C_rd <= 0
    # dut.D_rd <= 0

    yield RisingEdge(dut.clk)

    # dut._log.info(str(int(dut.src[0].value)))
    # dut._log.info(str(int(dut.src[1].value)))
    # dut._log.info(str(int(dut.src[2].value)))
    # dut._log.info(str(int(dut.src[3].value)))
    # dut._log.info(str(int(dut.src[4].value)))
    # dut._log.info(str(int(dut.src[5].value)))
    # dut._log.info(str(int(dut.src[6].value)))
    # dut._log.info(str(int(dut.src[7].value)))
    
    error=0

    
    for index in range(100):
        # yield Timer(10)
        yield RisingEdge(dut.clk)
        if(index<=10):
            # dut._log.info("This is if statement in coroutine")
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
            # dut._log.info("This is in else statement in coroutine")
            if(int(dut.A_full.value) ==0 & int(dut.A_rd_cnt.value) == 8):
                dut.A_wr_cnt <= (int(dut.A_wr_cnt.value) + 1)
            if(int(dut.B_full.value) ==0 & int(dut.B_rd_cnt.value) == 8):
                dut.B_wr_cnt <= (int(dut.B_wr_cnt.value) + 1)
            if(int(dut.C_full.value) ==0 & int(dut.C_rd_cnt.value) == 8):
                dut.C_wr_cnt <= (int(dut.C_wr_cnt.value) + 1)
            if(int(dut.D_full.value) ==0 & int(dut.D_rd_cnt.value) == 8):
                dut.D_wr_cnt <= (int(dut.D_wr_cnt.value) + 1)
            
            dut.A_valid <= (~int(dut.A_empty.value) & int(dut.A_rd.value))
            if (int(dut.A_valid.value)):
                if (int(dut.A_rd_cnt.value)<8 & dut.src[int(dut.A_rd_cnt.value)].value != int(dut.A_dout.value)):
                    error = 1
                dut.A_rd_cnt <= int(dut.A_rd_cnt.value) + 1

            dut.B_valid <= (~int(dut.B_empty.value) & int(dut.B_rd.value))
            if (int(dut.B_valid.value)):
                if (int(dut.B_rd_cnt.value)<8 & dut.src[int(dut.B_rd_cnt.value)].value != int(dut.B_dout.value)):
                    error = 1
                dut.B_rd_cnt <= int(dut.B_rd_cnt.value) + 1

            if (not int(dut.C_empty.value) & int(dut.C_rd.value)):
                if (int(dut.C_rd_cnt.value)<8 & dut.src[int(dut.C_rd_cnt.value)].value != int(dut.C_dout.value)):
                    error = 1
                dut.C_rd_cnt <= int(dut.C_rd_cnt.value) + 1

            if (not int(dut.D_empty.value) & int(dut.D_rd.value)):
                if (int(dut.D_rd_cnt.value)<8 & dut.src[int(dut.D_rd_cnt.value)].value != int(dut.D_dout.value)):
                    error = 1
                dut.D_rd_cnt <= int(dut.D_rd_cnt.value) + 1

            dut.A_rd.value <= (randint(0,2) == 0)
            dut.B_rd.value <= (randint(0,2) == 0)
            dut.C_rd.value <= (randint(0,2) == 0)
            dut.D_rd.value <= (randint(0,2) == 0)
            
            dut._log.info(str(int(dut.A_rd_cnt.value)))
            dut._log.info(str(int(dut.B_rd_cnt.value)))
            dut._log.info(str(int(dut.C_rd_cnt.value)))
            dut._log.info(str(int(dut.D_rd_cnt.value)))
            dut._log.info("------------------------------------------------------")
            
            if (int(dut.A_rd_cnt.value) >8  & int(dut.B_rd_cnt.value) > 8 & int(dut.C_rd_cnt.value) > 8 & int(dut.D_rd_cnt.value) > 8):
                dut._log.info(dut.A_rd_cnt.value)
                if (error):
                    raise TestFailure("FAIL")
>>>>>>> 15311bcaf0f8b49a069f91f5503fe2e10501211f
