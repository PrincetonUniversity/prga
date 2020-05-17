 module fifo_wrapper ();

    localparam DATA_WIDTH = 8;

    input wire [0:0] clk;
    input  [0:0] rst;

    output wire [0:0] full;
    input wire [0:0] wr;
    input wire [DATA_WIDTH - 1:0] din;

    output wire [0:0] empty;
    input wire [0:0] rd;
    output wire [DATA_WIDTH - 1:0] dout;

    wire _empty, _rd;
    wire [DATA_WIDTH - 1:0] _dout;

    // initial begin
    //     $dumpfile("dump.vcd");
    //     $dumpvars(1,fifo_tb);
    // end

    fifo #(
        .DATA_WIDTH                     (DATA_WIDTH)
        ,.LOOKAHEAD                     (1)
    ) B (
        .clk        (clk)
        ,.rst       (rst)
        ,.full      (full)
        ,.wr        (wr)
        ,.din       (din)
        ,.empty     (_empty)
        ,.rd        (_rd)
        ,.dout      (_dout)
        );

    fifo_lookahead_buffer #(
        .DATA_WIDTH                     (DATA_WIDTH)
        ,.REVERSED                      (1)
    ) Buffer (
        .clk        (clk)
        ,.rst       (rst)
        ,.empty_i   (_empty)
        ,.rd_i      (_rd)
        ,.dout_i    (_dout)
        ,.empty     (empty)
        ,.rd        (rd)
        ,.dout      (dout)
        );

endmodule
