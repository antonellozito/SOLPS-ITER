function output = set_netcdf_field(output, file, field_name, variable_name, transform_fn)
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

info = ncinfo(file, variable_name);

output = set_output_field(output, field_name, value, ...
    ncreadatt(file, variable_name, 'long_name'), ...
    ncreadatt(file, variable_name, 'units'), ...
    {info.Dimensions.Name});
end
