`timescale 1ns/1ps
module sha256_axilite_slave (
    input wire [0:0]    ACLK,
    input wire [0:0]    ARESETn,

    input wire [0:0]    AWVALID,
    output reg [0:0]    AWREADY,
    input wire [7:0]    AWADDR,
    input wire [2:0]    AWPROT,

    input wire [0:0]    WVALID,
    output reg [0:0]    WREADY,
    input wire [3:0]    WSTRB,
    input wire [31:0]   WDATA,

    input wire [0:0]    BREADY,
    output reg [0:0]    BVALID,
    output reg [1:0]    BRESP,

    input wire [0:0]    ARVALID,
    output reg [0:0]    ARREADY,
    input wire [7:0]    ARADDR,
    input wire [2:0]    ARPROT,

    input wire [0:0]    RREADY,
    output reg [0:0]    RVALID,
    output reg [31:0]   RDATA,
    output reg [1:0]    RRESP
    );

    // channel frontends
    reg [7:0] awaddr_f, araddr_f;
    reg [3:0] wstrb_f;
    reg [31:0] wdata_f, rdata;
    reg [1:0] bresp, rresp;
    reg awaddr_val, awaddr_stall, wdata_val, wdata_stall, bresp_val, bresp_stall;
    reg araddr_val, araddr_stall, rresp_val, rresp_stall;

    always @(posedge ACLK) begin
        if (~ARESETn) begin
            awaddr_f    <= 'b0;
            awaddr_val  <= 'b0;
            wstrb_f     <= 'b0;
            wdata_f     <= 'b0;
            wdata_val   <= 'b0;
            araddr_f    <= 'b0;
            araddr_val  <= 'b0;
            BVALID      <= 'b0;
            BRESP       <= 'b0;
            RVALID      <= 'b0;
            RDATA       <= 'b0;
            RRESP       <= 'b0;
        end else begin
            if (AWVALID && AWREADY) begin
                awaddr_f    <= AWADDR;
                awaddr_val  <= 'b1;
            end else if (~awaddr_stall) begin
                awaddr_val  <= 'b0;
            end

            if (WVALID && WREADY) begin
                wstrb_f     <= WSTRB;
                wdata_f     <= WDATA;
                wdata_val   <= 'b1;
            end else if (~wdata_stall) begin
                wdata_val   <= 'b0;
            end

            if (bresp_val) begin
                BVALID      <= 'b1;
                BRESP       <= bresp;
            end else if (~bresp_stall) begin
                BVALID      <= 'b0;
            end

            if (ARVALID && ARREADY) begin
                araddr_f    <= ARADDR;
                araddr_val  <= 'b1;
            end else if (~araddr_stall) begin
                araddr_val  <= 'b0;
            end

            if (rresp_val) begin
                RVALID      <= 'b1;
                RDATA       <= rdata;
                RRESP       <= rresp;
            end else if (~rresp_stall) begin
                RVALID      <= 'b0;
            end
        end
    end

    always @* begin
        AWREADY = ~awaddr_val || ~awaddr_stall;
        WREADY = ~wdata_val || ~wdata_stall;
        ARREADY = ~araddr_val || ~araddr_stall;
        bresp_stall = BVALID && ~BREADY;
        rresp_stall = RVALID && ~RREADY;
    end

    localparam  ADDR_BLOCK0     = 8'h00,
                ADDR_BLOCK60    = 8'h3c,
                ADDR_DIGEST0    = 8'h40,
                ADDR_DIGEST28   = 8'h5c,
                ADDR_RESET      = 8'h60,    // write to this address to soft reset the core
                ADDR_PROCEED    = 8'h64,    // read this address to signal that block is ready for use
                                            // if it returns 1, the block data are registered and
                                            // it's safe to write the next block. otherwise the user
                                            // must keep trying until it returns 1
                ADDR_DONE       = 8'h68,    // read this address to signal the end of block stream.
                                            // if it returns 1, the digest is valid for read. the core
                                            // is also automatically reset in this case (the digest will
                                            // remain valid until the user reads ADDR_PROCEED again)
                ADDR_SIGNATURE0 = 8'hF8,
                ADDR_SIGNATURE1 = 8'hFC;    // 2 32-bit signatures to check if the core is present

    localparam  SIGNATURE1      = 32'h73686132,     // "sha2"
                SIGNATURE0      = 32'h35360000;     // "56\0\0"

    reg init, next;
    wire ready, digest_valid;
    reg [511:0]         block;
    wire [255:0]        digest;

    sha256_core core (
        .clk                (ACLK)
        ,.reset_n           (ARESETn)
        ,.init              (init)
        ,.next              (next)
        ,.mode              (1)
        ,.block             (block)
        ,.ready             (ready)
        ,.digest            (digest)
        ,.digest_valid      (digest_valid)
        );

    reg first_n;

    always @(posedge ACLK) begin
        if (~ARESETn) begin
            block <= 'b0;
            first_n <= 'b0;
        end else begin
            if (awaddr_val && wdata_val && ~bresp_stall) begin
                case (awaddr_f)
                    8'h00, 8'h04, 8'h08, 8'h0C,
                    8'h10, 8'h14, 8'h18, 8'h1C,
                    8'h20, 8'h24, 8'h28, 8'h2C,
                    8'h30, 8'h34, 8'h38, 8'h3C: begin
                        if (wstrb_f[0]) begin
                            block[awaddr_f[5:2] * 32      +: 8] <= wdata_f[0  +: 8];
                        end

                        if (wstrb_f[1]) begin
                            block[awaddr_f[5:2] * 32 +  8 +: 8] <= wdata_f[8  +: 8];
                        end

                        if (wstrb_f[2]) begin
                            block[awaddr_f[5:2] * 32 + 16 +: 8] <= wdata_f[16 +: 8];
                        end

                        if (wstrb_f[3]) begin
                            block[awaddr_f[5:2] * 32 + 24 +: 8] <= wdata_f[24 +: 8];
                        end
                    end
                endcase
            end

            if (awaddr_val && wdata_val && ~bresp_stall && awaddr_f == ADDR_RESET) begin
                first_n <= 'b0;
            end else if (araddr_val && ~rresp_stall) begin
                case (araddr_f)
                    ADDR_PROCEED: if (ready) begin
                        first_n <= 'b1;
                    end
                    ADDR_DONE: if (digest_valid) begin
                        first_n <= 'b0;
                    end
                endcase
            end
        end
    end

    always @* begin
        awaddr_stall = bresp_stall || (wdata_val && ~awaddr_val);
        wdata_stall = bresp_stall || (awaddr_val && ~wdata_val);
        araddr_stall = 'b0;
        bresp = 'b0;
        bresp_val = awaddr_val && wdata_val && ~bresp_stall;
        rresp = 'b0;
        rdata = 'b0;
        rresp_val = araddr_val && ~rresp_stall;
        init = 'b0;
        next = 'b0;

        if (araddr_val && ~rresp_stall) begin
            case (araddr_f)
                8'h00, 8'h04, 8'h08, 8'h0C,
                8'h10, 8'h14, 8'h18, 8'h1C,
                8'h20, 8'h24, 8'h28, 8'h2C,
                8'h30, 8'h34, 8'h38, 8'h3C: begin
                    rdata = block[araddr_f[5:2] * 32 +: 32];
                end
                8'h40, 8'h44, 8'h48, 8'h4C,
                8'h50, 8'h54, 8'h58, 8'h5C: begin
                    rdata = digest[araddr_f[5:2] * 32 +: 32];
                end
                ADDR_PROCEED: begin
                    rdata = {32{ready}};
                    init = !first_n;
                    next = first_n;
                end
                ADDR_DONE: begin
                    rdata = {32{digest_valid}};
                end
                ADDR_SIGNATURE0: begin
                    rdata = SIGNATURE0;
                end
                ADDR_SIGNATURE1: begin
                    rdata = SIGNATURE1;
                end
            endcase
        end
    end

endmodule
