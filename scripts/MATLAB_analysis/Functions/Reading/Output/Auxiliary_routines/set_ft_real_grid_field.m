function output = set_ft_real_grid_field(output, fid, ver, field_name, token, data_dims, description, unit, dimension_labels, scale_factor)
if nargin < 10
    scale_factor = 1;
end

value = scan_ft_real_grid(fid, ver, token, data_dims);
value = value .* scale_factor;

output = set_output_field(output, field_name, value, description, unit, dimension_labels);
end
