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

temp_data = ncread(file,'pdena');
info = ncinfo(file,'pdena');
eirene_movies.n_atm.value = temp_data;
eirene_movies.n_atm.description = ncreadatt(file,'pdena','long_name');
eirene_movies.n_atm.unit = ncreadatt(file,'pdena','units');
eirene_movies.n_atm.dimensions = {info.Dimensions.Name};

temp_data = ncread(file,'pdenm');
info = ncinfo(file,'pdenm');
eirene_movies.n_mol.value = temp_data;
eirene_movies.n_mol.description = ncreadatt(file,'pdenm','long_name');
eirene_movies.n_mol.unit = ncreadatt(file,'pdenm','units');
eirene_movies.n_mol.dimensions = {info.Dimensions.Name};

temp_data = ncread(file,'edena');
info = ncinfo(file,'edena');
eirene_movies.e_atm.value = temp_data;
eirene_movies.e_atm.description = ncreadatt(file,'edena','long_name');
eirene_movies.e_atm.unit = ncreadatt(file,'edena','units');
eirene_movies.e_atm.dimensions = {info.Dimensions.Name};

temp_data = ncread(file,'edenm');
info = ncinfo(file,'edenm');
eirene_movies.e_mol.value = temp_data;
eirene_movies.e_mol.description = ncreadatt(file,'edenm','long_name');
eirene_movies.e_mol.unit = ncreadatt(file,'edenm','units');
eirene_movies.e_mol.dimensions = {info.Dimensions.Name};

for i = 1:size(eirene_movies.n_atm.value,2)
    eirene_movies.T_atm.value(:,i,:) = ((2/3).*eirene_movies.e_atm.value(:,i,:))./(eirene_movies.n_atm.value(:,i,:));
    eirene_movies.p_atm.value(:,i,:) = ((2/3).*eirene_movies.e_atm.value(:,i,:).*eV);
end
eirene_movies.T_atm.description = 'Atom temperature';
eirene_movies.T_atm.unit = 'eV';
eirene_movies.T_atm.dimensions = eirene_movies.n_atm.dimensions;

eirene_movies.p_atm.description = 'Atom pressure';
eirene_movies.p_atm.unit = 'Pa';
eirene_movies.p_atm.dimensions = eirene_movies.n_atm.dimensions;

for i = 1:size(eirene_movies.n_mol.value,2)
    eirene_movies.T_mol.value(:,i,:) = ((2/3).*eirene_movies.e_mol.value(:,i,:))./(eirene_movies.n_mol.value(:,i,:));
    eirene_movies.p_mol.value(:,i,:) = ((2/3).*eirene_movies.e_mol.value(:,i,:).*eV);
end
eirene_movies.T_mol.description = 'Molecular temperature';
eirene_movies.T_mol.unit = 'eV';
eirene_movies.T_mol.dimensions = eirene_movies.n_mol.dimensions;

eirene_movies.p_mol.description = 'Molecular pressure';
eirene_movies.p_mol.unit = 'Pa';
eirene_movies.p_mol.dimensions = eirene_movies.n_mol.dimensions;

temp_data = ncread(file,'vxdena');
info = ncinfo(file,'vxdena');
eirene_movies.m_atm_x.value = temp_data;
eirene_movies.m_atm_x.description = ncreadatt(file,'vxdena','long_name');
eirene_movies.m_atm_x.unit = ncreadatt(file,'vxdena','units');
eirene_movies.m_atm_x.dimensions = {info.Dimensions.Name};

temp_data = ncread(file,'vxdenm');
info = ncinfo(file,'vxdenm');
eirene_movies.m_mol_x.value = temp_data;
eirene_movies.m_mol_x.description = ncreadatt(file,'vxdenm','long_name');
eirene_movies.m_mol_x.unit = ncreadatt(file,'vxdenm','units');
eirene_movies.m_mol_x.dimensions = {info.Dimensions.Name};

temp_data = ncread(file,'vydena');
info = ncinfo(file,'vydena');
eirene_movies.m_atm_y.value = temp_data;
eirene_movies.m_atm_y.description = ncreadatt(file,'vydena','long_name');
eirene_movies.m_atm_y.unit = ncreadatt(file,'vydena','units');
eirene_movies.m_atm_y.dimensions = {info.Dimensions.Name};

temp_data = ncread(file,'vydenm');
info = ncinfo(file,'vydenm');
eirene_movies.m_mol_y.value = temp_data;
eirene_movies.m_mol_y.description = ncreadatt(file,'vydenm','long_name');
eirene_movies.m_mol_y.unit = ncreadatt(file,'vydenm','units');
eirene_movies.m_mol_y.dimensions = {info.Dimensions.Name};

temp_data = ncread(file,'vzdena');
info = ncinfo(file,'vzdena');
eirene_movies.m_atm_z.value = temp_data;
eirene_movies.m_atm_z.description = ncreadatt(file,'vzdena','long_name');
eirene_movies.m_atm_z.unit = ncreadatt(file,'vzdena','units');
eirene_movies.m_atm_z.dimensions = {info.Dimensions.Name};

temp_data = ncread(file,'vzdenm');
info = ncinfo(file,'vzdenm');
eirene_movies.m_mol_z.value = temp_data;
eirene_movies.m_mol_z.description = ncreadatt(file,'vzdenm','long_name');
eirene_movies.m_mol_z.unit = ncreadatt(file,'vzdenm','units');
eirene_movies.m_mol_z.dimensions = {info.Dimensions.Name};

for i = 1:size(eirene_movies.n_atm.value,2)
    eirene_movies.f_atm_x.value(:,i,:) = (eirene_movies.m_atm_x.value(:,i,:)./(eirene_movies.mass_atm{i}*pm));
    eirene_movies.f_atm_y.value(:,i,:) = (eirene_movies.m_atm_y.value(:,i,:)./(eirene_movies.mass_atm{i}*pm));
    eirene_movies.f_atm_z.value(:,i,:) = (eirene_movies.m_atm_z.value(:,i,:)./(eirene_movies.mass_atm{i}*pm));
    eirene_movies.f_atm.value(:,i,:) = ...
        ((eirene_movies.f_atm_x.value(:,i,:)).^2+(eirene_movies.f_atm_y.value(:,i,:)).^2+(eirene_movies.f_atm_z.value(:,i,:)).^2).^(1/2);
    eirene_movies.v_atm.value(:,i,:) = ...
        ((eirene_movies.f_atm.value(:,i,:).*1)./eirene_movies.n_atm.value(:,i,:));
end
eirene_movies.f_atm_x.description = 'Atom x-directed particle flux density';
eirene_movies.f_atm_x.unit = 'm^-2 s^-1';
eirene_movies.f_atm_x.dimensions = eirene_movies.m_atm_x.dimensions;

eirene_movies.f_atm_y.description = 'Atom y-directed particle flux density';
eirene_movies.f_atm_y.unit = 'm^-2 s^-1';
eirene_movies.f_atm_y.dimensions = eirene_movies.m_atm_y.dimensions;

eirene_movies.f_atm_z.description = 'Atom z-directed particle flux density';
eirene_movies.f_atm_z.unit = 'm^-2 s^-1';
eirene_movies.f_atm_z.dimensions = eirene_movies.m_atm_z.dimensions;

eirene_movies.f_atm.description = 'Atom particle flux density';
eirene_movies.f_atm.unit = 'm^-2 s^-1';
eirene_movies.f_atm.dimensions = eirene_movies.m_atm_x.dimensions;

eirene_movies.v_atm.description = 'Atom particle flow velocity';
eirene_movies.v_atm.unit = 'm s^-1';
eirene_movies.v_atm.dimensions = eirene_movies.n_atm.dimensions;

for i = 1:size(eirene_movies.n_mol.value,2)
    eirene_movies.f_mol_x.value(:,i,:) = (eirene_movies.m_mol_x.value(:,i,:)./(eirene_movies.mass_mol{i}*pm));
    eirene_movies.f_mol_y.value(:,i,:) = (eirene_movies.m_mol_y.value(:,i,:)./(eirene_movies.mass_mol{i}*pm));
    eirene_movies.f_mol_z.value(:,i,:) = (eirene_movies.m_mol_z.value(:,i,:)./(eirene_movies.mass_mol{i}*pm));
    eirene_movies.f_mol.value(:,i,:) = ...
        ((eirene_movies.f_mol_x.value(:,i,:)).^2+(eirene_movies.f_mol_y.value(:,i,:)).^2+(eirene_movies.f_mol_z.value(:,i,:)).^2).^(1/2);
    eirene_movies.v_mol.value(:,i,:) = ...
        ((eirene_movies.f_mol.value(:,i,:).*1)./eirene_movies.n_mol.value(:,i,:));
end
eirene_movies.f_mol_x.description = 'Molecular x-directed particle flux density';
eirene_movies.f_mol_x.unit = 'm^-2 s^-1';
eirene_movies.f_mol_x.dimensions = eirene_movies.m_mol_x.dimensions;

eirene_movies.f_mol_y.description = 'Molecular y-directed particle flux density';
eirene_movies.f_mol_y.unit = 'm^-2 s^-1';
eirene_movies.f_mol_y.dimensions = eirene_movies.m_mol_y.dimensions;

eirene_movies.f_mol_z.description = 'Molecular z-directed particle flux density';
eirene_movies.f_mol_z.unit = 'm^-2 s^-1';
eirene_movies.f_mol_z.dimensions = eirene_movies.m_mol_z.dimensions;

eirene_movies.f_mol.description = 'Molecular particle flux density';
eirene_movies.f_mol.unit = 'm^-2 s^-1';
eirene_movies.f_mol.dimensions = eirene_movies.m_mol_x.dimensions;

eirene_movies.v_mol.description = 'Molecular particle flow velocity';
eirene_movies.v_mol.unit = 'm s^-1';
eirene_movies.v_mol.dimensions = eirene_movies.n_mol.dimensions;

for i = 1:natm
    eirene_movies.V_atm.value(:,i,:) = sqrt((8*kB.*(eirene_movies.T_atm.value(:,i,:)./8.617e-5))./(pi*eirene_movies.mass_atm{i}*pm));
    eirene_movies.F_atm.value(:,i,:) = (eirene_movies.n_atm.value(:,i,:).*eirene_movies.V_atm.value(:,i,:))./4;
end
eirene_movies.V_atm.description = 'Mean atom particle velocity';
eirene_movies.V_atm.unit = 'm s^-1';
eirene_movies.V_atm.dimensions = eirene_movies.n_atm.dimensions;

eirene_movies.F_atm.description = 'Mean atom particle flux density';
eirene_movies.F_atm.unit = 'm^-2 s^-1';
eirene_movies.F_atm.dimensions = eirene_movies.n_atm.dimensions;

for i = 1:nmol
    eirene_movies.V_mol.value(:,i,:) = sqrt((8*kB.*(eirene_movies.T_mol.value(:,i,:)./8.617e-5))./(pi*eirene_movies.mass_mol{i}*pm));
    eirene_movies.F_mol.value(:,i,:) = (eirene_movies.n_mol.value(:,i,:).*eirene_movies.V_mol.value(:,i,:))./4;
end
eirene_movies.V_mol.description = 'Mean molecular particle velocity';
eirene_movies.V_mol.unit = 'm s^-1';
eirene_movies.V_mol.dimensions = eirene_movies.n_mol.dimensions;

eirene_movies.F_mol.description = 'Mean molecular particle flux density';
eirene_movies.F_mol.unit = 'm^-2 s^-1';
eirene_movies.F_mol.dimensions = eirene_movies.n_mol.dimensions;

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

fprintf('Structure EIRENE_MOVIES from eirenemovies.nc read.\n');

fclose(fid);

end
