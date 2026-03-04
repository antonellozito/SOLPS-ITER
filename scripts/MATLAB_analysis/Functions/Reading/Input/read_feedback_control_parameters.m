function feedback_control = read_feedback_control_parameters(simulation)

% read_feedback_control_parameters reads the b2.feedback_control.parameters
% containing the feedback control settings for B2.5
% Output is a struct "feedback_control" with all the data fields
% in the b2.feedback_control.parameters file.
%
% Each parameter is stored as a substruct with two fields:
%   .value       - the numeric/char/logical value
%   .description - a char containing the documentation from b2cdcn.F
%
% Structured grid: reads the /FEEDBACK_CONTROL/ namelist from b2mod_feedback,
%   containing vacuum_communication_* and na_feedback_* variables.
% Unstructured grid: reads from both b2mod_feedback (na_feedback_* subset) and
%   b2us_feedback (fb_* variables). Both old (na_feedback_*) and new (fb_*)
%   styles can appear in the same file.

%% PRELIMINARY OPERATIONS

% Load the files and read the version
index = find(contains({simulation.run.name},'b2.feedback_control.parameters'));
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

% Number of atomic species (NATM) — use natm from simulation if available
if isfield(simulation, 'natm')
    natm = simulation.natm;
else
    natm = ns; % fallback
end

% Fixed parameters
nvac    = 4;
nvacreg = 4;

%% READ DOCUMENTATION FROM b2cdcn.F

descriptions = read_feedback_control_descriptions(simulation.SOLPSTOP, grid_version);

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
        feedback_control.version = make_param(first_nonempty, '');
        idx_newline = find(raw == char(10), 1, 'first');
        if ~isempty(idx_newline)
            raw = raw(idx_newline+1:end);
        end
    else
        feedback_control.version = make_param('', '');
    end

    % Extract the namelist block
    idx_start = regexpi(raw, '&\s*FEEDBACK_CONTROL');
    if isempty(idx_start)
        nml_str = '';
    else
        in_string = false;
        idx_end = [];
        for ic = idx_start(1)+19 : length(raw)
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
    feedback_control.version = make_param('', '');
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

% --- vacuum_communication_* variables (both grid versions) ---

% Scalar integer
feedback_control.vacuum_communication = make_param(0, desc('vacuum_communication'));

% 1D integer arrays (nvac)
feedback_control.vacuum_communication_nreg   = make_param(zeros(1, nvac), desc('vacuum_communication_nreg'));
feedback_control.vacuum_communication_method = make_param(zeros(1, nvac), desc('vacuum_communication_method'));

% 2D integer arrays (nvacreg, nvac), default -2
feedback_control.vacuum_communication_iy  = make_param(-2 * ones(nvacreg, nvac), desc('vacuum_communication_iy'));
feedback_control.vacuum_communication_ix1 = make_param(-2 * ones(nvacreg, nvac), desc('vacuum_communication_ix1'));
feedback_control.vacuum_communication_ix2 = make_param(-2 * ones(nvacreg, nvac), desc('vacuum_communication_ix2'));

% 2D real arrays (0:nsdmax-1, nvac) — zero-based first dim
feedback_control.vacuum_communication_alpha = make_param(zeros(ns, nvac), desc('vacuum_communication_alpha'));
feedback_control.vacuum_communication_beta  = make_param(ones(ns, nvac), desc('vacuum_communication_beta'));

% --- na_feedback_* variables (both grid versions, different subsets) ---
% All are (0:DEF_NATM-1), zero-based

% 1D real arrays (natm)
feedback_control.na_feedback_target    = make_param(zeros(1, natm), desc('na_feedback_target'));
feedback_control.na_feedback_time      = make_param(zeros(1, natm), desc('na_feedback_time'));
feedback_control.na_feedback_alpha     = make_param(0.001 * ones(1, natm), desc('na_feedback_alpha'));
feedback_control.na_feedback_beta      = make_param(ones(1, natm), desc('na_feedback_beta'));
feedback_control.na_feedback_const     = make_param(zeros(1, natm), desc('na_feedback_const'));
feedback_control.na_feedback_puff_min  = make_param(zeros(1, natm), desc('na_feedback_puff_min'));
feedback_control.na_feedback_puff_max  = make_param(zeros(1, natm), desc('na_feedback_puff_max'));
feedback_control.na_feedback_overshoot = make_param(zeros(1, natm), desc('na_feedback_overshoot'));

% 1D integer arrays (natm)
feedback_control.na_feedback_choice   = make_param(zeros(1, natm), desc('na_feedback_choice'));
feedback_control.na_feedback_option   = make_param(zeros(1, natm), desc('na_feedback_option'));
feedback_control.na_feedback_actuator = make_param(zeros(1, natm), desc('na_feedback_actuator'));
feedback_control.na_feedback_ix1      = make_param(-2 * ones(1, natm), desc('na_feedback_ix1'));
feedback_control.na_feedback_ix2      = make_param(-2 * ones(1, natm), desc('na_feedback_ix2'));
feedback_control.na_feedback_iy1      = make_param(-2 * ones(1, natm), desc('na_feedback_iy1'));
feedback_control.na_feedback_iy2      = make_param(-2 * ones(1, natm), desc('na_feedback_iy2'));

% na_feedback_ib: default 0 for Structured, -1 for Unstructured
if strcmp(grid_version, 'Structured')
    feedback_control.na_feedback_ib = make_param(zeros(1, natm), desc('na_feedback_ib'));
else
    feedback_control.na_feedback_ib = make_param(-1 * ones(1, natm), desc('na_feedback_ib'));
end

% --- Structured-grid-only na_feedback_* variables ---
if strcmp(grid_version, 'Structured')
    feedback_control.na_feedback_gamma        = make_param(0.01 * ones(1, natm), desc('na_feedback_gamma'));
    feedback_control.na_feedback_it           = make_param(zeros(1, natm), desc('na_feedback_it'));
    feedback_control.na_feedback_actuator_min = make_param(zeros(1, natm), desc('na_feedback_actuator_min'));
    feedback_control.na_feedback_actuator_max = make_param(zeros(1, natm), desc('na_feedback_actuator_max'));
    feedback_control.na_feedback_inverse      = make_param(false(1, natm), desc('na_feedback_inverse'));
    % max_na_feedback_current is 1-based (DEF_NATM), not zero-based
    feedback_control.max_na_feedback_current  = make_param(zeros(1, natm), desc('max_na_feedback_current'));
end

% --- Unstructured-grid-only fb_* variables (from b2us_feedback) ---
% All fb_* arrays are sized DEF_NATM (1-based), but we only store up to
% what is read. nfb tells how many feedbacks are defined.
if strcmp(grid_version, 'Unstructured')
    feedback_control.nfb                = make_param(0, desc('nfb'));
    feedback_control.fb_type            = make_param(zeros(1, natm), desc('fb_type'));
    feedback_control.fb_rescale_option  = make_param(zeros(1, natm), desc('fb_rescale_option'));
    feedback_control.fb_actuator        = make_param(zeros(1, natm), desc('fb_actuator'));
    feedback_control.fb_target          = make_param(zeros(1, natm), desc('fb_target'));
    feedback_control.fb_type_inverse    = make_param(false(1, natm), desc('fb_type_inverse'));
    feedback_control.fb_species         = make_param(zeros(1, natm), desc('fb_species'));
    feedback_control.fb_time            = make_param(zeros(1, natm), desc('fb_time'));
    feedback_control.fb_alpha           = make_param(0.001 * ones(1, natm), desc('fb_alpha'));
    feedback_control.fb_beta            = make_param(ones(1, natm), desc('fb_beta'));
    feedback_control.fb_const           = make_param(zeros(1, natm), desc('fb_const'));
    feedback_control.fb_ib              = make_param(-1 * ones(1, natm), desc('fb_ib'));
    feedback_control.fb_istra           = make_param(zeros(1, natm), desc('fb_istra'));
    feedback_control.fb_puff_min        = make_param(zeros(1, natm), desc('fb_puff_min'));
    feedback_control.fb_puff_max        = make_param(zeros(1, natm), desc('fb_puff_max'));
    feedback_control.fb_overshoot       = make_param(zeros(1, natm), desc('fb_overshoot'));
    feedback_control.fb_regp            = make_param(zeros(natm, 2), desc('fb_regp'));
    feedback_control.fb_reg             = make_param(zeros(1, 1000), desc('fb_reg'));
    feedback_control.fb_reg_par         = make_param(zeros(natm, 2), desc('fb_reg_par'));
end

%% BUILD THE VARIABLE CATALOGUE
% Format: {name, type, zero_based_flag}
% Types: si=scalar int, sr=scalar real, sl=scalar logical,
%        1i=1D int, 1r=1D real, 1l=1D logical, 2i=2D int, 2r=2D real

catalogue = {
    % Shared vacuum_communication variables
    'vacuum_communication',        'si', false;
    'vacuum_communication_nreg',   '1i', false;
    'vacuum_communication_method', '1i', false;
    'vacuum_communication_iy',     '2i', false;
    'vacuum_communication_ix1',    '2i', false;
    'vacuum_communication_ix2',    '2i', false;
    'vacuum_communication_alpha',  '2r', true;   % zero-based 1st dim
    'vacuum_communication_beta',   '2r', true;   % zero-based 1st dim
    % Shared na_feedback_* variables (both versions)
    'na_feedback_target',          '1r', true;
    'na_feedback_time',            '1r', true;
    'na_feedback_choice',          '1i', true;
    'na_feedback_option',          '1i', true;
    'na_feedback_actuator',        '1i', true;
    'na_feedback_alpha',           '1r', true;
    'na_feedback_beta',            '1r', true;
    'na_feedback_const',           '1r', true;
    'na_feedback_ix1',             '1i', true;
    'na_feedback_ix2',             '1i', true;
    'na_feedback_iy1',             '1i', true;
    'na_feedback_iy2',             '1i', true;
    'na_feedback_ib',              '1i', true;
    'na_feedback_puff_min',        '1r', true;
    'na_feedback_puff_max',        '1r', true;
    'na_feedback_overshoot',       '1r', true;
};

% Structured-only variables
if strcmp(grid_version, 'Structured')
    catalogue = [catalogue; {
        'na_feedback_gamma',        '1r', true;
        'na_feedback_it',           '1i', true;
        'na_feedback_actuator_min', '1r', true;
        'na_feedback_actuator_max', '1r', true;
        'na_feedback_inverse',      '1l', true;
        'max_na_feedback_current',  '1r', false;  % 1-based (DEF_NATM)
    }];
end

% Unstructured-only fb_* variables (from b2us_feedback)
% Note: fb_rescale_option is the Fortran variable name; the b2cdcn
% documentation calls it FB_RESCALE but the actual namelist variable
% is fb_rescale_option. We accept both names.
if strcmp(grid_version, 'Unstructured')
    catalogue = [catalogue; {
        'nfb',                'si', false;
        'fb_type',            '1i', false;
        'fb_rescale_option',  '1i', false;
        'fb_actuator',        '1i', false;
        'fb_target',          '1r', false;
        'fb_type_inverse',    '1l', false;
        'fb_species',         '1i', false;
        'fb_time',            '1r', false;
        'fb_alpha',           '1r', false;
        'fb_beta',            '1r', false;
        'fb_const',           '1r', false;
        'fb_ib',              '1i', false;
        'fb_istra',           '1i', false;
        'fb_puff_min',        '1r', false;
        'fb_puff_max',        '1r', false;
        'fb_overshoot',       '1r', false;
        'fb_regp',            '2i', false;
        'fb_reg',             '1i', false;
        'fb_reg_par',         '2i', false;
    }];
end

cat_names = catalogue(:,1);
cat_types = catalogue(:,2);
cat_zb    = catalogue(:,3);

%% TOKENIZE AND PROCESS THE NAMELIST

nml_body = regexprep(nml_str, '&\s*FEEDBACK_CONTROL', '', 'ignorecase');
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
    feedback_control.grid_version = make_param(grid_version, '');
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
                feedback_control.(lhs).value = val(1);
            end
        case 'sr'
            val = parse_real_values(vstr);
            if ~isempty(val)
                feedback_control.(lhs).value = val(1);
            end
        case 'sl'
            val = parse_logical_values(vstr);
            if ~isempty(val)
                feedback_control.(lhs).value = val(1);
            end
        case '1i'
            val = parse_int_values(vstr);
            if ~isempty(val)
                feedback_control.(lhs).value = ...
                    set_1d(feedback_control.(lhs).value, indices, val, is_zb);
            end
        case '1r'
            val = parse_real_values(vstr);
            if ~isempty(val)
                feedback_control.(lhs).value = ...
                    set_1d(feedback_control.(lhs).value, indices, val, is_zb);
            end
        case '1l'
            val = parse_logical_values(vstr);
            if ~isempty(val)
                feedback_control.(lhs).value = ...
                    set_1d_logical(feedback_control.(lhs).value, indices, val, is_zb);
            end
        case '2i'
            val = parse_int_values(vstr);
            if ~isempty(val)
                feedback_control.(lhs).value = ...
                    set_2d(feedback_control.(lhs).value, indices, val, is_zb);
            end
        case '2r'
            val = parse_real_values(vstr);
            if ~isempty(val)
                feedback_control.(lhs).value = ...
                    set_2d(feedback_control.(lhs).value, indices, val, is_zb);
            end
    end
end

%% POST-PROCESSING

% Structured-only: handle obsolete puff_min/puff_max -> actuator_min/actuator_max
% From Fortran: if puff_max is set and actuator_max is not, copy over
if strcmp(grid_version, 'Structured')
    if any(abs(feedback_control.na_feedback_puff_max.value) ~= 0)
        if all(abs(feedback_control.na_feedback_actuator_max.value) == 0)
            feedback_control.na_feedback_actuator_max.value = ...
                feedback_control.na_feedback_puff_max.value;
        end
    end
    if any(abs(feedback_control.na_feedback_puff_min.value) ~= 0)
        if all(abs(feedback_control.na_feedback_actuator_min.value) == 0)
            feedback_control.na_feedback_actuator_min.value = ...
                feedback_control.na_feedback_puff_min.value;
        end
    end
end

feedback_control.grid_version = make_param(grid_version, '');

end


%% PARAMETER STRUCT CONSTRUCTOR

function p = make_param(value, description)
    p.value = value;
    p.description = description;
end


%% DOCUMENTATION PARSER

function descriptions = read_feedback_control_descriptions(SOLPSTOP, grid_version)

    descriptions = struct();

    docfile = sprintf('%s/modules/B2.5/src/documentation/b2cdcn.F', SOLPSTOP);
    fid = fopen(docfile, 'r');
    if fid == -1
        return;
    end

    raw_text = fread(fid, '*char')';
    fclose(fid);
    all_lines = strsplit(raw_text, char(10));

    % Find FEEDBACK_CONTROL blocks with
    % 'Found in b2.feedback_control.parameters'
    block_starts = [];
    block_ends = [];
    for iL = 1:length(all_lines)
        ln = all_lines{iL};
        if ~isempty(regexp(ln, '^\*\s+NAMELIST\s+/FEEDBACK_CONTROL/', 'once'))
            if iL < length(all_lines) && ...
               ~isempty(strfind(all_lines{iL+1}, 'Found in b2.feedback_control.parameters'))
                block_starts(end+1) = iL;
            end
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

    current_var = '';
    current_desc_lines = {};
    for iL = block_start:block_end
        ln = all_lines{iL};
        if isempty(ln) || ln(1) ~= '*'
            continue;
        end
        after_star = ln(2:end);
        var_match = regexp(after_star, '^\s{1,4}([A-Z]\w*)\s+-\s+', 'tokens');
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
    % Determine starting row and column
    i1 = 1; i2 = 1;
    if ~isempty(indices)
        if is_zb
            i1 = indices(1) + 1;
        else
            i1 = indices(1);
        end
        if length(indices) >= 2, i2 = indices(2); end
    end

    % Initialize if empty
    if isempty(arr)
        arr = zeros(i1 + length(val) - 1, i2);
    end
    sz = size(arr);

    % Grow if needed
    need_r = i1 + length(val) - 1;
    need_c = i2;
    if need_r > sz(1) || need_c > sz(2)
        new_r = max(sz(1), need_r);
        new_c = max(sz(2), need_c);
        tmp = zeros(new_r, new_c);
        tmp(1:sz(1), 1:sz(2)) = arr;
        arr = tmp;
        sz = size(arr);
    end

    % Assign values in column-major order starting from (i1, i2)
    lin0 = (i2 - 1) * sz(1) + i1;
    for iv = 1:length(val)
        lin = lin0 + iv - 1;
        c = ceil(lin / sz(1));
        r = lin - (c - 1) * sz(1);
        if c > sz(2)
            tmp = zeros(sz(1), c);
            tmp(1:sz(1), 1:sz(2)) = arr;
            arr = tmp;
            sz = size(arr);
        end
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
    val = false(1, length(parts));
    for i = 1:length(parts)
        s = upper(strtrim(parts{i}));
        s = strrep(s, '.', '');
        val(i) = strcmp(s, 'TRUE') || strcmp(s, 'T');
    end
end

function vstr = strip_trailing_comma(vstr)
    vstr = strtrim(vstr);
    if ~isempty(vstr) && vstr(end) == ','
        vstr = strtrim(vstr(1:end-1));
    end
end
