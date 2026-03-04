function atomic_physics_rescale = read_atomic_physics_rescale_parameters(simulation)

% read_atomic_physics_rescale_parameters reads the
% b2.atomic_physics_rescale.parameters containing rescaling multipliers
% for atomic physics rates in B2.5
% Output is a struct "atomic_physics_rescale" with all the data fields
% in the b2.atomic_physics_rescale.parameters file.
%
% Each parameter is stored as a substruct with two fields:
%   .value       - the numeric/char/logical value
%   .description - a char containing the documentation from b2cdcn.F

%% PRELIMINARY OPERATIONS

% Load the files and read the version
index = find(contains({simulation.run.name},'b2.atomic_physics_rescale.parameters'));
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

descriptions = read_atomic_rescale_descriptions(simulation.SOLPSTOP, grid_version);

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
        atomic_physics_rescale.version = make_param(first_nonempty, '');
        idx_newline = find(raw == char(10), 1, 'first');
        if ~isempty(idx_newline)
            raw = raw(idx_newline+1:end);
        end
    else
        atomic_physics_rescale.version = make_param('', '');
    end

    % Extract the namelist block
    idx_start = regexpi(raw, '&\s*ATOMIC_PHYSICS_RESCALE');
    if isempty(idx_start)
        nml_str = '';
    else
        in_string = false;
        idx_end = [];
        for ic = idx_start(1)+25 : length(raw)
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
    atomic_physics_rescale.version = make_param('', '');
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

% All arrays are 1D real of size (0:NS-1), default 1.0
atomic_physics_rescale.rescale_sa = make_param(ones(1, ns), desc('rescale_sa'));
atomic_physics_rescale.rescale_ra = make_param(ones(1, ns), desc('rescale_ra'));
atomic_physics_rescale.rescale_qa = make_param(ones(1, ns), desc('rescale_qa'));
atomic_physics_rescale.rescale_cx = make_param(ones(1, ns), desc('rescale_cx'));
atomic_physics_rescale.rescale_rd = make_param(ones(1, ns), desc('rescale_rd'));
atomic_physics_rescale.rescale_br = make_param(ones(1, ns), desc('rescale_br'));

%% BUILD THE VARIABLE CATALOGUE

catalogue = {
    'rescale_sa', '1r', true;
    'rescale_ra', '1r', true;
    'rescale_qa', '1r', true;
    'rescale_cx', '1r', true;
    'rescale_rd', '1r', true;
    'rescale_br', '1r', true;
};

cat_names = catalogue(:,1);
cat_types = catalogue(:,2);
cat_zb    = catalogue(:,3);

%% TOKENIZE AND PROCESS THE NAMELIST

nml_body = regexprep(nml_str, '&\s*ATOMIC_PHYSICS_RESCALE', '', 'ignorecase');
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
    atomic_physics_rescale.grid_version = make_param(grid_version, '');
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
        case '1r'
            val = parse_real_values(vstr);
            if ~isempty(val)
                atomic_physics_rescale.(lhs).value = ...
                    set_1d(atomic_physics_rescale.(lhs).value, indices, val, is_zb);
            end
    end
end

atomic_physics_rescale.grid_version = make_param(grid_version, '');

end


%% PARAMETER STRUCT CONSTRUCTOR

function p = make_param(value, description)
    p.value = value;
    p.description = description;
end


%% DOCUMENTATION PARSER

function descriptions = read_atomic_rescale_descriptions(SOLPSTOP, grid_version)

    descriptions = struct();

    docfile = sprintf('%s/modules/B2.5/src/documentation/b2cdcn.F', SOLPSTOP);
    fid = fopen(docfile, 'r');
    if fid == -1
        return;
    end

    raw_text = fread(fid, '*char')';
    fclose(fid);
    all_lines = strsplit(raw_text, char(10));

    % Find ATOMIC_PHYSICS_RESCALE blocks with
    % 'Found in b2.atomic_physics_rescale.parameters'
    block_starts = [];
    block_ends = [];
    for iL = 1:length(all_lines)
        ln = all_lines{iL};
        if ~isempty(regexp(ln, '^\*\s+NAMELIST\s+/ATOMIC_PHYSICS_RESCALE/', 'once'))
            if iL < length(all_lines) && ...
               ~isempty(strfind(all_lines{iL+1}, 'Found in b2.atomic_physics_rescale.parameters'))
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


%% VALUE PARSERS

function idx = parse_indices(idx_str)
    parts = strsplit(strtrim(idx_str), ',');
    idx = zeros(1, length(parts));
    for i = 1:length(parts)
        idx(i) = str2double(strtrim(parts{i}));
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

function vstr = strip_trailing_comma(vstr)
    vstr = strtrim(vstr);
    if ~isempty(vstr) && vstr(end) == ','
        vstr = strtrim(vstr(1:end-1));
    end
end
