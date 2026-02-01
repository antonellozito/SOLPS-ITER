function [field_averaged, field_pieces] = phase_average(field, steps, type)

if strcmp(type,'b2time_time_traces')

    dim = find(size(field) > 1, 1, 'last');
    if steps > size(field,dim)
        error('Error: Number of time steps for computing the phase average cannot be larger than total time steps available for plotting (%d)',size(field,dim));
    end

    if length(size(field)) == 3
        nBlocks = floor(size(field,3) / steps);
        for iBlock = 1:nBlocks
            field_pieces{iBlock} = field(:,:,(iBlock-1)*steps+1:iBlock*steps);
        end
        for j = 1:size(field,2)
            clear x;
            x(:,:) = field(:,j,:);
            nBlocks = floor(numel(x) / steps);
            x = x(1:nBlocks*steps);
            y(:,j,:) = mean(reshape(x, steps, nBlocks), 2);
        end
        field_averaged = y';
        clear y;
        field_averaged = reshape(field_averaged, 1, size(field_averaged,1), size(field_averaged,2));
    else
        nBlocks = floor(size(field,2) / steps);
        for iBlock = 1:nBlocks
            field_pieces{iBlock} = field(:,(iBlock-1)*steps+1:iBlock*steps);
        end
        clear x;
        x = field;
        nBlocks = floor(numel(x) / steps);
        x = x(1:nBlocks*steps);
        field_averaged = mean(reshape(x, steps, nBlocks), 2)';
        field_averaged = reshape(field_averaged, 1, size(field_averaged,2));
    end

elseif strcmp(type,'b2time_profiles')

    dim = find(size(field) > 1, 1, 'last');
    if steps > size(field,dim)
        error('Error: Number of time steps for computing the phase average cannot be larger than total time steps available for plotting (%d)',size(field,dim));
    end
    if length(size(field)) == 3
        nBlocks = floor(size(field,3) / steps);
        for iBlock = 1:nBlocks
            field_pieces{iBlock} = field(:,:,(iBlock-1)*steps+1:iBlock*steps);
        end
        for k = 1:size(field,1)
            for j = 1:size(field,2)
                clear x;
                x = field(k,j,:);
                nBlocks = floor(numel(x) / steps);
                x = x(1:nBlocks*steps);
                y(k,j,:) = mean(reshape(x, steps, nBlocks), 2);
            end
        end
        field_averaged = y;
        clear y;
    else
        nBlocks = floor(size(field,2) / steps);
        for iBlock = 1:nBlocks
            field_pieces{iBlock} = field(:,(iBlock-1)*steps+1:iBlock*steps);
        end
        for k = 1:size(field,1)
            clear x;
            x = field(k,:);
            nBlocks = floor(numel(x) / steps);
            x = x(1:nBlocks*steps);
            y(k,:) = mean(reshape(x, steps, nBlocks), 2);
        end
        field_averaged = y;
        clear y;
    end

elseif strcmp(type,'tracing')

    dim = max(1, find(size(field) > 1, 1, 'first'));
    if steps > size(field,dim)
        error('Error: Number of time steps for computing the rolling average cannot be larger than total time steps available for plotting (%d)',size(field,dim));
    end
    nBlocks = floor(size(field,dim) / steps);
    for iBlock = 1:nBlocks
        field_pieces{iBlock} = field((iBlock-1)*steps+1:iBlock*steps);
    end
    x = field;
    nBlocks = floor(numel(x) / steps);
    x = x(1:nBlocks*steps);
    field_averaged = mean(reshape(x, steps, nBlocks), 2);

elseif strcmp(type,'time')

    if steps > size(field,1)
        error('Error: Number of time steps for computing the phase average cannot be larger than total time steps available for plotting (%d)',size(field,1));
    end
    x = field;
    x = x(1:steps);
    field_averaged = x;
    field_pieces = x;

else
    
    error('Error: Unknown type %s in phase_average. Use ''b2time_time_traces'', ''b2time_profiles'', ''tracing'', or ''time''', type);

end

end
