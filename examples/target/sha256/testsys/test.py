import cocotb
from cocotb.binary import BinaryValue
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer, ReadOnly, Join, with_timeout
from cocotb.result import SimTimeoutError, TestFailure

from itertools import islice

import random
import logging

import os

from prga.cfg.pktchain.protocol import PktchainProtocol

def make_ctrl_addr(addr):
    return ((PktchainProtocol.AXILiteController.CTRL_ADDR_PREFIX <<
            PktchainProtocol.AXILiteController.CTRL_ADDR_WIDTH) | addr )

def make_data(v, size = 64):
    size = size or v.bit_length()
    return BinaryValue('{{:0>{}}}'.format(size).format(bin(v).lstrip('-0b')), n_bits = size)

@cocotb.coroutine
async def cycle_count(dut, tick):
    cnt = 0
    while True:
        await RisingEdge(dut.clk)
        cnt += 1
        if cnt % tick == 0:
            dut._log.info("[CLOCK] {:0>8d} cycles passed".format(cnt))

@cocotb.coroutine
async def stream_write(dut, q, max_ongoing_trxs = 10, prob_trx = 1.0, verbose = False):
    it = iter(q)
    addrq, dataq = [], []
    addr_sent, data_sent = 0, 0

    # initialize addrq & dataq
    for addr, strb, data in islice(it, 10):
        addrq.append(addr)
        dataq.append( (strb, data) )

    while addrq or dataq or addr_sent or data_sent:
        await RisingEdge(dut.clk)
        # address channel
        if addrq and addr_sent < max_ongoing_trxs and random.random() < prob_trx:
            addr = addrq[0]
            dut.m_AWVALID <= 1
            dut.m_AWADDR <= make_data(addr, PktchainProtocol.AXILiteController.ADDR_WIDTH)
            dut.m_AWPROT <= 0
        else:
            dut.m_AWVALID <= 0
        # data channel
        if dataq and data_sent < max_ongoing_trxs and random.random() < prob_trx:
            strb, data = dataq[0]
            dut.m_WVALID <= 1
            dut.m_WSTRB <= make_data(strb, 8)
            dut.m_WDATA <= make_data(data, 64)
        else:
            dut.m_WVALID <= 0
        # response channel
        if addr_sent and data_sent and random.random() < prob_trx:
            dut.m_BREADY <= 1
        else:
            dut.m_BREADY <= 0

        await ReadOnly()
        if int(dut.m_AWVALID.value) and int(dut.m_AWREADY.value):
            if verbose:
                dut._log.info("[WRITE] Write-address 0x{:0>4x} sent".format(int(dut.m_AWADDR.value)))
            addrq.pop(0)
            addr_sent += 1
        if int(dut.m_WVALID.value) and int(dut.m_WREADY.value):
            if verbose:
                dut._log.info("[WRITE] Write-data 0x{:0>2x}, 0x{:0>16x} sent"
                        .format(int(dut.m_WSTRB.value), int(dut.m_WDATA.value)))
            dataq.pop(0)
            data_sent += 1
        if int(dut.m_BREADY.value) and int(dut.m_BVALID.value):
            if verbose:
                dut._log.info("[WRITE] Write-response received")
            addr_sent -= 1
            data_sent -= 1

        for addr, strb, data in islice(it, 10 - max(len(addrq), len(dataq))):
            addrq.append(addr)
            dataq.append( (strb, data) )

@cocotb.coroutine
async def block_read(dut, addr, verbose = False):
    while True:
        await RisingEdge(dut.clk)
        dut.m_ARVALID <= 1
        dut.m_ARADDR <= make_data(addr, PktchainProtocol.AXILiteController.ADDR_WIDTH)
        dut.m_ARPROT <= 0

        await ReadOnly()
        if int(dut.m_ARVALID.value) and int(dut.m_ARREADY.value):
            if verbose:
                dut._log.info("[READ] Read-address 0x{:0>4x} sent".format(int(dut.m_ARADDR.value)))
            break

    data = 0

    while True:
        await RisingEdge(dut.clk)
        dut.m_ARVALID <= 0
        dut.m_RREADY <= 1

        await ReadOnly()
        if int(dut.m_RREADY.value) and int(dut.m_RVALID.value):
            data = dut.m_RDATA.value.integer
            if verbose:
                dut._log.info("[READ] Read-response received: {:0>16x}".format(data))
            break

    await RisingEdge(dut.clk)
    dut.m_RREADY <= 0

    return data

@cocotb.coroutine
async def awsend(dut, addr, pipelined = False):
    while True:
        await RisingEdge(dut.clk)
        dut.m_AWVALID <= 1
        dut.m_AWADDR <= make_data(addr, PktchainProtocol.AXILiteController.ADDR_WIDTH)
        dut.m_AWPROT <= 0

        await ReadOnly()
        if int(dut.m_AWVALID.value) and int(dut.m_AWREADY.value):
            break

    if not pipelined:
        await RisingEdge(dut.clk)
        dut.m_AWVALID <= 0

@cocotb.coroutine
async def wsend(dut, strb, data, pipelined = False):
    while True:
        await RisingEdge(dut.clk)
        dut.m_WVALID <= 1
        dut.m_WSTRB <= make_data(strb, 8)
        dut.m_WDATA <= make_data(data, 64)

        await ReadOnly()
        if int(dut.m_WVALID.value) and int(dut.m_WREADY.value):
            break

    if not pipelined:
        await RisingEdge(dut.clk)
        dut.m_WVALID <= 0

@cocotb.coroutine
async def block_write(dut, addr, strb, data):
    t_awsend = cocotb.fork(awsend(dut, addr))
    t_wsend = cocotb.fork(wsend(dut, strb, data))

    Join(t_awsend)
    Join(t_wsend)

    while True:
        await RisingEdge(dut.clk)
        dut.m_BREADY <= 1

        await ReadOnly()
        if int(dut.m_BVALID.value) and int(dut.m_BREADY.value):
            break

    await RisingEdge(dut.clk)
    dut.m_BREADY <= 0

@cocotb.coroutine
async def check_ctrl_state(dut, sleep = 1000):
    while True:
        # check state first
        try:
            state = await with_timeout(block_read(dut,
                make_ctrl_addr(PktchainProtocol.AXILiteController.CtrlAddr.STATE)),
                1000, "ns")
        except SimTimeoutError:
            dut._log.error("[STATE] CtrlAddr.STATE read timeout")
            raise TestFailure

        if state == PktchainProtocol.AXILiteController.CtrlState.APP_READY:
            dut._log.info("[STATE] Application Ready!")
            return
        elif state == PktchainProtocol.AXILiteController.CtrlState.PROG_ERR:
            dut._log.error("[STATE] Proragmming unsuccessful")
            raise TestFailure
        elif state != PktchainProtocol.AXILiteController.CtrlState.PROGRAMMING:
            dut._log.error("[STATE] Controller is out of programming state")
            raise TestFailure

        # check error
        try:
            error = await with_timeout(block_read(dut,
                make_ctrl_addr(PktchainProtocol.AXILiteController.CtrlAddr.ERR_FIFO)),
                1000, "ns")
        except SimTimeoutError:
            dut._log.error("[STATE] CtrlAddr.ERROR read timeout")
            raise TestFailure

        e = PktchainProtocol.AXILiteController.decode_error(error)
        if e["type"] != PktchainProtocol.AXILiteController.Error.NONE:
            dut._log.error("[STATE] Controller error: {}".format(e))
            raise TestFailure

        # wait some cycles and check again
        dut._log.info("[STATE] Ctrl state checked. No error at the moment. Going back to sleep.")
        for i in range(sleep):
            await RisingEdge(dut.clk)

mem = {}    # this is not thread-safe

@cocotb.coroutine
async def wslave(dut, max_ongoing_trxs = 10, prob_trx = 1.0):
    addrq, dataq, resp = [], [], 0
    while True:
        await RisingEdge(dut.clk)
        if len(addrq) < max_ongoing_trxs and random.random() < prob_trx:
            dut.u_AWREADY <= 1
        else:
            dut.u_AWREADY <= 0
        if len(dataq) < max_ongoing_trxs and random.random() < prob_trx:
            dut.u_WREADY <= 1
        else:
            dut.u_WREADY <= 0
        if resp > 0:
            dut.u_BVALID <= 1
            dut.u_BRESP <= 0
        else:
            dut.u_BVALID <= 0

        await ReadOnly()
        if int(dut.u_AWREADY.value) and int(dut.u_AWVALID.value):
            addrq.append(int(dut.u_AWADDR.value))
        if int(dut.u_WREADY.value) and int(dut.u_WVALID.value):
            dataq.append( (int(dut.u_WSTRB.value), int(dut.u_WDATA.value)) )
        if int(dut.u_BVALID.value) and int(dut.u_BREADY.value):
            resp -= 1

        if len(addrq) > 0 and len(dataq) > 0 and resp < max_ongoing_trxs:
            addr = addrq.pop(0)
            strb, data = dataq.pop(0)
            for i in range(8):
                if strb & (1 << i):
                    mem[addr + i] = (data >> (i * 8)) & 0xff;
            resp += 1

@cocotb.coroutine
async def rslave(dut, max_ongoing_trxs = 10, prob_trx = 1.0):
    addrq, respq = [], []
    while True:
        await RisingEdge(dut.clk)
        if len(addrq) < max_ongoing_trxs and random.random() < prob_trx:
            dut.u_ARREADY <= 1
        else:
            dut.u_ARREADY <= 0
        if len(respq) > 0 and random.random() < prob_trx:
            dut.u_RVALID <= 1
            dut.u_RDATA <= make_data(respq[0])
            dut.u_RRESP <= 0
        else:
            dut.u_RVALID <= 0

        await ReadOnly()
        if int(dut.u_ARREADY.value) and int(dut.u_ARVALID.value):
            addrq.append(int(dut.u_ARADDR.value))
        if int(dut.u_RVALID.value) and int(dut.u_RREADY.value):
            respq.pop(0)

        if len(addrq) > 0 and len(respq) < max_ongoing_trxs:
            addr = addrq.pop(0)
            data = 0
            for i in range(8):
                data += mem.get(addr + i, 0) << (i * 8);
            respq.append(data)

@cocotb.coroutine
async def sha256_testcase(dut, blocks, expected):
    for block in blocks:
        q = [ (i * 4, 0x0f, (block >> (i * 32)) & 0xffffffff) for i in range(16) ]
        await stream_write(dut, q, prob_trx = 0.5, verbose = True)

        dut._log.info("[APP] Block written")

        while True:
            rdata = await block_read(dut, 0x64, verbose = True)
            if rdata:
                dut._log.info("[APP] Block accepted")
                break
            else:
                dut._log.info("[APP] Block not accepted yet")

    while True:
        rdata = await block_read(dut, 0x68, verbose = True)
        if rdata:
            dut._log.info("[APP] Result ready")
            break
        else:
            dut._log.info("[APP] Result not ready yet")

    digest = 0
    for i in range(8):
        digest |= ((await block_read(dut, 0x40 + (i * 4), verbose = True)) & 0xffffffff) << (i * 32);

    if digest != expected:
        dut._log.error("[APP] digest mismatch: {:0>64x} != {:0>64x}".format(digest, expected))
        raise TestFailure
    else:
        dut._log.info("[APP] digest match: {:0>64x}".format(digest))

@cocotb.coroutine
async def sha256_test(dut):
    # Update timeout
    await block_write(dut, make_ctrl_addr(PktchainProtocol.AXILiteController.CtrlAddr.UREG_TIMEOUT), 0xf, 200)

    # Set 32b mode
    await block_write(dut, make_ctrl_addr(PktchainProtocol.AXILiteController.CtrlAddr.UDATA_WIDTH), 0x1, 0x1)

    # Reset application
    await block_write(dut, make_ctrl_addr(PktchainProtocol.AXILiteController.CtrlAddr.URST), 0x1, 0x10)

    # test 0
    await sha256_testcase(dut,
            [0x61626380000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000018],
            0xBA7816BF8F01CFEA414140DE5DAE2223B00361A396177A9CB410FF61F20015AD)

    # test 1
    await sha256_testcase(dut,
            [0x6162636462636465636465666465666765666768666768696768696A68696A6B696A6B6C6A6B6C6D6B6C6D6E6C6D6E6F6D6E6F706E6F70718000000000000000,
                0x000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001C0],
            0x248D6A61D20638B8E5C026930C3E6039A33CE45964FF2167F6ECEDD419DB06C1)

    # test 2
    await sha256_testcase(dut, [
        0x6b900001496e207468652061726561206f6620496f542028496e7465726e6574206f66205468696e6773292c206d6f726520616e64206d6f7265626f6f6d2c20,
        0x697420686173206265656e206120756e6976657273616c20636f6e73656e73757320746861742064617461206973207469732061206e657720746563686e6f6c,
        0x6f6779207468617420696e746567726174657320646563656e7472616c697a6174696f6e2c496e207468652061726561206f6620496f542028496e7465726e65,
        0x74206f66205468696e6773292c206d6f726520616e64206d6f7265626f6f6d2c20697420686173206265656e206120756e6976657273616c20636f6e73656e73,
        0x757320746861742064617461206973207469732061206e657720746563686e6f6c6f6779207468617420696e746567726174657320646563656e7472616c697a,
        0x6174696f6e2c496e207468652061726561206f6620496f542028496e7465726e6574206f66205468696e6773292c206d6f726520616e64206d6f7265626f6f6d,
        0x2c20697420686173206265656e206120756e6976657273616c20636f6e73656e73757320746861742064617461206973207469732061206e657720746563686e,
        0x6f6c6f6779207468617420696e746567726174657320646563656e7472616c697a6174696f6e2c496e207468652061726561206f6620496f542028496e746572,
        0x6e6574206f66205468696e6773292c206d6f726520616e64206d6f726580000000000000000000000000000000000000000000000000000000000000000010e8,
        ],
        0x7758a30bbdfc9cd92b284b05e9be9ca3d269d3d149e7e82ab4a9ed5e81fbcf9d)

def iter_bitstream(dut, f):
    data, half = 0, False
    for lineno, l in enumerate(open(f, "rb")):
        try:
            sgmt = int(l.strip(), 16)
            if half:
                yield (make_ctrl_addr(PktchainProtocol.AXILiteController.CtrlAddr.BITSTREAM_FIFO),
                        0xff, (data << 32) | sgmt)
            else:
                data = sgmt
            half = not half
        except ValueError:
            pass
        if lineno % 1000 == 0:
            dut._log.info("[BITSTREAM] {:0>8d} dwords loaded".format(lineno))
    if half:
        yield (make_ctrl_addr(PktchainProtocol.AXILiteController.CtrlAddr.BITSTREAM_FIFO),
                0xf, data)
    dut._log.info("[BITSTREAM] Bitstream loading finished")

@cocotb.test()
async def full_system(dut):
    dut._log.setLevel(logging.DEBUG)

    cocotb.fork(Clock(dut.clk, 10, units="ns").start())

    dut.m_AWVALID <= 0
    dut.m_WVALID <= 0
    dut.m_BREADY <= 0
    dut.m_ARVALID <= 0
    dut.m_RREADY <= 0

    await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    dut.rst <= 1
    for i in range(10):
        await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    dut.rst <= 0

    cocotb.fork(cycle_count(dut, 10000))

    # cocotb.fork(wslave(dut))
    # cocotb.fork(rslave(dut))

    q = [(
        make_ctrl_addr(PktchainProtocol.AXILiteController.CtrlAddr.BITSTREAM_FIFO), 0xf, 
        make_data(PktchainProtocol.Programming.encode_msg_header(PktchainProtocol.Programming.MSGType.SOB, 0, 0, 0)),
        )]
    # dut._log.setLevel(logging.DEBUG)
    # dut._log.info("Write Q: {}".format(q))
    bs_task = cocotb.fork(stream_write(dut, q, prob_trx = 0.5))
    await Join(bs_task)

    while True:
        state = await block_read(dut, make_ctrl_addr(PktchainProtocol.AXILiteController.CtrlAddr.STATE))
        dut._log.info("[STATE] Current state: {}".format(state))
        if state == PktchainProtocol.AXILiteController.CtrlState.PROGRAMMING:
            break

    t_check_ctrl_state = cocotb.fork(check_ctrl_state(dut, 5000))

    # bitstream_f = os.path.join(os.path.dirname(__file__), "..", "system_pktchain_axilite_32x32N8K6",
    #         "sha256_axilite_slave.memh")
    bitstream_f = "sha256_axilite_slave.memh"
    bs_task = cocotb.fork(stream_write(dut, iter_bitstream(dut, bitstream_f), prob_trx = 0.8))
    await Join(bs_task)

    q = [(
        make_ctrl_addr(PktchainProtocol.AXILiteController.CtrlAddr.BITSTREAM_FIFO), 0xf, 
        make_data(PktchainProtocol.Programming.encode_msg_header(PktchainProtocol.Programming.MSGType.EOB, 0, 0, 0)),
        )]
    bs_task = cocotb.fork(stream_write(dut, q, prob_trx = 0.5))
    await Join(bs_task)

    await Join(t_check_ctrl_state)

    for i in range(10):
        await RisingEdge(dut.clk)

    await sha256_test(dut)

    dut._log.info("[INFO] All tests passed")

@cocotb.test()
async def uprot(dut):
    dut._log.setLevel(logging.DEBUG)

    cocotb.fork(Clock(dut.clk, 10, units="ns").start())

    dut.m_AWVALID <= 0
    dut.m_WVALID <= 0
    dut.m_BREADY <= 0
    dut.m_ARVALID <= 0
    dut.m_RREADY <= 0

    await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    dut.rst <= 1
    for i in range(10):
        await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    dut.rst <= 0

    cocotb.fork(cycle_count(dut, 10000))

    await sha256_test(dut)
