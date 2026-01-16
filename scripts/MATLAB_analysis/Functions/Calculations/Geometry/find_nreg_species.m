function [NREG,species,isonuclear_species] = find_nreg_species(simulation)

% FIND_NREG
%
%   Reads run.log / run.log.gz / run.log.last10, processes the
%   "Start tallies by region" block, reconstructs continuation lines,
%   extracts the first line starting with "nnreg", and returns NREG.

%% PRELIMINARY OPERATIONS

% Load the files and read the version

index_log_last10 = find(contains({simulation.run.name},'run.log.last10'));
index_log_gz = find(contains({simulation.run.name},'run.log.gz'));
index_log = find(strcmp({simulation.run.name},'run.log'));
if isempty(index_log_last10) && isempty(index_log_gz) &&isempty (index_log)
   error('Error: no log files found');
end

if not(isempty(index_log_last10)) && strcmp(simulation.run(index_log_last10).status,'read')
    index = index_log_last10;
    FILE = simulation.run(index).file;
elseif not(isempty(index_log)) && strcmp(simulation.run(index_log).status,'read')
    index = index_log;
    FILE = simulation.run(index).file;
elseif not(isempty(index_log_gz)) && strcmp(simulation.run(index_log_gz).status,'read')
    index = index_log_gz;
    FILE = simulation.run(index).file;
end

%% READ FILE

if endsWith(FILE, '.gz')
    try
        % Try gunzip-compatible approach
        txt = read_gzip_file(FILE);
    catch
        error('Cannot read compressed file %s', FILE);
    end
else
    txt = fileread(FILE);
end

lines = splitlines(txt);

startIdx = find(contains(lines, 'Start tallies by region'), 1, 'first');
endIdx   = find(contains(lines, 'End tallies by region'), 1, 'first');

if isempty(startIdx) || isempty(endIdx) || endIdx <= startIdx
    error('Tallies block not found in file');
end

block = lines(startIdx+1:endIdx-1);

hasPlusLines = any(startsWith(block, '+'));

if hasPlusLines
    merged = {};
    current = block{1};

    for k = 2:numel(block)
        line = block{k};
        if ~startsWith(line, '+')
            merged{end+1,1} = current; %#ok<AGROW>
            current = line;
        else
            current = [current, line];
        end
    end
    merged{end+1,1} = current;
else
    merged = block;
end

%% EXTRACT NREG

idx = find(startsWith(strtrim(merged), 'nnreg'), 1, 'first');
if isempty(idx)
    error('Error: nnreg not found in %s',FILE);
end

tokens = split(strtrim(merged{idx}));
nums = str2double(tokens(2:end));

if any(isnan(nums))
    error('Error: Malformed nnreg line in %s',FILE);
end

NREG = nums;

%% EXTRACT SPECIES INFORMATION

idx = find(startsWith(strtrim(merged), 'species'), 1, 'first');
if isempty(idx)
    error('Error: species line not found in %s',FILE);
end

tokens = split(strtrim(merged{idx}));

NSPEC = str2double(tokens{2});
if isnan(NSPEC)
    error('Error: Malformed species line (NSPEC) in %s',FILE);
end

species = tokens(3:end);

if numel(species) ~= NSPEC
    error('Error: Mismatch between NSPEC and number of species labels in %s',FILE);
end

%% EXTRACT ISONUCLEAR SPECIES

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
