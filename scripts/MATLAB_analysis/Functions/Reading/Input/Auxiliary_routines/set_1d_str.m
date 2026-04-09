function arr = set_1d_str(arr, indices, val, is_zb)
%SET_1D_STR Assign values into a 1-D cell array of strings.
    si = 1;
    if ~isempty(indices)
        if is_zb
            si = indices(1) + 1;
        else
            si = max(1, indices(1));
        end
    end
    nv = length(val);
    need = si + nv - 1;
    if need > length(arr), arr{need} = ''; end
    arr(si:si+nv-1) = val;
end
