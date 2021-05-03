module romtest_test (
    input wire tb_clk,
    input wire tb_rst,
    output reg tb_pass,
    output reg tb_fail,
    input wire tb_prog_done,
    input wire [31:0] tb_verbosity,
    input wire [31:0] tb_cycle_cnt,

    output wire clk,
    output reg [7:0] addr,
    input wire [7:0] dout
    );

    assign clk = tb_clk;

    reg tb_prog_done_f;
    reg [7:0] addr_f;
    reg [7:0] rom [0:255];

    initial begin
        addr = 8'h0;
        tb_prog_done_f = 1'b0;
        tb_pass = 1'b0;
        tb_fail = 1'b0;

        `include "rom.vh"
    end

    always @(posedge tb_clk) begin
        if (tb_rst) begin
            addr <= 8'h0;
            tb_prog_done_f <= 1'b0;
        end else if (tb_prog_done) begin
            addr <= addr + 1;
            tb_prog_done_f <= 1'b1;
        end
    end

    always @(posedge tb_clk) begin
        addr_f <= addr;
    end

    always @(posedge tb_clk) begin
        #0;

        if (tb_prog_done_f) begin
            if (dout == rom[addr_f]) begin
                $display("[Cycle %05d] rom[%03d] => 0x%02x",
                    tb_cycle_cnt, addr_f, dout);

                if (&addr_f) begin
                    tb_pass <= 1'b1;
                end
            end else begin
                $display("[Cycle %05d] rom[%03d] => 0x%02x != 0x%02x (expected), fail",
                    tb_cycle_cnt, addr_f, dout, rom[addr_f]);
                tb_fail <= 1'b1;
            end
        end
    end

endmodule
