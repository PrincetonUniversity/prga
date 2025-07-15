module \$_DFF_P_ (D, C, Q);
    input D, C;
    output Q;

    m_dffe #(.ENABLE_CE(1'b0)) _TECHMAP_REPLACE_ (.C(C), .D(D), .Q(Q));

endmodule

module \$dff (CLK, D, Q);
    
    parameter WIDTH = 0;
    parameter CLK_POLARITY = 1'b1;

    input CLK;
    input [WIDTH-1:0] D;
    output [WIDTH-1:0] Q;

    wire _TECHMAP_FAIL_ = CLK_POLARITY != 1'b1;

    genvar i;
    generate for (i = 0; i < WIDTH; i = i + 1) begin
        m_dffe #(.ENABLE_CE(1'b0)) _TECHMAP_REPLACE_ (.C(CLK), .D(D[i]), .Q(Q[i]));
    end endgenerate

endmodule

module \$_DFFE_PN_ (D, C, E, Q);
    input D, C, E;
    output Q;

    \$_DFFE_PP_ _TECHMAP_REPLACE_ (.D(D), .C(C), .E(~E), .Q(Q));

endmodule

module \$_DFFE_PP_ (D, C, E, Q);
    input D, C, E;
    output Q;

    m_dffe #(.ENABLE_CE(1'b1)) _TECHMAP_REPLACE_ (.C(C), .D(D), .E(E), .Q(Q));

endmodule

module \$dffe (CLK, EN, D, Q);
    
    parameter WIDTH = 0;
    parameter CLK_POLARITY = 1'b1;
    parameter EN_POLARITY = 1'b1;

    input CLK, EN;
    input [WIDTH-1:0] D;
    output [WIDTH-1:0] Q;

    wire _TECHMAP_FAIL_ = CLK_POLARITY != 1'b1;

    genvar i;
    generate for (i = 0; i < WIDTH; i = i + 1) begin
        m_dffe #(.ENABLE_CE(1'b1)) _TECHMAP_REPLACE_ (.C(CLK), .D(D[i]), .E(EN == EN_POLARITY), .Q(Q[i]));
    end endgenerate

endmodule