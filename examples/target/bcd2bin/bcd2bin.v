module mux8to1(out,sel,data_in);
output out;     
input[7:0] data_in;
input[3:0] sel;
reg out;
always @(data_in or sel)
case(sel)
3'b000 :out<=data_in[0];
3'b001 :out<=data_in[1];
3'b010 :out<=data_in[2];
3'b011 :out<=data_in[3];
3'b100 :out<=data_in[4];
3'b101 :out<=data_in[5];
3'b110 :out<=data_in[6];
3'b111 :out<=data_in[7];

endcase

endmodule


module bcd2bin (
    input wire clk,
    input wire reset,
    input wire start,
    input wire [3:0] bcd1,
    input wire [3:0] bcd0,
    input [7:0] a,
    input [3:0] b,
    output c,
    output reg ready,
    output reg done_tick,
    output wire [6:0] bin
    );

    // symbolic state declaration
    localparam [1:0] idle = 2'b00,
                     op   = 2'b01,
                     done = 2'b10;

    // signal declaration
    reg [1:0] state_reg, state_next;
    reg [6:0] bin_reg, bin_next;
    reg [3:0] n_reg, n_next;
    reg [3:0] bcd1_reg, bcd0_reg;
    reg [3:0] bcd1_next, bcd0_next;

    // FSMD state & data registers
    always @(posedge clk)
        if (reset)
        begin
            state_reg <= idle;
            bin_reg <= 0;
            n_reg <= 0;
            bcd1_reg <= 0;
            bcd0_reg <= 0;
        end else begin
            state_reg <= state_next;
            bin_reg <= bin_next;
            n_reg <= n_next;
            bcd1_reg <= bcd1_next;
            bcd0_reg <= bcd0_next;
        end

    // FSMD next-state logic
    always @*
    begin
        // defaults
        state_next = state_reg;
        ready = 1'b0;
        done_tick = 1'b0;
        bin_next = bin_reg;
        bcd0_next = bcd0;   // route in bcd1 input
        bcd1_next = bcd1;   // route in bcd0 input
        n_next = n_reg;

        case (state_reg)
            idle: begin
                ready = 1'b1;
                if (start) begin
                    state_next = op;
                    n_next = 4'b0111; // iterate 7 times
                end
            end
            op: begin
                bin_next = {bcd0_reg[0], bin_reg[6:1]}; // right shift in lowest bit from bcd0_reg
                bcd1_next = {1'b0, bcd1_reg[3:1]}; // right shift in 0 to bcd1
                // right shift in bcd1[0] into bcd0, if bcd0 > 4, subtract 3
                bcd0_next = ({bcd1_reg[0], bcd0_reg[3:1]} > 4) ? ({bcd1_reg[0], bcd0_reg[3:1]} - 4'b0011) : {bcd1_reg[0], bcd0_reg[3:1]};   

                n_next = n_reg - 1; // decrement n
                if (n_next==0)
                    state_next = done; 
            end
            done: begin
                done_tick = 1'b1;   
                state_next = idle;  
            end
            default:
                state_next = idle;
        endcase
    end  

    // assign output
    assign bin = bin_reg;
    mux8to1 U1(.out(c),.data_in(a),.sel(b));
endmodule
