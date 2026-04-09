function val = parse_char_values(vstr)
%PARSE_CHAR_VALUES Parse concatenated quoted character data.
    vstr = strip_trailing_comma(vstr);
    if isempty(vstr), val = ''; return; end
    tok = regexp(vstr, '''([^'']*)''', 'tokens');
    val = '';
    for i = 1:length(tok)
        val = [val, tok{i}{1}]; %#ok<AGROW>
    end
end
