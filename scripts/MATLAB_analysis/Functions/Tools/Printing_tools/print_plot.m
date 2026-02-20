function print_plot(figs, size, name, format, resolution)

% print_plot(figs, name, format, resolution) saves figures to folder. 
% - PDF: all figures in a single file (multipage)
% - PS: combined into one multi-page file after creation
% - EPS: single-page format (multiple figures saved separately)
% - PNG/JPG: each figure is saved separately
%
% Usage:
%   print_plot(figs, [800,600], 'figure', 'pdf', 'vector')
%
% name: base name for files (default: 'figure')
% format: 'pdf','eps','ps','png','jpg' (default: 'pdf')
% resolution: 'vector' or numeric DPI in the format e.g. 'r600' (default: 'vector')

% Defaults
if nargin < 5 || isempty(resolution), resolution = 'vector'; end
if nargin < 4 || isempty(format), format = 'pdf'; end
if nargin < 3 || isempty(name), name = 'figure'; end
if nargin < 2 || isempty(size), size = [800,600]; end
if nargin < 1 || isempty(figs)
    error('Error: Select at least one figure.');
end

if not(isnumeric(size(1)))
    error('Error: Specify the plot width as a number.')
end
if not(isnumeric(size(2)))
    error('Error: Specify the plot height as a number.')
end

% Prepare figures: try copyobj, fall back to original
figs_print = gobjects(1, numel(figs));
used_original = false(1, numel(figs));

% Target paper size in inches
ppi = get(0, 'ScreenPixelsPerInch');
paperW = size(1) / ppi;
paperH = size(2) / ppi;

for k = 1:numel(figs)
    oldFig = figs(k);
    
    try
        % Try creating invisible copy (works for simple axes)
        newFig = figure('Visible','off', ...
                        'NumberTitle','off', ...
                        'Name', oldFig.Name, ...
                        'Position', oldFig.Position, ...
                        'Color', oldFig.Color, ...
                        'Colormap', oldFig.Colormap);
        
        copyobj(allchild(oldFig), newFig);
        
        % Fix axes properties
        oldAxes = findall(oldFig,'Type','axes');
        newAxes = findall(newFig,'Type','axes');
        
        for i = 1:numel(newAxes)
            props = {'FontSize','FontName','LineWidth','XLim','YLim','ZLim','XScale','YScale','ZScale'};
            for p = 1:numel(props)
                newAxes(i).(props{p}) = oldAxes(i).(props{p});
            end
            lbls = {'XLabel','YLabel','ZLabel','Title'};
            for l = lbls
                newAxes(i).(l{1}).FontSize = oldAxes(i).(l{1}).FontSize;
                newAxes(i).(l{1}).FontName = oldAxes(i).(l{1}).FontName;
            end
            oldLg = findall(oldAxes(i),'Type','Legend');
            newLg = findall(newAxes(i),'Type','Legend');
            for j = 1:numel(newLg)
                newLg(j).FontSize = oldLg(j).FontSize;
                newLg(j).FontName = oldLg(j).FontName;
            end
        end
        
        % Set size on the copy (safe — it's invisible and not docked)
        newFig.Position(3) = size(1);
        newFig.Position(4) = size(2);
        figs_print(k) = newFig;
        
    catch
        % Fallback: use original figure, do NOT touch Position
        figs_print(k) = oldFig;
        used_original(k) = true;
    end
end

% Find Ghostscript executable
gs_executable = '';
gs_failed_message = '';

gs_paths = {
    '/usr/bin/gs',...
    '/opt/homebrew/bin/gs',...
    '/usr/local/bin/gs',...
    '/bin/gs',...
    '/sw/bin/gs',...
    '/opt/local/bin/gs'};

for i = 1:length(gs_paths)
    if exist(gs_paths{i}, 'file') == 2
        gs_executable = gs_paths{i};
        break;
    end
end

if isempty(gs_executable)
    [status, result] = system('which gs');
    if status == 0 && ~isempty(strtrim(result))
        gs_executable = strtrim(result);
    end
end

figs_print = figs_print(:)';
plots_folder = pwd;
format = lower(format);

% Helper: configure paper properties for a figure before export.
% For copied figures, Position is already set so paper follows it.
% For original (fallback) figures, we set paper size directly to the
% desired output size WITHOUT touching Position (which would undock).
    function configure_paper(f, idx)
        f.Renderer = 'painters';
        f.PaperUnits = 'inches';
        if used_original(idx)
            % Don't touch Position — set paper size/position directly
            f.PaperPositionMode = 'manual';
            f.PaperSize = [paperW, paperH];
            f.PaperPosition = [0, 0, paperW, paperH];
        else
            % Copied figure: Position already set to desired size
            f.PaperPositionMode = 'auto';
            f.PaperSize = [f.Position(3) f.Position(4)] / ppi;
        end
    end

% PDF: multipage
if strcmp(format,'pdf')

    outfile = fullfile(plots_folder, [name '.' format]);
    for k = 1:numel(figs_print)
        configure_paper(figs_print(k), k);
        appendFlag = (k > 1);
        exportgraphics(figs_print(k), outfile, 'ContentType','vector', 'Append', appendFlag);
    end

% EPS: single file only
elseif strcmp(format, 'eps')

    if numel(figs_print) > 1
        for k = 1:numel(figs_print)
            configure_paper(figs_print(k), k);
            filename = sprintf('%s_%d.%s', name, k, format);
            outfile = fullfile(plots_folder, filename);
            exportgraphics(figs_print(k), outfile, 'ContentType','vector');
        end
    else
        configure_paper(figs_print(1), 1);
        outfile = fullfile(plots_folder, [name '.' format]);
        exportgraphics(figs_print(1), outfile, 'ContentType','vector');
    end

% PS: save individually then combine
elseif strcmp(format, 'ps')

    tempFiles = cell(1,numel(figs_print));
    for k = 1:numel(figs_print)
        configure_paper(figs_print(k), k);
        tempFiles{k} = fullfile(plots_folder, sprintf('temp_%d.eps', k));
        exportgraphics(figs_print(k), tempFiles{k}, 'ContentType','vector');
    end
    
    gs_failed = false;
    
    if isempty(gs_executable)
        gs_failed = true;
    else
        outfile = fullfile(plots_folder, [name '.ps']);
        quotedFiles = cellfun(@(x) sprintf('"%s"', x), tempFiles, 'UniformOutput', false);
        fileList = strjoin(quotedFiles, ' ');
        gsCmd = sprintf('"%s" -dBATCH -dNOPAUSE -dNOSAFER -dEPSCrop -sDEVICE=ps2write -sOutputFile="%s" %s', ...
                        gs_executable, outfile, fileList);
        [status, ~] = system(gsCmd);
        if status ~= 0
            gs_failed = true;
        else
            for k = 1:numel(tempFiles)
                if exist(tempFiles{k}, 'file')
                    try delete(tempFiles{k}); catch, end
                end
            end
        end
    end
    
    if gs_failed
        for k = 1:numel(tempFiles)
            if numel(figs_print) > 1
                newname = fullfile(plots_folder, sprintf('%s_%d.eps', name, k));
            else
                newname = fullfile(plots_folder, [name '.eps']);
            end
            movefile(tempFiles{k}, newname);
        end
        format = 'eps';
        gs_failed_message = ' (printing to .ps failed)';
    end

% PNG/JPG: separate files
elseif strcmp(format, 'png') || strcmp(format, 'jpg')

    for k = 1:numel(figs_print)
        configure_paper(figs_print(k), k);
        filename = sprintf('%s_%d.%s', name, k, format);
        outfile = fullfile(plots_folder, filename);
        opts = {};
        if strcmpi(resolution,'vector')
            opts = {'ContentType','vector'};
        elseif ischar(resolution) && ~isempty(regexp(resolution,'^r\d+$','once'))
            opts = {'Resolution',resolution(2:end)};
        else
            error('Error: File resolution should be ''vector'' or a DPI in the format e.g. ''r600''');
        end
        exportgraphics(figs_print(k), outfile, opts{:});
    end

else
    error('Error: Printing plot in .%s format not supported',format);
end

fprintf('Figure(s) saved in .%s format%s.\n', format, gs_failed_message);

% Cleanup: close copies, restore paper props on originals
for k = 1:numel(figs_print)
    if used_original(k)
        % Reset paper mode so it doesn't affect the figure going forward
        figs_print(k).PaperPositionMode = 'auto';
    else
        close(figs_print(k));
    end
end

end
