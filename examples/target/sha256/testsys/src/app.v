`include "pktchain_axilite_intf.vh"
`timescale 1ns/1ps
module app (
    // system ctrl signals
    input wire [0:0] clk,
    input wire [0:0] rst,

    // == AXI4-Lite Interface ================================================
    // write address channel
    input wire [0:0] m_AWVALID,
    output wire [0:0] m_AWREADY,
    input wire [`PRGA_AXI_ADDR_WIDTH - 1:0] m_AWADDR,
    input wire [2:0] m_AWPROT,

    // write data channel
    input wire [0:0] m_WVALID,
    output wire [0:0] m_WREADY,
    input wire [`PRGA_AXI_DATA_WIDTH - 1:0] m_WDATA,
    input wire [`PRGA_BYTES_PER_AXI_DATA - 1:0] m_WSTRB,

    // write response channel
    output wire [0:0] m_BVALID,
    input wire [0:0] m_BREADY,
    output wire [1:0] m_BRESP,

    // read address channel
    input wire [0:0] m_ARVALID,
    output wire [0:0] m_ARREADY,
    input wire [`PRGA_AXI_ADDR_WIDTH - 1:0] m_ARADDR,
    input wire [2:0] m_ARPROT,

    // read data channel
    output wire [0:0] m_RVALID,
    input wire [0:0] m_RREADY,
    output wire [`PRGA_AXI_DATA_WIDTH - 1:0] m_RDATA,
    output wire [1:0] m_RRESP
    );

    wire cfg_rst, cfg_e, uclk, urst_n;
    wire [0:0] cfg_phit_o_full, cfg_phit_o_wr, cfg_phit_i_full, cfg_phit_i_wr;
    wire [`PRGA_PKTCHAIN_PHIT_WIDTH - 1:0] cfg_phit_o, cfg_phit_i;

    wire [0:0] u_AWVALID;
    wire [0:0] u_AWREADY;
    wire [`PRGA_AXI_ADDR_WIDTH - 1:0] u_AWADDR;
    wire [2:0] u_AWPROT;

    // write data channel
    wire [0:0] u_WVALID;
    wire [0:0] u_WREADY;
    wire [`PRGA_AXI_DATA_WIDTH - 1:0] u_WDATA;
    wire [`PRGA_BYTES_PER_AXI_DATA - 1:0] u_WSTRB;

    // write response channel
    wire [0:0] u_BVALID;
    wire [0:0] u_BREADY;
    wire [1:0] u_BRESP;

    // read address channel
    wire [0:0] u_ARVALID;
    wire [0:0] u_ARREADY;
    wire [`PRGA_AXI_ADDR_WIDTH - 1:0] u_ARADDR;
    wire [2:0] u_ARPROT;

    // read data channel
    wire [0:0] u_RVALID;
    wire [0:0] u_RREADY;
    wire [`PRGA_AXI_DATA_WIDTH - 1:0] u_RDATA;
    wire [1:0] u_RRESP;

    pktchain_axilite_intf i_intf ( .* );
    sha256_axilite_slave i_slave (
        .ACLK               (uclk)
        ,.ARESETn           (urst_n)
		,.AWVALID			(u_AWVALID)
		,.AWREADY			(u_AWREADY)
		,.AWADDR			(u_AWADDR)
		,.AWPROT			(u_AWPROT)

		,.WVALID			(u_WVALID)
		,.WREADY			(u_WREADY)
		,.WSTRB			    (u_WSTRB)
		,.WDATA			    (u_WDATA)

		,.BREADY			(u_BREADY)
		,.BVALID			(u_BVALID)
		,.BRESP			    (u_BRESP)

		,.ARVALID			(u_ARVALID)
		,.ARREADY			(u_ARREADY)
		,.ARADDR			(u_ARADDR)
		,.ARPROT			(u_ARPROT)

		,.RREADY			(u_RREADY)
		,.RVALID			(u_RVALID)
		,.RDATA			    (u_RDATA)
		,.RRESP			    (u_RRESP)
        );

endmodule

