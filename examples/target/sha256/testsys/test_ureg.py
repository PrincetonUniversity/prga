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
async def stream(dut, q, max_ongoing_trxs = 10, prob_trx = 1.0, verbose = False):
    responses = []
    ongoing_trxs = 0

    it = iter(q)
    try:
        next_req = next(it)
    except StopIteration:
        next_req = None

    while next_req or ongoing_trxs:
        await RisingEdge(dut.clk)

        # send request
        if next_req and ongoing_trxs < max_ongoing_trxs and random.random() < prob_trx:
            addr, strb, data = next_req
            dut.reg_req_val <= 1
            dut.reg_req_addr <= addr
            dut.reg_req_strb <= strb
            dut.reg_req_data <= data
        else:
            dut.reg_req_val <= 0

        # receive response
        if ongoing_trxs and random.random() < prob_trx:
            dut.reg_resp_rdy <= 1
        else:
            dut.reg_resp_rdy <= 0

        await ReadOnly()

        # check if request is sent
        if int(dut.reg_req_val.value) and int(dut.reg_req_rdy.value):
            if verbose:
                dut._log.info("[STREAM] Request sent: addr = 0x{:0>4x}, strb = 0x{:0>2x}"
                        .format(int(dut.reg_req_addr.value), int(dut.reg_req_strb.value)))
            ongoing_trxs += 1
            try:
                next_req = next(it)
            except StopIteration:
                next_req = None

        # check if response is received
        if int(dut.reg_resp_val.value) and int(dut.reg_resp_rdy.value):
            if verbose:
                dut._log.info("[STREAM] Response received")
            responses.append( int(dut.reg_resp_data.value) )
            ongoing_trxs -= 1

    await RisingEdge(dut.clk)
    dut.reg_req_val <= 0
    dut.reg_resp_rdy <= 0

    return responses

@cocotb.coroutine
async def block_read(dut, addr, verbose = False):
    while True:
        await RisingEdge(dut.clk)
        dut.reg_resp_rdy <= 0
        dut.reg_req_val <= 1
        dut.reg_req_addr <= addr
        dut.reg_req_strb <= 0

        await ReadOnly()
        if int(dut.reg_req_val.value) and int(dut.reg_req_rdy.value):
            if verbose:
                dut._log.info("[BLOCK READ] Request sent: addr = 0x{:0>4x}"
                        .format(int(dut.reg_req_addr.value)))
            break

    data = 0

    while True:
        await RisingEdge(dut.clk)
        dut.reg_req_val <= 0
        dut.reg_resp_rdy <= 1

        await ReadOnly()
        if int(dut.reg_resp_rdy.value) and int(dut.reg_resp_val.value):
            data = int(dut.reg_resp_data.value)
            if verbose:
                dut._log.info("[BLOCK READ] Response received: data = 0x{:0>16x}".format(data))
            break
    
    await RisingEdge(dut.clk)
    dut.reg_req_val <= 0
    dut.reg_resp_rdy <= 0

    return data

@cocotb.coroutine
async def block_write(dut, addr, strb, data, verbose = False):
    while True:
        await RisingEdge(dut.clk)
        dut.reg_req_val <= 1
        dut.reg_resp_rdy <= 0
        dut.reg_req_addr <= addr
        dut.reg_req_strb <= strb
        dut.reg_req_data <= data

        await ReadOnly()
        if int(dut.reg_req_val.value) and int(dut.reg_req_rdy.value):
            if verbose:
                dut._log.info("[BLOCK WRITE] Request sent: addr = 0x{:0>4x}, strb = 0x{:0>2x}"
                        .format(int(dut.reg_req_addr.value), int(dut.reg_req_strb.value)))
            break

    data = 0

    while True:
        await RisingEdge(dut.clk)
        dut.reg_req_val <= 0
        dut.reg_resp_rdy <= 1

        await ReadOnly()
        if int(dut.reg_resp_rdy.value) and int(dut.reg_resp_val.value):
            if verbose:
                dut._log.info("[BLOCK WRITE] Response received")
            break
    
    await RisingEdge(dut.clk)
    dut.reg_req_val <= 0
    dut.reg_resp_rdy <= 0

@cocotb.coroutine
async def check_ctrl_state(dut, sleep = 1000):
    while True:
        # check state first
        try:
            state = await with_timeout(block_read(dut, 0x818), 1000, "ns")
        except SimTimeoutError:
            dut._log.error("[STATE] CFG_STATUS read timeout")
            raise TestFailure

        if state == 2:
            dut._log.info("[STATE] Application Ready!")
            return
        elif state == 3:
            dut._log.error("[STATE] Proragmming unsuccessful")
            raise TestFailure
        elif state != 1:
            dut._log.error("[STATE] Controller is out of programming state")
            raise TestFailure

        # check error
        try:
            error = await with_timeout(block_read(dut, 0x808), 1000, "ns")
        except SimTimeoutError:
            dut._log.error("[STATE] EFLAGS read timeout")
            raise TestFailure

        if error:
            dut._log.error("[STATE] Non-zero EFLAGS: 0x{:0>16x}".format(error))
            raise TestFailure

        # wait some cycles and check again
        dut._log.info("[STATE] Ctrl state checked. No error at the moment. Going back to sleep.")
        for i in range(sleep):
            await RisingEdge(dut.clk)

@cocotb.coroutine
async def sha256_testcase(dut, blocks, expected):
    for block in blocks:
        q = [ (i * 8, 0xff, make_data((block >> (i * 64)) & ((1 << 64) - 1)) ) for i in range(8) ]
        await stream(dut, q, prob_trx = 0.5, verbose = True)

        dut._log.info("[APP] Block written")

        while True:
            rdata = await block_read(dut, 0x68, verbose = True)
            if rdata:
                dut._log.info("[APP] Block accepted")
                break
            else:
                dut._log.info("[APP] Block not accepted yet")

    while True:
        rdata = await block_read(dut, 0x70, verbose = True)
        if rdata:
            dut._log.info("[APP] Result ready")
            break
        else:
            dut._log.info("[APP] Result not ready yet")

    digest = 0
    for i in range(4):
        digest |= (await block_read(dut, 0x40 + (i * 8), verbose = True)) << (i * 64);

    if digest != expected:
        dut._log.error("[APP] digest mismatch: {:0>64x} != {:0>64x}".format(digest, expected))
        raise TestFailure
    else:
        dut._log.info("[APP] digest match: {:0>64x}".format(digest))

@cocotb.coroutine
async def sha256_test(dut):
    # Enable UREG interface
    await block_write(dut, 0x820, 0xff, 0x1)

    # Update timeout
    await block_write(dut, 0xC08, 0xff, 200)

    # Reset application
    await block_write(dut, 0xC00, 0xff, 200)

    # # wait 1000 cycles
    # for i in range(1000):
    #     await RisingEdge(dut.clk)

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
                yield (0x900, 0xff, (data << 32) | sgmt)
            else:
                data = sgmt
            half = not half
        except ValueError:
            pass
        if lineno % 1000 == 0:
            dut._log.info("[BITSTREAM] {:0>8d} dwords loaded".format(lineno))
    if half:
        yield (0x900, 0xf, data)
    dut._log.info("[BITSTREAM] Bitstream loading finished")

@cocotb.test()
async def full_system(dut):
    dut._log.setLevel(logging.DEBUG)

    cocotb.fork(Clock(dut.clk, 10, units="ns").start())

    dut.reg_req_val <= 0
    dut.reg_req_addr <= 0
    dut.reg_req_strb <= 0
    dut.reg_req_data <= make_data(0, 64)
    dut.ccm_req_rdy <= 0
    dut.ccm_resp_val <= 0
    dut.rst_n <= 1

    await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    dut.rst_n <= 0
    for i in range(10):
        await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    dut.rst_n <= 1

    cocotb.fork(cycle_count(dut, 10000))

    q = [(
        0x900, 0xf, 
        make_data(PktchainProtocol.Programming.encode_msg_header(PktchainProtocol.Programming.MSGType.SOB, 0, 0, 0)),
        )]
    bs_task = cocotb.fork(stream(dut, q, prob_trx = 0.5))
    await Join(bs_task)

    while True:
        state = await block_read(dut, 0x818)
        dut._log.info("[STATE] Current state: {}".format(state))
        if state == 1:
            break

    bitstream_f = "sha256_ureg.memh"
    bs_task = cocotb.fork(stream(dut, iter_bitstream(dut, bitstream_f), prob_trx = 0.8))
    await Join(bs_task)

    q = [(
        0x900, 0xf, 
        make_data(PktchainProtocol.Programming.encode_msg_header(PktchainProtocol.Programming.MSGType.EOB, 0, 0, 0)),
        )]
    bs_task = cocotb.fork(stream(dut, q, prob_trx = 0.5))
    await Join(bs_task)

    await Join(cocotb.fork(check_ctrl_state(dut, 5000)))

    for i in range(10):
        await RisingEdge(dut.clk)

    await sha256_test(dut)

    dut._log.info("[INFO] All tests passed")

@cocotb.test()
async def uprot(dut):
    dut._log.setLevel(logging.DEBUG)

    cocotb.fork(Clock(dut.clk, 10, units="ns").start())

    dut.reg_req_val <= 0
    dut.reg_req_addr <= 0
    dut.reg_req_strb <= 0
    dut.reg_req_data <= make_data(0, 64)
    dut.rst_n <= 1

    await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    dut.rst_n <= 0
    for i in range(10):
        await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    dut.rst_n <= 1

    cocotb.fork(cycle_count(dut, 10000))

    await sha256_test(dut)
