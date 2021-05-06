module dffn (
    input wire  clk,
    input wire  D,
    output reg  Q
    );

    always @(negedge clk)
        Q <= D;

endmodule
