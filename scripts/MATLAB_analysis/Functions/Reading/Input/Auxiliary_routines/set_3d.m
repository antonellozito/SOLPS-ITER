function arr = set_3d(arr, indices, val, is_zb)
%SET_3D Assign values into a preallocated 3-D numeric array.
    sz = size(arr);
    if length(sz) < 3, sz(3) = 1; end
    i1 = 1; i2 = 1; i3 = 1;
    if ~isempty(indices)
        if is_zb
            i1 = indices(1) + 1;
        else
            i1 = indices(1);
        end
        if length(indices) >= 2, i2 = indices(2); end
        if length(indices) >= 3, i3 = indices(3); end
    end
    n1 = sz(1);
    n2 = sz(2);
    lin0 = (i3-1) * n1 * n2 + (i2-1) * n1 + i1;
    total = prod(sz);
    for iv = 1:length(val)
        lin = lin0 + iv - 1;
        if lin > total, break; end
        p = ceil(lin / (n1 * n2));
        rem12 = lin - (p-1) * n1 * n2;
        c = ceil(rem12 / n1);
        r = rem12 - (c-1) * n1;
        arr(r, c, p) = val(iv);
    end
end
