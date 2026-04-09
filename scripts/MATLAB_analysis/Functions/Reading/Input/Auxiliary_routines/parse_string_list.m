function val = parse_string_list(vstr)
%PARSE_STRING_LIST Parse a list of quoted namelist strings.
    tok = regexp(vstr, '''([^'']*)''', 'tokens');
    val = {};
    for i = 1:length(tok)
        val{end+1} = tok{i}{1}; %#ok<AGROW>
    end
end
