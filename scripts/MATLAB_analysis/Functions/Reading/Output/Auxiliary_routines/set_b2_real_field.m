function output = set_b2_real_field(output, fid, field_name, token, data_dims, description, unit, dimension_labels, scale_factor)
if nargin < 9
    scale_factor = 1;
end

value = scan_b2_real(fid, token, data_dims);
value = value .* scale_factor;

output = set_output_field(output, field_name, value, description, unit, dimension_labels);
end
