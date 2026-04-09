function value = parse_switch_value(raw_value, type_text, preserve_unparsed)
%PARSE_SWITCH_VALUE Parse a b2mn.dat or XML default switch value.
    if nargin < 3
        preserve_unparsed = true;
    end

    raw_value = strtrim(raw_value);
    type_text = lower(strtrim(type_text));

    if isempty(raw_value)
        if contains(type_text, 'string') || contains(type_text, 'character')
            value = '';
        else
            value = [];
        end
        return;
    end

    if contains(type_text, 'string') || contains(type_text, 'character')
        value = raw_value;
        return;
    end

    lower_value = lower(raw_value);
    if strcmp(lower_value, '.true.') || strcmp(lower_value, 'true') || strcmp(lower_value, 't')
        value = true;
        return;
    end
    if strcmp(lower_value, '.false.') || strcmp(lower_value, 'false') || strcmp(lower_value, 'f')
        value = false;
        return;
    end

    numeric_text = regexprep(raw_value, '([0-9.])D([+-]?\d)', '$1E$2', 'ignorecase');
    numeric_text = regexprep(numeric_text, '_[Rr]8', '');
    numeric_value = str2double(numeric_text);

    if contains(type_text, 'integer')
        if ~isnan(numeric_value)
            value = round(numeric_value);
        elseif preserve_unparsed
            value = raw_value;
        else
            value = [];
        end
        return;
    end

    if contains(type_text, 'real')
        if ~isnan(numeric_value)
            value = numeric_value;
        elseif preserve_unparsed
            value = raw_value;
        else
            value = [];
        end
        return;
    end

    if ~isnan(numeric_value)
        value = numeric_value;
    elseif preserve_unparsed
        value = raw_value;
    else
        value = [];
    end
end
