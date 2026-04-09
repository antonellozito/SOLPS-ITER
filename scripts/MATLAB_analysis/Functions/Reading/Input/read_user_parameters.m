function user_parameters = read_user_parameters(simulation)

% read_user_parameters reads the b2.user.parameters containing the
% input parameters for user-specific diagnostics for B2.5
% Output is a struct "user_parameters" with all the data fields
% in the b2.user.parameters file.

% Each parameter is stored as a substruct with four fields:
%   .value       - the numeric/char/logical value
%   .default     - the default entry from b2input.xml
%   .type        - the type entry from b2input.xml
%   .description - the description entry from b2input.xml

%% PRELIMINARY OPERATIONS

% Load the files and read the version
index = find(contains({simulation.run.name},'b2.user.parameters'));
file_ok = ~isempty(index);

if file_ok
    file = simulation.run(index).file;
    fid = fopen(file);
    if (fid == -1)
        file_ok = false;
    end
end

% Determine grid version and number of cuts
grid_version = simulation.grid_version; % 'Structured' or 'Unstructured'
geometry = read_b2fgmtry(simulation);
ncut = geometry.nncut;

%% READ DOCUMENTATION FROM b2input.xml

descriptions = read_user_descriptions(simulation.SOLPSTOP, grid_version);

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
        user_parameters.version = make_param(first_nonempty, '');
        idx_newline = find(raw == char(10), 1, 'first');
        if ~isempty(idx_newline)
            raw = raw(idx_newline+1:end);
        end
    else
        user_parameters.version = make_param('', '');
    end

    % Extract the namelist block
    idx_start = regexpi(raw, '&\s*USER');
    if isempty(idx_start)
        nml_str = '';
    else
        in_string = false;
        idx_end = [];
        for ic = idx_start(1)+5 : length(raw)
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
    user_parameters.version = make_param('', '');
    nml_str = '';
end

%% SET DEFAULT VALUES

% Helper to get XML metadata for a variable
    function d = desc(varname)
        if isfield(descriptions, lower(varname))
            d = descriptions.(lower(varname));
        else
            d = empty_param_metadata();
        end
    end

% Fixed parameters
npfrgrpd = 6;
nntrgrpd = 16;

% Scalar defaults
user_parameters.lpfrb_i   = make_param(0, desc('lpfrb_i'));
user_parameters.lpfrb_o   = make_param(0, desc('lpfrb_o'));
user_parameters.lpfrt_i   = make_param(0, desc('lpfrt_i'));
user_parameters.lpfrt_o   = make_param(0, desc('lpfrt_o'));
user_parameters.j_he_at   = make_param(0, desc('j_he_at'));
user_parameters.j_ne_at   = make_param(0, desc('j_ne_at'));
user_parameters.lpfrs_pmp = make_param(0, desc('lpfrs_pmp'));
user_parameters.npfrgrp   = make_param(0, desc('npfrgrp'));
user_parameters.nntrgrp   = make_param(0, desc('nntrgrp'));
user_parameters.fusion_power    = make_param(0.0, desc('fusion_power'));
user_parameters.spmp_he_to_d   = make_param(1.0, desc('spmp_he_to_d'));
user_parameters.spmp_nom       = make_param(0.0, desc('spmp_nom'));
user_parameters.te_det_threshold = make_param(2.0, desc('te_det_threshold'));
user_parameters.q95_albll      = make_param(0.0, desc('q95_albll'));
user_parameters.r0_albll       = make_param(0.0, desc('r0_albll'));
user_parameters.b0_albll       = make_param(0.0, desc('b0_albll'));
user_parameters.scale_he       = make_param(false, desc('scale_he'));
user_parameters.print_isat     = make_param(false, desc('print_isat'));
user_parameters.write_nml_user = make_param(true, desc('write_nml_user'));
user_parameters.user_filename  = make_param('b2.user.parameters', desc('user_filename'));

% Fixed-size integer arrays
user_parameters.j_h_at   = make_param(zeros(1, 3), desc('j_h_at'));
user_parameters.ipfrgrp  = make_param(zeros(1, npfrgrpd), desc('ipfrgrp'));
user_parameters.jpfrgrp  = make_param(zeros(1, npfrgrpd), desc('jpfrgrp'));
user_parameters.intrgrp  = make_param(zeros(1, nntrgrpd), desc('intrgrp'));
user_parameters.jntrgrp  = make_param(zeros(1, nntrgrpd), desc('jntrgrp'));

% Fixed-size string arrays
user_parameters.gpfrgrp  = make_param(repmat({' '}, 1, npfrgrpd), desc('gpfrgrp'));
user_parameters.gntrgrp  = make_param(repmat({' '}, 1, nntrgrpd), desc('gntrgrp'));

% Dynamic arrays (size NLIM, unknown — start empty, grow on read)
user_parameters.lhetrgts = make_param([], desc('lhetrgts'));
user_parameters.lpfrgrp  = make_param([], desc('lpfrgrp'));
user_parameters.lntrgrp  = make_param([], desc('lntrgrp'));

% Dynamic 2D array: l_h_mol (NMOL, 3) — start empty
user_parameters.l_h_mol  = make_param([], desc('l_h_mol'));

% trgshp: Fortran (NCUT*2), default 1.0
user_parameters.trgshp   = make_param(ones(1, ncut*2), desc('trgshp'));

% Filedata: logical array (size 12 for Structured, 10 for Unstructured)
if strcmp(grid_version, 'Structured')
    user_parameters.filedata = make_param(true(1, 12), desc('filedata'));
else
    user_parameters.filedata = make_param(true(1, 10), desc('filedata'));
end

% Unstructured-grid-only defaults
if strcmp(grid_version, 'Unstructured')
    user_parameters.rzomp    = make_param(zeros(2, 2), desc('rzomp'));
    user_parameters.rzimp    = make_param(zeros(2, 2), desc('rzimp'));
    user_parameters.npfr_cvs = make_param(0, desc('npfr_cvs'));
    user_parameters.pfr_cvs  = make_param(zeros(1, 100), desc('pfr_cvs'));
end

%% BUILD THE VARIABLE CATALOGUE

catalogue = {
    'lpfrb_i',          'si', false;
    'lpfrb_o',          'si', false;
    'lpfrt_i',          'si', false;
    'lpfrt_o',          'si', false;
    'j_he_at',          'si', false;
    'j_ne_at',          'si', false;
    'lpfrs_pmp',        'si', false;
    'npfrgrp',          'si', false;
    'nntrgrp',          'si', false;
    'fusion_power',     'sr', false;
    'spmp_he_to_d',     'sr', false;
    'spmp_nom',         'sr', false;
    'te_det_threshold', 'sr', false;
    'q95_albll',        'sr', false;
    'r0_albll',         'sr', false;
    'b0_albll',         'sr', false;
    'scale_he',         'sl', false;
    'print_isat',       'sl', false;
    'write_nml_user',   'sl', false;
    'user_filename',    'ss', false;
    'j_h_at',           '1i', false;
    'ipfrgrp',          '1i', false;
    'jpfrgrp',          '1i', false;
    'intrgrp',          '1i', false;
    'jntrgrp',          '1i', false;
    'lhetrgts',         '1i', false;
    'lpfrgrp',          '1i', false;
    'lntrgrp',          '1i', false;
    'trgshp',           '1r', false;
    'filedata',         '1l', false;
    'gpfrgrp',          '1s', false;
    'gntrgrp',          '1s', false;
    'l_h_mol',          '2i', false;
};

if strcmp(grid_version, 'Unstructured')
    catalogue = [catalogue; {
        'rzomp',        '2r', false;
        'rzimp',        '2r', false;
        'npfr_cvs',     'si', false;
        'pfr_cvs',      '1i', false;
    }];
end

cat_names = catalogue(:,1);
cat_types = catalogue(:,2);
cat_zb    = catalogue(:,3);

%% TOKENIZE AND PROCESS THE NAMELIST

nml_body = regexprep(nml_str, '&\s*USER', '', 'ignorecase');
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
    user_parameters.grid_version = make_param(grid_version, '');
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
                user_parameters.(lhs).value = val(1);
            end
        case 'sr'
            val = parse_real_values(vstr);
            if ~isempty(val)
                user_parameters.(lhs).value = val(1);
            end
        case 'sl'
            val = parse_logical_values(vstr);
            if ~isempty(val)
                user_parameters.(lhs).value = val(1);
            end
        case 'ss'
            val = parse_string_value(vstr);
            if ~isempty(val)
                user_parameters.(lhs).value = val;
            end
        case '1i'
            val = parse_int_values(vstr);
            if ~isempty(val)
                user_parameters.(lhs).value = ...
                    set_1d(user_parameters.(lhs).value, indices, val, is_zb);
            end
        case '1r'
            val = parse_real_values(vstr);
            if ~isempty(val)
                user_parameters.(lhs).value = ...
                    set_1d(user_parameters.(lhs).value, indices, val, is_zb);
            end
        case '1l'
            val = parse_logical_values(vstr);
            if ~isempty(val)
                user_parameters.(lhs).value = ...
                    set_1d_logical(user_parameters.(lhs).value, indices, val, is_zb);
            end
        case '1s'
            val = parse_string_list(vstr);
            if ~isempty(val)
                user_parameters.(lhs).value = ...
                    set_1d_str(user_parameters.(lhs).value, indices, val, is_zb);
            end
        case '2i'
            val = parse_int_values(vstr);
            if ~isempty(val)
                user_parameters.(lhs).value = ...
                    set_2d(user_parameters.(lhs).value, indices, val, is_zb);
            end
        case '2r'
            val = parse_real_values(vstr);
            if ~isempty(val)
                user_parameters.(lhs).value = ...
                    set_2d(user_parameters.(lhs).value, indices, val, is_zb);
            end
    end
end

user_parameters.grid_version = make_param(grid_version, '');

end


%% DOCUMENTATION PARSER

function descriptions = read_user_descriptions(SOLPSTOP, ~)
    descriptions = read_b2input_descriptions(SOLPSTOP, 'b2.user.parameters');
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
