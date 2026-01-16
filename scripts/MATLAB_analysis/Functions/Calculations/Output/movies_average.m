function S_avg = movies_average(S, range)

% MOVIES_AVERAGE Compute averages of struct fields along the last dimension.
%
%   S_avg = movies_average(S, 0)
%       → averages numerical fields along their entire last non-singleton dimension.
%
%   S_avg = movies_average(S, [M N])
%       → averages numerical fields from index M to N along that dimension.
%
%   S_avg = movies_average(S, N)
%       → extracts ONLY the slice at index N (i.e., no averaging).
%
%   Non-numeric fields are copied unchanged.
%   Works with structured fields containing .value, .description, .unit, .dimensions
    
    fields = fieldnames(S);
    S_avg = struct();
    
    for i = 1:numel(fields)
        field = fields{i};
        data = S.(field);
        
        % Check if this is a structured field with .value subfield
        if isstruct(data) && isfield(data, 'value')
            % Process the .value field
            value_data = data.value;
            
            if isnumeric(value_data) && not(isscalar(value_data))
                sz = size(value_data);
                last_dim = find(sz > 1, 1, 'last');
                
                if numel(range) == 1 && range == 0
                    % Mode 1: full average
                    S_avg.(field).value = mean(value_data, last_dim);
                elseif numel(range) == 1
                    % Mode 3: single slice extraction
                    idx = repmat({':'}, 1, ndims(value_data));
                    idx{last_dim} = range;
                    S_avg.(field).value = value_data(idx{:});
                elseif numel(range) == 2
                    % Mode 2: average from M to N
                    M = range(1);
                    N = range(2);
                    idx = repmat({':'}, 1, ndims(value_data));
                    idx{last_dim} = M:N;
                    S_avg.(field).value = mean(value_data(idx{:}), last_dim);
                end
            else
                S_avg.(field).value = value_data;
            end
            
            % Copy metadata fields
            if isfield(data, 'description')
                S_avg.(field).description = data.description;
            end
            if isfield(data, 'unit')
                S_avg.(field).unit = data.unit;
            end
            if isfield(data, 'dimensions')
                % Remove 'time' from dimensions after averaging/slicing
                dims = data.dimensions;
                % Remove 'time' or 'times' from the dimensions cell array
                dims = dims(~strcmpi(dims, 'time') & ~strcmpi(dims, 'times'));
                S_avg.(field).dimensions = dims;
            end
            
        elseif isnumeric(data) && not(isscalar(data))
            % Original behavior for non-structured numeric fields
            sz = size(data);
            last_dim = find(sz > 1, 1, 'last');
            
            if numel(range) == 1 && range == 0
                % Mode 1: full average
                S_avg.(field) = mean(data, last_dim);
            elseif numel(range) == 1
                % Mode 3: single slice extraction
                idx = repmat({':'}, 1, ndims(data));
                idx{last_dim} = range;
                S_avg.(field) = data(idx{:});
            elseif numel(range) == 2
                % Mode 2: average from M to N
                M = range(1);
                N = range(2);
                idx = repmat({':'}, 1, ndims(data));
                idx{last_dim} = M:N;
                S_avg.(field) = mean(data(idx{:}), last_dim);
            end
        else
            % Copy non-numeric or scalar fields unchanged
            S_avg.(field) = data;
        end
    end
end
