module \$_DFF_N_ (D, C, Q);
    input D, C;
    output Q;

    dffn _TECHMAP_REPLACE_ (.clk(C), .D(D), .Q(Q));

endmodule
