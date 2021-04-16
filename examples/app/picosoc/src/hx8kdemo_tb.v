/*
 *  PicoSoC - A simple example SoC using PicoRV32
 *
 *  Copyright (C) 2017  Clifford Wolf <clifford@clifford.at>
 *
 *  Permission to use, copy, modify, and/or distribute this software for any
 *  purpose with or without fee is hereby granted, provided that the above
 *  copyright notice and this permission notice appear in all copies.
 *
 *  THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 *  WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 *  MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 *  ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 *  WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 *  ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 *  OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 */

`timescale 1 ns / 1 ps

module testbench (
	input wire tb_clk,
	input wire tb_rst,
    output reg tb_pass,
    output reg tb_fail,
    input wire tb_prog_done,
    input wire [31:0] tb_verbosity,
    input wire [31:0] tb_cycle_cnt,

    output          clk,
    output          resetn,

    input           iomem_valid,
    output          iomem_ready,
    input  [ 3:0]   iomem_wstrb,
    input  [31:0]   iomem_addr,
    input  [31:0]   iomem_wdata,
    output [31:0]   iomem_rdata,

    output          irq_5,
    output          irq_6,
    output          irq_7,

    input           ser_tx,
    output          ser_rx,

    input           flash_csb,
    input           flash_clk,

	input           flash_io0_oe,
	input           flash_io1_oe,
	input           flash_io2_oe,
	input           flash_io3_oe,

	input           flash_io0_do,
	input           flash_io1_do,
	input           flash_io2_do,
	input           flash_io3_do,

	output          flash_io0_di,
	output          flash_io1_di,
	output          flash_io2_di,
	output          flash_io3_di
    );

    assign clk = tb_clk;

	localparam ser_half_period = 53;
	event ser_sample;

	integer cycle_cnt;
    reg [34 * 8 - 1:0]      serial_output_log;

	wire [7:0] leds;

	initial begin
		// $dumpfile("testbench.vcd");
		// $dumpvars(0, testbench);

        cycle_cnt = 0;
        serial_output_log = "";

        tb_pass = 1'b0;
        tb_fail = 1'b0;

		repeat (6) begin
			repeat (50000) @(posedge clk);
			$display("[PICOTB] +50000 cycles");
		end

        // $finish;
        $display("[PICOTB] Final state of leds: %b (expecting: 11111111)", leds);
        $display("[PICOTB] Serial output log: %s (expecting: Booting..Press ENTER to continue..)", serial_output_log);

        if (&leds && serial_output_log == "Booting..Press ENTER to continue..")
            tb_pass = 1'b1;
        else
            tb_fail = 1'b1;
	end

	always @(posedge clk) begin
		cycle_cnt <= cycle_cnt + 1;
	end

	tri1 flash_io0;
	tri1 flash_io1;
	tri1 flash_io2;
	tri1 flash_io3;

    initial begin
        // Give inout wires an initial value to prevent X-pollution of LUTs
        force flash_io0 = 1'b1;
        force flash_io1 = 1'b1;
        force flash_io2 = 1'b1;
        force flash_io3 = 1'b1;

        @(posedge tb_rst);
        @(negedge tb_rst);
        release flash_io0;
        release flash_io1;
        release flash_io2;
        release flash_io3;
    end

	always @(leds) begin
		#1 $display("[PICOTB] leds: %b", leds);
	end

	hx8kdemo uut (
		.clk      (clk      ),
        .tb_rst   (tb_rst || ~tb_prog_done),
        .resetn   (resetn   ),
		.leds     (leds     ),

		.flash_io0      (flash_io0),
		.flash_io1      (flash_io1),
		.flash_io2      (flash_io2),
		.flash_io3      (flash_io3),

        .iomem_valid    (iomem_valid),
        .iomem_ready    (iomem_ready),
        .iomem_wstrb    (iomem_wstrb),
        .iomem_addr     (iomem_addr),
        .iomem_wdata    (iomem_wdata),
        .iomem_rdata    (iomem_rdata),

        .flash_io0_oe   (flash_io0_oe),
        .flash_io1_oe   (flash_io1_oe),
        .flash_io2_oe   (flash_io2_oe),
        .flash_io3_oe   (flash_io3_oe),

        .flash_io0_do   (flash_io0_do),
        .flash_io1_do   (flash_io1_do),
        .flash_io2_do   (flash_io2_do),
        .flash_io3_do   (flash_io3_do),

        .flash_io0_di   (flash_io0_di),
        .flash_io1_di   (flash_io1_di),
        .flash_io2_di   (flash_io2_di),
        .flash_io3_di   (flash_io3_di)
	);

	spiflash spiflash (
		.csb(flash_csb),
		.clk(flash_clk),
		.io0(flash_io0),
		.io1(flash_io1),
		.io2(flash_io2),
		.io3(flash_io3)
	);

	reg [7:0] buffer;

	always begin
		@(negedge ser_tx);

		repeat (ser_half_period) @(posedge clk);
		-> ser_sample; // start bit

		repeat (8) begin
			repeat (ser_half_period) @(posedge clk);
			repeat (ser_half_period) @(posedge clk);
			buffer = {ser_tx, buffer[7:1]};
			-> ser_sample; // data bit
		end

		repeat (ser_half_period) @(posedge clk);
		repeat (ser_half_period) @(posedge clk);
		-> ser_sample; // stop bit

		if (buffer < 32 || buffer >= 127)
			$display("[PICOTB] Serial data: %d", buffer);
        else begin
			$display("[PICOTB] Serial data: '%c'", buffer);
            serial_output_log <= {serial_output_log, buffer};
        end
	end

    assign irq_5 = 1'b0;
    assign irq_6 = 1'b0;
    assign irq_7 = 1'b0;
    assign ser_rx = 1'b1;

endmodule
