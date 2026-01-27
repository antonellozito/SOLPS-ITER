function args_out = parse_command_line_args(varargin)
    % PARSE_COMMAND_LINE_ARGS Convert command-line string arguments to MATLAB types
    %
    % Returns a cell array of parsed arguments
    
    args = {};
    i = 1;
    while i <= numel(varargin)
        arg = varargin{i};
        
        if ischar(arg) && ~isempty(arg)
            args{end+1} = arg;
            
            if i + 1 <= numel(varargin)
                value = varargin{i+1};
                
                if ischar(value)
                    value = convert_string_value(value);
                end
                
                args{end+1} = value;
                i = i + 2;
            else
                i = i + 1;
            end
        else
            args{end+1} = arg;
            i = i + 1;
        end
    end
    
    % Return as cell array directly
    args_out = args;
end

function value = convert_string_value(str)
    str = strtrim(str);
    
    % Boolean
    if strcmpi(str, 'true')
        value = true;
        return;
    elseif strcmpi(str, 'false')
        value = false;
        return;
    end
    
    % NaN
    if strcmpi(str, 'nan')
        value = nan;
        return;
    end
    
    % Quoted string
    if (startsWith(str, '''') && endsWith(str, '''')) || ...
       (startsWith(str, '"') && endsWith(str, '"'))
        value = str(2:end-1);
        return;
    end
    
    % Numeric array (comma-separated)
    if contains(str, ',')
        parts = strsplit(str, ',');
        nums = cellfun(@str2double, parts);
        if ~any(isnan(nums)) || all(strcmpi(parts, 'nan'))
            value = nums;
            return;
        end
    end
    
    % Single numeric
    num = str2double(str);
    if ~isnan(num)
        value = num;
        return;
    end
    
    % Keep as string
    value = str;
end
