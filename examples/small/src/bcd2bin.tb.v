`timescale 1ns/1ps
module tb;
    
    reg clk, reset, start;
    reg [3:0] bcd1, bcd0;
    wire ready, done_tick;
    wire [6:0] bin;
    
    reg [3:0] test_counter;
    reg [7:0] source [0:15];
    reg [6:0] sink [0:15];

    bcd2bin dut (
        .clk(clk),
        .reset(reset),
        .start(start),
        .bcd1(bcd1),
        .bcd0(bcd0),
        .ready(ready),
        .done_tick(done_tick),
        .bin(bin)
        );

    reg [0:64*8-1] dumpfile;
    reg [31:0] cycle_count, max_cycle_count;

    // set up test source & sink
    initial begin
        source[0] = {4'd0, 4'd0}; sink[0] = 7'h00;
        source[1] = {4'd9, 4'd9}; sink[1] = 7'h63;
        source[2] = {4'd5, 4'd5}; sink[2] = 7'h37;
        source[3] = {4'd0, 4'd9}; sink[3] = 7'h09;
        source[4] = {4'd9, 4'd0}; sink[4] = 7'h5a;
    end

    initial begin
        if ($value$plusargs("dump=%s", dumpfile)) begin
            $display("[INFO] Dumping waveform: %s", dumpfile);
            $dumpfile(dumpfile);
            $dumpvars;
        end

        if (!$value$plusargs("max_cycle=%d", max_cycle_count)) begin
            max_cycle_count = 100_000;
        end
        $display("[INFO] Max cycle count: %d", max_cycle_count);

        clk = 1'b0;
        reset = 1'b1;
        start = 1'b0;

        #199 reset = 1'b0;
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
        if (reset) begin
            start           <= 1'b0;
            test_counter    <=  0;
        end else begin
            if (~start || done_tick) begin
                if (done_tick) begin
                    if (bin == sink[test_counter - 1]) begin
                        $display("[Cycle %04d] bcd2bin: %d => 0x%h",
                            cycle_count, bcd1 * 10 + bcd0, bin);
                    end else begin
                        $display("          * * *           ");
                        $display("bcd2bin: %d => 0x%h (0x%h expected), fail",
                            bcd1 * 10 + bcd0, bin, sink[test_counter - 1]);
                        $display("          * * *           ");
                        $finish;
                    end
                end

                if (source[test_counter] === 8'hx) begin
                    $display("          * * *           ");
                    $display("bcd2bin: all tests passed ");
                    $display("          * * *           ");
                    $finish;
                end else begin
                    {bcd1, bcd0}    <=  source[test_counter];
                    test_counter    <=  test_counter + 1;
                    start           <=  1'b1;
                end
            end
        end
    end

    always @* begin
        if (cycle_count == max_cycle_count) begin
            $display("          * * *           ");
            $display("bcd2bin: maximum cycle count reached");
            $display("          * * *           ");
            $finish;
        end
    end

endmodule
