function database = read_amjuel(amjuel_datafile)
    % Parse AMJUEL database
    % Returns a struct containing parsed AMJUEL reactions

    warnState = warning('off','all');
    cleanupObj = onCleanup(@() warning(warnState));
    
    database = struct();
    report = 'AMJUEL';
    
    % Open and read file
    fid = fopen(amjuel_datafile, 'r', 'n', 'UTF-8');
    if fid == -1
        error('Error: Cannot open file: %s', amjuel_datafile);
    end
    aj = fread(fid, '*char')';
    fclose(fid);
    
    % Split by sections
    headers_cell = strsplit(aj, '\section{H.');
    headers_cell = headers_cell(2:end);
    
    % Map: section number -> array index
    % From the debug output, the actual data sections are:
    % H.2 is at index 16, H.3 at 17, H.4 at 18, H.8 at 22, H.10 at 24, H.11 at 25, H.12 at 26
    
    section_map = containers.Map([2, 3, 4, 8, 10, 11, 12], [16, 17, 18, 22, 24, 25, 26]);
    
    % Process sections H3, H4, H10, H12 (double polynomial fits)
    for ih = [3, 4, 10, 12]
        if section_map.isKey(ih)
            idx = section_map(ih);
            if idx <= length(headers_cell)
                header = headers_cell{idx};
                subsections = strsplit(header, '\subsection{');
                
                for r = 2:length(subsections)
                    rsec = subsections{r};
                    lines = strsplit(rsec, newline);
                    
                    l3 = strtrim(strjoin(lines(1:min(3,length(lines))), ' '));
                    tokens = strsplit(l3);
                    if length(tokens) >= 2
                        nam = tokens{2};
                    else
                        continue;
                    end
                    
                    try
                        latex_parts = strsplit(l3, '$');
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
                        
                        if ih == 3
                            reaction.symbol = '$\langle\sigma\cdot v\rangle$';
                            reaction.unit = 'm$^3$ s$^{-1}$';
                            reaction.parameters = 'E,T';
                            reaction.factor = 1e-6;
                            reaction.factor_n = 1.0;
                        elseif ih == 4
                            reaction.symbol = '$\langle\sigma\cdot v\rangle$';
                            reaction.unit = 'm$^3$ s$^{-1}$';
                            reaction.parameters = 'n,T';
                            reaction.factor = 1e-6;
                            reaction.factor_n = 1e-14;
                        elseif ih == 10
                            reaction.symbol = '$\langle\sigma\cdot v\cdot E\rangle$';
                            reaction.unit = 'm$^3$ eV s$^{-1}$';
                            reaction.parameters = 'n,T';
                            reaction.factor = 1e-6;
                            reaction.factor_n = 1e-14;
                        elseif ih == 12
                            reaction.symbol = 'ratio';
                            reaction.unit = '';
                            reaction.parameters = 'n,T';
                            reaction.factor = 1;
                            reaction.factor_n = 1e-14;
                        end
                        
                        block = extract_data_block(rsec, true, {});
                        
                        if ~isempty(block)
                            coeffs = read_coefficients2D(block);
                            if ~isempty(coeffs)
                                reaction.coefficients = coeffs';
                                reaction = read_variables(block, reaction, get_vnfdTn());
                                
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
    end
    
    % Process sections H2, H8, H11 (single polynomial fits)
    for ih = [2, 8, 11]
        if section_map.isKey(ih)
            idx = section_map(ih);
            if idx <= length(headers_cell)
                header = headers_cell{idx};
                subsections = strsplit(header, '\subsection{');
                
                for s = 2:length(subsections)
                    S = subsections{s};
                    lines = strsplit(S, newline);
                    
                    if length(lines) >= 2
                        line2 = lines{2};
                        if startsWith(strtrim(line2), 'Reaction')
                            try
                                tokens = strsplit(line2);
                                if length(tokens) >= 2
                                    nam = tokens{2};
                                else
                                    continue;
                                end
                                
                                if length(lines) >= 3
                                    combined = [lines{2} lines{3}];
                                else
                                    combined = lines{2};
                                end
                                latex_parts = strsplit(combined, '$');
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
                                reaction.parameters = 'T';
                                
                                if ih == 2
                                    reaction.symbol = '$\langle\sigma\cdot v\rangle$';
                                    reaction.unit = 'm$^3$ s$^{-1}$';
                                    reaction.factor = 1e-6;
                                    varname = 'b';
                                elseif ih == 8
                                    reaction.symbol = '$\langle\sigma\cdot v\cdot E\rangle$';
                                    reaction.unit = 'm$^3$ eV s$^{-1}$';
                                    reaction.factor = 1e-6;
                                    varname = 'h';
                                elseif ih == 11
                                    reaction.symbol = '$\langle E\rangle$';
                                    reaction.unit = 'eV';
                                    reaction.factor = 1;
                                    varname = 'k';
                                end
                                
                                block = extract_data_block(S, true, {',', ' '; 'd', 'e'});
                                
                                if ~isempty(block)
                                    coeffs = read_coefficients1D(block, varname);
                                    if ~isempty(coeffs)
                                        reaction.coefficients = coeffs;
                                        reaction = read_variables(block, reaction, get_vnfdEnergy());
                                        
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
            end
        end
    end
end

function block = extract_data_block(s, do_lower, repl)
    % Extract data block from verbatim environment
    
    if contains(s, 'An analytic formula is given in the text.') || ...
       contains(s, 'See text for analytic formulas.')
        block = [];
        return;
    end
    
    begin_tag = '\begin{verbatim}';
    end_tag = '\end{verbatim}';
    
    begin_count = length(strfind(s, begin_tag));
    end_count = length(strfind(s, end_tag));
    
    if begin_count ~= 1 || end_count ~= 1
        block = [];
        return;
    end
    
    idx_begin = strfind(s, begin_tag);
    idx_end = strfind(s, end_tag);
    
    if isempty(idx_begin) || isempty(idx_end) || idx_end <= idx_begin
        block = [];
        return;
    end
    
    start_pos = idx_begin + length(begin_tag);
    end_pos = idx_end - 1;
    
    block = s(start_pos:end_pos);
    
    if nargin >= 2 && do_lower
        block = lower(block);
    end
    
    if nargin >= 3 && ~isempty(repl)
        for i = 1:size(repl, 1)
            block = strrep(block, repl{i,1}, repl{i,2});
        end
    end
end

function D = read_coefficients1D(block, varname)
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
    
    s = strrep(s, 'd', 'e');
    
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

function vnfd = get_vnfdTn()
    vnfd = {
        't1min=', 'Tmin', 1.0, 0.1;
        't1max=', 'Tmax', 1.0, 1e4;
        'n2min=', 'nmin', 1e6, 1e10;
        'n2max=', 'nmax', 1e6, 1e25
    };
end
