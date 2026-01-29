function [time_traces_av] = read_b2batch(simulation)
%
% read_b2batch reads the b2batch.nc file created by B2.5
% Output is the struct "time_traces_av" with the batch-averaged
% time traces at the times of the average
%
% input: main simulation structure
%
%% PRELIMINARY OPERATIONS

% Load the file

index = find(contains({simulation.run.name},'b2batch.nc'));
if isempty(index)
   error('Error: b2batch.nc not found');
end
file = simulation.run(index).file;
fid = fopen(file);
if (fid == -1)
   error('Error: b2batch.nc not found');
end

%% READ THE TIME TRACES

time_traces_av.batchsa = ncread(file,'batchsa');

time_traces_av.nesepm_av = ncread(file,'nesepm_av');

time_traces_av.tesepm_av = ncread(file,'tesepm_av');
time_traces_av.tisepm_av = ncread(file,'tisepm_av');

time_traces_av.nesepi_av = ncread(file,'nesepi_av');
time_traces_av.nemxip_av = ncread(file,'nemxip_av');
time_traces_av.nesepa_av = ncread(file,'nesepa_av');
time_traces_av.nemxap_av = ncread(file,'nemxap_av');

time_traces_av.tesepi_av = ncread(file,'tesepi_av');
time_traces_av.temxip_av = ncread(file,'temxip_av');
time_traces_av.tesepa_av = ncread(file,'tesepa_av');
time_traces_av.temxap_av = ncread(file,'temxap_av');

time_traces_av.tisepi_av = ncread(file,'tisepi_av');
time_traces_av.timxip_av = ncread(file,'timxip_av');
time_traces_av.tisepa_av = ncread(file,'tisepa_av');
time_traces_av.timxap_av = ncread(file,'timxap_av');

fprintf('Structure TIME_TRACES_AV from b2batch.nc read.\n');

fclose(fid);

end