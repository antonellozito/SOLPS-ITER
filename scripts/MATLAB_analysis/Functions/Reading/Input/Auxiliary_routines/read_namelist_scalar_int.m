function val = read_namelist_scalar_int(nml_str, varname)
%READ_NAMELIST_SCALAR_INT Read a scalar integer assignment from a namelist.
    pattern = ['(?i)' varname '\s*=\s*(-?\d+)'];
    tok = regexp(nml_str, pattern, 'tokens');
    if ~isempty(tok)
        val = str2double(tok{1}{1});
    else
        val = [];
    end
end
