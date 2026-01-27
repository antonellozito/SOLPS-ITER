function print_help(func_name, description, params)

    % PRINT_HELP Display formatted help for a function
    %   func_name   - Name of the function (string)
    %   description - Cell array of description lines
    %   params      - Struct array with fields: name, type, default, required, comment
    
    fprintf('\n==================================================================================================================\n');
    fprintf('HELP: %s\n', func_name);
    fprintf('==================================================================================================================\n\n');
    
    % Print description
    fprintf('DESCRIPTION:\n\n');
    for i = 1:numel(description)
        fprintf('  %s\n', description{i});
    end
    fprintf('\n');
    
    % Print arguments
    fprintf('AVAILABLE ARGUMENTS:\n\n');
    for i = 1:numel(params)
        p = params(i);
        
        if p.required
            if strcmp(p.type, 'logical') || strcmp(p.type, 'numeric')
                type_str = 'logical/numeric (REQUIRED)';
            elseif strcmp(p.type, 'cell')
                type_str = 'cell (REQUIRED)';
            elseif strcmp(p.type, 'char')
                type_str = 'char (REQUIRED)';
            else
                type_str = sprintf('%s (REQUIRED)', p.type);
            end
            fprintf('  --%-35s [%s]\n', p.name, type_str);
        else
            type_str = sprintf('%s (OPTIONAL)', p.type);
            
            % Format default value
            if islogical(p.default)
                if p.default
                    def_str = 'True';
                else
                    def_str = 'False';
                end
            elseif isnumeric(p.default)
                if isscalar(p.default) && isnan(p.default)
                    def_str = 'NaN';
                elseif isscalar(p.default)
                    if p.default == floor(p.default)
                        def_str = sprintf('%d', p.default);
                    else
                        def_str = sprintf('%g', p.default);
                    end
                else
                    def_str = mat2str(p.default);
                end
            elseif ischar(p.default)
                def_str = sprintf('''%s''', p.default);
            elseif iscell(p.default)
                def_str = cell2str(p.default);
            else
                def_str = '...';
            end
            
            padding = max(0, 29 - length(type_str));
            fprintf('  --%-45s [%s]%*s Default: %s\n', p.name, type_str, padding, '', def_str);
        end
        
        % Print comment on next line if present
        if isfield(p, 'comment') && ~isempty(p.comment)
            fprintf('      %s\n', p.comment);
        end
    end
    
    fprintf('\n==================================================================================================================\n');
    fprintf('USAGE:\n');
    fprintf('  run_matlab %s [arguments]\n\n', func_name);
    fprintf('EXAMPLE:\n');
    fprintf('  run_matlab %s --FLAG True --NAME ''text'' --SIZE 1000 --VECTOR 2.5,6,3.2 --CELL 7,False,''text'',3.5\n', func_name);
    fprintf('==================================================================================================================\n\n');
end

function str = cell2str(c)
    parts = {};
    for i = 1:numel(c)
        elem = c{i};
        if islogical(elem)
            if elem
                parts{end+1} = 'True';
            else
                parts{end+1} = 'False';
            end
        elseif isnumeric(elem)
            parts{end+1} = sprintf('%g', elem);
        elseif ischar(elem)
            parts{end+1} = sprintf('''%s''', elem);
        else
            parts{end+1} = '...';
        end
    end
    str = ['{', strjoin(parts, ','), '}'];
end