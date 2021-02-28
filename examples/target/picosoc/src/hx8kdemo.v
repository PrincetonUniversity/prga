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

module hx8kdemo (
	input clk,
    input tb_rst,
    output resetn,

	// output ser_tx,
	// input ser_rx,

	output [7:0] leds,

	// output flash_csb,
	// output flash_clk,
	inout  flash_io0,
	inout  flash_io1,
	inout  flash_io2,
	inout  flash_io3,

	input             iomem_valid,
	output reg        iomem_ready,
	input      [ 3:0] iomem_wstrb,
	input      [31:0] iomem_addr,
	input      [31:0] iomem_wdata,
	output reg [31:0] iomem_rdata,

	input  flash_io0_oe,
	input  flash_io1_oe,
	input  flash_io2_oe,
	input  flash_io3_oe,

	input  flash_io0_do,
	input  flash_io1_do,
	input  flash_io2_do,
	input  flash_io3_do,

	output flash_io0_di,
	output flash_io1_di,
	output flash_io2_di,
	output flash_io3_di
);
	reg [5:0] reset_cnt;
    assign resetn = &reset_cnt;

    initial begin
        reset_cnt = 0;
    end

	always @(posedge clk) begin
        if (~tb_rst) begin
            reset_cnt <= reset_cnt + !resetn;
        end
	end

	SB_IO #(
		.PIN_TYPE(6'b 1010_01),
		.PULLUP(1'b 0)
	) flash_io_buf [3:0] (
		.PACKAGE_PIN({flash_io3, flash_io2, flash_io1, flash_io0}),
		.OUTPUT_ENABLE({flash_io3_oe, flash_io2_oe, flash_io1_oe, flash_io0_oe}),
		.D_OUT_0({flash_io3_do, flash_io2_do, flash_io1_do, flash_io0_do}),
		.D_IN_0({flash_io3_di, flash_io2_di, flash_io1_di, flash_io0_di})
	);

	reg         iomem_ready;
	reg  [31:0] iomem_rdata;

	reg [31:0] gpio;
	assign leds = gpio;

	always @(posedge clk) begin
		if (!resetn) begin
            iomem_ready <= 0;
			gpio <= 0;
		end else begin
			iomem_ready <= 0;
			if (iomem_valid && !iomem_ready && iomem_addr[31:24] == 8'h 03) begin
				iomem_ready <= 1;
				iomem_rdata <= gpio;
				if (iomem_wstrb[0]) gpio[ 7: 0] <= iomem_wdata[ 7: 0];
				if (iomem_wstrb[1]) gpio[15: 8] <= iomem_wdata[15: 8];
				if (iomem_wstrb[2]) gpio[23:16] <= iomem_wdata[23:16];
				if (iomem_wstrb[3]) gpio[31:24] <= iomem_wdata[31:24];
			end
		end
	end

endmodule
