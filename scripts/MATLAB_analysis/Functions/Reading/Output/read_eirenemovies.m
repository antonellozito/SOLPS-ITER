function eirene_movies = read_eirenemovies(simulation)
%
% read_eirenemovies reads the eirenemovies.nc file created by B2.5
% Output is the struct "eirene_movies" with the 2D distributions of
% the Eirene state variables on the triangular grid
% at all simulated times
%
% input: main simulation structure

% TODO: fort46_to_triangles for the unstructured version does not work

%% PRELIMINARY OPERATIONS

eirene_movies = [];

% Load the file (fort.46)

index = find(contains({simulation.run.name},'fort.46'));
if isempty(index)
    error('Error: fort.46 not found');
end
file = simulation.run(index).file;
fid = fopen(file);
if (fid == -1)
    error('Error: fort.46 not found');
end

% Read the dimensions (fort.46)

ntri = fscanf(fid,'%d',1);
ver  = fscanf(fid,'%d',1);

eirene_movies.ntri = ntri;

fgetl(fid);

dims = fscanf(fid,'%d',3);
natm = dims(1);
nmol = dims(2);
nion = dims(3);
eirene_movies.natm = natm;
eirene_movies.nmol = nmol;
eirene_movies.nion = nion;

line = fgetl(fid);
for i = 1:natm
    line = fgetl(fid);
    eirene_movies.species_atm{i} = strtrim(line);
end
for i = 1:nmol
    line = fgetl(fid);
    eirene_movies.species_mol{i} = strtrim(line);
end
for i = 1:nion
    line = fgetl(fid);
    eirene_movies.species_ion{i} = strtrim(line);
end

for i = 1:natm
    switch eirene_movies.species_atm{i}
        case 'D'
            eirene_movies.mass_atm{i} = 2;
        case 'HE'
            eirene_movies.mass_atm{i} = 4;
        case 'BE'
            eirene_movies.mass_atm{i} = 9;
        case 'N'
            eirene_movies.mass_atm{i} = 14;
        case 'NE'
            eirene_movies.mass_atm{i} = 20;
        case 'AR'
            eirene_movies.mass_atm{i} = 40;
        case 'W'
            eirene_movies.mass_atm{i} = 184;
    end
end
for i = 1:nmol
    switch eirene_movies.species_mol{i}
        case 'D2'
            eirene_movies.mass_mol{i} = 4;
    end
end
for i = 1:nion
    switch eirene_movies.species_ion{i}
        case 'D2+'
            eirene_movies.mass_ion{i} = 4;
    end
end

eV    = 1.6022e-19;
pm    = 1.6726e-27;
kB    = 1.3806e-23;

frewind(fid);

fclose(fid);

% Load the file (eirenemovies.nc)

index = find(contains({simulation.run.name},'eirenemovies.nc'));
if isempty(index)
    error('Error: eirenemovies.nc not found');
end
file = simulation.run(index).file;
fid = fopen(file);
if (fid == -1)
    error('Error: eirenemovies.nc not found');
end

ft35 = read_fort35(simulation);
if isfield(ft35,'plasma_cell')
    version = 'unstructured';
    geometry = read_b2fgmtry(simulation);
    nCi = geometry.nCi;
else
    version = 'structured';
end

eV    = 1.6022e-19;
pm    = 1.6726e-27;
kB    = 1.3806e-23;

%% READ THE FIELDS

eirene_movies.times = ncread(file,'times');

eirene_movies = set_netcdf_fields(eirene_movies, file, {
    'n_atm', 'pdena';
    'n_mol', 'pdenm';
    'e_atm', 'edena';
    'e_mol', 'edenm';
    'm_atm_x', 'vxdena';
    'm_mol_x', 'vxdenm';
    'm_atm_y', 'vydena';
    'm_mol_y', 'vydenm';
    'm_atm_z', 'vzdena';
    'm_mol_z', 'vzdenm';
});

T_atm = zeros(size(eirene_movies.n_atm.value));
p_atm = zeros(size(eirene_movies.n_atm.value));
for i = 1:size(eirene_movies.n_atm.value, 2)
    T_atm(:, i, :) = ((2 / 3) .* eirene_movies.e_atm.value(:, i, :)) ./ eirene_movies.n_atm.value(:, i, :);
    p_atm(:, i, :) = ((2 / 3) .* eirene_movies.e_atm.value(:, i, :) .* eV);
end
eirene_movies = set_output_field(eirene_movies, 'T_atm', T_atm, ...
    'Atom temperature', 'eV', eirene_movies.n_atm.dimensions);
eirene_movies = set_output_field(eirene_movies, 'p_atm', p_atm, ...
    'Atom pressure', 'Pa', eirene_movies.n_atm.dimensions);

T_mol = zeros(size(eirene_movies.n_mol.value));
p_mol = zeros(size(eirene_movies.n_mol.value));
for i = 1:size(eirene_movies.n_mol.value, 2)
    T_mol(:, i, :) = ((2 / 3) .* eirene_movies.e_mol.value(:, i, :)) ./ eirene_movies.n_mol.value(:, i, :);
    p_mol(:, i, :) = ((2 / 3) .* eirene_movies.e_mol.value(:, i, :) .* eV);
end
eirene_movies = set_output_field(eirene_movies, 'T_mol', T_mol, ...
    'Molecular temperature', 'eV', eirene_movies.n_mol.dimensions);
eirene_movies = set_output_field(eirene_movies, 'p_mol', p_mol, ...
    'Molecular pressure', 'Pa', eirene_movies.n_mol.dimensions);

f_atm_x = zeros(size(eirene_movies.n_atm.value));
f_atm_y = zeros(size(eirene_movies.n_atm.value));
f_atm_z = zeros(size(eirene_movies.n_atm.value));
f_atm = zeros(size(eirene_movies.n_atm.value));
v_atm = zeros(size(eirene_movies.n_atm.value));
for i = 1:size(eirene_movies.n_atm.value, 2)
    f_atm_x(:, i, :) = eirene_movies.m_atm_x.value(:, i, :) ./ (eirene_movies.mass_atm{i} * pm);
    f_atm_y(:, i, :) = eirene_movies.m_atm_y.value(:, i, :) ./ (eirene_movies.mass_atm{i} * pm);
    f_atm_z(:, i, :) = eirene_movies.m_atm_z.value(:, i, :) ./ (eirene_movies.mass_atm{i} * pm);
    f_atm(:, i, :) = sqrt(f_atm_x(:, i, :) .^ 2 + f_atm_y(:, i, :) .^ 2 + f_atm_z(:, i, :) .^ 2);
    v_atm(:, i, :) = f_atm(:, i, :) ./ eirene_movies.n_atm.value(:, i, :);
end
eirene_movies = set_output_field(eirene_movies, 'f_atm_x', f_atm_x, ...
    'Atom x-directed particle flux density', 'm^-2 s^-1', eirene_movies.m_atm_x.dimensions);
eirene_movies = set_output_field(eirene_movies, 'f_atm_y', f_atm_y, ...
    'Atom y-directed particle flux density', 'm^-2 s^-1', eirene_movies.m_atm_y.dimensions);
eirene_movies = set_output_field(eirene_movies, 'f_atm_z', f_atm_z, ...
    'Atom z-directed particle flux density', 'm^-2 s^-1', eirene_movies.m_atm_z.dimensions);
eirene_movies = set_output_field(eirene_movies, 'f_atm', f_atm, ...
    'Atom particle flux density', 'm^-2 s^-1', eirene_movies.m_atm_x.dimensions);
eirene_movies = set_output_field(eirene_movies, 'v_atm', v_atm, ...
    'Atom particle flow velocity', 'm s^-1', eirene_movies.n_atm.dimensions);

f_mol_x = zeros(size(eirene_movies.n_mol.value));
f_mol_y = zeros(size(eirene_movies.n_mol.value));
f_mol_z = zeros(size(eirene_movies.n_mol.value));
f_mol = zeros(size(eirene_movies.n_mol.value));
v_mol = zeros(size(eirene_movies.n_mol.value));
for i = 1:size(eirene_movies.n_mol.value, 2)
    f_mol_x(:, i, :) = eirene_movies.m_mol_x.value(:, i, :) ./ (eirene_movies.mass_mol{i} * pm);
    f_mol_y(:, i, :) = eirene_movies.m_mol_y.value(:, i, :) ./ (eirene_movies.mass_mol{i} * pm);
    f_mol_z(:, i, :) = eirene_movies.m_mol_z.value(:, i, :) ./ (eirene_movies.mass_mol{i} * pm);
    f_mol(:, i, :) = sqrt(f_mol_x(:, i, :) .^ 2 + f_mol_y(:, i, :) .^ 2 + f_mol_z(:, i, :) .^ 2);
    v_mol(:, i, :) = f_mol(:, i, :) ./ eirene_movies.n_mol.value(:, i, :);
end
eirene_movies = set_output_field(eirene_movies, 'f_mol_x', f_mol_x, ...
    'Molecular x-directed particle flux density', 'm^-2 s^-1', eirene_movies.m_mol_x.dimensions);
eirene_movies = set_output_field(eirene_movies, 'f_mol_y', f_mol_y, ...
    'Molecular y-directed particle flux density', 'm^-2 s^-1', eirene_movies.m_mol_y.dimensions);
eirene_movies = set_output_field(eirene_movies, 'f_mol_z', f_mol_z, ...
    'Molecular z-directed particle flux density', 'm^-2 s^-1', eirene_movies.m_mol_z.dimensions);
eirene_movies = set_output_field(eirene_movies, 'f_mol', f_mol, ...
    'Molecular particle flux density', 'm^-2 s^-1', eirene_movies.m_mol_x.dimensions);
eirene_movies = set_output_field(eirene_movies, 'v_mol', v_mol, ...
    'Molecular particle flow velocity', 'm s^-1', eirene_movies.n_mol.dimensions);

V_atm = zeros(size(eirene_movies.n_atm.value));
F_atm = zeros(size(eirene_movies.n_atm.value));
for i = 1:natm
    V_atm(:, i, :) = sqrt((8 * kB .* (eirene_movies.T_atm.value(:, i, :) ./ 8.617e-5)) ./ (pi * eirene_movies.mass_atm{i} * pm));
    F_atm(:, i, :) = (eirene_movies.n_atm.value(:, i, :) .* V_atm(:, i, :)) ./ 4;
end
eirene_movies = set_output_field(eirene_movies, 'V_atm', V_atm, ...
    'Mean atom particle velocity', 'm s^-1', eirene_movies.n_atm.dimensions);
eirene_movies = set_output_field(eirene_movies, 'F_atm', F_atm, ...
    'Mean atom particle flux density', 'm^-2 s^-1', eirene_movies.n_atm.dimensions);

V_mol = zeros(size(eirene_movies.n_mol.value));
F_mol = zeros(size(eirene_movies.n_mol.value));
for i = 1:nmol
    V_mol(:, i, :) = sqrt((8 * kB .* (eirene_movies.T_mol.value(:, i, :) ./ 8.617e-5)) ./ (pi * eirene_movies.mass_mol{i} * pm));
    F_mol(:, i, :) = (eirene_movies.n_mol.value(:, i, :) .* V_mol(:, i, :)) ./ 4;
end
eirene_movies = set_output_field(eirene_movies, 'V_mol', V_mol, ...
    'Mean molecular particle velocity', 'm s^-1', eirene_movies.n_mol.dimensions);
eirene_movies = set_output_field(eirene_movies, 'F_mol', F_mol, ...
    'Mean molecular particle flux density', 'm^-2 s^-1', eirene_movies.n_mol.dimensions);

if strcmp(version,'unstructured')

    % for i = 1:size(eirene_movies.n_atm,3)
    %
    %     eirene_movies.n_atm(:,:,i) = fort46_to_triangles(eirene_movies.n_atm(:,:,i),nCi,ft35);
    %     eirene_movies.n_mol(:,:,i) = fort46_to_triangles(eirene_movies.n_mol(:,:,i),nCi,ft35);
    %     eirene_movies.n_ion(:,:,i) = fort46_to_triangles(eirene_movies.n_ion(:,:,i),nCi,ft35);
    %
    %     eirene_movies.e_atm(:,:,i) = fort46_to_triangles(eirene_movies.e_atm(:,:,i),nCi,ft35);
    %     eirene_movies.e_mol(:,:,i) = fort46_to_triangles(eirene_movies.e_mol(:,:,i),nCi,ft35);
    %     eirene_movies.e_ion(:,:,i) = fort46_to_triangles(eirene_movies.e_ion(:,:,i),nCi,ft35);
    %
    %     eirene_movies.T_atm(:,:,i) = fort46_to_triangles(eirene_movies.T_atm(:,:,i),nCi,ft35);
    %     eirene_movies.T_mol(:,:,i) = fort46_to_triangles(eirene_movies.T_mol(:,:,i),nCi,ft35);
    %     eirene_movies.T_ion(:,:,i) = fort46_to_triangles(eirene_movies.T_ion(:,:,i),nCi,ft35);
    %
    %     eirene_movies.p_atm(:,:,i) = fort46_to_triangles(eirene_movies.p_atm(:,:,i),nCi,ft35);
    %     eirene_movies.p_mol(:,:,i) = fort46_to_triangles(eirene_movies.p_mol(:,:,i),nCi,ft35);
    %     eirene_movies.p_ion(:,:,i) = fort46_to_triangles(eirene_movies.p_ion(:,:,i),nCi,ft35);
    %
    %     eirene_movies.m_atm_x(:,:,i) = fort46_to_triangles(eirene_movies.m_atm_x(:,:,i),nCi,ft35);
    %     eirene_movies.m_mol_x(:,:,i) = fort46_to_triangles(eirene_movies.m_mol_x(:,:,i),nCi,ft35);
    %     eirene_movies.m_ion_x(:,:,i) = fort46_to_triangles(eirene_movies.m_ion_x(:,:,i),nCi,ft35);
    %
    %     eirene_movies.m_atm_y(:,:,i) = fort46_to_triangles(eirene_movies.m_atm_y(:,:,i),nCi,ft35);
    %     eirene_movies.m_mol_y(:,:,i) = fort46_to_triangles(eirene_movies.m_mol_y(:,:,i),nCi,ft35);
    %     eirene_movies.m_ion_y(:,:,i) = fort46_to_triangles(eirene_movies.m_ion_y(:,:,i),nCi,ft35);
    %
    %     eirene_movies.m_atm_z(:,:,i) = fort46_to_triangles(eirene_movies.m_atm_z(:,:,i),nCi,ft35);
    %     eirene_movies.m_mol_z(:,:,i) = fort46_to_triangles(eirene_movies.m_mol_z(:,:,i),nCi,ft35);
    %     eirene_movies.m_ion_z(:,:,i) = fort46_to_triangles(eirene_movies.m_ion_z(:,:,i),nCi,ft35);
    %
    % end

end

fprintf('Time-dependent neutrals state variables from eirenemovies.nc read\n');

fclose(fid);

end
