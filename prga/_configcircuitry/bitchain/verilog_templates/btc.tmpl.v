module btc_w{{ width }}_d{{ depth }} (
    input wire [0:0] clk,
    input wire [{{ width - 1 }}:0] i,
    input wire [0:0] e,
    output wire [{{ width - 1 }}:0] o,
    output reg [{{ width * depth - 1 }}:0] d
    );

    always @(posedge clk) begin
        if (e) begin
            {%- if depth > 1 %}
            d   <=  {d[{{ width * (depth - 1) - 1}}:0], i};
            {%- else %}
            d   <=  i;
            {%- endif %}
        end
    end
    {% if depth > 1 %}
    assign o = d[{{ width * depth - 1}} -: {{ width }}];
    {%- else %}
    assign o = d;
    {%- endif %}

endmodule
