function output = set_raw_netcdf_values(output, file, field_specs)
for i = 1:size(field_specs, 1)
    field_name = field_specs{i, 1};

    if size(field_specs, 2) >= 2 && ~isempty(field_specs{i, 2})
        variable_name = field_specs{i, 2};
    else
        variable_name = field_name;
    end

    transform_fn = [];
    if size(field_specs, 2) >= 3
        transform_fn = field_specs{i, 3};
    end

    output = set_raw_netcdf_value(output, file, field_name, variable_name, transform_fn);
end
end
