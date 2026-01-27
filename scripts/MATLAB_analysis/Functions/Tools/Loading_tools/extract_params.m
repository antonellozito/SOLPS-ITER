function varargout = extract_params(results, params)

    % EXTRACT_PARAMS Extract inputParser results in order of PARAMS
    %   Returns values in the same order as params struct array
    
    varargout = cell(1, numel(params));
    for i = 1:numel(params)
        val = results.(params(i).name);
        if strcmp(params(i).type, 'logical')
            val = logical(val);
        end
        varargout{i} = val;
    end
end