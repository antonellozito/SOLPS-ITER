function balance_particles(RUN_DIRECTORY, varargin)

%% SELECT THE SIMULATION

RUN = '';

%% SCRIPT DESCRIPTION

% BALANCE_PARTICLES plots the particle balance time traces of the
%    current run (neutral sources and sinks, recycling fluxes, total
%    particle balances per species), extracted from blnn_SPb.trc.
% It can be used both while a simulation is running, to monitor its
%    status, and after the run has stopped.
% The plots are shown grouped in a multi-tab full-window figure.
% Various time-averaging schemes can also be applied to the time traces.
% Can be executed both from the command line, inside one specific run
%    directory, or as an interactive script within the MATLAB GUI,
%    in the last case requiring the manual definition of the
%    run directory of the simulation to be shown

%% USER INPUT

% Select which groups of particle balance plots to show
PLOT_NEUTRALS_SOURCES_SINKS = false;
PLOT_RECYCLING = false;
PLOT_TOTAL_BALANCES = true;

% Select species to plot (cell array of species labels, e.g. {'D','He'})
% By default all species are plotted
PLOT_SPECIES = {};

% Select the number of steps for rolling average of the time traces
% (0 for no rolling average)
ROLLING_AVERAGE_STEPS = 0;

% Select the number of steps for batch average of the time traces
% (0 for no batch average)
BATCH_AVERAGE_STEPS = 0;

% Select the number of steps for phase average of the time traces
% (0 for no phase average)
PHASE_AVERAGE_STEPS = 0;

% Select whether to plot the original data, in case of averaging scheme applied
PLOT_ORIGINAL_DATA = false;

% Specify the plot options
LINEWIDTH = 1.5;
TMIN = nan;
TMAX = nan;
YLIM_STYLE = 'tickaligned';

% Specify the size of the figure(s) (in pixels)
FIGURE_WIDTH = 1400;
FIGURE_HEIGHT = 800;

% Select whether to show name of the simulation in the plot(s)
SHOW_NAME = false;

% Select whether to show the figure(s)
SHOW_FIGURE = true;

% Select whether to print the the figure(s), and the file format
% ('pdf', 'eps', 'ps', 'png', or 'jpg') alongside with the resolution
% (in the format e.g. 'r600' or 'vector' for vector formats)
PRINT_FIGURE = true;
FILE_FORMAT = 'pdf';
FILE_RESOLUTION = 'vector';

%% END OF USER INPUT

%% DEFINE PARAMETER METADATA

FUNC_NAME = 'balance_particles';

DESCRIPTION = {
    'BALANCE_PARTICLES plots the particle balance time traces of the'
    '   current run (neutral sources and sinks, recycling fluxes, total'
    '   particle balances per species), extracted from blnn_SPb.trc.'
    'It can be used both while a simulation is running, to monitor its'
    '   status, and after the run has stopped.'
    'The plots are shown grouped in a multi-tab full-window figure.'
    'Various time-averaging schemes can also be applied to the time traces.'
    'Can be executed both from the command line, inside one specific run'
    '   directory, or as an interactive script within the MATLAB GUI,'
    '   in the last case requiring the manual definition of the'
    '   run directory of the simulation to be shown'
};

PARAMS = struct('name', {}, 'type', {}, 'default', {}, 'required', {}, 'comment', {}, 'validator', {});

PARAMS(end+1) = struct('name', 'PLOT_NEUTRALS_SOURCES_SINKS', 'type', 'logical', ...
    'default', PLOT_NEUTRALS_SOURCES_SINKS, 'required', false, ...
    'comment', 'Plot neutral sources and sinks', ...
    'validator', @(x) islogical(x) || isnumeric(x));

PARAMS(end+1) = struct('name', 'PLOT_RECYCLING', 'type', 'logical', ...
    'default', PLOT_RECYCLING, 'required', false, ...
    'comment', 'Plot recycling fluxes', ...
    'validator', @(x) islogical(x) || isnumeric(x));

PARAMS(end+1) = struct('name', 'PLOT_TOTAL_BALANCES', 'type', 'logical', ...
    'default', PLOT_TOTAL_BALANCES, 'required', false, ...
    'comment', 'Plot total particle balances', ...
    'validator', @(x) islogical(x) || isnumeric(x));

PARAMS(end+1) = struct('name', 'PLOT_SPECIES', 'type', 'cell', ...
    'default', {PLOT_SPECIES}, 'required', false, ...
    'comment', 'Species to plot (cell array of labels, e.g. {''D'',''He''}; empty = all)', ...
    'validator', @iscell);

PARAMS(end+1) = struct('name', 'ROLLING_AVERAGE_STEPS', 'type', 'numeric', ...
    'default', ROLLING_AVERAGE_STEPS, 'required', false, ...
    'comment', 'Number of steps for rolling average', ...
    'validator', @isnumeric);

PARAMS(end+1) = struct('name', 'BATCH_AVERAGE_STEPS', 'type', 'numeric', ...
    'default', BATCH_AVERAGE_STEPS, 'required', false, ...
    'comment', 'Number of steps for batch average', ...
    'validator', @isnumeric);

PARAMS(end+1) = struct('name', 'PHASE_AVERAGE_STEPS', 'type', 'numeric', ...
    'default', PHASE_AVERAGE_STEPS, 'required', false, ...
    'comment', 'Number of steps for phase average', ...
    'validator', @isnumeric);

PARAMS(end+1) = struct('name', 'PLOT_ORIGINAL_DATA', 'type', 'logical', ...
    'default', PLOT_ORIGINAL_DATA, 'required', false, ...
    'comment', 'Plot original data in case of averaging scheme applied', ...
    'validator', @(x) islogical(x) || isnumeric(x));

PARAMS(end+1) = struct('name', 'LINEWIDTH', 'type', 'numeric', ...
    'default', LINEWIDTH, 'required', false, ...
    'comment', 'Line width for plots', ...
    'validator', @isnumeric);

PARAMS(end+1) = struct('name', 'TMIN', 'type', 'numeric', ...
    'default', TMIN, 'required', false, ...
    'comment', 'Minimum time to show', ...
    'validator', @isnumeric);

PARAMS(end+1) = struct('name', 'TMAX', 'type', 'numeric', ...
    'default', TMAX, 'required', false, ...
    'comment', 'Maximum time to show', ...
    'validator', @isnumeric);

PARAMS(end+1) = struct('name', 'YLIM_STYLE', 'type', 'char', ...
    'default', YLIM_STYLE, 'required', false, ...
    'comment', 'Y-axis limit style', ...
    'validator', @ischar);

PARAMS(end+1) = struct('name', 'FIGURE_WIDTH', 'type', 'numeric', ...
    'default', FIGURE_WIDTH, 'required', false, ...
    'comment', 'Figure width in pixels', ...
    'validator', @isnumeric);

PARAMS(end+1) = struct('name', 'FIGURE_HEIGHT', 'type', 'numeric', ...
    'default', FIGURE_HEIGHT, 'required', false, ...
    'comment', 'Figure height in pixels', ...
    'validator', @isnumeric);

PARAMS(end+1) = struct('name', 'SHOW_NAME', 'type', 'logical', ...
    'default', SHOW_NAME, 'required', false, ...
    'comment', 'Show simulation name in plots', ...
    'validator', @(x) islogical(x) || isnumeric(x));

PARAMS(end+1) = struct('name', 'SHOW_FIGURE', 'type', 'logical', ...
    'default', SHOW_FIGURE, 'required', false, ...
    'comment', 'Display the figure(s)', ...
    'validator', @(x) islogical(x) || isnumeric(x));

PARAMS(end+1) = struct('name', 'PRINT_FIGURE', 'type', 'logical', ...
    'default', PRINT_FIGURE, 'required', false, ...
    'comment', 'Save the figure(s) to file', ...
    'validator', @(x) islogical(x) || isnumeric(x));

PARAMS(end+1) = struct('name', 'FILE_FORMAT', 'type', 'char', ...
    'default', FILE_FORMAT, 'required', false, ...
    'comment', 'Output format: pdf, eps, ps, png, jpg', ...
    'validator', @ischar);

PARAMS(end+1) = struct('name', 'FILE_RESOLUTION', 'type', 'char', ...
    'default', FILE_RESOLUTION, 'required', false, ...
    'comment', 'Output resolution: vector, r600, etc.', ...
    'validator', @ischar);

%% PARSE INPUT ARGUMENTS

if nargin == 0
    RUN_DIRECTORY = '';
end

% Parse input arguments as given in the command line
[args_parsed, RUN] = parse_function_args(nargin, RUN_DIRECTORY, varargin, FUNC_NAME, DESCRIPTION, PARAMS, RUN);

% Check if help was requested (RUN will be empty)
if isempty(RUN)
    return;
end

% Build and run inputParser
p = inputParser;
p.KeepUnmatched = false;
for i = 1:numel(PARAMS)
    p.addParameter(PARAMS(i).name, PARAMS(i).default, PARAMS(i).validator);
end
p.parse(args_parsed{:});

% Override local variables with parsed values
[PLOT_NEUTRALS_SOURCES_SINKS, PLOT_RECYCLING, PLOT_TOTAL_BALANCES, ...
 PLOT_SPECIES, ROLLING_AVERAGE_STEPS, BATCH_AVERAGE_STEPS, PHASE_AVERAGE_STEPS, ...
 PLOT_ORIGINAL_DATA, LINEWIDTH, TMIN, TMAX, YLIM_STYLE, ...
 FIGURE_WIDTH, FIGURE_HEIGHT, SHOW_NAME, SHOW_FIGURE, PRINT_FIGURE, ...
 FILE_FORMAT, FILE_RESOLUTION] = ...
    extract_params(p.Results, PARAMS);

%% SANITY CHECK OF USER INPUTS

% Variables which should be logicals
logicals_selection = {'PLOT_NEUTRALS_SOURCES_SINKS'
                      'PLOT_RECYCLING'
                      'PLOT_TOTAL_BALANCES'
                      'PLOT_ORIGINAL_DATA'
                      'SHOW_FIGURE'
                      'SHOW_NAME'
                      'PRINT_FIGURE'};
check_vars(logicals_selection, 'logical');

% Variables which should be numbers
numbers_selection = {'ROLLING_AVERAGE_STEPS'
                     'BATCH_AVERAGE_STEPS'
                     'PHASE_AVERAGE_STEPS'
                     'TMIN'
                     'TMAX'
                     'LINEWIDTH'
                     'FIGURE_WIDTH'
                     'FIGURE_HEIGHT'};
check_vars(numbers_selection, 'number');

% Variables which should be strings
strings_selection = {'YLIM_STYLE'
                     'FILE_FORMAT'
                     'FILE_RESOLUTION'};
check_vars(strings_selection, 'string');

% Only one averaging scheme can be used
averages_selection = {'ROLLING_AVERAGE_STEPS'
                      'BATCH_AVERAGE_STEPS'
                      'PHASE_AVERAGE_STEPS'};
if sum([ROLLING_AVERAGE_STEPS, BATCH_AVERAGE_STEPS, PHASE_AVERAGE_STEPS] ~= 0) > 1
    error('Error: At most one of these variables can be nonzero:\n%s', strjoin(averages_selection, ', '));
end

if ~isnan(TMIN) && ~isnan(TMAX)
    if TMIN >= TMAX
        error('Error: TMIN cannot be larger or equal than TMAX');
    end
end

% Check available styles of Y-limits
if not(strcmp(YLIM_STYLE,'tickaligned') || strcmp(YLIM_STYLE,'tight') || strcmp(YLIM_STYLE,'padded'))
    error('Error: YLIM_STYLE can only be ''tickaligned'', ''tight'' or ''padded''');
end

% Plots should be either shown or printed
if ~SHOW_FIGURE && ~PRINT_FIGURE
    error('Error: SHOW_FIGURE and PRINT_FIGURE cannot be both false');
end

%% LOAD SIMULATION

SIMULATION = load_solps_simulation(RUN);

%% READ DATA

% Extract data from blnn_SPb.trc
PARTICLE_BALANCE = read_blnn(SIMULATION);

% Extract species labels from field names
fnames = fieldnames(PARTICLE_BALANCE);
temp = startsWith(fnames, 'ion_core_');
labels_species = erase(fnames(temp), 'ion_core_');

%% DETERMINE SPECIES TO PLOT

% By default, plot all species
if isempty(PLOT_SPECIES)
    PLOT_SPECIES = labels_species;
end

% Validate requested species
for i = 1:numel(PLOT_SPECIES)
    if ~ismember(PLOT_SPECIES{i}, labels_species)
        error('Error: species ''%s'' not found in the simulation. Available species: %s', ...
            PLOT_SPECIES{i}, strjoin(labels_species, ', '));
    end
end

%% APPLY AVERAGING SCHEMES

PARTICLE_BALANCE_ORIGINAL = PARTICLE_BALANCE;

HAS_AVERAGING = (ROLLING_AVERAGE_STEPS > 0 || BATCH_AVERAGE_STEPS > 0 || PHASE_AVERAGE_STEPS > 0);

% Rolling average
if ROLLING_AVERAGE_STEPS > 0
    time_step = PARTICLE_BALANCE.time.value(2) - PARTICLE_BALANCE.time.value(1);
    fields = fieldnames(PARTICLE_BALANCE);
    for i = 1:numel(fields)
        f = fields{i};
        if ~ismember(f, {'time'})
            PARTICLE_BALANCE.(f).value = rolling_average(PARTICLE_BALANCE.(f).value, ROLLING_AVERAGE_STEPS, 'tracing');
            orig_val = PARTICLE_BALANCE_ORIGINAL.(f).value;
            PARTICLE_BALANCE_ORIGINAL.(f).value = {orig_val};
        end
    end
    fprintf('Rolling average of the particle balance time traces computed over a period of %d time steps (%.1e s)\n', ...
        ROLLING_AVERAGE_STEPS, ROLLING_AVERAGE_STEPS*time_step)
end

% Batch average
if BATCH_AVERAGE_STEPS > 0
    time_step = PARTICLE_BALANCE.time.value(2) - PARTICLE_BALANCE.time.value(1);
    fields = fieldnames(PARTICLE_BALANCE);
    for i = 1:numel(fields)
        f = fields{i};
        if ~ismember(f, {'time'})
            PARTICLE_BALANCE.(f).value = batch_average(PARTICLE_BALANCE.(f).value, BATCH_AVERAGE_STEPS, 'tracing');
            orig_val = PARTICLE_BALANCE_ORIGINAL.(f).value;
            PARTICLE_BALANCE_ORIGINAL.(f).value = {orig_val};
        else
            PARTICLE_BALANCE.time.value = batch_average(PARTICLE_BALANCE.time.value, BATCH_AVERAGE_STEPS, 'time');
        end
    end
    fprintf('Batch average of the particle balance time traces computed over a period of %d time steps (%.1e s)\n', ...
        BATCH_AVERAGE_STEPS, BATCH_AVERAGE_STEPS*time_step)
end

% Phase average
if PHASE_AVERAGE_STEPS > 0
    time_step = PARTICLE_BALANCE.time.value(2) - PARTICLE_BALANCE.time.value(1);
    fields = fieldnames(PARTICLE_BALANCE);
    for i = 1:numel(fields)
        f = fields{i};
        if ~ismember(f, {'time'})
            [PARTICLE_BALANCE.(f).value, PARTICLE_BALANCE_ORIGINAL.(f).value] = phase_average(PARTICLE_BALANCE.(f).value, PHASE_AVERAGE_STEPS, 'tracing');
        else
            [PARTICLE_BALANCE.time.value, PARTICLE_BALANCE_ORIGINAL.time.value] = phase_average(PARTICLE_BALANCE.time.value, PHASE_AVERAGE_STEPS, 'time');
        end
    end
    fprintf('Phase average of the particle balance time traces computed over a period of %d time steps (%.1e s)\n', ...
        PHASE_AVERAGE_STEPS, PHASE_AVERAGE_STEPS*time_step)
end

%% INITIALIZE FIGURES

figs = [];

if SHOW_FIGURE
    SHOW_FIGURE_status = 'on';
else
    SHOW_FIGURE_status = 'off';
end

if HAS_AVERAGING && PLOT_ORIGINAL_DATA
    orig_time = PARTICLE_BALANCE_ORIGINAL.time.value;
else
    orig_time = [];
end

% Load colors
COLORS = load_colors('default',7,'rgb');

% Set Y-limits style
originalYLimitMethod = get(groot, 'defaultAxesYLimitMethod');
set(groot, 'defaultAxesYLimitMethod', YLIM_STYLE);

% Common properties for all plots
tp_common = {'LineWidth', LINEWIDTH, 'TMIN', TMIN, 'TMAX', TMAX, ...
             'ShowName', SHOW_NAME, 'RunName', RUN};

% Extract time vector
time = PARTICLE_BALANCE.time.value;

%% PLOT THE TIME TRACES

for i = 1:numel(PLOT_SPECIES)

    sp = PLOT_SPECIES{i};

    % Check that required fields exist for this species
    if ~isfield(PARTICLE_BALANCE, sprintf('ion_core_%s', sp))
        continue;
    end

    %% NEUTRAL SOURCES AND SINKS

    if PLOT_NEUTRALS_SOURCES_SINKS

        fig = figure('windowstyle','docked','NumberTitle','off','Name', ...
            sprintf('Neutral sources and sinks (%s)', sp),'Visible',SHOW_FIGURE_status); figs = [figs, fig];

        % Neutral gas puff
        subplot('position',[0.1 0.58 0.32 0.34]);
        timeplot(time, ...
            struct('data',PARTICLE_BALANCE.(sprintf('ntr_puff_%s',sp)).value, 'color',COLORS{1}, 'display_name','Neutral gas puff', 'line_style','-'), ...
            'OriginalTime', orig_time, ...
            'OriginalTraces', {get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, PARTICLE_BALANCE_ORIGINAL, sprintf('ntr_puff_%s',sp))}, ...
            'YLabel','[s$^{-1}$]', 'Title',sprintf('Neutral gas puff (%s)',sp), tp_common{:});

        % Core sources
        subplot('position',[0.58 0.58 0.32 0.34]);
        timeplot(time, ...
            [struct('data',PARTICLE_BALANCE.(sprintf('ion_core_%s',sp)).value, 'color',COLORS{1}, 'display_name','Ion core source', 'line_style','-'), ...
             struct('data',PARTICLE_BALANCE.(sprintf('ntr_core_%s',sp)).value, 'color',COLORS{5}, 'display_name','Neutral core source', 'line_style','-')], ...
            'OriginalTime', orig_time, ...
            'OriginalTraces', {get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, PARTICLE_BALANCE_ORIGINAL, sprintf('ion_core_%s',sp)), ...
                               get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, PARTICLE_BALANCE_ORIGINAL, sprintf('ntr_core_%s',sp))}, ...
            'YLabel','[s$^{-1}$]', 'Title',sprintf('Core sources (%s)',sp), tp_common{:});
        yline(0,'linestyle','--','HandleVisibility','off');

        % Pumped neutral fluxes
        subplot('position',[0.1 0.08 0.32 0.34]);
        timeplot(time, ...
            [struct('data',PARTICLE_BALANCE.(sprintf('ntr_targ_pmp_%s',sp)).value, 'color',COLORS{2}, 'display_name','Target pumping', 'line_style','-'), ...
             struct('data',PARTICLE_BALANCE.(sprintf('ntr_wall_pmp_%s',sp)).value, 'color',COLORS{3}, 'display_name','Wall pumping', 'line_style','-')], ...
            'OriginalTime', orig_time, ...
            'OriginalTraces', {get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, PARTICLE_BALANCE_ORIGINAL, sprintf('ntr_targ_pmp_%s',sp)), ...
                               get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, PARTICLE_BALANCE_ORIGINAL, sprintf('ntr_wall_pmp_%s',sp))}, ...
            'YLabel','[s$^{-1}$]', 'Title',sprintf('Pumped neutral fluxes (%s)',sp), tp_common{:});
        yline(0,'linestyle','--','HandleVisibility','off');

        % Sputtered neutral fluxes
        subplot('position',[0.58 0.08 0.32 0.34]);
        timeplot(time, ...
            [struct('data',PARTICLE_BALANCE.(sprintf('ntr_targ_spt_%s',sp)).value, 'color',COLORS{2}, 'display_name','Target sputtering', 'line_style','-'), ...
             struct('data',PARTICLE_BALANCE.(sprintf('ntr_wall_spt_%s',sp)).value, 'color',COLORS{3}, 'display_name','Wall sputtering', 'line_style','-')], ...
            'OriginalTime', orig_time, ...
            'OriginalTraces', {get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, PARTICLE_BALANCE_ORIGINAL, sprintf('ntr_targ_spt_%s',sp)), ...
                               get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, PARTICLE_BALANCE_ORIGINAL, sprintf('ntr_wall_spt_%s',sp))}, ...
            'YLabel','[s$^{-1}$]', 'Title',sprintf('Sputtered neutral fluxes (%s)',sp), tp_common{:});
        yline(0,'linestyle','--','HandleVisibility','off');

        fprintf('Plot of neutral sources and sinks (%s) prepared\n', sp);

    end

    %% RECYCLING

    if PLOT_RECYCLING

        fig = figure('windowstyle','docked','NumberTitle','off','Name', ...
            sprintf('Recycling (%s)', sp),'Visible',SHOW_FIGURE_status); figs = [figs, fig];

        % Recycling fluxes from targets
        subplot('position',[0.07 0.25 0.38 0.50]);
        timeplot(time, ...
            [struct('data',PARTICLE_BALANCE.(sprintf('ion_targ_%s',sp)).value, 'color',COLORS{1}, 'display_name','Ion flux to targets', 'line_style','-'), ...
             struct('data',PARTICLE_BALANCE.(sprintf('ntr_targ_rec_%s',sp)).value, 'color',COLORS{5}, 'display_name','Recycled neutral flux from targets', 'line_style','-')], ...
            'OriginalTime', orig_time, ...
            'OriginalTraces', {get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, PARTICLE_BALANCE_ORIGINAL, sprintf('ion_targ_%s',sp)), ...
                               get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, PARTICLE_BALANCE_ORIGINAL, sprintf('ntr_targ_rec_%s',sp))}, ...
            'YLabel','[s$^{-1}$]', 'Title',sprintf('Recycling fluxes from targets (%s)',sp), tp_common{:});
        yline(0,'linestyle','--','HandleVisibility','off');

        % Recycling fluxes from wall
        subplot('position',[0.55 0.25 0.38 0.50]);
        timeplot(time, ...
            [struct('data',PARTICLE_BALANCE.(sprintf('ion_wall_%s',sp)).value, 'color',COLORS{1}, 'display_name','Ion flux to wall', 'line_style','-'), ...
             struct('data',PARTICLE_BALANCE.(sprintf('ntr_wall_rec_%s',sp)).value, 'color',COLORS{5}, 'display_name','Recycled neutral flux from wall', 'line_style','-')], ...
            'OriginalTime', orig_time, ...
            'OriginalTraces', {get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, PARTICLE_BALANCE_ORIGINAL, sprintf('ion_wall_%s',sp)), ...
                               get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, PARTICLE_BALANCE_ORIGINAL, sprintf('ntr_wall_rec_%s',sp))}, ...
            'YLabel','[s$^{-1}$]', 'Title',sprintf('Recycling fluxes from wall (%s)',sp), tp_common{:});
        yline(0,'linestyle','--','HandleVisibility','off');

        fprintf('Plot of recycling fluxes (%s) prepared\n', sp);

    end

    %% TOTAL BALANCES

    if PLOT_TOTAL_BALANCES

        fig = figure('windowstyle','docked','NumberTitle','off','Name', ...
            sprintf('Total balances (%s)', sp),'Visible',SHOW_FIGURE_status); figs = [figs, fig];

        % Total particle balance
        subplot('position',[0.07 0.25 0.38 0.50]);
        total_gas_source = PARTICLE_BALANCE.(sprintf('ntr_puff_%s',sp)).value ...
                         + PARTICLE_BALANCE.(sprintf('ion_core_%s',sp)).value ...
                         + PARTICLE_BALANCE.(sprintf('ntr_core_%s',sp)).value;
        sputtered_flux   = PARTICLE_BALANCE.(sprintf('ntr_targ_spt_%s',sp)).value ...
                         + PARTICLE_BALANCE.(sprintf('ntr_wall_spt_%s',sp)).value;
        pumped_flux      = PARTICLE_BALANCE.(sprintf('ntr_targ_pmp_%s',sp)).value ...
                         + PARTICLE_BALANCE.(sprintf('ntr_wall_pmp_%s',sp)).value;
        orig_total_gas = combine_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, PARTICLE_BALANCE_ORIGINAL, ...
            {sprintf('ntr_puff_%s',sp), sprintf('ion_core_%s',sp), sprintf('ntr_core_%s',sp)}, [1 1 1]);
        orig_sputtered = combine_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, PARTICLE_BALANCE_ORIGINAL, ...
            {sprintf('ntr_targ_spt_%s',sp), sprintf('ntr_wall_spt_%s',sp)}, [1 1]);
        orig_pumped = combine_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, PARTICLE_BALANCE_ORIGINAL, ...
            {sprintf('ntr_targ_pmp_%s',sp), sprintf('ntr_wall_pmp_%s',sp)}, [1 1]);
        timeplot(time, ...
            [struct('data',total_gas_source, 'color',COLORS{1}, 'display_name','Total gas source (puff+core)', 'line_style','-'), ...
             struct('data',sputtered_flux,   'color',COLORS{2}, 'display_name','Sputtered flux', 'line_style','-'), ...
             struct('data',pumped_flux,      'color',COLORS{3}, 'display_name','Pumped flux', 'line_style','-')], ...
            'OriginalTime', orig_time, ...
            'OriginalTraces', {orig_total_gas, orig_sputtered, orig_pumped}, ...
            'YLabel','[s$^{-1}$]', 'Title',sprintf('Total particle balance (%s)',sp), tp_common{:});
        yline(0,'linestyle','--','HandleVisibility','off');

        % Ion balance
        subplot('position',[0.55 0.25 0.38 0.50]);
        ion_core_val       = PARTICLE_BALANCE.(sprintf('ion_core_%s',sp)).value;
        ion_targ_val       = PARTICLE_BALANCE.(sprintf('ion_targ_%s',sp)).value;
        ion_wall_val       = PARTICLE_BALANCE.(sprintf('ion_wall_%s',sp)).value;
        src_ioniz_val      = PARTICLE_BALANCE.(sprintf('src_ioniz_%s',sp)).value;
        ion_time_var_val   = PARTICLE_BALANCE.(sprintf('ion_dn_divided_dt_%s',sp)).value;
        dynamic_residual   = ion_core_val + ion_targ_val + ion_wall_val + src_ioniz_val - ion_time_var_val;
        orig_residual = combine_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, PARTICLE_BALANCE_ORIGINAL, ...
            {sprintf('ion_core_%s',sp), sprintf('ion_targ_%s',sp), sprintf('ion_wall_%s',sp), sprintf('src_ioniz_%s',sp), sprintf('ion_dn_divided_dt_%s',sp)}, [1 1 1 1 -1]);
        timeplot(time, ...
            [struct('data',ion_core_val,      'color',COLORS{1},     'display_name','Core source',       'line_style','-'), ...
             struct('data',ion_targ_val,      'color',COLORS{2},     'display_name','Target source',     'line_style','-'), ...
             struct('data',ion_wall_val,      'color',COLORS{3},     'display_name','Wall source',       'line_style','-'), ...
             struct('data',src_ioniz_val,     'color',COLORS{4},     'display_name','Ionization source',  'line_style','-'), ...
             struct('data',ion_time_var_val,  'color',[0 0 0],       'display_name','Time variation',     'line_style','-'), ...
             struct('data',dynamic_residual,  'color',[0.6 0.6 0.6], 'display_name','Dynamic residual',   'line_style',':')], ...
            'OriginalTime', orig_time, ...
            'OriginalTraces', {get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, PARTICLE_BALANCE_ORIGINAL, sprintf('ion_core_%s',sp)), ...
                               get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, PARTICLE_BALANCE_ORIGINAL, sprintf('ion_targ_%s',sp)), ...
                               get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, PARTICLE_BALANCE_ORIGINAL, sprintf('ion_wall_%s',sp)), ...
                               get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, PARTICLE_BALANCE_ORIGINAL, sprintf('src_ioniz_%s',sp)), ...
                               get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, PARTICLE_BALANCE_ORIGINAL, sprintf('ion_dn_divided_dt_%s',sp)), ...
                               orig_residual}, ...
            'YLabel','[s$^{-1}$]', 'Title',sprintf('Ion balance (%s)',sp), tp_common{:});
        yline(0,'linestyle','--','HandleVisibility','off');

        fprintf('Plot of total particle balances (%s) prepared\n', sp);

    end

end

%% PRINT THE PLOTS

if PRINT_FIGURE
    print_plot(figs, [FIGURE_WIDTH FIGURE_HEIGHT], 'balance_particles', FILE_FORMAT, FILE_RESOLUTION);
end

set(groot, 'defaultAxesYLimitMethod', originalYLimitMethod);

%% QUIT SESSION AFTER CLOSING FIGURES IF CALLED AS FUNCTION

if nargin ~= 0
    for k = 1:numel(figs)
        waitfor(figs(k));
    end
end

end

%% HELPER FUNCTIONS

function orig_cells = get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, PB_ORIGINAL, field_name)

% GET_ORIG extracts original data cell array for particle balance fields

    if HAS_AVERAGING && PLOT_ORIGINAL_DATA && isfield(PB_ORIGINAL, field_name)
        raw = PB_ORIGINAL.(field_name).value;
        if iscell(raw)
            orig_cells = cell(1, length(raw));
            for j = 1:length(raw)
                orig_cells{j} = raw{j};
            end
        else
            orig_cells = {};
        end
    else
        orig_cells = {};
    end
end

function orig_cells = combine_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, PB_ORIGINAL, field_names, signs)

% COMBINE_ORIG computes original data for derived quantities (sums of fields)
%   field_names - cell array of field name strings
%   signs       - vector of +1/-1 coefficients for each field

    if ~HAS_AVERAGING || ~PLOT_ORIGINAL_DATA
        orig_cells = {};
        return;
    end

    % Get the first field to determine number of phases
    raw1 = PB_ORIGINAL.(field_names{1}).value;
    if ~iscell(raw1)
        orig_cells = {};
        return;
    end

    nphase = length(raw1);
    orig_cells = cell(1, nphase);
    for j = 1:nphase
        combined = signs(1) * raw1{j};
        for m = 2:numel(field_names)
            raw_m = PB_ORIGINAL.(field_names{m}).value;
            combined = combined + signs(m) * raw_m{j};
        end
        orig_cells{j} = combined;
    end
end
