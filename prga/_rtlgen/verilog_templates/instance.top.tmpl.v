
    {% if comment -%}
    // {{ comment|wordwrap(70, false, '\n\t// ') }}
    {% endif -%}
    {{ model }} {{ name }} (
        {%- set comma = joiner(",") %}
        {%- for pin in pins %}{{ comma() }}
        .{{ pin.name }}({{ pin.connection }})
        {%- endfor %}
        );
