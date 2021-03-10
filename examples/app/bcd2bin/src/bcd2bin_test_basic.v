module basic (
    input wire tb_clk,
    input wire tb_rst,
    output reg tb_pass,
    output reg tb_fail,
    input wire tb_prog_done,
    input wire [31:0] tb_verbosity,
    input wire [31:0] tb_cycle_cnt,

    output wire clk,
    output reg reset,
    output reg start,
    output reg [3:0] bcd0,
    output reg [3:0] bcd1,
    input wire ready,
    input wire done_tick,
    input wire [6:0] bin
    );

    assign clk = tb_clk;

    reg [7:0] reset_buf;
    always @(posedge tb_clk) begin
        if (tb_rst || ~tb_prog_done) begin
            {reset, reset_buf} <= 9'h03f;
        end else begin
            {reset, reset_buf} <= {reset_buf, 1'b0};
        end
    end
    
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

        reset = 1'b0;
        reset_buf = 8'h0;
        start = 1'b0;
        test_counter = 0;
        tb_pass = 1'b0;
        tb_fail = 1'b0;
        {bcd1, bcd0} = 0;
    end

    always @(posedge tb_clk) begin
        if (tb_rst || ~tb_prog_done) begin
            start           <=  1'b0;
            test_counter    <=  0;
            tb_pass     <=  1'b0;
            tb_fail        <=  1'b0;
            {bcd1, bcd0}    <=  0;
        end else if (tb_prog_done) begin
            if (~start || done_tick) begin
                if (done_tick) begin
                    if (bin == sink[test_counter - 1]) begin
                        $display("[Cycle %04d] bcd2bin: %d => 0x%h",
                            tb_cycle_cnt, bcd1 * 10 + bcd0, bin);
                    end else begin
                        $display("[Cycle %04d] bcd2bin: %d => 0x%h (0x%h expected), fail",
                            tb_cycle_cnt, bcd1 * 10 + bcd0, bin, sink[test_counter - 1]);
                        tb_fail    <=  1'b1;
                    end
                end

                if (source[test_counter] === 8'hx) begin
                    tb_pass     <=  1'b1;
                end else begin
                    {bcd1, bcd0}    <=  source[test_counter];
                    test_counter    <=  test_counter + 1;
                    start           <=  1'b1;
                end
            end
        end
    end

endmodule
