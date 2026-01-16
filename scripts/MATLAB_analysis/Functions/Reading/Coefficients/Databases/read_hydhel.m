function database = read_hydhel(hydhel_datafile)
    % Parse HYDHEL database
    % Returns a struct containing parsed HYDHEL reactions

    warnState = warning('off','all');
    cleanupObj = onCleanup(@() warning(warnState));
    
    database = struct();
    report = 'HYDHEL';
    
    % Open and read file
    fid = fopen(hydhel_datafile, 'r', 'n', 'UTF-8');
    if fid == -1
        error('Error: Cannot open file: %s', hydhel_datafile);
    end
    hh = fread(fid, '*char')';
    fclose(fid);
    
    % Split by sections
    sections = strsplit(hh, '\section{H.');
    headers = struct();
    for i = 2:length(sections)
        h = sections{i};
        if length(h) >= 2
            header_num = str2double(h(1:2));
            if ~isnan(header_num)
                headers.(sprintf('H%d', header_num)) = h;
            end
        end
    end
    
    % Process sections H1, H2, H8 (single polynomial fits)
    for ih = [1, 2, 8]
        if isfield(headers, sprintf('H%d', ih))
            subsections = strsplit(headers.(sprintf('H%d', ih)), '\subsection{');
            
            for s = 2:length(subsections)
                try
                    S = subsections{s};
                    lines = strsplit(S, newline);
                    
                    if length(lines) >= 2
                        line2 = lines{2};
                        if startsWith(strtrim(line2), 'Reaction')
                            tokens = strsplit(line2);
                            if length(tokens) >= 2
                                nam = tokens{2};
                            else
                                continue;
                            end
                            
                            % Extract latex
                            latex_parts = strsplit(line2, '$');
                            if length(latex_parts) >= 2
                                latex = strtrim(latex_parts{2});
                            else
                                latex = '';
                            end
                            
                            reaction = struct();
                            reaction.report = report;
                            reaction.header = ih;
                            reaction.name = nam;
                            reaction.latex = latex;
                            
                            if ih == 1
                                reaction.symbol = '$\sigma$';
                                reaction.unit = 'm$^2$';
                                reaction.parameters = 'E';
                                reaction.factor = 1e-4;
                                varname = 'a';
                            elseif ih == 2
                                reaction.symbol = '$\langle\sigma\cdot v\rangle$';
                                reaction.unit = 'm$^3$ s$^{-1}$';
                                reaction.parameters = 'T';
                                reaction.factor = 1e-6;
                                varname = 'b';
                            elseif ih == 8
                                reaction.symbol = '$\langle\sigma\cdot v\cdot E\rangle$';
                                reaction.unit = 'm$^3$ eV s$^{-1}$';
                                reaction.parameters = 'T';
                                reaction.factor = 1e-6;
                                varname = 'h';
                            end
                            
                            % Extract data block
                            block = extract_data_block(S, true, {',', ' '});
                            
                            % Try to read coefficients if block exists
                            if ~isempty(block)
                                coeffs = read_coefficients1D(block, varname);
                                if ~isempty(coeffs)
                                    reaction.coefficients = coeffs;
                                end
                                reaction = read_variables(block, reaction, get_vnfdEnergy());
                            end
                            
                            % Add reaction to database even if no coefficients
                            key = sprintf('H_%d_%s', ih, strrep(nam, '.', '_'));
                            database.(key) = reaction;
                        end
                    end
                catch ME
                    % Skip this subsection if error
                end
            end
        end
    end
    
    % Process section H3 (double polynomial fits)
    ih = 3;
    if isfield(headers, 'H3')
        subsections = strsplit(headers.H3, '\subsection{');
        
        for s = 2:length(subsections)
            try
                S = subsections{s};
                lines = strsplit(S, newline);
                
                if length(lines) >= 2
                    line2 = lines{2};
                    if startsWith(strtrim(line2), 'Reaction')
                        tokens = strsplit(line2);
                        if length(tokens) >= 2
                            nam = tokens{2};
                        else
                            continue;
                        end
                        
                        % Extract latex
                        latex_parts = strsplit(line2, '$');
                        if length(latex_parts) >= 2
                            latex = strtrim(latex_parts{2});
                        else
                            latex = '';
                        end
                        
                        reaction = struct();
                        reaction.report = report;
                        reaction.header = ih;
                        reaction.name = nam;
                        reaction.latex = latex;
                        reaction.symbol = '$\langle\sigma\cdot v\rangle$';
                        reaction.unit = 'm$^3$ s$^{-1}$';
                        reaction.parameters = 'E,T';
                        reaction.factor = 1.0e-6;
                        
                        % Extract data block
                        block = extract_data_block(S, true, {',', ' '});
                        
                        % Try to read coefficients if block exists
                        if ~isempty(block)
                            coeffs = read_coefficients2D(block);
                            if ~isempty(coeffs)
                                reaction.coefficients = coeffs';
                            end
                            reaction = read_variables(block, reaction, get_vnfdEnergy());
                        end
                        
                        % Add reaction to database even if no coefficients
                        key = sprintf('H_%d_%s', ih, strrep(nam, '.', '_'));
                        database.(key) = reaction;
                    end
                end
            catch ME
                % Skip this subsection if error
            end
        end
    end
end

function block = extract_data_block(s, do_lower, repl)
    % Extract data block from verbatim environment
    
    % Check for analytic formula messages
    if contains(s, 'An analytic formula is given in the text.') || ...
       contains(s, 'See text for analytic formulas.')
        block = [];
        return;
    end
    
    begin_tag = '\begin{verbatim}';
    end_tag = '\end{verbatim}';
    
    % Check if we found exactly one of each
    begin_count = length(strfind(s, begin_tag));
    end_count = length(strfind(s, end_tag));
    
    if begin_count ~= 1 || end_count ~= 1
        block = [];
        return;
    end
    
    % Extract block between tags
    idx_begin = strfind(s, begin_tag);
    idx_end = strfind(s, end_tag);
    
    if isempty(idx_begin) || isempty(idx_end) || idx_end <= idx_begin
        block = [];
        return;
    end
    
    % Extract the content between the tags
    start_pos = idx_begin + length(begin_tag);
    end_pos = idx_end - 1;
    
    block = s(start_pos:end_pos);
    
    % Apply lowercase if requested
    if nargin >= 2 && do_lower
        block = lower(block);
    end
    
    % Apply replacements if provided
    if nargin >= 3 && ~isempty(repl)
        for i = 1:size(repl, 1)
            block = strrep(block, repl{i,1}, repl{i,2});
        end
    end
end

function D = read_coefficients1D(block, varname)
    % Read 1D coefficients from block
    
    D = nan(10, 1);
    for i = 0:9
        sc = sprintf('%s%d ', varname, i);
        if contains(block, sc)
            idx = strfind(block, sc);
            remaining = block(idx(1)+length(sc):end);
            tokens = strsplit(strtrim(remaining));
            if ~isempty(tokens)
                D(i+1) = str2double(tokens{1});
            end
        end
    end
    
    if ~isnan(D(10))
        warning('Unexpected data block length');
        D = [];
        return;
    end
    
    D = D(1:9);
    if any(isnan(D))
        D = [];
        return;
    end
end

function T_out = read_coefficients2D(block)
    % Read 2D coefficients from block
    
    block = strrep(block, 't index', 't-index:');
    T = strsplit(block, 't-index:');
    T = T(2:end);
    
    if length(T) < 3
        T_out = [];
        return;
    end
    
    s = '';
    for i = 1:9
        for j = 1:3
            if j <= length(T)
                lines = strsplit(T{j}, newline);
                if (i+1) <= length(lines)
                    l = lines{i+1};
                    tokens = strsplit(strtrim(l));
                    if length(tokens) > 1
                        s = [s strjoin(tokens(2:end), ',') ','];
                    end
                end
            end
        end
        s = [s newline];
    end
    
    % Replace 'd' with 'e' for scientific notation
    s = strrep(s, 'd', 'e');
    
    % Parse as matrix
    lines = strsplit(s, newline);
    tmp = [];
    for i = 1:length(lines)
        if ~isempty(strtrim(lines{i}))
            vals = strsplit(strtrim(lines{i}), ',');
            row = [];
            for j = 1:length(vals)
                if ~isempty(strtrim(vals{j}))
                    val = str2double(vals{j});
                    if ~isnan(val)
                        row = [row val];
                    end
                end
            end
            if ~isempty(row)
                tmp = [tmp; row];
            end
        end
    end
    
    if numel(tmp) >= 81
        T_out = reshape(tmp(1:81), 9, 9)';
    else
        T_out = [];
    end
end

function reac = read_variables(block, reac, vnfd)
    % Read variables from block
    
    for i = 1:size(vnfd, 1)
        v = vnfd{i,1};
        n = vnfd{i,2};
        f = vnfd{i,3};
        d = vnfd{i,4};
        
        if ~isempty(d)
            reac.(n) = d;
        end
        
        if contains(block, v)
            idx = strfind(block, v);
            remaining = block(idx(1)+length(v):end);
            tokens = strsplit(strtrim(remaining));
            if ~isempty(tokens)
                x = str2double(tokens{1}) * f;
                if ~isnan(x)
                    reac.(n) = x;
                end
            end
        end
    end
end

function vnfd = get_vnfdEnergy()
    vnfd = {
        'emin', 'Emin', 1.0, [];
        'emax', 'Emax', 1.0, [];
        'eth', 'Eth', 1.0, []
    };
end