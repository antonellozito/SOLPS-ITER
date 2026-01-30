function particle_balance = read_blnn(simulation)
%
% read_balance_particles reads the particle balance tracing file created by B2.5
% Output is a struct "particle_balance" with all the data fields in the blnn_SPb.trc file
%
% 1st input: main simulation structure
%
%% PRELIMINARY OPERATIONS

% Load the files and read the version

index_temp = find(strcmp({simulation.run.name},'b2mn.exe.dir/tracing/blnn_SPb.trc'));
index_final = find(strcmp({simulation.run.name},'tracing/blnn_SPb.trc'));
if isempty(index_temp) && isempty (index_final)
   error('Error: blnn_SPb.trc not found');
end

if strcmp(simulation.run(index_temp).status,'found')
    index = index_temp;
elseif strcmp(simulation.run(index_final).status,'found')
    index = index_final;
elseif strcmp(simulation.run(index_run).status,'found')
    index = index_run;
end

file = importdata(simulation.run(index).file,' ',3);
data = file.data;
names = strsplit(file.textdata{3});

%% READ THE DATA

for i = 1:size(data,2)
    name = names{i+1};
    name = replace(name,'/','_divided_');
    particle_balance.(name) = data(:,i);
end

fprintf('Particle balance time traces from blnn.trc read\n');

end