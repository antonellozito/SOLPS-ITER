function field_averaged = batch_average(field, steps, type)
% BATCH_AVERAGE Computes batch average of a field
%   field_averaged = batch_average(field, steps, type) divides the field into
%   batches of 'steps' time steps and averages each batch.
%
% Inputs:
%   field - Input field to average (or time vector if type='time')
%   steps - Number of time steps per batch
%   type  - 'b2time', 'tracing', or 'time'
%
% Outputs:
%   field_averaged - Batch-averaged field (or time vector if type='time')

if strcmp(type, 'b2time')
    % Find the last non-singleton dimension
    dim = find(size(field) > 1, 1, 'last');
    
    % Get size information
    sz = size(field);
    nd = ndims(field);
    n_timesteps = sz(dim);
    
    % Calculate number of complete batches
    n_batches = floor(n_timesteps / steps);
    
    if n_batches == 0
        error('Error: Number of time steps (%d) is smaller than batch size (%d)', n_timesteps, steps);
    end
    
    % Warn if there are leftover time steps
    leftover = n_timesteps - n_batches * steps;
    if leftover > 0
        warning('Last %d time steps will be discarded (not a complete batch)', leftover);
    end
    
    % Initialize output
    sz_out = sz;
    sz_out(dim) = n_batches;
    field_averaged = zeros(sz_out, class(field));
    
    % Compute batch averages
    for k = 1:n_batches
        idx1 = (k - 1) * steps + 1;
        idx2 = k * steps;
        
        idx = repmat({':'}, 1, nd);
        idx_range = idx;
        idx_range{dim} = idx1:idx2;
        
        avg = mean(field(idx_range{:}), dim);
        
        sz_avg = sz;
        sz_avg(dim) = 1;
        avg = reshape(avg, sz_avg);
        
        idx{dim} = k;
        field_averaged(idx{:}) = avg;
    end
    
elseif strcmp(type, 'tracing')
    % First dimension is the time dimension
    dim = 1;
    
    % Get size information
    sz = size(field);
    nd = ndims(field);
    n_timesteps = sz(dim);
    
    % Calculate number of complete batches
    n_batches = floor(n_timesteps / steps);
    
    if n_batches == 0
        error('Error: Number of time steps (%d) is smaller than batch size (%d)', n_timesteps, steps);
    end
    
    % Warn if there are leftover time steps
    leftover = n_timesteps - n_batches * steps;
    if leftover > 0
        warning('Last %d time steps will be discarded (not a complete batch)', leftover);
    end
    
    % Initialize output
    sz_out = sz;
    sz_out(1) = n_batches;
    field_averaged = zeros(sz_out, class(field));
    
    % Compute batch averages
    for k = 1:n_batches
        idx1 = (k - 1) * steps + 1;
        idx2 = k * steps;
        
        idx = repmat({':'}, 1, nd);
        idx_range = idx;
        idx_range{1} = idx1:idx2;
        
        avg = mean(field(idx_range{:}), 1);
        
        sz_avg = sz;
        sz_avg(1) = 1;
        avg = reshape(avg, sz_avg);
        
        idx{1} = k;
        field_averaged(idx{:}) = avg;
    end
    
elseif strcmp(type, 'time')
    % For 1D time vector
    n_timesteps = length(field);
    
    % Calculate number of complete batches
    n_batches = floor(n_timesteps / steps);
    
    if n_batches == 0
        error('Error: Number of time steps (%d) is smaller than batch size (%d)', n_timesteps, steps);
    end
    
    % Warn if there are leftover time steps
    leftover = n_timesteps - n_batches * steps;
    if leftover > 0
        warning('Last %d time steps will be discarded (not a complete batch)', leftover);
    end
    
    % Initialize output
    field_averaged = zeros(n_batches, 1);
    
    % Compute batch averages
    for k = 1:n_batches
        idx1 = (k - 1) * steps + 1;
        idx2 = k * steps;
        
        field_averaged(k) = mean(field(idx1:idx2));
    end
    
else
    error('Error: Unknown type %s in batch_average. Use ''b2time'', ''tracing'', or ''time''', type);
end

end
