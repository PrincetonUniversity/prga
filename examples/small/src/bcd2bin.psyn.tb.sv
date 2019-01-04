`timescale 1ns/1ps
module tb;
    
    reg clk, reset, start, started;
    reg [3:0] bcd1, bcd0;
    wire ready, done_tick;
    wire [6:0] bin;
    
    wire [6:0] expected = 7'h37;

    bcd2bin dut (
        .\clk (clk),
        .\reset (reset),
        .\start (start),
        .\bcd1[0] (bcd1[0]),
        .\bcd1[1] (bcd1[1]),
        .\bcd1[2] (bcd1[2]),
        .\bcd1[3] (bcd1[3]),
        .\bcd0[0] (bcd0[0]),
        .\bcd0[1] (bcd0[1]),
        .\bcd0[2] (bcd0[2]),
        .\bcd0[3] (bcd0[3]),
        .\ready (ready),
        .\done_tick (done_tick),
        .\bin[0] (bin[0]),
        .\bin[1] (bin[1]),
        .\bin[2] (bin[2]),
        .\bin[3] (bin[3]),
        .\bin[4] (bin[4]),
        .\bin[5] (bin[5]),
        .\bin[6] (bin[6])
        );

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
        start = 1'b0;
        started = 1'b0;
        bcd1 = 4'd5;
        bcd0 = 4'd5;

        #999 reset = 1'b0;
    end

    always #2 clk = ~clk;

    always @(posedge clk) begin
        if (reset) begin
            cycle_count     <= 0;
        end else begin
            cycle_count     <= cycle_count + 1;
        end

        if (~reset && (cycle_count % 1_000 == 0)) begin
            $display("[INFO] %dK cycles passed", cycle_count / 1_000);
        end
    end

    always @(posedge clk) begin
        if (ready & ~started) begin
            start   <= 1'b1;
            started <= 1'b1;
        end else begin
            started <= 1'b0;
        end
    end

    always @(posedge clk) begin
        if (done_tick) begin
            if (bin == expected) begin
                $display("bcd2bin: 55 => 0x37, success.");
                $display("all tests passed.");
            end else begin
                $display("bcd2bin: 55 => 0x%h (0x37 expected), fail.", bin);
            end
            $finish;
        end
    end

endmodule

