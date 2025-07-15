module \$add (A, B, Y);

    parameter A_SIGNED = 0;
    parameter B_SIGNED = 0;
    parameter A_WIDTH = 1;
    parameter B_WIDTH = 1;
    parameter Y_WIDTH = 1;

    input [A_WIDTH-1:0] A;
    input [B_WIDTH-1:0] B;
    output [Y_WIDTH-1:0] Y;

    wire _TECHMAP_FAIL_ = Y_WIDTH <= 2;

    wire [Y_WIDTH-1:0] A_buf, B_buf;
    \$pos #(.A_SIGNED(A_SIGNED), .A_WIDTH(A_WIDTH), .Y_WIDTH(Y_WIDTH)) A_conv (.A(A), .Y(A_buf));
    \$pos #(.A_SIGNED(B_SIGNED), .A_WIDTH(B_WIDTH), .Y_WIDTH(Y_WIDTH)) B_conv (.A(B), .Y(B_buf));

    wire [Y_WIDTH-1:0] CARRY;

    m_xor2 #(.CIN_MODE(2'b00)) cc_first (.a(A_buf[0]), .b(B_buf[0]), .s(Y[0]), .cout(CARRY[0]));

    genvar i;
    generate for (i = 1; i < Y_WIDTH; i = i + 1) begin
        m_xor2 #(.CIN_MODE(2'b10)) cc (.a(A_buf[i]), .b(B_buf[i]), .cin(CARRY[i-1]), .s(Y[i]), .cout(CARRY[i]));
    end endgenerate

endmodule

module \$sub (A, B, Y);

    parameter A_SIGNED = 0;
    parameter B_SIGNED = 0;
    parameter A_WIDTH = 1;
    parameter B_WIDTH = 1;
    parameter Y_WIDTH = 1;

    input [A_WIDTH-1:0] A;
    input [B_WIDTH-1:0] B;
    output [Y_WIDTH-1:0] Y;

    wire _TECHMAP_FAIL_ = Y_WIDTH <= 2;

    wire [Y_WIDTH-1:0] A_buf, B_buf;
    \$pos #(.A_SIGNED(A_SIGNED), .A_WIDTH(A_WIDTH), .Y_WIDTH(Y_WIDTH)) A_conv (.A(A), .Y(A_buf));
    \$pos #(.A_SIGNED(B_SIGNED), .A_WIDTH(B_WIDTH), .Y_WIDTH(Y_WIDTH)) B_conv (.A(B), .Y(B_buf));

    wire [Y_WIDTH-1:0] CARRY;

    m_xor2 #(.CIN_MODE(2'b01)) cc_first (.a(A_buf[0]), .b(~B_buf[0]), .s(Y[0]), .cout(CARRY[0]));

    genvar i;
    generate for (i = 1; i < Y_WIDTH; i = i + 1) begin
        m_xor2 #(.CIN_MODE(2'b10)) cc (.a(A_buf[i]), .b(~B_buf[i]), .cin(CARRY[i-1]), .s(Y[i]), .cout(CARRY[i]));
    end endgenerate

endmodule

module _cmp_ (A, B, Y);
    // calculates A - B, set Y to 1'b1 if A < B
    parameter A_SIGNED = 0;
    parameter B_SIGNED = 0;
    parameter A_WIDTH = 1;
    parameter B_WIDTH = 1;

    input [A_WIDTH-1:0] A;
    input [B_WIDTH-1:0] B;
    output Y;

    localparam  MAX_AB_WIDTH = A_WIDTH > B_WIDTH ? A_WIDTH : B_WIDTH; 

    wire [MAX_AB_WIDTH:0] A_buf, B_buf;
    \$pos #(.A_SIGNED(A_SIGNED), .A_WIDTH(A_WIDTH), .Y_WIDTH(MAX_AB_WIDTH+1)) A_conv (.A(A), .Y(A_buf));
    \$pos #(.A_SIGNED(B_SIGNED), .A_WIDTH(B_WIDTH), .Y_WIDTH(MAX_AB_WIDTH+1)) B_conv (.A(B), .Y(B_buf));

    wire [MAX_AB_WIDTH-1:0] CARRY;

    m_xor2 #(.CIN_MODE(2'b01)) cc_first (.a(A_buf[0]), .b(~B_buf[0]), .cout(CARRY[0]));

    genvar i;
    generate for (i = 1; i < MAX_AB_WIDTH; i = i + 1) begin
        m_xor2 #(.CIN_MODE(2'b10)) cc (.a(A_buf[i]), .b(~B_buf[i]), .cin(CARRY[i-1]), .cout(CARRY[i]));
    end endgenerate

    m_xor2 #(.CIN_MODE(2'b10)) cc_last (.a(A_buf[MAX_AB_WIDTH]), .b(~B_buf[MAX_AB_WIDTH]), .cin(CARRY[MAX_AB_WIDTH-1]), .s(Y));

endmodule

module \$lt (A, B, Y);

    parameter A_SIGNED = 0;
    parameter B_SIGNED = 0;
    parameter A_WIDTH = 1;
    parameter B_WIDTH = 1;
    parameter Y_WIDTH = 1;

    input [A_WIDTH-1:0] A;
    input [B_WIDTH-1:0] B;
    output [Y_WIDTH-1:0] Y;

    wire cmp_o;

    _cmp_ #(.A_SIGNED(A_SIGNED), .B_SIGNED(B_SIGNED), .A_WIDTH(A_WIDTH), .B_WIDTH(B_WIDTH)) i_cmp (.A(A), .B(B), .Y(cmp_o));

    generate if (Y_WIDTH > 1) begin
        assign Y = { {(Y_WIDTH - 1) {1'b0} }, cmp_o };
    end else begin
        assign Y = cmp_o;
    end endgenerate

endmodule

module \$gt (A, B, Y);

    parameter A_SIGNED = 0;
    parameter B_SIGNED = 0;
    parameter A_WIDTH = 1;
    parameter B_WIDTH = 1;
    parameter Y_WIDTH = 1;

    input [A_WIDTH-1:0] A;
    input [B_WIDTH-1:0] B;
    output [Y_WIDTH-1:0] Y;

    wire cmp_o;

    _cmp_ #(.A_SIGNED(B_SIGNED), .B_SIGNED(A_SIGNED), .A_WIDTH(B_WIDTH), .B_WIDTH(A_WIDTH)) i_cmp (.A(B), .B(A), .Y(cmp_o));

    generate if (Y_WIDTH > 1) begin
        assign Y = { {(Y_WIDTH - 1) {1'b0} }, cmp_o };
    end else begin
        assign Y = cmp_o;
    end endgenerate

endmodule

module \$le (A, B, Y);

    parameter A_SIGNED = 0;
    parameter B_SIGNED = 0;
    parameter A_WIDTH = 1;
    parameter B_WIDTH = 1;
    parameter Y_WIDTH = 1;

    input [A_WIDTH-1:0] A;
    input [B_WIDTH-1:0] B;
    output [Y_WIDTH-1:0] Y;

    wire cmp_o;

    _cmp_ #(.A_SIGNED(B_SIGNED), .B_SIGNED(A_SIGNED), .A_WIDTH(B_WIDTH), .B_WIDTH(A_WIDTH)) i_cmp (.A(B), .B(A), .Y(cmp_o));

    generate if (Y_WIDTH > 1) begin
        assign Y = { {(Y_WIDTH - 1) {1'b0} }, ~cmp_o };
    end else begin
        assign Y = ~cmp_o;
    end endgenerate

endmodule

module \$ge (A, B, Y);

    parameter A_SIGNED = 0;
    parameter B_SIGNED = 0;
    parameter A_WIDTH = 1;
    parameter B_WIDTH = 1;
    parameter Y_WIDTH = 1;

    input [A_WIDTH-1:0] A;
    input [B_WIDTH-1:0] B;
    output [Y_WIDTH-1:0] Y;

    wire cmp_o;

    _cmp_ #(.A_SIGNED(A_SIGNED), .B_SIGNED(B_SIGNED), .A_WIDTH(A_WIDTH), .B_WIDTH(B_WIDTH)) i_cmp (.A(A), .B(B), .Y(cmp_o));

    generate if (Y_WIDTH > 1) begin
        assign Y = { {(Y_WIDTH - 1) {1'b0} }, ~cmp_o };
    end else begin
        assign Y = ~cmp_o;
    end endgenerate

endmodule