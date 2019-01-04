`timescale 1ns/1ps
module tb;
    
    reg clk, reset;
    reg a, b;
    wire c, ready;

    gate dut (
        .\reset (reset),
        .\a (a),
        .\b (b),
        .\c (c),
        .\ready (ready)
        );

    localparam n_tests = 4;
    reg [1:0] test_id;
    reg [0:0] a_src [0:n_tests - 1];
    reg [0:0] b_src [0:n_tests - 1];
    reg [0:0] c_sink [0:n_tests - 1];

    reg [0:64*8-1] dumpfile;
    reg [0:64*8-1] sdffile;
    reg [31:0] cycle_count, max_cycle_count;

    initial begin
        if ($value$plusargs("dump=%s", dumpfile)) begin
            $display("[INFO] Dumping waveform: %s", dumpfile);
            $dumpfile(dumpfile);
            $dumpvars;
        end

        if ($value$plusargs("sdf=%s", sdffile)) begin
            $display("[INFO] Using SDF back-annotation: %s", sdffile);
            // $sdf_annotate(sdffile, dut);
        end

        if (!$value$plusargs("max_cycle=%d", max_cycle_count)) begin
            max_cycle_count = 100_000;
        end
        $display("[INFO] Max cycle count: %d", max_cycle_count);

        clk = 1'b0;
        reset = 1'b1;

        a_src[0] = 1'b0;    b_src[0] = 1'b0;    c_sink[0] = 1'b0;
        a_src[1] = 1'b0;    b_src[1] = 1'b1;    c_sink[1] = 1'b1;
        a_src[2] = 1'b1;    b_src[2] = 1'b1;    c_sink[2] = 1'b0;
        a_src[3] = 1'b1;    b_src[3] = 1'b0;    c_sink[3] = 1'b1;

        #999 reset = 1'b0;
    end

    always #2 clk = ~clk;

    always @(posedge clk) begin
        if (reset) begin
            cycle_count     <= 0;
        end else begin
            cycle_count     <= cycle_count + 1;
        end

        if (cycle_count == max_cycle_count) begin
            $display("bcd2bin: maximum cycle count reached");
            $finish;
        end else if (~reset && (cycle_count % 1_000 == 0)) begin
            $display("[INFO] %dK cycles passed", cycle_count / 1_000);
        end
    end

    always @(posedge clk) begin
        if (reset) begin
            test_id <= 0;
        end else if (ready) begin
            if (test_id == n_tests - 1) begin
                $display("gate: all tests passed");
                $finish;
            end else begin
                test_id <= test_id + 1;
            end
        end
    end

    always @* begin
        if (ready) begin
            a = a_src[test_id];
            b = b_src[test_id];

            #1 if (c != c_sink[test_id]) begin
                $display("gate: %b ^ %b != %b, failed.", a, b, c);
                $finish;
            end else begin
                $display("gate: %b ^ %b == %b, passed.", a, b, c);
            end
        end
    end

endmodule

