module romtest (
    input wire          clk,
    input wire [7:0]    addr,
    output reg [7:0]    dout
    );

    reg [7:0] rom [0:255];

    initial begin
        `include "rom.vh"
    end

    always @(posedge clk) begin
        dout <= rom[addr];
    end

endmodule
