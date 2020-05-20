`timescale 1ns/1ps
module sha256_axilite_slave_host (
    input wire sys_clk,
    input wire sys_rst,
    output reg sys_success,
    output reg sys_fail,
    input wire [31:0] cycle_count,

    output reg [0:0]    ACLK,
    output reg [0:0]    ARESETn,

    output reg [0:0]    AWVALID,
    input wire [0:0]    AWREADY,
    output reg [7:0]    AWADDR,
    output reg [2:0]    AWPROT,

    output reg [0:0]    WVALID,
    input wire [0:0]    WREADY,
    output reg [3:0]    WSTRB,
    output reg [31:0]   WDATA,

    output reg [0:0]    BREADY,
    input wire [0:0]    BVALID,
    input wire [1:0]    BRESP,

    output reg [0:0]    ARVALID,
    input wire [0:0]    ARREADY,
    output reg [7:0]    ARADDR,
    output reg [2:0]    ARPROT,

    output reg [0:0]    RREADY,
    input wire [0:0]    RVALID,
    input wire [31:0]   RDATA,
    input wire [1:0]    RRESP
    );

    reg [3:0]   block_cnt   [0:2];
    reg [511:0] blocks      [0:2][0:8];
    reg [255:0] expected    [0:2];

    initial begin
        sys_success ='b0;
        sys_fail = 'b0;

        block_cnt[0] = 1;
        blocks[0][0] = 512'h61626380000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000018;
        expected[0] = 256'hBA7816BF8F01CFEA414140DE5DAE2223B00361A396177A9CB410FF61F20015AD;

        block_cnt[1] = 2;
        blocks[1][0] = 512'h6162636462636465636465666465666765666768666768696768696A68696A6B696A6B6C6A6B6C6D6B6C6D6E6C6D6E6F6D6E6F706E6F70718000000000000000;
        blocks[1][1] = 512'h000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001C0;
        expected[1] = 256'h248D6A61D20638B8E5C026930C3E6039A33CE45964FF2167F6ECEDD419DB06C1;

        block_cnt[2] = 9;
        blocks[2][0] = 512'h6b900001_496e2074_68652061_72656120_6f662049_6f542028_496e7465_726e6574_206f6620_5468696e_6773292c_206d6f72_6520616e_64206d6f_7265626f_6f6d2c20;
        blocks[2][1] = 512'h69742068_61732062_65656e20_6120756e_69766572_73616c20_636f6e73_656e7375_73207468_61742064_61746120_69732074_69732061_206e6577_20746563_686e6f6c;
        blocks[2][2] = 512'h6f677920_74686174_20696e74_65677261_74657320_64656365_6e747261_6c697a61_74696f6e_2c496e20_74686520_61726561_206f6620_496f5420_28496e74_65726e65;
        blocks[2][3] = 512'h74206f66_20546869_6e677329_2c206d6f_72652061_6e64206d_6f726562_6f6f6d2c_20697420_68617320_6265656e_20612075_6e697665_7273616c_20636f6e_73656e73;
        blocks[2][4] = 512'h75732074_68617420_64617461_20697320_74697320_61206e65_77207465_63686e6f_6c6f6779_20746861_7420696e_74656772_61746573_20646563_656e7472_616c697a;
        blocks[2][5] = 512'h6174696f_6e2c496e_20746865_20617265_61206f66_20496f54_2028496e_7465726e_6574206f_66205468_696e6773_292c206d_6f726520_616e6420_6d6f7265_626f6f6d;
        blocks[2][6] = 512'h2c206974_20686173_20626565_6e206120_756e6976_65727361_6c20636f_6e73656e_73757320_74686174_20646174_61206973_20746973_2061206e_65772074_6563686e;
        blocks[2][7] = 512'h6f6c6f67_79207468_61742069_6e746567_72617465_73206465_63656e74_72616c69_7a617469_6f6e2c49_6e207468_65206172_6561206f_6620496f_54202849_6e746572;
        blocks[2][8] = 512'h6e657420_6f662054_68696e67_73292c20_6d6f7265_20616e64_206d6f72_65800000_00000000_00000000_00000000_00000000_00000000_00000000_00000000_000010e8;
        expected[2] = 256'h7758a30bbdfc9cd92b284b05e9be9ca3d269d3d149e7e82ab4a9ed5e81fbcf9d;
    end

    reg [1:0]   test_ctr, test_ctr_next;
    reg [3:0]   block_ctr, block_ctr_next;
    reg [4:0]   word_ctr, word_ctr_next;
    reg [255:0] calculated;
    reg         update_calculated;

    localparam  ST_RESET        = 4'h0,
                ST_BLOCK        = 4'h1,
                ST_PROGRESS     = 4'h2,
                ST_DONE         = 4'h3,
                ST_DIGEST       = 4'h4,
                ST_CHECK        = 4'h5,
                ST_SUCCESS      = 4'h6,
                ST_FAIL         = 4'h7;

    reg [3:0]   state, state_next;
    reg         waddr_sent, waddr_sent_next, wdata_sent, wdata_sent_next, raddr_sent, raddr_sent_next;

    always @(posedge sys_clk) begin
        if (sys_rst) begin
            state       <= ST_RESET;
            test_ctr    <= 'b0;
            block_ctr   <= 'b0;
            word_ctr    <= 'b0;
            calculated  <= 'b0;
            waddr_sent  <= 'b0;
            wdata_sent  <= 'b0;
            raddr_sent  <= 'b0;
        end else begin
            state       <= state_next;
            test_ctr    <= test_ctr_next;
            block_ctr   <= block_ctr_next;
            word_ctr    <= word_ctr_next;

            if (update_calculated) begin
                calculated[word_ctr * 32 +: 32] <= RDATA;
            end

            waddr_sent  <= waddr_sent_next;
            wdata_sent  <= wdata_sent_next;
            raddr_sent  <= raddr_sent_next;
        end
    end

    always @* begin
        test_ctr_next = test_ctr;
        block_ctr_next = block_ctr;
        word_ctr_next = word_ctr;
        update_calculated = 'b0;
        state_next = state;
        waddr_sent_next = waddr_sent;
        wdata_sent_next = wdata_sent;
        raddr_sent_next = raddr_sent;

        AWVALID = 'b0;
        AWADDR = 'b0;
        WVALID = 'b0;
        WDATA = 'b0;
        BREADY = 'b0;
        ARVALID = 'b0;
        ARADDR = 'b0;
        RREADY = 'b0;

        case (state)
            ST_RESET: begin
                state_next = ST_BLOCK;
            end
            ST_BLOCK: begin
                if (word_ctr < 16) begin
                    if (~waddr_sent) begin
                        AWVALID = 'b1;
                        AWADDR = 8'h00 + (word_ctr << 2);

                        waddr_sent_next = AWREADY;
                    end

                    if (~wdata_sent) begin
                        WVALID = 'b1;
                        WDATA = blocks[test_ctr][block_ctr][word_ctr * 32 +: 32];

                        wdata_sent_next = WREADY;
                    end
                end

                if (waddr_sent_next && wdata_sent_next) begin
                    BREADY = 'b1;

                    if (BVALID) begin
                        waddr_sent_next = 'b0;
                        wdata_sent_next = 'b0;

                        if (word_ctr == 15) begin
                            word_ctr_next = 'b0;
                            state_next = ST_PROGRESS;
                        end else begin
                            word_ctr_next = word_ctr + 1;
                        end
                    end
                end
            end
            ST_PROGRESS: begin
                if (~raddr_sent) begin
                    ARVALID = 'b1;
                    ARADDR = 8'h64;

                    raddr_sent_next = ARREADY;
                end else begin
                    RREADY = 'b1;

                    if (RVALID) begin
                        raddr_sent_next = 'b0;

                        if (|RDATA) begin
                            if (block_ctr == block_cnt[test_ctr] - 1) begin
                                block_ctr_next = 'b0;
                                state_next = ST_DONE;
                            end else begin
                                block_ctr_next = block_ctr + 1;
                                state_next = ST_BLOCK;
                            end
                        end
                    end
                end
            end
            ST_DONE: begin
                if (~raddr_sent) begin
                    ARVALID = 'b1;
                    ARADDR = 8'h68;

                    raddr_sent_next = ARREADY;
                end else begin
                    RREADY = 'b1;

                    if (RVALID) begin
                        raddr_sent_next = 'b0;

                        if (|RDATA) begin
                            state_next = ST_DIGEST;
                        end
                    end
                end
            end
            ST_DIGEST: begin
                if (~raddr_sent) begin
                    ARVALID = 'b1;
                    ARADDR = 8'h40 + (word_ctr << 2);

                    raddr_sent_next = ARREADY;
                end else begin
                    RREADY = 'b1;

                    if (RVALID) begin
                        raddr_sent_next = 'b0;
                        update_calculated = 'b1;

                        if (word_ctr == 7) begin
                            word_ctr_next = 'b0;
                            state_next = ST_CHECK;
                        end else begin
                            word_ctr_next = word_ctr + 1;
                        end
                    end
                end
            end
            ST_CHECK: begin
                if (calculated != expected[test_ctr]) begin
                    state_next = ST_FAIL;
                end else if (test_ctr == 2) begin
                    state_next = ST_SUCCESS;
                end else begin
                    test_ctr_next = test_ctr + 1;
                    state_next = ST_BLOCK;
                end
            end
        endcase
    end

    always @* begin
        ACLK = sys_clk;
        ARESETn = ~sys_rst;
        AWPROT = 'b0;
        WSTRB = 4'hF;
        ARPROT = 'b0;

        sys_success = state == ST_SUCCESS;
        sys_fail = state == ST_FAIL;
    end

endmodule
