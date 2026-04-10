function traces = read_b2ftrace(simulation)
%
% read_b2ftrace reads the norm of the residuals of the equations solved at
% each B2.5 iteration
% Output is a struct "trace" with all the data fields in the b2ftrace file
%
% input: main simulation structure
%
% TODO: add unstructured grid option
%
%% PRELIMINARY OPERATIONS

% Load the file

index_temp = find(strcmp({simulation.run.name},'b2mn.exe.dir/b2ftrace'));
index_run = find(strcmp({simulation.run.name},'b2ftrace'));
if isempty(index_temp) && isempty(index_run)
   error('Error: b2ftrace not found');
end

index = select_trace_file_index(simulation, index_temp, index_run);

file = simulation.run(index).file;
fid = fopen(file);
if (fid == -1)
   error('Error: b2ftrace not found');
end

line = fgetl(fid); line = fgetl(fid);
species_number = sscanf(line, '%d');

line = fgetl(fid); line = fgetl(fid); line = fgetl(fid); line = fgetl(fid);
fields_number = sscanf(line, '%d');

%% READ THE DATA

labels = read_trace_labels(fid, fields_number);
data = read_trace_data(fid, fields_number);
traces = build_traces(data, labels, species_number);

%% ACCOUNT FOR INTERNAL ITERATIONS

internal_iterations_number = 1;
if numel(traces.iteration) > 1
    i = 2;
    while i <= numel(traces.iteration) && traces.iteration(i) < 2
        internal_iterations_number = internal_iterations_number+1;
        i = i+1;
    end
end
partial_time_step = 1/internal_iterations_number;
traces.internal_iteration = linspace(partial_time_step, partial_time_step*length(traces.iteration),length(traces.iteration));

fclose(fid);

end

function index = select_trace_file_index(simulation, index_temp, index_run)
if ~isempty(index_temp) && strcmp(simulation.run(index_temp(1)).status, 'found')
    index = index_temp(1);
elseif ~isempty(index_run) && strcmp(simulation.run(index_run(1)).status, 'found')
    index = index_run(1);
elseif ~isempty(index_temp)
    index = index_temp(1);
else
    index = index_run(1);
end
end

function labels = read_trace_labels(fid, fields_number)
labels = cell(1, fields_number);

for i = 1:fields_number
    read_trace_block_value(fid, '%d');
    read_trace_block_value(fid, '%c');
    labels{i} = strtrim(read_trace_block_value(fid, '%c'));
end
end

function value = read_trace_block_value(fid, format_spec)
fgetl(fid);
line = fgetl(fid);
value = sscanf(line, format_spec);
end

function data = read_trace_data(fid, fields_number)
fields = {};
j = 1;
while true

    line = fgetl(fid);
    if line == -1
        break
    end

    fields{j} = fscanf(fid, '%e', fields_number);
    fgetl(fid);
    j = j+1;

end

if isempty(fields)
    data = zeros(fields_number, 0);
else
    data = cell2mat(fields);
end
end

function traces = build_traces(data, labels, species_number)
indices = find_trace_indices(labels, species_number);

traces = [];
traces.iteration = data(1, :) + 1;
traces.aresco = data(indices.aresco, :);
traces.aresmo = data(indices.aresmo, :);
traces.acorpa = data(indices.acorpa, :);
traces.acorua = data(indices.acorua, :);

scalar_fields = {'aresmt', 'areshe', 'areshi', 'arespo', 'acorut', 'acorte', 'acorti', 'acorpo'};
for i = 1:numel(scalar_fields)
    field_name = scalar_fields{i};
    traces.(field_name) = data(indices.(field_name), :);
end
end

function indices = find_trace_indices(labels, species_number)
indices.aresco = find_species_trace_indices(labels, 'aresco', species_number);
indices.aresmo = find_species_trace_indices(labels, 'aresmo', species_number);
indices.acorpa = find_species_trace_indices(labels, 'acorpa', species_number);
indices.acorua = find_species_trace_indices(labels, 'acorua', species_number);

scalar_fields = {'aresmt', 'areshe', 'areshi', 'arespo', 'acorut', 'acorte', 'acorti', 'acorpo'};
for i = 1:numel(scalar_fields)
    field_name = scalar_fields{i};
    indices.(field_name) = find_trace_index(labels, field_name);
end
end

function indices = find_species_trace_indices(labels, prefix, species_number)
indices = zeros(species_number, 1);
for k = 1:species_number
    indices(k) = find_trace_index(labels, sprintf('%s(%3d)', prefix, k-1));
end
end

function index = find_trace_index(labels, label)
index = find(strcmp(labels, label), 1);
if isempty(index)
    error('Error: b2ftrace label %s not found', label);
end
end
