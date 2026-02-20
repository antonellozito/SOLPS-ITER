function particle_balance = read_blnn(simulation)

% READ_BLNN reads the particle balance tracing file created by B2.5.
%
%   particle_balance = read_blnn(simulation)
%
%   Output is a struct "particle_balance" with all the data fields
%   in the blnn_SPb.trc file. Each field is a struct with subfields:
%       .value       - Data vector
%       .description - Human-readable description
%       .unit        - Physical unit
%       .dimensions  - Cell array of dimension names
%
%   Input:
%       simulation - Main simulation structure

%% PRELIMINARY OPERATIONS

% Load the files and read the version
index_temp = find(strcmp({simulation.run.name},'b2mn.exe.dir/tracing/blnn_SPb.trc'));
index_final = find(strcmp({simulation.run.name},'tracing/blnn_SPb.trc'));

if isempty(index_temp) && isempty(index_final)
   error('Error: blnn_SPb.trc not found');
end

if strcmp(simulation.run(index_temp).status,'found')
    index = index_temp;
elseif strcmp(simulation.run(index_final).status,'found')
    index = index_final;
end

file = importdata(simulation.run(index).file,' ',3);
data = file.data;
names = strsplit(file.textdata{3});

%% DEFINE THE DESCRIPTION MAP

description_map = {
    'ion_core',           'Ion core source'
    'ntr_core',           'Neutral core source'
    'ion_targ',           'Ion flux to targets'
    'ntr_targ_tot',       'Neutral flux balance at targets'
    'ntr_targ_rec',       'Recycled neutral flux from targets'
    'ntr_targ_spt',       'Target sputtering'
    'ntr_targ_pmp',       'Target pumping'
    'ion_wall',           'Ion flux to wall'
    'ntr_wall_tot',       'Neutral flux balance at wall'
    'ntr_wall_rec',       'Recycled neutral flux from wall'
    'ntr_wall_spt',       'Wall sputtering'
    'ntr_wall_pmp',       'Wall pumping'
    'src_ioniz',          'Ionization source'
    'ntr_puff',           'Neutral gas puff'
    'flux_tot',           'Total flux balance'
    'src_ext',            'External source'
    'ion_dn_divided_dt',  'Total flux time variation'
};

% Sort prefixes by length (longest first) for correct matching
prefix_lengths = cellfun(@length, description_map(:,1));
[~, sort_idx] = sort(prefix_lengths, 'descend');
description_map = description_map(sort_idx,:);

%% READ THE DATA

for i = 1:size(data,2)

    name = names{i+1};
    name = replace(name,'/','_divided_');

    if strcmp(name, 'time')

        particle_balance.(name).value = data(:,i);
        particle_balance.(name).description = 'Time';
        particle_balance.(name).unit = 's';
        particle_balance.(name).dimensions = {'time'};

    else

        % Find the matching prefix and extract the species name
        description = name;
        species = '';
        for j = 1:size(description_map,1)
            prefix = description_map{j,1};
            if startsWith(name, [prefix '_'])
                species = name(length(prefix)+2:end);
                description = sprintf('%s (%s)', description_map{j,2}, species);
                break;
            end
        end

        particle_balance.(name).value = data(:,i);
        particle_balance.(name).description = description;
        particle_balance.(name).unit = 's^-1';
        particle_balance.(name).dimensions = {'time'};

    end

end

fprintf('Particle balance time traces from blnn_SPb.trc read\n');

end
