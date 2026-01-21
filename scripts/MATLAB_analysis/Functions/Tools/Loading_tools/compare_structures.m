function [isEqual, diffReport] = compare_structures(s1, s2, path)

% COMPARE_STRUCTURES Recursively compare two structures for exact equality
%
%   [isEqual, diffReport] = compare_structures(s1, s2)
%
%   Compares all fields, substructures, arrays, cell arrays, and nested
%   content. Returns true only if everything is identical.
%
%   Outputs:
%       isEqual    - true if structures are identical, false otherwise
%       diffReport - cell array of strings describing all differences found
%
%   Example:
%       a.x = 1; a.sub.y = [1 2 3];
%       b.x = 1; b.sub.y = [1 2 4];
%       [eq, report] = structcmp(a, b)

    if nargin < 3
        path = 'root';
    end
    
    diffReport = {};
    
    % Check if both are structures
    if ~isstruct(s1) || ~isstruct(s2)
        isEqual = false;
        diffReport{end+1} = sprintf('%s: One or both inputs are not structures', path);
        return;
    end
    
    % Check for struct arrays
    if ~isequal(size(s1), size(s2))
        isEqual = false;
        diffReport{end+1} = sprintf('%s: Size mismatch - [%s] vs [%s]', ...
            path, num2str(size(s1)), num2str(size(s2)));
        return;
    end
    
    % Handle struct arrays
    if numel(s1) > 1
        isEqual = true;
        for idx = 1:numel(s1)
            [subEqual, subReport] = structcmp(s1(idx), s2(idx), sprintf('%s(%d)', path, idx));
            if ~subEqual
                isEqual = false;
                diffReport = [diffReport, subReport];
            end
        end
        return;
    end
    
    % Get field names
    fields1 = sort(fieldnames(s1));
    fields2 = sort(fieldnames(s2));
    
    % Check if field names match
    if ~isequal(fields1, fields2)
        isEqual = false;
        only1 = setdiff(fields1, fields2);
        only2 = setdiff(fields2, fields1);
        if ~isempty(only1)
            diffReport{end+1} = sprintf('%s: Fields only in first struct: %s', ...
                path, strjoin(only1', ', '));
        end
        if ~isempty(only2)
            diffReport{end+1} = sprintf('%s: Fields only in second struct: %s', ...
                path, strjoin(only2', ', '));
        end
        % Continue checking common fields
        fields1 = intersect(fields1, fields2);
    end
    
    % Compare each field
    isEqual = true;
    for i = 1:length(fields1)
        fname = fields1{i};
        val1 = s1.(fname);
        val2 = s2.(fname);
        fieldPath = sprintf('%s.%s', path, fname);
        
        [fieldEqual, fieldReport] = compareValues(val1, val2, fieldPath);
        
        if ~fieldEqual
            isEqual = false;
            diffReport = [diffReport, fieldReport];
        end
    end
    
    % Update isEqual if we found field mismatches earlier
    if ~isempty(diffReport)
        isEqual = false;
    end
end

function [isEqual, diffReport] = compareValues(val1, val2, path)
%COMPAREVALUES Compare two values of any type recursively

    diffReport = {};
    
    % Check class
    if ~strcmp(class(val1), class(val2))
        isEqual = false;
        diffReport{end+1} = sprintf('%s: Type mismatch - %s vs %s', ...
            path, class(val1), class(val2));
        return;
    end
    
    % Check size
    if ~isequal(size(val1), size(val2))
        isEqual = false;
        diffReport{end+1} = sprintf('%s: Size mismatch - [%s] vs [%s]', ...
            path, num2str(size(val1)), num2str(size(val2)));
        return;
    end
    
    % Handle different types
    if isstruct(val1)
        % Recursive struct comparison
        [isEqual, diffReport] = compare_structures(val1, val2, path);
        
    elseif iscell(val1)
        % Cell array comparison
        isEqual = true;
        for idx = 1:numel(val1)
            [cellEqual, cellReport] = compareValues(val1{idx}, val2{idx}, ...
                sprintf('%s{%d}', path, idx));
            if ~cellEqual
                isEqual = false;
                diffReport = [diffReport, cellReport];
            end
        end
        
    elseif istable(val1)
        % Table comparison
        if isequal(val1, val2)
            isEqual = true;
        else
            isEqual = false;
            diffReport{end+1} = sprintf('%s: Tables differ', path);
        end
        
    elseif isa(val1, 'function_handle')
        % Function handle comparison
        if isequal(func2str(val1), func2str(val2))
            isEqual = true;
        else
            isEqual = false;
            diffReport{end+1} = sprintf('%s: Function handles differ - %s vs %s', ...
                path, func2str(val1), func2str(val2));
        end
        
    elseif isnumeric(val1) || islogical(val1)
        % Numeric/logical comparison (handles NaN properly)
        if isequaln(val1, val2)
            isEqual = true;
        else
            isEqual = false;
            if numel(val1) <= 10
                diffReport{end+1} = sprintf('%s: Value mismatch - %s vs %s', ...
                    path, mat2str(val1), mat2str(val2));
            else
                % Find first difference for large arrays
                diffIdx = find(val1(:) ~= val2(:) & ~(isnan(val1(:)) & isnan(val2(:))), 1);
                if isempty(diffIdx)
                    diffIdx = find(isnan(val1(:)) ~= isnan(val2(:)), 1);
                end
                diffReport{end+1} = sprintf('%s: Value mismatch at index %d - %g vs %g (array size [%s])', ...
                    path, diffIdx, val1(diffIdx), val2(diffIdx), num2str(size(val1)));
            end
        end
        
    elseif ischar(val1)
        % Character array comparison
        if strcmp(val1, val2)
            isEqual = true;
        else
            isEqual = false;
            diffReport{end+1} = sprintf('%s: String mismatch - ''%s'' vs ''%s''', ...
                path, val1, val2);
        end
        
    elseif isstring(val1)
        % String array comparison
        if all(val1 == val2, 'all')
            isEqual = true;
        else
            isEqual = false;
            diffReport{end+1} = sprintf('%s: String array mismatch', path);
        end
        
    elseif iscategorical(val1)
        % Categorical comparison
        if isequal(val1, val2)
            isEqual = true;
        else
            isEqual = false;
            diffReport{end+1} = sprintf('%s: Categorical mismatch', path);
        end
        
    elseif isdatetime(val1) || isduration(val1)
        % Datetime/duration comparison
        if isequal(val1, val2)
            isEqual = true;
        else
            isEqual = false;
            diffReport{end+1} = sprintf('%s: Datetime/duration mismatch', path);
        end
        
    elseif isobject(val1)
        % Generic object comparison
        if isequal(val1, val2)
            isEqual = true;
        else
            isEqual = false;
            diffReport{end+1} = sprintf('%s: Object mismatch (class: %s)', path, class(val1));
        end
        
    else
        % Fallback to isequal
        if isequal(val1, val2)
            isEqual = true;
        else
            isEqual = false;
            diffReport{end+1} = sprintf('%s: Mismatch (type: %s)', path, class(val1));
        end
    end
end