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

% Set plot dimensions
figs_print = gobjects(1, numel(figs));

for k = 1:numel(figs)
    oldFig = figs(k);
    
    % Create invisible figure with same size
    figs_print(k) = figure('Visible','off', ...
                        'NumberTitle','off', ...
                        'Name', oldFig.Name, ...
                        'Position', oldFig.Position, ...
                        'Color', oldFig.Color, ...
                        'Colormap', oldFig.Colormap);
    
    % Copy all children (axes, plots, etc.)
    copyobj(allchild(oldFig), figs_print(k));
    
    % Fix axes properties
    oldAxes = findall(oldFig,'Type','axes');
    newAxes = findall(figs_print(k),'Type','axes');
    
    for i = 1:numel(newAxes)
        props = {'FontSize','FontName','LineWidth','XLim','YLim','ZLim','XScale','YScale','ZScale'};
        for p = 1:numel(props)
            newAxes(i).(props{p}) = oldAxes(i).(props{p});
        end
        % Labels and title
        lbls = {'XLabel','YLabel','ZLabel','Title'};
        for l = lbls
            newAxes(i).(l{1}).FontSize = oldAxes(i).(l{1}).FontSize;
            newAxes(i).(l{1}).FontName = oldAxes(i).(l{1}).FontName;
        end
        % Legends
        oldLg = findall(oldAxes(i),'Type','Legend');
        newLg = findall(newAxes(i),'Type','Legend');
        for j = 1:numel(newLg)
            newLg(j).FontSize = oldLg(j).FontSize;
            newLg(j).FontName = oldLg(j).FontName;
        end
    end
    
end

if not(isnumeric(size(1)))
    error('Error: Specify the plot width as a number.')
end
if not(isnumeric(size(2)))
    error('Error: Specify the plot height as a number.')
end

for f = figs_print
    f.Position(3) = size(1);
    f.Position(4) = size(2);
end

% Find Ghostscript executable across different systems and architectures
gs_executable = '';
gs_failed_message = '';

% First try direct path check
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

% If not found, try 'which' command
if isempty(gs_executable)
    [status, result] = system('which gs');
    if status == 0 && ~isempty(strtrim(result))
        gs_executable = strtrim(result);
    end
end

figs_print = figs_print(:)';  % ensure row vector
plots_folder = pwd;

format = lower(format);

% PDF: multipage
if strcmp(format,'pdf')

    outfile = fullfile(plots_folder, [name '.' format]);
    for k = 1:numel(figs_print)
        f = figs_print(k);
        f.Renderer = 'painters';
        % Set paper size to match figure size
        f.PaperPositionMode = 'auto';
        f.PaperUnits = 'inches';
        f.PaperSize = [f.Position(3) f.Position(4)] / get(0, 'ScreenPixelsPerInch');
        appendFlag = (k > 1);
        exportgraphics(f, outfile, 'ContentType','vector', 'Append', appendFlag);
    end

% EPS: single file only (EPS doesn't support multi-page)
elseif strcmp(format, 'eps')

    if numel(figs_print) > 1
        for k = 1:numel(figs_print)
            f = figs_print(k);
            f.Renderer = 'painters';
            % Set paper size to match figure size
            f.PaperPositionMode = 'auto';
            f.PaperUnits = 'inches';
            f.PaperSize = [f.Position(3) f.Position(4)] / get(0, 'ScreenPixelsPerInch');
            filename = sprintf('%s_%d.%s', name, k, format);
            outfile = fullfile(plots_folder, filename);
            exportgraphics(f, outfile, 'ContentType','vector');
        end
    else
        % Single figure EPS
        f = figs_print(1);
        f.Renderer = 'painters';
        % Set paper size to match figure size
        f.PaperPositionMode = 'auto';
        f.PaperUnits = 'inches';
        f.PaperSize = [f.Position(3) f.Position(4)] / get(0, 'ScreenPixelsPerInch');
        outfile = fullfile(plots_folder, [name '.' format]);
        exportgraphics(f, outfile, 'ContentType','vector');
    end

% PS: save individually then combine into multi-page PS
elseif strcmp(format, 'ps')

    tempFiles = cell(1,numel(figs_print));
    for k = 1:numel(figs_print)
        f = figs_print(k);
        f.Renderer = 'painters';
        f.PaperPositionMode = 'auto';
        f.PaperUnits = 'inches';
        f.PaperSize = [f.Position(3) f.Position(4)] / get(0, 'ScreenPixelsPerInch');
        tempFiles{k} = fullfile(plots_folder, sprintf('temp_%d.eps', k));
        exportgraphics(f, tempFiles{k}, 'ContentType','vector');
    end
    
    gs_failed = false;
    
    if isempty(gs_executable)
        gs_failed = true;
    else
        % Combine into multi-page PS file using Ghostscript
        outfile = fullfile(plots_folder, [name '.ps']);
        
        quotedFiles = cellfun(@(x) sprintf('"%s"', x), tempFiles, 'UniformOutput', false);
        fileList = strjoin(quotedFiles, ' ');
        
        gsCmd = sprintf('"%s" -dBATCH -dNOPAUSE -dNOSAFER -dEPSCrop -sDEVICE=ps2write -sOutputFile="%s" %s', ...
                        gs_executable, outfile, fileList);
        
        [status, cmdout] = system(gsCmd);
        
        if status ~= 0
            gs_failed = true;
        else
            for k = 1:numel(tempFiles)
                if exist(tempFiles{k}, 'file')
                    try
                        delete(tempFiles{k});
                    catch
                    end
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
        f = figs_print(k);
        f.Renderer = 'painters';  % vector still okay for high-quality
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
        exportgraphics(f, outfile, opts{:});
    end

else

    error('Error: Printing plot in .%s format not supported',format);

end

fprintf('Figure(s) saved in .%s format%s.\n', format, gs_failed_message);

end
