function sources_profile = read_sources_profile(simulation)

% read_sources_profile reads the b2.sources.profile containing the
% external source profiles for B2.5
% Output is a struct "sources_profile" with all the data fields
% in the b2.sources.profile file.

% Each parameter is stored as a substruct with two fields:
%   .value       - the numeric/char/logical value
%   .description - a char containing the documentation from b2cdcn.F

%% PRELIMINARY OPERATIONS

% Load the files and read the version
index = find(contains({simulation.run.name},'b2.sources.profile'));
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
nkind_data   = 2;
nkind_source = 6;

%% READ DOCUMENTATION FROM b2cdcn.F

descriptions = read_sources_profile_descriptions(simulation.SOLPSTOP, grid_version);

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
        sources_profile.version = make_param(first_nonempty, '');
        idx_newline = find(raw == char(10), 1, 'first');
        if ~isempty(idx_newline)
            raw = raw(idx_newline+1:end);
        end
    else
        sources_profile.version = make_param('', '');
    end

    % Extract the namelist block
    idx_start = regexpi(raw, '&\s*PROFILE');
    if isempty(idx_start)
        nml_str = '';
    else
        in_string = false;
        idx_end = [];
        for ic = idx_start(1)+8 : length(raw)
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
    sources_profile.version = make_param('', '');
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

% 3D integer arrays: (nkind_data, nkind_source, 0:ns) — zero-based last dim
sources_profile.nsdata = make_param(zeros(nkind_data, nkind_source, ns), desc('nsdata'));
sources_profile.nxdata = make_param(zeros(nkind_data, nkind_source, ns), desc('nxdata'));

% 4D real arrays: (2, nrr, nkind_source, 0:ns) — nrr unknown, start empty
sources_profile.sdata = make_param([], desc('sdata'));
sources_profile.xdata = make_param([], desc('xdata'));

% Scalar real
sources_profile.divheat = make_param(0.0, desc('divheat'));

% Scalar string / time defaults
sources_profile.sources_filename    = make_param('b2.sources.profile', desc('sources_filename'));
sources_profile.sources_time_mod    = make_param(0.0, desc('sources_time_mod'));
sources_profile.sources_time_switch = make_param(0.0, desc('sources_time_switch'));

% Structured-grid-only defaults
if strcmp(grid_version, 'Structured')
    sources_profile.ixref_profile = make_param(-2, desc('ixref_profile'));
    sources_profile.iyref_profile = make_param(-2, desc('iyref_profile'));
end

%% BUILD THE VARIABLE CATALOGUE

catalogue = {
    'nsdata',              '3i', true;
    'nxdata',              '3i', true;
    'sdata',               '4r', true;
    'xdata',               '4r', true;
    'divheat',             'sr', false;
    'sources_filename',    'ss', false;
    'sources_time_mod',    'sr', false;
    'sources_time_switch', 'sr', false;
};

if strcmp(grid_version, 'Structured')
    catalogue = [catalogue; {
        'ixref_profile',   'si', false;
        'iyref_profile',   'si', false;
    }];
end

cat_names = catalogue(:,1);
cat_types = catalogue(:,2);
cat_zb    = catalogue(:,3);

%% TOKENIZE AND PROCESS THE NAMELIST

nml_body = regexprep(nml_str, '&\s*PROFILE', '', 'ignorecase');
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
    sources_profile.grid_version = make_param(grid_version, '');
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
                sources_profile.(lhs).value = val(1);
            end
        case 'sr'
            val = parse_real_values(vstr);
            if ~isempty(val)
                sources_profile.(lhs).value = val(1);
            end
        case 'ss'
            val = parse_string_value(vstr);
            if ~isempty(val)
                sources_profile.(lhs).value = val;
            end
        case '3i'
            val = parse_int_values(vstr);
            if ~isempty(val)
                sources_profile.(lhs).value = ...
                    set_nd(sources_profile.(lhs).value, indices, val, is_zb);
            end
        case '4r'
            val = parse_real_values(vstr);
            if ~isempty(val)
                sources_profile.(lhs).value = ...
                    set_nd(sources_profile.(lhs).value, indices, val, is_zb);
            end
    end
end

%% POST-PROCESSING: ENFORCE FULL DIMENSIONS

% Ensure nsdata has full dimensions (nkind_data, nkind_source, ns)
nsdata_val = sources_profile.nsdata.value;
if ~isempty(nsdata_val)
    sz = size(nsdata_val);
    need = [nkind_data, nkind_source, ns];
    if length(sz) < 3 || any(sz < need)
        new_sz = max([sz, ones(1, 3-length(sz))], need);
        tmp = zeros(new_sz);
        idx_cell = cell(1, 3);
        for k = 1:3, idx_cell{k} = 1:sz(min(k,length(sz))); end
        tmp(idx_cell{:}) = nsdata_val;
        nsdata_val = tmp;
    end
else
    nsdata_val = zeros(nkind_data, nkind_source, ns);
end
sources_profile.nsdata.value = nsdata_val;

% Ensure nxdata has full dimensions (nkind_data, nkind_source, ns)
nxdata_val = sources_profile.nxdata.value;
if ~isempty(nxdata_val)
    sz = size(nxdata_val);
    need = [nkind_data, nkind_source, ns];
    if length(sz) < 3 || any(sz < need)
        new_sz = max([sz, ones(1, 3-length(sz))], need);
        tmp = zeros(new_sz);
        idx_cell = cell(1, 3);
        for k = 1:3, idx_cell{k} = 1:sz(min(k,length(sz))); end
        tmp(idx_cell{:}) = nxdata_val;
        nxdata_val = tmp;
    end
else
    nxdata_val = zeros(nkind_data, nkind_source, ns);
end
sources_profile.nxdata.value = nxdata_val;

% Ensure sdata has full dimensions (2, nrr, nkind_source, ns)
sdata_val = sources_profile.sdata.value;
if ~isempty(sdata_val)
    sz = size(sdata_val);
    while length(sz) < 4, sz(end+1) = 1; end
    need = [2, sz(2), nkind_source, ns];
    if any(sz < need)
        new_sz = max(sz, need);
        tmp = zeros(new_sz);
        idx_cell = cell(1, 4);
        for k = 1:4, idx_cell{k} = 1:sz(k); end
        tmp(idx_cell{:}) = sdata_val;
        sdata_val = tmp;
    end
else
    sdata_val = zeros(2, 0, nkind_source, ns);
end
sources_profile.sdata.value = sdata_val;

% Ensure xdata has full dimensions (2, nrr, nkind_source, ns)
xdata_val = sources_profile.xdata.value;
if ~isempty(xdata_val)
    sz = size(xdata_val);
    while length(sz) < 4, sz(end+1) = 1; end
    need = [2, sz(2), nkind_source, ns];
    if any(sz < need)
        new_sz = max(sz, need);
        tmp = zeros(new_sz);
        idx_cell = cell(1, 4);
        for k = 1:4, idx_cell{k} = 1:sz(k); end
        tmp(idx_cell{:}) = xdata_val;
        xdata_val = tmp;
    end
else
    xdata_val = zeros(2, 0, nkind_source, ns);
end
sources_profile.xdata.value = xdata_val;

% Mark unused (kind_source, species) slices in sdata and xdata with NaN.
% A slice is "unused" if nsdata(:, iks, isp) / nxdata(:, iks, isp) is all zero.
nsdata_val = sources_profile.nsdata.value;
nxdata_val = sources_profile.nxdata.value;
sdata_val  = sources_profile.sdata.value;
xdata_val  = sources_profile.xdata.value;

if size(sdata_val, 2) > 0
    for iks = 1:nkind_source
        for isp = 1:ns
            if all(nsdata_val(:, iks, isp) == 0)
                sdata_val(:, :, iks, isp) = NaN;
            end
        end
    end
    sources_profile.sdata.value = sdata_val;
end

if size(xdata_val, 2) > 0
    for iks = 1:nkind_source
        for isp = 1:ns
            if all(nxdata_val(:, iks, isp) == 0)
                xdata_val(:, :, iks, isp) = NaN;
            end
        end
    end
    sources_profile.xdata.value = xdata_val;
end

sources_profile.grid_version = make_param(grid_version, '');

end


%% PARAMETER STRUCT CONSTRUCTOR

function p = make_param(value, description)
    p.value = value;
    p.description = description;
end


%% DOCUMENTATION PARSER

function descriptions = read_sources_profile_descriptions(SOLPSTOP, grid_version)

    descriptions = struct();

    docfile = sprintf('%s/modules/B2.5/src/documentation/b2cdcn.F', SOLPSTOP);
    fid = fopen(docfile, 'r');
    if fid == -1
        return;
    end

    raw_text = fread(fid, '*char')';
    fclose(fid);
    all_lines = strsplit(raw_text, char(10));

    % Find PROFILE blocks with 'Found in b2.sources.profile'
    block_starts = [];
    block_ends = [];
    for iL = 1:length(all_lines)
        ln = all_lines{iL};
        if ~isempty(regexp(ln, '^\*\s+NAMELIST\s+/PROFILE/', 'once'))
            if iL < length(all_lines) && ...
               ~isempty(strfind(all_lines{iL+1}, 'Found in b2.sources.profile'))
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

function arr = set_nd(arr, indices, val, is_zb)
% Generic N-dimensional array setter for numeric arrays.
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
            arr = zeros(1, sz(1));
        else
            arr = zeros(sz);
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
        tmp = zeros(new_sz);
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
    lin = subs(1);
    stride = 1;
    for k = 2:length(sz)
        stride = stride * sz(k-1);
        lin = lin + (subs(k) - 1) * stride;
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
