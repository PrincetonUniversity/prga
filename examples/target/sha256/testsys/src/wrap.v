`include "pktchain_axilite_intf.vh"
`timescale 1ns/1ps
module wrap (
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
    output wire [1:0] m_RRESP,

    // == User Backend Interface ============================================
    // user clock domain ctrl signals
    output reg [0:0] uclk,
    output wire [0:0] urst_n,

    // AXI4-Lite Interface
    output wire [0:0] u_AWVALID,
    input wire [0:0] u_AWREADY,
    output wire [`PRGA_AXI_ADDR_WIDTH - 1:0] u_AWADDR,
    output wire [2:0] u_AWPROT,

    // write data channel
    output wire [0:0] u_WVALID,
    input wire [0:0] u_WREADY,
    output wire [`PRGA_AXI_DATA_WIDTH - 1:0] u_WDATA,
    output wire [`PRGA_BYTES_PER_AXI_DATA - 1:0] u_WSTRB,

    // write response channel
    input wire [0:0] u_BVALID,
    output wire [0:0] u_BREADY,
    input wire [1:0] u_BRESP,

    // read address channel
    output wire [0:0] u_ARVALID,
    input wire [0:0] u_ARREADY,
    output wire [`PRGA_AXI_ADDR_WIDTH - 1:0] u_ARADDR,
    output wire [2:0] u_ARPROT,

    // read data channel
    input wire [0:0] u_RVALID,
    output wire [0:0] u_RREADY,
    input wire [`PRGA_AXI_DATA_WIDTH - 1:0] u_RDATA,
    input wire [1:0] u_RRESP
    );

    wire cfg_rst, cfg_e;
    wire [0:0] cfg_phit_o_full, cfg_phit_o_wr, cfg_phit_i_full, cfg_phit_i_wr;
    wire [`PRGA_PKTCHAIN_PHIT_WIDTH - 1:0] cfg_phit_o, cfg_phit_i;

    pktchain_axilite_intf i_intf ( .* );
    backbone i_backbone (.clk, .rst,
        .phit_i_full            (cfg_phit_o_full)
        ,.phit_i_wr             (cfg_phit_o_wr)
        ,.phit_i                (cfg_phit_o)
        ,.phit_o_full           (cfg_phit_i_full)
        ,.phit_o_wr             (cfg_phit_i_wr)
        ,.phit_o                (cfg_phit_i)
        );

endmodule
