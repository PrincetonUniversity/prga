import cocotb
from cocotb.binary import BinaryValue
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer, ReadOnly, Join

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
async def wdata(dut, q, max_ongoing_trxs = 10, prob_trx = 1.0):
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
            addrq.pop(0)
            addr_sent += 1
        if int(dut.m_WVALID.value) and int(dut.m_WREADY.value):
            dataq.pop(0)
            data_sent += 1
        if int(dut.m_BREADY.value) and int(dut.m_BVALID.value):
            addr_sent -= 1
            data_sent -= 1

        for addr, strb, data in islice(it, 10 - max(len(addrq), len(dataq))):
            addrq.append(addr)
            dataq.append( (strb, data) )

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

def iter_bitstream(f):
    data, half = 0, False
    for l in open(f, "rb"):
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
    if half:
        yield (make_ctrl_addr(PktchainProtocol.AXILiteController.CtrlAddr.BITSTREAM_FIFO),
                0xf, data)

@cocotb.test()
async def load_bitstream(dut):
    cocotb.fork(Clock(dut.clk, 10, units="ns").start())

    dut.m_AWVALID <= 0
    dut.m_WVALID <= 0
    dut.m_BREADY <= 0
    dut.m_ARVALID <= 0
    dut.m_RREADY <= 0

    await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    dut.rst <= 1
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    dut.rst <= 0

    # cocotb.fork(wslave(dut))
    # cocotb.fork(rslave(dut))

    q = [(
        make_ctrl_addr(PktchainProtocol.AXILiteController.CtrlAddr.BITSTREAM_FIFO), 0xf, 
        make_data(PktchainProtocol.Programming.encode_msg_header(PktchainProtocol.Programming.MSGType.SOB, 0, 0, 0)),
        )]
    # dut._log.setLevel(logging.DEBUG)
    # dut._log.info("Write Q: {}".format(q))
    bs_task = cocotb.fork(wdata(dut, q, prob_trx = 0.5))
    await Join(bs_task)

    bitstream_f = os.path.join(os.path.dirname(__file__), "..", "system_pktchain_axilite_32x32N8K6",
            "sha256_axilite_slave.memh")
    bs_task = cocotb.fork(wdata(dut, iter_bitstream(bitstream_f), prob_trx = 0.8))
    await Join(bs_task)

    q = [(
        make_ctrl_addr(PktchainProtocol.AXILiteController.CtrlAddr.BITSTREAM_FIFO), 0xf, 
        make_data(PktchainProtocol.Programming.encode_msg_header(PktchainProtocol.Programming.MSGType.EOB, 0, 0, 0)),
        )]
    bs_task = cocotb.fork(wdata(dut, q, prob_trx = 0.5))
    await Join(bs_task)
