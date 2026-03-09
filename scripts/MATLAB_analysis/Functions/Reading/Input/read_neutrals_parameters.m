function neutrals_parameters = read_neutrals_parameters(simulation)

% read_neutrals_parameters reads the b2.neutrals.parameters containing the
% input parameters for the neutral sources / recycling for B2.5
% Output is a struct "neutrals_parameters" with all the data fields
% in the b2.neutrals.parameters file.
%
% Each parameter is stored as a substruct with two fields:
%   .value       - the numeric/char/logical value
%   .description - a char containing the documentation from b2cdcn.F

%% PRELIMINARY OPERATIONS

% Load the files and read the version
index = find(contains({simulation.run.name},'b2.neutrals.parameters'));
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

descriptions = read_neutrals_descriptions(simulation.SOLPSTOP, grid_version);

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
        neutrals_parameters.version = make_param(first_nonempty, '');
        idx_newline = find(raw == char(10), 1, 'first');
        if ~isempty(idx_newline)
            raw = raw(idx_newline+1:end);
        end
    else
        neutrals_parameters.version = make_param('', '');
    end

    % Extract the namelist block
    idx_start = regexpi(raw, '&\s*NEUTRALS');
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
    neutrals_parameters.version = make_param('', '');
    nml_str = '';
end

%% READ NSTRAI

nstrai = read_scalar_int(nml_str, 'nstrai');
if isempty(nstrai), nstrai = 0; end

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
neutrals_parameters.nstrai                    = make_param(nstrai, desc('nstrai'));
neutrals_parameters.eirene_step_cpu           = make_param(0.0, desc('eirene_step_cpu'));
neutrals_parameters.eirene_step_dt            = make_param(0.0, desc('eirene_step_dt'));
neutrals_parameters.eirene_mod                = make_param(1, desc('eirene_mod'));
neutrals_parameters.volrecinc                 = make_param(0.0, desc('volrecinc'));
neutrals_parameters.volrecwt                  = make_param(0.1, desc('volrecwt'));
neutrals_parameters.neutrals_filename         = make_param('b2.neutrals.parameters', desc('neutrals_filename'));
neutrals_parameters.neutrals_time_mod         = make_param(0.0, desc('neutrals_time_mod'));
neutrals_parameters.neutrals_time_switch      = make_param(0.0, desc('neutrals_time_switch'));
neutrals_parameters.l_neutrad                 = make_param(0, desc('l_neutrad'));
neutrals_parameters.l_neutflux                = make_param(0, desc('l_neutflux'));
neutrals_parameters.dbg_eir_mc                = make_param(0, desc('dbg_eir_mc'));
neutrals_parameters.neut_scl_lim              = make_param(2.0, desc('neut_scl_lim'));
neutrals_parameters.maxpoin                   = make_param(2000, desc('maxpoin'));
neutrals_parameters.chemical_erosion_redep_fac = make_param(1.0, desc('chemical_erosion_redep_fac'));
neutrals_parameters.chemical_erosion_be_fac   = make_param(false, desc('chemical_erosion_be_fac'));
neutrals_parameters.chemical_erosion_be_fac_a = make_param(0.2, desc('chemical_erosion_be_fac_a'));
neutrals_parameters.chemical_erosion_be_fac_b = make_param(0.05, desc('chemical_erosion_be_fac_b'));
neutrals_parameters.chemical_erosion_be_fac_c = make_param(0.9, desc('chemical_erosion_be_fac_c'));
neutrals_parameters.n_spcsrf                  = make_param(0, desc('n_spcsrf'));
neutrals_parameters.write_nml_neut            = make_param(true, desc('write_nml_neut'));
neutrals_parameters.fchar_chemical            = make_param(0.0, desc('fchar_chemical'));
neutrals_parameters.igass_chemical            = make_param(0, desc('igass_chemical'));
neutrals_parameters.itsput_chemical           = make_param(0, desc('itsput_chemical'));
neutrals_parameters.issput_chemical           = make_param(0, desc('issput_chemical'));

% rf_neut (fixed size 4)
neutrals_parameters.rf_neut = make_param(ones(1, 4), desc('rf_neut'));

% debug_flags (fixed size 100)
neutrals_parameters.debug_flags = make_param(zeros(1, 100), desc('debug_flags'));

% Arrays dimensioned by NSTRAI
neutrals_parameters.rcpos        = make_param(-2 * ones(1, nstrai), desc('rcpos'));
neutrals_parameters.rcstart      = make_param(-2 * ones(1, nstrai), desc('rcstart'));
neutrals_parameters.rcend        = make_param(-2 * ones(1, nstrai), desc('rcend'));
neutrals_parameters.rc_list_size = make_param(zeros(1, nstrai), desc('rc_list_size'));
neutrals_parameters.rc_list_x    = make_param([], desc('rc_list_x'));
neutrals_parameters.rc_list_y    = make_param([], desc('rc_list_y'));
neutrals_parameters.crcstra      = make_param(repmat(' ', 1, nstrai), desc('crcstra'));
neutrals_parameters.chemsp       = make_param(false(1, nstrai), desc('chemsp'));
neutrals_parameters.time_dep_puff      = make_param(false(1, nstrai), desc('time_dep_puff'));
neutrals_parameters.time_dep_puff_func = make_param(false(1, nstrai), desc('time_dep_puff_func'));
neutrals_parameters.time_dep_puff_case = make_param(-1 * ones(1, nstrai), desc('time_dep_puff_case'));
neutrals_parameters.ngpdata      = make_param(zeros(1, nstrai), desc('ngpdata'));
neutrals_parameters.recyceir     = make_param(ones(1, nstrai), desc('recyceir'));
neutrals_parameters.volrecstart  = make_param(1.0e21 * ones(1, nstrai), desc('volrecstart'));
neutrals_parameters.species_start = make_param(zeros(1, nstrai), desc('species_start'));
neutrals_parameters.species_end  = make_param((ns-1) * ones(1, nstrai), desc('species_end'));
neutrals_parameters.ksns         = make_param(zeros(1, nstrai), desc('ksns'));

% Arrays dimensioned by (NSTRAI, NTRACK=4)
neutrals_parameters.targsp = make_param(-1 * ones(nstrai, 4), desc('targsp'));

% Arrays dimensioned by (NSTRAI, 2)
neutrals_parameters.userfluxparm = make_param(zeros(nstrai, 2), desc('userfluxparm'));

% Arrays dimensioned by (0:NS-1, NSTRAI)
neutrals_parameters.recyc   = make_param(zeros(ns, nstrai), desc('recyc'));
neutrals_parameters.erecyc  = make_param(zeros(ns, nstrai), desc('erecyc'));
neutrals_parameters.mrecyc  = make_param(zeros(ns, nstrai), desc('mrecyc'));
neutrals_parameters.rcion   = make_param(zeros(ns, nstrai), desc('rcion'));
neutrals_parameters.phys_sput = make_param(zeros(ns, nstrai), desc('phys_sput'));
neutrals_parameters.chem_sput = make_param(zeros(ns, nstrai), desc('chem_sput'));

% Arrays dimensioned by (0:NS-1)
neutrals_parameters.b2eatcr     = make_param(zeros(1, ns), desc('b2eatcr'));
neutrals_parameters.b2espcr     = make_param(zeros(1, ns), desc('b2espcr'));
neutrals_parameters.track_index = make_param(zeros(1, ns), desc('track_index'));

% Arrays of unknown dimension (will be grown as needed)
neutrals_parameters.eb2atcr = make_param([], desc('eb2atcr'));
neutrals_parameters.eb2spcr = make_param([], desc('eb2spcr'));
neutrals_parameters.latmscl = make_param([], desc('latmscl'));
neutrals_parameters.lmolscl = make_param([], desc('lmolscl'));
neutrals_parameters.lionscl = make_param([], desc('lionscl'));
neutrals_parameters.lcns    = make_param([], desc('lcns'));
neutrals_parameters.ltns    = make_param([], desc('ltns'));
neutrals_parameters.lsns    = make_param([], desc('lsns'));
neutrals_parameters.chemical_sputter_yield = make_param([], desc('chemical_sputter_yield'));
neutrals_parameters.track_chem_sput = make_param([], desc('track_chem_sput'));

% 2D arrays with variable dimension
neutrals_parameters.lstrascl = make_param([], desc('lstrascl'));
neutrals_parameters.mlcmp    = make_param([], desc('mlcmp'));
neutrals_parameters.micmp    = make_param([], desc('micmp'));
neutrals_parameters.gpfc     = make_param([], desc('gpfc'));

% 3D: time_dep_puff_param (10, NSTRAI)
neutrals_parameters.time_dep_puff_param = make_param(zeros(10, nstrai), desc('time_dep_puff_param'));

% 3D: gpdata (100, 2, NSTRAI)
neutrals_parameters.gpdata = make_param(zeros(100, 2, nstrai), desc('gpdata'));

% Structured-only arrays
if strcmp(grid_version, 'Structured')
    neutrals_parameters.rc_list_char = make_param([], desc('rc_list_char'));
end

% Unstructured-only arrays
if strcmp(grid_version, 'Unstructured')
    neutrals_parameters.b2recyc           = make_param(zeros(ns, nstrai), desc('b2recyc'));
    neutrals_parameters.recycm            = make_param(zeros(ns, nstrai), desc('recycm'));
    neutrals_parameters.rc_list_char      = make_param([], desc('rc_list_char'));
    neutrals_parameters.b2species_start   = make_param(-100 * ones(1, nstrai), desc('b2species_start'));
    neutrals_parameters.b2species_end     = make_param(-100 * ones(1, nstrai), desc('b2species_end'));
    neutrals_parameters.surf_mat          = make_param(repmat({'C '}, 1, nstrai), desc('surf_mat'));
    neutrals_parameters.hyb_type          = make_param(repmat({'M'}, 1, nstrai), desc('hyb_type'));
    neutrals_parameters.accel_ion         = make_param(ones(1, nstrai), desc('accel_ion'));
    neutrals_parameters.maxw              = make_param(ones(1, nstrai), desc('maxw'));
    neutrals_parameters.maxw_eff          = make_param(ones(1, nstrai), desc('maxw_eff'));
    neutrals_parameters.mol               = make_param(zeros(1, nstrai), desc('mol'));
    neutrals_parameters.e_fc              = make_param(3.0, desc('e_fc'));
    neutrals_parameters.strasclfl         = make_param(ones(1, nstrai), desc('strasclfl'));
    neutrals_parameters.rcfe              = make_param(0.5 * ones(1, nstrai), desc('rcfe'));
    neutrals_parameters.rcfi              = make_param(3.0 * ones(1, nstrai), desc('rcfi'));
    neutrals_parameters.nrelax_sni        = make_param(ones(1, nstrai), desc('nrelax_sni'));
    neutrals_parameters.nrelax_smo        = make_param(ones(1, nstrai), desc('nrelax_smo'));
    neutrals_parameters.nrelax_see        = make_param(ones(1, nstrai), desc('nrelax_see'));
    neutrals_parameters.nrelax_sei        = make_param(ones(1, nstrai), desc('nrelax_sei'));
end

% Arrays read if n_spcsrf > 0
neutrals_parameters.l_spcsrf  = make_param([], desc('l_spcsrf'));
neutrals_parameters.sps_id    = make_param({}, desc('sps_id'));
neutrals_parameters.i_spcsrf  = make_param([], desc('i_spcsrf'));
neutrals_parameters.j_spcsrf  = make_param([], desc('j_spcsrf'));
neutrals_parameters.sps_absr  = make_param([], desc('sps_absr'));
neutrals_parameters.sps_trno  = make_param([], desc('sps_trno'));
neutrals_parameters.sps_trni  = make_param([], desc('sps_trni'));
neutrals_parameters.sps_mtri  = make_param([], desc('sps_mtri'));
neutrals_parameters.sps_mtrl  = make_param({}, desc('sps_mtrl'));
neutrals_parameters.sps_tmpr  = make_param([], desc('sps_tmpr'));
neutrals_parameters.sps_spph  = make_param([], desc('sps_spph'));
neutrals_parameters.sps_spch  = make_param([], desc('sps_spch'));
neutrals_parameters.sps_sgrp  = make_param([], desc('sps_sgrp'));

% Arrays dimensioned by (NSTRAI, 2) for msns
neutrals_parameters.msns = make_param(zeros(2, nstrai), desc('msns'));

%% BUILD THE VARIABLE CATALOGUE

catalogue = {
    'nstrai',                    'si', false;
    'eirene_mod',                'si', false;
    'l_neutrad',                 'si', false;
    'l_neutflux',                'si', false;
    'dbg_eir_mc',                'si', false;
    'maxpoin',                   'si', false;
    'n_spcsrf',                  'si', false;
    'igass_chemical',            'si', false;
    'itsput_chemical',           'si', false;
    'issput_chemical',           'si', false;
    'eirene_step_cpu',           'sr', false;
    'eirene_step_dt',            'sr', false;
    'volrecinc',                 'sr', false;
    'volrecwt',                  'sr', false;
    'neutrals_time_mod',         'sr', false;
    'neutrals_time_switch',      'sr', false;
    'neut_scl_lim',              'sr', false;
    'chemical_erosion_redep_fac','sr', false;
    'chemical_erosion_be_fac_a', 'sr', false;
    'chemical_erosion_be_fac_b', 'sr', false;
    'chemical_erosion_be_fac_c', 'sr', false;
    'fchar_chemical',            'sr', false;
    'write_nml_neut',            'sl', false;
    'chemical_erosion_be_fac',   'sl', false;
    'neutrals_filename',         'ss', false;
    'crcstra',                   '1c', false;
    'rcpos',                     '1i', false;
    'rcstart',                   '1i', false;
    'rcend',                     '1i', false;
    'rc_list_size',              '1i', false;
    'ngpdata',                   '1i', false;
    'species_start',             '1i', false;
    'species_end',               '1i', false;
    'ksns',                      '1i', false;
    'time_dep_puff_case',        '1i', false;
    'rf_neut',                   '1r', false;
    'recyceir',                  '1r', false;
    'volrecstart',               '1r', false;
    'debug_flags',               '1i', false;
    'chemsp',                    '1l', false;
    'time_dep_puff',             '1l', false;
    'time_dep_puff_func',        '1l', false;
    'b2eatcr',                   '1i', true;
    'b2espcr',                   '1i', true;
    'track_index',               '1i', true;
    'eb2atcr',                   '1i', false;
    'eb2spcr',                   '1i', false;
    'latmscl',                   '1i', false;
    'lmolscl',                   '1i', false;
    'lionscl',                   '1i', false;
    'lcns',                      '1i', false;
    'ltns',                      '1i', false;
    'lsns',                      '1i', false;
    'chemical_sputter_yield',    '1r', false;
    'track_chem_sput',           '1l', false;
    'l_spcsrf',                  '1i', false;
    'i_spcsrf',                  '1i', false;
    'j_spcsrf',                  '1i', false;
    'sps_absr',                  '1r', false;
    'sps_trno',                  '1r', false;
    'sps_trni',                  '1r', false;
    'sps_mtri',                  '1r', false;
    'sps_tmpr',                  '1r', false;
    'sps_spph',                  '1r', false;
    'sps_spch',                  '1r', false;
    'sps_sgrp',                  '1i', false;
    'sps_id',                    '1s', false;
    'sps_mtrl',                  '1s', false;
    'rc_list_x',                 '2i', false;
    'rc_list_y',                 '2i', false;
    'targsp',                    '2i', false;
    'userfluxparm',              '2r', false;
    'msns',                      '2i', false;
    'recyc',                     '2r', true;
    'erecyc',                    '2r', true;
    'mrecyc',                    '2r', true;
    'rcion',                     '2r', true;
    'phys_sput',                 '2r', true;
    'chem_sput',                 '2r', true;
    'lstrascl',                  '2i', false;
    'mlcmp',                     '2i', false;
    'micmp',                     '2i', false;
    'gpfc',                      '2r', false;
    'time_dep_puff_param',       '2r', false;
    'gpdata',                    '3r', false;
};

if strcmp(grid_version, 'Unstructured')
    catalogue = [catalogue; {
        'b2recyc',           '2r', true;
        'recycm',            '2r', true;
        'rc_list_char',      '2c', false;
        'b2species_start',   '1i', false;
        'b2species_end',     '1i', false;
        'surf_mat',          '1s', false;
        'hyb_type',          '1s', false;
        'accel_ion',         '1i', false;
        'maxw',              '1i', false;
        'maxw_eff',          '1i', false;
        'mol',               '1i', false;
        'e_fc',              'sr', false;
        'strasclfl',         '1r', false;
        'rcfe',              '1r', false;
        'rcfi',              '1r', false;
        'nrelax_sni',        '1r', false;
        'nrelax_smo',        '1r', false;
        'nrelax_see',        '1r', false;
        'nrelax_sei',        '1r', false;
    }];
end

if strcmp(grid_version, 'Structured')
    catalogue = [catalogue; {
        'rc_list_char',      '2c', false;
    }];
end

cat_names = catalogue(:,1);
cat_types = catalogue(:,2);
cat_zb    = catalogue(:,3);

%% TOKENIZE AND PROCESS THE NAMELIST

nml_body = regexprep(nml_str, '&\s*NEUTRALS', '', 'ignorecase');
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
    neutrals_parameters.grid_version = make_param(grid_version, '');
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
                neutrals_parameters.(lhs).value = val(1);
            end
        case 'sr'
            val = parse_real_values(vstr);
            if ~isempty(val)
                neutrals_parameters.(lhs).value = val(1);
            end
        case 'sl'
            val = parse_logical_values(vstr);
            if ~isempty(val)
                neutrals_parameters.(lhs).value = val(1);
            end
        case 'ss'
            val = parse_string_value(vstr);
            if ~isempty(val)
                neutrals_parameters.(lhs).value = val;
            end
        case '1i'
            val = parse_int_values(vstr);
            if ~isempty(val)
                neutrals_parameters.(lhs).value = ...
                    set_1d(neutrals_parameters.(lhs).value, indices, val, is_zb);
            end
        case '1r'
            val = parse_real_values(vstr);
            if ~isempty(val)
                neutrals_parameters.(lhs).value = ...
                    set_1d(neutrals_parameters.(lhs).value, indices, val, is_zb);
            end
        case '1c'
            val = parse_char_values(vstr);
            if ~isempty(val)
                neutrals_parameters.(lhs).value = ...
                    set_1d_char(neutrals_parameters.(lhs).value, indices, val);
            end
        case '1l'
            val = parse_logical_values(vstr);
            if ~isempty(val)
                neutrals_parameters.(lhs).value = ...
                    set_1d_logical(neutrals_parameters.(lhs).value, indices, val, is_zb);
            end
        case '1s'
            val = parse_string_list(vstr);
            if ~isempty(val)
                neutrals_parameters.(lhs).value = ...
                    set_1d_str(neutrals_parameters.(lhs).value, indices, val, is_zb);
            end
        case '2i'
            val = parse_int_values(vstr);
            if ~isempty(val)
                neutrals_parameters.(lhs).value = ...
                    set_2d(neutrals_parameters.(lhs).value, indices, val, is_zb);
            end
        case '2r'
            val = parse_real_values(vstr);
            if ~isempty(val)
                neutrals_parameters.(lhs).value = ...
                    set_2d(neutrals_parameters.(lhs).value, indices, val, is_zb);
            end
        case '2c'
            val = parse_char_values(vstr);
            if ~isempty(val)
                neutrals_parameters.(lhs).value = ...
                    set_2d_char(neutrals_parameters.(lhs).value, indices, val);
            end
        case '2s'
            val = parse_string_list(vstr);
            if ~isempty(val)
                neutrals_parameters.(lhs).value = ...
                    set_2d_str(neutrals_parameters.(lhs).value, indices, val, is_zb);
            end
        case '3r'
            val = parse_real_values(vstr);
            if ~isempty(val)
                neutrals_parameters.(lhs).value = ...
                    set_3d(neutrals_parameters.(lhs).value, indices, val, is_zb);
            end
    end
end

neutrals_parameters.grid_version = make_param(grid_version, '');

end


%%  PARAMETER STRUCT CONSTRUCTOR

function p = make_param(value, description)
% Create a parameter substruct with .value and .description fields.
    p.value = value;
    p.description = description;
end


%% DOCUMENTATION PARSER

function descriptions = read_neutrals_descriptions(SOLPSTOP, grid_version)

% Read the NEUTRALS namelist documentation block from b2cdcn.F.
% Returns a struct where each field is a lowercase variable name and the
% value is a char containing the multi-line description (lines joined by \n).
%
% The file is located at:
%   <SOLPSTOP>/modules/B2.5/src/documentation/b2cdcn.F
%
% The relevant block starts at a line matching:
%   * NAMELIST /NEUTRALS/
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

    % Find the NEUTRALS block
    block_starts = [];
    block_ends = [];
    for iL = 1:length(all_lines)
        ln = all_lines{iL};
        if ~isempty(regexp(ln, '^\*\s+NAMELIST\s+/NEUTRALS/', 'once'))
            block_starts(end+1) = iL;
        elseif ~isempty(block_starts) && isempty(block_ends) || ...
               (~isempty(block_starts) && length(block_ends) < length(block_starts))
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
            new_total = lin;
            new_c = ceil(new_total / sz(1));
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

function arr = set_2d_char(arr, indices, val)
    if isempty(arr)
        arr = ' ';
    end
    sz = size(arr);
    i1 = 1; i2 = 1;
    if ~isempty(indices)
        i1 = max(1, indices(1));
        if length(indices) >= 2, i2 = indices(2); end
    end
    need_r = max(sz(1), i1 + length(val) - 1);
    need_c = max(sz(2), i2);
    if need_r > sz(1) || need_c > sz(2)
        tmp = repmat(' ', need_r, need_c);
        tmp(1:sz(1), 1:sz(2)) = arr;
        arr = tmp;
        sz = size(arr);
    end
    lin0 = (i2 - 1) * sz(1) + i1;
    for iv = 1:length(val)
        lin = lin0 + iv - 1;
        c = ceil(lin / sz(1));
        r = lin - (c-1) * sz(1);
        if r <= sz(1) && c <= sz(2)
            arr(r, c) = val(iv);
        end
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
