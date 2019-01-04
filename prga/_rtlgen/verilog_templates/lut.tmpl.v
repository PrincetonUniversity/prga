module lut{{ width }} (
    input wire [{{ width - 1 }}:0] in,
    output reg [0:0] out,
    input wire [{{ 2 ** width - 1}}:0] cfg_d,
    input wire [0:0] cfg_e
    );

    always @* begin
        if (cfg_e) begin
            out = 1'b0;
        end else begin
            case (in) // synopsys infer_mux
        {%- for i in range(2 ** width) %}
                {{ width }}'d{{ i }}: out = cfg_d[{{ i }}];
        {%- endfor %}
                default: out = 1'b0;
            endcase
        end
    end

endmodule
