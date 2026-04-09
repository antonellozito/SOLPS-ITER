function transport_inputfile = read_transport_inputfile(simulation)

% read_transport_inputfile reads the b2.transport.inputfile containing the
% transport coefficient profiles for B2.5
% Output is a struct "transport_inputfile" with all the data fields
% in the b2.transport.inputfile file.

% Each parameter is stored as a substruct with four fields:
%   .value       - the numeric/char/logical value
%   .default     - the default entry from b2input.xml
%   .type        - the type entry from b2input.xml
%   .description - the description entry from b2input.xml

%% PRELIMINARY OPERATIONS

% Load the files and read the version
index = find(contains({simulation.run.name},'b2.transport.inputfile'));
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

% Fixed parameters from b2mod_input_profile
nkind_data  = 2;
nkind_coeff = 9;
nscale      = 10;

%% READ DOCUMENTATION FROM b2input.xml

descriptions = read_transport_inputfile_descriptions(simulation.SOLPSTOP, grid_version);

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
        transport_inputfile.version = make_param(first_nonempty, '');
        idx_newline = find(raw == char(10), 1, 'first');
        if ~isempty(idx_newline)
            raw = raw(idx_newline+1:end);
        end
    else
        transport_inputfile.version = make_param('', '');
    end

    % Extract the namelist block
    idx_start = regexpi(raw, '&\s*TRANSPORT');
    if isempty(idx_start)
        nml_str = '';
    else
        in_string = false;
        idx_end = [];
        for ic = idx_start(1)+11 : length(raw)
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
    transport_inputfile.version = make_param('', '');
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

% 3D integer arrays: (nkind_data, nkind_coeff, 0:ns)
transport_inputfile.ndata   = make_param(zeros(nkind_data, nkind_coeff, ns), desc('ndata'));

% 4D real array: (3, nrr, nkind_coeff, 0:ns)
transport_inputfile.tdata   = make_param([], desc('tdata'));

% 3D integer array: (ns, nkind_coeff, 0:ns)
transport_inputfile.addspec = make_param(-5 * ones(ns, nkind_coeff, ns), desc('addspec'));

% 2D logical: (NNREGMAX/CVREGMAX, nkind_coeff)
transport_inputfile.region_flags = make_param([], desc('region_flags'));

% Scalar logicals
transport_inputfile.no_pflux = make_param(false, desc('no_pflux'));
transport_inputfile.no_div   = make_param(false, desc('no_div'));

% 1D logical array
transport_inputfile.poloidal_scaling = make_param(false(1, nscale), desc('poloidal_scaling'));

% 1D real arrays
transport_inputfile.scaling_strength = make_param(zeros(1, nscale), desc('scaling_strength'));
transport_inputfile.scaling_width    = make_param(zeros(1, nscale), desc('scaling_width'));

% 1D integer arrays
transport_inputfile.scaling_ix_begin = make_param(-2 * ones(1, nscale), desc('scaling_ix_begin'));
transport_inputfile.scaling_ix_end   = make_param(-2 * ones(1, nscale), desc('scaling_ix_end'));

% Scalar real
transport_inputfile.elm_time_period = make_param(0.0, desc('elm_time_period'));

% Scalar integer
transport_inputfile.elm_ix_begin = make_param(-2, desc('elm_ix_begin'));
transport_inputfile.elm_ix_end   = make_param(-2, desc('elm_ix_end'));

% Structured-grid-only defaults
if strcmp(grid_version, 'Structured')
    transport_inputfile.transport_filename    = make_param('b2.transport.inputfile', desc('transport_filename'));
    transport_inputfile.transport_time_mod    = make_param(0.0, desc('transport_time_mod'));
    transport_inputfile.transport_time_switch = make_param(0.0, desc('transport_time_switch'));
    transport_inputfile.elm_dynamics_multiple = make_param(false, desc('elm_dynamics_multiple'));
    transport_inputfile.elm_time_begin       = make_param(zeros(1, nkind_coeff), desc('elm_time_begin'));
    transport_inputfile.elm_time_plateau     = make_param(zeros(1, nkind_coeff), desc('elm_time_plateau'));
    transport_inputfile.elm_time_recovery    = make_param(zeros(1, nkind_coeff), desc('elm_time_recovery'));
    transport_inputfile.elm_time_end         = make_param(zeros(1, nkind_coeff), desc('elm_time_end'));
    transport_inputfile.elm_crash_factor     = make_param(1.0e-10 * ones(1, nkind_coeff), desc('elm_crash_factor'));
    transport_inputfile.elm_recovery_factor  = make_param(1.0e-10 * ones(1, nkind_coeff), desc('elm_recovery_factor'));
    transport_inputfile.elm_ballooning_exp   = make_param(zeros(1, nkind_coeff), desc('elm_ballooning_exp'));
    transport_inputfile.elm_ixref            = make_param(0, desc('elm_ixref'));
end

% Unstructured-grid-only defaults
if strcmp(grid_version, 'Unstructured')
    transport_inputfile.transport_ip_filename    = make_param('b2.transport.inputfile', desc('transport_ip_filename'));
    transport_inputfile.transport_ip_time_mod    = make_param(0.0, desc('transport_ip_time_mod'));
    transport_inputfile.transport_ip_time_switch = make_param(0.0, desc('transport_ip_time_switch'));
    transport_inputfile.elm_time_begin           = make_param(0.0, desc('elm_time_begin'));
    transport_inputfile.elm_time_end             = make_param(0.0, desc('elm_time_end'));
end

%% BUILD THE VARIABLE CATALOGUE

catalogue = {
    'ndata',              '3i', true;
    'tdata',              '4r', true;
    'addspec',            '3i', true;
    'region_flags',       '2l', false;
    'no_pflux',           'sl', false;
    'no_div',             'sl', false;
    'poloidal_scaling',   '1l', false;
    'scaling_strength',   '1r', false;
    'scaling_width',      '1r', false;
    'scaling_ix_begin',   '1i', false;
    'scaling_ix_end',     '1i', false;
    'elm_time_period',    'sr', false;
    'elm_ix_begin',       'si', false;
    'elm_ix_end',         'si', false;
};

if strcmp(grid_version, 'Structured')
    catalogue = [catalogue; {
        'transport_filename',    'ss', false;
        'transport_time_mod',    'sr', false;
        'transport_time_switch', 'sr', false;
        'elm_dynamics_multiple', 'sl', false;
        'elm_time_begin',        '1r', false;
        'elm_time_plateau',      '1r', false;
        'elm_time_recovery',     '1r', false;
        'elm_time_end',          '1r', false;
        'elm_crash_factor',      '1r', false;
        'elm_recovery_factor',   '1r', false;
        'elm_ballooning_exp',    '1r', false;
        'elm_ixref',             'si', false;
    }];
end

if strcmp(grid_version, 'Unstructured')
    catalogue = [catalogue; {
        'transport_ip_filename',    'ss', false;
        'transport_ip_time_mod',    'sr', false;
        'transport_ip_time_switch', 'sr', false;
        'elm_time_begin',           'sr', false;
        'elm_time_end',             'sr', false;
    }];
end

cat_names = catalogue(:,1);
cat_types = catalogue(:,2);
cat_zb    = catalogue(:,3);

%% TOKENIZE AND PROCESS THE NAMELIST

nml_body = regexprep(nml_str, '&\s*TRANSPORT', '', 'ignorecase');
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
    transport_inputfile.grid_version = make_param(grid_version, '');
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
                transport_inputfile.(lhs).value = val(1);
            end
        case 'sr'
            val = parse_real_values(vstr);
            if ~isempty(val)
                transport_inputfile.(lhs).value = val(1);
            end
        case 'sl'
            val = parse_logical_values(vstr);
            if ~isempty(val)
                transport_inputfile.(lhs).value = val(1);
            end
        case 'ss'
            val = parse_string_value(vstr);
            if ~isempty(val)
                transport_inputfile.(lhs).value = val;
            end
        case '1i'
            val = parse_int_values(vstr);
            if ~isempty(val)
                transport_inputfile.(lhs).value = ...
                    set_1d(transport_inputfile.(lhs).value, indices, val, is_zb);
            end
        case '1r'
            val = parse_real_values(vstr);
            if ~isempty(val)
                transport_inputfile.(lhs).value = ...
                    set_1d(transport_inputfile.(lhs).value, indices, val, is_zb);
            end
        case '1l'
            val = parse_logical_values(vstr);
            if ~isempty(val)
                transport_inputfile.(lhs).value = ...
                    set_1d_logical(transport_inputfile.(lhs).value, indices, val, is_zb);
            end
        case '2l'
            val = parse_logical_values(vstr);
            if ~isempty(val)
                transport_inputfile.(lhs).value = ...
                    set_nd_logical(transport_inputfile.(lhs).value, indices, val, is_zb);
            end
        case '3i'
            val = parse_int_values(vstr);
            if ~isempty(val)
                transport_inputfile.(lhs).value = ...
                    set_nd(transport_inputfile.(lhs).value, indices, val, is_zb);
            end
        case '4r'
            val = parse_real_values(vstr);
            if ~isempty(val)
                transport_inputfile.(lhs).value = ...
                    set_nd(transport_inputfile.(lhs).value, indices, val, is_zb);
            end
    end
end

%% POST-PROCESSING: ENFORCE FULL DIMENSIONS AND APPLY ADDSPEC

% Ensure ndata has full dimensions (nkind_data, nkind_coeff, ns)
ndata_val = transport_inputfile.ndata.value;
if ~isempty(ndata_val)
    sz = size(ndata_val);
    need = [nkind_data, nkind_coeff, ns];
    if length(sz) < 3 || any(sz < need)
        new_sz = max([sz, ones(1, 3-length(sz))], need);
        tmp = zeros(new_sz);
        idx_cell = cell(1, 3);
        for k = 1:3, idx_cell{k} = 1:sz(min(k,length(sz))); end
        tmp(idx_cell{:}) = ndata_val;
        ndata_val = tmp;
    end
else
    ndata_val = zeros(nkind_data, nkind_coeff, ns);
end
transport_inputfile.ndata.value = ndata_val;

% Ensure tdata has full dimensions (3, nrr, nkind_coeff, ns)
% nrr is determined by the data read; if empty, leave as zeros(3,0,9,ns)
tdata_val = transport_inputfile.tdata.value;
if ~isempty(tdata_val)
    sz = size(tdata_val);
    % Pad size to 4D
    while length(sz) < 4, sz(end+1) = 1; end
    need = [3, sz(2), nkind_coeff, ns];
    if any(sz < need)
        new_sz = max(sz, need);
        tmp = zeros(new_sz);
        idx_cell = cell(1, 4);
        for k = 1:4, idx_cell{k} = 1:sz(k); end
        tmp(idx_cell{:}) = tdata_val;
        tdata_val = tmp;
    end
else
    tdata_val = zeros(3, 0, nkind_coeff, ns);
end
transport_inputfile.tdata.value = tdata_val;

% Ensure addspec has full dimensions (ns, nkind_coeff, ns)
addspec_val = transport_inputfile.addspec.value;
if ~isempty(addspec_val)
    sz = size(addspec_val);
    need = [ns, nkind_coeff, ns];
    if length(sz) < 3 || any(sz < need)
        new_sz = max([sz, ones(1, 3-length(sz))], need);
        tmp = -5 * ones(new_sz);
        idx_cell = cell(1, 3);
        for k = 1:3, idx_cell{k} = 1:sz(min(k,length(sz))); end
        tmp(idx_cell{:}) = addspec_val;
        addspec_val = tmp;
    end
else
    addspec_val = -5 * ones(ns, nkind_coeff, ns);
end
transport_inputfile.addspec.value = addspec_val;

% Apply addspec: propagate transport profiles to additional species
% In Fortran (0-based species), addspec(is, kind_coeff, spec) >= 0 means
% species addspec(is,...) gets the same profile as species spec.
% In MATLAB (1-based), species index s corresponds to Fortran spec = s-1.
ndata_val = transport_inputfile.ndata.value;
tdata_val = transport_inputfile.tdata.value;
for ikc = 1:nkind_coeff
    for isp = 1:ns  % isp corresponds to Fortran species isp-1
        % Check if this (kind_coeff, species) has data
        has_data = false;
        for ikd = 1:nkind_data
            if ndata_val(ikd, ikc, isp) > 0
                has_data = true;
                break;
            end
        end
        if ~has_data, continue; end

        % Look at addspec(:, ikc, isp) for additional species
        for is = 1:ns
            target_spec_f = addspec_val(is, ikc, isp); % Fortran 0-based species
            if target_spec_f < 0, continue; end
            target_sp = target_spec_f + 1; % Convert to 1-based MATLAB index
            if target_sp < 1 || target_sp > ns, continue; end

            % Copy ndata from source species to target species
            ndata_val(:, ikc, target_sp) = ndata_val(:, ikc, isp);

            % Copy tdata from source species to target species
            if size(tdata_val, 2) > 0
                tdata_val(:, :, ikc, target_sp) = tdata_val(:, :, ikc, isp);
            end
        end
    end
end
transport_inputfile.ndata.value = ndata_val;
transport_inputfile.tdata.value = tdata_val;

% Mark unused (kind_coeff, species) slices in tdata with NaN.
% A slice is "unused" if ndata(:, ikc, isp) is all zero, meaning no
% profile data points were defined (either explicitly or via addspec).
if size(tdata_val, 2) > 0
    for ikc = 1:nkind_coeff
        for isp = 1:ns
            if all(ndata_val(:, ikc, isp) == 0)
                % No data at all for this (kind_coeff, species)
                tdata_val(:, :, ikc, isp) = NaN;
            else
                % Data exists; check if ELM profile (index 3) was provided
                if all(tdata_val(3, :, ikc, isp) == 0)
                    tdata_val(3, :, ikc, isp) = NaN;
                end
            end
        end
    end
    transport_inputfile.tdata.value = tdata_val;
end

transport_inputfile.grid_version = make_param(grid_version, '');

end


%% DOCUMENTATION PARSER

function descriptions = read_transport_inputfile_descriptions(SOLPSTOP, ~)
    descriptions = read_b2input_descriptions(SOLPSTOP, 'b2.transport.inputfile');
end

function arr = set_nd(arr, indices, val, is_zb)
% Generic N-dimensional array setter for numeric arrays.
    if isempty(arr)
        % Array not yet allocated; determine size from indices
        nd = max(length(indices), 1);
        sz = ones(1, nd);
        for k = 1:length(indices)
            if k == length(indices) && is_zb
                sz(k) = indices(k) + 1 + length(val) - 1;
            else
                sz(k) = max(1, indices(k)) + length(val) - 1;
            end
        end
        if nd == 1
            arr = zeros(1, sz(1));
        else
            arr = zeros(sz);
        end
    end
    sz = size(arr);
    nd = ndims(arr);
    % Compute linear start index
    subs = ones(1, nd);
    for k = 1:min(length(indices), nd)
        if k == nd && is_zb
            subs(k) = indices(k) + 1;
        else
            subs(k) = max(1, indices(k));
        end
    end
    % Grow array if any subscript exceeds current size
    need_grow = false;
    new_sz = sz;
    for k = 1:nd
        if subs(k) > sz(k)
            new_sz(k) = subs(k);
            need_grow = true;
        end
    end
    last_sub = subs;
    last_sub(1) = subs(1) + length(val) - 1;
    if last_sub(1) > new_sz(1)
        new_sz(1) = last_sub(1);
        need_grow = true;
    end
    if need_grow
        tmp = zeros(new_sz);
        if prod(sz) > 0
            idx_cell = cell(1, nd);
            for k = 1:nd, idx_cell{k} = 1:sz(k); end
            tmp(idx_cell{:}) = arr;
        end
        arr = tmp;
        sz = new_sz;
    end
    % Place values (column-major: values fill along first dimension)
    lin0 = sub2ind_custom(sz, subs);
    for iv = 1:length(val)
        lin = lin0 + iv - 1;
        arr(lin) = val(iv);
    end
end

function arr = set_nd_logical(arr, indices, val, is_zb)
% Generic N-dimensional array setter for logical arrays.
    if isempty(arr)
        nd = max(length(indices), 1);
        sz = ones(1, nd);
        for k = 1:length(indices)
            if k == length(indices) && is_zb
                sz(k) = indices(k) + 1 + length(val) - 1;
            else
                sz(k) = max(1, indices(k)) + length(val) - 1;
            end
        end
        if nd == 1
            arr = true(1, sz(1));
        else
            arr = true(sz);
        end
    end
    sz = size(arr);
    nd = ndims(arr);
    subs = ones(1, nd);
    for k = 1:min(length(indices), nd)
        if k == nd && is_zb
            subs(k) = indices(k) + 1;
        else
            subs(k) = max(1, indices(k));
        end
    end
    need_grow = false;
    new_sz = sz;
    for k = 1:nd
        if subs(k) > sz(k)
            new_sz(k) = subs(k);
            need_grow = true;
        end
    end
    last_sub = subs;
    last_sub(1) = subs(1) + length(val) - 1;
    if last_sub(1) > new_sz(1)
        new_sz(1) = last_sub(1);
        need_grow = true;
    end
    if need_grow
        tmp = true(new_sz);
        if prod(sz) > 0
            idx_cell = cell(1, nd);
            for k = 1:nd, idx_cell{k} = 1:sz(k); end
            tmp(idx_cell{:}) = arr;
        end
        arr = tmp;
        sz = new_sz;
    end
    lin0 = sub2ind_custom(sz, subs);
    for iv = 1:length(val)
        lin = lin0 + iv - 1;
        arr(lin) = val(iv);
    end
end

function lin = sub2ind_custom(sz, subs)
% Compute linear index from subscripts (Fortran column-major order).
    lin = subs(1);
    stride = 1;
    for k = 2:length(sz)
        stride = stride * sz(k-1);
        lin = lin + (subs(k) - 1) * stride;
    end
end
