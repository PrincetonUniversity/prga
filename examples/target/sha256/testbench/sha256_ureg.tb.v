`timescale 1ns/1ps
module sha256_ureg_tb;

    reg sys_clk, sys_rst;
    wire sys_success, sys_fail;
    reg [31:0] cycle_count;

    wire ureg_req_rdy, ureg_req_val, ureg_resp_rdy, ureg_resp_val, ureg_resp_ecc;
    wire [11:0] ureg_req_addr;
    wire [63:0] ureg_req_data, ureg_resp_data;
    wire [7:0] ureg_req_strb;

    sha256_ureg_host host (
        .sys_clk                (sys_clk)
        ,.sys_rst               (sys_rst)
        ,.sys_success           (sys_success)
        ,.sys_fail              (sys_fail)
        ,.cycle_count           (cycle_count)

        ,.clk		            (clk)
        ,.rst_n		            (rst_n)

        ,.ureg_req_rdy		    (ureg_req_rdy)
        ,.ureg_req_val		    (ureg_req_val)
        ,.ureg_req_addr		    (ureg_req_addr)
        ,.ureg_req_strb		    (ureg_req_strb)
        ,.ureg_req_data		    (ureg_req_data)

        ,.ureg_resp_rdy		    (ureg_resp_rdy)
        ,.ureg_resp_val		    (ureg_resp_val)
        ,.ureg_resp_data		(ureg_resp_data)
        ,.ureg_resp_ecc         (ureg_resp_ecc)
        );

    sha256_ureg dut (
        .clk		            (clk)
        ,.rst_n		            (rst_n)

        ,.ureg_req_rdy		    (ureg_req_rdy)
        ,.ureg_req_val		    (ureg_req_val)
        ,.ureg_req_addr		    (ureg_req_addr)
        ,.ureg_req_strb		    (ureg_req_strb)
        ,.ureg_req_data		    (ureg_req_data)

        ,.ureg_resp_rdy		    (ureg_resp_rdy)
        ,.ureg_resp_val		    (ureg_resp_val)
        ,.ureg_resp_data		(ureg_resp_data)
        ,.ureg_resp_ecc         (ureg_resp_ecc)
        );

    localparam CLK_PERIOD = 10;

    initial begin
        sys_clk = 'b0;
        sys_rst = 'b0;
        cycle_count = 'b0;

        #(CLK_PERIOD + 2);
        sys_rst = 'b1;
        #CLK_PERIOD;
        sys_rst = 'b0;

        #(10000 * CLK_PERIOD);
        $display("[TIMEOUT]");
        $finish;
    end

    always #(CLK_PERIOD / 2) sys_clk = ~sys_clk;

    always @(posedge sys_clk) begin
        if (sys_rst) begin
            cycle_count <= 'b0;
        end else begin
            cycle_count <= cycle_count + 1;

            if (sys_success) begin
                $display("[PASS]");
                $finish;
            end else if (sys_fail) begin
                $display("[FAIL]");
                $finish;
            end
        end
    end

endmodule

