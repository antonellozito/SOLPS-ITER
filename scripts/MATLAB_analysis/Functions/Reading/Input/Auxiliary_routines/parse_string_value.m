function val = parse_string_value(vstr)
%PARSE_STRING_VALUE Parse a single quoted namelist string.
    tok = regexp(vstr, '''([^'']*)''', 'tokens');
    if ~isempty(tok)
        val = tok{1}{1};
    else
        val = strip_trailing_comma(vstr);
    end
end
