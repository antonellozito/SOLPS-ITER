function arr = set_1d_char(arr, indices, val)
%SET_1D_CHAR Assign values into a 1-D character array.
    si = 1;
    if ~isempty(indices), si = max(1, indices(1)); end
    nv = length(val);
    need = si + nv - 1;
    if need > length(arr), arr(need) = ' '; end
    arr(si:si+nv-1) = val;
end
