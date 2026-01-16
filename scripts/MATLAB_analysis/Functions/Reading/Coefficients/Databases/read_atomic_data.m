function atomic_data = read_atomic_data(data_file)
%
% read_atomic data reads various atomic-related data
% for various species, namely:
% - Atomic number
% - Atomic mass
% - Surface binding energy
% - Density
% according to the incatm file present in the B2.5 database
%
%% PRELIMINARY OPERATIONS

fid = fopen(data_file);

%% READ THE DATA

i = 1;
while true
    line = fgetl(fid);
    if ~ischar(line)
        break;
    end
    text = textscan(line,'%s %d %f %f %f');
    atomic_data(i).species = char(text{1});
    atomic_data(i).atomic_number = double(text{2});
    atomic_data(i).atomic_mass = double(text{3}); % in AMU
    atomic_data(i).surface_binding_energy = double(text{4}); % in ???
    atomic_data(i).density = double(text{5}); % in g/L
    i = i+1;
end

%% CLOSE THE FILE

fclose(fid);

end
