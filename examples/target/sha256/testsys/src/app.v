`timescale 1ns/1ps
module app (
    input wire [0:0] clk,
    input wire [0:0] rst_n,
    output wire [0:0] reg_req_rdy,
    input wire [0:0] reg_req_val,
    input wire [11:0] reg_req_addr,
    input wire [7:0] reg_req_strb,
    input wire [63:0] reg_req_data,
    input wire [0:0] reg_resp_rdy,
    output wire [0:0] reg_resp_val,
    output wire [63:0] reg_resp_data,
    output wire [0:0] sax_rdy,
    input wire [0:0] sax_val,
    input wire [143:0] sax_data,
    input wire [0:0] asx_rdy,
    output wire [0:0] asx_val,
    output wire [127:0] asx_data
    );

    wire aclk, arst_n;
    wire ureg_req_rdy, ureg_req_val, ureg_resp_rdy, ureg_resp_val;
    wire [11:0] ureg_req_addr;
    wire [7:0] ureg_req_strb;
    wire [63:0] ureg_req_data;
    wire [0:0] ureg_resp_ecc;
    wire [63:0] ureg_resp_data;

    prga_sysintf i_sysintf (
        .clk(clk),
        .rst_n(rst_n),
        .aclk(aclk),
        .arst_n(arst_n),
        .reg_req_rdy(reg_req_rdy),
        .reg_req_val(reg_req_val),
        .reg_req_addr(reg_req_addr),
        .reg_req_strb(reg_req_strb),
        .reg_req_data(reg_req_data),
        .reg_resp_rdy(reg_resp_rdy),
        .reg_resp_val(reg_resp_val),
        .reg_resp_data(reg_resp_data),
        .ureg_req_rdy(ureg_req_rdy),
        .ureg_req_val(ureg_req_val),
        .ureg_req_addr(ureg_req_addr),
        .ureg_req_strb(ureg_req_strb),
        .ureg_req_data(ureg_req_data),
        .ureg_resp_rdy(ureg_resp_rdy),
        .ureg_resp_val(ureg_resp_val),
        .ureg_resp_ecc(ureg_resp_ecc),
        .ureg_resp_data(ureg_resp_data),
        .cfg_status(2'h2),
        .cfg_req_rdy(1'b0),
        .cfg_resp_val(1'b0),
        .cfg_resp_err(1'b0),
        .cfg_resp_data(64'h0),
        .sax_rdy(sax_rdy),
        .sax_val(sax_val),
        .sax_data(sax_data),
        .asx_rdy(asx_rdy),
        .asx_val(asx_val),
        .asx_data(asx_data),
        .ccm_req_val(1'b0),
        .ccm_req_type(2'h0),
        .ccm_req_addr(40'h0),
        .ccm_req_data(64'h0),
        .ccm_req_size(3'h0),
        .ccm_req_ecc(1'b0),
        .ccm_resp_rdy(1'b0)
        );
    sha256_ureg i_app (
        .clk                (aclk)
        ,.rst_n             (arst_n)

        ,.ureg_req_rdy      (ureg_req_rdy)
        ,.ureg_req_val      (ureg_req_val)
        ,.ureg_req_addr     (ureg_req_addr)
        ,.ureg_req_strb     (ureg_req_strb)
        ,.ureg_req_data     (ureg_req_data)

        ,.ureg_resp_rdy     (ureg_resp_rdy)
        ,.ureg_resp_val     (ureg_resp_val)
        ,.ureg_resp_data    (ureg_resp_data)
        ,.ureg_resp_ecc     (ureg_resp_ecc)
        );

endmodule

