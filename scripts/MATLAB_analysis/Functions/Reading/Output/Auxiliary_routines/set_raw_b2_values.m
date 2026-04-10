function output = set_raw_b2_values(output, fid, field_specs)
for i = 1:size(field_specs, 1)
    field_name = field_specs{i, 1};
    token = field_specs{i, 2};
    data_dims = field_specs{i, 3};

    scale_factor = 1;
    if size(field_specs, 2) >= 4
        scale_factor = field_specs{i, 4};
    end

    output = set_raw_b2_value(output, fid, field_name, token, data_dims, scale_factor);
end
end
