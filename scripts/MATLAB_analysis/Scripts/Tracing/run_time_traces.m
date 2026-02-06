function run_time_traces(RUN_DIRECTORY, varargin)

%% SELECT THE SIMULATION

RUN = '';

%% SCRIPT DESCRIPTION

% RUN_TIME_TRACES plots the main time traces of the current run
%    (state variables and species densities at the outer midplane
%    and at the divertor targets, poloidal and radial fluxes, integral
%    quantities), extracted from b2time.nc.
% It can be used both while a simulation is running, to monitor its
%    status, and after the run has stopped.
% The plots are shown grouped in a multi-tab full-window figure.
% Various time-averaging schemes can also be applied to the time traces.
% Can be executed both from the command line, inside one specific run
%    directory, or as an interactive script within the MATLAB GUI,
%    in the last case requiring the manual definition of the
%    run directory of the simulation to be shown

%% USER INPUT

% Select which groups of time traces to plot
PLOT_MIDPLANE_STATE_VARIABLES = true;
PLOT_MIDPLANE_SPECIES_DENSITIES = false;
PLOT_DIVERTOR_STATE_VARIABLES = true;
PLOT_DIVERTOR_SPECIES_DENSITIES = false;
PLOT_POLOIDAL_FLUXES = true;
PLOT_RADIAL_FLUXES = true;
PLOT_INTEGRAL_QUANTITIES = false;

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
% (colors for various types of plots, linewidths,
% time range to show in the plots and style of y-axis range)
COLOR_DENSITIES = 'blue';
COLOR_TEMPERATURES = 'red';
COLOR_PARTICLE_FLUXES = 'blue';
COLOR_ENERGY_FLUXES = 'red';
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

FUNC_NAME = 'run_time_traces';

DESCRIPTION = {
    'RUN_TIME_TRACES plots the main time traces of the current run'
    '   (state variables and species densities at the outer midplane'
    '   and at the divertor targets, poloidal and radial fluxes, integral'
    '   quantities), extracted from b2time.nc.'
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

PARAMS(end+1) = struct('name', 'PLOT_MIDPLANE_STATE_VARIABLES', 'type', 'logical', ...
    'default', PLOT_MIDPLANE_STATE_VARIABLES, 'required', false, ...
    'comment', 'Plot state variables at outer midplane', ...
    'validator', @(x) islogical(x) || isnumeric(x));

PARAMS(end+1) = struct('name', 'PLOT_MIDPLANE_SPECIES_DENSITIES', 'type', 'logical', ...
    'default', PLOT_MIDPLANE_SPECIES_DENSITIES, 'required', false, ...
    'comment', 'Plot species densities at outer midplane', ...
    'validator', @(x) islogical(x) || isnumeric(x));

PARAMS(end+1) = struct('name', 'PLOT_DIVERTOR_STATE_VARIABLES', 'type', 'logical', ...
    'default', PLOT_DIVERTOR_STATE_VARIABLES, 'required', false, ...
    'comment', 'Plot state variables at divertor targets', ...
    'validator', @(x) islogical(x) || isnumeric(x));

PARAMS(end+1) = struct('name', 'PLOT_DIVERTOR_SPECIES_DENSITIES', 'type', 'logical', ...
    'default', PLOT_DIVERTOR_SPECIES_DENSITIES, 'required', false, ...
    'comment', 'Plot species densities at divertor targets', ...
    'validator', @(x) islogical(x) || isnumeric(x));

PARAMS(end+1) = struct('name', 'PLOT_POLOIDAL_FLUXES', 'type', 'logical', ...
    'default', PLOT_POLOIDAL_FLUXES, 'required', false, ...
    'comment', 'Plot poloidal fluxes', ...
    'validator', @(x) islogical(x) || isnumeric(x));

PARAMS(end+1) = struct('name', 'PLOT_RADIAL_FLUXES', 'type', 'logical', ...
    'default', PLOT_RADIAL_FLUXES, 'required', false, ...
    'comment', 'Plot radial fluxes', ...
    'validator', @(x) islogical(x) || isnumeric(x));

PARAMS(end+1) = struct('name', 'PLOT_INTEGRAL_QUANTITIES', 'type', 'logical', ...
    'default', PLOT_INTEGRAL_QUANTITIES, 'required', false, ...
    'comment', 'Plot integral quantities', ...
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

PARAMS(end+1) = struct('name', 'COLOR_DENSITIES', 'type', 'char', ...
    'default', COLOR_DENSITIES, 'required', false, ...
    'comment', 'Line color for density-related plots', ...
    'validator', @ischar);

PARAMS(end+1) = struct('name', 'COLOR_TEMPERATURES', 'type', 'char', ...
    'default', COLOR_TEMPERATURES, 'required', false, ...
    'comment', 'Line color for temperature-related plots', ...
    'validator', @ischar);

PARAMS(end+1) = struct('name', 'COLOR_PARTICLE_FLUXES', 'type', 'char', ...
    'default', COLOR_PARTICLE_FLUXES, 'required', false, ...
    'comment', 'Line color for particle-fluxes-related plots', ...
    'validator', @ischar);

PARAMS(end+1) = struct('name', 'COLOR_ENERGY_FLUXES', 'type', 'char', ...
    'default', COLOR_ENERGY_FLUXES, 'required', false, ...
    'comment', 'Line color for energy-fluxes-related plots', ...
    'validator', @ischar);

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
[PLOT_MIDPLANE_STATE_VARIABLES, PLOT_MIDPLANE_SPECIES_DENSITIES, ...
 PLOT_DIVERTOR_STATE_VARIABLES, PLOT_DIVERTOR_SPECIES_DENSITIES, ...
 PLOT_POLOIDAL_FLUXES, PLOT_RADIAL_FLUXES, PLOT_INTEGRAL_QUANTITIES, ...
 ROLLING_AVERAGE_STEPS, BATCH_AVERAGE_STEPS, PHASE_AVERAGE_STEPS, PLOT_ORIGINAL_DATA, ...
 COLOR_DENSITIES, COLOR_TEMPERATURES, COLOR_PARTICLE_FLUXES, COLOR_ENERGY_FLUXES, ...
 LINEWIDTH, TMIN, TMAX, YLIM_STYLE, FIGURE_WIDTH, FIGURE_HEIGHT, ...
 SHOW_NAME, SHOW_FIGURE, PRINT_FIGURE, FILE_FORMAT, FILE_RESOLUTION] = ...
    extract_params(p.Results, PARAMS);

%% SANITY CHECK OF USER INPUTS

% Variables which should be logicals
logicals_selection = {'PLOT_MIDPLANE_STATE_VARIABLES'
                      'PLOT_MIDPLANE_SPECIES_DENSITIES'
                      'PLOT_DIVERTOR_STATE_VARIABLES'
                      'PLOT_DIVERTOR_SPECIES_DENSITIES'
                      'PLOT_POLOIDAL_FLUXES'
                      'PLOT_RADIAL_FLUXES'
                      'PLOT_INTEGRAL_QUANTITIES'
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
strings_selection = {'COLOR_DENSITIES'
                     'COLOR_TEMPERATURES'
                     'COLOR_PARTICLE_FLUXES'
                     'COLOR_ENERGY_FLUXES'
                     'YLIM_STYLE'
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

% Check availably styles of Y-limiys
if not(strcmp(YLIM_STYLE,'tickaligned') || strcmp(YLIM_STYLE,'tight') || strcmp(YLIM_STYLE,'padded')) 
    error('Error: YLIM_STYLE can only be ''tickaligned'', ''tight'' or ''padded''');
end

% Check available groups of colors
valid_colors = {'blue','red','yellow','purple','green','cyan','magenta'};
color_vars = {'COLOR_DENSITIES','COLOR_TEMPERATURES','COLOR_PARTICLE_FLUXES','COLOR_ENERGY_FLUXES'};
for k = 1:numel(color_vars)
    var_name = color_vars{k};
    color_value = eval(var_name);
    if ~ismember(color_value, valid_colors)
        error('Error: %s can only be one of %s', var_name, strjoin(valid_colors, ', '));
    end
end

% Plots should be either shown or printed
if ~SHOW_FIGURE && ~PRINT_FIGURE
    error('Error: SHOW_FIGURE and PRINT_FIGURE cannot be both false');
end

%% LOAD SIMULATION

SIMULATION = load_solps_simulation(RUN);

%% READ DATA

% Extract data from b2time.nc
TIME_TRACES = read_b2time(SIMULATION,'TIME_TRACES');

% Read the species labels
if PLOT_MIDPLANE_SPECIES_DENSITIES || PLOT_DIVERTOR_SPECIES_DENSITIES
    [species_label,atomic_number,charge_state] = read_species(SIMULATION);
end

%% APPLY AVERAGING SCHEMES

TIME_TRACES_ORIGINAL = TIME_TRACES;

% Rolling average
if ROLLING_AVERAGE_STEPS > 0
    time_step = TIME_TRACES.timesa.value(2) - TIME_TRACES.timesa.value(1);
    fields = fieldnames(TIME_TRACES);
    for i = 1:numel(fields)
        f = fields{i};
        if ~ismember(f, {'timesa'})
            TIME_TRACES.(f).value = rolling_average(TIME_TRACES.(f).value,ROLLING_AVERAGE_STEPS,'b2time');
            TIME_TRACES_ORIGINAL.(f).value = {TIME_TRACES_ORIGINAL.(f).value};
        end
    end
    fprintf('Rolling average of the time traces computed over a period of %d time steps (%.1e s)\n',...
        ROLLING_AVERAGE_STEPS,ROLLING_AVERAGE_STEPS*time_step)
end

% Batch average
if BATCH_AVERAGE_STEPS > 0
    time_step = TIME_TRACES.timesa.value(2) - TIME_TRACES.timesa.value(1);
    fields = fieldnames(TIME_TRACES);
    for i = 1:numel(fields)
        f = fields{i};
        if ~ismember(f, {'timesa'})
            TIME_TRACES.(f).value = batch_average(TIME_TRACES.(f).value,BATCH_AVERAGE_STEPS,'b2time');
            TIME_TRACES_ORIGINAL.(f).value = {TIME_TRACES_ORIGINAL.(f).value};
        else
            TIME_TRACES.timesa.value = batch_average(TIME_TRACES.timesa.value,BATCH_AVERAGE_STEPS,'time');
        end
    end
    fprintf('Batch average of the time traces computed over a period of %d time steps (%.1e s)\n',...
        BATCH_AVERAGE_STEPS,BATCH_AVERAGE_STEPS*time_step)
end

% Phase average
if PHASE_AVERAGE_STEPS > 0
    time_step = TIME_TRACES.timesa.value(2) - TIME_TRACES.timesa.value(1);
    fields = fieldnames(TIME_TRACES);
    for i = 1:numel(fields)
        f = fields{i};
        if ~ismember(f, {'timesa'})
            [TIME_TRACES.(f).value,TIME_TRACES_ORIGINAL.(f).value] = phase_average(TIME_TRACES.(f).value,PHASE_AVERAGE_STEPS,'b2time_time_traces');
        else
            [TIME_TRACES.timesa.value,TIME_TRACES_ORIGINAL.timesa.value] = phase_average(TIME_TRACES.timesa.value,PHASE_AVERAGE_STEPS,'time');
        end
    end
    fprintf('Phase average of the time traces computed over a period of %d time steps (%.1e s)\n',...
        PHASE_AVERAGE_STEPS,PHASE_AVERAGE_STEPS*time_step)
end

%% INITIALIZE FIGURES

figs = [];

if SHOW_FIGURE
    SHOW_FIGURE_status = 'on';
else
    SHOW_FIGURE_status = 'off';
end

HAS_AVERAGING = (ROLLING_AVERAGE_STEPS > 0 || BATCH_AVERAGE_STEPS > 0 || PHASE_AVERAGE_STEPS > 0);
if HAS_AVERAGING && PLOT_ORIGINAL_DATA
    orig_time = TIME_TRACES_ORIGINAL.timesa.value;
else
    orig_time = [];
end

% Load colors
COLORS = load_colors('default',7,'rgb');
COLORS_DARK = load_colors('default_dark',7,'rgb');
COLORS_LIGHT = load_colors('default_light',7,'rgb');
groups = {'DENSITIES','TEMPERATURES','PARTICLE_FLUXES','ENERGY_FLUXES'};
for k = 1:numel(groups)
    prefix = groups{k};
    color_name = eval(sprintf('COLOR_%s', prefix));
    switch color_name
        case 'blue',    color_index = 1;
        case 'red',     color_index = 2;
        case 'yellow',  color_index = 3;
        case 'purple',  color_index = 4;
        case 'green',   color_index = 5;
        case 'cyan',    color_index = 6;
        case 'magenta', color_index = 7;
    end 
    eval(sprintf('COLOR_%s       = COLORS{%d};',       prefix, color_index));
    eval(sprintf('COLOR_%s_DARK  = COLORS_DARK{%d};',  prefix, color_index));
    eval(sprintf('COLOR_%s_LIGHT = COLORS_LIGHT{%d};', prefix, color_index));
end

% Set Y-limits style
originalYLimitMethod = get(groot, 'defaultAxesYLimitMethod');
set(groot, 'defaultAxesYLimitMethod', YLIM_STYLE);

% Common properties for all plots
tp_common = {'LineWidth', LINEWIDTH, 'TMIN', TMIN, 'TMAX', TMAX, ...
             'ShowName', SHOW_NAME, 'RunName', RUN};

% Define the groups of plots depending on the grid topology
ncut = size(TIME_TRACES.nesepm.value,1);
if ncut == 1
    if strcmp(SIMULATION.geometry_type,'Limiter')
        titles_midplane_state_variables = {'Midpoint state variables'};
        titles_midplane_species_densities = {'Midpoint species densities'};
        labels_midplane = {'LCFS, midpoint'};
        titles_divertor_state_variables = {'Targets state variables'};
        titles_divertor_species_densities = {'Targets species densities'};
        labels_divertor = {{'LCFS, left','Max., left','LCFS, right','Max., right'}};
        titles_poloidal_fluxes = {'Poloidal fluxes'};
        labels_poloidal_fluxes = {{'Left target','Right target'}};
        titles_radial_fluxes = {'Radial fluxes'};
        labels_radial_fluxes = {{'Wall boundary',''}};
    else
        titles_midplane_state_variables = {'Outer midplane state variables'};
        titles_midplane_species_densities = {'Outer midplane species densities'};
        labels_midplane = {'Sep., outer midplane'};
        titles_divertor_state_variables = {'Divertor state variables'};
        titles_divertor_species_densities = {'Divertor species densities'};
        if strcmp(SIMULATION.geometry_type,'Lower single null')
            labels_divertor = {{'Sep., inner target','Max., inner target','Sep., outer target','Max., outer target'}};
        elseif strcmp(SIMULATION.geometry_type,'Upper single null')
            labels_divertor = {{'Sep., outer target','Max., outer target','Sep., inner target','Max., inner target'}};
        end
        titles_poloidal_fluxes = {'Poloidal fluxes'};
        if strcmp(SIMULATION.geometry_type,'Lower single null')
            labels_poloidal_fluxes = {{'Inner target','Outer target'}};
        elseif strcmp(SIMULATION.geometry_type,'Upper single null')
            labels_poloidal_fluxes = {{'Outer target','Inner target'}};
        end
        titles_radial_fluxes = {'Radial fluxes'};
        labels_radial_fluxes = {{'Wall boundary','PFR boundary'}};
    end
else
    if strcmp(SIMULATION.geometry_type,'Connected double null') || strcmp(SIMULATION.geometry_type,'Disconnected double null')
        titles_midplane_state_variables = {'Outer midplane state variables','Inner midplane state variables'};
        titles_midplane_species_densities = {'Outer midplane species densities','Inner midplane species densities'};
        labels_midplane = {'Sep., inner midplane','Sep., outer midplane'};
        titles_divertor_state_variables = {'Bottom divertor state variables','Top divertor state variables'};
        titles_divertor_species_densities = {'Bottom divertor species densities','Top divertor species densities'};
        labels_divertor = {{'Sep., inner target, bottom','Max., inner target, bottom','Sep., outer target, bottom','Max., outer target, bottom'},...
                           {'Sep., inner target, top','Max., inner target, top','Sep., outer target, top','Max., outer target, top'}};
        titles_poloidal_fluxes = {'Bottom divertor poloidal fluxes','Top divertor poloidal fluxes'};
        labels_poloidal_fluxes = {{'Inner target, bottom','Outer target, bottom'},{'Inner target, top','Outer target, top'}};
        titles_radial_fluxes = {'Outer side radial fluxes','Inner side radial fluxes'};
        labels_radial_fluxes = {{'Wall boundary, outer side','PFR boundary, outer side'},{'Wall boundary, inner side','PFR boundary, inner side'}};
    else
        titles_midplane_state_variables = {'Outer midplane state variables','Inner midplane state variables'};
        titles_midplane_species_densities = {'Outer midplane species densities','Inner midplane species densities'};
        labels_midplane = {'Sep., inner midplane','Sep., outer midplane'};
        titles_divertor_state_variables = {'Primary divertor state variables','Secondary divertor state variables'};
        titles_divertor_species_densities = {'Primary divertor species densities','Secondary divertor species densities'};
        labels_divertor = {{'Sep., inner target, primary','Max., inner target, primary','Sep., outer target, primary','Max., outer target, primary'},...
                           {'Sep., outer target, far SOL','Max., outer target, far SOL','Sep., outer target, secondary','Max., outer target, secondary'}};
        titles_poloidal_fluxes = {'Primary divertor poloidal fluxes','Secondary divertor poloidal fluxes'};
        labels_poloidal_fluxes = {{'Inner target, primary','Outer target, primary'},{'Outer target, far SOL','Outer target, secondary'}};
        titles_radial_fluxes = {'Primary radial fluxes','Secondary radial fluxes'};
        labels_radial_fluxes = {{'Wall boundary, primary','PFR boundary, primary'},{'Wall boundary, secondary','PFR boundary, secondary'}};
    end
end

%% PLOT MIDPLANE STATE VARIABLES

if PLOT_MIDPLANE_STATE_VARIABLES

    for i = 1:ncut

        fig = figure('windowstyle','docked','NumberTitle','off','Name',titles_midplane_state_variables{i},'Visible',SHOW_FIGURE_status); figs = [figs, fig];

        % Separatrix electron density
        subplot('position',[0.08 0.25 0.42 0.5]);
        timeplot(TIME_TRACES.timesa.value, ...
            struct('data',TIME_TRACES.nesepm.value(i,:), 'color',COLOR_DENSITIES, 'display_name',labels_midplane{i}, 'line_style','-'), ...
            'OriginalTime', orig_time, ...
            'OriginalTraces', {get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, TIME_TRACES_ORIGINAL, 'nesepm', {i,':'})}, ...
            'YLabel','$n_e$ [m$^{-3}$]', 'Title','Midplane electron density', tp_common{:});

        % Separatrix electron temperature
        subplot('position',[0.57 0.55 0.32 0.38]);
        timeplot(TIME_TRACES.timesa.value, ...
            struct('data',TIME_TRACES.tesepm.value(i,:), 'color',COLOR_TEMPERATURES, 'display_name',labels_midplane{i}, 'line_style','-'), ...
            'OriginalTime', orig_time, ...
            'OriginalTraces', {get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, TIME_TRACES_ORIGINAL, 'tesepm', {i,':'})}, ...
            'YLabel','$T_e$ [eV]', 'Title','Midplane electron temperature', ...
            'LabelFontSize',16, 'TitleFontSize',18, tp_common{:});

        % Separatrix ion temperature
        subplot('position',[0.57 0.06 0.32 0.38]);
        timeplot(TIME_TRACES.timesa.value, ...
            struct('data',TIME_TRACES.tisepm.value(i,:), 'color',COLOR_TEMPERATURES, 'display_name',labels_midplane{i}, 'line_style','-'), ...
            'OriginalTime', orig_time, ...
            'OriginalTraces', {get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, TIME_TRACES_ORIGINAL, 'tisepm', {i,':'})}, ...
            'YLabel','$T_i$ [eV]', 'Title','Midplane ion temperature', ...
            'LabelFontSize',16, 'TitleFontSize',18, tp_common{:});
    end

    fprintf('Plot of midplane species variables prepared\n');

end

%% PLOT MIDPLANE SPECIES DENSITIES

if PLOT_MIDPLANE_SPECIES_DENSITIES

    if not(isfield(TIME_TRACES,'nasepm'))
        error('Error: species densities fields not present in b2time.nc')
    end

    ns = length(species_label);
    positions{1}=[0.03 0.58 0.20 0.32]; positions{2}=[0.28 0.58 0.20 0.32];
    positions{3}=[0.53 0.58 0.20 0.32]; positions{4}=[0.78 0.58 0.20 0.32];
    positions{5}=[0.03 0.10 0.20 0.32]; positions{6}=[0.28 0.10 0.20 0.32];
    positions{7}=[0.53 0.10 0.20 0.32]; positions{8}=[0.78 0.10 0.20 0.32];

    for i = 1:ncut

        is = 1; iatm = 1;
        while is <= ns

            if mod(is-1,8) == 0
                fig = figure('windowstyle','docked','NumberTitle','off','Name',titles_midplane_species_densities{i},'Visible',SHOW_FIGURE_status); figs = [figs, fig];
            end

            % Separatrix density of species is
            subplot('position',positions{mod(is-1,8)+1});
            if charge_state(is)==0
                sp_title = sprintf('Midplane %s atom density',species_label{is});
            else
                sp_title = sprintf('Midplane %s ion density',species_label{is});
            end
            sp_ylabel = sprintf('$n_{%s}$ [m$^{-3}$]',species_label{is});
            if charge_state(is)==0
                try
                    timeplot(TIME_TRACES.timesa.value, ...
                        struct('data',squeeze(TIME_TRACES.dabsepm.value(i,iatm,:))', 'color',COLOR_DENSITIES, 'display_name',labels_midplane{i}, 'line_style','-'), ...
                        'OriginalTime', orig_time, ...
                        'OriginalTraces', {get_orig_3d(HAS_AVERAGING, PLOT_ORIGINAL_DATA, TIME_TRACES_ORIGINAL, 'dabsepm', i, iatm)}, ...
                        'YLabel',sp_ylabel, 'Title',sp_title, tp_common{:});
                catch
                    timeplot(TIME_TRACES.timesa.value, ...
                        struct('data',squeeze(TIME_TRACES.nasepm.value(i,is,:))', 'color',COLOR_DENSITIES, 'display_name',labels_midplane{i}, 'line_style','-'), ...
                        'OriginalTime', orig_time, ...
                        'OriginalTraces', {get_orig_3d(HAS_AVERAGING, PLOT_ORIGINAL_DATA, TIME_TRACES_ORIGINAL, 'nasepm', i, is)}, ...
                        'YLabel',sp_ylabel, 'Title',sp_title, tp_common{:});
                end
                iatm = iatm+1;
            else
                timeplot(TIME_TRACES.timesa.value, ...
                    struct('data',squeeze(TIME_TRACES.nasepm.value(i,is,:))', 'color',COLOR_DENSITIES, 'display_name',labels_midplane{i}, 'line_style','-'), ...
                    'OriginalTime', orig_time, ...
                    'OriginalTraces', {get_orig_3d(HAS_AVERAGING, PLOT_ORIGINAL_DATA, TIME_TRACES_ORIGINAL, 'nasepm', i, is)}, ...
                    'YLabel',sp_ylabel, 'Title',sp_title, tp_common{:});
            end
            is = is+1;

        end
    
    end

    fprintf('Plot of midplane species densities prepared\n');

end

%% PLOT DIVERTOR STATE VARIABLES

if PLOT_DIVERTOR_STATE_VARIABLES

    for i = 1:ncut

        fig = figure('windowstyle','docked','NumberTitle','off','Name',titles_divertor_state_variables{i},'Visible',SHOW_FIGURE_status); figs = [figs, fig];

        % Separatrix and maximum electron densities
        subplot('position',[0.08 0.25 0.42 0.5]);
        timeplot(TIME_TRACES.timesa.value, ...
            [struct('data',TIME_TRACES.nesepi.value(i,:), 'color',COLOR_DENSITIES_LIGHT, 'display_name',labels_divertor{i}{1}, 'line_style','-'), ...
             struct('data',TIME_TRACES.nemxip.value(i,:), 'color',COLOR_DENSITIES_LIGHT, 'display_name',labels_divertor{i}{2}, 'line_style',':'), ...
             struct('data',TIME_TRACES.nesepa.value(i,:), 'color',COLOR_DENSITIES_DARK,  'display_name',labels_divertor{i}{3}, 'line_style','-'), ...
             struct('data',TIME_TRACES.nemxap.value(i,:), 'color',COLOR_DENSITIES_DARK,  'display_name',labels_divertor{i}{4}, 'line_style',':')], ...
            'OriginalTime', orig_time, ...
            'OriginalTraces', {get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, TIME_TRACES_ORIGINAL, 'nesepi', {i,':'}), ...
                               get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, TIME_TRACES_ORIGINAL, 'nemxip', {i,':'}), ...
                               get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, TIME_TRACES_ORIGINAL, 'nesepa', {i,':'}), ...
                               get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, TIME_TRACES_ORIGINAL, 'nemxap', {i,':'})}, ...
            'YLabel','$n_e$ [m$^{-3}$]', 'Title','Divertor electron density', tp_common{:});

        % Separatrix and maximum electron temperatures
        subplot('position',[0.57 0.55 0.32 0.38]);
        timeplot(TIME_TRACES.timesa.value, ...
            [struct('data',TIME_TRACES.tesepi.value(i,:), 'color',COLOR_TEMPERATURES_LIGHT, 'display_name',labels_divertor{i}{1}, 'line_style','-'), ...
             struct('data',TIME_TRACES.temxip.value(i,:), 'color',COLOR_TEMPERATURES_LIGHT, 'display_name',labels_divertor{i}{2}, 'line_style',':'), ...
             struct('data',TIME_TRACES.tesepa.value(i,:), 'color',COLOR_TEMPERATURES_DARK,  'display_name',labels_divertor{i}{3}, 'line_style','-'), ...
             struct('data',TIME_TRACES.temxap.value(i,:), 'color',COLOR_TEMPERATURES_DARK,  'display_name',labels_divertor{i}{4}, 'line_style',':')], ...
            'OriginalTime', orig_time, ...
            'OriginalTraces', {get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, TIME_TRACES_ORIGINAL, 'tesepi', {i,':'}), ...
                               get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, TIME_TRACES_ORIGINAL, 'temxip', {i,':'}), ...
                               get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, TIME_TRACES_ORIGINAL, 'tesepa', {i,':'}), ...
                               get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, TIME_TRACES_ORIGINAL, 'temxap', {i,':'})}, ...
            'YLabel','$T_e$ [eV]', 'Title','Divertor electron temperature', ...
            'LabelFontSize',16, 'TitleFontSize',18, tp_common{:});

        % Separatrix and maximum ion temperatures
        subplot('position',[0.57 0.06 0.32 0.38]);
        timeplot(TIME_TRACES.timesa.value, ...
            [struct('data',TIME_TRACES.tisepi.value(i,:), 'color',COLOR_TEMPERATURES_LIGHT, 'display_name',labels_divertor{i}{1}, 'line_style','-'), ...
             struct('data',TIME_TRACES.timxip.value(i,:), 'color',COLOR_TEMPERATURES_LIGHT, 'display_name',labels_divertor{i}{2}, 'line_style',':'), ...
             struct('data',TIME_TRACES.tisepa.value(i,:), 'color',COLOR_TEMPERATURES_DARK,  'display_name',labels_divertor{i}{3}, 'line_style','-'), ...
             struct('data',TIME_TRACES.timxap.value(i,:), 'color',COLOR_TEMPERATURES_DARK,  'display_name',labels_divertor{i}{4}, 'line_style',':')], ...
            'OriginalTime', orig_time, ...
            'OriginalTraces', {get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, TIME_TRACES_ORIGINAL, 'tisepi', {i,':'}), ...
                               get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, TIME_TRACES_ORIGINAL, 'timxip', {i,':'}), ...
                               get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, TIME_TRACES_ORIGINAL, 'tisepa', {i,':'}), ...
                               get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, TIME_TRACES_ORIGINAL, 'timxap', {i,':'})}, ...
            'YLabel','$T_i$ [eV]', 'Title','Divertor ion temperature', ...
            'LabelFontSize',16, 'TitleFontSize',18, tp_common{:});
    
    end

    fprintf('Plot of divertor state variables prepared\n');

end

%% PLOT DIVERTOR SPECIES DENSITIES

if PLOT_DIVERTOR_SPECIES_DENSITIES

    if not(isfield(TIME_TRACES,'nasepm'))
        error('Error: species densities fields not present in b2time.nc')
    end

    ns = length(species_label);
    positions{1}=[0.03 0.58 0.20 0.32]; positions{2}=[0.28 0.58 0.20 0.32];
    positions{3}=[0.53 0.58 0.20 0.32]; positions{4}=[0.78 0.58 0.20 0.32];
    positions{5}=[0.03 0.10 0.20 0.32]; positions{6}=[0.28 0.10 0.20 0.32];
    positions{7}=[0.53 0.10 0.20 0.32]; positions{8}=[0.78 0.10 0.20 0.32];

    for i = 1:ncut

        is = 1; iatm = 1;
        while is <= ns

            if mod(is-1,8) == 0
                fig = figure('windowstyle','docked','NumberTitle','off','Name',titles_divertor_species_densities{i},'Visible',SHOW_FIGURE_status); figs = [figs, fig];
            end

            % Separatrix and maximum densities of species is
            subplot('position',positions{mod(is-1,8)+1});
            if charge_state(is)==0
                sp_title = sprintf('Divertor %s atom density',species_label{is});
            else
                sp_title = sprintf('Divertor %s ion density',species_label{is});
            end
            sp_ylabel = sprintf('$n_{%s}$ [m$^{-3}$]',species_label{is});
            if charge_state(is)==0
                try
                    timeplot(TIME_TRACES.timesa.value, ...
                        [struct('data',squeeze(TIME_TRACES.dabsepi.value(i,iatm,:))', 'color',COLOR_DENSITIES_LIGHT, 'display_name',labels_divertor{i}{1}, 'line_style','-'), ...
                         struct('data',squeeze(TIME_TRACES.dabsepa.value(i,iatm,:))', 'color',COLOR_DENSITIES_DARK,  'display_name',labels_divertor{i}{3}, 'line_style','-')], ...
                        'OriginalTime', orig_time, ...
                        'OriginalTraces', {get_orig_3d(HAS_AVERAGING, PLOT_ORIGINAL_DATA, TIME_TRACES_ORIGINAL, 'dabsepi', i, iatm), ...
                                           get_orig_3d(HAS_AVERAGING, PLOT_ORIGINAL_DATA, TIME_TRACES_ORIGINAL, 'dabsepa', i, iatm)}, ...
                        'YLabel',sp_ylabel, 'Title',sp_title, tp_common{:});
                catch
                    timeplot(TIME_TRACES.timesa.value, ...
                        [struct('data',squeeze(TIME_TRACES.nasepi.value(i,is,:))',  'color',COLOR_DENSITIES_LIGHT, 'display_name',labels_divertor{i}{1}, 'line_style','-'), ...
                         struct('data',squeeze(TIME_TRACES.namxip.value(i,is,:))',  'color',COLOR_DENSITIES_LIGHT, 'display_name',labels_divertor{i}{2}, 'line_style',':'), ...
                         struct('data',squeeze(TIME_TRACES.nesepa.value(i,is,:))',  'color',COLOR_DENSITIES_DARK,  'display_name',labels_divertor{i}{3}, 'line_style','-'), ...
                         struct('data',squeeze(TIME_TRACES.namxap.value(i,is,:))',  'color',COLOR_DENSITIES_DARK,  'display_name',labels_divertor{i}{4}, 'line_style',':')], ...
                        'OriginalTime', orig_time, ...
                        'OriginalTraces', {get_orig_3d(HAS_AVERAGING, PLOT_ORIGINAL_DATA, TIME_TRACES_ORIGINAL, 'nasepi', i, is), ...
                                           get_orig_3d(HAS_AVERAGING, PLOT_ORIGINAL_DATA, TIME_TRACES_ORIGINAL, 'namxip', i, is), ...
                                           get_orig_3d(HAS_AVERAGING, PLOT_ORIGINAL_DATA, TIME_TRACES_ORIGINAL, 'nesepa', i, is), ...
                                           get_orig_3d(HAS_AVERAGING, PLOT_ORIGINAL_DATA, TIME_TRACES_ORIGINAL, 'namxap', i, is)}, ...
                        'YLabel',sp_ylabel, 'Title',sp_title, tp_common{:});
                end
                iatm = iatm+1;
            else
                timeplot(TIME_TRACES.timesa.value, ...
                    [struct('data',squeeze(TIME_TRACES.nasepi.value(i,is,:))',  'color',COLOR_DENSITIES_LIGHT, 'display_name',labels_divertor{i}{1}, 'line_style','-'), ...
                     struct('data',squeeze(TIME_TRACES.namxip.value(i,is,:))',  'color',COLOR_DENSITIES_LIGHT, 'display_name',labels_divertor{i}{2}, 'line_style',':'), ...
                     struct('data',squeeze(TIME_TRACES.nasepa.value(i,is,:))',  'color',COLOR_DENSITIES_DARK,  'display_name',labels_divertor{i}{3}, 'line_style','-'), ...
                     struct('data',squeeze(TIME_TRACES.namxap.value(i,is,:))',  'color',COLOR_DENSITIES_DARK,  'display_name',labels_divertor{i}{4}, 'line_style',':')], ...
                    'OriginalTime', orig_time, ...
                    'OriginalTraces', {get_orig_3d(HAS_AVERAGING, PLOT_ORIGINAL_DATA, TIME_TRACES_ORIGINAL, 'nasepi', i, is), ...
                                       get_orig_3d(HAS_AVERAGING, PLOT_ORIGINAL_DATA, TIME_TRACES_ORIGINAL, 'namxip', i, is), ...
                                       get_orig_3d(HAS_AVERAGING, PLOT_ORIGINAL_DATA, TIME_TRACES_ORIGINAL, 'nasepa', i, is), ...
                                       get_orig_3d(HAS_AVERAGING, PLOT_ORIGINAL_DATA, TIME_TRACES_ORIGINAL, 'namxap', i, is)}, ...
                    'YLabel',sp_ylabel, 'Title',sp_title, tp_common{:});
            end
            is = is+1;

        end

    end

    fprintf('Plot of divertor species densities prepared\n');

end

%% PLOT POLOIDAL FLUXES

if PLOT_POLOIDAL_FLUXES

    for i = 1:ncut

        fig = figure('windowstyle','docked','NumberTitle','off','Name',titles_poloidal_fluxes{i},'Visible',SHOW_FIGURE_status); figs = [figs, fig];

        % Particle fluxes
        subplot('position',[0.08 0.25 0.42 0.5]);
        timeplot(TIME_TRACES.timesa.value, ...
            [struct('data',TIME_TRACES.fnixip.value(i,:), 'color',COLOR_PARTICLE_FLUXES_LIGHT, 'line_style','-', 'display_name',labels_poloidal_fluxes{i}{1}, 'use_abs',true), ...
             struct('data',TIME_TRACES.fnixap.value(i,:), 'color',COLOR_PARTICLE_FLUXES_DARK, 'line_style','-', 'display_name',labels_poloidal_fluxes{i}{2}, 'use_abs',true)], ...
            'OriginalTime', orig_time, ...
            'OriginalTraces', {get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, TIME_TRACES_ORIGINAL, 'fnixip', {i,':'}), ...
                               get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, TIME_TRACES_ORIGINAL, 'fnixap', {i,':'})}, ...
            'YLabel','$\Gamma_{x}$ [s$^{-1}$]', 'Title','Poloidal particle fluxes', tp_common{:});

        % Electron energy fluxes
        subplot('position',[0.57 0.55 0.32 0.38]);
        timeplot(TIME_TRACES.timesa.value, ...
            [struct('data',TIME_TRACES.feexip.value(i,:), 'color',COLOR_ENERGY_FLUXES_LIGHT, 'line_style','-', 'display_name',labels_poloidal_fluxes{i}{1}, 'use_abs',true), ...
             struct('data',TIME_TRACES.feexap.value(i,:), 'color',COLOR_ENERGY_FLUXES_DARK, 'line_style','-', 'display_name',labels_poloidal_fluxes{i}{2}, 'use_abs',true)], ...
            'OriginalTime', orig_time, ...
            'OriginalTraces', {get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, TIME_TRACES_ORIGINAL, 'feexip', {i,':'}), ...
                               get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, TIME_TRACES_ORIGINAL, 'feexap', {i,':'})}, ...
            'YLabel','$Q_{e,x}$ [W]', 'Title','Poloidal electron energy fluxes', ...
            'LabelFontSize',16, 'TitleFontSize',18, tp_common{:});

        % Ion energy fluxes
        subplot('position',[0.57 0.06 0.32 0.38]);
        timeplot(TIME_TRACES.timesa.value, ...
            [struct('data',TIME_TRACES.feixip.value(i,:), 'color',COLOR_ENERGY_FLUXES_LIGHT, 'line_style','-', 'display_name',labels_poloidal_fluxes{i}{1}, 'use_abs',true), ...
             struct('data',TIME_TRACES.feixap.value(i,:), 'color',COLOR_ENERGY_FLUXES_DARK, 'line_style','-', 'display_name',labels_poloidal_fluxes{i}{2}, 'use_abs',true)], ...
            'OriginalTime', orig_time, ...
            'OriginalTraces', {get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, TIME_TRACES_ORIGINAL, 'feixip', {i,':'}), ...
                               get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, TIME_TRACES_ORIGINAL, 'feixap', {i,':'})}, ...
            'YLabel','$Q_{i,x}$ [W]', 'Title','Poloidal ion energy fluxes', ...
            'LabelFontSize',16, 'TitleFontSize',18, tp_common{:});
    
    end

    fprintf('Plot of poloidal fluxes prepared\n');

end

%% PLOT RADIAL FLUXES

if PLOT_RADIAL_FLUXES

    is_limiter = strcmp(SIMULATION.geometry_type,'Limiter');

    for i = 1:ncut

        fig = figure('windowstyle','docked','NumberTitle','off','Name',titles_radial_fluxes{i},'Visible',SHOW_FIGURE_status); figs = [figs, fig];

        % Particle fluxes
        subplot('position',[0.08 0.25 0.42 0.5]);
        tr_part = struct('data',TIME_TRACES.fniyip.value(i,:), 'color',COLOR_PARTICLE_FLUXES_LIGHT, 'line_style','-', 'display_name',labels_radial_fluxes{i}{1}, 'use_abs',true);
        orig_part = {get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, TIME_TRACES_ORIGINAL, 'fniyip', {i,':'})};
        if ~is_limiter
            tr_part(2) = struct('data',TIME_TRACES.fniyap.value(i,:), 'color',COLOR_PARTICLE_FLUXES_DARK, 'line_style','-', 'display_name',labels_radial_fluxes{i}{2}, 'use_abs',true);
            orig_part{2} = get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, TIME_TRACES_ORIGINAL, 'fniyap', {i,':'});
        end
        timeplot(TIME_TRACES.timesa.value, tr_part, 'OriginalTime', orig_time, 'OriginalTraces', orig_part, ...
            'YLabel','[$\Gamma_{y}$ s$^{-1}$]', 'Title','Radial particle fluxes', tp_common{:});

        % Electron energy fluxes
        subplot('position',[0.57 0.55 0.32 0.38]);
        tr_ee = struct('data',TIME_TRACES.feeyip.value(i,:), 'color',COLOR_ENERGY_FLUXES_LIGHT, 'line_style','-', 'display_name',labels_radial_fluxes{i}{1}, 'use_abs',true);
        orig_ee = {get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, TIME_TRACES_ORIGINAL, 'feeyip', {i,':'})};
        if ~is_limiter
            tr_ee(2) = struct('data',TIME_TRACES.feeyap.value(i,:), 'color',COLOR_ENERGY_FLUXES_DARK, 'line_style','-', 'display_name',labels_radial_fluxes{i}{2}, 'use_abs',true);
            orig_ee{2} = get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, TIME_TRACES_ORIGINAL, 'feeyap', {i,':'});
        end
        timeplot(TIME_TRACES.timesa.value, tr_ee, 'OriginalTime', orig_time, 'OriginalTraces', orig_ee, ...
            'YLabel','$Q_{e,y}$ [W]', 'Title','Radial electron energy fluxes', ...
            'LabelFontSize',16, 'TitleFontSize',18, tp_common{:});

        % Ion energy fluxes
        subplot('position',[0.57 0.06 0.32 0.38]);
        tr_ei = struct('data',TIME_TRACES.feiyip.value(i,:), 'color',COLOR_ENERGY_FLUXES_LIGHT, 'line_style','-', 'display_name',labels_radial_fluxes{i}{1}, 'use_abs',true);
        orig_ei = {get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, TIME_TRACES_ORIGINAL, 'feiyip', {i,':'})};
        if ~is_limiter
            tr_ei(2) = struct('data',TIME_TRACES.feiyap.value(i,:), 'color',COLOR_ENERGY_FLUXES_DARK, 'line_style','-', 'display_name',labels_radial_fluxes{i}{2}, 'use_abs',true);
            orig_ei{2} = get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, TIME_TRACES_ORIGINAL, 'feiyap', {i,':'});
        end
        timeplot(TIME_TRACES.timesa.value, tr_ei, 'OriginalTime', orig_time, 'OriginalTraces', orig_ei, ...
            'YLabel','$Q_{i,y}$ [W]', 'Title','Radial ion energy fluxes', ...
            'LabelFontSize',16, 'TitleFontSize',18, tp_common{:});

    end

    fprintf('Plot of radial fluxes prepared\n');

end

%% PLOT INTEGRAL QUANTITIES

if PLOT_INTEGRAL_QUANTITIES

    fig = figure('windowstyle','docked','NumberTitle','off','Name','Integral quantities','Visible',SHOW_FIGURE_status); figs = [figs, fig];

    % Total number of particles
    subplot('position',[0.05 0.25 0.42 0.5]);
    timeplot(TIME_TRACES.timesa.value, ...
        struct('data',TIME_TRACES.tmne.value(1,:), 'color',COLOR_DENSITIES, 'line_style','-', 'display_name',''), ...
        'OriginalTime', orig_time, ...
        'OriginalTraces', {get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, TIME_TRACES_ORIGINAL, 'tmne', {1,':'})}, ...
        'Title','Total number of particles', tp_common{:});

    % Total energy
    subplot('position',[0.53 0.25 0.42 0.5]);
    timeplot(TIME_TRACES.timesa.value, ...
        [struct('data',TIME_TRACES.tmte.value(1,:), 'color',COLOR_TEMPERATURES_LIGHT, 'line_style','-', 'display_name','Electron energy'), ...
         struct('data',TIME_TRACES.tmti.value(1,:), 'color',COLOR_TEMPERATURES_DARK, 'line_style','-',  'display_name','Ion energy')], ...
        'OriginalTime', orig_time, ...
        'OriginalTraces', {get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, TIME_TRACES_ORIGINAL, 'tmte', {1,':'}), ...
                           get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, TIME_TRACES_ORIGINAL, 'tmti', {1,':'})}, ...
        'YLabel','[eV]', 'Title','Total energy', tp_common{:});

    fprintf('Plot of integral quantities prepared\n');

end

%% PRINT THE PLOTS

if PRINT_FIGURE
    print_plot(figs, [FIGURE_WIDTH FIGURE_HEIGHT], 'run_time_traces', FILE_FORMAT, FILE_RESOLUTION);
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

function orig_cells = get_orig(HAS_AVERAGING, PLOT_ORIGINAL_DATA, TIME_TRACES_ORIGINAL, field_name, idx)

% GET_ORIG extracts original data cell array for 2D fields (e.g. value(i,:))

    if HAS_AVERAGING && PLOT_ORIGINAL_DATA && isfield(TIME_TRACES_ORIGINAL, field_name)
        raw = TIME_TRACES_ORIGINAL.(field_name).value;
        if iscell(raw)
            orig_cells = cell(1, length(raw));
            for j = 1:length(raw)
                orig_cells{j} = raw{j}(idx{:});
            end
        else
            orig_cells = {};
        end
    else
        orig_cells = {};
    end
end

function orig_cells = get_orig_3d(HAS_AVERAGING, PLOT_ORIGINAL_DATA, TIME_TRACES_ORIGINAL, field_name, idx1, idx2)

% GET_ORIG_3D extracts original data cell array for 3D fields (e.g. value(i,is,:))

    if HAS_AVERAGING && PLOT_ORIGINAL_DATA && isfield(TIME_TRACES_ORIGINAL, field_name)
        raw = TIME_TRACES_ORIGINAL.(field_name).value;
        if iscell(raw)
            orig_cells = cell(1, length(raw));
            for j = 1:length(raw)
                orig_cells{j} = squeeze(raw{j}(idx1,idx2,:))';
            end
        else
            orig_cells = {};
        end
    else
        orig_cells = {};
    end
end
