`timescale 1ns/1ps
module sha256_ureg (
    input wire                                  clk,
    input wire                                  rst_n,

    output reg                                  ureg_req_rdy,
    input wire                                  ureg_req_val,
    input wire [11:0]                           ureg_req_addr,
    input wire [7:0]                            ureg_req_strb,
    input wire [63:0]                           ureg_req_data,

    input wire                                  ureg_resp_rdy,
    output reg                                  ureg_resp_val,
    output reg [63:0]                           ureg_resp_data,
    output reg                                  ureg_resp_ecc
    );

    reg req_val_f;
    reg [11:0] req_addr_f;
    reg [7:0] req_strb_f;
    reg [63:0] req_data_f;

    always @(posedge clk) begin
        if (~rst_n) begin
            req_val_f <= 1'b0;
            req_addr_f <= 12'h0;
            req_strb_f <= 8'h0;
            req_data_f <= 64'h0;
        end else if (ureg_req_rdy) begin
            req_val_f <= ureg_req_val;
            req_addr_f <= ureg_req_addr;
            req_strb_f <= ureg_req_strb;
            req_data_f <= ureg_req_data;
        end
    end

    reg resp_val, resp_stall;
    reg [63:0] resp_data;

    always @(posedge clk) begin
        if (~rst_n) begin
            ureg_resp_val   <= 1'b0;
            ureg_resp_data  <= 64'b0;
            ureg_resp_ecc   <= 1'b0;
        end if (~resp_stall) begin
            ureg_resp_val   <= resp_val;
            ureg_resp_data  <= resp_data;
            ureg_resp_ecc   <= ~^resp_data;
        end
    end

    always @* begin
        resp_stall = ureg_resp_val && ~ureg_resp_rdy;
        ureg_req_rdy = ~resp_stall;
    end

    localparam  ADDR_BLOCK0     = 12'h00,
                ADDR_BLOCK56    = 12'h38,
                ADDR_DIGEST0    = 12'h40,
                ADDR_DIGEST24   = 12'h58,
                ADDR_RESET      = 12'h60,   // write to this address to soft reset the core
                ADDR_PROCEED    = 12'h68,   // read this address to signal that block is ready for use
                                            // if it returns 1, the block data are registered and
                                            // it's safe to write the next block. otherwise the user
                                            // must keep trying until it returns 1
                ADDR_DONE       = 12'h70,   // read this address to signal the end of block stream.
                                            // if it returns 1, the digest is valid for read. the core
                                            // is also automatically reset in this case (the digest will
                                            // remain valid until the user reads ADDR_PROCEED again)
                ADDR_SIGNATURE  = 12'hF8;   // signature value to check if the core is present

    localparam  SIGNATURE       = 64'h73686132_35360000;        // "sha256\0\0"

    reg init, next;
    wire ready, digest_valid;
    reg [511:0]         block;
    wire [255:0]        digest;

    sha256_core core (
        .clk                (clk)
        ,.reset_n           (rst_n)
        ,.init              (init)
        ,.next              (next)
        ,.mode              (1)
        ,.block             (block)
        ,.ready             (ready)
        ,.digest            (digest)
        ,.digest_valid      (digest_valid)
        );

    reg first_n;

    always @(posedge clk) begin
        if (~rst_n) begin
            block   <= 512'b0;
            first_n <= 1'b0;
        end else begin
            if (req_val_f && ~resp_stall && |req_strb_f) begin
                case (req_addr_f)
                    12'h00, 12'h08, 12'h10, 12'h18, 12'h20, 12'h28, 12'h30, 12'h38: begin
                        block[req_addr_f[5:3] * 64     +: 64]    <= req_data_f;
                    end
                endcase
            end

            if (req_val_f && ~resp_stall && req_addr_f == ADDR_RESET && |req_strb_f) begin
                first_n <= 1'b0;
            end else if (req_val_f && ~resp_stall && ~|req_strb_f) begin
                case (req_addr_f)
                    ADDR_PROCEED: if (ready) begin
                        first_n     <= 1'b1;
                    end
                    ADDR_DONE: if (digest_valid) begin
                        first_n     <= 1'b0;
                    end
                endcase
            end
        end
    end

    always @* begin
        resp_val = 1'b0;
        resp_data = 64'h0;
        init = 1'b0;
        next = 1'b0;

        if (req_val_f) begin
            resp_val = 1'b1;

            if (~|req_strb_f) begin
                case (req_addr_f)
                    12'h00, 12'h08, 12'h10, 12'h18, 12'h20, 12'h28, 12'h30, 12'h38: begin
                        resp_data = block[req_addr_f[5:3] * 64 +: 64];
                    end
                    12'h40, 12'h48, 12'h50, 12'h58: begin
                        resp_data = digest[req_addr_f[4:3] * 64 +: 64];
                    end
                    ADDR_PROCEED: begin
                        resp_data = {64{ready}};
                        init = !first_n;
                        next = first_n;
                    end
                    ADDR_DONE: begin
                        resp_data = {64{digest_valid}};
                    end
                    ADDR_SIGNATURE: begin
                        resp_data = SIGNATURE;
                    end
                endcase
            end
        end
    end

endmodule
