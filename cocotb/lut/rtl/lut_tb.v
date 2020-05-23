module lut_tb();
    reg [3:0] in,
    wire [0:0] out,
    reg [0:0] cfg_clk,
    reg [0:0] cfg_e,
    reg [0:0] cfg_we,
    reg [0:0] cfg_i,
    wire [0:0] cfg_o

    lut4 uut(
        .in(in),
        .out(out),
        .cfg_clk(cfg_clk),
        .cfg_e(cfg_e),
        .cfg_we(cfg_we),
        .cfg_o(cfg_o),
        .cfg_i(cfg_i)
    );
    initial begin
      cfg_e <= 1;
      cfg_we <= 1;
      in = 0;
      cfg_i <= 0
      #10
      cfg_i <= 1 
      #10
      cfg_i <= 0 
      #10
      cfg_i <= 1 
      #10
      cfg_i <= 0 
      #10
      cfg_i <= 0 
      #10
      cfg_i <= 0
      #10
      cfg_i <= 1 
      #10
      cfg_i <= 1 
      #10
      cfg_i <= 1 
      #10
      cfg_i <= 0
      #10
      cfg_i <= 0 
      #10
      cfg_i <= 1 
      #10
      cfg_i <= 0 
      #10
      cfg_i <= 1 
      #10
      cfg_i <= 0 
      #10

      cfg_e <= 0;
      cfg_we <= 0; 
    end
    always@(posedge clk) begin
      in <= in+1;
    end

    always #5 cfg_clk=~cfg_clk;

endmodule