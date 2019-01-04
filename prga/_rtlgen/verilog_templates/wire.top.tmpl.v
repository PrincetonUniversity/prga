
    {% if comment -%}
    // {{ comment|wordwrap(70, false, '\n\t// ') }}
    {% endif -%}
    wire [{{ width - 1 }}:0] {{ name }}{%- if assignment %} = {{ assignment }}{%- endif -%};
