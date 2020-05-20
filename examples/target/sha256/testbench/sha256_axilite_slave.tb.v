`timescale 1ns/1ps
module sha256_axilite_slave_tb;

    reg sys_clk, sys_rst;
    wire sys_success, sys_fail;
    reg [31:0] cycle_count;

    wire ACLK, ARESETn, AWVALID, AWREADY, WVALID, WREADY, BVALID, BREADY, ARVALID, ARREADY, RVALID, RREADY;
    wire [7:0] AWADDR, ARADDR;
    wire [2:0] AWPROT, ARPROT;
    wire [1:0] BRESP, RRESP;
    wire [31:0] WDATA, RDATA;
    wire [3:0] WSTRB;

    sha256_axilite_slave_host host (
        .sys_clk                (sys_clk)
        ,.sys_rst               (sys_rst)
        ,.sys_success           (sys_success)
        ,.sys_fail              (sys_fail)
        ,.cycle_count           (cycle_count)
        ,.ACLK                  (ACLK)
        ,.ARESETn               (ARESETn)
        ,.AWVALID               (AWVALID)
        ,.AWREADY               (AWREADY)
        ,.AWADDR                (AWADDR)
        ,.AWPROT                (AWPROT)
        ,.WVALID                (WVALID)
        ,.WREADY                (WREADY)
        ,.WSTRB                 (WSTRB)
        ,.WDATA                 (WDATA)
        ,.BREADY                (BREADY)
        ,.BVALID                (BVALID)
        ,.BRESP                 (BRESP)
        ,.ARVALID               (ARVALID)
        ,.ARREADY               (ARREADY)
        ,.ARADDR                (ARADDR)
        ,.ARPROT                (ARPROT)
        ,.RREADY                (RREADY)
        ,.RVALID                (RVALID)
        ,.RDATA                 (RDATA)
        ,.RRESP                 (RRESP)
        );

    sha256_axilite_slave dut (
        .ACLK                   (ACLK)
        ,.ARESETn               (ARESETn)
        ,.AWVALID               (AWVALID)
        ,.AWREADY               (AWREADY)
        ,.AWADDR                (AWADDR)
        ,.AWPROT                (AWPROT)
        ,.WVALID                (WVALID)
        ,.WREADY                (WREADY)
        ,.WSTRB                 (WSTRB)
        ,.WDATA                 (WDATA)
        ,.BREADY                (BREADY)
        ,.BVALID                (BVALID)
        ,.BRESP                 (BRESP)
        ,.ARVALID               (ARVALID)
        ,.ARREADY               (ARREADY)
        ,.ARADDR                (ARADDR)
        ,.ARPROT                (ARPROT)
        ,.RREADY                (RREADY)
        ,.RVALID                (RVALID)
        ,.RDATA                 (RDATA)
        ,.RRESP                 (RRESP)
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
