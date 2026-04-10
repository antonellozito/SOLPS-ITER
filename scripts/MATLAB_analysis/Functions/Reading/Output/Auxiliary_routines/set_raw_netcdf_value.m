function output = set_raw_netcdf_value(output, file, field_name, variable_name, transform_fn)
if nargin < 4 || isempty(variable_name)
    variable_name = field_name;
end
if nargin < 5
    transform_fn = [];
end

value = ncread(file, variable_name);
if ~isempty(transform_fn)
    value = transform_fn(value);
end

output.(field_name) = value;
end
