function p = make_param(value, metadata)
%MAKE_PARAM Create a parameter substruct with XML metadata fields.
    if nargin < 2 || isempty(metadata)
        metadata = empty_param_metadata();
    elseif ischar(metadata) || (isstring(metadata) && isscalar(metadata))
        metadata = struct('default', '', 'type', '', 'description', char(metadata));
    elseif ~isstruct(metadata)
        metadata = empty_param_metadata();
    end

    if ~isfield(metadata, 'default'), metadata.default = ''; end
    if ~isfield(metadata, 'type'), metadata.type = ''; end
    if ~isfield(metadata, 'description'), metadata.description = ''; end

    p.value = value;
    p.default = metadata.default;
    p.type = metadata.type;
    p.description = metadata.description;
end
