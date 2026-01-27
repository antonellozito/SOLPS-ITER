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