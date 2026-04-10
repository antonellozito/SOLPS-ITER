function output = read_fort44(varargin)
%
% read_ft44 reads the fort.44 file created by EIRENE
% Output is the structs "neutrals_grid" and "wall" with all the data fields in the fort.44 file
%
% 1st input: main simulation structure
%
% Following inputs: strings which specify which subsets of fields
%                   should be read:
%                   - 'NEUTRALS_GRID'
%                   - 'WALL'

%% PRELIMINARY OPERATIONS

% Load the file

simulation = varargin{1};

index = find(contains({simulation.run.name},'fort.44'));
if isempty(index)
   error('Error: fort.44 not found');
end
file = simulation.run(index).file;
fid = fopen(file);
if (fid == -1)
   error('Error: fort.44 not found');
end

nlwrmsh = 1;
nfla = 1;

line = fgetl(fid);
countEntries = @(str) sum(~cellfun(@isempty, strsplit(str)));
n = countEntries(line);
if n==4
    version = 'structured';
elseif n==3
    version = 'unstructured';
end

frewind(fid);

% Select which group of fields to read

READ_NEUTRALS_GRID = false;
READ_WALL = false;

if numel(varargin) == 1
    READ_NEUTRALS_GRID = true;
    READ_WALL = true;
else
    if any(strcmp(varargin,'NEUTRALS_GRID'))
        READ_NEUTRALS_GRID = true;
    end
    if any(strcmp(varargin,'WALL'))
        READ_WALL = true;  
    end
end

%% READ THE DATA ON THE COMPUTATIONAL GRID

if READ_NEUTRALS_GRID

% Read the dimensions

if strcmp(version,'structured')

    dims = fscanf(fid,'%d',3);
    nx   = dims(1);
    ny   = dims(2);
    ver  = dims(3);

    ft44dims = [nx,ny];

    output.nx = nx;
    output.ny = ny;

elseif strcmp(version,'unstructured')

    dims = fscanf(fid,'%d',3);
    nCv   = dims(1);
    ver  = dims(2);

    ft44dims = [nCv,1];

    output.nCv = nCv;

end

line = fgetl(fid);

while ~contains(line,'wldnek(0)')
    prevline = line;
    line = fgetl(fid);
end

dims  = sscanf(prevline,'%d',3);
nlim  = dims(1);
nsts  = dims(2);
nstra = dims(3);
output.nstra = nstra;

frewind(fid);

% Read the names of the strata

if strcmp(version,'structured')

    temp = find(contains({simulation.run.name},'b2.neutrals.parameters'));
    file_neut_par = simulation.run(temp).file;
    fid_neut_par = fopen(file_neut_par);
    line = fgetl(fid_neut_par);
    while ~contains(line,'crcstra')
        line = fgetl(fid_neut_par);
    end
    temp = extractAfter(line,'crcstra=');
    temp = textscan(temp,'%s ',nstra);
    for istra = 1:nstra
        stratum_type{istra} = temp{1}{istra}(2);
    end
    
    while ~contains(line,'species_start')
        line = fgetl(fid_neut_par);
    end
    temp = extractAfter(line,'species_start=');
    temp = textscan(temp,'%d, ',istra);
    for istra = 1:nstra
        stratum_species_start{istra} = temp{1}(istra);
    end
    
    while ~contains(line,'species_end')
        line = fgetl(fid_neut_par);
    end
    temp = extractAfter(line,'species_end=');
    temp = textscan(temp,'%d, ',istra);
    for istra = 1:nstra
        stratum_species_end{istra} = temp{1}(istra);
    end
    
    for istra = 1:nstra
        switch stratum_type{istra}
            case 'W'
                stratum_name{istra} = 'Recycling, inner target';
            case 'E'
                stratum_name{istra} = 'Recycling, outer target';
            case 'N'
                stratum_name{istra} = 'Recycling, wall';
            case 'S'
                stratum_name{istra} = 'Recycling, PFR';
            case 'C'
                stratum_name{istra} = 'Gas puff source';
            case 'V'
                stratum_name{istra} = 'Recombination';
            case 'T'
                stratum_name{istra} = 'Time-dependent source';
        end
    end
    for istra = 1:nstra
        if stratum_species_end{istra}-stratum_species_start{istra}==1
            stratum_name{istra} = append(stratum_name{istra},' (D)');
        elseif  stratum_species_end{istra}-stratum_species_start{istra}==7
            stratum_name{istra} = append(stratum_name{istra},' (N)');
        elseif  stratum_species_end{istra}-stratum_species_start{istra}==2
            stratum_name{istra} = append(stratum_name{istra},' (He)');
        end
    end
    
    frewind(fid_neut_par);

    fclose(fid_neut_par);

elseif strcmp(version,'unstructured')

    % TODO

end

% Read the number of species

fgetl(fid);

dims = fscanf(fid,'%d',3);
natm = dims(1);
nmol = dims(2);
nion = dims(3);
output.natm = natm;
output.nmol = nmol;
output.nion = nion;

% Write the names of strata and species

if strcmp(version,'structured')

output.strata = stratum_name;

elseif strcmp(version,'unstructured')

% output.strata = stratum_name;

end

line = fgetl(fid);
for i = 1:natm
    line = fgetl(fid);
    output.species_atm{i} = strtrim(line);
end
for i = 1:nmol
    line = fgetl(fid);
    output.species_mol{i} = strtrim(line);
end
for i = 1:nion
    line = fgetl(fid);
    output.species_ion{i} = strtrim(line);
end

% Determine dimension labels
if strcmp(version,'structured')
    dim_labels = {'nx','ny'};
    dim_labels_species_atm = {'nx','ny','natm'};
    dim_labels_species_mol = {'nx','ny','nmol'};
    dim_labels_species_ion = {'nx','ny','nion'};
elseif strcmp(version,'unstructured')
    dim_labels = {'nCv'};
    dim_labels_species_atm = {'nCv','natm'};
    dim_labels_species_mol = {'nCv','nmol'};
    dim_labels_species_ion = {'nCv','nion'};
end

% State variables

output = set_ft_real_grid_field(output, fid, ver, 'n_atm', 'dab2', [ft44dims, natm], ...
    'atomic density', 'm^-3', dim_labels_species_atm);
output = set_ft_real_grid_field(output, fid, ver, 'T_atm', 'tab2', [ft44dims, natm], ...
    'atomic temperature', 'eV', dim_labels_species_atm);
output = set_ft_real_grid_field(output, fid, ver, 'n_mol', 'dmb2', [ft44dims, nmol], ...
    'molecular density', 'm^-3', dim_labels_species_mol);
output = set_ft_real_grid_field(output, fid, ver, 'T_mol', 'tmb2', [ft44dims, nmol], ...
    'molecular temperature', 'eV', dim_labels_species_mol);
output = set_ft_real_grid_field(output, fid, ver, 'n_ion', 'dib2', [ft44dims, nion], ...
    'test ions density', 'm^-3', dim_labels_species_ion);
output = set_ft_real_grid_field(output, fid, ver, 'T_ion', 'tib2', [ft44dims, nion], ...
    'test ions temperature', 'eV', dim_labels_species_ion);

% Fluxes

output = set_ft_real_grid_field(output, fid, ver, 'fn_atm_y', 'rfluxa', [ft44dims, natm], ...
    'atomic radial flux density', 'm^-2 s^-1', dim_labels_species_atm);
output = set_ft_real_grid_field(output, fid, ver, 'fn_mol_y', 'rfluxm', [ft44dims, nmol], ...
    'molecular radial flux density', 'm^-2 s^-1', dim_labels_species_mol);
output = set_ft_real_grid_field(output, fid, ver, 'fn_atm_x', 'pfluxa', [ft44dims, natm], ...
    'atomic poloidal flux density', 'm^-2 s^-1', dim_labels_species_atm);
output = set_ft_real_grid_field(output, fid, ver, 'fn_mol_x', 'pfluxm', [ft44dims, nmol], ...
    'molecular poloidal flux density', 'm^-2 s^-1', dim_labels_species_mol);
output = set_ft_real_grid_field(output, fid, ver, 'fe_atm_y', 'refluxa', [ft44dims, natm], ...
    'atomic radial energy flux density', 'W m^-2', dim_labels_species_atm);
output = set_ft_real_grid_field(output, fid, ver, 'fe_mol_y', 'refluxm', [ft44dims, nmol], ...
    'molecular radial energy flux density', 'W m^-2', dim_labels_species_mol);
output = set_ft_real_grid_field(output, fid, ver, 'fe_atm_x', 'pefluxa', [ft44dims, natm], ...
    'atomic poloidal energy flux density', 'W m^-2', dim_labels_species_atm);
output = set_ft_real_grid_field(output, fid, ver, 'fe_mol_x', 'pefluxm', [ft44dims, nmol], ...
    'molecular poloidal energy flux density', 'W m^-2', dim_labels_species_mol);

% Radiation, emissivity and dissociation

if strcmp(version,'structured')
    dim_labels_single = {'nx','ny','1'};
else
    dim_labels_single = {'nCv','1'};
end

output = set_ft_real_grid_field(output, fid, ver, 'Ha_atm', 'emiss', [ft44dims, 1], ...
    'atomic H_alpha emissivity', 'photons m^-3 s^-1', dim_labels_single);
output = set_ft_real_grid_field(output, fid, ver, 'Ha_mol', 'emissmol', [ft44dims, 1], ...
    'molecular H_alpha emissivity', 'photons m^-3 s^-1', dim_labels_single);
output = set_ft_real_grid_field(output, fid, ver, 'mol_source', 'srcml', [ft44dims, nmol], ...
    'molecule particle source', 'A', dim_labels_species_mol);
output = set_ft_real_grid_field(output, fid, ver, 'en_mol_diss', 'edissml', [ft44dims, nmol], ...
    'energy for hydrogenic molecular dissociation', 'W', dim_labels_species_mol);
output = set_ft_real_grid_field(output, fid, ver, 'rad_atm', 'eneutrad', [ft44dims, natm], ...
    'radiation rate due to atoms', 'W', dim_labels_species_atm);
output = set_ft_real_grid_field(output, fid, ver, 'rad_mol', 'emolrad', [ft44dims, nmol], ...
    'radiation rate due to molecules', 'W', dim_labels_species_mol);
output = set_ft_real_grid_field(output, fid, ver, 'rad_ion', 'eionrad', [ft44dims, nion], ...
    'radiation rate due to test ions', 'W', dim_labels_species_ion);

% Integral quantities

try

output = set_ft_real_grid_field(output, fid, ver, 'tot_atm_eirene', 'pdena_int', [natm, nstra+1], ...
    'Total number of atoms over the EIRENE grid', '-', {'natm','nstra+1'});
output = set_ft_real_grid_field(output, fid, ver, 'tot_mol_eirene', 'pdenm_int', [nmol, nstra+1], ...
    'Total number of molecules over the EIRENE grid', '-', {'nmol','nstra+1'});
output = set_ft_real_grid_field(output, fid, ver, 'tot_ion_eirene', 'pdeni_int', [nion, nstra+1], ...
    'Total number of test ions over the EIRENE grid', '-', {'nion','nstra+1'});
output = set_ft_real_grid_field(output, fid, ver, 'tot_atm_b2', 'pdena_int_b2', [natm, nstra+1], ...
    'Total number of atoms over the B2.5 grid', '-', {'natm','nstra+1'});
output = set_ft_real_grid_field(output, fid, ver, 'tot_mol_b2', 'pdenm_int_b2', [nmol, nstra+1], ...
    'Total number of molecules over the B2.5 grid', '-', {'nmol','nstra+1'});
output = set_ft_real_grid_field(output, fid, ver, 'tot_ion_b2', 'pdeni_int_b2', [nion, nstra+1], ...
    'Total number of test ions over the B2.5 grid', '-', {'nion','nstra+1'});
output = set_ft_real_grid_field(output, fid, ver, 'tot_en_atm_eirene', 'edena_int', [natm, nstra+1], ...
    'Total energy carried by atoms over the EIRENE grid', 'J', {'natm','nstra+1'});
output = set_ft_real_grid_field(output, fid, ver, 'tot_en_mol_eirene', 'edenm_int', [nmol, nstra+1], ...
    'Total energy carried by molecules over the EIRENE grid', 'J', {'nmol','nstra+1'});
output = set_ft_real_grid_field(output, fid, ver, 'tot_en_ion_eirene', 'edeni_int', [nion, nstra+1], ...
    'Total energy carried by test ions over the EIRENE grid', 'J', {'nion','nstra+1'});
output = set_ft_real_grid_field(output, fid, ver, 'tot_en_atm_b2', 'edena_int_b2', [natm, nstra+1], ...
    'Total energy carried by atoms over the B2.5 grid', 'J', {'natm','nstra+1'});
output = set_ft_real_grid_field(output, fid, ver, 'tot_en_mol_b2', 'edenm_int_b2', [nmol, nstra+1], ...
    'Total energy carried by molecules over the B2.5 grid', 'J', {'nmol','nstra+1'});
output = set_ft_real_grid_field(output, fid, ver, 'tot_en_ion_b2', 'edeni_int_b2', [nion, nstra+1], ...
    'Total energy carried by test ions over the B2.5 grid', 'J', {'nion','nstra+1'});

catch

end

frewind(fid);

fprintf('Eirene neutrals state variables from fort.44 read\n');

end

%% READ WALL DATA

if READ_WALL

if strcmp(version,'structured')

% Read the dimensions

line = fgetl(fid);
while ~contains(line,'wldnek(0)')
    prevline = line;
    line = fgetl(fid);
end

dims  = sscanf(prevline,'%d',3);
nlim  = dims(1);
nsts  = dims(2);
nstra = dims(3);
output.nlim = nlim;
output.nsts = nsts;
output.nstra = nstra;

% Read the number of species

output.natm = output.natm;
output.nmol = output.nmol;
output.nion = output.nion;

line = fgetl(fid);
while ~contains(line,'wlabsrp(P)')
    line = fgetl(fid);
end
temp = sscanf(line,'*eirene data field wlabsrp(P) with size %d');
npls = temp/(nlim+nsts);
output.npls = npls;

% Write the names of strata and species

output.strata = stratum_name;

for i = 1:natm
    output.species_atm{i} = output.species_atm{i};
end
for i = 1:nmol
    output.species_mol{i} = output.species_mol{i};
end
for i = 1:nion
    output.species_ion{i} = output.species_ion{i};
end

lines_plasma = ceil(npls/6);
k = 1;
for i = 1:lines_plasma
    line = fgetl(fid);
    % Split by whitespace and remove empty entries
    temp = strsplit(strtrim(line));
    temp = temp(~cellfun('isempty', temp));
    
    for j = 1:length(temp)
        if k <= npls
            output.species_plasma{k} = temp{j};
            k = k+1;
        end
    end
end

frewind(fid);

% Characteristics of surfaces

output.surface_type.value = scan_ft_int_wall(fid,ver,'isrftype',[nlim+nsts]);
output = set_output_field(output, 'surface_type', output.surface_type.value, ...
    'ILIIN surface type variable', '-', {'nlim+nsts'});

output.area.value = scan_ft_real_wall(fid,ver,'wlarea',[nlim+nsts]);
output = set_output_field(output, 'area', output.area.value, ...
    'surface area', 'm^2', {'nlim+nsts'});

frewind(fid);

% Wall loading, reflection

output.kin_power.value(:,1) = scan_ft_real_wall(fid,ver,'wldnek(0)',[nlim+nsts]);

output.pot_power.value(:,1) = scan_ft_real_wall(fid,ver,'wldnep(0)',[nlim+nsts]);

fn_atm_temp(:,1) = scan_ft_real_wall(fid,ver,'wldna(0)',[nlim+nsts,natm]);
en_atm_temp(:,1) = scan_ft_real_wall(fid,ver,'ewlda(0)',[nlim+nsts,natm]);
fn_mol_temp(:,1) = scan_ft_real_wall(fid,ver,'wldnm(0)',[nlim+nsts,nmol]);
en_mol_temp(:,1) = scan_ft_real_wall(fid,ver,'ewldm(0)',[nlim+nsts,nmol]);
fn_atm_ref_temp(:,1)  = scan_ft_real_wall(fid,ver,'wldra(0)',[nlim+nsts,natm]);
fn_mol_ref_temp(:,1)  = scan_ft_real_wall(fid,ver,'wldrm(0)',[nlim+nsts,nmol]);

if (nstra > 1)
   for i = 1:nstra
       temp = sprintf('    %d',i); temp = temp(end-2:end);
       output.kin_power.value(:,i+1) = scan_ft_real_wall(fid,ver,sprintf('%s%s%s','wldnek(',temp,')'),[nlim+nsts]);
       output.pot_power.value(:,i+1) = scan_ft_real_wall(fid,ver,sprintf('%s%s%s','wldnep(',temp,')'),[nlim+nsts]);
       fn_atm_temp(:,i+1) = scan_ft_real_wall(fid,ver,sprintf('%s%s%s','wldna(',temp,')'),[nlim+nsts,natm]);
       en_atm_temp(:,i+1) = scan_ft_real_wall(fid,ver,sprintf('%s%s%s','ewlda(',temp,')'),[nlim+nsts,natm]);
       fn_mol_temp(:,i+1) = scan_ft_real_wall(fid,ver,sprintf('%s%s%s','wldnm(',temp,')'),[nlim+nsts,nmol]);
       en_mol_temp(:,i+1) = scan_ft_real_wall(fid,ver,sprintf('%s%s%s','ewldm(',temp,')'),[nlim+nsts,nmol]);
       fn_atm_ref_temp(:,i+1) = scan_ft_real_wall(fid,ver,sprintf('%s%s%s','wldra(',temp,')'),[nlim+nsts,natm]);
       fn_mol_ref_temp(:,i+1) = scan_ft_real_wall(fid,ver,sprintf('%s%s%s','wldrm(',temp,')'),[nlim+nsts,nmol]);
   end
end

for i = 1:natm
    output.fn_atm.value(:,:,i) = fn_atm_temp(1+(nlim+nsts)*(i-1):(nlim+nsts)*i,:);
    output.en_atm.value(:,:,i) = en_atm_temp(1+(nlim+nsts)*(i-1):(nlim+nsts)*i,:);
    output.fn_atm_ref.value(:,:,i) = fn_atm_ref_temp(1+(nlim+nsts)*(i-1):(nlim+nsts)*i,:);
end
output = set_output_field(output, 'kin_power', output.kin_power.value, ...
    'kinetic energy transfered by neutrals to the surface', 'W', {'nlim+nsts','nstra+1'});
output = set_output_field(output, 'pot_power', output.pot_power.value, ...
    'potential energy released by neutrals on the surface', 'W', {'nlim+nsts','nstra+1'});
output = set_output_field(output, 'fn_atm', output.fn_atm.value, ...
    'flux of atoms impinging on the surface', 'A', {'nlim+nsts','nstra+1','natm'});
output = set_output_field(output, 'en_atm', output.en_atm.value, ...
    'average energy of atoms impinging on the surface', 'eV', {'nlim+nsts','nstra+1','natm'});
output = set_output_field(output, 'fn_atm_ref', output.fn_atm_ref.value, ...
    'flux of atoms reflected from the surface', 'A', {'nlim+nsts','nstra+1','natm'});

for i = 1:nmol
    output.fn_mol.value(:,:,i) = fn_mol_temp(1+(nlim+nsts)*(i-1):(nlim+nsts)*i,:);
    output.en_mol.value(:,:,i) = en_mol_temp(1+(nlim+nsts)*(i-1):(nlim+nsts)*i,:);
    output.fn_mol_ref.value(:,:,i) = fn_mol_ref_temp(1+(nlim+nsts)*(i-1):(nlim+nsts)*i,:);
end
output = set_output_field(output, 'fn_mol', output.fn_mol.value, ...
    'flux of molecules impinging on the surface', 'A', {'nlim+nsts','nstra+1','nmol'});
output = set_output_field(output, 'en_mol', output.en_mol.value, ...
    'average energy of molecules impinging on the surface', 'eV', {'nlim+nsts','nstra+1','nmol'});
output = set_output_field(output, 'fn_mol_ref', output.fn_mol_ref.value, ...
    'flux of molecules reflected from the surface', 'A', {'nlim+nsts','nstra+1','nmol'});

% Emission and sputtering

fn_pls_temp(:,1) = scan_ft_real_wall(fid,ver,'wldpp(0)',[nlim+nsts,npls]);
fn_atm_em_temp(:,1) = scan_ft_real_wall(fid,ver,'wldpa(0)',[nlim+nsts,natm]);
fn_mol_em_temp(:,1) = scan_ft_real_wall(fid,ver,'wldpm(0)',[nlim+nsts,nmol]);
power_em_temp(:,1) = scan_ft_real_wall(fid,ver,'wldpeb(0)',[nlim+nsts]);
output.fn_sput.value(:,1) = scan_ft_real_wall(fid,ver,'wldspt(0)',[nlim+nsts]);
fn_sput_atm_temp(:,1) = scan_ft_real_wall(fid,ver,'wldspta(0)',[nlim+nsts,natm]);
fn_sput_mol_temp(:,1) = scan_ft_real_wall(fid,ver,'wldsptm(0)',[nlim+nsts,nmol]);

if (nstra > 1)
   for i = 1:nstra
       temp = sprintf('    %d',i); temp = temp(end-2:end);
       fn_pls_temp(:,i+1) = scan_ft_real_wall(fid,ver,sprintf('%s%s%s','wldpp(',temp,')'),[nlim+nsts,npls]);
       fn_atm_em_temp(:,i+1) = scan_ft_real_wall(fid,ver,sprintf('%s%s%s','wldpa(',temp,')'),[nlim+nsts,natm]);
       fn_mol_em_temp(:,i+1) = scan_ft_real_wall(fid,ver,sprintf('%s%s%s','wldpm(',temp,')'),[nlim+nsts,nmol]);
       power_em_temp(:,i+1) = scan_ft_real_wall(fid,ver,sprintf('%s%s%s','wldpeb(',temp,')'),[nlim+nsts]);
       output.fn_sput.value(:,i+1) = scan_ft_real_wall(fid,ver,sprintf('%s%s%s','wldspt(',temp,')'),[nlim+nsts]);
       fn_sput_atm_temp(:,i+1) = scan_ft_real_wall(fid,ver,sprintf('%s%s%s','wldspta(',temp,')'),[nlim+nsts,natm]);
       fn_sput_mol_temp(:,i+1) = scan_ft_real_wall(fid,ver,sprintf('%s%s%s','wldsptm(',temp,')'),[nlim+nsts,nmol]);
   end
end

for i = 1:npls
    output.fn_pls.value(:,:,i) = fn_pls_temp(1+(nlim+nsts)*(i-1):(nlim+nsts)*i,:);
end
output = set_output_field(output, 'fn_pls', output.fn_pls.value, ...
    'flux of plasma ions impinging on the surface', 'A', {'nlim+nsts','nstra+1','npls'});

for i = 1:natm
    output.fn_atm_em.value(:,:,i) = fn_atm_em_temp(1+(nlim+nsts)*(i-1):(nlim+nsts)*i,:);
    output.fn_sput_atm.value(:,:,i) = fn_sput_atm_temp(1+(nlim+nsts)*(i-1):(nlim+nsts)*i,:);
end
output = set_output_field(output, 'fn_atm_em', output.fn_atm_em.value, ...
    'flux of atoms emitted from the surface', 'A', {'nlim+nsts','nstra+1','natm'});
output = set_output_field(output, 'fn_sput_atm', output.fn_sput_atm.value, ...
    'flux of sputtered wall material per atom', 'A', {'nlim+nsts','nstra+1','natm'});

for i = 1:nmol
    output.fn_mol_em.value(:,:,i) = fn_mol_em_temp(1+(nlim+nsts)*(i-1):(nlim+nsts)*i,:);
    output.fn_sput_mol.value(:,:,i) = fn_sput_mol_temp(1+(nlim+nsts)*(i-1):(nlim+nsts)*i,:);
end
output = set_output_field(output, 'fn_mol_em', output.fn_mol_em.value, ...
    'flux of molecules emitted from the surface', 'A', {'nlim+nsts','nstra+1','nmol'});
output = set_output_field(output, 'fn_sput_mol', output.fn_sput_mol.value, ...
    'flux of sputtered wall material per molecule', 'A', {'nlim+nsts','nstra+1','nmol'});
output = set_output_field(output, 'power_em', power_em_temp, ...
    'power carried by particles emitted from the surface', 'W', {'nlim+nsts','nstra+1'});
output = set_output_field(output, 'fn_sput', output.fn_sput.value, ...
    'flux of sputtered wall material', 'A', {'nlim+nsts','nstra+1'});

% Absorption

abs_rate_atm_temp(:,:) = scan_ft_real_pump(fid,ver,'wlabsrp(A)',[natm,nlim+nsts]);
abs_rate_mol_temp(:,:) = scan_ft_real_pump(fid,ver,'wlabsrp(M)',[nmol,nlim+nsts]);
abs_rate_ion_temp(:,:) = scan_ft_real_pump(fid,ver,'wlabsrp(I)',[nion,nlim+nsts]);
pump_atm_temp(:,:) = scan_ft_real_pump(fid,ver,'wlpump(A)',[natm,nlim+nsts]);
pump_mol_temp(:,:) = scan_ft_real_pump(fid,ver,'wlpump(M)',[nmol,nlim+nsts]);
pump_ion_temp(:,:) = scan_ft_real_pump(fid,ver,'wlpump(I)',[nion,nlim+nsts]);

for i = 1:natm
    output.abs_rate_atm.value(:,i) = abs_rate_atm_temp(i,:);
    output.pump_atm.value(:,i) = pump_atm_temp(i,:);   
end
output = set_output_field(output, 'abs_rate_atm', output.abs_rate_atm.value, ...
    'absoption rate for atoms', '-', {'nlim+nsts','natm'});
output = set_output_field(output, 'pump_atm', output.pump_atm.value, ...
    'pumped flux for atoms', 'A', {'nlim+nsts','natm'});

for i = 1:nmol
    output.abs_rate_mol.value(:,i) = abs_rate_mol_temp(i,:);
    output.pump_mol.value(:,i) = pump_mol_temp(i,:);  
end
output = set_output_field(output, 'abs_rate_mol', output.abs_rate_mol.value, ...
    'absoption rate for molecules', '-', {'nlim+nsts','nmol'});
output = set_output_field(output, 'pump_mol', output.pump_mol.value, ...
    'pumped flux for molecules', 'A', {'nlim+nsts','nmol'});

for i = 1:nion
    output.abs_rate_ion.value(:,i) = abs_rate_ion_temp(i,:);
    output.pump_ion.value(:,i) = pump_ion_temp(i,:);  
end
output = set_output_field(output, 'abs_rate_ion', output.abs_rate_ion.value, ...
    'absoption rate for test ions', '-', {'nlim+nsts','nion'});
output = set_output_field(output, 'pump_ion', output.pump_ion.value, ...
    'pumped flux for test ions', 'A', {'nlim+nsts','nion'});

frewind(fid);

fclose(fid);

fprintf('Eirene wall data from fort.44 read\n');

elseif strcmp(version,'unstructured')

    %TODO

end

end

end
