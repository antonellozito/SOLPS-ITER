function balance_energy(RUN_DIRECTORY, varargin)

%% SELECT THE SIMULATION

RUN = '';

%% SCRIPT DESCRIPTION

% BALANCE_ENERGY plots the energy balance time traces of the
%    current run (total energy balance, decomposition of energy flows
%    into core input, radiation, target loads and wall loads),
%    extracted from blne.trc.
% It can be used both while a simulation is running, to monitor its
%    status, and after the run has stopped.
% The plots are shown grouped in a multi-tab full-window figure.
% Various time-averaging schemes can also be applied to the time traces.
% Can be executed both from the command line, inside one specific run
%    directory, or as an interactive script within the MATLAB GUI,
%    in the last case requiring the manual definition of the
%    run directory of the simulation to be shown

%% USER INPUT

% Select which groups of energy balance plots to show
PLOT_TOTAL_ENERGY_BALANCE = true;
PLOT_DECOMPOSITION_ENERGY_FLOWS = true;

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

FUNC_NAME = 'balance_energy';

DESCRIPTION = {
    'BALANCE_ENERGY plots the energy balance time traces of the'
    '   current run (total energy balance, decomposition of energy flows'
    '   into core input, radiation, target loads and wall loads),'
    '   extracted from blne.trc.'
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

PARAMS(end+1) = struct('name', 'PLOT_TOTAL_ENERGY_BALANCE', 'type', 'logical', ...
    'default', PLOT_TOTAL_ENERGY_BALANCE, 'required', false, ...
    'comment', 'Plot total energy balance', ...
    'validator', @(x) islogical(x) || isnumeric(x));

PARAMS(end+1) = struct('name', 'PLOT_DECOMPOSITION_ENERGY_FLOWS', 'type', 'logical', ...
    'default', PLOT_DECOMPOSITION_ENERGY_FLOWS, 'required', false, ...
    'comment', 'Plot decomposition of energy flows', ...
    'validator', @(x) islogical(x) || isnumeric(x));

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
[PLOT_TOTAL_ENERGY_BALANCE, PLOT_DECOMPOSITION_ENERGY_FLOWS, ...
 ROLLING_AVERAGE_STEPS, BATCH_AVERAGE_STEPS, PHASE_AVERAGE_STEPS, ...
 PLOT_ORIGINAL_DATA, LINEWIDTH, TMIN, TMAX, YLIM_STYLE, ...
 FIGURE_WIDTH, FIGURE_HEIGHT, SHOW_NAME, SHOW_FIGURE, PRINT_FIGURE, ...
 FILE_FORMAT, FILE_RESOLUTION] = ...
    extract_params(p.Results, PARAMS);

%% SANITY CHECK OF USER INPUTS

% Variables which should be logicals
logicals_selection = {'PLOT_TOTAL_ENERGY_BALANCE'
                      'PLOT_DECOMPOSITION_ENERGY_FLOWS'
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

% Extract data from blne.trc
ENERGY_BALANCE = read_blne(SIMULATION);

% Extract impurity species labels from field names
fnames = fieldnames(ENERGY_BALANCE);
temp = startsWith(fnames, 'imp_rad_');
labels_species = erase(fnames(temp), 'imp_rad_');

%% DETERMINE TARGET CONFIGURATION BASED ON GEOMETRY

geometry = SIMULATION.geometry_type;
IS_LIMITER = strcmp(geometry, 'Limiter');

if IS_LIMITER
    % One target (aggregated): use tot_targ, plsm_trg, ntrl_trg
    targets = struct( ...
        'suffix', {'targ'}, ...
        'label',  {'target'});

elseif contains(geometry, 'Lower single null')
    % Two targets: inner (il) and outer (ol)
    targets = struct( ...
        'suffix', {'il', 'ol'}, ...
        'label',  {'inner target', 'outer target'});

elseif contains(geometry, 'Upper single null')
    % Two targets: inner (ol) and outer (il) — suffixes reversed
    targets = struct( ...
        'suffix', {'ol', 'il'}, ...
        'label',  {'inner target', 'outer target'});

elseif strcmp(geometry, 'Connected double null') || strcmp(geometry, 'Disconnected double null')
    % Four targets
    targets = struct( ...
        'suffix', {'il',                  'ol',                  'iu',               'ou'}, ...
        'label',  {'inner target bottom', 'outer target bottom', 'inner target top', 'outer target top'});

elseif strcmp(geometry, 'Lower LFS snowflake') || strcmp(geometry, 'Upper LFS snowflake')
    % Four targets
    targets = struct( ...
        'suffix', {'il',           'ol',                   'iu',                    'ou'}, ...
        'label',  {'inner target', 'outer target primary', 'outer target far-SOL',  'outer target secondary'});

else
    warning('Unknown geometry type ''%s''. Defaulting to two-target (il/ol) configuration.', geometry);
    targets = struct( ...
        'suffix', {'il', 'ol'}, ...
        'label',  {'inner target', 'outer target'});
end

n_targets = numel(targets);

%% APPLY AVERAGING SCHEMES

ENERGY_BALANCE_ORIGINAL = ENERGY_BALANCE;

HAS_AVERAGING = (ROLLING_AVERAGE_STEPS > 0 || BATCH_AVERAGE_STEPS > 0 || PHASE_AVERAGE_STEPS > 0);

% Rolling average
if ROLLING_AVERAGE_STEPS > 0
    time_step = ENERGY_BALANCE.time.value(2) - ENERGY_BALANCE.time.value(1);
    fields = fieldnames(ENERGY_BALANCE);
    for i = 1:numel(fields)
        f = fields{i};
        if ~ismember(f, {'time'})
            ENERGY_BALANCE.(f).value = rolling_average(ENERGY_BALANCE.(f).value, ROLLING_AVERAGE_STEPS, 'tracing');
            orig_val = ENERGY_BALANCE_ORIGINAL.(f).value;
            ENERGY_BALANCE_ORIGINAL.(f).value = {orig_val};
        end
    end
    fprintf('Rolling average of the energy balance time traces computed over a period of %d time steps (%.1e s)\n', ...
        ROLLING_AVERAGE_STEPS, ROLLING_AVERAGE_STEPS*time_step)
end

% Batch average
if BATCH_AVERAGE_STEPS > 0
    time_step = ENERGY_BALANCE.time.value(2) - ENERGY_BALANCE.time.value(1);
    fields = fieldnames(ENERGY_BALANCE);
    for i = 1:numel(fields)
        f = fields{i};
        if ~ismember(f, {'time'})
            ENERGY_BALANCE.(f).value = batch_average(ENERGY_BALANCE.(f).value, BATCH_AVERAGE_STEPS, 'tracing');
            orig_val = ENERGY_BALANCE_ORIGINAL.(f).value;
            ENERGY_BALANCE_ORIGINAL.(f).value = {orig_val};
        else
            ENERGY_BALANCE.time.value = batch_average(ENERGY_BALANCE.time.value, BATCH_AVERAGE_STEPS, 'time');
        end
    end
    fprintf('Batch average of the energy balance time traces computed over a period of %d time steps (%.1e s)\n', ...
        BATCH_AVERAGE_STEPS, BATCH_AVERAGE_STEPS*time_step)
end

% Phase average
if PHASE_AVERAGE_STEPS > 0
    time_step = ENERGY_BALANCE.time.value(2) - ENERGY_BALANCE.time.value(1);
    fields = fieldnames(ENERGY_BALANCE);
    for i = 1:numel(fields)
        f = fields{i};
        if ~ismember(f, {'time'})
            [ENERGY_BALANCE.(f).value, ENERGY_BALANCE_ORIGINAL.(f).value] = phase_average(ENERGY_BALANCE.(f).value, PHASE_AVERAGE_STEPS, 'tracing');
        else
            [ENERGY_BALANCE.time.value, ENERGY_BALANCE_ORIGINAL.time.value] = phase_average(ENERGY_BALANCE.time.value, PHASE_AVERAGE_STEPS, 'time');
        end
    end
    fprintf('Phase average of the energy balance time traces computed over a period of %d time steps (%.1e s)\n', ...
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
    orig_time = ENERGY_BALANCE_ORIGINAL.time.value;
else
    orig_time = [];
end

% Load colors
COLORS = load_colors('default',7,'rgb');
COLORS_DARK = load_colors('default_dark',7,'rgb');
COLORS_LIGHT = load_colors('default_light',7,'rgb');

% Set Y-limits style
originalYLimitMethod = get(groot, 'defaultAxesYLimitMethod');
set(groot, 'defaultAxesYLimitMethod', YLIM_STYLE);

% Common properties for all plots
tp_common = {'LineWidth', LINEWIDTH, 'TMIN', TMIN, 'TMAX', TMAX, ...
             'ShowName', SHOW_NAME, 'RunName', RUN};

% Extract time vector
time = ENERGY_BALANCE.time.value;

%% PLOT THE TIME TRACES — TOTAL ENERGY BALANCE

if PLOT_TOTAL_ENERGY_BALANCE

    fig = figure('windowstyle','docked','NumberTitle','off','Name', ...
        'Total energy balance','Visible',SHOW_FIGURE_status); figs = [figs, fig];

    % Build target traces for the total energy balance plot
    target_traces = [];
    target_orig = {};
    target_colors = {COLORS{2}, COLORS_DARK{2}, COLORS_LIGHT{2}, COLORS{6}};
    if IS_LIMITER
        % Limiter: single aggregated target and wall fields
        target_traces = struct('data', ENERGY_BALANCE.tot_targ.value, ...
                               'color', target_colors{1}, ...
                               'display_name', 'Energy to target', ...
                               'line_style', '-');
        target_orig = {get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, ENERGY_BALANCE_ORIGINAL, 'tot_targ')};
        wall_trace = struct('data', ENERGY_BALANCE.tot_wall.value, 'color', COLORS{3}, ...
                            'display_name', 'Energy to main wall', 'line_style', '-');
        wall_orig = {get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, ENERGY_BALANCE_ORIGINAL, 'tot_wall')};
    else
        % Divertor: per-surface target fields and wall field
        for t = 1:n_targets
            sf = targets(t).suffix;
            lb = targets(t).label;
            target_traces = [target_traces, ...
                struct('data', ENERGY_BALANCE.(sprintf('pwr_totl_%s',sf)).value, ...
                       'color', target_colors{t}, ...
                       'display_name', sprintf('Energy to %s', lb), ...
                       'line_style', '-')];
            target_orig = [target_orig, ...
                {get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, ENERGY_BALANCE_ORIGINAL, sprintf('pwr_totl_%s',sf))}];
        end
        wall_trace = struct('data', ENERGY_BALANCE.pwr_totl_wl.value, 'color', COLORS{3}, ...
                            'display_name', 'Energy to main wall', 'line_style', '-');
        wall_orig = {get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, ENERGY_BALANCE_ORIGINAL, 'pwr_totl_wl')};
    end

    subplot('position',[0.25 0.18 0.5 0.65]);
    timeplot(time, ...
        [struct('data',ENERGY_BALANCE.pwr_totl.value,    'color',[0 0 0],    'display_name','Dynamic energy balance',          'line_style','--'), ...
         struct('data',ENERGY_BALANCE.tot_core.value,    'color',COLORS{1},  'display_name','Input energy from core boundary', 'line_style','-'), ...
         target_traces, ...
         wall_trace, ...
         struct('data',ENERGY_BALANCE.tot_rad.value,     'color',COLORS{4},  'display_name','Radiated energy',                 'line_style','-')], ...
        'OriginalTime', orig_time, ...
        'OriginalTraces', [{get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, ENERGY_BALANCE_ORIGINAL, 'pwr_totl')}, ...
                           {get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, ENERGY_BALANCE_ORIGINAL, 'tot_core')}, ...
                           target_orig, ...
                           wall_orig, ...
                           {get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, ENERGY_BALANCE_ORIGINAL, 'tot_rad')}], ...
        'YLabel','[W]', 'Title','Total energy balance', tp_common{:});
    yline(0,'linestyle','--','HandleVisibility','off');

    fprintf('Plot of total energy balance prepared\n');

end

%% PLOT THE TIME TRACES — DECOMPOSITION OF ENERGY FLOWS

if PLOT_DECOMPOSITION_ENERGY_FLOWS

    fig = figure('windowstyle','docked','NumberTitle','off','Name', ...
        'Decomposition of energy flows','Visible',SHOW_FIGURE_status); figs = [figs, fig];

    % Compute subplot positions depending on geometry
    if IS_LIMITER
        % Limiter: first row 2 plots (core, radiation),
        %          second row 2 plots (target, wall)
        pos_core = [0.20 0.58 0.25 0.32];
        pos_rad  = [0.56 0.58 0.25 0.32];
        pos_targets = {[0.20 0.10 0.25 0.32]};
        pos_wall = [0.56 0.10 0.25 0.32];
    elseif n_targets <= 2
        % Two targets: first row 2 plots (core, radiation),
        %              second row 3 plots (target1, target2, wall)
        pos_core = [0.20 0.58 0.25 0.32];
        pos_rad  = [0.56 0.58 0.25 0.32];
        pos_wall = [0.69 0.10 0.25 0.32];
        pos_targets = cell(1, n_targets);
        pos_targets{1} = [0.05 0.10 0.25 0.32];
        pos_targets{2} = [0.37 0.10 0.25 0.32];
    else
        % Four targets: first row 3 plots (core, radiation, wall),
        %               second row 4 plots (targets)
        margin_x = 0.04;
        gap_x = 0.03;
        plot_w_3 = (1 - 2*margin_x - 2*gap_x) / 3;
        plot_w_4 = (1 - 2*margin_x - 3*gap_x) / 4;
        plot_h = 0.32;
        y_top = 0.58;
        y_bot = 0.10;

        pos_core = [margin_x                       y_top plot_w_3 plot_h];
        pos_rad  = [margin_x + plot_w_3 + gap_x    y_top plot_w_3 plot_h];
        pos_wall = [margin_x + 2*(plot_w_3+gap_x)  y_top plot_w_3 plot_h];

        pos_targets = cell(1, n_targets);
        for t = 1:n_targets
            pos_targets{t} = [margin_x + (t-1)*(plot_w_4+gap_x)  y_bot plot_w_4 plot_h];
        end
    end

    % Core input energy
    subplot('position', pos_core);
    timeplot(time, ...
        [struct('data',ENERGY_BALANCE.heat_cor.value,  'color',COLORS{1},       'display_name','Heat crossing core boundary',       'line_style','-'), ...
         struct('data',ENERGY_BALANCE.ptnt_cor.value,  'color',COLORS_DARK{1},  'display_name','Potential energy at core boundary', 'line_style','-'), ...
         struct('data',-ENERGY_BALANCE.ntrl_cor.value, 'color',COLORS_LIGHT{1}, 'display_name','Neutral energy loss towards core',  'line_style','-')], ...
        'OriginalTime', orig_time, ...
        'OriginalTraces', {get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, ENERGY_BALANCE_ORIGINAL, 'heat_cor'), ...
                           get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, ENERGY_BALANCE_ORIGINAL, 'ptnt_cor'), ...
                           negate_orig(get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, ENERGY_BALANCE_ORIGINAL, 'ntrl_cor'))}, ...
        'YLabel','[W]', 'Title','Core input energy', tp_common{:});
    yline(0,'linestyle','--','HandleVisibility','off');

    % Radiation
    subplot('position', pos_rad);
    rad_traces = [struct('data',ENERGY_BALANCE.brms_rad.value, 'color',COLORS_LIGHT{4}, 'display_name','Bremsstrahlung radiation', 'line_style','-'), ...
                  struct('data',ENERGY_BALANCE.ntrl_rad.value, 'color',COLORS{4},       'display_name','Neutrals radiation',       'line_style','-')];
    rad_orig = {get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, ENERGY_BALANCE_ORIGINAL, 'brms_rad'), ...
                get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, ENERGY_BALANCE_ORIGINAL, 'ntrl_rad')};
    if ~isempty(labels_species)
        COLORS_RADIATION = load_colors('winter',length(labels_species),'rgb');
        for i = 1:length(labels_species)
            field_name = sprintf('imp_rad_%s', labels_species{i});
            if isfield(ENERGY_BALANCE, field_name)
                rad_traces = [rad_traces, ...
                    struct('data', ENERGY_BALANCE.(field_name).value, ...
                           'color', COLORS_RADIATION{i}, ...
                           'display_name', sprintf('Impurity line radiation (%s)', labels_species{i}), ...
                           'line_style', '-')];
                rad_orig = [rad_orig, ...
                    {get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, ENERGY_BALANCE_ORIGINAL, field_name)}];
            end
        end
    end
    timeplot(time, rad_traces, ...
        'OriginalTime', orig_time, ...
        'OriginalTraces', rad_orig, ...
        'YLabel','[W]', 'Title','Radiation', tp_common{:});

    % Energy load onto targets and wall
    if IS_LIMITER
        % Limiter: decompose target and wall into plasma + neutrals only
        subplot('position', pos_targets{1});
        timeplot(time, ...
            [struct('data',ENERGY_BALANCE.plsm_trg.value, 'color',COLORS{1}, 'display_name','Plasma energy load',   'line_style','-'), ...
             struct('data',ENERGY_BALANCE.ntrl_trg.value, 'color',COLORS{5}, 'display_name','Neutrals energy load', 'line_style','-')], ...
            'OriginalTime', orig_time, ...
            'OriginalTraces', {get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, ENERGY_BALANCE_ORIGINAL, 'plsm_trg'), ...
                               get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, ENERGY_BALANCE_ORIGINAL, 'ntrl_trg')}, ...
            'YLabel','[W]', 'Title','Energy load onto target', tp_common{:});
        yline(0,'linestyle','--','HandleVisibility','off');

        subplot('position', pos_wall);
        timeplot(time, ...
            [struct('data',ENERGY_BALANCE.plsm_wll.value, 'color',COLORS{1}, 'display_name','Plasma energy load',   'line_style','-'), ...
             struct('data',ENERGY_BALANCE.ntrl_wll.value, 'color',COLORS{5}, 'display_name','Neutrals energy load', 'line_style','-')], ...
            'OriginalTime', orig_time, ...
            'OriginalTraces', {get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, ENERGY_BALANCE_ORIGINAL, 'plsm_wll'), ...
                               get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, ENERGY_BALANCE_ORIGINAL, 'ntrl_wll')}, ...
            'YLabel','[W]', 'Title','Energy load onto main wall', tp_common{:});
        yline(0,'linestyle','--','HandleVisibility','off');
    else
        % Divertor: decompose each target into plasma + neutrals + ionizations + dissociations
        for t = 1:n_targets
            sf = targets(t).suffix;
            lb = targets(t).label;

            subplot('position', pos_targets{t});
            timeplot(time, ...
                [struct('data',ENERGY_BALANCE.(sprintf('pwr_plsm_%s',sf)).value, 'color',COLORS{1},       'display_name','Plasma energy load',              'line_style','-'), ...
                 struct('data',ENERGY_BALANCE.(sprintf('pwr_neut_%s',sf)).value, 'color',COLORS{5},       'display_name','Neutrals energy load',             'line_style','-'), ...
                 struct('data',ENERGY_BALANCE.(sprintf('pwr_ionz_%s',sf)).value, 'color',COLORS{2},       'display_name','Energy released by ionizations',   'line_style','-'), ...
                 struct('data',ENERGY_BALANCE.(sprintf('pwr_diss_%s',sf)).value, 'color',COLORS_LIGHT{2}, 'display_name','Energy released by dissociations', 'line_style','-')], ...
                'OriginalTime', orig_time, ...
                'OriginalTraces', {get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, ENERGY_BALANCE_ORIGINAL, sprintf('pwr_plsm_%s',sf)), ...
                                   get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, ENERGY_BALANCE_ORIGINAL, sprintf('pwr_neut_%s',sf)), ...
                                   get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, ENERGY_BALANCE_ORIGINAL, sprintf('pwr_ionz_%s',sf)), ...
                                   get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, ENERGY_BALANCE_ORIGINAL, sprintf('pwr_diss_%s',sf))}, ...
                'YLabel','[W]', 'Title',sprintf('Energy load onto %s', lb), tp_common{:});
            yline(0,'linestyle','--','HandleVisibility','off');
        end

        % Wall decomposition for divertor geometries
        subplot('position', pos_wall);
        timeplot(time, ...
            [struct('data',ENERGY_BALANCE.pwr_plsm_wl.value, 'color',COLORS{1},       'display_name','Plasma energy load',              'line_style','-'), ...
             struct('data',ENERGY_BALANCE.pwr_neut_wl.value,  'color',COLORS{5},       'display_name','Neutrals energy load',             'line_style','-'), ...
             struct('data',ENERGY_BALANCE.pwr_ionz_wl.value,  'color',COLORS{2},       'display_name','Energy released by ionizations',   'line_style','-'), ...
             struct('data',ENERGY_BALANCE.pwr_diss_wl.value,  'color',COLORS_LIGHT{2}, 'display_name','Energy released by dissociations', 'line_style','-')], ...
            'OriginalTime', orig_time, ...
            'OriginalTraces', {get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, ENERGY_BALANCE_ORIGINAL, 'pwr_plsm_wl'), ...
                               get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, ENERGY_BALANCE_ORIGINAL, 'pwr_neut_wl'), ...
                               get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, ENERGY_BALANCE_ORIGINAL, 'pwr_ionz_wl'), ...
                               get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, ENERGY_BALANCE_ORIGINAL, 'pwr_diss_wl')}, ...
            'YLabel','[W]', 'Title','Energy load onto main wall', tp_common{:});
        yline(0,'linestyle','--','HandleVisibility','off');
    end

    fprintf('Plot of decomposition of energy flows prepared\n');

end

%% PRINT THE PLOTS

if PRINT_FIGURE
    print_plot(figs, [FIGURE_WIDTH FIGURE_HEIGHT], 'balance_energy', FILE_FORMAT, FILE_RESOLUTION);
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

function orig_cells = get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, EB_ORIGINAL, field_name)

% GET_ORIG extracts original data cell array for energy balance fields

    if HAS_AVERAGING && PLOT_ORIGINAL_DATA && isfield(EB_ORIGINAL, field_name)
        raw = EB_ORIGINAL.(field_name).value;
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

function orig_cells = negate_orig(orig_input)

% NEGATE_ORIG negates the values in an original data cell array
%   Used for quantities that are plotted with a sign flip (e.g. -ntrl_cor)

    if isempty(orig_input)
        orig_cells = {};
        return;
    end

    orig_cells = cell(size(orig_input));
    for j = 1:numel(orig_input)
        orig_cells{j} = -orig_input{j};
    end
end
