module gate (
    input wire clk,
    input wire reset,
    input wire a,
    input wire b,
    output reg ready,
    output wire c
    );

    localparam  config_width    =   1,
                total_size      =   115;

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

    wire reset_impl = reset || ~config_stable;
    wire a_impl = a;
    wire b_impl = b;
    wire ready_impl;

    top dut (
    	.clk(clk),
    	.IO_LEFT_x0y2_0_extio_i(reset_impl),
    	.IO_LEFT_x0y2_0_extio_o(),
    	.IO_LEFT_x0y2_0_extio_oe(),
    	.IO_BOTTOM_x1y0_0_extio_i(a_impl),
    	.IO_BOTTOM_x1y0_0_extio_o(),
    	.IO_BOTTOM_x1y0_0_extio_oe(),
    	.IO_TOP_x1y3_0_extio_i(),
    	.IO_TOP_x1y3_0_extio_o(ready_impl),
    	.IO_TOP_x1y3_0_extio_oe(),
    	.IO_BOTTOM_x2y0_0_extio_i(b_impl),
    	.IO_BOTTOM_x2y0_0_extio_o(),
    	.IO_BOTTOM_x2y0_0_extio_oe(),
    	.IO_TOP_x2y3_0_extio_i(),
    	.IO_TOP_x2y3_0_extio_o(),
    	.IO_TOP_x2y3_0_extio_oe(),
    	.IO_RIGHT_x3y1_0_extio_i(),
    	.IO_RIGHT_x3y1_0_extio_o(c),
    	.IO_RIGHT_x3y1_0_extio_oe(),
    	.IO_RIGHT_x3y2_0_extio_i(),
    	.IO_RIGHT_x3y2_0_extio_o(),
    	.IO_RIGHT_x3y2_0_extio_oe(),
    	.cfg_clk(config_clk_impl),
    	.cfg_e(config_en_impl),
    	.cfg_i(config_in_impl)
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
        config_in_impl = config_mem[config_shifted[31:4]][config_shifted[3:0]];
        ready = config_stable && ready_impl;
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
