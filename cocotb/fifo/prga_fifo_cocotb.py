import cocotb
from cocotb.triggers import Timer,RisingEdge,Join
from cocotb.clock import Clock
from cocotb.binary import BinaryValue
from random import randint
from cocotb.result import TestFailure

@cocotb.coroutine
def reset_signal(dut):
    dut.rst <= 1
    yield Timer(10)
    dut.rst <= 0

@cocotb.test()
def prga_fifo_test(dut):
    """Add a description line"""
    
    # Variable initialise
    A_wr_cnt=0
    B_wr_cnt=0
    C_wr_cnt=0
    D_wr_cnt=0    
    A_rd_cnt=0
    B_rd_cnt=0
    C_rd_cnt=0
    D_rd_cnt=0

    # Start Clock 
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
    
    A_wr_cnt <= 0
    B_wr_cnt <= 0
    C_wr_cnt <= 0
    D_wr_cnt <= 0
    A_rd_cnt <= 0
    B_rd_cnt <= 0
    C_rd_cnt <= 0
    D_rd_cnt <= 0
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
    
    Join(reset_signal(dut))
    
    error=0
    for _ in range(10000):
        yield Timer(20)
        yield RisingEdge(dut.clk)
        if(int(dut.rst.value) == 1):
            dut._log.info("This is if statement in coroutine")
            A_wr_cnt = 0
            B_wr_cnt = 0
            C_wr_cnt = 0
            D_wr_cnt = 0
            A_rd_cnt = 0
            B_rd_cnt = 0
            C_rd_cnt = 0
            D_rd_cnt = 0
            dut.A_valid <= 0
            dut.A_rd <= 0
            dut.B_valid <= 0
            dut.B_rd <= 0
            dut.C_rd <= 0
            dut.D_rd <= 0
        else:
            dut._log.info("This is in else statement in coroutine")

            if(int(dut.A_full.value) ==0 and int(A_rd_cnt) == 8):
                A_wr_cnt += 1
            if(int(dut.B_full.value) ==0 and int(B_rd_cnt) == 8):
                B_wr_cnt += 1
            if(int(dut.C_full.value) ==0 and int(C_rd_cnt) == 8):
                C_wr_cnt += 1
            if(int(dut.D_full.value) ==0 and int(D_rd_cnt.value) == 8):
                D_wr_cnt += 1
            
            dut.A_valid <= (not int(dut.A_empty.value) and int(dut.A_rd.value))
            if (int(dut.A_valid.value)):
                if (dut.src[int(A_rd_cnt)] != int(dut.A_dout.value)):
                    error = 1
                A_rd_cnt <= int(A_rd_cnt) + 1

            dut.B_valid <= (not int(dut.B_empty.value) and int(dut.B_rd.value))
            if (int(dut.B_valid.value)):
                if (dut.src[int(B_rd_cnt)] != int(dut.B_dout.value)):
                    error = 1
                B_rd_cnt <= int(B_rd_cnt) + 1

            if (not int(dut.C_empty.value) and int(dut.C_rd.value)):
                if (dut.src[int(C_rd_cnt)] != int(dut.C_dout.value)):
                    error = 1
                C_rd_cnt <= int(C_rd_cnt) + 1

            if (not int(dut.D_empty.value) and int(dut.D_rd.value)):
                if (dut.src[int(D_rd_cnt.value)] != int(dut.D_dout.value)):
                    error = 1
                D_rd_cnt <= int(D_rd_cnt.value) + 1

            dut.A_rd.value <= (randint(0,2) == 0)
            dut.B_rd.value <= (randint(0,2) == 0)
            dut.C_rd.value <= (randint(0,2) == 0)
            dut.D_rd.value <= (randint(0,2) == 0)
            
            if (int(A_rd_cnt) >8  and int(B_rd_cnt) > 8 and int(C_rd_cnt) > 8 and int(D_rd_cnt) > 8):
                if (error):
                    raise TestFailure("FAIL")