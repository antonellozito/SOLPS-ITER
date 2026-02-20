function run_profiles(RUN_DIRECTORY, varargin)

%% SELECT THE SIMULATION

RUN = '';

%% SCRIPT DESCRIPTION

% RUN_PROFILES plots the main radial profiles of the current run
%    (state variables and species densities at inner/outer midplanes
%    and at divertor targets, target load profiles, optionally
%    overlaid with transport coefficients and experimental data),
%    extracted from b2time.nc.
% It can be used both while a simulation is running, to monitor its
%    status, and after the run has stopped.
% The plots are shown grouped in a multi-tab full-window figure.
% Various time-averaging schemes can also be applied to the profiles.
% Can be executed both from the command line, inside one specific run
%    directory, or as an interactive script within the MATLAB GUI,
%    in the last case requiring the manual definition of the
%    run directory of the simulation to be shown

%% USER INPUT

% Select which groups of profiles to plot
PLOT_OUTER_MIDPLANE_PROFILES = true;
PLOT_OUTER_MIDPLANE_SPECIES_PROFILES = false;
PLOT_INNER_MIDPLANE_PROFILES = false;
PLOT_INNER_MIDPLANE_SPECIES_PROFILES = false;
PLOT_OUTER_DIVERTOR_TARGET_PROFILES = true;
PLOT_OUTER_DIVERTOR_TARGET_SPECIES_PROFILES = false;
PLOT_INNER_DIVERTOR_TARGET_PROFILES = true;
PLOT_INNER_DIVERTOR_TARGET_SPECIES_PROFILES = false;
PLOT_TARGET_LOAD_PROFILES = true;

% Select whether to plot transport coefficients
PLOT_TRANSPORT = false;

% Select whether to plot past profiles and the plotting frequency
PLOT_PAST_PROFILES = false;
PLOT_FREQUENCY = 1;

% Select the number of steps for rolling average of the profiles
% (0 for no rolling average)
ROLLING_AVERAGE_STEPS = 0;

% Select the number of steps for batch average of the profiles
% (0 for no batch average)
BATCH_AVERAGE_STEPS = 0;

% Select the radial distance ('dssep' or 'rhop')
RADIAL_DISTANCE = 'dssep';

% Select the scale for profiles and transport coefficients
% ('linear' or 'logarithmic')
SCALE_PROFILES = 'linear';
SCALE_TRANSPORT = 'linear';

% Specify the plot options for profiles
% (colors and colormaps for single/multiple profiles, linewidths, linestyles)
COLOR_DENSITIES = 'blue';
COLOR_TEMPERATURES = 'red';
COLORMAP_DENSITIES = 'turbo';
COLORMAP_TEMPERATURES = 'turbo';
LINEWIDTH_LATEST = 4;
LINEWIDTH_PAST = 0.8;
LINESTYLE_LATEST = '-';
LINESTYLE_PAST = '-';

% Specify the plot options for transport coefficients
COLOR_TRANSPORT = 'green';
LINEWIDTH_TRANSPORT = 2.2;
LINESTYLE_TRANSPORT = '-.';

% Specify the axis limits and styles
XMIN = nan;
XMAX = nan;
YLIM_STYLE = 'custom';

% Select whether to plot the LCFS line
PLOT_LCFS = true;

% Select whether to plot experimental data at midplane and targets
PLOT_EXP_DATA_MIDPLANE = false;
PLOT_EXP_DATA_TARGETS = false;

% Select the types of experimental data plots
% (cell arrays of 'scatter' or 'line'; 'auto' = all 'scatter')
EXP_DATA_MIDPLANE_ELECTRON_DENSITY_TYPES = 'auto';
EXP_DATA_MIDPLANE_ELECTRON_TEMPERATURE_TYPES = 'auto';
EXP_DATA_MIDPLANE_ION_TEMPERATURE_TYPES = 'auto';
EXP_DATA_MIDPLANE_ION_SPECIES_DENSITY_TYPES = 'auto';
EXP_DATA_TARGETS_ELECTRON_DENSITY_TYPES = 'auto';
EXP_DATA_TARGETS_ELECTRON_TEMPERATURE_TYPES = 'auto';
EXP_DATA_TARGETS_PARTICLE_FLUX_DENSITY_TYPES = 'auto';
EXP_DATA_TARGETS_ENERGY_FLUX_DENSITY_TYPES = 'auto';

% Select the colors of experimental data plots
% (cell arrays of color names; 'auto' = auto from 'default' colormap)
EXP_DATA_MIDPLANE_ELECTRON_DENSITY_COLORS = 'auto';
EXP_DATA_MIDPLANE_ELECTRON_TEMPERATURE_COLORS = 'auto';
EXP_DATA_MIDPLANE_ION_TEMPERATURE_COLORS = 'auto';
EXP_DATA_MIDPLANE_ION_SPECIES_DENSITY_COLORS = 'auto';
EXP_DATA_TARGETS_ELECTRON_DENSITY_COLORS = 'auto';
EXP_DATA_TARGETS_ELECTRON_TEMPERATURE_COLORS = 'auto';
EXP_DATA_TARGETS_PARTICLE_FLUX_DENSITY_COLORS = 'auto';
EXP_DATA_TARGETS_ENERGY_FLUX_DENSITY_COLORS = 'auto';

% Specify plot properties for experimental profiles (line) and data (scatter)
EXP_PROFILES_MARKER = '^';
EXP_PROFILES_MARKERSIZE = 12;
EXP_PROFILES_LINEWIDTH = 1.5;
EXP_PROFILES_LINESTYLE = 'none';
EXP_PROFILES_CAPSIZE = 12;
EXP_DATA_MARKER = 'd';
EXP_DATA_MARKERSIZE = 25;

% Specify the size of the figure(s) (in pixels)
FIGURE_WIDTH = 1400;
FIGURE_HEIGHT = 800;

% Select whether to show name of the simulation in the plot(s)
SHOW_NAME = false;

% Select whether to show the figure(s)
SHOW_FIGURE = true;

% Select whether to print the figure(s), and the file format
% ('pdf', 'eps', 'ps', 'png', or 'jpg') alongside with the resolution
% (in the format e.g. 'r600' or 'vector' for vector formats)
PRINT_FIGURE = true;
FILE_FORMAT = 'pdf';
FILE_RESOLUTION = 'vector';

%% END OF USER INPUT

%% DEFINE PARAMETER METADATA

FUNC_NAME = 'run_profiles';

DESCRIPTION = {
    'RUN_PROFILES plots the main radial profiles of the current run'
    '   (state variables and species densities at inner/outer midplanes'
    '   and at divertor targets, target load profiles, optionally'
    '   overlaid with transport coefficients and experimental data),'
    '   extracted from b2time.nc.'
    'It can be used both while a simulation is running, to monitor its'
    '   status, and after the run has stopped.'
    'The plots are shown grouped in a multi-tab full-window figure.'
    'Various time-averaging schemes can also be applied to the profiles.'
    'Can be executed both from the command line, inside one specific run'
    '   directory, or as an interactive script within the MATLAB GUI,'
    '   in the last case requiring the manual definition of the'
    '   run directory of the simulation to be shown'
};

PARAMS = struct('name', {}, 'type', {}, 'default', {}, 'required', {}, 'comment', {}, 'validator', {});

PARAMS(end+1) = struct('name', 'PLOT_OUTER_MIDPLANE_PROFILES', 'type', 'logical', ...
    'default', PLOT_OUTER_MIDPLANE_PROFILES, 'required', false, ...
    'comment', 'Plot state variables at outer midplane', ...
    'validator', @(x) islogical(x) || isnumeric(x));

PARAMS(end+1) = struct('name', 'PLOT_OUTER_MIDPLANE_SPECIES_PROFILES', 'type', 'logical', ...
    'default', PLOT_OUTER_MIDPLANE_SPECIES_PROFILES, 'required', false, ...
    'comment', 'Plot species densities at outer midplane', ...
    'validator', @(x) islogical(x) || isnumeric(x));

PARAMS(end+1) = struct('name', 'PLOT_INNER_MIDPLANE_PROFILES', 'type', 'logical', ...
    'default', PLOT_INNER_MIDPLANE_PROFILES, 'required', false, ...
    'comment', 'Plot state variables at inner midplane', ...
    'validator', @(x) islogical(x) || isnumeric(x));

PARAMS(end+1) = struct('name', 'PLOT_INNER_MIDPLANE_SPECIES_PROFILES', 'type', 'logical', ...
    'default', PLOT_INNER_MIDPLANE_SPECIES_PROFILES, 'required', false, ...
    'comment', 'Plot species densities at inner midplane', ...
    'validator', @(x) islogical(x) || isnumeric(x));

PARAMS(end+1) = struct('name', 'PLOT_OUTER_DIVERTOR_TARGET_PROFILES', 'type', 'logical', ...
    'default', PLOT_OUTER_DIVERTOR_TARGET_PROFILES, 'required', false, ...
    'comment', 'Plot state variables at outer divertor target(s)', ...
    'validator', @(x) islogical(x) || isnumeric(x));

PARAMS(end+1) = struct('name', 'PLOT_OUTER_DIVERTOR_TARGET_SPECIES_PROFILES', 'type', 'logical', ...
    'default', PLOT_OUTER_DIVERTOR_TARGET_SPECIES_PROFILES, 'required', false, ...
    'comment', 'Plot species densities at outer divertor target(s)', ...
    'validator', @(x) islogical(x) || isnumeric(x));

PARAMS(end+1) = struct('name', 'PLOT_INNER_DIVERTOR_TARGET_PROFILES', 'type', 'logical', ...
    'default', PLOT_INNER_DIVERTOR_TARGET_PROFILES, 'required', false, ...
    'comment', 'Plot state variables at inner divertor target(s)', ...
    'validator', @(x) islogical(x) || isnumeric(x));

PARAMS(end+1) = struct('name', 'PLOT_INNER_DIVERTOR_TARGET_SPECIES_PROFILES', 'type', 'logical', ...
    'default', PLOT_INNER_DIVERTOR_TARGET_SPECIES_PROFILES, 'required', false, ...
    'comment', 'Plot species densities at inner divertor target(s)', ...
    'validator', @(x) islogical(x) || isnumeric(x));

PARAMS(end+1) = struct('name', 'PLOT_TARGET_LOAD_PROFILES', 'type', 'logical', ...
    'default', PLOT_TARGET_LOAD_PROFILES, 'required', false, ...
    'comment', 'Plot target load profiles', ...
    'validator', @(x) islogical(x) || isnumeric(x));

PARAMS(end+1) = struct('name', 'PLOT_TRANSPORT', 'type', 'logical', ...
    'default', PLOT_TRANSPORT, 'required', false, ...
    'comment', 'Plot transport coefficients on midplane plots', ...
    'validator', @(x) islogical(x) || isnumeric(x));

PARAMS(end+1) = struct('name', 'PLOT_PAST_PROFILES', 'type', 'logical', ...
    'default', PLOT_PAST_PROFILES, 'required', false, ...
    'comment', 'Plot past profiles', ...
    'validator', @(x) islogical(x) || isnumeric(x));

PARAMS(end+1) = struct('name', 'PLOT_FREQUENCY', 'type', 'numeric', ...
    'default', PLOT_FREQUENCY, 'required', false, ...
    'comment', 'Plot 1 out of every PLOT_FREQUENCY past profiles', ...
    'validator', @isnumeric);

PARAMS(end+1) = struct('name', 'ROLLING_AVERAGE_STEPS', 'type', 'numeric', ...
    'default', ROLLING_AVERAGE_STEPS, 'required', false, ...
    'comment', 'Number of steps for rolling average', ...
    'validator', @isnumeric);

PARAMS(end+1) = struct('name', 'BATCH_AVERAGE_STEPS', 'type', 'numeric', ...
    'default', BATCH_AVERAGE_STEPS, 'required', false, ...
    'comment', 'Number of steps for batch average', ...
    'validator', @isnumeric);

PARAMS(end+1) = struct('name', 'RADIAL_DISTANCE', 'type', 'char', ...
    'default', RADIAL_DISTANCE, 'required', false, ...
    'comment', 'Radial distance type: rho or dssep', ...
    'validator', @ischar);

PARAMS(end+1) = struct('name', 'SCALE_PROFILES', 'type', 'char', ...
    'default', SCALE_PROFILES, 'required', false, ...
    'comment', 'Scale for profile axis: linear or logarithmic', ...
    'validator', @ischar);

PARAMS(end+1) = struct('name', 'SCALE_TRANSPORT', 'type', 'char', ...
    'default', SCALE_TRANSPORT, 'required', false, ...
    'comment', 'Scale for transport axis: linear or logarithmic', ...
    'validator', @ischar);

PARAMS(end+1) = struct('name', 'COLOR_DENSITIES', 'type', 'char', ...
    'default', COLOR_DENSITIES, 'required', false, ...
    'comment', 'Line color for latest density profile', ...
    'validator', @ischar);

PARAMS(end+1) = struct('name', 'COLOR_TEMPERATURES', 'type', 'char', ...
    'default', COLOR_TEMPERATURES, 'required', false, ...
    'comment', 'Line color for latest temperature profile', ...
    'validator', @ischar);

PARAMS(end+1) = struct('name', 'COLORMAP_DENSITIES', 'type', 'char', ...
    'default', COLORMAP_DENSITIES, 'required', false, ...
    'comment', 'Colormap for past density profiles', ...
    'validator', @ischar);

PARAMS(end+1) = struct('name', 'COLORMAP_TEMPERATURES', 'type', 'char', ...
    'default', COLORMAP_TEMPERATURES, 'required', false, ...
    'comment', 'Colormap for past temperature profiles', ...
    'validator', @ischar);

PARAMS(end+1) = struct('name', 'LINEWIDTH_LATEST', 'type', 'numeric', ...
    'default', LINEWIDTH_LATEST, 'required', false, ...
    'comment', 'Line width for the latest profile', ...
    'validator', @isnumeric);

PARAMS(end+1) = struct('name', 'LINEWIDTH_PAST', 'type', 'numeric', ...
    'default', LINEWIDTH_PAST, 'required', false, ...
    'comment', 'Line width for past profiles', ...
    'validator', @isnumeric);

PARAMS(end+1) = struct('name', 'LINESTYLE_LATEST', 'type', 'char', ...
    'default', LINESTYLE_LATEST, 'required', false, ...
    'comment', 'Line style for the latest profile', ...
    'validator', @ischar);

PARAMS(end+1) = struct('name', 'LINESTYLE_PAST', 'type', 'char', ...
    'default', LINESTYLE_PAST, 'required', false, ...
    'comment', 'Line style for past profiles', ...
    'validator', @ischar);

PARAMS(end+1) = struct('name', 'COLOR_TRANSPORT', 'type', 'char', ...
    'default', COLOR_TRANSPORT, 'required', false, ...
    'comment', 'Line color for transport coefficients', ...
    'validator', @ischar);

PARAMS(end+1) = struct('name', 'LINEWIDTH_TRANSPORT', 'type', 'numeric', ...
    'default', LINEWIDTH_TRANSPORT, 'required', false, ...
    'comment', 'Line width for transport coefficients', ...
    'validator', @isnumeric);

PARAMS(end+1) = struct('name', 'LINESTYLE_TRANSPORT', 'type', 'char', ...
    'default', LINESTYLE_TRANSPORT, 'required', false, ...
    'comment', 'Line style for transport coefficients', ...
    'validator', @ischar);

PARAMS(end+1) = struct('name', 'XMIN', 'type', 'numeric', ...
    'default', XMIN, 'required', false, ...
    'comment', 'Minimum x-axis value', ...
    'validator', @isnumeric);

PARAMS(end+1) = struct('name', 'XMAX', 'type', 'numeric', ...
    'default', XMAX, 'required', false, ...
    'comment', 'Maximum x-axis value', ...
    'validator', @isnumeric);

PARAMS(end+1) = struct('name', 'YLIM_STYLE', 'type', 'char', ...
    'default', YLIM_STYLE, 'required', false, ...
    'comment', 'Y-axis limit style: tickaligned, tight, padded, or custom', ...
    'validator', @ischar);

PARAMS(end+1) = struct('name', 'PLOT_LCFS', 'type', 'logical', ...
    'default', PLOT_LCFS, 'required', false, ...
    'comment', 'Plot LCFS line', ...
    'validator', @(x) islogical(x) || isnumeric(x));

PARAMS(end+1) = struct('name', 'PLOT_EXP_DATA_MIDPLANE', 'type', 'logical', ...
    'default', PLOT_EXP_DATA_MIDPLANE, 'required', false, ...
    'comment', 'Plot experimental data at midplane', ...
    'validator', @(x) islogical(x) || isnumeric(x));

PARAMS(end+1) = struct('name', 'PLOT_EXP_DATA_TARGETS', 'type', 'logical', ...
    'default', PLOT_EXP_DATA_TARGETS, 'required', false, ...
    'comment', 'Plot experimental data at targets', ...
    'validator', @(x) islogical(x) || isnumeric(x));

PARAMS(end+1) = struct('name', 'EXP_DATA_MIDPLANE_ELECTRON_DENSITY_TYPES', 'type', 'cell', ...
    'default', {{EXP_DATA_MIDPLANE_ELECTRON_DENSITY_TYPES}}, 'required', false, ...
    'comment', 'Types of exp data plots for midplane ne', ...
    'validator', @(x) iscell(x) || ischar(x));

PARAMS(end+1) = struct('name', 'EXP_DATA_MIDPLANE_ELECTRON_TEMPERATURE_TYPES', 'type', 'cell', ...
    'default', {{EXP_DATA_MIDPLANE_ELECTRON_TEMPERATURE_TYPES}}, 'required', false, ...
    'comment', 'Types of exp data plots for midplane Te', ...
    'validator', @(x) iscell(x) || ischar(x));

PARAMS(end+1) = struct('name', 'EXP_DATA_MIDPLANE_ION_TEMPERATURE_TYPES', 'type', 'cell', ...
    'default', {{EXP_DATA_MIDPLANE_ION_TEMPERATURE_TYPES}}, 'required', false, ...
    'comment', 'Types of exp data plots for midplane Ti', ...
    'validator', @(x) iscell(x) || ischar(x));

PARAMS(end+1) = struct('name', 'EXP_DATA_MIDPLANE_ION_SPECIES_DENSITY_TYPES', 'type', 'cell', ...
    'default', {{EXP_DATA_MIDPLANE_ION_SPECIES_DENSITY_TYPES}}, 'required', false, ...
    'comment', 'Types of exp data plots for midplane species densities', ...
    'validator', @(x) iscell(x) || ischar(x));

PARAMS(end+1) = struct('name', 'EXP_DATA_TARGETS_ELECTRON_DENSITY_TYPES', 'type', 'cell', ...
    'default', {{EXP_DATA_TARGETS_ELECTRON_DENSITY_TYPES}}, 'required', false, ...
    'comment', 'Types of exp data plots for target ne', ...
    'validator', @(x) iscell(x) || ischar(x));

PARAMS(end+1) = struct('name', 'EXP_DATA_TARGETS_ELECTRON_TEMPERATURE_TYPES', 'type', 'cell', ...
    'default', {{EXP_DATA_TARGETS_ELECTRON_TEMPERATURE_TYPES}}, 'required', false, ...
    'comment', 'Types of exp data plots for target Te', ...
    'validator', @(x) iscell(x) || ischar(x));

PARAMS(end+1) = struct('name', 'EXP_DATA_TARGETS_PARTICLE_FLUX_DENSITY_TYPES', 'type', 'cell', ...
    'default', {{EXP_DATA_TARGETS_PARTICLE_FLUX_DENSITY_TYPES}}, 'required', false, ...
    'comment', 'Types of exp data plots for target particle flux density', ...
    'validator', @(x) iscell(x) || ischar(x));

PARAMS(end+1) = struct('name', 'EXP_DATA_TARGETS_ENERGY_FLUX_DENSITY_TYPES', 'type', 'cell', ...
    'default', {{EXP_DATA_TARGETS_ENERGY_FLUX_DENSITY_TYPES}}, 'required', false, ...
    'comment', 'Types of exp data plots for target energy flux density', ...
    'validator', @(x) iscell(x) || ischar(x));

PARAMS(end+1) = struct('name', 'EXP_DATA_MIDPLANE_ELECTRON_DENSITY_COLORS', 'type', 'cell', ...
    'default', {{EXP_DATA_MIDPLANE_ELECTRON_DENSITY_COLORS}}, 'required', false, ...
    'comment', 'Colors for midplane ne exp data', ...
    'validator', @(x) iscell(x) || ischar(x));

PARAMS(end+1) = struct('name', 'EXP_DATA_MIDPLANE_ELECTRON_TEMPERATURE_COLORS', 'type', 'cell', ...
    'default', {{EXP_DATA_MIDPLANE_ELECTRON_TEMPERATURE_COLORS}}, 'required', false, ...
    'comment', 'Colors for midplane Te exp data', ...
    'validator', @(x) iscell(x) || ischar(x));

PARAMS(end+1) = struct('name', 'EXP_DATA_MIDPLANE_ION_TEMPERATURE_COLORS', 'type', 'cell', ...
    'default', {{EXP_DATA_MIDPLANE_ION_TEMPERATURE_COLORS}}, 'required', false, ...
    'comment', 'Colors for midplane Ti exp data', ...
    'validator', @(x) iscell(x) || ischar(x));

PARAMS(end+1) = struct('name', 'EXP_DATA_MIDPLANE_ION_SPECIES_DENSITY_COLORS', 'type', 'cell', ...
    'default', {{EXP_DATA_MIDPLANE_ION_SPECIES_DENSITY_COLORS}}, 'required', false, ...
    'comment', 'Colors for midplane species density exp data', ...
    'validator', @(x) iscell(x) || ischar(x));

PARAMS(end+1) = struct('name', 'EXP_DATA_TARGETS_ELECTRON_DENSITY_COLORS', 'type', 'cell', ...
    'default', {{EXP_DATA_TARGETS_ELECTRON_DENSITY_COLORS}}, 'required', false, ...
    'comment', 'Colors for target ne exp data', ...
    'validator', @(x) iscell(x) || ischar(x));

PARAMS(end+1) = struct('name', 'EXP_DATA_TARGETS_ELECTRON_TEMPERATURE_COLORS', 'type', 'cell', ...
    'default', {{EXP_DATA_TARGETS_ELECTRON_TEMPERATURE_COLORS}}, 'required', false, ...
    'comment', 'Colors for target Te exp data', ...
    'validator', @(x) iscell(x) || ischar(x));

PARAMS(end+1) = struct('name', 'EXP_DATA_TARGETS_PARTICLE_FLUX_DENSITY_COLORS', 'type', 'cell', ...
    'default', {{EXP_DATA_TARGETS_PARTICLE_FLUX_DENSITY_COLORS}}, 'required', false, ...
    'comment', 'Colors for target particle flux density exp data', ...
    'validator', @(x) iscell(x) || ischar(x));

PARAMS(end+1) = struct('name', 'EXP_DATA_TARGETS_ENERGY_FLUX_DENSITY_COLORS', 'type', 'cell', ...
    'default', {{EXP_DATA_TARGETS_ENERGY_FLUX_DENSITY_COLORS}}, 'required', false, ...
    'comment', 'Colors for target energy flux density exp data', ...
    'validator', @(x) iscell(x) || ischar(x));

PARAMS(end+1) = struct('name', 'EXP_PROFILES_MARKER', 'type', 'char', ...
    'default', EXP_PROFILES_MARKER, 'required', false, ...
    'comment', 'Marker for experimental profile lines', ...
    'validator', @ischar);

PARAMS(end+1) = struct('name', 'EXP_PROFILES_MARKERSIZE', 'type', 'numeric', ...
    'default', EXP_PROFILES_MARKERSIZE, 'required', false, ...
    'comment', 'Marker size for experimental profile lines', ...
    'validator', @isnumeric);

PARAMS(end+1) = struct('name', 'EXP_PROFILES_LINEWIDTH', 'type', 'numeric', ...
    'default', EXP_PROFILES_LINEWIDTH, 'required', false, ...
    'comment', 'Line width for experimental profile lines', ...
    'validator', @isnumeric);

PARAMS(end+1) = struct('name', 'EXP_PROFILES_LINESTYLE', 'type', 'char', ...
    'default', EXP_PROFILES_LINESTYLE, 'required', false, ...
    'comment', 'Line style for experimental profile lines', ...
    'validator', @ischar);

PARAMS(end+1) = struct('name', 'EXP_PROFILES_CAPSIZE', 'type', 'numeric', ...
    'default', EXP_PROFILES_CAPSIZE, 'required', false, ...
    'comment', 'Cap size for experimental profile errorbars', ...
    'validator', @isnumeric);

PARAMS(end+1) = struct('name', 'EXP_DATA_MARKER', 'type', 'char', ...
    'default', EXP_DATA_MARKER, 'required', false, ...
    'comment', 'Marker for experimental scatter data', ...
    'validator', @ischar);

PARAMS(end+1) = struct('name', 'EXP_DATA_MARKERSIZE', 'type', 'numeric', ...
    'default', EXP_DATA_MARKERSIZE, 'required', false, ...
    'comment', 'Marker size for experimental scatter data', ...
    'validator', @isnumeric);

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
[PLOT_OUTER_MIDPLANE_PROFILES, PLOT_OUTER_MIDPLANE_SPECIES_PROFILES, ...
 PLOT_INNER_MIDPLANE_PROFILES, PLOT_INNER_MIDPLANE_SPECIES_PROFILES, ...
 PLOT_OUTER_DIVERTOR_TARGET_PROFILES, PLOT_OUTER_DIVERTOR_TARGET_SPECIES_PROFILES, ...
 PLOT_INNER_DIVERTOR_TARGET_PROFILES, PLOT_INNER_DIVERTOR_TARGET_SPECIES_PROFILES, ...
 PLOT_TARGET_LOAD_PROFILES, PLOT_TRANSPORT, PLOT_PAST_PROFILES, PLOT_FREQUENCY, ...
 ROLLING_AVERAGE_STEPS, BATCH_AVERAGE_STEPS, RADIAL_DISTANCE, ...
 SCALE_PROFILES, SCALE_TRANSPORT, ...
 COLOR_DENSITIES, COLOR_TEMPERATURES, COLORMAP_DENSITIES, COLORMAP_TEMPERATURES, ...
 LINEWIDTH_LATEST, LINEWIDTH_PAST, LINESTYLE_LATEST, LINESTYLE_PAST, ...
 COLOR_TRANSPORT, LINEWIDTH_TRANSPORT, LINESTYLE_TRANSPORT, ...
 XMIN, XMAX, YLIM_STYLE, PLOT_LCFS, ...
 PLOT_EXP_DATA_MIDPLANE, PLOT_EXP_DATA_TARGETS, ...
 EXP_DATA_MIDPLANE_ELECTRON_DENSITY_TYPES, EXP_DATA_MIDPLANE_ELECTRON_TEMPERATURE_TYPES, ...
 EXP_DATA_MIDPLANE_ION_TEMPERATURE_TYPES, EXP_DATA_MIDPLANE_ION_SPECIES_DENSITY_TYPES, ...
 EXP_DATA_TARGETS_ELECTRON_DENSITY_TYPES, EXP_DATA_TARGETS_ELECTRON_TEMPERATURE_TYPES, ...
 EXP_DATA_TARGETS_PARTICLE_FLUX_DENSITY_TYPES, EXP_DATA_TARGETS_ENERGY_FLUX_DENSITY_TYPES, ...
 EXP_DATA_MIDPLANE_ELECTRON_DENSITY_COLORS, EXP_DATA_MIDPLANE_ELECTRON_TEMPERATURE_COLORS, ...
 EXP_DATA_MIDPLANE_ION_TEMPERATURE_COLORS, EXP_DATA_MIDPLANE_ION_SPECIES_DENSITY_COLORS, ...
 EXP_DATA_TARGETS_ELECTRON_DENSITY_COLORS, EXP_DATA_TARGETS_ELECTRON_TEMPERATURE_COLORS, ...
 EXP_DATA_TARGETS_PARTICLE_FLUX_DENSITY_COLORS, EXP_DATA_TARGETS_ENERGY_FLUX_DENSITY_COLORS, ...
 EXP_PROFILES_MARKER, EXP_PROFILES_MARKERSIZE, EXP_PROFILES_LINEWIDTH, ...
 EXP_PROFILES_LINESTYLE, EXP_PROFILES_CAPSIZE, EXP_DATA_MARKER, EXP_DATA_MARKERSIZE, ...
 FIGURE_WIDTH, FIGURE_HEIGHT, SHOW_NAME, SHOW_FIGURE, PRINT_FIGURE, FILE_FORMAT, FILE_RESOLUTION] = ...
    extract_params(p.Results, PARAMS);

% Unwrap double-wrapped cell arrays (from {{}} struct default workaround)
EXP_DATA_MIDPLANE_ELECTRON_DENSITY_TYPES = unwrap_cell(EXP_DATA_MIDPLANE_ELECTRON_DENSITY_TYPES);
EXP_DATA_MIDPLANE_ELECTRON_TEMPERATURE_TYPES = unwrap_cell(EXP_DATA_MIDPLANE_ELECTRON_TEMPERATURE_TYPES);
EXP_DATA_MIDPLANE_ION_TEMPERATURE_TYPES = unwrap_cell(EXP_DATA_MIDPLANE_ION_TEMPERATURE_TYPES);
EXP_DATA_MIDPLANE_ION_SPECIES_DENSITY_TYPES = unwrap_cell(EXP_DATA_MIDPLANE_ION_SPECIES_DENSITY_TYPES);
EXP_DATA_TARGETS_ELECTRON_DENSITY_TYPES = unwrap_cell(EXP_DATA_TARGETS_ELECTRON_DENSITY_TYPES);
EXP_DATA_TARGETS_ELECTRON_TEMPERATURE_TYPES = unwrap_cell(EXP_DATA_TARGETS_ELECTRON_TEMPERATURE_TYPES);
EXP_DATA_TARGETS_PARTICLE_FLUX_DENSITY_TYPES = unwrap_cell(EXP_DATA_TARGETS_PARTICLE_FLUX_DENSITY_TYPES);
EXP_DATA_TARGETS_ENERGY_FLUX_DENSITY_TYPES = unwrap_cell(EXP_DATA_TARGETS_ENERGY_FLUX_DENSITY_TYPES);
EXP_DATA_MIDPLANE_ELECTRON_DENSITY_COLORS = unwrap_cell(EXP_DATA_MIDPLANE_ELECTRON_DENSITY_COLORS);
EXP_DATA_MIDPLANE_ELECTRON_TEMPERATURE_COLORS = unwrap_cell(EXP_DATA_MIDPLANE_ELECTRON_TEMPERATURE_COLORS);
EXP_DATA_MIDPLANE_ION_TEMPERATURE_COLORS = unwrap_cell(EXP_DATA_MIDPLANE_ION_TEMPERATURE_COLORS);
EXP_DATA_MIDPLANE_ION_SPECIES_DENSITY_COLORS = unwrap_cell(EXP_DATA_MIDPLANE_ION_SPECIES_DENSITY_COLORS);
EXP_DATA_TARGETS_ELECTRON_DENSITY_COLORS = unwrap_cell(EXP_DATA_TARGETS_ELECTRON_DENSITY_COLORS);
EXP_DATA_TARGETS_ELECTRON_TEMPERATURE_COLORS = unwrap_cell(EXP_DATA_TARGETS_ELECTRON_TEMPERATURE_COLORS);
EXP_DATA_TARGETS_PARTICLE_FLUX_DENSITY_COLORS = unwrap_cell(EXP_DATA_TARGETS_PARTICLE_FLUX_DENSITY_COLORS);
EXP_DATA_TARGETS_ENERGY_FLUX_DENSITY_COLORS = unwrap_cell(EXP_DATA_TARGETS_ENERGY_FLUX_DENSITY_COLORS);

% Convert 'auto' sentinel values back to empty cell arrays
EXP_DATA_MIDPLANE_ELECTRON_DENSITY_TYPES = auto_to_empty(EXP_DATA_MIDPLANE_ELECTRON_DENSITY_TYPES);
EXP_DATA_MIDPLANE_ELECTRON_TEMPERATURE_TYPES = auto_to_empty(EXP_DATA_MIDPLANE_ELECTRON_TEMPERATURE_TYPES);
EXP_DATA_MIDPLANE_ION_TEMPERATURE_TYPES = auto_to_empty(EXP_DATA_MIDPLANE_ION_TEMPERATURE_TYPES);
EXP_DATA_MIDPLANE_ION_SPECIES_DENSITY_TYPES = auto_to_empty(EXP_DATA_MIDPLANE_ION_SPECIES_DENSITY_TYPES);
EXP_DATA_TARGETS_ELECTRON_DENSITY_TYPES = auto_to_empty(EXP_DATA_TARGETS_ELECTRON_DENSITY_TYPES);
EXP_DATA_TARGETS_ELECTRON_TEMPERATURE_TYPES = auto_to_empty(EXP_DATA_TARGETS_ELECTRON_TEMPERATURE_TYPES);
EXP_DATA_TARGETS_PARTICLE_FLUX_DENSITY_TYPES = auto_to_empty(EXP_DATA_TARGETS_PARTICLE_FLUX_DENSITY_TYPES);
EXP_DATA_TARGETS_ENERGY_FLUX_DENSITY_TYPES = auto_to_empty(EXP_DATA_TARGETS_ENERGY_FLUX_DENSITY_TYPES);
EXP_DATA_MIDPLANE_ELECTRON_DENSITY_COLORS = auto_to_empty(EXP_DATA_MIDPLANE_ELECTRON_DENSITY_COLORS);
EXP_DATA_MIDPLANE_ELECTRON_TEMPERATURE_COLORS = auto_to_empty(EXP_DATA_MIDPLANE_ELECTRON_TEMPERATURE_COLORS);
EXP_DATA_MIDPLANE_ION_TEMPERATURE_COLORS = auto_to_empty(EXP_DATA_MIDPLANE_ION_TEMPERATURE_COLORS);
EXP_DATA_MIDPLANE_ION_SPECIES_DENSITY_COLORS = auto_to_empty(EXP_DATA_MIDPLANE_ION_SPECIES_DENSITY_COLORS);
EXP_DATA_TARGETS_ELECTRON_DENSITY_COLORS = auto_to_empty(EXP_DATA_TARGETS_ELECTRON_DENSITY_COLORS);
EXP_DATA_TARGETS_ELECTRON_TEMPERATURE_COLORS = auto_to_empty(EXP_DATA_TARGETS_ELECTRON_TEMPERATURE_COLORS);
EXP_DATA_TARGETS_PARTICLE_FLUX_DENSITY_COLORS = auto_to_empty(EXP_DATA_TARGETS_PARTICLE_FLUX_DENSITY_COLORS);
EXP_DATA_TARGETS_ENERGY_FLUX_DENSITY_COLORS = auto_to_empty(EXP_DATA_TARGETS_ENERGY_FLUX_DENSITY_COLORS);

%% SANITY CHECK OF USER INPUTS

% Variables which should be logicals
logicals_selection = {'PLOT_OUTER_MIDPLANE_PROFILES'
                      'PLOT_OUTER_MIDPLANE_SPECIES_PROFILES'
                      'PLOT_INNER_MIDPLANE_PROFILES'
                      'PLOT_INNER_MIDPLANE_SPECIES_PROFILES'
                      'PLOT_OUTER_DIVERTOR_TARGET_PROFILES'
                      'PLOT_OUTER_DIVERTOR_TARGET_SPECIES_PROFILES'
                      'PLOT_INNER_DIVERTOR_TARGET_PROFILES'
                      'PLOT_INNER_DIVERTOR_TARGET_SPECIES_PROFILES'
                      'PLOT_TARGET_LOAD_PROFILES'
                      'PLOT_TRANSPORT'
                      'PLOT_PAST_PROFILES'
                      'PLOT_LCFS'
                      'PLOT_EXP_DATA_MIDPLANE'
                      'PLOT_EXP_DATA_TARGETS'
                      'SHOW_NAME'
                      'SHOW_FIGURE'
                      'PRINT_FIGURE'};
check_vars(logicals_selection, 'logical');

% Variables which should be numbers
numbers_selection = {'PLOT_FREQUENCY'
                     'ROLLING_AVERAGE_STEPS'
                     'BATCH_AVERAGE_STEPS'
                     'LINEWIDTH_LATEST'
                     'LINEWIDTH_PAST'
                     'LINEWIDTH_TRANSPORT'
                     'XMIN'
                     'XMAX'
                     'EXP_PROFILES_MARKERSIZE'
                     'EXP_PROFILES_LINEWIDTH'
                     'EXP_PROFILES_CAPSIZE'
                     'EXP_DATA_MARKERSIZE'
                     'FIGURE_WIDTH'
                     'FIGURE_HEIGHT'};
check_vars(numbers_selection, 'number');

% Variables which should be strings
strings_selection = {'RADIAL_DISTANCE'
                     'SCALE_PROFILES'
                     'SCALE_TRANSPORT'
                     'COLOR_DENSITIES'
                     'COLOR_TEMPERATURES'
                     'COLORMAP_DENSITIES'
                     'COLORMAP_TEMPERATURES'
                     'COLOR_TRANSPORT'
                     'LINESTYLE_LATEST'
                     'LINESTYLE_PAST'
                     'LINESTYLE_TRANSPORT'
                     'YLIM_STYLE'
                     'EXP_PROFILES_MARKER'
                     'EXP_PROFILES_LINESTYLE'
                     'EXP_DATA_MARKER'
                     'FILE_FORMAT'
                     'FILE_RESOLUTION'};
check_vars(strings_selection, 'string');

% Only one averaging scheme can be used
if ROLLING_AVERAGE_STEPS > 0 && BATCH_AVERAGE_STEPS > 0
    error('Error: At most one of ROLLING_AVERAGE_STEPS and BATCH_AVERAGE_STEPS can be nonzero');
end

if ~isnan(XMIN) && ~isnan(XMAX)
    if XMIN >= XMAX
        error('Error: XMIN cannot be larger or equal than XMAX');
    end
end

% Check available styles of Y-limits
if ~ismember(YLIM_STYLE, {'tickaligned','tight','padded','custom'})
    error('Error: YLIM_STYLE can only be ''tickaligned'', ''tight'', ''padded'' or ''custom''');
end

% Check available radial distance types
if ~ismember(RADIAL_DISTANCE, {'rhop','dssep'})
    error('Error: RADIAL_DISTANCE can only be ''rhop'' or ''dssep''');
end

% Check available scale types
if ~ismember(SCALE_PROFILES, {'linear','logarithmic'})
    error('Error: SCALE_PROFILES can only be ''linear'' or ''logarithmic''');
end
if ~ismember(SCALE_TRANSPORT, {'linear','logarithmic'})
    error('Error: SCALE_TRANSPORT can only be ''linear'' or ''logarithmic''');
end

% Check available groups of colors
valid_colors = {'blue','red','yellow','purple','green','cyan','magenta','black'};
color_vars = {'COLOR_DENSITIES','COLOR_TEMPERATURES','COLOR_TRANSPORT'};
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

GEOMETRY = read_b2fgmtry(SIMULATION);
if strcmp(RADIAL_DISTANCE,'rhop')
    EQUILIBRIUM = read_equilibrium(SIMULATION);
end
PROFILES = read_b2time(SIMULATION,'PROFILES');

%% READ SPECIES

if PLOT_OUTER_MIDPLANE_SPECIES_PROFILES || PLOT_INNER_MIDPLANE_SPECIES_PROFILES || ...
        PLOT_OUTER_DIVERTOR_TARGET_SPECIES_PROFILES || PLOT_INNER_DIVERTOR_TARGET_SPECIES_PROFILES
    [species_label,atomic_number,charge_state] = read_species(SIMULATION);
end

%% APPLY AVERAGING SCHEMES

% Rolling average
if ROLLING_AVERAGE_STEPS > 0
    time_step = PROFILES.timesa.value(2) - PROFILES.timesa.value(1);
    fields = fieldnames(PROFILES);
    for i = 1:numel(fields)
        f = fields{i};
        if ~ismember(f, {'timesa'})
            PROFILES.(f).value = rolling_average(PROFILES.(f).value,ROLLING_AVERAGE_STEPS,'b2time');
        end
    end
    fprintf('Rolling average of the profiles computed over a period of %d time steps (%.1e s)\n',...
        ROLLING_AVERAGE_STEPS,ROLLING_AVERAGE_STEPS*time_step)
end

% Batch average
if BATCH_AVERAGE_STEPS > 0
    time_step = PROFILES.timesa.value(2) - PROFILES.timesa.value(1);
    fields = fieldnames(PROFILES);
    for i = 1:numel(fields)
        f = fields{i};
        if ~ismember(f, {'timesa'})
            PROFILES.(f).value = batch_average(PROFILES.(f).value,BATCH_AVERAGE_STEPS,'b2time');
        else
            PROFILES.timesa.value = batch_average(PROFILES.timesa.value,BATCH_AVERAGE_STEPS,'time');
        end
    end
    fprintf('Batch average of the profiles computed over a period of %d time steps (%.1e s)\n',...
        BATCH_AVERAGE_STEPS,BATCH_AVERAGE_STEPS*time_step)
end

%% DETERMINE GEOMETRY TYPE AND TARGET CONFIGURATION

is_limiter = strcmp(SIMULATION.geometry_type,'Limiter');
is_lsn = contains(SIMULATION.geometry_type,'Lower single null');
is_usn = contains(SIMULATION.geometry_type,'Upper single null');
is_sn = is_lsn || is_usn;
is_cdn = strcmp(SIMULATION.geometry_type,'Connected double null');
is_ddn = strcmp(SIMULATION.geometry_type,'Disconnected double null');
is_dn = is_cdn || is_ddn;
is_lsf = strcmp(SIMULATION.geometry_type,'Lower LFS snowflake');
is_usf = strcmp(SIMULATION.geometry_type,'Upper LFS snowflake');
is_sf = is_lsf || is_usf;
has_additional_targets = is_dn || is_sf;

%% CALCULATE COORDINATES

switch RADIAL_DISTANCE

    case 'rhop'

        x_OMP = calc_rhop(GEOMETRY,EQUILIBRIUM,'outer_midplane');
        x_IMP = calc_rhop(GEOMETRY,EQUILIBRIUM,'inner_midplane');
        if is_limiter || is_lsn || is_usn
            x_IT = calc_rhop(GEOMETRY,EQUILIBRIUM,'inner_target');
            x_OT = calc_rhop(GEOMETRY,EQUILIBRIUM,'outer_target');
        elseif is_dn
            x_IT_bottom = calc_rhop(GEOMETRY,EQUILIBRIUM,'lower_inner_target');
            x_OT_bottom = calc_rhop(GEOMETRY,EQUILIBRIUM,'lower_outer_target');
            x_IT_top = calc_rhop(GEOMETRY,EQUILIBRIUM,'upper_inner_target');
            x_OT_top = calc_rhop(GEOMETRY,EQUILIBRIUM,'upper_inner_target');
        elseif is_sf
            x_IT_primary = calc_rhop(GEOMETRY,EQUILIBRIUM,'inner_target');
            x_OT_primary = calc_rhop(GEOMETRY,EQUILIBRIUM,'primary_outer_target');
            x_OT_farSOL = calc_rhop(GEOMETRY,EQUILIBRIUM,'far_SOL_outer_target');
            x_OT_secondary = calc_rhop(GEOMETRY,EQUILIBRIUM,'secondary_outer_target');
        end

    case 'dssep'

        x_OMP = GEOMETRY.dsa;
        x_IMP = GEOMETRY.dsi;
        if is_limiter || is_lsn
            x_IT = GEOMETRY.dsl;
            x_OT = GEOMETRY.dsr;
        elseif is_usn
            x_IT = GEOMETRY.dsr;
            x_OT = GEOMETRY.dsl;
        elseif is_dn
            x_IT_bottom = GEOMETRY.dsl;
            x_OT_bottom = GEOMETRY.dsr;
            x_IT_top = GEOMETRY.dstl;
            x_OT_top = GEOMETRY.dstr;
        elseif is_sf
            x_IT_primary = GEOMETRY.dsl;
            x_OT_primary = GEOMETRY.dsr;
            x_OT_farSOL = GEOMETRY.dstl;
            x_OT_secondary = GEOMETRY.dstr;
        end

end

%% CALCULATE NORMAL AREAS

normal_area_r = GEOMETRY.dsRT;
normal_area_l = GEOMETRY.dsLT;

if has_additional_targets
    normal_area_tl = GEOMETRY.dsTLT;
    normal_area_tr = GEOMETRY.dsTRT;
end

%% TRIM COORDINATES AND NORMAL AREAS IF NEEDED

% Determine reference field and coordinate for trimming
if is_limiter || is_lsn
    ref_field_size = size(PROFILES.ne3dr.value,1);
    ref_coord_len = length(x_OT);
elseif is_usn
    ref_field_size = size(PROFILES.ne3dl.value,1);
    ref_coord_len = length(x_OT);
elseif is_dn
    ref_field_size = size(PROFILES.ne3dr.value,1);
    ref_coord_len = length(x_OT_bottom);
elseif is_sf
    ref_field_size = size(PROFILES.ne3dr.value,1);
    ref_coord_len = length(x_OT_primary);
end

if ref_field_size == ref_coord_len - 2
    if is_limiter || is_lsn || is_usn
        x_IT = x_IT(2:end-1);
        x_OT = x_OT(2:end-1);
    elseif is_dn
        x_IT_bottom = x_IT_bottom(2:end-1);
        x_OT_bottom = x_OT_bottom(2:end-1);
        x_IT_top = x_IT_top(2:end-1);
        x_OT_top = x_OT_top(2:end-1);
    elseif is_sf
        x_IT_primary = x_IT_primary(2:end-1);
        x_OT_primary = x_OT_primary(2:end-1);
        x_OT_farSOL = x_OT_farSOL(2:end-1);
        x_OT_secondary = x_OT_secondary(2:end-1);
    end
    normal_area_r = normal_area_r(2:end-1);
    normal_area_l = normal_area_l(2:end-1);
    if has_additional_targets
        normal_area_tl = normal_area_tl(2:end-1);
        normal_area_tr = normal_area_tr(2:end-1);
    end
end

%% SET RADIAL LABEL AND LCFS POSITION

switch RADIAL_DISTANCE
    case 'rhop'
        RADIAL_LABEL = '$\rho_{p}$';
        LCFS_POSITION = 1;
    case 'dssep'
        RADIAL_LABEL = '$R-R_{sep}$ [m]';
        LCFS_POSITION = 0;
end

%% EXTRACT TRANSPORT COEFFICIENTS

if PLOT_TRANSPORT
    dna0_outer = PROFILES.dn3da.value(:,:,end);
    dna0_inner = PROFILES.dn3di.value(:,:,end);
    hce0_outer = PROFILES.ke3da.value(:,end);
    hce0_inner = PROFILES.ke3di.value(:,end);
    hci0_outer = PROFILES.ki3da.value(:,end);
    hci0_inner = PROFILES.ki3di.value(:,end);
end

%% READ EXPERIMENTAL DATA - MIDPLANE

measurements_midplane_experiment = struct();
measurements_targets_experiment = struct();

if (PLOT_OUTER_MIDPLANE_PROFILES || PLOT_INNER_MIDPLANE_PROFILES) && PLOT_EXP_DATA_MIDPLANE
    [measurements_midplane_experiment,exp_data_midplane_avail] = read_measurements_midplane_experiment(SIMULATION);
    if ~exp_data_midplane_avail
        PLOT_EXP_DATA_MIDPLANE = false;
    end
end

%% READ EXPERIMENTAL DATA - TARGETS

if (PLOT_OUTER_DIVERTOR_TARGET_PROFILES || PLOT_INNER_DIVERTOR_TARGET_PROFILES || PLOT_TARGET_LOAD_PROFILES) && PLOT_EXP_DATA_TARGETS
    [measurements_targets_experiment,exp_data_target_avail] = read_measurements_targets_experiment(SIMULATION);
    if ~exp_data_target_avail
        PLOT_EXP_DATA_TARGETS = false;
    end
end

%% SANITY CHECK OF EXPERIMENTAL DATA TYPES LENGTHS

if PLOT_EXP_DATA_MIDPLANE
    check_exp_types_length(EXP_DATA_MIDPLANE_ELECTRON_DENSITY_TYPES, measurements_midplane_experiment, {'outer','inner'}, 'ne_data', 'EXP_DATA_MIDPLANE_ELECTRON_DENSITY_TYPES');
    check_exp_types_length(EXP_DATA_MIDPLANE_ELECTRON_TEMPERATURE_TYPES, measurements_midplane_experiment, {'outer','inner'}, 'Te_data', 'EXP_DATA_MIDPLANE_ELECTRON_TEMPERATURE_TYPES');
    check_exp_types_length(EXP_DATA_MIDPLANE_ION_TEMPERATURE_TYPES, measurements_midplane_experiment, {'outer','inner'}, 'Ti_data', 'EXP_DATA_MIDPLANE_ION_TEMPERATURE_TYPES');
end

if PLOT_EXP_DATA_TARGETS
    if is_usn
        tgt_sides = {'upper_outer','upper_inner'};
    elseif is_dn
        tgt_sides = {'lower_outer','lower_inner','upper_outer','upper_inner'};
    else
        tgt_sides = {'lower_outer','lower_inner'};
    end
    check_exp_types_length(EXP_DATA_TARGETS_ELECTRON_DENSITY_TYPES, measurements_targets_experiment, tgt_sides, 'ne_data', 'EXP_DATA_TARGETS_ELECTRON_DENSITY_TYPES');
    check_exp_types_length(EXP_DATA_TARGETS_ELECTRON_TEMPERATURE_TYPES, measurements_targets_experiment, tgt_sides, 'Te_data', 'EXP_DATA_TARGETS_ELECTRON_TEMPERATURE_TYPES');
    check_exp_types_length(EXP_DATA_TARGETS_PARTICLE_FLUX_DENSITY_TYPES, measurements_targets_experiment, tgt_sides, 'gamma_data', 'EXP_DATA_TARGETS_PARTICLE_FLUX_DENSITY_TYPES');
    check_exp_types_length(EXP_DATA_TARGETS_ENERGY_FLUX_DENSITY_TYPES, measurements_targets_experiment, tgt_sides, 'q_data', 'EXP_DATA_TARGETS_ENERGY_FLUX_DENSITY_TYPES');
end

%% INITIALIZE FIGURES

figs = [];

if SHOW_FIGURE
    SHOW_FIGURE_status = 'on';
else
    SHOW_FIGURE_status = 'off';
end

%% LOAD COLORS

% Profile colors (latest profile)
COLORS_MAP = load_colors('default',7,'rgb');
COLORS_MAP{8} = [0, 0, 0];
color_name_to_index = containers.Map({'blue','red','yellow','purple','green','cyan','magenta','black'},{1,2,3,4,5,6,7,8});

COLOR_DENSITIES_RGB = COLORS_MAP{color_name_to_index(COLOR_DENSITIES)};
COLOR_TEMPERATURES_RGB = COLORS_MAP{color_name_to_index(COLOR_TEMPERATURES)};
COLOR_TRANSPORT_RGB = COLORS_MAP{color_name_to_index(COLOR_TRANSPORT)};

% Past profile colors (from colormaps)
nsnaps = length(PROFILES.timesa.value);
ncolors = ceil(nsnaps / PLOT_FREQUENCY);
if ncolors > 50
    PLOT_FREQUENCY = ceil(nsnaps / 50);
    ncolors = ceil(nsnaps / PLOT_FREQUENCY);
end
nsnaps_plotted = numel(1:PLOT_FREQUENCY:nsnaps);
time_step_plot = PROFILES.timesa.value(2) - PROFILES.timesa.value(1);
effective_time_step_plot = PLOT_FREQUENCY * time_step_plot;
PAST_COLORS_DENSITIES = load_colors(COLORMAP_DENSITIES, ncolors, 'rgb');
PAST_COLORS_TEMPERATURES = load_colors(COLORMAP_TEMPERATURES, ncolors, 'rgb');

% Add transparency to past colors
for i = 1:length(PAST_COLORS_DENSITIES)
    PAST_COLORS_DENSITIES{i}(4) = 0.5;
end
for i = 1:length(PAST_COLORS_TEMPERATURES)
    PAST_COLORS_TEMPERATURES{i}(4) = 0.5;
end

% If experimental data are plotted, reduce past profile opacity further
if PLOT_EXP_DATA_MIDPLANE || PLOT_EXP_DATA_TARGETS
    for i = 1:length(PAST_COLORS_DENSITIES)
        PAST_COLORS_DENSITIES{i}(4) = 0.2;
    end
    for i = 1:length(PAST_COLORS_TEMPERATURES)
        PAST_COLORS_TEMPERATURES{i}(4) = 0.2;
    end
end

% Resolve experimental data colors from names to RGB
EXP_DATA_MIDPLANE_ELECTRON_DENSITY_COLORS = resolve_exp_colors(EXP_DATA_MIDPLANE_ELECTRON_DENSITY_COLORS, COLORS_MAP, color_name_to_index);
EXP_DATA_MIDPLANE_ELECTRON_TEMPERATURE_COLORS = resolve_exp_colors(EXP_DATA_MIDPLANE_ELECTRON_TEMPERATURE_COLORS, COLORS_MAP, color_name_to_index);
EXP_DATA_MIDPLANE_ION_TEMPERATURE_COLORS = resolve_exp_colors(EXP_DATA_MIDPLANE_ION_TEMPERATURE_COLORS, COLORS_MAP, color_name_to_index);
EXP_DATA_MIDPLANE_ION_SPECIES_DENSITY_COLORS = resolve_exp_colors(EXP_DATA_MIDPLANE_ION_SPECIES_DENSITY_COLORS, COLORS_MAP, color_name_to_index);
EXP_DATA_TARGETS_ELECTRON_DENSITY_COLORS = resolve_exp_colors(EXP_DATA_TARGETS_ELECTRON_DENSITY_COLORS, COLORS_MAP, color_name_to_index);
EXP_DATA_TARGETS_ELECTRON_TEMPERATURE_COLORS = resolve_exp_colors(EXP_DATA_TARGETS_ELECTRON_TEMPERATURE_COLORS, COLORS_MAP, color_name_to_index);
EXP_DATA_TARGETS_PARTICLE_FLUX_DENSITY_COLORS = resolve_exp_colors(EXP_DATA_TARGETS_PARTICLE_FLUX_DENSITY_COLORS, COLORS_MAP, color_name_to_index);
EXP_DATA_TARGETS_ENERGY_FLUX_DENSITY_COLORS = resolve_exp_colors(EXP_DATA_TARGETS_ENERGY_FLUX_DENSITY_COLORS, COLORS_MAP, color_name_to_index);

%% COMMON PROPERTIES FOR ALL PROFILEPLOT CALLS

pp_common = {'XMIN', XMIN, 'XMAX', XMAX, 'YLimStyle', YLIM_STYLE, ...
             'PlotLCFS', PLOT_LCFS, 'LCFSPosition', LCFS_POSITION, ...
             'ScaleProfiles', SCALE_PROFILES, ...
             'ShowName', SHOW_NAME, 'RunName', RUN};

pp_past = {'PastLineWidth', LINEWIDTH_PAST, 'PastLineStyle', LINESTYLE_PAST, ...
           'PlotFrequency', PLOT_FREQUENCY};

pp_transport = {'TransportLineWidth', LINEWIDTH_TRANSPORT, ...
                'TransportLineStyle', LINESTYLE_TRANSPORT, ...
                'TransportColor', COLOR_TRANSPORT_RGB, ...
                'ScaleTransport', SCALE_TRANSPORT};

pp_exp = {'ExpMarker', EXP_DATA_MARKER, 'ExpMarkerSize', EXP_DATA_MARKERSIZE, ...
          'ExpProfilesMarker', EXP_PROFILES_MARKER, 'ExpProfilesMarkerSize', EXP_PROFILES_MARKERSIZE, ...
          'ExpProfilesLineWidth', EXP_PROFILES_LINEWIDTH, 'ExpProfilesLineStyle', EXP_PROFILES_LINESTYLE, ...
          'ExpProfilesCapSize', EXP_PROFILES_CAPSIZE};

pp_latest_ne = {'ProfileColor', COLOR_DENSITIES_RGB, 'ProfileLineWidth', LINEWIDTH_LATEST, 'ProfileLineStyle', LINESTYLE_LATEST};
pp_latest_te = {'ProfileColor', COLOR_TEMPERATURES_RGB, 'ProfileLineWidth', LINEWIDTH_LATEST, 'ProfileLineStyle', LINESTYLE_LATEST};

%% DEFINE TITLES DEPENDING ON GEOMETRY

if is_limiter
    title_outer_midplane = 'Outer midpoint profiles';
    title_inner_midplane = 'Inner midpoint profiles';
    title_outer_midplane_species = 'Outer midpoint species densities';
    title_inner_midplane_species = 'Inner midpoint species densities';
elseif is_sn || is_dn || is_sf
    title_outer_midplane = 'Outer midplane profiles';
    title_inner_midplane = 'Inner midplane profiles';
    title_outer_midplane_species = 'Outer midplane species densities';
    title_inner_midplane_species = 'Inner midplane species densities';
end

%% DEFINE TARGET CONFIGURATIONS

% Each target entry: struct with fields:
%   x_coord, suffix, normal_area, title_state, title_species, title_load_ne/Te, exp_side
% suffix is appended to field base names (ne3d, te3d, ti3d, na3d, dab3d, fo3d, ft3d)

if is_limiter
    outer_targets = struct('x',x_OT, 'sfx','r', 'na',normal_area_r, ...
        'title','Outer target profiles', 'title_sp','Outer target species densities', ...
        'title_load_outer','Particle (ion) flux density (outer target)', ...
        'title_load_outer_e','Energy flux density (outer target)', ...
        'exp_side','lower_outer');
    inner_targets = struct('x',x_IT, 'sfx','l', 'na',normal_area_l, ...
        'title','Inner target profiles', 'title_sp','Inner target species densities', ...
        'title_load_inner','Particle (ion) flux density (inner target)', ...
        'title_load_inner_e','Energy flux density (inner target)', ...
        'exp_side','lower_inner');
elseif is_lsn
    outer_targets = struct('x',x_OT, 'sfx','r', 'na',normal_area_r, ...
        'title','Outer divertor target profiles', 'title_sp','Outer divertor target species densities', ...
        'exp_side','lower_outer');
    inner_targets = struct('x',x_IT, 'sfx','l', 'na',normal_area_l, ...
        'title','Inner divertor target profiles', 'title_sp','Inner divertor target species densities', ...
        'exp_side','lower_inner');
elseif is_usn
    outer_targets = struct('x',x_OT, 'sfx','l', 'na',normal_area_l, ...
        'title','Outer divertor target profiles', 'title_sp','Outer divertor target species densities', ...
        'exp_side','upper_outer');
    inner_targets = struct('x',x_IT, 'sfx','r', 'na',normal_area_r, ...
        'title','Inner divertor target profiles', 'title_sp','Inner divertor target species densities', ...
        'exp_side','upper_inner');
elseif is_dn
    outer_targets(1) = struct('x',x_OT_bottom, 'sfx','r', 'na',normal_area_r, ...
        'title','Bottom outer target profiles', 'title_sp','Bottom outer target species densities', ...
        'exp_side','lower_outer');
    outer_targets(2) = struct('x',x_OT_top, 'sfx','tr', 'na',normal_area_tr, ...
        'title','Top outer target profiles', 'title_sp','Top outer target species densities', ...
        'exp_side','upper_outer');
    inner_targets(1) = struct('x',x_IT_bottom, 'sfx','l', 'na',normal_area_l, ...
        'title','Bottom inner target profiles', 'title_sp','Bottom inner target species densities', ...
        'exp_side','lower_inner');
    inner_targets(2) = struct('x',x_IT_top, 'sfx','tl', 'na',normal_area_tl, ...
        'title','Top inner target profiles', 'title_sp','Top inner target species densities', ...
        'exp_side','upper_inner');
elseif is_sf
    outer_targets(1) = struct('x',x_OT_primary, 'sfx','r', 'na',normal_area_r, ...
        'title','Primary outer target profiles', 'title_sp','Primary outer target species densities', ...
        'exp_side','');  % TODO: add experimental data for snowflake
    outer_targets(2) = struct('x',x_OT_secondary, 'sfx','tr', 'na',normal_area_tr, ...
        'title','Secondary outer target profiles', 'title_sp','Secondary outer target species densities', ...
        'exp_side','');  % TODO: add experimental data for snowflake
    inner_targets(1) = struct('x',x_IT_primary, 'sfx','l', 'na',normal_area_l, ...
        'title','Inner target profiles', 'title_sp','Inner target species densities', ...
        'exp_side','');  % TODO: add experimental data for snowflake
    inner_targets(2) = struct('x',x_OT_farSOL, 'sfx','tl', 'na',normal_area_tl, ...
        'title','Far SOL outer target profiles', 'title_sp','Far SOL outer target species densities', ...
        'exp_side','');  % TODO: add experimental data for snowflake
end

%% PLOT OUTER MIDPLANE PROFILES

if PLOT_OUTER_MIDPLANE_PROFILES

    fig = figure('windowstyle','docked','NumberTitle','off','Name',title_outer_midplane,'Visible',SHOW_FIGURE_status); figs = [figs, fig];

    % Electron density
    subplot('position',[0.08 0.25 0.42 0.5]);
    exp_ne = get_exp_data_field(PLOT_EXP_DATA_MIDPLANE, measurements_midplane_experiment, 'outer', 'ne_data');
    transport_args = {};
    if PLOT_TRANSPORT
        transport_args = {'TransportProfile', dna0_outer(:,2), 'TransportYLabel', '$D_n$ [m$^2$/s]', pp_transport{:}};
    end
    profileplot(x_OMP, PROFILES.ne3da.value(:,end), ...
        'PastProfiles', get_past(PLOT_PAST_PROFILES, PROFILES.ne3da.value), ...
        'PastColors', PAST_COLORS_DENSITIES, pp_past{:}, ...
        'ExpData', exp_ne, 'ExpDataCoord', RADIAL_DISTANCE, 'ExpDataTypes', EXP_DATA_MIDPLANE_ELECTRON_DENSITY_TYPES, ...
        'ExpDataColors', EXP_DATA_MIDPLANE_ELECTRON_DENSITY_COLORS, pp_exp{:}, ...
        pp_latest_ne{:}, transport_args{:}, ...
        'XLabel', RADIAL_LABEL, 'YLabel', '$n_e$ [m$^{-3}$]', 'Title', 'Electron density', ...
        'LegendLocation', 'southwest', pp_common{:});

    % Electron temperature
    subplot('position',[0.57 0.55 0.32 0.38]);
    exp_Te = get_exp_data_field(PLOT_EXP_DATA_MIDPLANE, measurements_midplane_experiment, 'outer', 'Te_data');
    transport_args = {};
    if PLOT_TRANSPORT
        transport_args = {'TransportProfile', hce0_outer, 'TransportYLabel', '$\chi_e$ [m$^2$/s]', pp_transport{:}};
    end
    profileplot(x_OMP, PROFILES.te3da.value(:,end), ...
        'PastProfiles', get_past(PLOT_PAST_PROFILES, PROFILES.te3da.value), ...
        'PastColors', PAST_COLORS_TEMPERATURES, pp_past{:}, ...
        'ExpData', exp_Te, 'ExpDataCoord', RADIAL_DISTANCE, 'ExpDataTypes', EXP_DATA_MIDPLANE_ELECTRON_TEMPERATURE_TYPES, ...
        'ExpDataColors', EXP_DATA_MIDPLANE_ELECTRON_TEMPERATURE_COLORS, pp_exp{:}, ...
        pp_latest_te{:}, transport_args{:}, ...
        'XLabel', RADIAL_LABEL, 'YLabel', '$T_e$ [eV]', 'Title', 'Electron temperature', ...
        'LabelFontSize', 16, 'TitleFontSize', 18, 'LegendLocation', 'southwest', pp_common{:});

    % Ion temperature
    subplot('position',[0.57 0.06 0.32 0.38]);
    exp_Ti = get_exp_data_field(PLOT_EXP_DATA_MIDPLANE, measurements_midplane_experiment, 'outer', 'Ti_data');
    transport_args = {};
    if PLOT_TRANSPORT
        transport_args = {'TransportProfile', hci0_outer, 'TransportYLabel', '$\chi_i$ [m$^2$/s]', pp_transport{:}};
    end
    profileplot(x_OMP, PROFILES.ti3da.value(:,end), ...
        'PastProfiles', get_past(PLOT_PAST_PROFILES, PROFILES.ti3da.value), ...
        'PastColors', PAST_COLORS_TEMPERATURES, pp_past{:}, ...
        'ExpData', exp_Ti, 'ExpDataCoord', RADIAL_DISTANCE, 'ExpDataTypes', EXP_DATA_MIDPLANE_ION_TEMPERATURE_TYPES, ...
        'ExpDataColors', EXP_DATA_MIDPLANE_ION_TEMPERATURE_COLORS, pp_exp{:}, ...
        pp_latest_te{:}, transport_args{:}, ...
        'XLabel', RADIAL_LABEL, 'YLabel', '$T_i$ [eV]', 'Title', 'Ion temperature', ...
        'LabelFontSize', 16, 'TitleFontSize', 18, 'LegendLocation', 'southwest', pp_common{:});

    if PLOT_PAST_PROFILES
        fprintf('Plot of outer midplane profiles prepared (showing %d time steps, every %.1e s)\n', nsnaps_plotted, effective_time_step_plot);
    else
        fprintf('Plot of outer midplane profiles prepared\n');
    end

end

%% PLOT OUTER MIDPLANE SPECIES PROFILES

if PLOT_OUTER_MIDPLANE_SPECIES_PROFILES

    ns = length(species_label);
    positions = {[0.03 0.58 0.20 0.32],[0.28 0.58 0.20 0.32],[0.53 0.58 0.20 0.32],[0.78 0.58 0.20 0.32], ...
                 [0.03 0.10 0.20 0.32],[0.28 0.10 0.20 0.32],[0.53 0.10 0.20 0.32],[0.78 0.10 0.20 0.32]};

    is = 1; iatm = 1;
    while is <= ns

        if mod(is-1,8) == 0
            fig = figure('windowstyle','docked','NumberTitle','off','Name',title_outer_midplane_species,'Visible',SHOW_FIGURE_status); figs = [figs, fig];
        end

        subplot('position',positions{mod(is-1,8)+1});

        [sp_title, sp_ylabel] = species_title_ylabel(species_label{is}, charge_state(is));
        [latest, past_data, iatm] = get_species_profile(PROFILES, 'a', charge_state(is), is, iatm, PLOT_PAST_PROFILES);

        transport_args = {};
        if PLOT_TRANSPORT
            transport_args = {'TransportProfile', dna0_outer(:,is), pp_transport{:}};
        end

        profileplot(x_OMP, latest, ...
            'PastProfiles', past_data, 'PastColors', PAST_COLORS_DENSITIES, pp_past{:}, ...
            pp_latest_ne{:}, transport_args{:}, ...
            'XLabel', RADIAL_LABEL, 'YLabel', sp_ylabel, 'Title', sp_title, ...
            'LegendLocation', 'southwest', pp_common{:});

        is = is + 1;
    end

    if PLOT_PAST_PROFILES
        fprintf('Plot of outer midplane species densities prepared (showing %d time steps, every %.1e s)\n', nsnaps_plotted, effective_time_step_plot);
    else
        fprintf('Plot of outer midplane species densities prepared\n');
    end

end

%% PLOT INNER MIDPLANE PROFILES

if PLOT_INNER_MIDPLANE_PROFILES

    fig = figure('windowstyle','docked','NumberTitle','off','Name',title_inner_midplane,'Visible',SHOW_FIGURE_status); figs = [figs, fig];

    % Electron density
    subplot('position',[0.08 0.25 0.42 0.5]);
    exp_ne = get_exp_data_field(PLOT_EXP_DATA_MIDPLANE, measurements_midplane_experiment, 'inner', 'ne_data');
    transport_args = {};
    if PLOT_TRANSPORT
        transport_args = {'TransportProfile', dna0_inner(:,2), 'TransportYLabel', '$D_n$ [m$^2$/s]', pp_transport{:}};
    end
    profileplot(x_IMP, PROFILES.ne3di.value(:,end), ...
        'PastProfiles', get_past(PLOT_PAST_PROFILES, PROFILES.ne3di.value), ...
        'PastColors', PAST_COLORS_DENSITIES, pp_past{:}, ...
        'ExpData', exp_ne, 'ExpDataCoord', RADIAL_DISTANCE, 'ExpDataTypes', EXP_DATA_MIDPLANE_ELECTRON_DENSITY_TYPES, ...
        'ExpDataColors', EXP_DATA_MIDPLANE_ELECTRON_DENSITY_COLORS, pp_exp{:}, ...
        pp_latest_ne{:}, transport_args{:}, ...
        'XLabel', RADIAL_LABEL, 'YLabel', '$n_e$ [m$^{-3}$]', 'Title', 'Electron density', ...
        'LegendLocation', 'southwest', pp_common{:});

    % Electron temperature
    subplot('position',[0.57 0.55 0.32 0.38]);
    exp_Te = get_exp_data_field(PLOT_EXP_DATA_MIDPLANE, measurements_midplane_experiment, 'inner', 'Te_data');
    transport_args = {};
    if PLOT_TRANSPORT
        transport_args = {'TransportProfile', hce0_inner, 'TransportYLabel', '$\chi_e$ [m$^2$/s]', pp_transport{:}};
    end
    profileplot(x_IMP, PROFILES.te3di.value(:,end), ...
        'PastProfiles', get_past(PLOT_PAST_PROFILES, PROFILES.te3di.value), ...
        'PastColors', PAST_COLORS_TEMPERATURES, pp_past{:}, ...
        'ExpData', exp_Te, 'ExpDataCoord', RADIAL_DISTANCE, 'ExpDataTypes', EXP_DATA_MIDPLANE_ELECTRON_TEMPERATURE_TYPES, ...
        'ExpDataColors', EXP_DATA_MIDPLANE_ELECTRON_TEMPERATURE_COLORS, pp_exp{:}, ...
        pp_latest_te{:}, transport_args{:}, ...
        'XLabel', RADIAL_LABEL, 'YLabel', '$T_e$ [eV]', 'Title', 'Electron temperature', ...
        'LabelFontSize', 16, 'TitleFontSize', 18, 'LegendLocation', 'southwest', pp_common{:});

    % Ion temperature
    subplot('position',[0.57 0.06 0.32 0.38]);
    exp_Ti = get_exp_data_field(PLOT_EXP_DATA_MIDPLANE, measurements_midplane_experiment, 'inner', 'Ti_data');
    transport_args = {};
    if PLOT_TRANSPORT
        transport_args = {'TransportProfile', hci0_inner, 'TransportYLabel', '$\chi_i$ [m$^2$/s]', pp_transport{:}};
    end
    profileplot(x_IMP, PROFILES.ti3di.value(:,end), ...
        'PastProfiles', get_past(PLOT_PAST_PROFILES, PROFILES.ti3di.value), ...
        'PastColors', PAST_COLORS_TEMPERATURES, pp_past{:}, ...
        'ExpData', exp_Ti, 'ExpDataCoord', RADIAL_DISTANCE, 'ExpDataTypes', EXP_DATA_MIDPLANE_ION_TEMPERATURE_TYPES, ...
        'ExpDataColors', EXP_DATA_MIDPLANE_ION_TEMPERATURE_COLORS, pp_exp{:}, ...
        pp_latest_te{:}, transport_args{:}, ...
        'XLabel', RADIAL_LABEL, 'YLabel', '$T_i$ [eV]', 'Title', 'Ion temperature', ...
        'LabelFontSize', 16, 'TitleFontSize', 18, 'LegendLocation', 'southwest', pp_common{:});

    if PLOT_PAST_PROFILES
        fprintf('Plot of inner midplane profiles prepared (showing %d time steps, every %.1e s)\n', nsnaps_plotted, effective_time_step_plot);
    else
        fprintf('Plot of inner midplane profiles prepared\n');
    end

end

%% PLOT INNER MIDPLANE SPECIES PROFILES

if PLOT_INNER_MIDPLANE_SPECIES_PROFILES

    ns = length(species_label);
    positions = {[0.03 0.58 0.20 0.32],[0.28 0.58 0.20 0.32],[0.53 0.58 0.20 0.32],[0.78 0.58 0.20 0.32], ...
                 [0.03 0.10 0.20 0.32],[0.28 0.10 0.20 0.32],[0.53 0.10 0.20 0.32],[0.78 0.10 0.20 0.32]};

    is = 1; iatm = 1;
    while is <= ns

        if mod(is-1,8) == 0
            fig = figure('windowstyle','docked','NumberTitle','off','Name',title_inner_midplane_species,'Visible',SHOW_FIGURE_status); figs = [figs, fig];
        end

        subplot('position',positions{mod(is-1,8)+1});

        [sp_title, sp_ylabel] = species_title_ylabel(species_label{is}, charge_state(is));
        [latest, past_data, iatm] = get_species_profile(PROFILES, 'i', charge_state(is), is, iatm, PLOT_PAST_PROFILES);

        transport_args = {};
        if PLOT_TRANSPORT
            transport_args = {'TransportProfile', dna0_inner(:,is), pp_transport{:}};
        end

        profileplot(x_IMP, latest, ...
            'PastProfiles', past_data, 'PastColors', PAST_COLORS_DENSITIES, pp_past{:}, ...
            pp_latest_ne{:}, transport_args{:}, ...
            'XLabel', RADIAL_LABEL, 'YLabel', sp_ylabel, 'Title', sp_title, ...
            'LegendLocation', 'southwest', pp_common{:});

        is = is + 1;
    end

    if PLOT_PAST_PROFILES
        fprintf('Plot of inner midplane species densities prepared (showing %d time steps, every %.1e s)\n', nsnaps_plotted, effective_time_step_plot);
    else
        fprintf('Plot of inner midplane species densities prepared\n');
    end

end

%% PLOT OUTER DIVERTOR TARGET PROFILES

if PLOT_OUTER_DIVERTOR_TARGET_PROFILES

    for t = 1:numel(outer_targets)

        tgt = outer_targets(t);
        sfx = tgt.sfx;
        x_tgt = tgt.x;

        fig = figure('windowstyle','docked','NumberTitle','off','Name',tgt.title,'Visible',SHOW_FIGURE_status); figs = [figs, fig];

        % Electron density
        subplot('position',[0.08 0.25 0.42 0.5]);
        exp_ne = get_exp_data_field(PLOT_EXP_DATA_TARGETS, measurements_targets_experiment, tgt.exp_side, 'ne_data');
        profileplot(x_tgt, PROFILES.(sprintf('ne3d%s',sfx)).value(:,end), ...
            'PastProfiles', get_past(PLOT_PAST_PROFILES, PROFILES.(sprintf('ne3d%s',sfx)).value), ...
            'PastColors', PAST_COLORS_DENSITIES, pp_past{:}, ...
            'ExpData', exp_ne, 'ExpDataCoord', RADIAL_DISTANCE, 'ExpDataTypes', EXP_DATA_TARGETS_ELECTRON_DENSITY_TYPES, ...
            'ExpDataColors', EXP_DATA_TARGETS_ELECTRON_DENSITY_COLORS, pp_exp{:}, ...
            pp_latest_ne{:}, ...
            'XLabel', RADIAL_LABEL, 'YLabel', '$n_e$ [m$^{-3}$]', 'Title', 'Electron density', ...
            pp_common{:});

        % Electron temperature
        subplot('position',[0.57 0.55 0.32 0.38]);
        exp_Te = get_exp_data_field(PLOT_EXP_DATA_TARGETS, measurements_targets_experiment, tgt.exp_side, 'Te_data');
        profileplot(x_tgt, PROFILES.(sprintf('te3d%s',sfx)).value(:,end), ...
            'PastProfiles', get_past(PLOT_PAST_PROFILES, PROFILES.(sprintf('te3d%s',sfx)).value), ...
            'PastColors', PAST_COLORS_TEMPERATURES, pp_past{:}, ...
            'ExpData', exp_Te, 'ExpDataCoord', RADIAL_DISTANCE, 'ExpDataTypes', EXP_DATA_TARGETS_ELECTRON_TEMPERATURE_TYPES, ...
            'ExpDataColors', EXP_DATA_TARGETS_ELECTRON_TEMPERATURE_COLORS, pp_exp{:}, ...
            pp_latest_te{:}, ...
            'XLabel', RADIAL_LABEL, 'YLabel', '$T_e$ [eV]', 'Title', 'Electron temperature', ...
            'LabelFontSize', 16, 'TitleFontSize', 18, pp_common{:});

        % Ion temperature
        subplot('position',[0.57 0.06 0.32 0.38]);
        profileplot(x_tgt, PROFILES.(sprintf('ti3d%s',sfx)).value(:,end), ...
            'PastProfiles', get_past(PLOT_PAST_PROFILES, PROFILES.(sprintf('ti3d%s',sfx)).value), ...
            'PastColors', PAST_COLORS_TEMPERATURES, pp_past{:}, ...
            pp_latest_te{:}, ...
            'XLabel', RADIAL_LABEL, 'YLabel', '$T_i$ [eV]', 'Title', 'Ion temperature', ...
            'LabelFontSize', 16, 'TitleFontSize', 18, pp_common{:});

    end

    if PLOT_PAST_PROFILES
        fprintf('Plot of outer divertor target profiles prepared (showing %d time steps, every %.1e s)\n', nsnaps_plotted, effective_time_step_plot);
    else
        fprintf('Plot of outer divertor target profiles prepared\n');
    end

end

%% PLOT OUTER DIVERTOR TARGET SPECIES PROFILES

if PLOT_OUTER_DIVERTOR_TARGET_SPECIES_PROFILES

    ns = length(species_label);
    positions = {[0.03 0.58 0.20 0.32],[0.28 0.58 0.20 0.32],[0.53 0.58 0.20 0.32],[0.78 0.58 0.20 0.32], ...
                 [0.03 0.10 0.20 0.32],[0.28 0.10 0.20 0.32],[0.53 0.10 0.20 0.32],[0.78 0.10 0.20 0.32]};

    for t = 1:numel(outer_targets)

        tgt = outer_targets(t);
        sfx = tgt.sfx;
        x_tgt = tgt.x;

        is = 1; iatm = 1;
        while is <= ns

            if mod(is-1,8) == 0
                fig = figure('windowstyle','docked','NumberTitle','off','Name',tgt.title_sp,'Visible',SHOW_FIGURE_status); figs = [figs, fig];
            end

            subplot('position',positions{mod(is-1,8)+1});

            [sp_title, sp_ylabel] = species_title_ylabel(species_label{is}, charge_state(is));
            [latest, past_data, iatm] = get_species_profile(PROFILES, sfx, charge_state(is), is, iatm, PLOT_PAST_PROFILES);

            profileplot(x_tgt, latest, ...
                'PastProfiles', past_data, 'PastColors', PAST_COLORS_DENSITIES, pp_past{:}, ...
                pp_latest_ne{:}, ...
                'XLabel', RADIAL_LABEL, 'YLabel', sp_ylabel, 'Title', sp_title, ...
                'LegendLocation', 'southwest', pp_common{:});

            is = is + 1;
        end

    end

    if PLOT_PAST_PROFILES
        fprintf('Plot of outer divertor target species densities prepared (showing %d time steps, every %.1e s)\n', nsnaps_plotted, effective_time_step_plot);
    else
        fprintf('Plot of outer divertor target species densities prepared\n');
    end

end

%% PLOT INNER DIVERTOR TARGET PROFILES

if PLOT_INNER_DIVERTOR_TARGET_PROFILES

    for t = 1:numel(inner_targets)

        tgt = inner_targets(t);
        sfx = tgt.sfx;
        x_tgt = tgt.x;

        fig = figure('windowstyle','docked','NumberTitle','off','Name',tgt.title,'Visible',SHOW_FIGURE_status); figs = [figs, fig];

        % Electron density
        subplot('position',[0.08 0.25 0.42 0.5]);
        exp_ne = get_exp_data_field(PLOT_EXP_DATA_TARGETS, measurements_targets_experiment, tgt.exp_side, 'ne_data');
        profileplot(x_tgt, PROFILES.(sprintf('ne3d%s',sfx)).value(:,end), ...
            'PastProfiles', get_past(PLOT_PAST_PROFILES, PROFILES.(sprintf('ne3d%s',sfx)).value), ...
            'PastColors', PAST_COLORS_DENSITIES, pp_past{:}, ...
            'ExpData', exp_ne, 'ExpDataCoord', RADIAL_DISTANCE, 'ExpDataTypes', EXP_DATA_TARGETS_ELECTRON_DENSITY_TYPES, ...
            'ExpDataColors', EXP_DATA_TARGETS_ELECTRON_DENSITY_COLORS, pp_exp{:}, ...
            pp_latest_ne{:}, ...
            'XLabel', RADIAL_LABEL, 'YLabel', '$n_e$ [m$^{-3}$]', 'Title', 'Electron density', ...
            pp_common{:});

        % Electron temperature
        subplot('position',[0.57 0.55 0.32 0.38]);
        exp_Te = get_exp_data_field(PLOT_EXP_DATA_TARGETS, measurements_targets_experiment, tgt.exp_side, 'Te_data');
        profileplot(x_tgt, PROFILES.(sprintf('te3d%s',sfx)).value(:,end), ...
            'PastProfiles', get_past(PLOT_PAST_PROFILES, PROFILES.(sprintf('te3d%s',sfx)).value), ...
            'PastColors', PAST_COLORS_TEMPERATURES, pp_past{:}, ...
            'ExpData', exp_Te, 'ExpDataCoord', RADIAL_DISTANCE, 'ExpDataTypes', EXP_DATA_TARGETS_ELECTRON_TEMPERATURE_TYPES, ...
            'ExpDataColors', EXP_DATA_TARGETS_ELECTRON_TEMPERATURE_COLORS, pp_exp{:}, ...
            pp_latest_te{:}, ...
            'XLabel', RADIAL_LABEL, 'YLabel', '$T_e$ [eV]', 'Title', 'Electron temperature', ...
            'LabelFontSize', 16, 'TitleFontSize', 18, pp_common{:});

        % Ion temperature
        subplot('position',[0.57 0.06 0.32 0.38]);
        profileplot(x_tgt, PROFILES.(sprintf('ti3d%s',sfx)).value(:,end), ...
            'PastProfiles', get_past(PLOT_PAST_PROFILES, PROFILES.(sprintf('ti3d%s',sfx)).value), ...
            'PastColors', PAST_COLORS_TEMPERATURES, pp_past{:}, ...
            pp_latest_te{:}, ...
            'XLabel', RADIAL_LABEL, 'YLabel', '$T_i$ [eV]', 'Title', 'Ion temperature', ...
            'LabelFontSize', 16, 'TitleFontSize', 18, pp_common{:});

    end

    if PLOT_PAST_PROFILES
        fprintf('Plot of inner divertor target profiles prepared (showing %d time steps, every %.1e s)\n', nsnaps_plotted, effective_time_step_plot);
    else
        fprintf('Plot of inner divertor target profiles prepared\n');
    end

end

%% PLOT INNER DIVERTOR TARGET SPECIES PROFILES

if PLOT_INNER_DIVERTOR_TARGET_SPECIES_PROFILES

    ns = length(species_label);
    positions = {[0.03 0.58 0.20 0.32],[0.28 0.58 0.20 0.32],[0.53 0.58 0.20 0.32],[0.78 0.58 0.20 0.32], ...
                 [0.03 0.10 0.20 0.32],[0.28 0.10 0.20 0.32],[0.53 0.10 0.20 0.32],[0.78 0.10 0.20 0.32]};

    for t = 1:numel(inner_targets)

        tgt = inner_targets(t);
        sfx = tgt.sfx;
        x_tgt = tgt.x;

        is = 1; iatm = 1;
        while is <= ns

            if mod(is-1,8) == 0
                fig = figure('windowstyle','docked','NumberTitle','off','Name',tgt.title_sp,'Visible',SHOW_FIGURE_status); figs = [figs, fig];
            end

            subplot('position',positions{mod(is-1,8)+1});

            [sp_title, sp_ylabel] = species_title_ylabel(species_label{is}, charge_state(is));
            [latest, past_data, iatm] = get_species_profile(PROFILES, sfx, charge_state(is), is, iatm, PLOT_PAST_PROFILES);

            profileplot(x_tgt, latest, ...
                'PastProfiles', past_data, 'PastColors', PAST_COLORS_DENSITIES, pp_past{:}, ...
                pp_latest_ne{:}, ...
                'XLabel', RADIAL_LABEL, 'YLabel', sp_ylabel, 'Title', sp_title, ...
                'LegendLocation', 'southwest', pp_common{:});

            is = is + 1;
        end

    end

    if PLOT_PAST_PROFILES
        fprintf('Plot of inner divertor target species densities prepared (showing %d time steps, every %.1e s)\n', nsnaps_plotted, effective_time_step_plot);
    else
        fprintf('Plot of inner divertor target species densities prepared\n');
    end

end

%% PLOT TARGET LOAD PROFILES

if PLOT_TARGET_LOAD_PROFILES

    % Build list of target load plot groups
    % Each group: struct array of targets to plot together in one figure
    if is_limiter || is_sn
        load_groups = {struct( ...
            'outer', struct('x', outer_targets(1).x, 'sfx', outer_targets(1).sfx, 'na', outer_targets(1).na, ...
                'exp_side', outer_targets(1).exp_side, 'tag', 'outer target'), ...
            'inner', struct('x', inner_targets(1).x, 'sfx', inner_targets(1).sfx, 'na', inner_targets(1).na, ...
                'exp_side', inner_targets(1).exp_side, 'tag', 'inner target'), ...
            'fig_title', 'Target load profiles')};
    elseif is_dn
        load_groups = { ...
            struct( ...
                'outer', struct('x', outer_targets(1).x, 'sfx', outer_targets(1).sfx, 'na', outer_targets(1).na, ...
                    'exp_side', outer_targets(1).exp_side, 'tag', 'outer target, bottom'), ...
                'inner', struct('x', inner_targets(1).x, 'sfx', inner_targets(1).sfx, 'na', inner_targets(1).na, ...
                    'exp_side', inner_targets(1).exp_side, 'tag', 'inner target, bottom'), ...
                'fig_title', 'Target load profiles (bottom)'), ...
            struct( ...
                'outer', struct('x', outer_targets(2).x, 'sfx', outer_targets(2).sfx, 'na', outer_targets(2).na, ...
                    'exp_side', outer_targets(2).exp_side, 'tag', 'outer target, top'), ...
                'inner', struct('x', inner_targets(2).x, 'sfx', inner_targets(2).sfx, 'na', inner_targets(2).na, ...
                    'exp_side', inner_targets(2).exp_side, 'tag', 'inner target, top'), ...
                'fig_title', 'Target load profiles (top)')};
    elseif is_sf
        load_groups = { ...
            struct( ...
                'outer', struct('x', outer_targets(1).x, 'sfx', outer_targets(1).sfx, 'na', outer_targets(1).na, ...
                    'exp_side', outer_targets(1).exp_side, 'tag', 'outer target, primary'), ...
                'inner', struct('x', inner_targets(1).x, 'sfx', inner_targets(1).sfx, 'na', inner_targets(1).na, ...
                    'exp_side', inner_targets(1).exp_side, 'tag', 'inner target, primary'), ...
                'fig_title', 'Target load profiles (primary)'), ...
            struct( ...
                'outer', struct('x', outer_targets(2).x, 'sfx', outer_targets(2).sfx, 'na', outer_targets(2).na, ...
                    'exp_side', outer_targets(2).exp_side, 'tag', 'outer target, secondary'), ...
                'inner', struct('x', inner_targets(2).x, 'sfx', inner_targets(2).sfx, 'na', inner_targets(2).na, ...
                    'exp_side', inner_targets(2).exp_side, 'tag', 'outer target, far SOL'), ...
                'fig_title', 'Target load profiles (secondary)')};
    end

    for g = 1:numel(load_groups)

        lg = load_groups{g};
        ot = lg.outer;
        it = lg.inner;

        fig = figure('windowstyle','docked','NumberTitle','off','Name',lg.fig_title,'Visible',SHOW_FIGURE_status); figs = [figs, fig];

        % Particle (ion) flux density (outer target)
        subplot('position',[0.1 0.55 0.32 0.38]);
        fo_outer = abs(PROFILES.(sprintf('fo3d%s',ot.sfx)).value(:,end)) ./ ot.na;
        fo_outer_past = [];
        if PLOT_PAST_PROFILES
            fo_outer_all = PROFILES.(sprintf('fo3d%s',ot.sfx)).value;
            fo_outer_past = zeros(size(fo_outer_all));
            for i = 1:size(fo_outer_all,2)
                fo_outer_past(:,i) = abs(fo_outer_all(:,i)) ./ ot.na;
            end
        end
        exp_gamma_ot = get_exp_data_field(PLOT_EXP_DATA_TARGETS, measurements_targets_experiment, ot.exp_side, 'gamma_data');
        profileplot(ot.x, fo_outer, ...
            'PastProfiles', fo_outer_past, 'PastColors', PAST_COLORS_DENSITIES, pp_past{:}, ...
            'ExpData', exp_gamma_ot, 'ExpDataCoord', RADIAL_DISTANCE, 'ExpDataTypes', EXP_DATA_TARGETS_PARTICLE_FLUX_DENSITY_TYPES, ...
            'ExpDataColors', EXP_DATA_TARGETS_PARTICLE_FLUX_DENSITY_COLORS, pp_exp{:}, ...
            pp_latest_ne{:}, ...
            'XLabel', RADIAL_LABEL, 'YLabel', '$\Gamma_{\perp}$ [m$^{-2}$s$^{-1}$]', ...
            'Title', sprintf('Particle (ion) flux density (%s)',ot.tag), ...
            'LabelFontSize', 16, 'TitleFontSize', 18, pp_common{:});

        % Energy flux density (outer target)
        subplot('position',[0.1 0.06 0.32 0.38]);
        ft_outer = PROFILES.(sprintf('ft3d%s',ot.sfx)).value(:,end) ./ ot.na;
        ft_outer_past = [];
        if PLOT_PAST_PROFILES
            ft_outer_all = PROFILES.(sprintf('ft3d%s',ot.sfx)).value;
            ft_outer_past = zeros(size(ft_outer_all));
            for i = 1:size(ft_outer_all,2)
                ft_outer_past(:,i) = ft_outer_all(:,i) ./ ot.na;
            end
        end
        exp_q_ot = get_exp_data_field(PLOT_EXP_DATA_TARGETS, measurements_targets_experiment, ot.exp_side, 'q_data');
        profileplot(ot.x, ft_outer, ...
            'PastProfiles', ft_outer_past, 'PastColors', PAST_COLORS_TEMPERATURES, pp_past{:}, ...
            'ExpData', exp_q_ot, 'ExpDataCoord', RADIAL_DISTANCE, 'ExpDataTypes', EXP_DATA_TARGETS_ENERGY_FLUX_DENSITY_TYPES, ...
            'ExpDataColors', EXP_DATA_TARGETS_ENERGY_FLUX_DENSITY_COLORS, pp_exp{:}, ...
            pp_latest_te{:}, ...
            'XLabel', RADIAL_LABEL, 'YLabel', '$Q_{\perp}$ [W/m$^2$]', ...
            'Title', sprintf('Energy flux density (%s)',ot.tag), ...
            'LabelFontSize', 16, 'TitleFontSize', 18, pp_common{:});

        % Particle (ion) flux density (inner target)
        subplot('position',[0.55 0.55 0.32 0.38]);
        fo_inner = abs(PROFILES.(sprintf('fo3d%s',it.sfx)).value(:,end)) ./ it.na;
        fo_inner_past = [];
        if PLOT_PAST_PROFILES
            fo_inner_all = PROFILES.(sprintf('fo3d%s',it.sfx)).value;
            fo_inner_past = zeros(size(fo_inner_all));
            for i = 1:size(fo_inner_all,2)
                fo_inner_past(:,i) = abs(fo_inner_all(:,i)) ./ it.na;
            end
        end
        exp_gamma_it = get_exp_data_field(PLOT_EXP_DATA_TARGETS, measurements_targets_experiment, it.exp_side, 'gamma_data');
        profileplot(it.x, fo_inner, ...
            'PastProfiles', fo_inner_past, 'PastColors', PAST_COLORS_DENSITIES, pp_past{:}, ...
            'ExpData', exp_gamma_it, 'ExpDataCoord', RADIAL_DISTANCE, 'ExpDataTypes', EXP_DATA_TARGETS_PARTICLE_FLUX_DENSITY_TYPES, ...
            'ExpDataColors', EXP_DATA_TARGETS_PARTICLE_FLUX_DENSITY_COLORS, pp_exp{:}, ...
            pp_latest_ne{:}, ...
            'XLabel', RADIAL_LABEL, 'YLabel', '$\Gamma_{\perp}$ [m$^{-2}$s$^{-1}$]', ...
            'Title', sprintf('Particle (ion) flux density (%s)',it.tag), ...
            'LabelFontSize', 16, 'TitleFontSize', 18, pp_common{:});

        % Energy flux density (inner target)
        subplot('position',[0.55 0.06 0.32 0.38]);
        ft_inner = PROFILES.(sprintf('ft3d%s',it.sfx)).value(:,end) ./ it.na;
        ft_inner_past = [];
        if PLOT_PAST_PROFILES
            ft_inner_all = PROFILES.(sprintf('ft3d%s',it.sfx)).value;
            ft_inner_past = zeros(size(ft_inner_all));
            for i = 1:size(ft_inner_all,2)
                ft_inner_past(:,i) = ft_inner_all(:,i) ./ it.na;
            end
        end
        exp_q_it = get_exp_data_field(PLOT_EXP_DATA_TARGETS, measurements_targets_experiment, it.exp_side, 'q_data');
        profileplot(it.x, ft_inner, ...
            'PastProfiles', ft_inner_past, 'PastColors', PAST_COLORS_TEMPERATURES, pp_past{:}, ...
            'ExpData', exp_q_it, 'ExpDataCoord', RADIAL_DISTANCE, 'ExpDataTypes', EXP_DATA_TARGETS_ENERGY_FLUX_DENSITY_TYPES, ...
            'ExpDataColors', EXP_DATA_TARGETS_ENERGY_FLUX_DENSITY_COLORS, pp_exp{:}, ...
            pp_latest_te{:}, ...
            'XLabel', RADIAL_LABEL, 'YLabel', '$Q_{\perp}$ [W/m$^2$]', ...
            'Title', sprintf('Energy flux density (%s)',it.tag), ...
            'LabelFontSize', 16, 'TitleFontSize', 18, pp_common{:});

    end

    if PLOT_PAST_PROFILES
        fprintf('Plot of target load profiles prepared (showing %d time steps, every %.1e s)\n', nsnaps_plotted, effective_time_step_plot);
    else
        fprintf('Plot of target load profiles prepared\n');
    end

end

%% PRINT THE PLOTS

if PRINT_FIGURE
    print_plot(figs, [FIGURE_WIDTH FIGURE_HEIGHT], 'run_profiles', FILE_FORMAT, FILE_RESOLUTION);
end

%% QUIT SESSION AFTER CLOSING FIGURES IF CALLED AS FUNCTION

if nargin ~= 0
    for k = 1:numel(figs)
        waitfor(figs(k));
    end
end

end

%% HELPER FUNCTIONS

function past_data = get_past(PLOT_PAST_PROFILES, field_value)
% GET_PAST returns the profile matrix for past profiles, or [] if not requested

    if PLOT_PAST_PROFILES
        past_data = field_value;
    else
        past_data = [];
    end
end

function past_data = get_past_3d(PLOT_PAST_PROFILES, field_value, species_idx)
% GET_PAST_3D returns past profiles for a 3D field (radial x species x time)

    if PLOT_PAST_PROFILES
        past_data = squeeze(field_value(:,species_idx,:));
    else
        past_data = [];
    end
end

function exp_data = get_exp_data_field(plot_flag, measurements, side, field_name)
% GET_EXP_DATA_FIELD extracts experimental data cell array for a given side and field

    exp_data = {};
    if ~plot_flag
        return;
    end
    if isempty(side)
        return;
    end
    try
        if isfield(measurements.(side), field_name)
            exp_data = measurements.(side).(field_name);
        end
    catch
    end
end

function [sp_title, sp_ylabel] = species_title_ylabel(label, cs)
% SPECIES_TITLE_YLABEL returns formatted title and ylabel for a species subplot

    if cs == 0
        sp_title = sprintf('%s atom density', label);
    else
        sp_title = sprintf('%s ion density', label);
    end
    sp_ylabel = sprintf('$n_{%s}$ [m$^{-3}$]', label);
end

function [latest, past_data, iatm] = get_species_profile(PROFILES, sfx, cs, is, iatm, PLOT_PAST_PROFILES)
% GET_SPECIES_PROFILE returns the latest and past species density profiles
%   sfx: field suffix ('a' for outer midplane, 'i' for inner midplane,
%         'l','r','tl','tr' for targets)

    if cs == 0
        try
            latest = PROFILES.(sprintf('dab3d%s',sfx)).value(:,iatm,end);
            past_data = get_past_3d(PLOT_PAST_PROFILES, PROFILES.(sprintf('dab3d%s',sfx)).value, iatm);
        catch
            latest = PROFILES.(sprintf('na3d%s',sfx)).value(:,is,end);
            past_data = get_past_3d(PLOT_PAST_PROFILES, PROFILES.(sprintf('na3d%s',sfx)).value, is);
        end
        iatm = iatm + 1;
    else
        latest = PROFILES.(sprintf('na3d%s',sfx)).value(:,is,end);
        past_data = get_past_3d(PLOT_PAST_PROFILES, PROFILES.(sprintf('na3d%s',sfx)).value, is);
    end
end

function check_exp_types_length(types_cell, measurements, sides, field_name, var_name)
% CHECK_EXP_TYPES_LENGTH validates that the exp data types cell is long enough

    if isempty(types_cell)
        return;
    end
    max_len = 0;
    for k = 1:numel(sides)
        try
            if isfield(measurements.(sides{k}), field_name)
                max_len = max(max_len, numel(measurements.(sides{k}).(field_name)));
            end
        catch
        end
    end
    if numel(types_cell) < max_len
        error('Error: %s has length %d but at least %d entries are needed', ...
            var_name, numel(types_cell), max_len);
    end
end

function rgb_colors = resolve_exp_colors(color_names, COLORS_MAP, name_to_index)
% RESOLVE_EXP_COLORS converts a cell array of color name strings to RGB values
%   If empty or 'auto', returns empty (auto-assignment will be handled by profileplot)

    if isempty(color_names) || (ischar(color_names) && strcmp(color_names, 'auto'))
        rgb_colors = {};
        return;
    end
    rgb_colors = cell(1, numel(color_names));
    for k = 1:numel(color_names)
        rgb_colors{k} = COLORS_MAP{name_to_index(color_names{k})};
    end
end

function out = unwrap_cell(val)
% UNWRAP_CELL unwraps a cell array that was double-wrapped via {{}} in struct default
    if iscell(val) && numel(val) == 1 && (iscell(val{1}) || ischar(val{1}))
        out = val{1};
    else
        out = val;
    end
end

function out = auto_to_empty(val)
% AUTO_TO_EMPTY converts the 'auto' sentinel string to an empty cell array

    if ischar(val) && strcmp(val, 'auto')
        out = {};
    else
        out = val;
    end
end
