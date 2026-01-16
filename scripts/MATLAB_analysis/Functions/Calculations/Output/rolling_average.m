function field_averaged = rolling_average(field, steps, type)

steps = floor(steps/2);

if strcmp(type,'b2time')

    dim = find(size(field) > 1, 1, 'last');
    if 2*steps > size(field,dim)
        error('Error: Number of time steps for computing the rolling average cannot be larger than total time steps available for plotting (%d)',size(field,dim));
    end

    sz = size(field);
    nd = ndims(field);
    last_dim = nd;

    field_averaged = zeros(sz, class(field));

    for k = 1:sz(last_dim)
        idx1 = max(1, k - steps);
        idx2 = min(sz(last_dim), k + steps);

        idx = repmat({':'}, 1, nd);
        idx_last_range = idx;
        idx_last_range{last_dim} = idx1:idx2;

        avg = mean(field(idx_last_range{:}), last_dim);

        sz_avg = sz;
        sz_avg(last_dim) = 1;
        avg = reshape(avg, sz_avg);

        idx{last_dim} = k;
        field_averaged(idx{:}) = avg;
    end

elseif strcmp(type,'tracing')

    dim = max(1, find(size(field) > 1, 1, 'first'));
    if 2*steps > size(field,dim)
        error('Error: Number of time steps for computing the rolling average cannot be larger than total time steps available for plotting (%d)',size(field,dim));
    end

    sz = size(field);
    nd = ndims(field);

    field_averaged = zeros(sz, class(field));

    for k = 1:sz(1)
        idx1 = max(1, k - steps);
        idx2 = min(sz(1), k + steps);

        idx = repmat({':'}, 1, nd);
        idx_last_range = idx;
        idx_last_range{1} = idx1:idx2;

        avg = mean(field(idx_last_range{:}), 1);

        sz_avg = sz;
        sz_avg(1) = 1;
        avg = reshape(avg, sz_avg);

        idx{1} = k;
        field_averaged(idx{:}) = avg;
    end

else

    error('Error: Unknown type %s in rolling_average. Use ''b2time'', or ''tracing''', type);

end

end
