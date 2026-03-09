function numerics_parameters = read_numerics_parameters(simulation)

% read_numerics_parameters reads the b2.numerics.parameters containing the
% input parameters for the numerics / time multipliers for B2.5
% Output is a struct "numerics_parameters" with all the data fields
% in the b2.numerics.parameters file.

% Each parameter is stored as a substruct with two fields:
%   .value       - the numeric/char/logical value
%   .description - a char containing the documentation from b2cdcn.F

%% PRELIMINARY OPERATIONS

% Load the files and read the version
index = find(contains({simulation.run.name},'b2.numerics.parameters'));
file_ok = ~isempty(index);

if file_ok
    file = simulation.run(index).file;
    fid = fopen(file);
    if (fid == -1)
        file_ok = false;
    end
end

% Determine grid version, number of species and number of regions
grid_version = simulation.grid_version; % 'Structured' or 'Unstructured'
ns = length(simulation.species);
nreg = length(simulation.volume_regions_names); % Fortran 0:NREG --> MATLAB size nreg+1

%% READ DOCUMENTATION FROM b2cdcn.F

descriptions = read_numerics_descriptions(simulation.SOLPSTOP, grid_version);

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
        numerics_parameters.version = make_param(first_nonempty, '');
        idx_newline = find(raw == char(10), 1, 'first');
        if ~isempty(idx_newline)
            raw = raw(idx_newline+1:end);
        end
    else
        numerics_parameters.version = make_param('', '');
    end

    % Extract the namelist block
    idx_start = regexpi(raw, '&\s*NUMERICS');
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
    numerics_parameters.version = make_param('', '');
    nml_str = '';
end

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
numerics_parameters.time_factor_required  = make_param(0.1, desc('time_factor_required'));
numerics_parameters.core_dt_suppression   = make_param(1.0, desc('core_dt_suppression'));
numerics_parameters.core_dt_factor        = make_param(1.0, desc('core_dt_factor'));
numerics_parameters.corr_core_dt          = make_param(1.0, desc('corr_core_dt'));
numerics_parameters.write_nml_num         = make_param(true, desc('write_nml_num'));
numerics_parameters.numerics_filename     = make_param('b2.numerics.parameters', desc('numerics_filename'));
numerics_parameters.numerics_time_mod     = make_param(0.0, desc('numerics_time_mod'));
numerics_parameters.numerics_time_switch  = make_param(0.0, desc('numerics_time_switch'));

% Arrays dimensioned by (0:NS-1) --> MATLAB size ns
numerics_parameters.corr_core_dn = make_param(ones(1, ns), desc('corr_core_dn'));

% Arrays dimensioned by (0:NS-1, 0:NREG) --> MATLAB (ns, nreg+1)
numerics_parameters.dtco = make_param(ones(ns, nreg+1), desc('dtco'));
numerics_parameters.dtmo = make_param(ones(ns, nreg+1), desc('dtmo'));

% Arrays dimensioned by (0:NREG) --> MATLAB (1, nreg+1)
numerics_parameters.dtee = make_param(ones(1, nreg+1), desc('dtee'));
numerics_parameters.dtei = make_param(ones(1, nreg+1), desc('dtei'));

% Arrays dimensioned by (0:NS-1, 0:NREG) --> MATLAB (ns, nreg+1)
numerics_parameters.solveco = make_param(true(ns, nreg+1), desc('solveco'));
numerics_parameters.solvemo = make_param(true(ns, nreg+1), desc('solvemo'));

% Arrays dimensioned by (0:NREG) --> MATLAB (1, nreg+1)
numerics_parameters.solvemt        = make_param(true(1, nreg+1), desc('solvemt'));
numerics_parameters.solvepo        = make_param(true(1, nreg+1), desc('solvepo'));
numerics_parameters.solveee        = make_param(true(1, nreg+1), desc('solveee'));
numerics_parameters.solveei        = make_param(true(1, nreg+1), desc('solveei'));
numerics_parameters.solveet        = make_param(true(1, nreg+1), desc('solveet'));
numerics_parameters.add_te_corr_to_po = make_param(true(1, nreg+1), desc('add_te_corr_to_po'));

% Arrays dimensioned by (1:NSPECIES)
elements = regexprep(simulation.species, '\d+$', '');
nspecies = length(unique(elements));
numerics_parameters.sna_corr         = make_param(zeros(1, nspecies), desc('sna_corr'));
numerics_parameters.taumax           = make_param(0.05 * ones(1, nspecies), desc('taumax'));
numerics_parameters.do_sna_corr_core = make_param(true(1, nspecies), desc('do_sna_corr_core'));

% Structured-grid-only arrays
if strcmp(grid_version, 'Structured')
    % Arrays dimensioned by (0:NS-1) --> MATLAB size ns
    numerics_parameters.dtco_sol  = make_param(ones(1, ns), desc('dtco_sol'));
    numerics_parameters.dtmo_sol  = make_param(ones(1, ns), desc('dtmo_sol'));
    % Scalar arrays
    numerics_parameters.dtee_sol  = make_param(1.0, desc('dtee_sol'));
    numerics_parameters.dtei_sol  = make_param(1.0, desc('dtei_sol'));
    numerics_parameters.iy_sol_dtxx = make_param(-2, desc('iy_sol_dtxx'));
    % Arrays dimensioned by (0:NS, 0:NREG) --> MATLAB (ns+1, nreg+1)
    numerics_parameters.last_solve_5  = make_param(true(ns+1, nreg+1), desc('last_solve_5'));
    numerics_parameters.last_solve_7  = make_param(true(ns+1, nreg+1), desc('last_solve_7'));
    numerics_parameters.last_solve_9  = make_param(true(ns+1, nreg+1), desc('last_solve_9'));
    numerics_parameters.last_solve_11 = make_param(true(ns+1, nreg+1), desc('last_solve_11'));
end

% Unstructured-grid-only arrays
if strcmp(grid_version, 'Unstructured')
    % Arrays dimensioned by (0:NREG) --> MATLAB (1, nreg+1)
    numerics_parameters.dten = make_param(ones(1, nreg+1), desc('dten'));
    % Arrays dimensioned by (0:NS-1, 0:NREG) --> MATLAB (ns, nreg+1)
    numerics_parameters.min_na = make_param(zeros(ns, nreg+1), desc('min_na'));
    % Arrays dimensioned by (0:NREG) --> MATLAB (1, nreg+1)
    numerics_parameters.solveen = make_param(true(1, nreg+1), desc('solveen'));
    numerics_parameters.solvekt = make_param(true(1, nreg+1), desc('solvekt'));
    numerics_parameters.solvezt = make_param(true(1, nreg+1), desc('solvezt'));
    % Arrays dimensioned by (0:NREG) --> MATLAB (1, nreg+1)
    numerics_parameters.last_solve_5 = make_param(true(1, nreg+1), desc('last_solve_5'));
    numerics_parameters.last_solve_9 = make_param(true(1, nreg+1), desc('last_solve_9'));
    % Arrays dimensioned by (1:DEF_NYD), dynamic
    numerics_parameters.dtfts    = make_param([], desc('dtfts'));
    numerics_parameters.dtco_ft  = make_param([], desc('dtco_ft'));
    numerics_parameters.dtmo_ft  = make_param([], desc('dtmo_ft'));
    numerics_parameters.dtee_ft  = make_param([], desc('dtee_ft'));
    numerics_parameters.dtei_ft  = make_param([], desc('dtei_ft'));
end

%% BUILD THE VARIABLE CATALOGUE

catalogue = {
    'time_factor_required',  'sr', false;
    'core_dt_suppression',   'sr', false;
    'core_dt_factor',        'sr', false;
    'corr_core_dt',          'sr', false;
    'numerics_time_mod',     'sr', false;
    'numerics_time_switch',  'sr', false;
    'write_nml_num',         'sl', false;
    'numerics_filename',     'ss', false;
    'corr_core_dn',          '1r', true;
    'dtee',                  '1r', true;
    'dtei',                  '1r', true;
    'sna_corr',              '1r', false;
    'taumax',                '1r', false;
    'solvemt',               '1l', true;
    'solvepo',               '1l', true;
    'solveee',               '1l', true;
    'solveei',               '1l', true;
    'solveet',               '1l', true;
    'add_te_corr_to_po',     '1l', true;
    'do_sna_corr_core',      '1l', false;
    'dtco',                  '2r', true;
    'dtmo',                  '2r', true;
    'solveco',               '2l', true;
    'solvemo',               '2l', true;
};

if strcmp(grid_version, 'Structured')
    catalogue = [catalogue; {
        'dtco_sol',      '1r', true;
        'dtmo_sol',      '1r', true;
        'dtee_sol',      'sr', false;
        'dtei_sol',      'sr', false;
        'iy_sol_dtxx',   'si', false;
        'last_solve_5',  '2l', true;
        'last_solve_7',  '2l', true;
        'last_solve_9',  '2l', true;
        'last_solve_11', '2l', true;
    }];
end

if strcmp(grid_version, 'Unstructured')
    catalogue = [catalogue; {
        'dten',          '1r', true;
        'min_na',        '2r', true;
        'solveen',       '1l', true;
        'solvekt',       '1l', true;
        'solvezt',       '1l', true;
        'last_solve_5',  '1l', true;
        'last_solve_9',  '1l', true;
        'dtfts',         '1i', false;
        'dtco_ft',       '1r', false;
        'dtmo_ft',       '1r', false;
        'dtee_ft',       '1r', false;
        'dtei_ft',       '1r', false;
    }];
end

cat_names = catalogue(:,1);
cat_types = catalogue(:,2);
cat_zb    = catalogue(:,3);

%% TOKENIZE AND PROCESS THE NAMELIST

nml_body = regexprep(nml_str, '&\s*NUMERICS', '', 'ignorecase');
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
    numerics_parameters.grid_version = make_param(grid_version, '');
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
                numerics_parameters.(lhs).value = val(1);
            end
        case 'sr'
            val = parse_real_values(vstr);
            if ~isempty(val)
                numerics_parameters.(lhs).value = val(1);
            end
        case 'sl'
            val = parse_logical_values(vstr);
            if ~isempty(val)
                numerics_parameters.(lhs).value = val(1);
            end
        case 'ss'
            val = parse_string_value(vstr);
            if ~isempty(val)
                numerics_parameters.(lhs).value = val;
            end
        case '1i'
            val = parse_int_values(vstr);
            if ~isempty(val)
                numerics_parameters.(lhs).value = ...
                    set_1d(numerics_parameters.(lhs).value, indices, val, is_zb);
            end
        case '1r'
            val = parse_real_values(vstr);
            if ~isempty(val)
                numerics_parameters.(lhs).value = ...
                    set_1d(numerics_parameters.(lhs).value, indices, val, is_zb);
            end
        case '1l'
            val = parse_logical_values(vstr);
            if ~isempty(val)
                numerics_parameters.(lhs).value = ...
                    set_1d_logical(numerics_parameters.(lhs).value, indices, val, is_zb);
            end
        case '2r'
            val = parse_real_values(vstr);
            if ~isempty(val)
                numerics_parameters.(lhs).value = ...
                    set_2d(numerics_parameters.(lhs).value, indices, val, is_zb);
            end
        case '2l'
            val = parse_logical_values(vstr);
            if ~isempty(val)
                numerics_parameters.(lhs).value = ...
                    set_2d_logical(numerics_parameters.(lhs).value, indices, val, is_zb);
            end
    end
end

numerics_parameters.grid_version = make_param(grid_version, '');

end


%% PARAMETER STRUCT CONSTRUCTOR

function p = make_param(value, description)
% Create a parameter substruct with .value and .description fields.
    p.value = value;
    p.description = description;
end


%% DOCUMENTATION PARSER

function descriptions = read_numerics_descriptions(SOLPSTOP, grid_version)

% Read the NUMERICS namelist documentation block from b2cdcn.F.
% Returns a struct where each field is a lowercase variable name and the
% value is a char containing the multi-line description (lines joined by \n).
%
% The file is located at:
%   <SOLPSTOP>/modules/B2.5/src/documentation/b2cdcn.F
%
% The relevant block starts at a line matching:
%   * NAMELIST /NUMERICS/
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

    % Find the NUMERICS block
    block_starts = [];
    block_ends = [];
    for iL = 1:length(all_lines)
        ln = all_lines{iL};
        if ~isempty(regexp(ln, '^\*\s+NAMELIST\s+/NUMERICS/', 'once'))
            block_starts(end+1) = iL;
        elseif ~isempty(block_starts) && length(block_ends) < length(block_starts)
            if ~isempty(regexp(ln, '^\*\s+NAMELIST\s+/', 'once'))
                block_ends(end+1) = iL - 1;
            end
        end
    end
    if length(block_starts) > length(block_ends)
        block_ends(end+1) = length(all_lines);
    end

    if isempty(block_starts)
        return;
    end

    if strcmp(grid_version, 'Unstructured') && length(block_starts) >= 2
        block_start = block_starts(2);
        block_end = block_ends(2);
    else
        block_start = block_starts(1);
        block_end = block_ends(1);
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

function arr = set_1d_logical(arr, indices, val, is_zb)
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
    if need > length(arr), arr(need) = false; end
    arr(si:si+nv-1) = val;
end

function arr = set_2d(arr, indices, val, is_zb)
    sz = size(arr);
    if isempty(arr)
        i1 = 1; i2 = 1;
        if ~isempty(indices)
            if is_zb
                i1 = indices(1) + 1;
            else
                i1 = indices(1);
            end
            if length(indices) >= 2, i2 = indices(2); end
        end
        need_r = i1 + length(val) - 1;
        need_c = i2;
        arr = zeros(need_r, need_c);
        sz = size(arr);
    end
    i1 = 1; i2 = 1;
    if ~isempty(indices)
        if is_zb
            i1 = indices(1) + 1;
        else
            i1 = indices(1);
        end
        if length(indices) >= 2, i2 = indices(2); end
    end
    if i1 > sz(1) || i2 > sz(2)
        new_r = max(sz(1), i1 + length(val) - 1);
        new_c = max(sz(2), i2);
        tmp = zeros(new_r, new_c);
        tmp(1:sz(1), 1:sz(2)) = arr;
        arr = tmp;
        sz = size(arr);
    end
    lin0 = (i2 - 1) * sz(1) + i1;
    total = prod(sz);
    for iv = 1:length(val)
        lin = lin0 + iv - 1;
        if lin > total
            new_c = ceil(lin / sz(1));
            if new_c > sz(2)
                tmp = zeros(sz(1), new_c);
                tmp(1:sz(1), 1:sz(2)) = arr;
                arr = tmp;
                sz = size(arr);
                total = prod(sz);
            end
        end
        c = ceil(lin / sz(1));
        r = lin - (c-1) * sz(1);
        arr(r, c) = val(iv);
    end
end

function arr = set_2d_logical(arr, indices, val, is_zb)
    sz = size(arr);
    if isempty(arr)
        i1 = 1; i2 = 1;
        if ~isempty(indices)
            if is_zb
                i1 = indices(1) + 1;
            else
                i1 = indices(1);
            end
            if length(indices) >= 2, i2 = indices(2); end
        end
        need_r = i1 + length(val) - 1;
        need_c = i2;
        arr = true(need_r, need_c);
        sz = size(arr);
    end
    i1 = 1; i2 = 1;
    if ~isempty(indices)
        if is_zb
            i1 = indices(1) + 1;
        else
            i1 = indices(1);
        end
        if length(indices) >= 2, i2 = indices(2); end
    end
    if i1 > sz(1) || i2 > sz(2)
        new_r = max(sz(1), i1 + length(val) - 1);
        new_c = max(sz(2), i2);
        tmp = true(new_r, new_c);
        tmp(1:sz(1), 1:sz(2)) = arr;
        arr = tmp;
        sz = size(arr);
    end
    lin0 = (i2 - 1) * sz(1) + i1;
    total = prod(sz);
    for iv = 1:length(val)
        lin = lin0 + iv - 1;
        if lin > total
            new_c = ceil(lin / sz(1));
            if new_c > sz(2)
                tmp = true(sz(1), new_c);
                tmp(1:sz(1), 1:sz(2)) = arr;
                arr = tmp;
                sz = size(arr);
                total = prod(sz);
            end
        end
        c = ceil(lin / sz(1));
        r = lin - (c-1) * sz(1);
        arr(r, c) = val(iv);
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
    val = logical([]);
    for i = 1:length(parts)
        s = upper(strtrim(parts{i}));
        if isempty(s), continue; end
        rep = regexp(s, '^(\d+)\*(.+)$', 'tokens');
        if ~isempty(rep)
            n = str2double(rep{1}{1});
            v = strrep(rep{1}{2}, '.', '');
            lv = strcmp(v, 'TRUE') || strcmp(v, 'T');
            val = [val, repmat(lv, 1, n)];
        else
            s = strrep(s, '.', '');
            val = [val, strcmp(s, 'TRUE') || strcmp(s, 'T')];
        end
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

function vstr = strip_trailing_comma(vstr)
    vstr = strtrim(vstr);
    if ~isempty(vstr) && vstr(end) == ','
        vstr = strtrim(vstr(1:end-1));
    end
end
