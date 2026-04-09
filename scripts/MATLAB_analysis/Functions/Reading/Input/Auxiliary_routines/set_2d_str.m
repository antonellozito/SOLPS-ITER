function arr = set_2d_str(arr, indices, val, is_zb)
%SET_2D_STR Assign values into a 2-D cell array of strings.
    sz = size(arr);
    i1 = 1; i2 = 1;
    if ~isempty(indices)
        if is_zb
            i1 = indices(1) + 1;
        else
            i1 = indices(1);
        end
        if length(indices) >= 2, i2 = indices(2); end
    end
    lin0 = (i2 - 1) * sz(1) + i1;
    total = prod(sz);
    for iv = 1:length(val)
        lin = lin0 + iv - 1;
        if lin > total, break; end
        c = ceil(lin / sz(1));
        r = lin - (c-1) * sz(1);
        arr{r, c} = val{iv};
    end
end
