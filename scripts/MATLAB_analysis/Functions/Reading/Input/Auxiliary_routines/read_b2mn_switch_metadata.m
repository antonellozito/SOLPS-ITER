function definitions = read_b2mn_switch_metadata(SOLPSTOP)
%READ_B2MN_SWITCH_METADATA Read b2mn.dat switch metadata from b2input.xml.
    definitions = struct('name', {}, 'value', {}, 'metadata', {});

    if nargin < 1 || isempty(SOLPSTOP)
        return;
    end

    xmlfile = sprintf('%s/modules/B2.5/src/documentation/b2input.xml', SOLPSTOP);
    fid = fopen(xmlfile, 'r');
    if fid == -1
        return;
    end

    raw_text = fread(fid, '*char')';
    fclose(fid);

    module_block = extract_module_block(raw_text, 'b2mn.dat');
    if isempty(module_block)
        return;
    end

    blocks = regexp(module_block, ...
        '<switchgroup>[\s\S]*?</switchgroup>|<switch>[\s\S]*?</switch>', ...
        'match');

    for iBlock = 1:length(blocks)
        block = strtrim(blocks{iBlock});
        if strncmp(block, '<switchgroup>', 13)
            group_definitions = parse_switchgroup(block);
            definitions = [definitions; group_definitions(:)]; %#ok<AGROW>
        else
            definition = parse_switch_block(block, '');
            if ~isempty(definition.name)
                definitions(end+1, 1) = definition; %#ok<AGROW>
            end
        end
    end
end


function module_block = extract_module_block(raw_text, module_name)
    pattern = ['<module\s+name="' regexptranslate('escape', module_name) '"[^>]*>([\s\S]*?)</module>'];
    token = regexp(raw_text, pattern, 'tokens', 'once');
    if isempty(token)
        module_block = '';
    else
        module_block = token{1};
    end
end


function definitions = parse_switchgroup(block_text)
    definitions = struct('name', {}, 'value', {}, 'metadata', {});
    shared_description = normalize_description_text(extract_tag_inner(block_text, 'description'));
    switch_blocks = regexp(block_text, '<switch>[\s\S]*?</switch>', 'match');

    for iSwitch = 1:length(switch_blocks)
        definition = parse_switch_block(switch_blocks{iSwitch}, shared_description);
        if ~isempty(definition.name)
            definitions(end+1, 1) = definition; %#ok<AGROW>
        end
    end
end


function definition = parse_switch_block(block_text, shared_description)
    definition = struct('name', '', 'value', [], 'metadata', empty_param_metadata());

    name = normalize_inline_xml_text(extract_tag_inner(block_text, 'name'));
    if isempty(name)
        return;
    end

    [default_text, has_default] = extract_default_text(block_text);
    default_text = normalize_inline_xml_text(default_text);
    type_text = normalize_inline_xml_text(extract_tag_inner(block_text, 'type'));
    description_text = normalize_description_text(extract_tag_inner(block_text, 'description'));

    if isempty(description_text)
        description_text = shared_description;
    end

    if has_default
        default_value = default_text;
    else
        default_value = '';
    end

    metadata = struct( ...
        'default', default_value, ...
        'type', type_text, ...
        'description', description_text);

    definition.name = name;
    definition.value = parse_switch_value(default_value, type_text, false);
    definition.metadata = metadata;
end


function inner_text = extract_tag_inner(block_text, tag_name)
    pattern = ['<' tag_name '>\s*([\s\S]*?)\s*</' tag_name '>'];
    token = regexp(block_text, pattern, 'tokens', 'once');
    if isempty(token)
        inner_text = '';
    else
        inner_text = token{1};
    end
end


function [default_text, has_default] = extract_default_text(block_text)
    if ~isempty(regexp(block_text, '<default\s*/>', 'once'))
        default_text = '';
        has_default = true;
        return;
    end

    has_default = ~isempty(regexp(block_text, '<default>', 'once'));
    default_text = extract_tag_inner(block_text, 'default');
end


function text = normalize_inline_xml_text(raw_text)
    text = normalize_xml_fragment(raw_text);
    text = regexprep(text, '\s+', ' ');
    text = strtrim(text);
end


function text = normalize_description_text(raw_text)
    text = normalize_xml_fragment(raw_text);
    if isempty(text)
        return;
    end

    raw_lines = regexp(text, '\n', 'split');
    lines = {};
    for iLine = 1:length(raw_lines)
        line = regexprep(raw_lines{iLine}, '\s+', ' ');
        line = strtrim(line);
        if ~isempty(line)
            lines{end+1} = line; %#ok<AGROW>
        end
    end

    if isempty(lines)
        text = '';
    else
        text = strjoin(lines, sprintf('\n'));
    end
end


function text = normalize_xml_fragment(raw_text)
    text = raw_text;
    if isempty(text)
        return;
    end

    text = strrep(text, char(13), '');
    text = regexprep(text, '<!--[\s\S]*?-->', '');
    text = replace_markup_tag(text, 'sup', '^{', '}');
    text = replace_markup_tag(text, 'sub', '_{', '}');

    text = strrep(text, '&lt;', '<');
    text = strrep(text, '&gt;', '>');
    text = strrep(text, '&amp;', '&');
    text = strrep(text, '&alpha;', 'alpha');
    text = strrep(text, '&beta;', 'beta');
    text = strrep(text, '&gamma;', 'gamma');
    text = strrep(text, '&Gamma;', 'Gamma');
    text = strrep(text, '&rho;', 'rho');
    text = strrep(text, '&Phi;', 'Phi');
    text = strrep(text, '&kappa;', 'kappa');
    text = strrep(text, '&zeta;', 'zeta');

    text = regexprep(text, '<[^>]+>', '');
end


function text = replace_markup_tag(text, tag_name, prefix, suffix)
    pattern = ['<' tag_name '>\s*([\s\S]*?)\s*</' tag_name '>'];
    while true
        [start_idx, end_idx, token] = regexp(text, pattern, 'start', 'end', 'tokens', 'once');
        if isempty(start_idx)
            break;
        end

        replacement = [prefix strtrim(token{1}) suffix];
        text = [text(1:start_idx-1) replacement text(end_idx+1:end)];
    end
end
