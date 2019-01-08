module gate (
    input wire clk,
    input wire reset,
    input wire a,
    input wire b,
    output wire c
    );

    assign c = a ^ b;

endmodule
