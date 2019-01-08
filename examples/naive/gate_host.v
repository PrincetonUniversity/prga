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

    localparam n_tests = 4;
    reg [1:0] test_id;
    reg [0:0] a_src [0:n_tests - 1];
    reg [0:0] b_src [0:n_tests - 1];
    reg [0:0] c_sink [0:n_tests - 1];

    initial begin
        a_src[0] = 1'b0;    b_src[0] = 1'b0;    c_sink[0] = 1'b0;
        a_src[1] = 1'b0;    b_src[1] = 1'b1;    c_sink[1] = 1'b1;
        a_src[2] = 1'b1;    b_src[2] = 1'b1;    c_sink[2] = 1'b0;
        a_src[3] = 1'b1;    b_src[3] = 1'b0;    c_sink[3] = 1'b1;
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

