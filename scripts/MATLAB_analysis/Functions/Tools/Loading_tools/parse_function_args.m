function [args_parsed, RUN] = parse_function_args(nargin_val, RUN_DIRECTORY, varargin_cell, FUNC_NAME, DESCRIPTION, PARAMS, RUN)
    
    % PARSE_FUNCTION_ARGS Universal argument parser
    %
    % Handles three modes:
    %   1. Script mode (nargin == 0): Uses RUN variable defined in script
    %   2. Function mode: Arguments passed as struct from shell script
    %   3. Compiled mode: Arguments passed as name-value string pairs
    %
    % Inputs:
    %   nargin_val     - nargin from the calling function
    %   RUN_DIRECTORY  - First argument passed to the function (or empty)
    %   varargin_cell  - The varargin cell array from the calling function
    %   FUNC_NAME      - Name of the function (for help display)
    %   DESCRIPTION    - Cell array of description lines (for help display)
    %   PARAMS         - Struct array with parameter definitions
    %   RUN            - RUN variable from script (may be empty)
    %
    % Outputs:
    %   args_parsed    - Cell array of name-value pairs for inputParser
    %   RUN            - Simulation name
    %   RUN_DIRECTORY  - Full path to simulation directory
    
    args_parsed = {};
    
    if nargin_val >= 1
        % Function or compiled mode
        if numel(varargin_cell) >= 1
            if ischar(varargin_cell{1})
                % Compiled mode or help request: arguments come as 'name1', value1, 'name2', value2, or single string 'help'
                if numel(varargin_cell) == 1 && any(strcmpi(varargin_cell{1}, {'help', '-h', '--help', '-help'}))
                    print_help(FUNC_NAME, DESCRIPTION, PARAMS);
                    RUN = '';
                    RUN_DIRECTORY = '';
                    return;
                end
                
                % Convert sequential name-value pairs for inputParser
                i = 1;
                while i <= numel(varargin_cell)
                    name = varargin_cell{i};
                    if i + 1 <= numel(varargin_cell)
                        value = varargin_cell{i+1};
                        % Convert string values to proper types
                        if ischar(value)
                            value = convert_string_value(value);
                        end
                        args_parsed{end+1} = name;
                        args_parsed{end+1} = value;
                        i = i + 2;
                    else
                        i = i + 1;
                    end
                end
                
            elseif isstruct(varargin_cell{1})
                % Function mode: arguments come as a struct from shell script
                args_struct = varargin_cell{1};
                fields = fieldnames(args_struct);
                for i = 1:numel(fields)
                    args_parsed{end+1} = fields{i};
                    args_parsed{end+1} = args_struct.(fields{i});
                end
                
            else
                args_parsed = parse_command_line_args(varargin_cell{:});
            end
        end
        
        % Extract RUN from RUN_DIRECTORY
        RUN = extractAfter(RUN_DIRECTORY, sprintf('%s/runs/', getenv('SOLPSTOP')));
        
    elseif nargin_val == 0
        % Script mode: RUN must be defined manually
        if isempty(RUN)
            error('Error: specify a simulation with the variable ''RUN'' when using %s as an interactive script', FUNC_NAME);
        end
        RUN_DIRECTORY = sprintf('%s/runs/%s', getenv('SOLPSTOP'), RUN);
    end
end