import cocotb
from cocotb.triggers import Timer
from cocotb.clock import Clock
from random import randint

@cocotb.coroutine()
def always_block(dut):
	await RisingEdge(dut.clk)
	error <= 0
	if(dut.rst):
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
		if(dut.A_full.value==0 and dut.A_rd_cnt == len(src)):
			dut.A_wr_cnt <= (int(dut.A_wr_cnt.value) + 1)

		if (!dut.B_full.value and dut.B_rd_cnt == len(src)):
			dut.B_wr_cnt <= dut.B_wr_cnt + 1
		
		if (!dut.C_full.value and dut.C_rd_cnt == len(src)):
			dut.C_wr_cnt <= dut.C_wr_cnt + 1

		if (!dut.D_full.value and dut.D_rd_cnt == len(src)):
			dut.D_wr_cnt <= dut.D_wr_cnt + 1

		dut.A_valid <= !dut.A_empty and dut.A_rd

		if (dut.A_valid.value):
			if (src[dut.A_rd_cnt] != dut.A_dout):
				error <= 1
				# $display("[ERROR] A output No. %d 0x%08x != 0x%08x", A_rd_cnt, A_dout, src[A_rd_cnt])
			dut.A_rd_cnt <= dut.A_rd_cnt + 1

		dut.B_valid <= !dut.B_empty and dut.B_rd

		if (dut.B_valid.value):
			if (src[dut.B_rd_cnt] != dut.B_dout):
				error <= 1
				# $display("[ERROR] B output No. %d 0x%08x != 0x%08x", B_rd_cnt, B_dout, src[B_rd_cnt])
			dut.B_rd_cnt <= dut.B_rd_cnt + 1

		if (!dut.C_empty.value and dut.C_rd):
			if (src[dut.C_rd_cnt] != dut.C_dout):
				error <= 1
				# $display("[ERROR] C output No. %d 0x%08x != 0x%08x", C_rd_cnt, C_dout, src[C_rd_cnt])
			dut.C_rd_cnt <= dut.C_rd_cnt + 1

		if (!dut.D_empty.value and dut.D_rd):
			if (src[dut.D_rd_cnt] != dut.D_dout):
				error <= 1
				# $display("[ERROR] D output No. %d 0x%08x != 0x%08x", D_rd_cnt, D_dout, src[D_rd_cnt])
			D_rd_cnt <= D_rd_cnt + 1

		dut.A_rd <= randint(0,2) == 0
		dut.B_rd <= randint(0,2) == 0
		dut.C_rd <= randint(0,2) == 0
		dut.D_rd <= randint(0,2) == 0

		if (dut.A_rd_cnt == len(src) and
			dut.B_rd_cnt == len(src) and
			dut.C_rd_cnt == len(src) and
			dut.D_rd_cnt == len(src))
			if (error):
				print("[FAIL]")
			else:
				print("[PASS]")

async def reset_signal(dut):
	dut.rst <= 0
	await Timer(3,"ns")
	dut.rst <= 1
	await Timer(10,"ns")
	dut.rst <= 0

@cocotb.test()
def prga_fifo_test(dut):

	dut._log.info("Starting Test")

	# Start clock
	clock_period = 10 #This must be an even number
	test_time = 10000
	c= Clock(dut.clk,clock_period,units='ns')
	cocotb.fork(c.start(test_time//clock_period))

	cocotb.fork(always_block(dut))

	# Initial block in prga_fifo_tb.v
	dut.src <= [90,246,9,196,129,226,160,122]
	cocotb.fork(reset_signal(dut))