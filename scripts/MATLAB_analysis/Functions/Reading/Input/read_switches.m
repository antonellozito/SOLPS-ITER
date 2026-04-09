function switches = read_switches(simulation)

% read_switches reads the b2mn.dat file containing single-valued switches
% for B2.5.
% Output is a struct "switches" preallocated from the b2mn.dat module of
% b2input.xml, with any values found in b2mn.dat overriding the XML
% defaults.
%
% Each parameter is stored as a substruct with four fields:
%   .value       - the numeric/char/logical value
%   .default     - the default entry from b2input.xml
%   .type        - the type entry from b2input.xml
%   .description - the description entry from b2input.xml
%
% Commented lines in b2mn.dat are ignored. If a switch appears multiple
% times, only the last occurrence is kept. If a switch is found in b2mn.dat
% but not in b2input.xml, only its .value field is filled.

%% PREALLOCATE FROM b2input.xml

definitions = struct('name', {}, 'value', {}, 'metadata', {});
if isfield(simulation, 'SOLPSTOP')
    definitions = read_b2mn_switch_metadata(simulation.SOLPSTOP);
end

switches = struct();
switch_name_to_field = containers.Map('KeyType', 'char', 'ValueType', 'char');

for iDef = 1:length(definitions)
    field_name = make_valid_fieldname(definitions(iDef).name);
    switches.(field_name) = make_param(definitions(iDef).value, definitions(iDef).metadata);
    switch_name_to_field(definitions(iDef).name) = field_name;
end

%% FIND AND READ b2mn.dat

if ~isfield(simulation, 'run') || isempty(simulation.run)
    return;
end

index = find(contains({simulation.run.name}, 'b2mn.dat'), 1, 'first');
if isempty(index)
    return;
end

fid = fopen(simulation.run(index).file, 'r');
if fid == -1
    return;
end

raw_text = fread(fid, '*char')';
fclose(fid);

lines = regexp(raw_text, '\r\n|\n|\r', 'split');
start_line = 1;

for iLine = 1:length(lines)
    line = strtrim(lines{iLine});
    if length(line) >= 7 && strcmpi(line(1:7), '*endphy')
        start_line = iLine + 1;
        break;
    end
end

for iLine = start_line:length(lines)
    line = strtrim(lines{iLine});
    if isempty(line)
        continue;
    end

    if line(1) == '#'
        continue;
    end

    if line(1) == '*'
        continue;
    end

    line = strtrim(strip_inline_comment(line));
    if isempty(line)
        continue;
    end

    [switch_name, raw_value, ok] = parse_switch_line(line);
    if ~ok
        continue;
    end

    if isKey(switch_name_to_field, switch_name)
        field_name = switch_name_to_field(switch_name);
        type_text = switches.(field_name).type;
    else
        field_name = make_valid_fieldname(switch_name);
        if ~isfield(switches, field_name)
            switches.(field_name) = make_param([], empty_param_metadata());
        end
        switch_name_to_field(switch_name) = field_name;
        type_text = switches.(field_name).type;
    end

    switches.(field_name).value = parse_switch_value(raw_value, type_text);
end

end


function line = strip_inline_comment(line)
    in_string = false;
    for iChar = 1:length(line)
        if line(iChar) == ''''
            in_string = ~in_string;
        elseif line(iChar) == '#' && ~in_string
            line = line(1:iChar-1);
            return;
        end
    end
end


function [switch_name, raw_value, ok] = parse_switch_line(line)
    switch_name = '';
    raw_value = '';
    ok = false;

    [~, end_idx, tokens] = regexp(line, '^\s*''([^'']+)''', 'start', 'end', 'tokens', 'once');

    if isempty(tokens)
        return;
    end

    switch_name = strtrim(tokens{1});
    remainder = strtrim(line(end_idx+1:end));
    if isempty(remainder)
        return;
    end

    if remainder(1) == ''''
        closing_quote = find(remainder(2:end) == '''', 1, 'first');
        if isempty(closing_quote)
            return;
        end
        closing_quote = closing_quote + 1;
        raw_value = remainder(2:closing_quote-1);
    else
        token = regexp(remainder, '^\S+', 'match', 'once');
        if isempty(token)
            return;
        end
        raw_value = token;
    end

    ok = ~isempty(switch_name);
end


function field_name = make_valid_fieldname(name)
    field_name = regexprep(name, '[^a-zA-Z0-9_]', '_');
    if isempty(field_name) || ~isstrprop(field_name(1), 'alpha')
        field_name = ['x_' field_name];
    end
end
