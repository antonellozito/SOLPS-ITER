function load_input_arguments(RUN, args)

    % LOAD_INPUT_ARGUMENTS Handle help display and argument validation
    % This function is called by multiple analysis functions to standardize
    % argument parsing and help display
    
    if nargin >= 2 && ischar(args) && strcmp(args, 'help')
        % Display help by parsing the USER INPUT section
        caller_name = dbstack(1);
        func_name = caller_name(1).name;
        func_path = which(func_name);
        
        fprintf('\n==================================================================================================================\n');
        fprintf('HELP: %s\n', func_name);
        fprintf('==================================================================================================================\n\n');
        
        % Read the caller's file
        fid = fopen(func_path, 'r');
        if fid == -1
            error('Error: Could not open function file for reading');
        end
        
        % First pass: extract description block (first comment block before %% USER INPUT)
        description_lines = {};
        in_description = false;
        found_function_line = false;
        
        fseek(fid, 0, 'bof'); % Reset to beginning
        while ~feof(fid)
            line = fgetl(fid);
            
            % Skip until we find the function line
            if ~found_function_line
                if startsWith(strtrim(line), 'function ')
                    found_function_line = true;
                end
                continue;
            end
            
            % Check if we reached USER INPUT section
            if contains(line, '%% USER INPUT')
                break;
            end
            
            % Capture comment lines
            trimmed = strtrim(line);
            if startsWith(trimmed, '%')
                in_description = true;
                % Remove the leading % and any following space
                comment_text = regexprep(trimmed, '^%\s?', '');
                % Skip section markers like "SCRIPT DESCRIPTION" but add empty line
                if contains(comment_text, 'SCRIPT DESCRIPTION')
                    description_lines{end+1} = '';
                else
                    description_lines{end+1} = comment_text;
                end
            elseif in_description && ~isempty(trimmed)
                % Stop at first non-comment, non-empty line after comments started
                break;
            end
        end
        
        % Display description if found
        if ~isempty(description_lines)
            fprintf('DESCRIPTION:\n');
            for i = 1:length(description_lines)
                fprintf('  %s\n', description_lines{i});
            end
            fprintf('\n');
        end
        
        % Second pass: extract arguments
        fprintf('AVAILABLE ARGUMENTS:\n\n');
        
        fseek(fid, 0, 'bof'); % Reset to beginning
        in_user_input = false;
        
        while ~feof(fid)
            line = fgetl(fid);
            
            % Start capturing after %% USER INPUT
            if contains(line, '%% USER INPUT')
                in_user_input = true;
                continue;
            end
            
            % Stop at if nargin
            if in_user_input && contains(line, 'if nargin')
                break;
            end
            
            % Parse variable assignments
            if in_user_input && ~isempty(line)
                % Match pattern: VARIABLE = value;
                tokens = regexp(line, '^\s*([A-Z_][A-Z0-9_]*)\s*=\s*(.+);', 'tokens');
                if ~isempty(tokens)
                    var_name = tokens{1}{1};
                    var_value = strtrim(tokens{1}{2});
                    
% Check if this is a required variable (empty initialization)
                    is_required = false;
                    if strcmp(var_value, '[]')
                        is_required = true;
                        type_hint = 'logical/numeric (REQUIRED)';
                    elseif strcmp(var_value, '{}')
                        is_required = true;
                        type_hint = 'cell (REQUIRED)';
                    elseif strcmp(var_value, '''''')
                        is_required = true;
                        type_hint = 'char (REQUIRED)';
                    elseif strcmp(var_value, 'true') || strcmp(var_value, 'false')
                        type_hint = 'logical (OPTIONAL)';
                        var_value_print = [upper(var_value(1)), var_value(2:end)];
                    elseif strcmpi(var_value, 'nan') || strcmpi(var_value, 'NaN')
                        type_hint = 'numeric (OPTIONAL)';
                        var_value_print = 'NaN';
                    elseif ~isempty(regexp(var_value, '^[0-9]+(\.[0-9]+)?$', 'once'))
                        type_hint = 'numeric (OPTIONAL)';
                        var_value_print = var_value;
                    elseif startsWith(var_value, '''') || startsWith(var_value, '"')
                        type_hint = 'char (OPTIONAL)';
                        var_value_print = var_value;
                    elseif startsWith(var_value, '{')
                        type_hint = 'cell (OPTIONAL)';
                        var_value_print = var_value;
                    else
                        type_hint = 'value (OPTIONAL)';
                        var_value_print = var_value;
                    end
                    
                    % Print with or without default value
                    if is_required
                        fprintf('  --%-35s [%s]\n', var_name, type_hint);
                    else
                        fprintf('  --%-35s [%s]%*s Default: %s\n', var_name, type_hint, 29-length(type_hint), '', var_value_print);
                    end 
                end
            end
        end
        
        fclose(fid);
        
        fprintf('\n==================================================================================================================\n');
        fprintf('USAGE:\n');
        fprintf('  run_matlab %s [arguments]\n\n', func_name);
        fprintf('EXAMPLE:\n');
        fprintf('  run_matlab %s --FLAG True --NAME ''text'' --SIZE 1000 --VECTOR 2.5,6,3.2 --CELL 7,False,''text'',3.5\n', func_name);
        fprintf('For more details, read the script:\n');
        fprintf('  %s\n', func_path);
        fprintf('==================================================================================================================\n\n');
        return;
    end
    
    % Validate and override arguments
    if nargin >= 2 && isstruct(args)
        % First, detect required variables from caller's workspace
        caller_name = dbstack(1);
        func_name = caller_name(1).name;
        func_path = which(func_name);
        
        required_vars = struct('logical_numeric', {{}}, 'cell', {{}}, 'char', {{}});
        
        % Read the function file to find required variables
        fid = fopen(func_path, 'r');
        if fid ~= -1
            in_user_input = false;
            while ~feof(fid)
                line = fgetl(fid);
                
                if contains(line, '%% USER INPUT')
                    in_user_input = true;
                    continue;
                end
                
                if in_user_input && contains(line, 'if nargin')
                    break;
                end
                
                if in_user_input && ~isempty(line)
                    % Check for empty initializations
                    tokens_empty_bracket = regexp(line, '^\s*([A-Z_][A-Z0-9_]*)\s*=\s*\[\];', 'tokens');
                    tokens_empty_cell = regexp(line, '^\s*([A-Z_][A-Z0-9_]*)\s*=\s*\{\};', 'tokens');
                    tokens_empty_char = regexp(line, '^\s*([A-Z_][A-Z0-9_]*)\s*=\s*'''';', 'tokens');
                    
                    if ~isempty(tokens_empty_bracket)
                        required_vars.logical_numeric{end+1} = tokens_empty_bracket{1}{1};
                    elseif ~isempty(tokens_empty_cell)
                        required_vars.cell{end+1} = tokens_empty_cell{1}{1};
                    elseif ~isempty(tokens_empty_char)
                        required_vars.char{end+1} = tokens_empty_char{1}{1};
                    end
                end
            end
            fclose(fid);
        end
        
        % Check if required variables are provided in args
        missing_required = {};
        
        for i = 1:numel(required_vars.logical_numeric)
            var_name = required_vars.logical_numeric{i};
            if ~isfield(args, var_name)
                missing_required{end+1} = sprintf('  - required argument "%s" which should be logical or numeric (e.g., --%s True or --%s 4)', ...
                    var_name, var_name, var_name);
            end
        end
        
        for i = 1:numel(required_vars.cell)
            var_name = required_vars.cell{i};
            if ~isfield(args, var_name)
                missing_required{end+1} = sprintf('  - required argument "%s" which should be a cell (e.g., --%s 7,False,''text'',3.5)', ...
                    var_name, var_name);
            end
        end
        
        for i = 1:numel(required_vars.char)
            var_name = required_vars.char{i};
            if ~isfield(args, var_name)
                missing_required{end+1} = sprintf('  - required argument "%s" which should be a char (e.g., --%s ''text'')', ...
                    var_name, var_name);
            end
        end
        
        % Get caller's workspace variables
        args_fields = fieldnames(args);
        
        % We need to validate in the caller's workspace
        error_msgs = {};
        for i = 1:numel(args_fields)
            arg_name = args_fields{i};
            
            % Check if variable exists in caller workspace
            if ~evalin('caller', sprintf('exist(''%s'', ''var'')', arg_name))
                error('Error: Invalid argument: "%s". Run with --h for help.', arg_name);
            end
            
            % Get original value from caller workspace
            original_val = evalin('caller', arg_name);
            new_val = args.(arg_name);
            
            % Type checking - collect errors instead of throwing immediately
            if islogical(original_val)
                if ~islogical(new_val)
                    error_msgs{end+1} = sprintf('argument "%s" should be logical (e.g., --%s True or --%s False)', ...
                          arg_name, arg_name, arg_name);
                end
            elseif isnumeric(original_val)
                if ~isnumeric(new_val)
                    error_msgs{end+1} = sprintf('argument "%s" should be numeric (e.g., --%s 0.4 or --%s 1,2,3,4)', ...
                          arg_name, arg_name, arg_name);
                end
            elseif ischar(original_val)
                if ~ischar(new_val)
                    error_msgs{end+1} = sprintf('argument "%s" should be a char (e.g., --%s ''text'')', ...
                          arg_name, arg_name);
                end
            elseif iscell(original_val)
                if ~iscell(new_val)
                    error_msgs{end+1} = sprintf('argument "%s" should be a cell (e.g., --%s 7,False,''text'',3.5)', ...
                          arg_name, arg_name);
                end
            end
            
            % Only assign if no type mismatch
            if islogical(original_val) && islogical(new_val) || ...
               isnumeric(original_val) && isnumeric(new_val) || ...
               ischar(original_val) && ischar(new_val) || ...
               iscell(original_val) && iscell(new_val)
                assignin('caller', arg_name, new_val);
            end
        end

        % Collect all errors
        all_errors = {};
        
        % Add missing required arguments error
        if ~isempty(missing_required)
            missing_error = sprintf('Error: Missing required argument(s) detected:\n%s', strjoin(missing_required, '\n'));
            all_errors{end+1} = missing_error;
        end
        
        % Add type mismatch error
        if ~isempty(error_msgs)
            type_error = sprintf('Error: Type mismatch(es) detected:\n  - %s', strjoin(error_msgs, '\n  - '));
            all_errors{end+1} = type_error;
        end
        
        % Throw combined error if any errors exist
        if ~isempty(all_errors)
            full_error = sprintf('%s\nRun with --h for help.', strjoin(all_errors, '\n'));
            error('%s', full_error);
        end
    end
end
