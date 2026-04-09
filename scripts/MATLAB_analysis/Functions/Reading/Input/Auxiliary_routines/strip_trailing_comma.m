function vstr = strip_trailing_comma(vstr)
%STRIP_TRAILING_COMMA Remove a trailing namelist separator, if present.
    vstr = strtrim(vstr);
    if ~isempty(vstr) && vstr(end) == ','
        vstr = strtrim(vstr(1:end-1));
    end
end
