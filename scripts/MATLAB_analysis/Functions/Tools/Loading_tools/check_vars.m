function check_vars(var_names, type)

% CHECK_VARS Check that a list of variables in caller workspace have the given type
%
%   check_vars(var_names, type)
%   var_names : cell array of variable names (strings)
%   type      : 'logical', 'number', 'string', 'cell', 'required'
%   Throws an error if any variable is missing or has the wrong type.
%   For 'required' type: checks that variables exist and are not empty.

if nargin < 2
    error('Error: Must provide variable names and type.');
end
if ~iscell(var_names)
    error('Error: var_names must be a cell array of variable names.');
end

missing_vars = {};
wrong_type_vars = {};
empty_vars = {};

for k = 1:numel(var_names)
    v = var_names{k};
    
    % Check if variable exists in caller
    if ~evalin('caller', sprintf('exist(''%s'',''var'')', v))
        missing_vars{end+1} = v;
        continue
    end
    
    % Check type
    val = evalin('caller', v);
    
    switch lower(type)
        case 'logical'
            is_valid = islogical(val) && isscalar(val);
            type_name = 'logical scalar';
        case 'number'
            is_valid = isnumeric(val);
            type_name = 'numeric';
        case 'string'
            is_valid = ischar(val) || (isstring(val) && isscalar(val));
            type_name = 'string or char vector';
        case 'cell'
            is_valid = iscell(val);
            type_name = 'cell array';
        case 'required'
            is_valid = true;
            type_name = 'non-empty';
            if isempty(val)
                empty_vars{end+1} = v;
            end
        otherwise
            error('Error: Unknown type: %s', type);
    end
    
    if ~strcmp(lower(type), 'required') && ~is_valid
        wrong_type_vars{end+1} = v;
    end
end

% Report missing variables
if ~isempty(missing_vars)
    error('Error: The following variable(s) are missing:\n%s', strjoin(missing_vars, ', '));
end

% Report empty variables (for 'required' type)
if ~isempty(empty_vars)
    error('Error: The following variable(s) must have a value:\n%s', strjoin(empty_vars, ', '));
end

% Report variables with wrong type
if ~isempty(wrong_type_vars)
    error('Error: The following variable(s) must be %s:\n%s', type_name, strjoin(wrong_type_vars, ', '));
end
end
