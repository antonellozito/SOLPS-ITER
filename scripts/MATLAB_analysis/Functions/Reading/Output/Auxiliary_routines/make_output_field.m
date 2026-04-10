function field = make_output_field(value, description, unit, dimensions)
field = struct();
field.value = value;
field.description = description;
field.unit = unit;
field.dimensions = dimensions;
end
