function val = parse_logical_values(vstr)
%PARSE_LOGICAL_VALUES Parse logical namelist values and repetition syntax.
    vstr = strip_trailing_comma(vstr);
    if isempty(vstr), val = []; return; end
    parts = strsplit(vstr, ',');
    val = logical([]);
    for i = 1:length(parts)
        s = upper(strtrim(parts{i}));
        if isempty(s), continue; end
        rep = regexp(s, '^(\d+)\*(.+)$', 'tokens');
        if ~isempty(rep)
            n = str2double(rep{1}{1});
            v = strrep(rep{1}{2}, '.', '');
            lv = strcmp(v, 'TRUE') || strcmp(v, 'T');
            val = [val, repmat(lv, 1, n)]; %#ok<AGROW>
        else
            s = strrep(s, '.', '');
            val = [val, strcmp(s, 'TRUE') || strcmp(s, 'T')]; %#ok<AGROW>
        end
    end
end
