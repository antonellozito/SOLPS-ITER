function energy_balance = read_blne(simulation)

% READ_BLNE reads the energy balance tracing file created by B2.5.
%
%   energy_balance = read_blne(simulation)
%
%   Output is a struct "energy_balance" with all the data fields
%   in the blne.trc file. Each field is a struct with subfields:
%       .value       - Data vector
%       .description - Human-readable description
%       .unit        - Physical unit
%       .dimensions  - Cell array of dimension names
%
%   Input:
%       simulation - Main simulation structure

%% PRELIMINARY OPERATIONS

% Load the files and read the version
index_temp = find(strcmp({simulation.run.name},'b2mn.exe.dir/tracing/blne.trc'));
index_final = find(strcmp({simulation.run.name},'tracing/blne.trc'));

if isempty(index_temp) && isempty(index_final)
   error('Error: blne.trc not found');
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

% Map of base prefixes to human-readable descriptions
description_map = {
    'pwr_totl',  'Total power'
    'tot_core',  'Total input power from core'
    'tot_targ',  'Total power to targets'
    'tot_wall',  'Total power to wall'
    'tot_rad',   'Total radiated power'
    'heat_cor',  'Heat crossing core boundary'
    'ptnt_cor',  'Potential energy at core boundary'
    'ntrl_cor',  'Neutral energy loss towards core'
    'plsm_trg',  'Plasma energy load to targets'
    'ntrl_trg',  'Neutrals energy load to targets'
    'plsm_wll',  'Plasma energy load to wall'
    'ntrl_wll',  'Neutrals energy load to wall'
    'pwr_plsm',  'Plasma energy load'
    'pwr_neut',  'Neutrals energy load'
    'pwr_ionz',  'Energy released by ionizations'
    'pwr_diss',  'Energy released by dissociations'
    'brms_rad',  'Bremsstrahlung radiation'
    'ntrl_rad',  'Neutrals radiation'
    'imp_rad',   'Impurity line radiation'
};

% Sort prefixes by length (longest first) for correct matching
prefix_lengths = cellfun(@length, description_map(:,1));
[~, sort_idx] = sort(prefix_lengths, 'descend');
description_map = description_map(sort_idx,:);

% Map of surface suffixes to human-readable labels
surface_map = {
    'il', 'inner lower surface'
    'ol', 'outer lower surface'
    'iu', 'inner upper surface'
    'ou', 'outer upper surface'
    'wl', 'wall'
};

%% READ THE DATA

for i = 1:size(data,2)

    name = names{i+1};

    % Sanitize the column name for use as a valid MATLAB field name
    name = replace(name, '/', '_divided_');

    if strcmp(name, 'time')
        energy_balance.(name).value = data(:,i);
        energy_balance.(name).description = 'Time';
        energy_balance.(name).unit = 's';
        energy_balance.(name).dimensions = {'time'};
    else
        % Skip columns with names that are not valid MATLAB identifiers
        % (e.g. placeholder columns like '-' when no impurities are present)
        if ~isvarname(name)
            continue;
        end

        % Find the matching prefix and build description
        description = name;
        matched = false;

        for j = 1:size(description_map,1)
            prefix = description_map{j,1};

            if strcmp(name, prefix)
                % Exact match (no suffix), e.g. pwr_totl, tot_core, tot_rad
                description = description_map{j,2};
                matched = true;
                break;

            elseif startsWith(name, [prefix '_'])
                suffix = name(length(prefix)+2:end);

                % Check if suffix is a known surface
                surf_idx = find(strcmp(surface_map(:,1), suffix));
                if ~isempty(surf_idx)
                    description = sprintf('%s (%s)', description_map{j,2}, surface_map{surf_idx,2});
                else
                    % Suffix is a species name (e.g. imp_rad_He)
                    description = sprintf('%s (%s)', description_map{j,2}, suffix);
                end
                matched = true;
                break;
            end
        end

        if ~matched
            description = name;
        end

        energy_balance.(name).value = data(:,i);
        energy_balance.(name).description = description;
        energy_balance.(name).unit = 'W';
        energy_balance.(name).dimensions = {'time'};
    end

end

fprintf('Energy balance time traces from blne.trc read\n');

end
