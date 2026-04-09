function arr = set_1d_logical(arr, indices, val, is_zb)
%SET_1D_LOGICAL Assign values into a 1-D logical array.
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
    if need > length(arr), arr(need) = false; end
    arr(si:si+nv-1) = val;
end
