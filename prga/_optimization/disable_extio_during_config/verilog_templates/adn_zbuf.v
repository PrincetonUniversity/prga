module adn_zbuf (
    input wire [0:0] i,
    output reg [0:0] o,
    input wire [0:0] cfg_e
    );

    always @* begin
        if (~cfg_e)
            o   =   i;
        else
            o   =   1'b0;
    end

endmodule
