function transport_parameters = read_transport_parameters(simulation)

% read_transport_parameters reads the b2.transport.parameters containing the
% input parameters for the anomalous transport models for B2.5
% Output is a struct "transport_parameters" with all the data fields
% in the b2.transport.parameters file.

% Each parameter is stored as a substruct with four fields:
%   .value       - the numeric/char/logical value
%   .default     - the default entry from b2input.xml
%   .type        - the type entry from b2input.xml
%   .description - the description entry from b2input.xml

%% PRELIMINARY OPERATIONS

% Load the files and read the version
index = find(contains({simulation.run.name},'b2.transport.parameters'));
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

descriptions = read_transport_descriptions(simulation.SOLPSTOP, grid_version);

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
        transport_parameters.version = make_param(first_nonempty, '');
        idx_newline = find(raw == char(10), 1, 'first');
        if ~isempty(idx_newline)
            raw = raw(idx_newline+1:end);
        end
    else
        transport_parameters.version = make_param('', '');
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
    transport_parameters.version = make_param('', '');
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

% Scalar defaults
transport_parameters.flag_dna = make_param(0, desc('flag_dna'));
transport_parameters.flag_dpa = make_param(0, desc('flag_dpa'));
transport_parameters.flag_vla = make_param(0, desc('flag_vla'));
transport_parameters.flag_vsa = make_param(0, desc('flag_vsa'));
transport_parameters.flag_hci = make_param(0, desc('flag_hci'));
transport_parameters.flag_hce = make_param(0, desc('flag_hce'));
transport_parameters.flag_sig = make_param(0, desc('flag_sig'));
transport_parameters.flag_alf = make_param(0, desc('flag_alf'));
transport_parameters.parm_hce = make_param(0.0, desc('parm_hce'));
transport_parameters.parm_sig = make_param(0.0, desc('parm_sig'));
transport_parameters.parm_alf = make_param(0.0, desc('parm_alf'));
transport_parameters.transport_filename    = make_param('b2.transport.parameters', desc('transport_filename'));
transport_parameters.transport_time_mod    = make_param(0.0, desc('transport_time_mod'));
transport_parameters.transport_time_switch = make_param(0.0, desc('transport_time_switch'));
transport_parameters.write_nml_transp      = make_param(true, desc('write_nml_transp'));
transport_parameters.cflme = make_param(0.0, desc('cflme'));
transport_parameters.cflmi = make_param(0.0, desc('cflmi'));
transport_parameters.cflmv = make_param(0.0, desc('cflmv'));
transport_parameters.cflal = make_param(0.0, desc('cflal'));
transport_parameters.cflab = make_param(0.0, desc('cflab'));

% Arrays dimensioned by (0:NS-1) --> MATLAB size ns
transport_parameters.parm_dna = make_param(zeros(1, ns), desc('parm_dna'));
transport_parameters.parm_dpa = make_param(zeros(1, ns), desc('parm_dpa'));
transport_parameters.parm_vla = make_param(zeros(1, ns), desc('parm_vla'));
transport_parameters.parm_vsa = make_param(zeros(1, ns), desc('parm_vsa'));
transport_parameters.parm_hci = make_param(zeros(1, ns), desc('parm_hci'));
transport_parameters.vout_cnv = make_param(zeros(1, ns), desc('vout_cnv'));
transport_parameters.pw0_cnv  = make_param(ones(1, ns), desc('pw0_cnv'));
transport_parameters.pw1_cnv  = make_param(5.0 * ones(1, ns), desc('pw1_cnv'));
transport_parameters.pw2_cnv  = make_param(2.0 * ones(1, ns), desc('pw2_cnv'));

% Structured-grid-only defaults
if strcmp(grid_version, 'Structured')
    transport_parameters.cflme_core   = make_param(0.0, desc('cflme_core'));
    transport_parameters.cflme_sol    = make_param(0.0, desc('cflme_sol'));
    transport_parameters.cflme_tanh_a = make_param(0.0, desc('cflme_tanh_a'));
    transport_parameters.cflme_tanh_b = make_param(0.0, desc('cflme_tanh_b'));
    transport_parameters.cflmi_core   = make_param(0.0, desc('cflmi_core'));
    transport_parameters.cflmi_sol    = make_param(0.0, desc('cflmi_sol'));
    transport_parameters.cflmi_tanh_a = make_param(0.0, desc('cflmi_tanh_a'));
    transport_parameters.cflmi_tanh_b = make_param(0.0, desc('cflmi_tanh_b'));
    transport_parameters.cflmv_core   = make_param(0.0, desc('cflmv_core'));
    transport_parameters.cflmv_sol    = make_param(0.0, desc('cflmv_sol'));
    transport_parameters.cflmv_tanh_a = make_param(0.0, desc('cflmv_tanh_a'));
    transport_parameters.cflmv_tanh_b = make_param(0.0, desc('cflmv_tanh_b'));
end

%% BUILD THE VARIABLE CATALOGUE

catalogue = {
    'flag_dna',              'si', false;
    'flag_dpa',              'si', false;
    'flag_vla',              'si', false;
    'flag_vsa',              'si', false;
    'flag_hci',              'si', false;
    'flag_hce',              'si', false;
    'flag_sig',              'si', false;
    'flag_alf',              'si', false;
    'parm_hce',              'sr', false;
    'parm_sig',              'sr', false;
    'parm_alf',              'sr', false;
    'transport_time_mod',    'sr', false;
    'transport_time_switch', 'sr', false;
    'cflme',                 'sr', false;
    'cflmi',                 'sr', false;
    'cflmv',                 'sr', false;
    'cflal',                 'sr', false;
    'cflab',                 'sr', false;
    'write_nml_transp',      'sl', false;
    'transport_filename',    'ss', false;
    'parm_dna',              '1r', true;
    'parm_dpa',              '1r', true;
    'parm_vla',              '1r', true;
    'parm_vsa',              '1r', true;
    'parm_hci',              '1r', true;
    'vout_cnv',              '1r', true;
    'pw0_cnv',               '1r', true;
    'pw1_cnv',               '1r', true;
    'pw2_cnv',               '1r', true;
};

if strcmp(grid_version, 'Structured')
    catalogue = [catalogue; {
        'cflme_core',    'sr', false;
        'cflme_sol',     'sr', false;
        'cflme_tanh_a',  'sr', false;
        'cflme_tanh_b',  'sr', false;
        'cflmi_core',    'sr', false;
        'cflmi_sol',     'sr', false;
        'cflmi_tanh_a',  'sr', false;
        'cflmi_tanh_b',  'sr', false;
        'cflmv_core',    'sr', false;
        'cflmv_sol',     'sr', false;
        'cflmv_tanh_a',  'sr', false;
        'cflmv_tanh_b',  'sr', false;
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
    transport_parameters.grid_version = make_param(grid_version, '');
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
                transport_parameters.(lhs).value = val(1);
            end
        case 'sr'
            val = parse_real_values(vstr);
            if ~isempty(val)
                transport_parameters.(lhs).value = val(1);
            end
        case 'sl'
            val = parse_logical_values(vstr);
            if ~isempty(val)
                transport_parameters.(lhs).value = val(1);
            end
        case 'ss'
            val = parse_string_value(vstr);
            if ~isempty(val)
                transport_parameters.(lhs).value = val;
            end
        case '1r'
            val = parse_real_values(vstr);
            if ~isempty(val)
                transport_parameters.(lhs).value = ...
                    set_1d(transport_parameters.(lhs).value, indices, val, is_zb);
            end
    end
end

transport_parameters.grid_version = make_param(grid_version, '');

end


%% DOCUMENTATION PARSER

function descriptions = read_transport_descriptions(SOLPSTOP, ~)
    descriptions = read_b2input_descriptions(SOLPSTOP, 'b2.transport.parameters');
end
