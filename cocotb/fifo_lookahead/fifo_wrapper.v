module fifo_wrapper (
	input wire clk, rst,
    output wire C_full, C_empty,
    output wire [DATA_WIDTH - 1:0] C_dout,
    input wire C_rd,

        );

    localparam DATA_WIDTH = 8;
    localparam BUS_WIDTH = 8;
    
	
	wire [DATA_WIDTH - 1:0] src [0:1023];
    wire [0:BUS_WIDTH-1] C_wr_cnt,
    wire [0:BUS_WIDTH-1] C_rd_cnt  
    // C: lookahead



    initial begin
        $dumpfile("test.vcd");
        $dumpvars(1,prga_fifo_tb_wrapper);
    end

    reg r_rst;
    always @(*) r_rst =rst;
    
    fifo #(
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

endmodule
