function profileplot(x, profile, varargin)

% PROFILEPLOT plots one profile (optionally with past profiles, transport
%    coefficients, and experimental data) on the current axes and finalizes
%    the subplot.
%
%   profileplot(x, profile, 'Name', Value, ...)
%
%   Required:
%       x         - Radial coordinate vector (1D)
%       profile   - Latest profile vector (1D) to plot
%
%   Optional Name-Value pairs for past profiles overlay:
%       'PastProfiles'         - Matrix whose columns are past profile snapshots
%                                (default: [])
%       'PastColors'           - Cell array of RGB(A) color vectors for past profiles
%                                (default: {})
%       'PastLineWidth'        - Line width for past profiles (default: 0.8)
%       'PastLineStyle'        - Line style for past profiles (default: '-')
%       'PlotFrequency'        - Plot 1 out of every PlotFrequency past profiles
%                                (default: 1)
%
%   Optional Name-Value pairs for transport coefficient overlay:
%       'TransportProfile'     - Transport coefficient profile vector (default: [])
%       'TransportColor'       - RGB color for transport line (default: [])
%       'TransportLineWidth'   - Line width for transport line (default: 2.2)
%       'TransportLineStyle'   - Line style for transport line (default: '-.')
%       'TransportYLabel'      - Y-axis label for transport axis (default: '')
%       'ScaleTransport'       - Scale for transport axis: 'linear' or 'logarithmic'
%                                (default: 'logarithmic')
%
%   Optional Name-Value pairs for experimental data overlay:
%       'ExpData'              - Cell array of experimental data structs, each with
%                                fields: .rhop (NxM), .values (NxM),
%                                .values_unc (NxM, optional), .name (char)
%                                (default: {})
%       'ExpDataTypes'         - Cell array of strings ('scatter' or 'line') for
%                                each element in ExpData (default: all 'scatter')
%       'ExpDataColors'        - Cell array of RGB colors for each element in ExpData
%                                (default: auto from load_colors)
%       'ExpMarker'            - Marker for scatter exp data (default: 'd')
%       'ExpMarkerSize'        - Marker size for scatter exp data (default: 25)
%       'ExpProfilesMarker'    - Marker for line exp data (default: '^')
%       'ExpProfilesMarkerSize'- Marker size for line exp data (default: 12)
%       'ExpProfilesLineWidth' - Line width for line exp data (default: 1.5)
%       'ExpProfilesLineStyle' - Line style for line exp data (default: 'none')
%       'ExpProfilesCapSize'   - Cap size for errorbars (default: 12)
%
%   Optional Name-Value pairs for main profile appearance:
%       'ProfileColor'         - RGB color for the latest profile (default: [0 0 0])
%       'ProfileLineWidth'     - Line width for the latest profile (default: 4)
%       'ProfileLineStyle'     - Line style for the latest profile (default: '-')
%       'ProfileDisplayName'   - Display name for the latest profile (default: 'Current profile')
%
%   Optional Name-Value pairs for subplot finalization:
%       'ScaleProfiles'        - Scale for profile axis: 'linear' or 'logarithmic'
%                                (default: 'linear')
%       'XMIN'                 - Minimum x-axis value (default: NaN = auto from data)
%       'XMAX'                 - Maximum x-axis value (default: NaN = auto from data)
%       'YLimStyle'            - Y-axis limit style: 'tickaligned', 'tight',
%                                'padded', or 'custom' (default: 'custom')
%       'XLabel'               - X-axis label string (default: '')
%       'YLabel'               - Y-axis label string (default: '')
%       'Title'                - Subplot title string (default: '')
%       'LabelFontSize'        - Font size for axis labels (default: 18)
%       'TitleFontSize'        - Font size for title (default: 20)
%       'LegendFontSize'       - Font size for legend (default: 15)
%       'LegendLocation'       - Legend location (default: 'best')
%       'PlotLCFS'             - Whether to draw LCFS line (default: true)
%       'LCFSPosition'         - x-position of the LCFS line (default: 1)
%       'ShowName'             - Whether to show run name annotation (default: false)
%       'RunName'              - Run name string for annotation (default: '')

%% PARSE INPUTS

p = inputParser;
p.addRequired('x');
p.addRequired('profile');

% Past profiles
p.addParameter('PastProfiles', []);
p.addParameter('PastColors', {});
p.addParameter('PastLineWidth', 0.8, @isnumeric);
p.addParameter('PastLineStyle', '-', @ischar);
p.addParameter('PlotFrequency', 1, @isnumeric);

% Transport
p.addParameter('TransportProfile', []);
p.addParameter('TransportColor', []);
p.addParameter('TransportLineWidth', 2.2, @isnumeric);
p.addParameter('TransportLineStyle', '-.', @ischar);
p.addParameter('TransportYLabel', '', @ischar);
p.addParameter('ScaleTransport', 'logarithmic', @ischar);

% Experimental data
p.addParameter('ExpData', {});
p.addParameter('ExpDataTypes', {});
p.addParameter('ExpDataColors', {});
p.addParameter('ExpMarker', 'd');
p.addParameter('ExpMarkerSize', 25, @isnumeric);
p.addParameter('ExpProfilesMarker', '^');
p.addParameter('ExpProfilesMarkerSize', 12, @isnumeric);
p.addParameter('ExpProfilesLineWidth', 1.5, @isnumeric);
p.addParameter('ExpProfilesLineStyle', 'none', @ischar);
p.addParameter('ExpProfilesCapSize', 12, @isnumeric);

% Main profile appearance
p.addParameter('ProfileColor', [0 0 0], @isnumeric);
p.addParameter('ProfileLineWidth', 4, @isnumeric);
p.addParameter('ProfileLineStyle', '-', @ischar);
p.addParameter('ProfileDisplayName', 'Current profile', @ischar);

% Subplot finalization
p.addParameter('ScaleProfiles', 'linear', @ischar);
p.addParameter('XMIN', nan, @isnumeric);
p.addParameter('XMAX', nan, @isnumeric);
p.addParameter('YLimStyle', 'custom');
p.addParameter('XLabel', '', @ischar);
p.addParameter('YLabel', '', @ischar);
p.addParameter('Title', '', @ischar);
p.addParameter('LabelFontSize', 18, @isnumeric);
p.addParameter('TitleFontSize', 20, @isnumeric);
p.addParameter('LegendFontSize', 15, @isnumeric);
p.addParameter('LegendLocation', 'best', @ischar);
p.addParameter('PlotLCFS', true);
p.addParameter('LCFSPosition', 1, @isnumeric);
p.addParameter('ShowName', false);
p.addParameter('RunName', '', @ischar);

p.parse(x, profile, varargin{:});
opts = p.Results;

hold on;

%% PLOT PAST PROFILES

all_data = opts.profile;

if ~isempty(opts.PastProfiles)
    nsnaps = size(opts.PastProfiles, 2);
    k = 1;
    for i = 1:opts.PlotFrequency:nsnaps
        col = opts.PastColors{k};
        plot(opts.x, opts.PastProfiles(:,i), ...
            'linewidth', opts.PastLineWidth, ...
            'HandleVisibility', 'off', ...
            'color', col, ...
            'linestyle', opts.PastLineStyle, ...
            'marker', 'none');
        k = k + 1;
    end
    all_data = [all_data; reshape(opts.PastProfiles, [], 1)];
end

%% PLOT EXPERIMENTAL DATA

if ~isempty(opts.ExpData)

    nexp = numel(opts.ExpData);

    % Default types: all scatter
    exp_types = opts.ExpDataTypes;
    if isempty(exp_types)
        exp_types = repmat({'scatter'}, 1, nexp);
    end

    % Default colors: auto from load_colors
    exp_colors = opts.ExpDataColors;
    if isempty(exp_colors)
        exp_colors = load_colors('default', nexp, 'rgb');
    end

    for i = 1:nexp

        ed = opts.ExpData{i};
        col = exp_colors{i};

        if strcmp(exp_types{i}, 'scatter')
            scatter(ed.rhop(1,:), ed.values(1,:), ...
                opts.ExpMarkerSize, col, 'filled', opts.ExpMarker, ...
                'DisplayName', ed.name);
            if size(ed.values, 1) > 1
                for j = 2:size(ed.values, 1)
                    scatter(ed.rhop(j,:), ed.values(j,:), ...
                        opts.ExpMarkerSize, col, 'filled', opts.ExpMarker, ...
                        'HandleVisibility', 'off');
                end
            end

        elseif strcmp(exp_types{i}, 'line')
            errorbar(mean(ed.rhop, 1), ...
                mean(ed.values, 1), mean(ed.values_unc, 1), ...
                'CapSize', opts.ExpProfilesCapSize, ...
                'Color', col, ...
                'MarkerFaceColor', 'auto', ...
                'Marker', opts.ExpProfilesMarker, ...
                'MarkerSize', opts.ExpProfilesMarkerSize, ...
                'LineWidth', opts.ExpProfilesLineWidth, ...
                'LineStyle', opts.ExpProfilesLineStyle, ...
                'DisplayName', ed.name);
        end

    end
end

%% PLOT MAIN (LATEST) PROFILE

plot(opts.x, opts.profile, ...
    'linewidth', opts.ProfileLineWidth, ...
    'DisplayName', opts.ProfileDisplayName, ...
    'color', opts.ProfileColor, ...
    'linestyle', opts.ProfileLineStyle);

%% SET PROFILE AXIS SCALE

if strcmp(opts.ScaleProfiles, 'logarithmic')
    set(gca, 'Yscale', 'log');
end

%% PLOT TRANSPORT COEFFICIENT ON SECONDARY AXIS

if ~isempty(opts.TransportProfile) && ~isempty(opts.TransportColor)
    yyaxis right;
    if strcmp(opts.ScaleTransport, 'logarithmic')
        set(gca, 'Yscale', 'log');
    end
    plot(opts.x, opts.TransportProfile, ...
        'Color', opts.TransportColor, ...
        'linewidth', opts.TransportLineWidth, ...
        'LineStyle', opts.TransportLineStyle, ...
        'HandleVisibility', 'off');
    if ~isempty(opts.TransportYLabel)
        ylabel(opts.TransportYLabel, 'interpreter', 'latex', 'fontsize', opts.LabelFontSize);
    end
    ax = gca;
    ax.YAxis(2).Color = opts.TransportColor;
    ylim([0.02, 20]);
    yyaxis left;
end

%% FINALIZE SUBPLOT

% LCFS line
if opts.PlotLCFS
    xline(opts.LCFSPosition, 'linestyle', '--', 'linewidth', 0.4, 'HandleVisibility', 'off');
end

box on;

% X limits
xl = [opts.x(1), opts.x(end)];
if ~isnan(opts.XMIN), xl(1) = opts.XMIN; end
if ~isnan(opts.XMAX), xl(2) = opts.XMAX; end
xlim(xl);

% Y limits
if strcmp(opts.YLimStyle, 'custom')
    if strcmp(opts.ScaleProfiles, 'linear')
        max_val = max(all_data(:));
        if ~isnan(max_val) && max_val > 0
            ylim([0, max_val * 1.1]);
        end
    end
    % For logarithmic scale in custom mode, let MATLAB auto-determine
else
    set(gca, 'YLimitMethod', opts.YLimStyle);
end

% Labels
if ~isempty(opts.XLabel)
    xlabel(opts.XLabel, 'interpreter', 'latex', 'fontsize', opts.LabelFontSize);
end
if ~isempty(opts.YLabel)
    ylabel(opts.YLabel, 'interpreter', 'latex', 'fontsize', opts.LabelFontSize);
end

% Legend and title
legend('interpreter', 'latex', 'fontsize', opts.LegendFontSize, 'location', opts.LegendLocation);
title(opts.Title, 'interpreter', 'latex', 'fontsize', opts.TitleFontSize);

% Run name annotation
if opts.ShowName
    text(0.98, 0.04, opts.RunName, 'Units', 'normalized', ...
        'HorizontalAlignment', 'right', 'VerticalAlignment', 'bottom', ...
        'interpreter', 'latex', 'FontSize', 8, ...
        'BackgroundColor', 'white', 'EdgeColor', 'black');
end

end
