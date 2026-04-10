function output = set_raw_b2_value(output, fid, field_name, token, data_dims, scale_factor)
if nargin < 6
    scale_factor = 1;
end

output.(field_name) = scan_b2_real(fid, token, data_dims) .* scale_factor;
end
