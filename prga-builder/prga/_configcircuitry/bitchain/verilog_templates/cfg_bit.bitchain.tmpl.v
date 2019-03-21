module cfg_bit(
    input  wire [0:0] cfg_clk,
    input  wire [0:0] cfg_e,
    input  wire [0:0] i,
    output reg  [0:0] o
    );

    always @(posedge cfg_clk) begin
        if (cfg_e) begin
            o   <=  i;
        end
    end

endmodule
