function database = read_ammonx(ammonx_datafile)
    % Parse AMMONX database
    % Returns a struct containing parsed AMMONX reactions

    warnState = warning('off','all');
    cleanupObj = onCleanup(@() warning(warnState));
    
    database = struct();
    report = 'AMMONX';
    
    % Open and read file
    fid = fopen(ammonx_datafile, 'r', 'n', 'UTF-8');
    if fid == -1
        error('Error: Cannot open file: %s', ammonx_datafile);
    end
    AMMONX = fread(fid, '*char')';
    fclose(fid);
    
    % Split by sections
    sections = strsplit(AMMONX, '\section{H.');
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
    
    % Process header 2
    ih = 2;
    if isfield(headers, 'H2')
        % Split by \subsection{ (without the newline)
        subsections = strsplit(headers.H2, '\subsection{');
        
        for s = 2:length(subsections)
            S = subsections{s};
            
            try
                % Check if this subsection contains "Reaction"
                if contains(S, 'Reaction')
                    lines = strsplit(S, newline);
                    
                    % Find the line that starts with "Reaction"
                    reaction_line = '';
                    for li = 1:min(5, length(lines))
                        if startsWith(strtrim(lines{li}), 'Reaction')
                            reaction_line = lines{li};
                            break;
                        end
                    end
                    
                    if isempty(reaction_line)
                        continue;
                    end
                    
                    % Parse reaction line: "Reaction 01 e + N = N+ + 2e }"
                    % or "Reaction R_H_H H + H = H2 }"
                    parts = strsplit(reaction_line);
                    
                    % Find "Reaction" and get the next token
                    reaction_idx = find(strcmp(parts, 'Reaction'));
                    if isempty(reaction_idx) || length(parts) <= reaction_idx
                        continue;
                    end
                    nam = parts{reaction_idx(1) + 1};
                    
                    % Extract latex - everything between name and closing }
                    latex_parts = strsplit(reaction_line, nam);
                    if length(latex_parts) > 1
                        latex_temp = strsplit(latex_parts{2}, '}');
                        latex = strrep(strtrim(latex_temp{1}), '=', '\rightarrow');
                    else
                        latex = '';
                    end
                    
                    % Extract data block
                    block = extract_data_block(S);
                    
                    if ~isempty(block)
                        reaction = struct();
                        reaction.report = report;
                        reaction.header = ih;
                        reaction.name = nam;
                        reaction.latex = latex;
                        reaction.symbol = '$\langle\sigma\cdot v\rangle$';
                        reaction.unit = 'm$^3$ s$^{-1}$';
                        reaction.parameters = 'T';
                        reaction.factor = 1.0e-6;
                        
                        % Extract Arrhenius coefficient
                        sc = 'b-1 ';
                        if contains(block, sc)
                            idx = strfind(block, sc);
                            remaining = block(idx(1)+length(sc):end);
                            tokens = strsplit(strtrim(remaining));
                            if ~isempty(tokens)
                                reaction.Arrhenius_coefficient = str2double(tokens{1});
                            end
                        end
                        
                        % Extract coefficients b0-b9
                        D = zeros(10, 1);
                        for i = 0:9
                            sc = sprintf('b%d ', i);
                            if contains(block, sc)
                                idx = strfind(block, sc);
                                remaining = block(idx(1)+length(sc):end);
                                tokens = strsplit(strtrim(remaining));
                                if ~isempty(tokens)
                                    D(i+1) = str2double(tokens{1});
                                end
                            end
                        end
                        
                        reaction.coefficients = D;
                        
                        % Store in database - replace dots and dashes with underscores
                        key = sprintf('H_%d_%s', ih, strrep(strrep(nam, '.', '_'), '-', '_'));
                        database.(key) = reaction;
                    end
                end
            catch ME
                % Skip this subsection if error
                % Uncomment for debugging:
                % warning('Error processing subsection: %s', ME.message);
            end
        end
    end
end

function block = extract_data_block(s)
    % Extract data block from verbatim environment (AMMONX version)
    
    % Check for analytic formula messages
    if contains(s, 'An analytic formula is given in the text.') || ...
       contains(s, 'See text for analytic formulas.')
        block = [];
        return;
    end
    
    % The actual pattern in the LaTeX files is \begin{verbatim} (single backslash)
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
    
    % Convert to lowercase and replace commas with spaces
    block = lower(s(start_pos:end_pos));
    block = strrep(block, ',', ' ');
end