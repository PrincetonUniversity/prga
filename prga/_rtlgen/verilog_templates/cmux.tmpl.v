module cmux{{ width }} (
    input wire [{{ width - 1 }}:0] i,
    output reg [0:0] o,
    input wire [{{ width_sel - 1 }}:0] cfg_d,
    input wire [0:0] cfg_e
    );

    always @* begin
        if (cfg_e) begin
            o = 1'b0;
        end else begin
            case (cfg_d) // synopsys infer_mux
        {%- for i in range(width) %}
                {{ width_sel }}'d{{ i }}: o = i[{{ i }}];
        {%- endfor %}
                default: o = 1'b0;
            endcase
        end
    end

endmodule
