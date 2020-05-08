module prga_fifo_tb ();

    localparam DATA_WIDTH = 8;

    reg clk, rst;

    reg [DATA_WIDTH - 1:0] src [0:1023];

    initial begin
        clk = 'b0;
        rst = 'b0;

        src[0] = 'h5A;
        src[1] = 'hF6;
        src[2] = 'h09;
        src[3] = 'hC4;
        src[4] = 'h81;
        src[5] = 'hE2;
        src[6] = 'hA0;
        src[7] = 'h7A;

        $dumpfile("dump.vcd");
        $dumpvars;

        #3;
        rst = 'b1;
        #10;
        rst = 'b0;

        #10000;
        $display("[TIMEOUT]");
        $finish;
    end

    always #5 clk = ~clk;

    // A: non-lookahead
    // B: lookahead converted to non-lookahead
    // C: lookahead
    // D: non-lookahead converted to lookahead

    wire A_full, A_empty, B_full, B_empty, C_full, C_empty, D_full, D_empty;
    wire [DATA_WIDTH - 1:0] A_dout, B_dout, C_dout, D_dout;
    reg A_valid, A_rd, B_valid, B_rd, C_rd, D_rd;
    integer A_wr_cnt, B_wr_cnt, C_wr_cnt, D_wr_cnt;
    integer A_rd_cnt, B_rd_cnt, C_rd_cnt, D_rd_cnt;
    wire _B_empty, _B_rd, _D_empty, _D_rd;
    wire [DATA_WIDTH - 1:0] _B_dout, _D_dout;

    prga_fifo #(
        .DATA_WIDTH                     (DATA_WIDTH)
        ,.LOOKAHEAD                     (0)
    ) A (
        .clk        (clk)
        ,.rst       (rst)
        ,.full      (A_full)
        ,.wr        (src[A_wr_cnt] !== {DATA_WIDTH{1'bx}})
        ,.din       (src[A_wr_cnt])
        ,.empty     (A_empty)
        ,.rd        (A_rd)
        ,.dout      (A_dout)
        );

    prga_fifo #(
        .DATA_WIDTH                     (DATA_WIDTH)
        ,.LOOKAHEAD                     (1)
    ) B (
        .clk        (clk)
        ,.rst       (rst)
        ,.full      (B_full)
        ,.wr        (src[B_wr_cnt] !== {DATA_WIDTH{1'bx}})
        ,.din       (src[B_wr_cnt])
        ,.empty     (_B_empty)
        ,.rd        (_B_rd)
        ,.dout      (_B_dout)
        );

    prga_fifo_lookahead_buffer #(
        .DATA_WIDTH                     (DATA_WIDTH)
        ,.REVERSED                      (1)
    ) B_buffer (
        .clk        (clk)
        ,.rst       (rst)
        ,.empty_i   (_B_empty)
        ,.rd_i      (_B_rd)
        ,.dout_i    (_B_dout)
        ,.empty     (B_empty)
        ,.rd        (B_rd)
        ,.dout      (B_dout)
        );

    prga_fifo #(
        .DATA_WIDTH                     (DATA_WIDTH)
        ,.LOOKAHEAD                     (1)
    ) C (
        .clk        (clk)
        ,.rst       (rst)
        ,.full      (C_full)
        ,.wr        (src[C_wr_cnt] !== {DATA_WIDTH{1'bx}})
        ,.din       (src[C_wr_cnt])
        ,.empty     (C_empty)
        ,.rd        (C_rd)
        ,.dout      (C_dout)
        );

    prga_fifo #(
        .DATA_WIDTH                     (DATA_WIDTH)
        ,.LOOKAHEAD                     (0)
    ) D (
        .clk        (clk)
        ,.rst       (rst)
        ,.full      (D_full)
        ,.wr        (src[D_wr_cnt] !== {DATA_WIDTH{1'bx}})
        ,.din       (src[D_wr_cnt])
        ,.empty     (_D_empty)
        ,.rd        (_D_rd)
        ,.dout      (_D_dout)
        );

    prga_fifo_lookahead_buffer #(
        .DATA_WIDTH                     (DATA_WIDTH)
        ,.REVERSED                      (0)
    ) D_buffer (
        .clk        (clk)
        ,.rst       (rst)
        ,.empty_i   (_D_empty)
        ,.rd_i      (_D_rd)
        ,.dout_i    (_D_dout)
        ,.empty     (D_empty)
        ,.rd        (D_rd)
        ,.dout      (D_dout)
        );

    reg error;

    always @(posedge clk) begin
        if (rst) begin
            A_wr_cnt <= 0;
            B_wr_cnt <= 0;
            C_wr_cnt <= 0;
            D_wr_cnt <= 0;
            A_rd_cnt <= 0;
            B_rd_cnt <= 0;
            C_rd_cnt <= 0;
            D_rd_cnt <= 0;
            A_valid <= 'b0;
            A_rd <= 'b0;
            B_valid <= 'b0;
            B_rd <= 'b0;
            C_rd <= 'b0;
            D_rd <= 'b0;
            error <= 'b0;
        end else begin
            if (!A_full && src[A_wr_cnt] !== {DATA_WIDTH{1'bx}}) begin
                A_wr_cnt <= A_wr_cnt + 1;
            end

            if (!B_full && src[B_wr_cnt] !== {DATA_WIDTH{1'bx}}) begin
                B_wr_cnt <= B_wr_cnt + 1;
            end

            if (!C_full && src[C_wr_cnt] !== {DATA_WIDTH{1'bx}}) begin
                C_wr_cnt <= C_wr_cnt + 1;
            end

            if (!D_full && src[D_wr_cnt] !== {DATA_WIDTH{1'bx}}) begin
                D_wr_cnt <= D_wr_cnt + 1;
            end

            A_valid <= !A_empty && A_rd;
            
            if (A_valid) begin
                if (src[A_rd_cnt] !== A_dout) begin
                    error <= 'b1;
                    $display("[ERROR] A output No. %d 0x%08x != 0x%08x", A_rd_cnt, A_dout, src[A_rd_cnt]);
                end
                A_rd_cnt <= A_rd_cnt + 1;
            end

            B_valid <= !B_empty && B_rd;
            
            if (B_valid) begin
                if (src[B_rd_cnt] !== B_dout) begin
                    error <= 'b1;
                    $display("[ERROR] B output No. %d 0x%08x != 0x%08x", B_rd_cnt, B_dout, src[B_rd_cnt]);
                end
                B_rd_cnt <= B_rd_cnt + 1;
            end

            if (!C_empty && C_rd) begin
                if (src[C_rd_cnt] !== C_dout) begin
                    error <= 'b1;
                    $display("[ERROR] C output No. %d 0x%08x != 0x%08x", C_rd_cnt, C_dout, src[C_rd_cnt]);
                end
                C_rd_cnt <= C_rd_cnt + 1;
            end

            if (!D_empty && D_rd) begin
                if (src[D_rd_cnt] !== D_dout) begin
                    error <= 'b1;
                    $display("[ERROR] D output No. %d 0x%08x != 0x%08x", D_rd_cnt, D_dout, src[D_rd_cnt]);
                end
                D_rd_cnt <= D_rd_cnt + 1;
            end

            A_rd <= $random() % 3 == 0;
            B_rd <= $random() % 3 == 0;
            C_rd <= $random() % 3 == 0;
            D_rd <= $random() % 3 == 0;

            if (src[A_rd_cnt] === {DATA_WIDTH{1'bx}} &&
                src[B_rd_cnt] === {DATA_WIDTH{1'bx}} &&
                src[C_rd_cnt] === {DATA_WIDTH{1'bx}} &&
                src[D_rd_cnt] === {DATA_WIDTH{1'bx}}) begin
                if (error) begin
                    $display("[FAIL]");
                end else begin
                    $display("[PASS]");
                end
                $finish;
            end
        end
    end

endmodule
