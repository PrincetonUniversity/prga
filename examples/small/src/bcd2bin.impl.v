module bcd2bin (
    input wire clk,
    input wire reset,
    input wire start,
    input wire [3:0] bcd1,
    input wire [3:0] bcd0,
    output reg ready,
    output reg done_tick,
    output wire [6:0] bin
    );

    localparam  config_width    =   1,
                total_size      =   7055;

    reg [15:0] config_mem [0:1023];
    reg [31:0] config_shifted;

    localparam  INIT = 2'd0,
                CONFIG = 2'd1,
                CONFIG_DONE = 2'd2,
                CONFIG_STABLE = 2'd3;

    reg [1:0] state, state_next;

    reg config_stable;
    reg config_en_impl;
    wire config_clk_impl = config_en_impl & clk;
    reg [0:0] config_in_impl;

    // FPGA instantiation
    wire clk_impl = clk;
    wire reset_impl = reset || ~config_stable;
    wire start_impl = start;
    wire [3:0] bcd1_impl = bcd1;
    wire [3:0] bcd0_impl = bcd0;
    wire ready_impl;
    wire done_tick_impl;

    top dut (
        .cfg_clk(config_clk_impl),
        .cfg_e(config_en_impl),
        .cfg_i(config_in_impl),

    	.clk(clk_impl),
    	.IO_LEFT_x0y1_1_extio_i(reset_impl),
    	.IO_LEFT_x0y1_1_extio_o(),
    	.IO_LEFT_x0y1_1_extio_oe(),
    	.IO_LEFT_x0y2_0_extio_i(bcd0_impl[0]),
    	.IO_LEFT_x0y2_0_extio_o(),
    	.IO_LEFT_x0y2_0_extio_oe(),
    	.IO_LEFT_x0y2_1_extio_i(bcd0_impl[1]),
    	.IO_LEFT_x0y2_1_extio_o(),
    	.IO_LEFT_x0y2_1_extio_oe(),
    	.IO_LEFT_x0y3_0_extio_i(bcd0_impl[2]),
    	.IO_LEFT_x0y3_0_extio_o(),
    	.IO_LEFT_x0y3_0_extio_oe(),
    	.IO_LEFT_x0y3_1_extio_i(bcd0_impl[3]),
    	.IO_LEFT_x0y3_1_extio_o(),
    	.IO_LEFT_x0y3_1_extio_oe(),
    	.IO_LEFT_x0y4_0_extio_i(bcd1_impl[0]),
    	.IO_LEFT_x0y4_0_extio_o(),
    	.IO_LEFT_x0y4_0_extio_oe(),
    	.IO_LEFT_x0y4_1_extio_i(bcd1_impl[1]),
    	.IO_LEFT_x0y4_1_extio_o(),
    	.IO_LEFT_x0y4_1_extio_oe(),
    	.IO_LEFT_x0y5_0_extio_i(bcd1_impl[2]),
    	.IO_LEFT_x0y5_0_extio_o(),
    	.IO_LEFT_x0y5_0_extio_oe(),
    	.IO_LEFT_x0y5_1_extio_i(bcd1_impl[3]),
    	.IO_LEFT_x0y5_1_extio_o(),
    	.IO_LEFT_x0y5_1_extio_oe(),
    	.IO_LEFT_x0y6_0_extio_i(),
    	.IO_LEFT_x0y6_0_extio_o(),
    	.IO_LEFT_x0y6_0_extio_oe(),
    	.IO_LEFT_x0y6_1_extio_i(),
    	.IO_LEFT_x0y6_1_extio_o(),
    	.IO_LEFT_x0y6_1_extio_oe(),
    	.IO_BOTTOM_x1y0_0_extio_i(start_impl),
    	.IO_BOTTOM_x1y0_0_extio_o(),
    	.IO_BOTTOM_x1y0_0_extio_oe(),
    	.IO_BOTTOM_x1y0_1_extio_i(),
    	.IO_BOTTOM_x1y0_1_extio_o(),
    	.IO_BOTTOM_x1y0_1_extio_oe(),
    	.IO_TOP_x1y7_0_extio_i(),
    	.IO_TOP_x1y7_0_extio_o(),
    	.IO_TOP_x1y7_0_extio_oe(),
    	.IO_TOP_x1y7_1_extio_i(),
    	.IO_TOP_x1y7_1_extio_o(),
    	.IO_TOP_x1y7_1_extio_oe(),
    	.IO_BOTTOM_x2y0_0_extio_i(),
    	.IO_BOTTOM_x2y0_0_extio_o(),
    	.IO_BOTTOM_x2y0_0_extio_oe(),
    	.IO_BOTTOM_x2y0_1_extio_i(),
    	.IO_BOTTOM_x2y0_1_extio_o(),
    	.IO_BOTTOM_x2y0_1_extio_oe(),
    	.IO_TOP_x2y7_0_extio_i(),
    	.IO_TOP_x2y7_0_extio_o(),
    	.IO_TOP_x2y7_0_extio_oe(),
    	.IO_TOP_x2y7_1_extio_i(),
    	.IO_TOP_x2y7_1_extio_o(),
    	.IO_TOP_x2y7_1_extio_oe(),
    	.IO_BOTTOM_x3y0_0_extio_i(),
    	.IO_BOTTOM_x3y0_0_extio_o(),
    	.IO_BOTTOM_x3y0_0_extio_oe(),
    	.IO_BOTTOM_x3y0_1_extio_i(),
    	.IO_BOTTOM_x3y0_1_extio_o(),
    	.IO_BOTTOM_x3y0_1_extio_oe(),
    	.IO_TOP_x3y7_0_extio_i(),
    	.IO_TOP_x3y7_0_extio_o(),
    	.IO_TOP_x3y7_0_extio_oe(),
    	.IO_TOP_x3y7_1_extio_i(),
    	.IO_TOP_x3y7_1_extio_o(),
    	.IO_TOP_x3y7_1_extio_oe(),
    	.IO_BOTTOM_x4y0_0_extio_i(),
    	.IO_BOTTOM_x4y0_0_extio_o(),
    	.IO_BOTTOM_x4y0_0_extio_oe(),
    	.IO_BOTTOM_x4y0_1_extio_i(),
    	.IO_BOTTOM_x4y0_1_extio_o(),
    	.IO_BOTTOM_x4y0_1_extio_oe(),
    	.IO_TOP_x4y7_0_extio_i(),
    	.IO_TOP_x4y7_0_extio_o(),
    	.IO_TOP_x4y7_0_extio_oe(),
    	.IO_TOP_x4y7_1_extio_i(),
    	.IO_TOP_x4y7_1_extio_o(),
    	.IO_TOP_x4y7_1_extio_oe(),
    	.IO_BOTTOM_x5y0_0_extio_i(),
    	.IO_BOTTOM_x5y0_0_extio_o(),
    	.IO_BOTTOM_x5y0_0_extio_oe(),
    	.IO_BOTTOM_x5y0_1_extio_i(),
    	.IO_BOTTOM_x5y0_1_extio_o(),
    	.IO_BOTTOM_x5y0_1_extio_oe(),
    	.IO_TOP_x5y7_0_extio_i(),
    	.IO_TOP_x5y7_0_extio_o(),
    	.IO_TOP_x5y7_0_extio_oe(),
    	.IO_TOP_x5y7_1_extio_i(),
    	.IO_TOP_x5y7_1_extio_o(),
    	.IO_TOP_x5y7_1_extio_oe(),
    	.IO_BOTTOM_x6y0_0_extio_i(),
    	.IO_BOTTOM_x6y0_0_extio_o(),
    	.IO_BOTTOM_x6y0_0_extio_oe(),
    	.IO_BOTTOM_x6y0_1_extio_i(),
    	.IO_BOTTOM_x6y0_1_extio_o(),
    	.IO_BOTTOM_x6y0_1_extio_oe(),
    	.IO_TOP_x6y7_0_extio_i(),
    	.IO_TOP_x6y7_0_extio_o(),
    	.IO_TOP_x6y7_0_extio_oe(),
    	.IO_TOP_x6y7_1_extio_i(),
    	.IO_TOP_x6y7_1_extio_o(),
    	.IO_TOP_x6y7_1_extio_oe(),
    	.IO_RIGHT_x7y1_0_extio_i(),
    	.IO_RIGHT_x7y1_0_extio_o(ready_impl),
    	.IO_RIGHT_x7y1_0_extio_oe(),
    	.IO_RIGHT_x7y1_1_extio_i(),
    	.IO_RIGHT_x7y1_1_extio_o(done_tick_impl),
    	.IO_RIGHT_x7y1_1_extio_oe(),
    	.IO_RIGHT_x7y2_0_extio_i(),
    	.IO_RIGHT_x7y2_0_extio_o(bin[0]),
    	.IO_RIGHT_x7y2_0_extio_oe(),
    	.IO_RIGHT_x7y2_1_extio_i(),
    	.IO_RIGHT_x7y2_1_extio_o(bin[1]),
    	.IO_RIGHT_x7y2_1_extio_oe(),
    	.IO_RIGHT_x7y3_0_extio_i(),
    	.IO_RIGHT_x7y3_0_extio_o(bin[2]),
    	.IO_RIGHT_x7y3_0_extio_oe(),
    	.IO_RIGHT_x7y3_1_extio_i(),
    	.IO_RIGHT_x7y3_1_extio_o(bin[3]),
    	.IO_RIGHT_x7y3_1_extio_oe(),
    	.IO_RIGHT_x7y4_0_extio_i(),
    	.IO_RIGHT_x7y4_0_extio_o(bin[4]),
    	.IO_RIGHT_x7y4_0_extio_oe(),
    	.IO_RIGHT_x7y4_1_extio_i(),
    	.IO_RIGHT_x7y4_1_extio_o(bin[5]),
    	.IO_RIGHT_x7y4_1_extio_oe(),
    	.IO_RIGHT_x7y5_0_extio_i(),
    	.IO_RIGHT_x7y5_0_extio_o(bin[6]),
    	.IO_RIGHT_x7y5_0_extio_oe(),
    	.IO_RIGHT_x7y5_1_extio_i(),
    	.IO_RIGHT_x7y5_1_extio_o(),
    	.IO_RIGHT_x7y5_1_extio_oe(),
    	.IO_RIGHT_x7y6_0_extio_i(),
    	.IO_RIGHT_x7y6_0_extio_o(),
    	.IO_RIGHT_x7y6_0_extio_oe(),
    	.IO_RIGHT_x7y6_1_extio_i(),
    	.IO_RIGHT_x7y6_1_extio_o(),
    	.IO_RIGHT_x7y6_1_extio_oe()
        );

    // FSM
    always @(posedge clk) begin
        if (reset) begin
            state   <=  INIT;
        end else begin
            state   <=  state_next;
        end
    end

    // FSM next-state logic
    always @* begin
        state_next  =   state;
        case (state)
            INIT: begin
                state_next  =   CONFIG;
            end
            CONFIG: begin
                if (config_shifted + config_width >= total_size) begin
                    state_next  =   CONFIG_DONE;
                end
            end
            CONFIG_DONE: begin
                state_next  =   CONFIG_STABLE;
            end
        endcase
    end

    // FSM output
    always @* begin
        config_stable = state == CONFIG_STABLE;
        config_en_impl = state == CONFIG;
        ready = config_stable && ready_impl;
        done_tick = config_stable && done_tick_impl;
        config_in_impl = config_mem[config_shifted[31:4]][config_shifted[3:0]];
    end

    // sequential logic
    always @(posedge clk) begin
        if (state == CONFIG) begin
            config_shifted  <=  config_shifted + config_width;
        end else begin
            config_shifted  <=  0;
        end
    end

    reg [0:256*8-1] bitstream_memh;

    initial begin
        if (!$value$plusargs("bitstream_memh=%s", bitstream_memh)) begin
            $display("[INFO] Missing required argument: bitstream_memh");
            $finish;
        end

        $readmemh(bitstream_memh, config_mem);
    end

    reg [7:0] config_percentage;

    always @(posedge clk) begin
        if (~reset && state == INIT && state_next == CONFIG) begin
            $display("[INFO] [CONF] Config started");
        end else if (state == CONFIG_DONE) begin
            $display("[INFO] [CONF] Config finished");
        end

        if (state == INIT) begin
            config_percentage   <= 0;
        end else begin
            if (config_shifted * 100 / total_size > config_percentage) begin
                $display("[INFO] [CONF] %3d%% config done", config_percentage);
                config_percentage   <= config_percentage + 1;
            end
        end

    end

endmodule
