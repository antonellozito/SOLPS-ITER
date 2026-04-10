function neutrals_triangles = read_fort46(simulation)
%
% read_ft46 reads the fort.46 file created by EIRENE
% Output is the struct "neutrals_triangles" with all the data fields in the fort.46 file
%
% input: main simulation structure
%
%% PRELIMINARY OPERATIONS

% Load the file

index = find(contains({simulation.run.name},'fort.46'));
if isempty(index)
   error('Error: fort.46 not found');
end
file = simulation.run(index).file;
fid = fopen(file);
if (fid == -1)
   error('Error: fort.46 not found');
end

% Read the dimensions

ntri = fscanf(fid,'%d',1);
ver  = fscanf(fid,'%d',1);

ft35 = read_fort35(simulation);
if isfield(ft35,'plasma_cell')
    version = 'unstructured';
    geometry = read_b2fgmtry(simulation);
    nCi = geometry.nCi;
else
    version = 'structured';
end

neutrals_triangles.ntri = ntri;

if ver ~= 20160513 && ver ~= 20160829 && ver ~= 20170930  && ver ~= 20231224
    error('Error: read_ft46: unknown format of fort.46 file');
end

fgetl(fid);

dims = fscanf(fid,'%d',3);
natm = dims(1);
nmol = dims(2);
nion = dims(3);
neutrals_triangles.natm = natm;
neutrals_triangles.nmol = nmol;
neutrals_triangles.nion = nion;

line = fgetl(fid);
for i = 1:natm
    line = fgetl(fid);
    neutrals_triangles.species_atm{i} = strtrim(line);
end
for i = 1:nmol
    line = fgetl(fid);
    neutrals_triangles.species_mol{i} = strtrim(line);
end
for i = 1:nion
    line = fgetl(fid);
    neutrals_triangles.species_ion{i} = strtrim(line);
end

for i = 1:natm
    switch neutrals_triangles.species_atm{i}
        case 'D'
            neutrals_triangles.mass_atm{i} = 2;
        case 'HE'
            neutrals_triangles.mass_atm{i} = 4;
        case 'BE'
            neutrals_triangles.mass_atm{i} = 9;
        case 'N'
            neutrals_triangles.mass_atm{i} = 14;
        case 'NE'
            neutrals_triangles.mass_atm{i} = 20;
        case 'AR'
            neutrals_triangles.mass_atm{i} = 40;
        case 'W'
            neutrals_triangles.mass_atm{i} = 184;
    end
end
for i = 1:nmol
    switch neutrals_triangles.species_mol{i}
        case 'D2'
            neutrals_triangles.mass_mol{i} = 4;
    end
end
for i = 1:nion
    switch neutrals_triangles.species_ion{i}
        case 'D2+'
            neutrals_triangles.mass_ion{i} = 4;
    end
end

eV    = 1.6022e-19;
pm    = 1.6726e-27;
kB    = 1.3806e-23;

%% READ THE DATA

% State variables

tri_atm_dims = {'ntri', 'natm'};
tri_mol_dims = {'ntri', 'nmol'};
tri_ion_dims = {'ntri', 'nion'};

neutrals_triangles = set_ft_real_grid_field(neutrals_triangles, fid, ver, ...
    'n_atm', 'pdena', [ntri, natm], 'Atom particle density', 'm^-3', tri_atm_dims, 1e6);
neutrals_triangles = set_ft_real_grid_field(neutrals_triangles, fid, ver, ...
    'n_mol', 'pdenm', [ntri, nmol], 'Molecular particle density', 'm^-3', tri_mol_dims, 1e6);
neutrals_triangles = set_ft_real_grid_field(neutrals_triangles, fid, ver, ...
    'n_ion', 'pdeni', [ntri, nion], 'Test ion particle density', 'm^-3', tri_ion_dims, 1e6);
neutrals_triangles = set_ft_real_grid_field(neutrals_triangles, fid, ver, ...
    'e_atm', 'edena', [ntri, natm], 'Atom energy density', 'eV m^-3', tri_atm_dims, 1e6);
neutrals_triangles = set_ft_real_grid_field(neutrals_triangles, fid, ver, ...
    'e_mol', 'edenm', [ntri, nmol], 'Molecular energy density', 'eV m^-3', tri_mol_dims, 1e6);
neutrals_triangles = set_ft_real_grid_field(neutrals_triangles, fid, ver, ...
    'e_ion', 'edeni', [ntri, nion], 'Test ion energy density', 'eV m^-3', tri_ion_dims, 1e6);

T_atm = zeros(ntri, natm);
p_atm = zeros(ntri, natm);
for i = 1:natm
    T_atm(:, i) = ((2 / 3) .* neutrals_triangles.e_atm.value(:, i)) ./ neutrals_triangles.n_atm.value(:, i);
    p_atm(:, i) = ((2 / 3) .* neutrals_triangles.e_atm.value(:, i) .* eV);
end
neutrals_triangles = set_output_field(neutrals_triangles, 'T_atm', T_atm, ...
    'Atom temperature', 'eV', tri_atm_dims);
neutrals_triangles = set_output_field(neutrals_triangles, 'p_atm', p_atm, ...
    'Atom pressure', 'Pa', tri_atm_dims);

T_mol = zeros(ntri, nmol);
p_mol = zeros(ntri, nmol);
for i = 1:nmol
    T_mol(:, i) = ((2 / 3) .* neutrals_triangles.e_mol.value(:, i)) ./ neutrals_triangles.n_mol.value(:, i);
    p_mol(:, i) = ((2 / 3) .* neutrals_triangles.e_mol.value(:, i) .* eV);
end
neutrals_triangles = set_output_field(neutrals_triangles, 'T_mol', T_mol, ...
    'Molecular temperature', 'eV', tri_mol_dims);
neutrals_triangles = set_output_field(neutrals_triangles, 'p_mol', p_mol, ...
    'Molecular pressure', 'Pa', tri_mol_dims);

T_ion = zeros(ntri, nion);
p_ion = zeros(ntri, nion);
for i = 1:nion
    T_ion(:, i) = ((2 / 3) .* neutrals_triangles.e_ion.value(:, i)) ./ neutrals_triangles.n_ion.value(:, i);
    p_ion(:, i) = ((2 / 3) .* neutrals_triangles.e_ion.value(:, i) .* eV);
end
neutrals_triangles = set_output_field(neutrals_triangles, 'T_ion', T_ion, ...
    'Test ion temperature', 'eV', tri_ion_dims);
neutrals_triangles = set_output_field(neutrals_triangles, 'p_ion', p_ion, ...
    'Test ion pressure', 'Pa', tri_ion_dims);

neutrals_triangles = set_ft_real_grid_field(neutrals_triangles, fid, ver, ...
    'm_atm_x', 'vxdena', [ntri, natm], 'Atom x-directed momentum density', 'kg s^-1 m^-2', tri_atm_dims, 1e1);
neutrals_triangles = set_ft_real_grid_field(neutrals_triangles, fid, ver, ...
    'm_mol_x', 'vxdenm', [ntri, nmol], 'Molecular x-directed momentum density', 'kg s^-1 m^-2', tri_mol_dims, 1e1);
neutrals_triangles = set_ft_real_grid_field(neutrals_triangles, fid, ver, ...
    'm_ion_x', 'vxdeni', [ntri, nion], 'Test ion x-directed momentum density', 'kg s^-1 m^-2', tri_ion_dims, 1e1);
neutrals_triangles = set_ft_real_grid_field(neutrals_triangles, fid, ver, ...
    'm_atm_y', 'vydena', [ntri, natm], 'Atom y-directed momentum density', 'kg s^-1 m^-2', tri_atm_dims, 1e1);
neutrals_triangles = set_ft_real_grid_field(neutrals_triangles, fid, ver, ...
    'm_mol_y', 'vydenm', [ntri, nmol], 'Molecular y-directed momentum density', 'kg s^-1 m^-2', tri_mol_dims, 1e1);
neutrals_triangles = set_ft_real_grid_field(neutrals_triangles, fid, ver, ...
    'm_ion_y', 'vydeni', [ntri, nion], 'Test ion y-directed momentum density', 'kg s^-1 m^-2', tri_ion_dims, 1e1);
neutrals_triangles = set_ft_real_grid_field(neutrals_triangles, fid, ver, ...
    'm_atm_z', 'vzdena', [ntri, natm], 'Atom z-directed momentum density', 'kg s^-1 m^-2', tri_atm_dims, 1e1);
neutrals_triangles = set_ft_real_grid_field(neutrals_triangles, fid, ver, ...
    'm_mol_z', 'vzdenm', [ntri, nmol], 'Molecular z-directed momentum density', 'kg s^-1 m^-2', tri_mol_dims, 1e1);
neutrals_triangles = set_ft_real_grid_field(neutrals_triangles, fid, ver, ...
    'm_ion_z', 'vzdeni', [ntri, nion], 'Test ion z-directed momentum density', 'kg s^-1 m^-2', tri_ion_dims, 1e1);

f_atm_x = zeros(ntri, natm);
f_atm_y = zeros(ntri, natm);
f_atm_z = zeros(ntri, natm);
f_atm = zeros(ntri, natm);
v_atm = zeros(ntri, natm);
for i = 1:natm
    f_atm_x(:, i) = neutrals_triangles.m_atm_x.value(:, i) ./ (neutrals_triangles.mass_atm{i} * pm);
    f_atm_y(:, i) = neutrals_triangles.m_atm_y.value(:, i) ./ (neutrals_triangles.mass_atm{i} * pm);
    f_atm_z(:, i) = neutrals_triangles.m_atm_z.value(:, i) ./ (neutrals_triangles.mass_atm{i} * pm);
    f_atm(:, i) = sqrt(f_atm_x(:, i) .^ 2 + f_atm_y(:, i) .^ 2 + f_atm_z(:, i) .^ 2);
    v_atm(:, i) = f_atm(:, i) ./ neutrals_triangles.n_atm.value(:, i);
end
neutrals_triangles = set_output_field(neutrals_triangles, 'f_atm_x', f_atm_x, ...
    'Atom x-directed flux density', 'm^-2 s^-1', tri_atm_dims);
neutrals_triangles = set_output_field(neutrals_triangles, 'f_atm_y', f_atm_y, ...
    'Atom y-directed flux density', 'm^-2 s^-1', tri_atm_dims);
neutrals_triangles = set_output_field(neutrals_triangles, 'f_atm_z', f_atm_z, ...
    'Atom z-directed flux density', 'm^-2 s^-1', tri_atm_dims);
neutrals_triangles = set_output_field(neutrals_triangles, 'f_atm', f_atm, ...
    'Atom particle flux density', 'm^-2 s^-1', tri_atm_dims);
neutrals_triangles = set_output_field(neutrals_triangles, 'v_atm', v_atm, ...
    'Atom particle flow velocity', 'm s^-1', tri_atm_dims);

f_mol_x = zeros(ntri, nmol);
f_mol_y = zeros(ntri, nmol);
f_mol_z = zeros(ntri, nmol);
f_mol = zeros(ntri, nmol);
v_mol = zeros(ntri, nmol);
for i = 1:nmol
    f_mol_x(:, i) = neutrals_triangles.m_mol_x.value(:, i) ./ (neutrals_triangles.mass_mol{i} * pm);
    f_mol_y(:, i) = neutrals_triangles.m_mol_y.value(:, i) ./ (neutrals_triangles.mass_mol{i} * pm);
    f_mol_z(:, i) = neutrals_triangles.m_mol_z.value(:, i) ./ (neutrals_triangles.mass_mol{i} * pm);
    f_mol(:, i) = sqrt(f_mol_x(:, i) .^ 2 + f_mol_y(:, i) .^ 2 + f_mol_z(:, i) .^ 2);
    v_mol(:, i) = f_mol(:, i) ./ neutrals_triangles.n_mol.value(:, i);
end
neutrals_triangles = set_output_field(neutrals_triangles, 'f_mol_x', f_mol_x, ...
    'Molecular x-directed flux density', 'm^-2 s^-1', tri_mol_dims);
neutrals_triangles = set_output_field(neutrals_triangles, 'f_mol_y', f_mol_y, ...
    'Molecular y-directed flux density', 'm^-2 s^-1', tri_mol_dims);
neutrals_triangles = set_output_field(neutrals_triangles, 'f_mol_z', f_mol_z, ...
    'Molecular z-directed flux density', 'm^-2 s^-1', tri_mol_dims);
neutrals_triangles = set_output_field(neutrals_triangles, 'f_mol', f_mol, ...
    'Molecular particle flux density', 'm^-2 s^-1', tri_mol_dims);
neutrals_triangles = set_output_field(neutrals_triangles, 'v_mol', v_mol, ...
    'Molecular particle flow velocity', 'm s^-1', tri_mol_dims);

f_ion_x = zeros(ntri, nion);
f_ion_y = zeros(ntri, nion);
f_ion_z = zeros(ntri, nion);
f_ion = zeros(ntri, nion);
v_ion = zeros(ntri, nion);
for i = 1:nion
    f_ion_x(:, i) = neutrals_triangles.m_ion_x.value(:, i) ./ (neutrals_triangles.mass_ion{i} * pm);
    f_ion_y(:, i) = neutrals_triangles.m_ion_y.value(:, i) ./ (neutrals_triangles.mass_ion{i} * pm);
    f_ion_z(:, i) = neutrals_triangles.m_ion_z.value(:, i) ./ (neutrals_triangles.mass_ion{i} * pm);
    f_ion(:, i) = sqrt(f_ion_x(:, i) .^ 2 + f_ion_y(:, i) .^ 2 + f_ion_z(:, i) .^ 2);
    v_ion(:, i) = f_ion(:, i) ./ neutrals_triangles.n_ion.value(:, i);
end
neutrals_triangles = set_output_field(neutrals_triangles, 'f_ion_x', f_ion_x, ...
    'Test ion x-directed flux density', 'm^-2 s^-1', tri_ion_dims);
neutrals_triangles = set_output_field(neutrals_triangles, 'f_ion_y', f_ion_y, ...
    'Test ion y-directed flux density', 'm^-2 s^-1', tri_ion_dims);
neutrals_triangles = set_output_field(neutrals_triangles, 'f_ion_z', f_ion_z, ...
    'Test ion z-directed flux density', 'm^-2 s^-1', tri_ion_dims);
neutrals_triangles = set_output_field(neutrals_triangles, 'f_ion', f_ion, ...
    'Test ion particle flux density', 'm^-2 s^-1', tri_ion_dims);
neutrals_triangles = set_output_field(neutrals_triangles, 'v_ion', v_ion, ...
    'Test ion particle flow velocity', 'm s^-1', tri_ion_dims);

V_atm = zeros(ntri, natm);
F_atm = zeros(ntri, natm);
for i = 1:natm
    V_atm(:, i) = sqrt((8 * kB .* (neutrals_triangles.T_atm.value(:, i) ./ 8.617e-5)) ./ (pi * neutrals_triangles.mass_atm{i} * pm));
    F_atm(:, i) = (neutrals_triangles.n_atm.value(:, i) .* V_atm(:, i)) ./ 4;
end
neutrals_triangles = set_output_field(neutrals_triangles, 'V_atm', V_atm, ...
    'Mean atom particle velocity', 'm s^-1', tri_atm_dims);
neutrals_triangles = set_output_field(neutrals_triangles, 'F_atm', F_atm, ...
    'Mean atom particle flux density', 'm^-2 s^-1', tri_atm_dims);

V_mol = zeros(ntri, nmol);
F_mol = zeros(ntri, nmol);
for i = 1:nmol
    V_mol(:, i) = sqrt((8 * kB .* (neutrals_triangles.T_mol.value(:, i) ./ 8.617e-5)) ./ (pi * neutrals_triangles.mass_mol{i} * pm));
    F_mol(:, i) = (neutrals_triangles.n_mol.value(:, i) .* V_mol(:, i)) ./ 4;
end
neutrals_triangles = set_output_field(neutrals_triangles, 'V_mol', V_mol, ...
    'Mean molecular particle velocity', 'm s^-1', tri_mol_dims);
neutrals_triangles = set_output_field(neutrals_triangles, 'F_mol', F_mol, ...
    'Mean molecular particle flux density', 'm^-2 s^-1', tri_mol_dims);

V_ion = zeros(ntri, nion);
F_ion = zeros(ntri, nion);
for i = 1:nion
    V_ion(:, i) = sqrt((8 * kB .* (neutrals_triangles.T_ion.value(:, i) ./ 8.617e-5)) ./ (pi * neutrals_triangles.mass_ion{i} * pm));
    F_ion(:, i) = (neutrals_triangles.n_ion.value(:, i) .* V_ion(:, i)) ./ 4;
end
neutrals_triangles = set_output_field(neutrals_triangles, 'V_ion', V_ion, ...
    'Mean test ion particle velocity', 'm s^-1', tri_ion_dims);
neutrals_triangles = set_output_field(neutrals_triangles, 'F_ion', F_ion, ...
    'Mean test ion particle flux density', 'm^-2 s^-1', tri_ion_dims);

if strcmp(version,'structured')

    neutrals_triangles = set_ft_real_grid_field(neutrals_triangles, fid, ver, ...
        'vol', 'vol', [ntri], 'volume of the cell', 'm^3', {'ntri'}, 1e-6);

elseif strcmp(version,'unstructured')

    neutrals_triangles.n_atm.value = fort46_to_triangles(neutrals_triangles.n_atm.value,nCi,ft35);
    neutrals_triangles.n_mol.value = fort46_to_triangles(neutrals_triangles.n_mol.value,nCi,ft35);
    neutrals_triangles.n_ion.value = fort46_to_triangles(neutrals_triangles.n_ion.value,nCi,ft35);
    
    neutrals_triangles.e_atm.value = fort46_to_triangles(neutrals_triangles.e_atm.value,nCi,ft35);
    neutrals_triangles.e_mol.value = fort46_to_triangles(neutrals_triangles.e_mol.value,nCi,ft35);
    neutrals_triangles.e_ion.value = fort46_to_triangles(neutrals_triangles.e_ion.value,nCi,ft35);
    
    neutrals_triangles.T_atm.value = fort46_to_triangles(neutrals_triangles.T_atm.value,nCi,ft35);
    neutrals_triangles.T_mol.value = fort46_to_triangles(neutrals_triangles.T_mol.value,nCi,ft35);
    neutrals_triangles.T_ion.value = fort46_to_triangles(neutrals_triangles.T_ion.value,nCi,ft35);
    
    neutrals_triangles.p_atm.value = fort46_to_triangles(neutrals_triangles.p_atm.value,nCi,ft35);
    neutrals_triangles.p_mol.value = fort46_to_triangles(neutrals_triangles.p_mol.value,nCi,ft35);
    neutrals_triangles.p_ion.value = fort46_to_triangles(neutrals_triangles.p_ion.value,nCi,ft35);
    
    neutrals_triangles.m_atm_x.value = fort46_to_triangles(neutrals_triangles.m_atm_x.value,nCi,ft35);
    neutrals_triangles.m_mol_x.value = fort46_to_triangles(neutrals_triangles.m_mol_x.value,nCi,ft35);
    neutrals_triangles.m_ion_x.value = fort46_to_triangles(neutrals_triangles.m_ion_x.value,nCi,ft35);
    
    neutrals_triangles.m_atm_y.value = fort46_to_triangles(neutrals_triangles.m_atm_y.value,nCi,ft35);
    neutrals_triangles.m_mol_y.value = fort46_to_triangles(neutrals_triangles.m_mol_y.value,nCi,ft35);
    neutrals_triangles.m_ion_y.value = fort46_to_triangles(neutrals_triangles.m_ion_y.value,nCi,ft35);
    
    neutrals_triangles.m_atm_z.value = fort46_to_triangles(neutrals_triangles.m_atm_z.value,nCi,ft35);
    neutrals_triangles.m_mol_z.value = fort46_to_triangles(neutrals_triangles.m_mol_z.value,nCi,ft35);
    neutrals_triangles.m_ion_z.value = fort46_to_triangles(neutrals_triangles.m_ion_z.value,nCi,ft35);
    
    neutrals_triangles.f_atm_x.value = fort46_to_triangles(neutrals_triangles.f_atm_x.value,nCi,ft35);
    neutrals_triangles.f_mol_x.value = fort46_to_triangles(neutrals_triangles.f_mol_x.value,nCi,ft35);
    neutrals_triangles.f_ion_x.value = fort46_to_triangles(neutrals_triangles.f_ion_x.value,nCi,ft35);
    
    neutrals_triangles.f_atm_y.value = fort46_to_triangles(neutrals_triangles.f_atm_y.value,nCi,ft35);
    neutrals_triangles.f_mol_y.value = fort46_to_triangles(neutrals_triangles.f_mol_y.value,nCi,ft35);
    neutrals_triangles.f_ion_y.value = fort46_to_triangles(neutrals_triangles.f_ion_y.value,nCi,ft35);
    
    neutrals_triangles.f_atm_z.value = fort46_to_triangles(neutrals_triangles.f_atm_z.value,nCi,ft35);
    neutrals_triangles.f_mol_z.value = fort46_to_triangles(neutrals_triangles.f_mol_z.value,nCi,ft35);
    neutrals_triangles.f_ion_z.value = fort46_to_triangles(neutrals_triangles.f_ion_z.value,nCi,ft35);
    
    neutrals_triangles.V_atm.value = fort46_to_triangles(neutrals_triangles.V_atm.value,nCi,ft35);
    neutrals_triangles.V_mol.value = fort46_to_triangles(neutrals_triangles.V_mol.value,nCi,ft35);
    neutrals_triangles.V_ion.value = fort46_to_triangles(neutrals_triangles.V_ion.value,nCi,ft35);
    
    neutrals_triangles.F_atm.value = fort46_to_triangles(neutrals_triangles.F_atm.value,nCi,ft35);
    neutrals_triangles.F_mol.value = fort46_to_triangles(neutrals_triangles.F_mol.value,nCi,ft35);
    neutrals_triangles.F_ion.value = fort46_to_triangles(neutrals_triangles.F_ion.value,nCi,ft35);

end

frewind(fid);

fclose(fid);

fprintf('Eirene neutrals state variables from fort.46 read\n');

end
