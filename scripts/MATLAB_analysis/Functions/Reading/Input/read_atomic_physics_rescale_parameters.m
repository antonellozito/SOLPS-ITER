function atomic_physics_rescale = read_atomic_physics_rescale_parameters(simulation)

% read_atomic_physics_rescale_parameters reads the
% b2.atomic_physics_rescale.parameters containing rescaling multipliers
% for atomic physics rates in B2.5
% Output is a struct "atomic_physics_rescale" with all the data fields
% in the b2.atomic_physics_rescale.parameters file.
%
% Each parameter is stored as a substruct with four fields:
%   .value       - the numeric/char/logical value
%   .default     - the default entry from b2input.xml
%   .type        - the type entry from b2input.xml
%   .description - the description entry from b2input.xml

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

%% READ DOCUMENTATION FROM b2input.xml

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

% Helper to get XML metadata for a variable
    function d = desc(varname)
        if isfield(descriptions, lower(varname))
            d = descriptions.(lower(varname));
        else
            d = empty_param_metadata();
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


%% DOCUMENTATION PARSER

function descriptions = read_atomic_rescale_descriptions(SOLPSTOP, ~)
    descriptions = read_b2input_descriptions(SOLPSTOP, 'b2.atomic_physics_rescale.parameters');
end
