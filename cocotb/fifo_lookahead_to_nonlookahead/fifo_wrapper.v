 module fifo_wrapper (
    input clk,
    input rst,
    output full,
    input  wr,
    input [DATA_WIDTH - 1:0] din,
    output empty,
    input rd,
    output [DATA_WIDTH - 1:0] dout,
     output [DATA_WIDTH - 1:0] _dout,
     output _empty, _rd
);

    localparam DATA_WIDTH = 32;


//    wire [DATA_WIDTH - 1:0] _dout;

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
