module bcd2bin_host (
    input wire sys_clk,
    input wire sys_rst,
    output reg sys_success,
    output reg sys_fail,
    input wire [31:0] cycle_count,

    output wire clk,
    output wire reset,
    output reg start,
    output reg [3:0] bcd0,
    output reg [3:0] bcd1,
    input wire ready,
    input wire done_tick,
    input wire [6:0] bin
    );

    assign clk = sys_clk;
    assign reset = sys_rst;
    
    reg [3:0] test_counter;
    reg [7:0] source [0:15];
    reg [6:0] sink [0:15];

    // set up test source & sink
    initial begin
        source[0] = {4'd0, 4'd0}; sink[0] = 7'h00;
        source[1] = {4'd9, 4'd9}; sink[1] = 7'h63;
        source[2] = {4'd5, 4'd5}; sink[2] = 7'h37;
        source[3] = {4'd0, 4'd9}; sink[3] = 7'h09;
        source[4] = {4'd9, 4'd0}; sink[4] = 7'h5a;
    end

    always @(posedge sys_clk) begin
        if (sys_rst) begin
            start           <=  1'b0;
            test_counter    <=  0;
            sys_success     <=  1'b0;
            sys_fail        <=  1'b0;
        end else begin
            if (~start || done_tick) begin
                if (done_tick) begin
                    if (bin == sink[test_counter - 1]) begin
                        $display("[Cycle %04d] bcd2bin: %d => 0x%h",
                            cycle_count, bcd1 * 10 + bcd0, bin);
                    end else begin
                        $display("[Cycle %04d] bcd2bin: %d => 0x%h (0x%h expected), fail",
                            cycle_count, bcd1 * 10 + bcd0, bin, sink[test_counter - 1]);
                        sys_fail    <=  1'b1;
                    end
                end

                if (source[test_counter] === 8'hx) begin
                    sys_success     <=  1'b1;
                end else begin
                    {bcd1, bcd0}    <=  source[test_counter];
                    test_counter    <=  test_counter + 1;
                    start           <=  1'b1;
                end
            end
        end
    end

endmodule
