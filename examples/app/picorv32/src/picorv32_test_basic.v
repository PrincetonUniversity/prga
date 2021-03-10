// This is free and unencumbered software released into the public domain.
//
// Anyone is free to copy, modify, publish, use, compile, sell, or
// distribute this software, either in source code form or as a compiled
// binary, for any purpose, commercial or non-commercial, and by any
// means.


module picorv32_test_basic #(
	parameter AXI_TEST = 0,
	parameter VERBOSE = 0
) (
	input wire tb_clk,
	input wire tb_rst,
    output reg tb_pass,
    output reg tb_fail,
    input wire tb_prog_done,
    input wire [31:0] tb_verbosity,
    input wire [31:0] tb_cycle_cnt,

    output wire        clk,
    output wire        resetn,
    input  wire        trap,

    input  wire        mem_axi_awvalid,
	output wire        mem_axi_awready,
	input  wire [31:0] mem_axi_awaddr,
	input  wire [ 2:0] mem_axi_awprot,

	input  wire        mem_axi_wvalid,
	output wire        mem_axi_wready,
	input  wire [31:0] mem_axi_wdata,
	input  wire [ 3:0] mem_axi_wstrb,

	output wire        mem_axi_bvalid,
	input  wire        mem_axi_bready,

	input  wire        mem_axi_arvalid,
	output wire        mem_axi_arready,
	input  wire [31:0] mem_axi_araddr,
	input  wire [ 2:0] mem_axi_arprot,

	output wire        mem_axi_rvalid,
	input  wire        mem_axi_rready,
	output reg  [31:0] mem_axi_rdata,

	// Pico Co-Processor Interface (PCPI)
	input  wire        pcpi_valid,
	input  wire [31:0] pcpi_insn,
	input  wire [31:0] pcpi_rs1,
	input  wire [31:0] pcpi_rs2,
	output wire        pcpi_wr,
	output wire [31:0] pcpi_rd,
	output wire        pcpi_wait,
	output wire        pcpi_ready,

	// IRQ interface
	output reg  [31:0] irq,
	input  wire [31:0] eoi,

	// Trace Interface
	output wire        trace_valid,
	output wire [35:0] trace_data,

    input wire [63:0] internal_cycle_count
);

    assign clk = tb_clk;
    assign resetn = ~(tb_rst || ~tb_prog_done);

	always @* begin
		irq = 0;
		irq[4] = &internal_cycle_count[12:0];
		irq[5] = &internal_cycle_count[15:0];
	end

    wire [31:0] mem_axi_rdata_p;

    integer mem_axi_rdata_x2r_idx;
    initial begin
        mem_axi_rdata = $unsigned($random);
    end

    always @*
        for (mem_axi_rdata_x2r_idx = 0; mem_axi_rdata_x2r_idx < 32; mem_axi_rdata_x2r_idx = mem_axi_rdata_x2r_idx + 1)
            if (mem_axi_rdata_p[mem_axi_rdata_x2r_idx] === 1'bx)
                mem_axi_rdata[mem_axi_rdata_x2r_idx] = ($unsigned($random) % 2);
            else
                mem_axi_rdata[mem_axi_rdata_x2r_idx] = mem_axi_rdata_p[mem_axi_rdata_x2r_idx];

	axi4_memory #(
		.AXI_TEST (AXI_TEST),
		.VERBOSE  (VERBOSE)
	) mem (
		.clk             (tb_clk         ),
        .rst             (tb_rst         ),

		.mem_axi_awvalid (mem_axi_awvalid ),
		.mem_axi_awready (mem_axi_awready ),
		.mem_axi_awaddr  (mem_axi_awaddr  ),
		.mem_axi_awprot  (mem_axi_awprot  ),

		.mem_axi_wvalid  (mem_axi_wvalid  ),
		.mem_axi_wready  (mem_axi_wready  ),
		.mem_axi_wdata   (mem_axi_wdata   ),
		.mem_axi_wstrb   (mem_axi_wstrb   ),

		.mem_axi_bvalid  (mem_axi_bvalid  ),
		.mem_axi_bready  (mem_axi_bready  ),

		.mem_axi_arvalid (mem_axi_arvalid ),
		.mem_axi_arready (mem_axi_arready ),
		.mem_axi_araddr  (mem_axi_araddr  ),
		.mem_axi_arprot  (mem_axi_arprot  ),

		.mem_axi_rvalid  (mem_axi_rvalid  ),
		.mem_axi_rready  (mem_axi_rready  ),
		.mem_axi_rdata   (mem_axi_rdata_p ),

		.tests_passed    (tests_passed    )
	);

`ifdef RISCV_FORMAL
	wire        rvfi_valid;
	wire [63:0] rvfi_order;
	wire [31:0] rvfi_insn;
	wire        rvfi_trap;
	wire        rvfi_halt;
	wire        rvfi_intr;
	wire [4:0]  rvfi_rs1_addr;
	wire [4:0]  rvfi_rs2_addr;
	wire [31:0] rvfi_rs1_rdata;
	wire [31:0] rvfi_rs2_rdata;
	wire [4:0]  rvfi_rd_addr;
	wire [31:0] rvfi_rd_wdata;
	wire [31:0] rvfi_pc_rdata;
	wire [31:0] rvfi_pc_wdata;
	wire [31:0] rvfi_mem_addr;
	wire [3:0]  rvfi_mem_rmask;
	wire [3:0]  rvfi_mem_wmask;
	wire [31:0] rvfi_mem_rdata;
	wire [31:0] rvfi_mem_wdata;
`endif

	reg [1023:0] firmware_file;
	initial begin
        if (!$value$plusargs("firmware=%s", firmware_file)) begin
            $display("Missing required argument: +firmware=FIRMWARE.hex");
            $finish;
        end
		$readmemh(firmware_file, mem.memory);
	end

	always @(posedge tb_clk) begin
        if (tb_rst) begin
            tb_pass <= 1'b0;
            tb_fail <= 1'b0;
        end
		if (resetn && trap) begin
`ifndef VERILATOR
			repeat (10) @(posedge tb_clk);
`endif
			$display("TRAP after %1d clock cycles", tb_cycle_cnt);
			if (tests_passed) begin
				$display("ALL TESTS PASSED.");
                tb_pass <= 1'b1;
			end else begin
				$display("ERROR!");
                tb_fail <= 1'b1;
			end
		end
	end
endmodule

module axi4_memory #(
	parameter AXI_TEST = 0,
	parameter VERBOSE = 0
) (
	/* verilator lint_off MULTIDRIVEN */

	input             clk,
    input             rst,

	input             mem_axi_awvalid,
	output reg        mem_axi_awready,
	input      [31:0] mem_axi_awaddr,
	input      [ 2:0] mem_axi_awprot,

	input             mem_axi_wvalid,
	output reg        mem_axi_wready,
	input      [31:0] mem_axi_wdata,
	input      [ 3:0] mem_axi_wstrb,

	output reg        mem_axi_bvalid,
	input             mem_axi_bready,

	input             mem_axi_arvalid,
	output reg        mem_axi_arready,
	input      [31:0] mem_axi_araddr,
	input      [ 2:0] mem_axi_arprot,

	output reg        mem_axi_rvalid,
	input             mem_axi_rready,
	output reg [31:0] mem_axi_rdata,

	output reg        tests_passed
);
	reg [31:0]   memory [0:64*1024/4-1] /* verilator public */;
	reg verbose;
	initial verbose = $test$plusargs("verbose") || VERBOSE;

	reg axi_test;
	initial axi_test = $test$plusargs("axi_test") || AXI_TEST;

	initial begin
		mem_axi_awready = 0;
		mem_axi_wready = 0;
		mem_axi_bvalid = 0;
		mem_axi_arready = 0;
		mem_axi_rvalid = 0;
		tests_passed = 0;
	end

	reg [63:0] xorshift64_state = 64'd88172645463325252;

	task xorshift64_next;
		begin
			// see page 4 of Marsaglia, George (July 2003). "Xorshift RNGs". Journal of Statistical Software 8 (14).
			xorshift64_state = xorshift64_state ^ (xorshift64_state << 13);
			xorshift64_state = xorshift64_state ^ (xorshift64_state >>  7);
			xorshift64_state = xorshift64_state ^ (xorshift64_state << 17);
		end
	endtask

	reg [2:0] fast_axi_transaction = ~0;
	reg [4:0] async_axi_transaction = ~0;
	reg [4:0] delay_axi_transaction = 0;

	always @(posedge clk) begin
		if (axi_test) begin
				xorshift64_next;
				{fast_axi_transaction, async_axi_transaction, delay_axi_transaction} <= xorshift64_state;
		end
	end

	reg latched_raddr_en = 0;
	reg latched_waddr_en = 0;
	reg latched_wdata_en = 0;

	reg fast_raddr = 0;
	reg fast_waddr = 0;
	reg fast_wdata = 0;

	reg [31:0] latched_raddr;
	reg [31:0] latched_waddr;
	reg [31:0] latched_wdata;
	reg [ 3:0] latched_wstrb;
	reg        latched_rinsn;

	task handle_axi_arvalid; begin
		mem_axi_arready <= 1;
		latched_raddr = mem_axi_araddr;
		latched_rinsn = mem_axi_arprot[2];
		latched_raddr_en = 1;
		fast_raddr <= 1;
	end endtask

	task handle_axi_awvalid; begin
		mem_axi_awready <= 1;
		latched_waddr = mem_axi_awaddr;
		latched_waddr_en = 1;
		fast_waddr <= 1;
	end endtask

	task handle_axi_wvalid; begin
		mem_axi_wready <= 1;
		latched_wdata = mem_axi_wdata;
		latched_wstrb = mem_axi_wstrb;
		latched_wdata_en = 1;
		fast_wdata <= 1;
	end endtask

	task handle_axi_rvalid; begin
		if (verbose)
			$display("RD: ADDR=%08x DATA=%08x%s", latched_raddr, memory[latched_raddr >> 2], latched_rinsn ? " INSN" : "");
		if (latched_raddr < 64*1024) begin
			mem_axi_rdata <= memory[latched_raddr >> 2];
			mem_axi_rvalid <= 1;
			latched_raddr_en = 0;
		end else begin
			$display("OUT-OF-BOUNDS MEMORY READ FROM %08x", latched_raddr);
			$finish;
		end
	end endtask

	task handle_axi_bvalid; begin
		if (verbose)
			$display("WR: ADDR=%08x DATA=%08x STRB=%04b", latched_waddr, latched_wdata, latched_wstrb);
		if (latched_waddr < 64*1024) begin
			if (latched_wstrb[0]) memory[latched_waddr >> 2][ 7: 0] <= latched_wdata[ 7: 0];
			if (latched_wstrb[1]) memory[latched_waddr >> 2][15: 8] <= latched_wdata[15: 8];
			if (latched_wstrb[2]) memory[latched_waddr >> 2][23:16] <= latched_wdata[23:16];
			if (latched_wstrb[3]) memory[latched_waddr >> 2][31:24] <= latched_wdata[31:24];
		end else
		if (latched_waddr == 32'h1000_0000) begin
			if (verbose) begin
				if (32 <= latched_wdata && latched_wdata < 128)
					$display("OUT: '%c'", latched_wdata[7:0]);
				else
					$display("OUT: %3d", latched_wdata);
			end else begin
				$write("%c", latched_wdata[7:0]);
`ifndef VERILATOR
				$fflush();
`endif
			end
		end else
		if (latched_waddr == 32'h2000_0000) begin
			if (latched_wdata == 123456789)
				tests_passed = 1;
		end else begin
			$display("OUT-OF-BOUNDS MEMORY WRITE TO %08x", latched_waddr);
			$finish;
		end
		mem_axi_bvalid <= 1;
		latched_waddr_en = 0;
		latched_wdata_en = 0;
	end endtask

	always @(negedge clk or posedge clk) begin
        if (~rst) begin
            if (~clk) begin
                if (mem_axi_arvalid && !(latched_raddr_en || fast_raddr) && async_axi_transaction[0]) handle_axi_arvalid;
                if (mem_axi_awvalid && !(latched_waddr_en || fast_waddr) && async_axi_transaction[1]) handle_axi_awvalid;
                if (mem_axi_wvalid  && !(latched_wdata_en || fast_wdata) && async_axi_transaction[2]) handle_axi_wvalid;
                if (!mem_axi_rvalid && latched_raddr_en && async_axi_transaction[3]) handle_axi_rvalid;
                if (!mem_axi_bvalid && latched_waddr_en && latched_wdata_en && async_axi_transaction[4]) handle_axi_bvalid;
            end else begin
                mem_axi_arready <= 0;
                mem_axi_awready <= 0;
                mem_axi_wready <= 0;

                fast_raddr <= 0;
                fast_waddr <= 0;
                fast_wdata <= 0;

                if (mem_axi_rvalid && mem_axi_rready) begin
                    mem_axi_rvalid <= 0;
                end

                if (mem_axi_bvalid && mem_axi_bready) begin
                    mem_axi_bvalid <= 0;
                end

                if (mem_axi_arvalid && mem_axi_arready && !fast_raddr) begin
                    latched_raddr = mem_axi_araddr;
                    latched_rinsn = mem_axi_arprot[2];
                    latched_raddr_en = 1;
                end

                if (mem_axi_awvalid && mem_axi_awready && !fast_waddr) begin
                    latched_waddr = mem_axi_awaddr;
                    latched_waddr_en = 1;
                end

                if (mem_axi_wvalid && mem_axi_wready && !fast_wdata) begin
                    latched_wdata = mem_axi_wdata;
                    latched_wstrb = mem_axi_wstrb;
                    latched_wdata_en = 1;
                end

                if (mem_axi_arvalid && !(latched_raddr_en || fast_raddr) && !delay_axi_transaction[0]) handle_axi_arvalid;
                if (mem_axi_awvalid && !(latched_waddr_en || fast_waddr) && !delay_axi_transaction[1]) handle_axi_awvalid;
                if (mem_axi_wvalid  && !(latched_wdata_en || fast_wdata) && !delay_axi_transaction[2]) handle_axi_wvalid;

                if (!mem_axi_rvalid && latched_raddr_en && !delay_axi_transaction[3]) handle_axi_rvalid;
                if (!mem_axi_bvalid && latched_waddr_en && latched_wdata_en && !delay_axi_transaction[4]) handle_axi_bvalid;
            end
        end
    end
endmodule
