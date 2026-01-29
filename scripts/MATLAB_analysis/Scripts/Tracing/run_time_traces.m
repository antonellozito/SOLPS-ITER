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

% Specify the plot options
% (linewidths, time range to show in the plots and style of y-axis range)
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
 ROLLING_AVERAGE_STEPS, BATCH_AVERAGE_STEPS, PHASE_AVERAGE_STEPS, ...
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

% Custom rules

averages_selection = {'ROLLING_AVERAGE_STEPS'
                      'BATCH_AVERAGE_STEPS'
                      'PHASE_AVERAGE_STEPS'};

num_nonzero = sum(cellfun(@(v) any(evalin('caller', v) ~= 0), averages_selection));

if num_nonzero > 1
    error('Error: At most one of these variables can be nonzero:\n%s', strjoin(averages_selection, ', '));
end

if not(strcmp(YLIM_STYLE,'tickaligned') || strcmp(YLIM_STYLE,'tight') || strcmp(YLIM_STYLE,'padded')) 
    error('Error: YLIM_STYLE should be ''tickaligned'' or ''tight'' or ''padded''');
end

if ~SHOW_FIGURE && ~PRINT_FIGURE
    error('Error: ''SHOW_FIGURE'' and ''PRINT_FIGURE'' cannot be both false');
end

%% LOAD SIMULATION

SIMULATION = load_solps_simulation(RUN);

%% READ DATA

TIME_TRACES = read_b2time(SIMULATION,'TIME_TRACES');

if PLOT_MIDPLANE_SPECIES_DENSITIES || PLOT_DIVERTOR_SPECIES_DENSITIES

    [species_label,atomic_number,charge_state] = read_species(SIMULATION);

end

%% CALCULATE ROLLING AVERAGE

if ROLLING_AVERAGE_STEPS > 0

    time_step = TIME_TRACES.timesa.value(2) - TIME_TRACES.timesa.value(1);

    fields = fieldnames(TIME_TRACES);
    for i = 1:numel(fields)
        f = fields{i};
        if ~ismember(f, {'timesa'})
            TIME_TRACES.(f).value = rolling_average(TIME_TRACES.(f).value,ROLLING_AVERAGE_STEPS,'b2time');
        end
    end

    fprintf('Rolling average of the time traces computed over a period of %d time steps (%.1e s)\n',...
        ROLLING_AVERAGE_STEPS,ROLLING_AVERAGE_STEPS*time_step)

end

%% CALCULATE BATCH AVERAGE

if BATCH_AVERAGE_STEPS > 0

    time_step = TIME_TRACES.timesa.value(2) - TIME_TRACES.timesa.value(1);

    fields = fieldnames(TIME_TRACES);
    for i = 1:numel(fields)
        f = fields{i};
        if ~ismember(f, {'timesa'})
            TIME_TRACES.(f).value = batch_average(TIME_TRACES.(f).value,BATCH_AVERAGE_STEPS,'b2time');
        else
            TIME_TRACES.timesa.value = batch_average(TIME_TRACES.timesa.value,BATCH_AVERAGE_STEPS,'time');
        end
    end

    fprintf('Batch average of the time traces computed over a period of %d time steps (%.1e s)\n',...
        BATCH_AVERAGE_STEPS,BATCH_AVERAGE_STEPS*time_step)

end

%% CALCULATE PHASE AVERAGE

if PHASE_AVERAGE_STEPS > 0

    time_step = TIME_TRACES.timesa.value(2) - TIME_TRACES.timesa.value(1);

    fields = fieldnames(TIME_TRACES);
    for i = 1:numel(fields)
        f = fields{i};
        if ~ismember(f, {'timesa'})
            TIME_TRACES.(f).value = phase_average(TIME_TRACES.(f).value,PHASE_AVERAGE_STEPS,'b2time_time_traces');
        else
            TIME_TRACES.timesa.value = phase_average(TIME_TRACES.timesa.value,PHASE_AVERAGE_STEPS,'time');
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

COLORS = load_colors('default',7,'rgb');
COLORS_DARK = load_colors('default_dark',7,'rgb');
COLORS_LIGHT = load_colors('default_light',7,'rgb');

originalYLimitMethod = get(groot, 'defaultAxesYLimitMethod');
set(groot, 'defaultAxesYLimitMethod', YLIM_STYLE);

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

%% PLOT MIDPLANE QUANTITIES

% Midplane state variables

if PLOT_MIDPLANE_STATE_VARIABLES
    
    for i = 1:ncut

        fig = figure('windowstyle','docked','NumberTitle','off','Name',titles_midplane_state_variables{i},'Visible',SHOW_FIGURE_status); figs = [figs, fig];
    
        subplot('position',[0.08 0.25 0.42 0.5]);
        plot(TIME_TRACES.timesa.value,TIME_TRACES.nesepm.value(i,:),'linewidth',LINEWIDTH,'DisplayName',labels_midplane{i},'color',COLORS{1}); hold on;
        xl = xlim; 
        if exist('TMIN','var') && ~isnan(TMIN), xl(1) = TMIN; end
        if exist('TMAX','var') && ~isnan(TMAX), xl(2) = TMAX; end
        xlim(xl);
        xlabel('Time [s]','interpreter','latex','fontsize',18);
        ylabel('$n_e$ [m$^{-3}$]','interpreter','latex','fontsize',18);
        lgd = legend('interpreter','latex','fontsize',15);
        title('Midplane electron density','interpreter','latex','fontsize',20);
        if SHOW_NAME
            text(0.98,0.04,RUN,'Units','normalized','HorizontalAlignment','right','VerticalAlignment','bottom', ...
                'interpreter','latex','FontSize',8,'BackgroundColor','white','EdgeColor','black');
        end
    
        subplot('position',[0.57 0.55 0.32 0.38]);
        plot(TIME_TRACES.timesa.value,TIME_TRACES.tesepm.value(i,:),'linewidth',LINEWIDTH,'DisplayName',labels_midplane{i},'color',COLORS{2}); hold on;
        xl = xlim; 
        if exist('TMIN','var') && ~isnan(TMIN), xl(1) = TMIN; end
        if exist('TMAX','var') && ~isnan(TMAX), xl(2) = TMAX; end
        xlim(xl);
        xlabel('Time [s]','interpreter','latex','fontsize',16);
        ylabel('$T_e$ [eV]','interpreter','latex','fontsize',16);
        lgd = legend('interpreter','latex','fontsize',15);
        title('Midplane electron temperature','interpreter','latex','fontsize',18);
        if SHOW_NAME
            text(0.98,0.04,RUN,'Units','normalized','HorizontalAlignment','right','VerticalAlignment','bottom', ...
                'interpreter','latex','FontSize',8,'BackgroundColor','white','EdgeColor','black');
        end
    
        subplot('position',[0.57 0.06 0.32 0.38]);
        plot(TIME_TRACES.timesa.value,TIME_TRACES.tisepm.value(i,:),'linewidth',LINEWIDTH,'DisplayName',labels_midplane{i},'color',COLORS{2}); hold on;
        xl = xlim; 
        if exist('TMIN','var') && ~isnan(TMIN), xl(1) = TMIN; end
        if exist('TMAX','var') && ~isnan(TMAX), xl(2) = TMAX; end
        xlim(xl);
        xlabel('Time [s]','interpreter','latex','fontsize',16);
        ylabel('$T_i$ [eV]','interpreter','latex','fontsize',16);
        lgd = legend('interpreter','latex','fontsize',15);
        title('Midplane ion temperature','interpreter','latex','fontsize',18);
        if SHOW_NAME
            text(0.98,0.04,RUN,'Units','normalized','HorizontalAlignment','right','VerticalAlignment','bottom', ...
                'interpreter','latex','FontSize',8,'BackgroundColor','white','EdgeColor','black');
        end

    end

    fprintf('Plot of midplane species variables prepared\n');

end

% Midplane species densities

if PLOT_MIDPLANE_SPECIES_DENSITIES

    if not(isfield(TIME_TRACES,'nasepm'))
        error('Error: species densities fields not present in b2time.nc')
    end

    ns = length(species_label);

    positions{1}=[0.03 0.58 0.20 0.32];
    positions{2}=[0.28 0.58 0.20 0.32];
    positions{3}=[0.53 0.58 0.20 0.32];
    positions{4}=[0.78 0.58 0.20 0.32];
    positions{5}=[0.03 0.10 0.20 0.32];
    positions{6}=[0.28 0.10 0.20 0.32];
    positions{7}=[0.53 0.10 0.20 0.32];
    positions{8}=[0.78 0.10 0.20 0.32];

    for i = 1:ncut

        is = 1;
        iatm = 1;
        while is <= ns
    
            if mod(is-1,8) == 0
                fig = figure('windowstyle','docked','NumberTitle','off','Name',titles_midplane_species_densities{i},'Visible',SHOW_FIGURE_status); figs = [figs, fig];
            end
    
            subplot('position',positions{mod(is-1,8)+1});
            if charge_state(is)==0
                try
                    temp(:) = TIME_TRACES.dabsepm.value(i,iatm,:);
                    plot(TIME_TRACES.timesa.value,temp,'linewidth',LINEWIDTH,'DisplayName',labels_midplane{i},'color',COLORS{1}); hold on;
                catch
                    temp(:) = TIME_TRACES.nasepm.value(i,is,:);
                    plot(TIME_TRACES.timesa.value,temp,'linewidth',LINEWIDTH,'DisplayName',labels_midplane{i},'color',COLORS{1}); hold on;
                end
                iatm = iatm+1;
            else
                temp(:) = TIME_TRACES.nasepm.value(i,is,:);
                plot(TIME_TRACES.timesa.value,temp,'linewidth',LINEWIDTH,'DisplayName',labels_midplane{i},'color',COLORS{1}); hold on;
            end
            xl = xlim; 
            if exist('TMIN','var') && ~isnan(TMIN), xl(1) = TMIN; end
            if exist('TMAX','var') && ~isnan(TMAX), xl(2) = TMAX; end
            xlim(xl);
            xlabel('Time [s]','interpreter','latex','fontsize',18);
            ylabel(sprintf('$n_{%s}$ [m$^{-3}$]',species_label{is}),'interpreter','latex','fontsize',18);
            lgd = legend('interpreter','latex','fontsize',15);
            if charge_state(is)==0
                title(sprintf('Midplane %s atom density',species_label{is}),'interpreter','latex','fontsize',20);
            else
                title(sprintf('Midplane %s ion density',species_label{is}),'interpreter','latex','fontsize',20);
            end
            if SHOW_NAME
                text(0.98,0.04,RUN,'Units','normalized','HorizontalAlignment','right','VerticalAlignment','bottom', ...
                    'interpreter','latex','FontSize',8,'BackgroundColor','white','EdgeColor','black');
            end
    
            is = is+1;

        end

    end

    fprintf('Plot of midplane species densities prepared\n');

end

%% PLOT DIVERTOR QUANTITIES

% Divertor state variables

if PLOT_DIVERTOR_STATE_VARIABLES

    for i = 1:ncut

        fig = figure('windowstyle','docked','NumberTitle','off','Name',titles_divertor_state_variables{i},'Visible',SHOW_FIGURE_status); figs = [figs, fig];
    
        subplot('position',[0.08 0.25 0.42 0.5]);
        plot(TIME_TRACES.timesa.value,TIME_TRACES.nesepi.value(i,:),'linewidth',LINEWIDTH,'DisplayName',labels_divertor{i}{1},'color',COLORS_LIGHT{1}); hold on;
        plot(TIME_TRACES.timesa.value,TIME_TRACES.nemxip.value(i,:),'linewidth',LINEWIDTH,'DisplayName',labels_divertor{i}{2},'color',COLORS_LIGHT{1},'linestyle',':'); hold on;
        plot(TIME_TRACES.timesa.value,TIME_TRACES.nesepa.value(i,:),'linewidth',LINEWIDTH,'DisplayName',labels_divertor{i}{3},'color',COLORS_DARK{1}); hold on;
        plot(TIME_TRACES.timesa.value,TIME_TRACES.nemxap.value(i,:),'linewidth',LINEWIDTH,'DisplayName',labels_divertor{i}{4},'color',COLORS_DARK{1},'linestyle',':'); hold on;
        xl = xlim; 
        if exist('TMIN','var') && ~isnan(TMIN), xl(1) = TMIN; end
        if exist('TMAX','var') && ~isnan(TMAX), xl(2) = TMAX; end
        xlim(xl);
        xlabel('Time [s]','interpreter','latex','fontsize',18);
        ylabel('$n_e$ [m$^{-3}$]','interpreter','latex','fontsize',18);
        lgd = legend('interpreter','latex','fontsize',15);
        title('Divertor electron density','interpreter','latex','fontsize',20);
        if SHOW_NAME
            text(0.98,0.04,RUN,'Units','normalized','HorizontalAlignment','right','VerticalAlignment','bottom', ...
                'interpreter','latex','FontSize',8,'BackgroundColor','white','EdgeColor','black');
        end
    
        subplot('position',[0.57 0.55 0.32 0.38]);
        plot(TIME_TRACES.timesa.value,TIME_TRACES.tesepi.value(i,:),'linewidth',LINEWIDTH,'DisplayName',labels_divertor{i}{1},'color',COLORS_LIGHT{2}); hold on;
        plot(TIME_TRACES.timesa.value,TIME_TRACES.temxip.value(i,:),'linewidth',LINEWIDTH,'DisplayName',labels_divertor{i}{2},'color',COLORS_LIGHT{2},'linestyle',':'); hold on;
        plot(TIME_TRACES.timesa.value,TIME_TRACES.tesepa.value(i,:),'linewidth',LINEWIDTH,'DisplayName',labels_divertor{i}{3},'color',COLORS_DARK{2}); hold on;
        plot(TIME_TRACES.timesa.value,TIME_TRACES.temxap.value(i,:),'linewidth',LINEWIDTH,'DisplayName',labels_divertor{i}{4},'color',COLORS_DARK{2},'linestyle',':'); hold on;
        xl = xlim; 
        if exist('TMIN','var') && ~isnan(TMIN), xl(1) = TMIN; end
        if exist('TMAX','var') && ~isnan(TMAX), xl(2) = TMAX; end
        xlim(xl);
        xlabel('Time [s]','interpreter','latex','fontsize',16);
        ylabel('$T_e$ [eV]','interpreter','latex','fontsize',16);
        lgd = legend('interpreter','latex','fontsize',15);
        title('Divertor electron temperature','interpreter','latex','fontsize',18);
        if SHOW_NAME
            text(0.98,0.04,RUN,'Units','normalized','HorizontalAlignment','right','VerticalAlignment','bottom', ...
                'interpreter','latex','FontSize',8,'BackgroundColor','white','EdgeColor','black');
        end
    
        subplot('position',[0.57 0.06 0.32 0.38]);
        plot(TIME_TRACES.timesa.value,TIME_TRACES.tisepi.value(i,:),'linewidth',LINEWIDTH,'DisplayName',labels_divertor{i}{1},'color',COLORS_LIGHT{2}); hold on;
        plot(TIME_TRACES.timesa.value,TIME_TRACES.timxip.value(i,:),'linewidth',LINEWIDTH,'DisplayName',labels_divertor{i}{2},'color',COLORS_LIGHT{2},'linestyle',':'); hold on;
        plot(TIME_TRACES.timesa.value,TIME_TRACES.tisepa.value(i,:),'linewidth',LINEWIDTH,'DisplayName',labels_divertor{i}{3},'color',COLORS_DARK{2}); hold on;
        plot(TIME_TRACES.timesa.value,TIME_TRACES.timxap.value(i,:),'linewidth',LINEWIDTH,'DisplayName',labels_divertor{i}{4}','color',COLORS_DARK{2},'linestyle',':'); hold on;
        xl = xlim; 
        if exist('TMIN','var') && ~isnan(TMIN), xl(1) = TMIN; end
        if exist('TMAX','var') && ~isnan(TMAX), xl(2) = TMAX; end
        xlim(xl);
        xlabel('Time [s]','interpreter','latex','fontsize',16);
        ylabel('$T_e$ [eV]','interpreter','latex','fontsize',16);
        lgd = legend('interpreter','latex','fontsize',15);
        title('Divertor ion temperature','interpreter','latex','fontsize',18);
        if SHOW_NAME
            text(0.98,0.04,RUN,'Units','normalized','HorizontalAlignment','right','VerticalAlignment','bottom', ...
                'interpreter','latex','FontSize',8,'BackgroundColor','white','EdgeColor','black');
        end
        
    end

    fprintf('Plot of divertor state variables prepared\n');

end

% Divertor species densities

if PLOT_DIVERTOR_SPECIES_DENSITIES

    if not(isfield(TIME_TRACES,'nasepm'))
        error('Error: species densities fields not present in b2time.nc')
    end

    ns = length(species_label);

    positions{1}=[0.03 0.58 0.20 0.32];
    positions{2}=[0.28 0.58 0.20 0.32];
    positions{3}=[0.53 0.58 0.20 0.32];
    positions{4}=[0.78 0.58 0.20 0.32];
    positions{5}=[0.03 0.10 0.20 0.32];
    positions{6}=[0.28 0.10 0.20 0.32];
    positions{7}=[0.53 0.10 0.20 0.32];
    positions{8}=[0.78 0.10 0.20 0.32];

    for i = 1:ncut

        is = 1;
        iatm = 1;
        while is <= ns
    
            if mod(is-1,8) == 0
                fig = figure('windowstyle','docked','NumberTitle','off','Name',titles_divertor_species_densities{i},'Visible',SHOW_FIGURE_status); figs = [figs, fig];
            end
    
            subplot('position',positions{mod(is-1,8)+1});
            if charge_state(is)==0
                try
                    temp(:) = TIME_TRACES.dabsepi.value(i,iatm,:);
                    plot(TIME_TRACES.timesa.value,temp,'linewidth',LINEWIDTH,'DisplayName',labels_divertor{i}{1},'color',COLORS_LIGHT{1}); hold on;
                    temp(:) = TIME_TRACES.dabsepa.value(i,iatm,:);
                    plot(TIME_TRACES.timesa.value,temp,'linewidth',LINEWIDTH,'DisplayName',labels_divertor{i}{3},'color',COLORS_DARK{1}); hold on;
                catch
                    temp(:) = TIME_TRACES.nasepi.value(i,is,:);
                    plot(TIME_TRACES.timesa.value,temp,'linewidth',LINEWIDTH,'DisplayName',labels_divertor{i}{1},'color',COLORS_LIGHT{1}); hold on;
                    temp(:) = TIME_TRACES.namxip.value(i,is,:);
                    plot(TIME_TRACES.timesa.value,temp,'linewidth',LINEWIDTH,'DisplayName',labels_divertor{i}{2},'color',COLORS_LIGHT{1},'linestyle',':'); hold on;
                    temp(:) = TIME_TRACES.nesepa.value(i,is,:);
                    plot(TIME_TRACES.timesa.value,temp,'linewidth',LINEWIDTH,'DisplayName',labels_divertor{i}{3},'color',COLORS_DARK{1}); hold on;
                    temp(:) = TIME_TRACES.namxap.value(i,is,:);
                    plot(TIME_TRACES.timesa.value,temp,'linewidth',LINEWIDTH,'DisplayName',labels_divertor{i}{4},'color',COLORS_DARK{1},'linestyle',':'); hold on;
                end
                iatm = iatm+1;
            else
                temp(:) = TIME_TRACES.nasepi.value(i,is,:);
                plot(TIME_TRACES.timesa.value,temp,'linewidth',LINEWIDTH,'DisplayName',labels_divertor{i}{1},'color',COLORS_LIGHT{1}); hold on;
                temp(:) = TIME_TRACES.namxip.value(i,is,:);
                plot(TIME_TRACES.timesa.value,temp,'linewidth',LINEWIDTH,'DisplayName',labels_divertor{i}{2}','color',COLORS_LIGHT{1},'linestyle',':'); hold on;
                temp(:) = TIME_TRACES.nasepa.value(i,is,:);
                plot(TIME_TRACES.timesa.value,temp,'linewidth',LINEWIDTH,'DisplayName',labels_divertor{i}{3},'color',COLORS_DARK{1}); hold on;
                temp(:) = TIME_TRACES.namxap.value(i,is,:);
                plot(TIME_TRACES.timesa.value,temp,'linewidth',LINEWIDTH,'DisplayName',labels_divertor{i}{4},'color',COLORS_DARK{1},'linestyle',':'); hold on;
            end
            xl = xlim; 
            if exist('TMIN','var') && ~isnan(TMIN), xl(1) = TMIN; end
            if exist('TMAX','var') && ~isnan(TMAX), xl(2) = TMAX; end
            xlim(xl);
            xlabel('Time [s]','interpreter','latex','fontsize',18);
            ylabel(sprintf('$n_{%s}$ [m$^{-3}$]',species_label{is}),'interpreter','latex','fontsize',18);
            lgd = legend('interpreter','latex','fontsize',15);
            if charge_state(is)==0
                title(sprintf('Divertor %s atom density',species_label{is}),'interpreter','latex','fontsize',20);
            else
                title(sprintf('Divertor %s ion density',species_label{is}),'interpreter','latex','fontsize',20);
            end
            if SHOW_NAME
                text(0.98,0.04,RUN,'Units','normalized','HorizontalAlignment','right','VerticalAlignment','bottom', ...
                    'interpreter','latex','FontSize',8,'BackgroundColor','white','EdgeColor','black');
            end
    
            is = is+1;

        end

    end

    fprintf('Plot of divertor species densities prepared\n');

end

%% PLOT FLUXES

% Poloidal fluxes

if PLOT_POLOIDAL_FLUXES

    for i = 1:ncut
    
        fig = figure('windowstyle','docked','NumberTitle','off','Name',titles_poloidal_fluxes{i},'Visible',SHOW_FIGURE_status); figs = [figs, fig];
    
        subplot('position',[0.08 0.25 0.42 0.5]);
        plot(TIME_TRACES.timesa.value,abs(TIME_TRACES.fnixip.value(i,:)),'linewidth',LINEWIDTH,'DisplayName',labels_poloidal_fluxes{i}{1},'color',COLORS_LIGHT{1}); hold on;
        plot(TIME_TRACES.timesa.value,abs(TIME_TRACES.fnixap.value(i,:)),'linewidth',LINEWIDTH,'DisplayName',labels_poloidal_fluxes{i}{2},'color',COLORS_DARK{1}); hold on;
        xl = xlim; 
        if exist('TMIN','var') && ~isnan(TMIN), xl(1) = TMIN; end
        if exist('TMAX','var') && ~isnan(TMAX), xl(2) = TMAX; end
        xlim(xl);
        xlabel('Time [s]','interpreter','latex','fontsize',18);
        ylabel('$\Gamma_{x}$ [s$^{-1}$]','interpreter','latex','fontsize',18);
        lgd = legend('interpreter','latex','fontsize',15);
        title('Poloidal particle fluxes','interpreter','latex','fontsize',20);
        if SHOW_NAME
            text(0.98,0.04,RUN,'Units','normalized','HorizontalAlignment','right','VerticalAlignment','bottom', ...
                'interpreter','latex','FontSize',8,'BackgroundColor','white','EdgeColor','black');
        end
    
        subplot('position',[0.57 0.55 0.32 0.38]);
        plot(TIME_TRACES.timesa.value,abs(TIME_TRACES.feexip.value(i,:)),'linewidth',LINEWIDTH,'DisplayName',labels_poloidal_fluxes{i}{1}','color',COLORS_LIGHT{2}); hold on;
        plot(TIME_TRACES.timesa.value,abs(TIME_TRACES.feexap.value(i,:)),'linewidth',LINEWIDTH,'DisplayName',labels_poloidal_fluxes{i}{2},'color',COLORS_DARK{2}); hold on;
        xl = xlim; 
        if exist('TMIN','var') && ~isnan(TMIN), xl(1) = TMIN; end
        if exist('TMAX','var') && ~isnan(TMAX), xl(2) = TMAX; end
        xlim(xl);
        xlabel('Time [s]','interpreter','latex','fontsize',16);
        ylabel('$Q_{e,x}$ [W]','interpreter','latex','fontsize',16);
        lgd = legend('interpreter','latex','fontsize',15);
        title('Poloidal electron energy fluxes','interpreter','latex','fontsize',18);
        if SHOW_NAME
            text(0.98,0.04,RUN,'Units','normalized','HorizontalAlignment','right','VerticalAlignment','bottom', ...
                'interpreter','latex','FontSize',8,'BackgroundColor','white','EdgeColor','black');
        end
    
        subplot('position',[0.57 0.06 0.32 0.38]);
        plot(TIME_TRACES.timesa.value,abs(TIME_TRACES.feixip.value(i,:)),'linewidth',LINEWIDTH,'DisplayName',labels_poloidal_fluxes{i}{1},'color',COLORS_LIGHT{2}); hold on;
        plot(TIME_TRACES.timesa.value,abs(TIME_TRACES.feixap.value(i,:)),'linewidth',LINEWIDTH,'DisplayName',labels_poloidal_fluxes{i}{2},'color',COLORS_DARK{2}); hold on;
        xl = xlim; 
        if exist('TMIN','var') && ~isnan(TMIN), xl(1) = TMIN; end
        if exist('TMAX','var') && ~isnan(TMAX), xl(2) = TMAX; end
        xlim(xl);
        xlabel('Time [s]','interpreter','latex','fontsize',16);
        ylabel('$Q_{i,x}$ [W]','interpreter','latex','fontsize',16);
        lgd = legend('interpreter','latex','fontsize',15);
        title('Poloidal ion energy fluxes','interpreter','latex','fontsize',18);
        if SHOW_NAME
            text(0.98,0.04,RUN,'Units','normalized','HorizontalAlignment','right','VerticalAlignment','bottom', ...
                'interpreter','latex','FontSize',8,'BackgroundColor','white','EdgeColor','black');
        end

    end

    fprintf('Plot of poloidal fluxes prepared\n');

end

% Radial fluxes

if PLOT_RADIAL_FLUXES

    for i = 1:ncut

        fig = figure('windowstyle','docked','NumberTitle','off','Name',titles_radial_fluxes{i},'Visible',SHOW_FIGURE_status); figs = [figs, fig];
    
        subplot('position',[0.08 0.25 0.42 0.5]);
        plot(TIME_TRACES.timesa.value,abs(TIME_TRACES.fniyip.value(i,:)),'linewidth',LINEWIDTH,'DisplayName',labels_radial_fluxes{i}{1},'color',COLORS_LIGHT{1}); hold on;
        if not(strcmp(SIMULATION.geometry_type,'Limiter'))
            plot(TIME_TRACES.timesa.value,abs(TIME_TRACES.fniyap.value(i,:)),'linewidth',LINEWIDTH,'DisplayName',labels_radial_fluxes{i}{2},'color',COLORS_DARK{1}); hold on;
        end
        xl = xlim; 
        if exist('TMIN','var') && ~isnan(TMIN), xl(1) = TMIN; end
        if exist('TMAX','var') && ~isnan(TMAX), xl(2) = TMAX; end
        xlim(xl);
        xlabel('Time [s]','interpreter','latex','fontsize',18);
        ylabel('[$\Gamma_{y}$ s$^{-1}$]','interpreter','latex','fontsize',18);
        lgd = legend('interpreter','latex','fontsize',15);
        title('Radial particle fluxes','interpreter','latex','fontsize',20);
        if SHOW_NAME
            text(0.98,0.04,RUN,'Units','normalized','HorizontalAlignment','right','VerticalAlignment','bottom', ...
                'interpreter','latex','FontSize',8,'BackgroundColor','white','EdgeColor','black');
        end
    
        subplot('position',[0.57 0.55 0.32 0.38]);
        plot(TIME_TRACES.timesa.value,abs(TIME_TRACES.feeyip.value(i,:)),'linewidth',LINEWIDTH,'DisplayName',labels_radial_fluxes{i}{1},'color',COLORS_LIGHT{2}); hold on;
        if not(strcmp(SIMULATION.geometry_type,'Limiter'))
            plot(TIME_TRACES.timesa.value,abs(TIME_TRACES.feeyap.value(i,:)),'linewidth',LINEWIDTH,'DisplayName',labels_radial_fluxes{i}{2},'color',COLORS_DARK{2}); hold on;
        end
        xl = xlim; 
        if exist('TMIN','var') && ~isnan(TMIN), xl(1) = TMIN; end
        if exist('TMAX','var') && ~isnan(TMAX), xl(2) = TMAX; end
        xlim(xl);
        xlabel('Time [s]','interpreter','latex','fontsize',16);
        ylabel('$Q_{e,y}$ [W]','interpreter','latex','fontsize',16);
        lgd = legend('interpreter','latex','fontsize',15);
        title('Radial electron energy fluxes','interpreter','latex','fontsize',18);
        if SHOW_NAME
            text(0.98,0.04,RUN,'Units','normalized','HorizontalAlignment','right','VerticalAlignment','bottom', ...
                'interpreter','latex','FontSize',8,'BackgroundColor','white','EdgeColor','black');
        end
    
        subplot('position',[0.57 0.06 0.32 0.38]);
        plot(TIME_TRACES.timesa.value,abs(TIME_TRACES.feiyip.value(i,:)),'linewidth',LINEWIDTH,'DisplayName',labels_radial_fluxes{i}{1},'color',COLORS_LIGHT{2}); hold on;
        if not(strcmp(SIMULATION.geometry_type,'Limiter'))
            plot(TIME_TRACES.timesa.value,abs(TIME_TRACES.feiyap.value(i,:)),'linewidth',LINEWIDTH,'DisplayName',labels_radial_fluxes{i}{2},'color',COLORS_DARK{2}); hold on;
        end
        xl = xlim; 
        if exist('TMIN','var') && ~isnan(TMIN), xl(1) = TMIN; end
        if exist('TMAX','var') && ~isnan(TMAX), xl(2) = TMAX; end
        xlim(xl);
        xlabel('Time [s]','interpreter','latex','fontsize',16);
        ylabel('$Q_{i,y}$ [W]','interpreter','latex','fontsize',16);
        lgd = legend('interpreter','latex','fontsize',15);
        title('Radial ion energy fluxes','interpreter','latex','fontsize',18);
        if SHOW_NAME
            text(0.98,0.04,RUN,'Units','normalized','HorizontalAlignment','right','VerticalAlignment','bottom', ...
                'interpreter','latex','FontSize',8,'BackgroundColor','white','EdgeColor','black');
        end

    end

    fprintf('Plot of radial fluxes prepared\n');

end

%% PLOT INTEGRAL QUANTITIES

if PLOT_INTEGRAL_QUANTITIES

    fig = figure('windowstyle','docked','NumberTitle','off','Name','Integral quantities','Visible',SHOW_FIGURE_status); figs = [figs, fig];

    subplot('position',[0.05 0.25 0.42 0.5]);
    plot(TIME_TRACES.timesa.value,TIME_TRACES.tmne(1,:).value,'linewidth',LINEWIDTH,'color',COLORS{1});
    xl = xlim; 
    if exist('TMIN','var') && ~isnan(TMIN), xl(1) = TMIN; end
    if exist('TMAX','var') && ~isnan(TMAX), xl(2) = TMAX; end
    xlim(xl);
    xlabel('Time [s]','interpreter','latex','fontsize',18);
    title('Total number of particles','interpreter','latex','fontsize',20);
    if SHOW_NAME
        text(0.98,0.04,RUN,'Units','normalized','HorizontalAlignment','right','VerticalAlignment','bottom', ...
            'interpreter','latex','FontSize',8,'BackgroundColor','white','EdgeColor','black');
    end

    subplot('position',[0.53 0.25 0.42 0.5]);
    plot(TIME_TRACES.timesa.value,TIME_TRACES.tmte(1,:).value,'linewidth',LINEWIDTH,'DisplayName','Electron energy','color',COLORS_LIGHT{2}); hold on;
    plot(TIME_TRACES.timesa.value,TIME_TRACES.tmti(1,:).value,'linewidth',LINEWIDTH,'DisplayName','Ion energy','color',COLORS_DARK{2}); hold on;
    xl = xlim; 
    if exist('TMIN','var') && ~isnan(TMIN), xl(1) = TMIN; end
    if exist('TMAX','var') && ~isnan(TMAX), xl(2) = TMAX; end
    xlim(xl);
    xlabel('Time [s]','interpreter','latex','fontsize',18);
    ylabel('[eV]','interpreter','latex','fontsize',18);
    lgd = legend('interpreter','latex','fontsize',15);
    title('Total energy','interpreter','latex','fontsize',20);
    if SHOW_NAME
        text(0.98,0.04,RUN,'Units','normalized','HorizontalAlignment','right','VerticalAlignment','bottom', ...
            'interpreter','latex','FontSize',8,'BackgroundColor','white','EdgeColor','black');
    end

    fprintf('Plot of integral quantities prepared\n');

end

%% PRINT THE PLOTS

if PRINT_FIGURE
    print_plot(figs, [FIGURE_WIDTH FIGURE_HEIGHT], 'run_time_traces', FILE_FORMAT, FILE_RESOLUTION);
end

set(groot, 'defaultAxesYLimitMethod', originalYLimitMethod);

%% CLOSE SESSION AFTER CLOSING FIGURES IF CALLED AS FUNCTION

if nargin ~= 0
    for k = 1:numel(figs)
        waitfor(figs(k));
    end
end

end
