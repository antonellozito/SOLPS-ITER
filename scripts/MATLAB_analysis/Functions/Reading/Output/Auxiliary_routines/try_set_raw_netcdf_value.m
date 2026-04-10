function output = try_set_raw_netcdf_value(output, file, field_name, variable_name, transform_fn)
if nargin < 5
    transform_fn = [];
end

try
    output = set_raw_netcdf_value(output, file, field_name, variable_name, transform_fn);
catch
end
end
