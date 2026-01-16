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
fid = simulation.run(index).fid;
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

neutrals_triangles.n_atm.value = scan_ft_real_grid(fid,ver,'pdena',[ntri,natm])*1e6;
neutrals_triangles.n_atm.description = 'Atom particle density';
neutrals_triangles.n_atm.unit = 'm^-3';
neutrals_triangles.n_atm.dimensions = {'ntri','natm'};

neutrals_triangles.n_mol.value = scan_ft_real_grid(fid,ver,'pdenm',[ntri,nmol])*1e6;
neutrals_triangles.n_mol.description = 'Molecular particle density';
neutrals_triangles.n_mol.unit = 'm^-3';
neutrals_triangles.n_mol.dimensions = {'ntri','nmol'};

neutrals_triangles.n_ion.value = scan_ft_real_grid(fid,ver,'pdeni',[ntri,nion])*1e6;
neutrals_triangles.n_ion.description = 'Test ion particle density';
neutrals_triangles.n_ion.unit = 'm^-3';
neutrals_triangles.n_ion.dimensions = {'ntri','nion'};

neutrals_triangles.e_atm.value = scan_ft_real_grid(fid,ver,'edena',[ntri,natm])*1e6;
neutrals_triangles.e_atm.description = 'Atom energy density';
neutrals_triangles.e_atm.unit = 'eV m^-3';
neutrals_triangles.e_atm.dimensions = {'ntri','natm'};

neutrals_triangles.e_mol.value = scan_ft_real_grid(fid,ver,'edenm',[ntri,nmol])*1e6;
neutrals_triangles.e_mol.description = 'Molecular energy density';
neutrals_triangles.e_mol.unit = 'eV m^-3';
neutrals_triangles.e_mol.dimensions = {'ntri','nmol'};

neutrals_triangles.e_ion.value = scan_ft_real_grid(fid,ver,'edeni',[ntri,nion])*1e6;
neutrals_triangles.e_ion.description = 'Test ion energy density';
neutrals_triangles.e_ion.unit = 'eV m^-3';
neutrals_triangles.e_ion.dimensions = {'ntri','nion'};

for i = 1:natm
    neutrals_triangles.T_atm.value(:,i) = ((2/3).*neutrals_triangles.e_atm.value(:,i))./(neutrals_triangles.n_atm.value(:,i));
    neutrals_triangles.p_atm.value(:,i) = ((2/3).*neutrals_triangles.e_atm.value(:,i).*eV);
end
neutrals_triangles.T_atm.description = 'Atom temperature';
neutrals_triangles.T_atm.unit = 'eV';
neutrals_triangles.T_atm.dimensions = {'ntri','natm'};

neutrals_triangles.p_atm.description = 'Atom pressure';
neutrals_triangles.p_atm.unit = 'Pa';
neutrals_triangles.p_atm.dimensions = {'ntri','natm'};

for i = 1:nmol
    neutrals_triangles.T_mol.value(:,i) = ((2/3).*neutrals_triangles.e_mol.value(:,i))./(neutrals_triangles.n_mol.value(:,i));
    neutrals_triangles.p_mol.value(:,i) = ((2/3).*neutrals_triangles.e_mol.value(:,i).*eV);
end
neutrals_triangles.T_mol.description = 'Molecular temperature';
neutrals_triangles.T_mol.unit = 'eV';
neutrals_triangles.T_mol.dimensions = {'ntri','nmol'};

neutrals_triangles.p_mol.description = 'Molecular pressure';
neutrals_triangles.p_mol.unit = 'Pa';
neutrals_triangles.p_mol.dimensions = {'ntri','nmol'};

for i = 1:nion
    neutrals_triangles.T_ion.value(:,i) = ((2/3).*neutrals_triangles.e_ion.value(:,i))./(neutrals_triangles.n_ion.value(:,i));
    neutrals_triangles.p_ion.value(:,i) = ((2/3).*neutrals_triangles.e_ion.value(:,i).*eV);
end
neutrals_triangles.T_ion.description = 'Test ion temperature';
neutrals_triangles.T_ion.unit = 'eV';
neutrals_triangles.T_ion.dimensions = {'ntri','nion'};

neutrals_triangles.p_ion.description = 'Test ion pressure';
neutrals_triangles.p_ion.unit = 'Pa';
neutrals_triangles.p_ion.dimensions = {'ntri','nion'};

neutrals_triangles.m_atm_x.value = scan_ft_real_grid(fid,ver,'vxdena',[ntri,natm])*1e1;
neutrals_triangles.m_atm_x.description = 'Atom x-directed momentum density';
neutrals_triangles.m_atm_x.unit = 'kg s^-1 m^-2';
neutrals_triangles.m_atm_x.dimensions = {'ntri','natm'};

neutrals_triangles.m_mol_x.value = scan_ft_real_grid(fid,ver,'vxdenm',[ntri,nmol])*1e1;
neutrals_triangles.m_mol_x.description = 'Molecular x-directed momentum density';
neutrals_triangles.m_mol_x.unit = 'kg s^-1 m^-2';
neutrals_triangles.m_mol_x.dimensions = {'ntri','nmol'};

neutrals_triangles.m_ion_x.value = scan_ft_real_grid(fid,ver,'vxdeni',[ntri,nion])*1e1;
neutrals_triangles.m_ion_x.description = 'Test ion x-directed momentum density';
neutrals_triangles.m_ion_x.unit = 'kg s^-1 m^-2';
neutrals_triangles.m_ion_x.dimensions = {'ntri','nion'};

neutrals_triangles.m_atm_y.value = scan_ft_real_grid(fid,ver,'vydena',[ntri,natm])*1e1;
neutrals_triangles.m_atm_y.description = 'Atom y-directed momentum density';
neutrals_triangles.m_atm_y.unit = 'kg s^-1 m^-2';
neutrals_triangles.m_atm_y.dimensions = {'ntri','natm'};

neutrals_triangles.m_mol_y.value = scan_ft_real_grid(fid,ver,'vydenm',[ntri,nmol])*1e1;
neutrals_triangles.m_mol_y.description = 'Molecular y-directed momentum density';
neutrals_triangles.m_mol_y.unit = 'kg s^-1 m^-2';
neutrals_triangles.m_mol_y.dimensions = {'ntri','nmol'};

neutrals_triangles.m_ion_y.value = scan_ft_real_grid(fid,ver,'vydeni',[ntri,nion])*1e1;
neutrals_triangles.m_ion_y.description = 'Test ion y-directed momentum density';
neutrals_triangles.m_ion_y.unit = 'kg s^-1 m^-2';
neutrals_triangles.m_ion_y.dimensions = {'ntri','nion'};

neutrals_triangles.m_atm_z.value = scan_ft_real_grid(fid,ver,'vzdena',[ntri,natm])*1e1;
neutrals_triangles.m_atm_z.description = 'Atom z-directed momentum density';
neutrals_triangles.m_atm_z.unit = 'kg s^-1 m^-2';
neutrals_triangles.m_atm_z.dimensions = {'ntri','natm'};

neutrals_triangles.m_mol_z.value = scan_ft_real_grid(fid,ver,'vzdenm',[ntri,nmol])*1e1;
neutrals_triangles.m_mol_z.description = 'Molecular z-directed momentum density';
neutrals_triangles.m_mol_z.unit = 'kg s^-1 m^-2';
neutrals_triangles.m_mol_z.dimensions = {'ntri','nmol'};

neutrals_triangles.m_ion_z.value = scan_ft_real_grid(fid,ver,'vzdeni',[ntri,nion])*1e1;
neutrals_triangles.m_ion_z.description = 'Test ion z-directed momentum density';
neutrals_triangles.m_ion_z.unit = 'kg s^-1 m^-2';
neutrals_triangles.m_ion_z.dimensions = {'ntri','nion'};

for i = 1:natm
    neutrals_triangles.f_atm_x.value(:,i) = (neutrals_triangles.m_atm_x.value(:,i)./(neutrals_triangles.mass_atm{i}*pm));
    neutrals_triangles.f_atm_y.value(:,i) = (neutrals_triangles.m_atm_y.value(:,i)./(neutrals_triangles.mass_atm{i}*pm));
    neutrals_triangles.f_atm_z.value(:,i) = (neutrals_triangles.m_atm_z.value(:,i)./(neutrals_triangles.mass_atm{i}*pm));
    neutrals_triangles.f_atm.value(:,i) = ...
        ((neutrals_triangles.f_atm_x.value(:,i)).^2+(neutrals_triangles.f_atm_y.value(:,i)).^2+(neutrals_triangles.f_atm_z.value(:,i)).^2).^(1/2);
    neutrals_triangles.v_atm.value(:,i) = ...
        ((neutrals_triangles.f_atm.value(:,i).*1)./neutrals_triangles.n_atm.value(:,i));
end
neutrals_triangles.f_atm_x.description = 'Atom x-directed flux density';
neutrals_triangles.f_atm_x.unit = 'm^-2 s^-1';
neutrals_triangles.f_atm_x.dimensions = {'ntri','natm'};

neutrals_triangles.f_atm_y.description = 'Atom y-directed flux density';
neutrals_triangles.f_atm_y.unit = 'm^-2 s^-1';
neutrals_triangles.f_atm_y.dimensions = {'ntri','natm'};

neutrals_triangles.f_atm_z.description = 'Atom z-directed flux density';
neutrals_triangles.f_atm_z.unit = 'm^-2 s^-1';
neutrals_triangles.f_atm_z.dimensions = {'ntri','natm'};

neutrals_triangles.f_atm.description = 'Atom particle flux density';
neutrals_triangles.f_atm.unit = 'm^-2 s^-1';
neutrals_triangles.f_atm.dimensions = {'ntri','natm'};

neutrals_triangles.v_atm.description = 'Atom particle flow velocity';
neutrals_triangles.v_atm.unit = 'm s^-1';
neutrals_triangles.v_atm.dimensions = {'ntri','natm'};

for i = 1:nmol
    neutrals_triangles.f_mol_x.value(:,i) = (neutrals_triangles.m_mol_x.value(:,i)./(neutrals_triangles.mass_mol{i}*pm));
    neutrals_triangles.f_mol_y.value(:,i) = (neutrals_triangles.m_mol_y.value(:,i)./(neutrals_triangles.mass_mol{i}*pm));
    neutrals_triangles.f_mol_z.value(:,i) = (neutrals_triangles.m_mol_z.value(:,i)./(neutrals_triangles.mass_mol{i}*pm));
    neutrals_triangles.f_mol.value(:,i) = ...
        ((neutrals_triangles.f_mol_x.value(:,i)).^2+(neutrals_triangles.f_mol_y.value(:,i)).^2+(neutrals_triangles.f_mol_z.value(:,i)).^2).^(1/2);
    neutrals_triangles.v_mol.value(:,i) = ...
        ((neutrals_triangles.f_mol.value(:,i).*1)./neutrals_triangles.n_mol.value(:,i));
end
neutrals_triangles.f_mol_x.description = 'Molecular x-directed flux density';
neutrals_triangles.f_mol_x.unit = 'm^-2 s^-1';
neutrals_triangles.f_mol_x.dimensions = {'ntri','nmol'};

neutrals_triangles.f_mol_y.description = 'Molecular y-directed flux density';
neutrals_triangles.f_mol_y.unit = 'm^-2 s^-1';
neutrals_triangles.f_mol_y.dimensions = {'ntri','nmol'};

neutrals_triangles.f_mol_z.description = 'Molecular z-directed flux density';
neutrals_triangles.f_mol_z.unit = 'm^-2 s^-1';
neutrals_triangles.f_mol_z.dimensions = {'ntri','nmol'};

neutrals_triangles.f_mol.description = 'Molecular particle flux density';
neutrals_triangles.f_mol.unit = 'm^-2 s^-1';
neutrals_triangles.f_mol.dimensions = {'ntri','nmol'};

neutrals_triangles.v_mol.description = 'Molecular particle flow velocity';
neutrals_triangles.v_mol.unit = 'm s^-1';
neutrals_triangles.v_mol.dimensions = {'ntri','nmol'};

for i = 1:nion
    neutrals_triangles.f_ion_x.value(:,i) = (neutrals_triangles.m_ion_x.value(:,i)./(neutrals_triangles.mass_ion{i}*pm));
    neutrals_triangles.f_ion_y.value(:,i) = (neutrals_triangles.m_ion_y.value(:,i)./(neutrals_triangles.mass_ion{i}*pm));
    neutrals_triangles.f_ion_z.value(:,i) = (neutrals_triangles.m_ion_z.value(:,i)./(neutrals_triangles.mass_ion{i}*pm));
    neutrals_triangles.f_ion.value(:,i) = ...
        ((neutrals_triangles.f_ion_x.value(:,i)).^2+(neutrals_triangles.f_ion_y.value(:,i)).^2+(neutrals_triangles.f_ion_z.value(:,i)).^2).^(1/2);
    neutrals_triangles.v_ion.value(:,i) = ...
        ((neutrals_triangles.f_ion.value(:,i).*1)./neutrals_triangles.n_ion.value(:,i));
end
neutrals_triangles.f_ion_x.description = 'Test ion x-directed flux density';
neutrals_triangles.f_ion_x.unit = 'm^-2 s^-1';
neutrals_triangles.f_ion_x.dimensions = {'ntri','nion'};

neutrals_triangles.f_ion_y.description = 'Test ion y-directed flux density';
neutrals_triangles.f_ion_y.unit = 'm^-2 s^-1';
neutrals_triangles.f_ion_y.dimensions = {'ntri','nion'};

neutrals_triangles.f_ion_z.description = 'Test ion z-directed flux density';
neutrals_triangles.f_ion_z.unit = 'm^-2 s^-1';
neutrals_triangles.f_ion_z.dimensions = {'ntri','nion'};

neutrals_triangles.f_ion.description = 'Test ion particle flux density';
neutrals_triangles.f_ion.unit = 'm^-2 s^-1';
neutrals_triangles.f_ion.dimensions = {'ntri','nion'};

neutrals_triangles.v_ion.description = 'Test ion particle flow velocity';
neutrals_triangles.v_ion.unit = 'm s^-1';
neutrals_triangles.v_ion.dimensions = {'ntri','nion'};

for i = 1:natm
    neutrals_triangles.V_atm.value(:,i) = sqrt((8*kB.*(neutrals_triangles.T_atm.value(:,i)./8.617e-5))./(pi*neutrals_triangles.mass_atm{i}*pm));
    neutrals_triangles.F_atm.value(:,i) = (neutrals_triangles.n_atm.value(:,i).*neutrals_triangles.V_atm.value(:,i))./4;
end
neutrals_triangles.V_atm.description = 'Mean atom particle velocity';
neutrals_triangles.V_atm.unit = 'm s^-1';
neutrals_triangles.V_atm.dimensions = {'ntri','natm'};

neutrals_triangles.F_atm.description = 'Mean atom particle flux density';
neutrals_triangles.F_atm.unit = 'm^-2 s^-1';
neutrals_triangles.F_atm.dimensions = {'ntri','natm'};

for i = 1:nmol
    neutrals_triangles.V_mol.value(:,i) = sqrt((8*kB.*(neutrals_triangles.T_mol.value(:,i)./8.617e-5))./(pi*neutrals_triangles.mass_mol{i}*pm));
    neutrals_triangles.F_mol.value(:,i) = (neutrals_triangles.n_mol.value(:,i).*neutrals_triangles.V_mol.value(:,i))./4;
end
neutrals_triangles.V_mol.description = 'Mean molecular particle velocity';
neutrals_triangles.V_mol.unit = 'm s^-1';
neutrals_triangles.V_mol.dimensions = {'ntri','nmol'};

neutrals_triangles.F_mol.description = 'Mean molecular particle flux density';
neutrals_triangles.F_mol.unit = 'm^-2 s^-1';
neutrals_triangles.F_mol.dimensions = {'ntri','nmol'};

for i = 1:nion
    neutrals_triangles.V_ion.value(:,i) = sqrt((8*kB.*(neutrals_triangles.T_ion.value(:,i)./8.617e-5))./(pi*neutrals_triangles.mass_ion{i}*pm));
    neutrals_triangles.F_ion.value(:,i) = (neutrals_triangles.n_ion.value(:,i).*neutrals_triangles.V_ion.value(:,i))./4;
end
neutrals_triangles.V_ion.description = 'Mean test ion particle velocity';
neutrals_triangles.V_ion.unit = 'm s^-1';
neutrals_triangles.V_ion.dimensions = {'ntri','nion'};

neutrals_triangles.F_ion.description = 'Mean test ion particle flux density';
neutrals_triangles.F_ion.unit = 'm^-2 s^-1';
neutrals_triangles.F_ion.dimensions = {'ntri','nion'};

if strcmp(version,'structured')

    neutrals_triangles.vol.value = scan_ft_real_grid(fid,ver,'vol',[ntri])/1e6;
    neutrals_triangles.vol.description = 'volume of the cell';
    neutrals_triangles.vol.unit = 'm^3';
    neutrals_triangles.vol.dimensions = {'ntri'};

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

fprintf('Structure NEUTRALS_TRIANGLES from fort.46 read.\n');

end
