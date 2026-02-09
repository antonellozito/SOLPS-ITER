function timeplot(time, traces, varargin)

% TIMEPLOT plots one or more time traces on the current axes and finalizes the subplot.
%
%   timeplot(time, traces, 'Name', Value, ...)
%
%   Required:
%       time      - Time vector (1D)
%       traces    - Struct array of traces to plot, each with fields:
%                       .data          - Data vector (1D) to plot
%                       .color         - Line color (RGB triplet)
%                       .display_name  - Legend entry ('' for no legend entry)
%                   Optional fields (defaults applied if missing):
%                       .line_style    - Line style (default: '-')
%                       .use_abs       - Plot absolute values (default: false)
%
%   Optional Name-Value pairs for original data overlay:
%       'OriginalTime'           - Time vector for original (un-averaged) data (default: [])
%       'OriginalTraces'         - Cell array (same length as traces) of original data.
%                                  Each element is a cell array of vectors to overlay.
%                                  (default: {})
%
%   Optional Name-Value pairs for subplot finalization:
%       'LineWidth'      - Line width for main traces (default: 1.5)
%       'TMIN'           - Minimum x-axis time (default: NaN = auto)
%       'TMAX'           - Maximum x-axis time (default: NaN = auto)
%       'XLabel'         - X-axis label string (default: 'Time [s]')
%       'YLabel'         - Y-axis label string (default: '', meaning no ylabel)
%       'Title'          - Subplot title string (default: '')
%       'LabelFontSize'  - Font size for axis labels (default: 18)
%       'TitleFontSize'  - Font size for title (default: 20)
%       'ShowName'       - Whether to show run name annotation (default: false)
%       'RunName'        - Run name string for annotation (default: '')
%
%   Helper entry points for building the 'OriginalTraces' input:
%       timeplot.get_original_time(HAS_AVG, PLOT_ORIG, TT_ORIG)
%       timeplot.get_original_data(HAS_AVG, PLOT_ORIG, TT_ORIG, field, idx)
%       timeplot.get_original_data_3d(HAS_AVG, PLOT_ORIG, TT_ORIG, field, i1, i2)
%
%   Example (single trace, no original data):
%       timeplot(t, struct('data',ne,'color',[0 0 1],'display_name','Sep.'), ...
%           'YLabel','$n_e$ [m$^{-3}$]', 'Title','Electron density');
%
%   Example (multiple traces with original overlay):
%       traces(1) = struct('data',ne_sep,'color',col_light,'display_name','Sep.');
%       traces(2) = struct('data',ne_max,'color',col_light,'display_name','Max.','line_style',':');
%       orig{1} = get_original_data(...);
%       orig{2} = get_original_data(...);
%       timeplot(t, traces, 'OriginalTime',t_orig, 'OriginalTraces',orig, ...
%           'YLabel','$n_e$', 'Title','Density');

%% PARSE INPUTS

p = inputParser;
p.addRequired('time');
p.addRequired('traces');
p.addParameter('OriginalTime', []);
p.addParameter('OriginalTraces', {});
p.addParameter('LineWidth', 1.5, @isnumeric);
p.addParameter('TMIN', nan, @isnumeric);
p.addParameter('TMAX', nan, @isnumeric);
p.addParameter('XLabel', 'Time [s]', @ischar);
p.addParameter('YLabel', '', @ischar);
p.addParameter('Title', '', @ischar);
p.addParameter('LabelFontSize', 18, @isnumeric);
p.addParameter('TitleFontSize', 20, @isnumeric);
p.addParameter('ShowName', false);
p.addParameter('RunName', '', @ischar);
p.parse(time, traces, varargin{:});
opts = p.Results;

ntrace = numel(traces);

%% PLOT EACH TIME TRACE

for k = 1:ntrace

    tr = traces(k);

    % Defaults for optional trace fields
    if ~isfield(tr, 'line_style') || isempty(tr.line_style)
        tr.line_style = '-';
    end
    if ~isfield(tr, 'use_abs') || isempty(tr.use_abs)
        tr.use_abs = false;
    end

    % Transform function (identity or abs)
    if tr.use_abs
        xfm = @(x) abs(x);
    else
        xfm = @(x) x;
    end

    % Plot original (un-averaged) data if provided for this trace
    if ~isempty(opts.OriginalTraces) && ~isempty(opts.OriginalTime) ...
            && k <= numel(opts.OriginalTraces) && ~isempty(opts.OriginalTraces{k})
        orig_data = opts.OriginalTraces{k};
        for j = 1:length(orig_data)
            plot(opts.OriginalTime, xfm(orig_data{j}), ...
                'linewidth', opts.LineWidth/3, ...
                'HandleVisibility', 'off', ...
                'color', tr.color, ...
                'linestyle', tr.line_style); hold on;
        end
    end

    % Plot main trace
    if isempty(tr.display_name)
        plot(opts.time, xfm(tr.data), ...
            'linewidth', opts.LineWidth, ...
            'color', tr.color, ...
            'linestyle', tr.line_style); hold on;
    else
        plot(opts.time, xfm(tr.data), ...
            'linewidth', opts.LineWidth, ...
            'DisplayName', tr.display_name, ...
            'color', tr.color, ...
            'linestyle', tr.line_style); hold on;
    end

end

%% FINALIZE SUBPLOTS

box on;

xl = xlim;
if ~isnan(opts.TMIN), xl(1) = opts.TMIN; else, xl(1) = time(1); end
if ~isnan(opts.TMAX), xl(2) = opts.TMAX; else, xl(2) = time(end); end
xlim(xl);

xlabel(opts.XLabel, 'interpreter', 'latex', 'fontsize', opts.LabelFontSize);
if ~isempty(opts.YLabel)
    ylabel(opts.YLabel, 'interpreter', 'latex', 'fontsize', opts.LabelFontSize);
end
legend('interpreter', 'latex', 'fontsize', 15);
title(opts.Title, 'interpreter', 'latex', 'fontsize', opts.TitleFontSize);

if opts.ShowName
    text(0.98, 0.04, opts.RunName, 'Units', 'normalized', ...
        'HorizontalAlignment', 'right', 'VerticalAlignment', 'bottom', ...
        'interpreter', 'latex', 'FontSize', 8, ...
        'BackgroundColor', 'white', 'EdgeColor', 'black');
end

end
