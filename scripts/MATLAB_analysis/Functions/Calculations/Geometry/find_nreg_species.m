function [NREG, species, isonuclear_species] = find_nreg_species(simulation)

% FIND_NREG_SPECIES
%
%   Reads run.log / run.log.gz / run.log.last10, processes the
%   "Start tallies by region" block, reconstructs continuation lines,
%   extracts the first line starting with "nnreg", and returns NREG.

%% PRELIMINARY OPERATIONS

index_log_last10 = find(contains({simulation.run.name},'run.log.last10'));
index_log_gz = find(contains({simulation.run.name},'run.log.gz'));
index_log = find(strcmp({simulation.run.name},'run.log'));

if isempty(index_log_last10) && isempty(index_log_gz) && isempty(index_log)
   error('Error: no log files found');
end

if ~isempty(index_log_last10) && strcmp(simulation.run(index_log_last10).status,'found')
    FILE = simulation.run(index_log_last10).file;
elseif ~isempty(index_log) && strcmp(simulation.run(index_log).status,'found')
    FILE = simulation.run(index_log).file;
elseif ~isempty(index_log_gz) && strcmp(simulation.run(index_log_gz).status,'found')
    FILE = simulation.run(index_log_gz).file;
end

%% READ FILE

if endsWith(FILE, '.gz')
    % For compressed files, we still need to decompress fully
    [NREG, species, isonuclear_species] = parse_from_text(read_gzip_file(FILE));
else
    % For uncompressed files, use streaming line-by-line read
    [NREG, species, isonuclear_species] = parse_file_streaming(FILE);
end

end

function [NREG, species, isonuclear_species] = parse_file_streaming(filename)
% Ultra-fast streaming parser - reads only what's needed

fid = fopen(filename, 'r');
if fid == -1
    error('Cannot open file %s', filename);
end

cleanup = onCleanup(@() fclose(fid));

% State machine variables
state = 'searching';  % 'searching' -> 'in_block' -> 'done'
block_lines = {};
current_line = '';

while ~feof(fid)
    line = fgetl(fid);
    
    if ~ischar(line)
        break;
    end
    
    switch state
        case 'searching'
            if contains(line, 'Start tallies by region')
                state = 'in_block';
            end
            
        case 'in_block'
            if contains(line, 'End tallies by region')
                state = 'done';
                break;
            end
            
            % Handle continuation lines
            if ~isempty(line) && line(1) == '+'
                current_line = [current_line, line];
            else
                if ~isempty(current_line)
                    block_lines{end+1} = current_line;
                end
                current_line = line;
            end
    end
end

% Add the last line if it exists
if ~isempty(current_line)
    block_lines{end+1} = current_line;
end

if strcmp(state, 'searching')
    error('Tallies block not found in file');
end

% Now parse the block
[NREG, species, isonuclear_species] = parse_block(block_lines, filename);

end

function [NREG, species, isonuclear_species] = parse_from_text(txt)
% Parse from full text (for compressed files)

lines = splitlines(txt);

% Find block boundaries
startIdx = 0;
endIdx = 0;

for i = 1:numel(lines)
    if contains(lines{i}, 'Start tallies by region')
        startIdx = i;
    elseif contains(lines{i}, 'End tallies by region')
        endIdx = i;
        break;
    end
end

if startIdx == 0 || endIdx == 0 || endIdx <= startIdx
    error('Tallies block not found in file');
end

block = lines(startIdx+1:endIdx-1);

% Merge continuation lines
merged = {};
current = block{1};

for k = 2:numel(block)
    line = block{k};
    if ~isempty(line) && line(1) == '+'
        current = [current, line];
    else
        merged{end+1} = current;
        current = line;
    end
end
merged{end+1} = current;

[NREG, species, isonuclear_species] = parse_block(merged, 'compressed file');

end

function [NREG, species, isonuclear_species] = parse_block(block_lines, filename)
% Common parsing logic for the block

% Find nnreg line
nnreg_idx = 0;
for i = 1:numel(block_lines)
    trimmed = strtrim(block_lines{i});
    if startsWith(trimmed, 'nnreg')
        nnreg_idx = i;
        break;
    end
end

if nnreg_idx == 0
    error('Error: nnreg not found in %s', filename);
end

% Parse NREG
tokens = strsplit(strtrim(block_lines{nnreg_idx}));
nums = str2double(tokens(2:end));

if any(isnan(nums))
    error('Error: Malformed nnreg line in %s', filename);
end

NREG = nums;

% Find species line
species_idx = 0;
for i = 1:numel(block_lines)
    trimmed = strtrim(block_lines{i});
    if startsWith(trimmed, 'species')
        species_idx = i;
        break;
    end
end

if species_idx == 0
    error('Error: species line not found in %s', filename);
end

% Parse species
tokens = strsplit(strtrim(block_lines{species_idx}));
NSPEC = str2double(tokens{2});

if isnan(NSPEC)
    error('Error: Malformed species line (NSPEC) in %s', filename);
end

species = tokens(3:end);

if numel(species) ~= NSPEC
    error('Error: Mismatch between NSPEC and number of species labels in %s', filename);
end

% Extract isonuclear species
isonuclear = regexprep(species, '[0-9+]+', '');
[~, ia] = unique(isonuclear, 'stable');
isonuclear_species = isonuclear(ia);

end

function txt = read_gzip_file(fname)
tmpdir = tempname;
mkdir(tmpdir);
cleanup = onCleanup(@() rmdir(tmpdir, 's'));
gunzip(fname, tmpdir);
[~, base] = fileparts(fname);
txt = fileread(fullfile(tmpdir, base));
end
