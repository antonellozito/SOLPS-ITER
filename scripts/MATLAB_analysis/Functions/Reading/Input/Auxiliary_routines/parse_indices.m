function idx = parse_indices(idx_str)
%PARSE_INDICES Parse a comma-separated Fortran index list.
    parts = strsplit(strtrim(idx_str), ',');
    idx = zeros(1, length(parts));
    for i = 1:length(parts)
        idx(i) = str2double(strtrim(parts{i}));
    end
end
