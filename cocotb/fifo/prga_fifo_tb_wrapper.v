module prga_fifo_tb_wrapper ();

    localparam DATA_WIDTH = 8;
    localparam BUS_WIDTH = 8;
    input wire clk, rst;

<<<<<<< HEAD
    input clk, rst;

    input [DATA_WIDTH - 1:0] src [0:1023];

    // initial begin
      
    //     src[0] = 'h5A;
    //     src[1] = 'hF6;
    //     src[2] = 'h09;
    //     src[3] = 'hC4;
    //     src[4] = 'h81;
    //     src[5] = 'hE2;
    //     src[6] = 'hA0;
    //     src[7] = 'h7A;
    // end

=======
    input wire [DATA_WIDTH - 1:0] src [0:1023];
  
>>>>>>> 15311bcaf0f8b49a069f91f5503fe2e10501211f
    // A: non-lookahead
    // B: lookahead converted to non-lookahead
    // C: lookahead
    // D: non-lookahead converted to lookahead

    output wire A_full, A_empty, B_full, B_empty, C_full, C_empty, D_full, D_empty;
    output wire [DATA_WIDTH - 1:0] A_dout, B_dout, C_dout, D_dout;
    input wire A_valid, A_rd, B_valid, B_rd, C_rd, D_rd;
    input wire [0:BUS_WIDTH-1] A_wr_cnt, B_wr_cnt, C_wr_cnt, D_wr_cnt;
    input wire [0:BUS_WIDTH-1] A_rd_cnt, B_rd_cnt, C_rd_cnt, D_rd_cnt;
    output wire _B_empty, _B_rd, _D_empty, _D_rd;
    output wire [DATA_WIDTH - 1:0] _B_dout, _D_dout;

    initial begin
        $dumpfile("test.vcd");
        $dumpvars(1,prga_fifo_tb_wrapper);
    end

    reg r_rst;
    always @(*) r_rst =rst;
    
    prga_fifo #(
        .DATA_WIDTH                     (DATA_WIDTH)
        ,.LOOKAHEAD                     (0)
    ) A (
        .clk        (clk)
        ,.rst       (r_rst)
        ,.full      (A_full)
        ,.wr        (src[A_wr_cnt] !== {DATA_WIDTH{1'bx}})
        ,.din       (src[A_wr_cnt])
        ,.empty     (A_empty)
        ,.rd        (A_rd)
        ,.dout      (A_dout)
        );

    prga_fifo #(
        .DATA_WIDTH                     (DATA_WIDTH)
        ,.LOOKAHEAD                     (1)
    ) B (
        .clk        (clk)
        ,.rst       (r_rst)
        ,.full      (B_full)
        ,.wr        (src[B_wr_cnt] !== {DATA_WIDTH{1'bx}})
        ,.din       (src[B_wr_cnt])
        ,.empty     (_B_empty)
        ,.rd        (_B_rd)
        ,.dout      (_B_dout)
        );

    prga_fifo_lookahead_buffer #(
        .DATA_WIDTH                     (DATA_WIDTH)
        ,.REVERSED                      (1)
    ) B_buffer (
        .clk        (clk)
        ,.rst       (r_rst)
        ,.empty_i   (_B_empty)
        ,.rd_i      (_B_rd)
        ,.dout_i    (_B_dout)
        ,.empty     (B_empty)
        ,.rd        (B_rd)
        ,.dout      (B_dout)
        );

    prga_fifo #(
        .DATA_WIDTH                     (DATA_WIDTH)
        ,.LOOKAHEAD                     (1)
    ) C (
        .clk        (clk)
        ,.rst       (r_rst)
        ,.full      (C_full)
        ,.wr        (src[C_wr_cnt] !== {DATA_WIDTH{1'bx}})
        ,.din       (src[C_wr_cnt])
        ,.empty     (C_empty)
        ,.rd        (C_rd)
        ,.dout      (C_dout)
        );

    prga_fifo #(
        .DATA_WIDTH                     (DATA_WIDTH)
        ,.LOOKAHEAD                     (0)
    ) D (
        .clk        (clk)
        ,.rst       (r_rst)
        ,.full      (D_full)
        ,.wr        (src[D_wr_cnt] !== {DATA_WIDTH{1'bx}})
        ,.din       (src[D_wr_cnt])
        ,.empty     (_D_empty)
        ,.rd        (_D_rd)
        ,.dout      (_D_dout)
        );

    prga_fifo_lookahead_buffer #(
        .DATA_WIDTH                     (DATA_WIDTH)
        ,.REVERSED                      (0)
    ) D_buffer (
        .clk        (clk)
        ,.rst       (r_rst)
        ,.empty_i   (_D_empty)
        ,.rd_i      (_D_rd)
        ,.dout_i    (_D_dout)
        ,.empty     (D_empty)
        ,.rd        (D_rd)
        ,.dout      (D_dout)
        );

endmodule