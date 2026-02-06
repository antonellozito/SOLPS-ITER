function geometry_type = find_geometry(simulation)

% FIND_GEOMETRY
%
%   Reads run.log / run.log.gz, searches for the
%   b2mod_connectivity.geometryId() line, and returns the geometry type
%   as a human-readable string.

%% PRELIMINARY OPERATIONS

index_log_gz = find(contains({simulation.run.name},'run.log.gz'));
index_log = find(strcmp({simulation.run.name},'run.log'));

if isempty(index_log_gz) && isempty(index_log)
   error('Error: no log files found');
end

if ~isempty(index_log) && strcmp(simulation.run(index_log).status,'found')
    FILE = simulation.run(index_log).file;
elseif ~isempty(index_log_gz) && strcmp(simulation.run(index_log_gz).status,'found')
    FILE = simulation.run(index_log_gz).file;
end

%% READ FILE

if endsWith(FILE, '.gz')
    % For compressed files, decompress and parse
    geometry_type = parse_from_text(read_gzip_file(FILE));
else
    % For uncompressed files, use streaming line-by-line read
    geometry_type = parse_file_streaming(FILE);
end

end

function geometry_type = parse_file_streaming(filename)
% Ultra-fast streaming parser - reads only what's needed

fid = fopen(filename, 'r');
if fid == -1
    error('Cannot open file %s', filename);
end

cleanup = onCleanup(@() fclose(fid));

% Search for the geometry line
while ~feof(fid)
    line = fgetl(fid);
    
    if ~ischar(line)
        break;
    end
    
    if contains(line, 'b2mod_connectivity.geometryId()') && contains(line, 'identified grid')
        geometry_type = parse_geometry_line(line, filename);
        return;
    end
end

error('Geometry identification line not found in %s', filename);

end

function geometry_type = parse_from_text(txt)
% Parse from full text (for compressed files)

lines = splitlines(txt);

% Find the geometry line
for i = 1:numel(lines)
    if contains(lines{i}, 'b2mod_connectivity.geometryId()') && contains(lines{i}, 'identified grid')
        geometry_type = parse_geometry_line(lines{i}, 'compressed file');
        return;
    end
end

error('Geometry identification line not found in compressed file');

end

function geometry_type = parse_geometry_line(line, filename)
% Extract and classify the geometry type

% Extract the text after "identified grid"
tokens = strsplit(line, 'identified grid');

if numel(tokens) < 2
    error('Error: Malformed geometry line in %s', filename);
end

% Get the geometry identifier and trim whitespace
geometry_id = strtrim(tokens{2});

% Map geometry identifiers to human-readable names
if strcmp(geometry_id, 'GEOMETRY_LIMITER')
    geometry_type = 'Limiter';
elseif strcmp(geometry_id, 'GEOMETRY_SN')
    geometry_type = 'Single null';
elseif strcmp(geometry_id, 'GEOMETRY_DDN_BOTTOM') || strcmp(geometry_id, 'GEOMETRY_DDN_TOP')
    geometry_type = 'Disconnected double null';
elseif strcmp(geometry_id, 'GEOMETRY_CDN')
    geometry_type = 'Connected double null';
elseif strcmp(geometry_id, 'GEOMETRY_LFS_SNOWFLAKE_MINUS') || strcmp(geometry_id, 'GEOMETRY_LFS_SNOWFLAKE_PLUS')
    geometry_type = 'LFS snowflake';
elseif strcmp(geometry_id, 'GEOMETRY_DDN(_BOTTOM?)')
    geometry_type = 'Single null (DDN grid)';
else
    error('Error: Unknown geometry type "%s" in %s', geometry_id, filename);
end

end

function txt = read_gzip_file(fname)
tmpdir = tempname;
mkdir(tmpdir);
cleanup = onCleanup(@() rmdir(tmpdir, 's'));
gunzip(fname, tmpdir);
[~, base] = fileparts(fname);
txt = fileread(fullfile(tmpdir, base));
end