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
if isempty(index_temp) && isempty (index_run)
   error('Error: b2ftrace not found');
end

if strcmp(simulation.run(index_temp).status,'read')
    index = index_temp;
elseif strcmp(simulation.run(index_run).status,'read')
    index = index_run;
end

file = simulation.run(index).file;
fid = simulation.run(index).fid;
if (fid == -1)
   error('Error: b2ftrace not found');
end

line = fgetl(fid); line = fgetl(fid);
species_number = sscanf(line, '%d');

line = fgetl(fid); line = fgetl(fid); line = fgetl(fid); line = fgetl(fid);
fields_number = sscanf(line, '%d');

%% READ THE DATA

traces = [];

for i = 1:fields_number

    line = fgetl(fid); line = fgetl(fid);
    linlog = sscanf(line, '%d');
    if linlog == 0
        scale{i} = 'linear';
    elseif linlog == 1
        scale{i} = 'log';
    end

    line = fgetl(fid); line = fgetl(fid);
    temp = sscanf(line, '%c');
    name{i} = strtrim(temp);

    line = fgetl(fid); line = fgetl(fid);
    temp = sscanf(line, '%c');
    label{i} = strtrim(temp);

end

j = 1;
while 1

    line = fgetl(fid);
    if line == -1
        break
    end
    fields{j} = fscanf(fid,'%e',fields_number);
    line = fgetl(fid);
    j = j+1;

end

for j = 1:length(fields)

    traces.iteration(j) = fields{j}(1)+1;
    
    for k = 1:species_number

        temp = sprintf('aresco(%3s)',string(k-1));
        index = find(strcmp(label, temp));
        traces.aresco(k,j) = fields{j}(index);

        temp = sprintf('aresmo(%3s)',string(k-1));
        index = find(strcmp(label, temp));
        traces.aresmo(k,j) = fields{j}(index);

        temp = sprintf('acorpa(%3s)',string(k-1));
        index = find(strcmp(label, temp));
        traces.acorpa(k,j) = fields{j}(index);

        temp = sprintf('acorua(%3s)',string(k-1));
        index = find(strcmp(label, temp));
        traces.acorua(k,j) = fields{j}(index);

    end

    index = find(strcmp(label, 'aresmt'));
    traces.aresmt(1,j) = fields{j}(index);

    index = find(strcmp(label, 'areshe'));
    traces.areshe(1,j) = fields{j}(index);

    index = find(strcmp(label, 'areshi'));
    traces.areshi(1,j) = fields{j}(index);

    index = find(strcmp(label, 'arespo'));
    traces.arespo(1,j) = fields{j}(index);

    index = find(strcmp(label, 'acorut'));
    traces.acorut(1,j) = fields{j}(index);

    index = find(strcmp(label, 'acorte'));
    traces.acorte(1,j) = fields{j}(index);

    index = find(strcmp(label, 'acorti'));
    traces.acorti(1,j) = fields{j}(index);

    index = find(strcmp(label, 'acorpo'));
    traces.acorpo(1,j) = fields{j}(index);

end

%% ACCOUNT FOR INTERNAL ITERATIONS

i = 2;
internal_iterations_number = 1;
while traces.iteration(i) < 2
    internal_iterations_number = internal_iterations_number+1;
    i = i+1;
end
partial_time_step = 1/internal_iterations_number;
traces.internal_iteration = linspace(partial_time_step, partial_time_step*length(traces.iteration),length(traces.iteration));

end
