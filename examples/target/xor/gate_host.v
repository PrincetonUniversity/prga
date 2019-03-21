module gate_host (
    input wire sys_clk,
    input wire sys_rst,
    output reg sys_success,
    output reg sys_fail,
    input wire [31:0] cycle_count,

    output wire clk,
    output wire reset,
    output reg a,
    output reg b,
    input wire c
    );

    localparam n_tests = 16;
    reg [4:0] test_id;
    reg [0:0] a_src [0:n_tests];
    reg [0:0] b_src [0:n_tests];
    reg [0:0] c_sink [0:n_tests];

    initial begin
        a_src[ 0] = 1'b0;   b_src[ 0] = 1'b0;   c_sink[ 0] = 1'b0;
        a_src[ 1] = 1'b0;   b_src[ 1] = 1'b1;   c_sink[ 1] = 1'b1;
        a_src[ 2] = 1'b1;   b_src[ 2] = 1'b1;   c_sink[ 2] = 1'b0;
        a_src[ 3] = 1'b1;   b_src[ 3] = 1'b0;   c_sink[ 3] = 1'b1;
        a_src[ 4] = 1'b0;   b_src[ 4] = 1'b1;   c_sink[ 4] = 1'b1;
        a_src[ 5] = 1'b1;   b_src[ 5] = 1'b0;   c_sink[ 5] = 1'b1;
        a_src[ 6] = 1'b1;   b_src[ 6] = 1'b1;   c_sink[ 6] = 1'b0;
        a_src[ 7] = 1'b0;   b_src[ 7] = 1'b0;   c_sink[ 7] = 1'b0;
        a_src[ 8] = 1'b0;   b_src[ 8] = 1'b1;   c_sink[ 8] = 1'b1;
        a_src[ 9] = 1'b0;   b_src[ 9] = 1'b1;   c_sink[ 9] = 1'b1;
        a_src[10] = 1'b1;   b_src[10] = 1'b0;   c_sink[10] = 1'b1;
        a_src[11] = 1'b1;   b_src[11] = 1'b1;   c_sink[11] = 1'b0;
        a_src[12] = 1'b1;   b_src[12] = 1'b0;   c_sink[12] = 1'b1;
        a_src[13] = 1'b1;   b_src[13] = 1'b1;   c_sink[13] = 1'b0;
        a_src[14] = 1'b0;   b_src[14] = 1'b0;   c_sink[14] = 1'b0;
        a_src[15] = 1'b0;   b_src[15] = 1'b0;   c_sink[15] = 1'b0;
    end

    always @(posedge sys_clk) begin
        if (sys_rst) begin
            test_id <= 0;
        end else begin
            test_id     <=  test_id + 1;
            $display("[Cyce %04d] testing %d", cycle_count, test_id);
        end
    end

    always @* begin
        sys_fail    =   1'b0;
        sys_success =   1'b0;

        if (~sys_rst) begin
            a = a_src[test_id];
            b = b_src[test_id];

            #1 if (c == c_sink[test_id]) begin
                $display("[Cycle %04d] gate: %b ^ %b == %b, passed", cycle_count, a, b, c);
            end else begin
                $display("[Cycle %04d] gate: %b ^ %b != %b, failed", cycle_count, a, b, c);
                sys_fail    =   1'b1;
            end

            if (test_id == n_tests - 1) begin
                sys_success =   1'b1;
            end
        end
    end

endmodule

