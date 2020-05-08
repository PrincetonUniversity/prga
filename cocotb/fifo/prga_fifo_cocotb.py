import cocotb
from cocotb.triggers import Timer,RisingEdge
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
		if (!dut.A_full && src[dut.A_wr_cnt] != {DATA_WIDTH{random.getrandbits(1)}}):
                dut.A_wr_cnt <= dut.A_wr_cnt + 1

        if (!dut.B_full && src[dut.B_wr_cnt] != {DATA_WIDTH{random.getrandbits(1)}}):
            dut.B_wr_cnt <= dut.B_wr_cnt + 1

        if (!dut.C_full && src[dut.C_wr_cnt] != {DATA_WIDTH{random.getrandbits(1)}}):
            dut.C_wr_cnt <= dut.C_wr_cnt + 1

        if (!dut.D_full && src[dut.D_wr_cnt] != {DATA_WIDTH{random.getrandbits(1)}}):
            dut.D_wr_cnt <= dut.D_wr_cnt + 1

        dut.A_valid <= !dut.A_empty && dut.A_rd
        
        if (dut.A_valid):
            if (src[dut.A_rd_cnt] != dut.A_dout):
                error <= 1
                # $display("[ERROR] A output No. %d 0x%08x != 0x%08x", A_rd_cnt, A_dout, src[A_rd_cnt])
            dut.A_rd_cnt <= dut.A_rd_cnt + 1

        dut.B_valid <= !dut.B_empty && dut.B_rd
    
        if (dut.B_valid):
            if (src[dut.B_rd_cnt] != dut.B_dout):
                error <= 1
                # $display("[ERROR] B output No. %d 0x%08x != 0x%08x", B_rd_cnt, B_dout, src[B_rd_cnt])
            dut.B_rd_cnt <= dut.B_rd_cnt + 1

        if (!dut.C_empty && dut.C_rd):
            if (src[dut.C_rd_cnt] != dut.C_dout):
                error <= 1
                # $display("[ERROR] C output No. %d 0x%08x != 0x%08x", C_rd_cnt, C_dout, src[C_rd_cnt])
            dut.C_rd_cnt <= dut.C_rd_cnt + 1

        if (!dut.D_empty && dut.D_rd):
            if (src[dut.D_rd_cnt] != dut.D_dout):
                error <= 1
                # $display("[ERROR] D output No. %d 0x%08x != 0x%08x", D_rd_cnt, D_dout, src[D_rd_cnt])
            D_rd_cnt <= D_rd_cnt + 1

        dut.A_rd <= randint(0,2) == 0
        dut.B_rd <= randint(0,2) == 0
        dut.C_rd <= randint(0,2) == 0
        dut.D_rd <= randint(0,2) == 0

        if (src[dut.A_rd_cnt] == {DATA_WIDTH{random.getrandbits(1)}} &&
            src[dut.B_rd_cnt] == {DATA_WIDTH{random.getrandbits(1)}} &&
            src[dut.C_rd_cnt] == {DATA_WIDTH{random.getrandbits(1)}} &&
            src[dut.D_rd_cnt] == {DATA_WIDTH{random.getrandbits(1)}}):
            if (error):
                print("[FAIL]")
            else:
                print("[PASS]")

@cocotb.test()
def prga_fifo_test(dut):

	dut._log.info("Starting Test")

	# Start clock
	clock_period = 10 #This must be an even number
	test_time = 10000
	c= Clock(dut.clk,clock_period,'sec')
	cocotb.fork(c.start(test_time//clock_period))

	cocotb.fork(always_block(dut))

	# Initial block in prga_fifo_tb.v
	dut.rst <= 0
	dut.src <= [90,246,9,196,129,226,160,122]

	await Timer(3,"ns")
	dut.rst <= 1

	await Timer(10,"ns")
	dut.rst <= 0
