module dff (CK,Q,D);
input CK,D;
output reg Q;

    always @(posedge CK)
        Q <= D;

endmodule
