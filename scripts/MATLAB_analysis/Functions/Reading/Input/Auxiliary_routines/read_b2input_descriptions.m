function descriptions = read_b2input_descriptions(SOLPSTOP, category_name, aliases)
%READ_B2INPUT_DESCRIPTIONS Read namelist metadata from b2input.xml.
%   DESCRIPTIONS = READ_B2INPUT_DESCRIPTIONS(SOLPSTOP, CATEGORY_NAME)
%   returns a struct keyed by lowercase namelist variable names. Each field
%   is a struct with the normalized fields .default, .type, and
%   .description taken directly from b2input.xml.
%
%   DESCRIPTIONS = READ_B2INPUT_DESCRIPTIONS(..., ALIASES) copies
%   metadata from documented names to reader-specific field names. Pass
%   aliases as an N-by-2 cell array of {target_name, source_name} pairs.

    if nargin < 3
        aliases = {};
    end

    descriptions = struct();

    xmlfile = sprintf('%s/modules/B2.5/src/documentation/b2input.xml', SOLPSTOP);
    fid = fopen(xmlfile, 'r');
    if fid == -1
        return;
    end

    raw_text = fread(fid, '*char')';
    fclose(fid);

    category_block = extract_category_block(raw_text, category_name);
    if isempty(category_block)
        return;
    end

    switch_blocks = regexp(category_block, '<switch>([\s\S]*?)</switch>', 'tokens');
    for iBlock = 1:length(switch_blocks)
        switch_block = switch_blocks{iBlock}{1};

        name = normalize_inline_xml_text(extract_tag_inner(switch_block, 'name'));
        if isempty(name)
            continue;
        end

        type_text = normalize_inline_xml_text(extract_tag_inner(switch_block, 'type'));
        [default_text, has_default] = extract_default_text(switch_block);
        default_text = normalize_inline_xml_text(default_text);
        if has_default
            default_value = default_text;
        else
            default_value = '';
        end

        descriptions.(lower(name)) = struct( ...
            'default', default_value, ...
            'type', type_text, ...
            'description', normalize_description_text(extract_tag_inner(switch_block, 'description')));
    end

    descriptions = apply_aliases(descriptions, aliases);
end


function category_block = extract_category_block(raw_text, category_name)
    pattern = ['<category\s+name="' regexptranslate('escape', category_name) '">([\s\S]*?)</category>'];
    token = regexp(raw_text, pattern, 'tokens', 'once');
    if isempty(token)
        category_block = '';
    else
        category_block = token{1};
    end
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


function descriptions = apply_aliases(descriptions, aliases)
    if isempty(aliases)
        return;
    end

    if isvector(aliases)
        aliases = reshape(aliases, 2, []).';
    end

    for iAlias = 1:size(aliases, 1)
        target_name = lower(aliases{iAlias, 1});
        source_name = lower(aliases{iAlias, 2});

        if ~isfield(descriptions, target_name) && isfield(descriptions, source_name)
            descriptions.(target_name) = descriptions.(source_name);
        end
    end
end
