function boundary_parameters = read_boundary_parameters(simulation)

% read_boundary_parameters reads the b2.boundary.parameters containing the
% input parameters for the boundary conditions for B2.5
% Output is a struct "boundary_parameters" with all the data fields
% in the b2.boundary.parameters file.

% Each parameter is stored as a substruct with two fields:
%   .value       - the numeric/char/logical value
%   .description - a char containing the documentation from b2cdcn.F

%% PRELIMINARY OPERATIONS

% Load the files and read the version
index = find(contains({simulation.run.name},'b2.boundary.parameters'));
file_ok = ~isempty(index);

if file_ok
    file = simulation.run(index).file;
    fid = fopen(file);
    if (fid == -1)
        file_ok = false;
    end
end

% Determine grid version and number of species
grid_version = simulation.grid_version; % 'Structured' or 'Unstructured'
ns = length(simulation.species);

%% READ DOCUMENTATION FROM b2cdcn.F

descriptions = read_boundary_descriptions(simulation.SOLPSTOP, grid_version);

%% READ THE ENTIRE FILE, HANDLE VERSION LINE, EXTRACT NAMELIST BLOCK

if file_ok
    raw = fread(fid, '*char')';
    fclose(fid);

    % Handle version line
    lines = strsplit(raw, {char(10), char(13)});
    first_nonempty = '';
    for iL = 1:length(lines)
        stripped = strtrim(lines{iL});
        if ~isempty(stripped)
            first_nonempty = stripped;
            break;
        end
    end
    if length(first_nonempty) >= 7 && strcmpi(first_nonempty(1:7), 'VERSION')
        boundary_parameters.version = make_param(first_nonempty, '');
        idx_newline = find(raw == char(10), 1, 'first');
        if ~isempty(idx_newline)
            raw = raw(idx_newline+1:end);
        end
    else
        boundary_parameters.version = make_param('', '');
    end

    % Extract the namelist block
    idx_start = regexpi(raw, '&\s*BOUNDARY');
    if isempty(idx_start)
        nml_str = '';
    else
        in_string = false;
        idx_end = [];
        for ic = idx_start(1)+10 : length(raw)
            if raw(ic) == ''''
                in_string = ~in_string;
            end
            if raw(ic) == '/' && ~in_string
                idx_end = ic;
                break;
            end
        end
        if isempty(idx_end)
            nml_str = '';
        else
            nml_str = raw(idx_start(1):idx_end);
        end
    end
else
    boundary_parameters.version = make_param('', '');
    nml_str = '';
end

%% READ NBC AND NNISO

nbc = read_scalar_int(nml_str, 'nbc');
if isempty(nbc), nbc = 0; end
nniso = read_scalar_int(nml_str, 'nniso');
if isempty(nniso), nniso = 0; end

%% SET DEFAULT VALUES

% Helper to get description for a variable
    function d = desc(varname)
        if isfield(descriptions, lower(varname))
            d = descriptions.(lower(varname));
        else
            d = '';
        end
    end

% Scalar defaults
boundary_parameters.nbc                  = make_param(nbc, desc('nbc'));
boundary_parameters.nniso                = make_param(nniso, desc('nniso'));
boundary_parameters.gammai               = make_param(1.0, desc('gammai'));
boundary_parameters.gammae               = make_param(0.5, desc('gammae'));
boundary_parameters.lbndusr              = make_param(false, desc('lbndusr'));
boundary_parameters.lfeedback            = make_param(false, desc('lfeedback'));
boundary_parameters.teiso                = make_param(1.0, desc('teiso'));
boundary_parameters.tiiso                = make_param(1.0, desc('tiiso'));
boundary_parameters.phiiso               = make_param(0.0, desc('phiiso'));
boundary_parameters.write_nml_bnd        = make_param(true, desc('write_nml_bnd'));
boundary_parameters.boundary_filename    = make_param('b2.boundary.parameters', desc('boundary_filename'));
boundary_parameters.boundary_time_mod    = make_param(0.0, desc('boundary_time_mod'));
boundary_parameters.boundary_time_switch = make_param(0.0, desc('boundary_time_switch'));

% Array defaults
boundary_parameters.conpar       = make_param(zeros(ns, nbc, 3), desc('conpar'));
boundary_parameters.mompar       = make_param(zeros(ns, nbc, 2), desc('mompar'));
boundary_parameters.enepar       = make_param(zeros(nbc, 2), desc('enepar'));
boundary_parameters.enipar       = make_param(zeros(nbc, 2), desc('enipar'));
boundary_parameters.potpar       = make_param(zeros(nbc, 2), desc('potpar'));
boundary_parameters.bcpos        = make_param(-2 * ones(1, nbc), desc('bcpos'));
boundary_parameters.bcstart      = make_param(-2 * ones(1, nbc), desc('bcstart'));
boundary_parameters.bcend        = make_param(-2 * ones(1, nbc), desc('bcend'));
boundary_parameters.bc_list_size = make_param(zeros(1, nbc), desc('bc_list_size'));
boundary_parameters.bc_list_x    = make_param([], desc('bc_list_x'));
boundary_parameters.bc_list_y    = make_param([], desc('bc_list_y'));
boundary_parameters.bccon        = make_param(zeros(ns, nbc), desc('bccon'));
boundary_parameters.bcmom        = make_param(zeros(ns, nbc), desc('bcmom'));
boundary_parameters.bcene        = make_param(zeros(1, nbc), desc('bcene'));
boundary_parameters.bceni        = make_param(zeros(1, nbc), desc('bceni'));
boundary_parameters.bcpot        = make_param(zeros(1, nbc), desc('bcpot'));
boundary_parameters.bcchar       = make_param(repmat(' ', 1, nbc), desc('bcchar'));
boundary_parameters.niiso        = make_param(1.0e10 * ones(1, ns), desc('niiso'));
boundary_parameters.lcbs         = make_param(zeros(1, nbc), desc('lcbs'));

if nniso > 0
    boundary_parameters.nxiso1 = make_param(-2 * ones(1, nniso), desc('nxiso1'));
    boundary_parameters.nxiso2 = make_param(-2 * ones(1, nniso), desc('nxiso2'));
    boundary_parameters.nyiso1 = make_param(-2 * ones(1, nniso), desc('nyiso1'));
    boundary_parameters.nyiso2 = make_param(-2 * ones(1, nniso), desc('nyiso2'));
else
    boundary_parameters.nxiso1 = make_param([], desc('nxiso1'));
    boundary_parameters.nxiso2 = make_param([], desc('nxiso2'));
    boundary_parameters.nyiso1 = make_param([], desc('nyiso1'));
    boundary_parameters.nyiso2 = make_param([], desc('nyiso2'));
end

% Structured-only arrays
if strcmp(grid_version, 'Structured')
    boundary_parameters.con_fn = make_param(repmat({'b2.con.profile'}, ns, nbc), desc('con_fn'));
    boundary_parameters.mom_fn = make_param(repmat({'b2.mom.profile'}, ns, nbc), desc('mom_fn'));
    boundary_parameters.ene_fn = make_param(repmat({'b2.ene.profile'}, 1, nbc), desc('ene_fn'));
    boundary_parameters.eni_fn = make_param(repmat({'b2.eni.profile'}, 1, nbc), desc('eni_fn'));
    boundary_parameters.pot_fn = make_param(repmat({'b2.pot.profile'}, 1, nbc), desc('pot_fn'));
end

% Unstructured-only arrays
if strcmp(grid_version, 'Unstructured')
    boundary_parameters.enkpar = make_param(zeros(nbc, 2), desc('enkpar'));
    boundary_parameters.enzpar = make_param(zeros(nbc, 2), desc('enzpar'));
    boundary_parameters.bcenk  = make_param(zeros(1, nbc), desc('bcenk'));
    boundary_parameters.bcenz  = make_param(zeros(1, nbc), desc('bcenz'));
end

%% BUILD THE VARIABLE CATALOGUE

catalogue = {
    'nbc',                   'si', false;
    'nniso',                 'si', false;
    'gammai',                'sr', false;
    'gammae',                'sr', false;
    'teiso',                 'sr', false;
    'tiiso',                 'sr', false;
    'phiiso',                'sr', false;
    'boundary_time_mod',     'sr', false;
    'boundary_time_switch',  'sr', false;
    'lbndusr',               'sl', false;
    'lfeedback',             'sl', false;
    'write_nml_bnd',         'sl', false;
    'boundary_filename',     'ss', false;
    'bcchar',                '1c', false;
    'bcpos',                 '1i', false;
    'bcstart',               '1i', false;
    'bcend',                 '1i', false;
    'bc_list_size',          '1i', false;
    'bcene',                 '1i', false;
    'bceni',                 '1i', false;
    'bcpot',                 '1i', false;
    'lcbs',                  '1i', false;
    'nxiso1',                '1i', false;
    'nxiso2',                '1i', false;
    'nyiso1',                '1i', false;
    'nyiso2',                '1i', false;
    'niiso',                 '1r', true;
    'bc_list_x',             '2i', false;
    'bc_list_y',             '2i', false;
    'bccon',                 '2i', true;
    'bcmom',                 '2i', true;
    'enepar',                '2r', false;
    'enipar',                '2r', false;
    'potpar',                '2r', false;
    'conpar',                '3r', true;
    'mompar',                '3r', true;
};

if strcmp(grid_version, 'Structured')
    catalogue = [catalogue; {
        'con_fn',  '2s', true;
        'mom_fn',  '2s', true;
        'ene_fn',  '1s', false;
        'eni_fn',  '1s', false;
        'pot_fn',  '1s', false;
    }];
end

if strcmp(grid_version, 'Unstructured')
    catalogue = [catalogue; {
        'bcenk',   '1i', false;
        'bcenz',   '1i', false;
        'enkpar',  '2r', false;
        'enzpar',  '2r', false;
    }];
end

cat_names = catalogue(:,1);
cat_types = catalogue(:,2);
cat_zb    = catalogue(:,3);

%% TOKENIZE AND PROCESS THE NAMELIST

nml_body = regexprep(nml_str, '&\s*BOUNDARY', '', 'ignorecase');
idx_slash = find(nml_body == '/', 1, 'last');
if ~isempty(idx_slash)
    nml_body = nml_body(1:idx_slash-1);
end
nml_body = strrep(nml_body, char(13), '');
nml_body = strrep(nml_body, char(10), ' ');

pattern = '([a-zA-Z]\w*)\s*(\([^)]*\))?\s*=';
[tokens, tok_starts, tok_ends] = regexp(nml_body, pattern, ...
    'tokens', 'start', 'end');
if isempty(tokens)
    boundary_parameters.grid_version = make_param(grid_version, '');
    return;
end

for it = 1:length(tokens)
    tok = tokens{it};
    lhs = lower(tok{1});

    if length(tok) >= 2 && ~isempty(tok{2})
        idx_str = strrep(strrep(tok{2}, '(', ''), ')', '');
        indices = parse_indices(idx_str);
    else
        indices = [];
    end

    val_start = tok_ends(it) + 1;
    if it < length(tokens)
        val_end = tok_starts(it+1) - 1;
    else
        val_end = length(nml_body);
    end
    vstr = strtrim(nml_body(val_start:val_end));

    cat_idx = find(strcmp(lhs, cat_names), 1);
    if isempty(cat_idx), continue; end
    vtype = cat_types{cat_idx};
    is_zb = cat_zb{cat_idx};

    switch vtype
        case 'si'
            val = parse_int_values(vstr);
            if ~isempty(val)
                boundary_parameters.(lhs).value = val(1);
            end
        case 'sr'
            val = parse_real_values(vstr);
            if ~isempty(val)
                boundary_parameters.(lhs).value = val(1);
            end
        case 'sl'
            val = parse_logical_values(vstr);
            if ~isempty(val)
                boundary_parameters.(lhs).value = val(1);
            end
        case 'ss'
            val = parse_string_value(vstr);
            if ~isempty(val)
                boundary_parameters.(lhs).value = val;
            end
        case '1i'
            val = parse_int_values(vstr);
            if ~isempty(val)
                boundary_parameters.(lhs).value = ...
                    set_1d(boundary_parameters.(lhs).value, indices, val, is_zb);
            end
        case '1r'
            val = parse_real_values(vstr);
            if ~isempty(val)
                boundary_parameters.(lhs).value = ...
                    set_1d(boundary_parameters.(lhs).value, indices, val, is_zb);
            end
        case '1c'
            val = parse_char_values(vstr);
            if ~isempty(val)
                boundary_parameters.(lhs).value = ...
                    set_1d_char(boundary_parameters.(lhs).value, indices, val);
            end
        case '1s'
            val = parse_string_list(vstr);
            if ~isempty(val)
                boundary_parameters.(lhs).value = ...
                    set_1d_str(boundary_parameters.(lhs).value, indices, val, is_zb);
            end
        case '2i'
            val = parse_int_values(vstr);
            if ~isempty(val)
                boundary_parameters.(lhs).value = ...
                    set_2d(boundary_parameters.(lhs).value, indices, val, is_zb);
            end
        case '2r'
            val = parse_real_values(vstr);
            if ~isempty(val)
                boundary_parameters.(lhs).value = ...
                    set_2d(boundary_parameters.(lhs).value, indices, val, is_zb);
            end
        case '2s'
            val = parse_string_list(vstr);
            if ~isempty(val)
                boundary_parameters.(lhs).value = ...
                    set_2d_str(boundary_parameters.(lhs).value, indices, val, is_zb);
            end
        case '3r'
            val = parse_real_values(vstr);
            if ~isempty(val)
                boundary_parameters.(lhs).value = ...
                    set_3d(boundary_parameters.(lhs).value, indices, val, is_zb);
            end
    end
end

boundary_parameters.grid_version = make_param(grid_version, '');

end


%% PARAMETER STRUCT CONSTRUCTOR

function p = make_param(value, description)
% Create a parameter substruct with .value and .description fields.
    p.value = value;
    p.description = description;
end


%% DOCUMENTATION PARSER

function descriptions = read_boundary_descriptions(SOLPSTOP, grid_version)

% Read the BOUNDARY namelist documentation block from b2cdcn.F.
% Returns a struct where each field is a lowercase variable name and the
% value is a char containing the multi-line description (lines joined by \n).
%
% The file is located at:
%   <SOLPSTOP>/modules/B2.5/src/documentation/b2cdcn.F
%
% The relevant block starts at a line matching:
%   * NAMELIST /BOUNDARY/
% and ends just before the next line matching:
%   * NAMELIST /...
%
% Within the block, each variable description starts with a line like:
%   *  VARNAME - type. Description text...
% and continuation lines are more indented:
%   *     continuation text...

    descriptions = struct();

    docfile = sprintf('%s/modules/B2.5/src/documentation/b2cdcn.F', SOLPSTOP);
    fid = fopen(docfile, 'r');
    if fid == -1
        return;
    end

    % Read all lines
    raw_text = fread(fid, '*char')';
    fclose(fid);
    all_lines = strsplit(raw_text, char(10));

    % Find the BOUNDARY block
    block_start = 0;
    block_end = length(all_lines);
    for iL = 1:length(all_lines)
        ln = all_lines{iL};
        if ~isempty(regexp(ln, '^\*\s+NAMELIST\s+/BOUNDARY/', 'once'))
            block_start = iL;
        elseif block_start > 0 && ~isempty(regexp(ln, '^\*\s+NAMELIST\s+/', 'once'))
            block_end = iL - 1;
            break;
        end
    end

    if block_start == 0
        return;
    end

    % Parse variable descriptions within the block
    current_var = '';
    current_desc_lines = {};
    for iL = block_start:block_end
        ln = all_lines{iL};
        if isempty(ln) || ln(1) ~= '*'
            continue;
        end
        after_star = ln(2:end);
        var_match = regexp(after_star, '^\s{1,2}([A-Z]\w*)\s+-\s+', 'tokens');
        if ~isempty(var_match)
            if ~isempty(current_var)
                descriptions.(lower(current_var)) = strjoin(current_desc_lines, '\n');
            end
            current_var = var_match{1}{1};
            desc_text = strtrim(after_star);
            current_desc_lines = {desc_text};
        elseif ~isempty(current_var)
            desc_text = after_star;
            desc_text = regexprep(desc_text, '^\s{1,5}', '');
            current_desc_lines{end+1} = desc_text;
        end
    end

    % Save the last variable
    if ~isempty(current_var)
        descriptions.(lower(current_var)) = strjoin(current_desc_lines, '\n');
    end
end


%% ARRAY ASSIGNMENT HELPERS

function arr = set_1d(arr, indices, val, is_zb)
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
    if need > length(arr), arr(need) = 0; end
    arr(si:si+nv-1) = val;
end

function arr = set_1d_char(arr, indices, val)
    si = 1;
    if ~isempty(indices), si = max(1, indices(1)); end
    nv = length(val);
    need = si + nv - 1;
    if need > length(arr), arr(need) = ' '; end
    arr(si:si+nv-1) = val;
end

function arr = set_1d_str(arr, indices, val, is_zb)
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
    if need > length(arr), arr{need} = ''; end
    arr(si:si+nv-1) = val;
end

function arr = set_2d(arr, indices, val, is_zb)
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
        arr(r, c) = val(iv);
    end
end

function arr = set_2d_str(arr, indices, val, is_zb)
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

function arr = set_3d(arr, indices, val, is_zb)
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
    n1 = sz(1); n2 = sz(2);
    lin0 = (i3-1)*n1*n2 + (i2-1)*n1 + i1;
    total = prod(sz);
    for iv = 1:length(val)
        lin = lin0 + iv - 1;
        if lin > total, break; end
        p = ceil(lin / (n1*n2));
        rem12 = lin - (p-1)*n1*n2;
        c = ceil(rem12 / n1);
        r = rem12 - (c-1)*n1;
        arr(r, c, p) = val(iv);
    end
end


%% VALUE PARSERS

function idx = parse_indices(idx_str)
    parts = strsplit(strtrim(idx_str), ',');
    idx = zeros(1, length(parts));
    for i = 1:length(parts)
        idx(i) = str2double(strtrim(parts{i}));
    end
end

function val = parse_int_values(vstr)
    vstr = strip_trailing_comma(vstr);
    if isempty(vstr), val = []; return; end
    parts = strsplit(vstr, ',');
    val = [];
    for i = 1:length(parts)
        s = strtrim(parts{i});
        if isempty(s), continue; end
        rep = regexp(s, '^(\d+)\*(.+)$', 'tokens');
        if ~isempty(rep)
            val = [val, repmat(round(str2double(rep{1}{2})), 1, ...
                               str2double(rep{1}{1}))];
        else
            v = str2double(s);
            if ~isnan(v), val = [val, round(v)]; end
        end
    end
end

function val = parse_real_values(vstr)
    vstr = strip_trailing_comma(vstr);
    if isempty(vstr), val = []; return; end
    vstr = regexprep(vstr, '([0-9.])D([+-]?\d)', '$1E$2', 'ignorecase');
    vstr = regexprep(vstr, '_[Rr]8', '');
    parts = strsplit(vstr, ',');
    val = [];
    for i = 1:length(parts)
        s = strtrim(parts{i});
        if isempty(s), continue; end
        rep = regexp(s, '^(\d+)\*(.+)$', 'tokens');
        if ~isempty(rep)
            val = [val, repmat(str2double(rep{1}{2}), 1, ...
                               str2double(rep{1}{1}))];
        else
            v = str2double(s);
            if ~isnan(v), val = [val, v]; end
        end
    end
end

function val = parse_logical_values(vstr)
    vstr = strip_trailing_comma(vstr);
    if isempty(vstr), val = []; return; end
    parts = strsplit(vstr, ',');
    val = false(1, length(parts));
    for i = 1:length(parts)
        s = upper(strtrim(parts{i}));
        s = strrep(s, '.', '');
        val(i) = strcmp(s, 'TRUE') || strcmp(s, 'T');
    end
end

function val = parse_string_value(vstr)
    tok = regexp(vstr, '''([^'']*)''', 'tokens');
    if ~isempty(tok)
        val = tok{1}{1};
    else
        val = strip_trailing_comma(vstr);
    end
end

function val = parse_string_list(vstr)
    tok = regexp(vstr, '''([^'']*)''', 'tokens');
    val = {};
    for i = 1:length(tok)
        val{end+1} = tok{i}{1};
    end
end

function val = parse_char_values(vstr)
    vstr = strip_trailing_comma(vstr);
    if isempty(vstr), val = ''; return; end
    tok = regexp(vstr, '''([^'']*)''', 'tokens');
    val = '';
    for i = 1:length(tok)
        val = [val, tok{i}{1}];
    end
end

function val = read_scalar_int(nml_str, varname)
    pattern = ['(?i)' varname '\s*=\s*(-?\d+)'];
    tok = regexp(nml_str, pattern, 'tokens');
    if ~isempty(tok)
        val = str2double(tok{1}{1});
    else
        val = [];
    end
end

function vstr = strip_trailing_comma(vstr)
    vstr = strtrim(vstr);
    if ~isempty(vstr) && vstr(end) == ','
        vstr = strtrim(vstr(1:end-1));
    end
end
