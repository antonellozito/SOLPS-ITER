function energy_balance = read_blne(simulation)
%
% read_balance_energy reads the energy balance tracing file created by B2.5
% Output is a struct "energy_balance" with all the data fields in the blne.trc file
%
% input: main simulation structure
%
%% PRELIMINARY OPERATIONS

% Load the files and read the version

index_temp = find(strcmp({simulation.run.name},'b2mn.exe.dir/tracing/blne.trc'));
index_final = find(strcmp({simulation.run.name},'tracing/blne.trc'));
if isempty(index_temp) && isempty (index_final)
   error('Error: blne.trc not found');
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
    energy_balance.(name) = data(:,i);
end

fprintf('Structure ENERGY_BALANCE from blne.trc read.\n');

end