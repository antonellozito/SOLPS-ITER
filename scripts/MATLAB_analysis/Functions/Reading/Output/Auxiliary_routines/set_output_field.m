function output = set_output_field(output, field_name, value, description, unit, dimensions)
output.(field_name) = make_output_field(value, description, unit, dimensions);
end
