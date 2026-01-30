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

output.n_atm.value = scan_ft_real_grid(fid,ver,'dab2',[ft44dims,natm]);
output.n_atm.description = 'atomic density';
output.n_atm.unit = 'm^-3';
output.n_atm.dimensions = dim_labels_species_atm;

output.T_atm.value = scan_ft_real_grid(fid,ver,'tab2',[ft44dims,natm]);
output.T_atm.description = 'atomic temperature';
output.T_atm.unit = 'eV';
output.T_atm.dimensions = dim_labels_species_atm;

output.n_mol.value = scan_ft_real_grid(fid,ver,'dmb2',[ft44dims,nmol]);
output.n_mol.description = 'molecular density';
output.n_mol.unit = 'm^-3';
output.n_mol.dimensions = dim_labels_species_mol;

output.T_mol.value = scan_ft_real_grid(fid,ver,'tmb2',[ft44dims,nmol]);
output.T_mol.description = 'molecular temperature';
output.T_mol.unit = 'eV';
output.T_mol.dimensions = dim_labels_species_mol;

output.n_ion.value = scan_ft_real_grid(fid,ver,'dib2',[ft44dims,nion]);
output.n_ion.description = 'test ions density';
output.n_ion.unit = 'm^-3';
output.n_ion.dimensions = dim_labels_species_ion;

output.T_ion.value = scan_ft_real_grid(fid,ver,'tib2',[ft44dims,nion]);
output.T_ion.description = 'test ions temperature';
output.T_ion.unit = 'eV';
output.T_ion.dimensions = dim_labels_species_ion;

% Fluxes

output.fn_atm_y.value = scan_ft_real_grid(fid,ver,'rfluxa',[ft44dims,natm]);
output.fn_atm_y.description = 'atomic radial flux density';
output.fn_atm_y.unit = 'm^-2 s^-1';
output.fn_atm_y.dimensions = dim_labels_species_atm;

output.fn_mol_y.value = scan_ft_real_grid(fid,ver,'rfluxm',[ft44dims,nmol]);
output.fn_mol_y.description = 'molecular radial flux density';
output.fn_mol_y.unit = 'm^-2 s^-1';
output.fn_mol_y.dimensions = dim_labels_species_mol;

output.fn_atm_x.value = scan_ft_real_grid(fid,ver,'pfluxa',[ft44dims,natm]);
output.fn_atm_x.description = 'atomic poloidal flux density';
output.fn_atm_x.unit = 'm^-2 s^-1';
output.fn_atm_x.dimensions = dim_labels_species_atm;

output.fn_mol_x.value = scan_ft_real_grid(fid,ver,'pfluxm',[ft44dims,nmol]);
output.fn_mol_x.description = 'molecular poloidal flux density';
output.fn_mol_x.unit = 'm^-2 s^-1';
output.fn_mol_x.dimensions = dim_labels_species_mol;

output.fe_atm_y.value = scan_ft_real_grid(fid,ver,'refluxa',[ft44dims,natm]);
output.fe_atm_y.description = 'atomic radial energy flux density';
output.fe_atm_y.unit = 'W m^-2';
output.fe_atm_y.dimensions = dim_labels_species_atm;

output.fe_mol_y.value = scan_ft_real_grid(fid,ver,'refluxm',[ft44dims,nmol]);
output.fe_mol_y.description = 'molecular radial energy flux density';
output.fe_mol_y.unit = 'W m^-2';
output.fe_mol_y.dimensions = dim_labels_species_mol;

output.fe_atm_x.value = scan_ft_real_grid(fid,ver,'pefluxa',[ft44dims,natm]);
output.fe_atm_x.description = 'atomic poloidal energy flux density';
output.fe_atm_x.unit = 'W m^-2';
output.fe_atm_x.dimensions = dim_labels_species_atm;

output.fe_mol_x.value = scan_ft_real_grid(fid,ver,'pefluxm',[ft44dims,nmol]);
output.fe_mol_x.description = 'molecular poloidal energy flux density';
output.fe_mol_x.unit = 'W m^-2';
output.fe_mol_x.dimensions = dim_labels_species_mol;

% Radiation, emissivity and dissociation

output.Ha_atm.value = scan_ft_real_grid(fid,ver,'emiss',[ft44dims,1]);
output.Ha_atm.description = 'atomic H_alpha emissivity';
output.Ha_atm.unit = 'photons m^-3 s^-1';
if strcmp(version,'structured')
    output.Ha_atm.dimensions = {'nx','ny','1'};
else
    output.Ha_atm.dimensions = {'nCv','1'};
end

output.Ha_mol.value = scan_ft_real_grid(fid,ver,'emissmol',[ft44dims,1]);
output.Ha_mol.description = 'molecular H_alpha emissivity';
output.Ha_mol.unit = 'photons m^-3 s^-1';
if strcmp(version,'structured')
    output.Ha_mol.dimensions = {'nx','ny','1'};
else
    output.Ha_mol.dimensions = {'nCv','1'};
end

output.mol_source.value = scan_ft_real_grid(fid,ver,'srcml',[ft44dims,nmol]);
output.mol_source.description = 'molecule particle source';
output.mol_source.unit = 'A';
output.mol_source.dimensions = dim_labels_species_mol;

output.en_mol_diss.value = scan_ft_real_grid(fid,ver,'edissml',[ft44dims,nmol]);
output.en_mol_diss.description = 'energy for hydrogenic molecular dissociation';
output.en_mol_diss.unit = 'W';
output.en_mol_diss.dimensions = dim_labels_species_mol;

output.rad_atm.value = scan_ft_real_grid(fid,ver,'eneutrad',[ft44dims,natm]);
output.rad_atm.description = 'radiation rate due to atoms';
output.rad_atm.unit = 'W';
output.rad_atm.dimensions = dim_labels_species_atm;

output.rad_mol.value = scan_ft_real_grid(fid,ver,'emolrad',[ft44dims,nmol]);
output.rad_mol.description = 'radiation rate due to molecules';
output.rad_mol.unit = 'W';
output.rad_mol.dimensions = dim_labels_species_mol;

output.rad_ion.value = scan_ft_real_grid(fid,ver,'eionrad',[ft44dims,nion]);
output.rad_ion.description = 'radiation rate due to test ions';
output.rad_ion.unit = 'W';
output.rad_ion.dimensions = dim_labels_species_ion;

% Integral quantities

try

output.tot_atm_eirene.value = scan_ft_real_grid(fid,ver,'pdena_int',[natm,nstra+1]);
output.tot_atm_eirene.description = 'Total number of atoms over the EIRENE grid';
output.tot_atm_eirene.unit = '-';
output.tot_atm_eirene.dimensions = {'natm','nstra+1'};

output.tot_mol_eirene.value = scan_ft_real_grid(fid,ver,'pdenm_int',[nmol,nstra+1]);
output.tot_mol_eirene.description = 'Total number of molecules over the EIRENE grid';
output.tot_mol_eirene.unit = '-';
output.tot_mol_eirene.dimensions = {'nmol','nstra+1'};

output.tot_ion_eirene.value = scan_ft_real_grid(fid,ver,'pdeni_int',[nion,nstra+1]);
output.tot_ion_eirene.description = 'Total number of test ions over the EIRENE grid';
output.tot_ion_eirene.unit = '-';
output.tot_ion_eirene.dimensions = {'nion','nstra+1'};

output.tot_atm_b2.value = scan_ft_real_grid(fid,ver,'pdena_int_b2',[natm,nstra+1]);
output.tot_atm_b2.description = 'Total number of atoms over the B2.5 grid';
output.tot_atm_b2.unit = '-';
output.tot_atm_b2.dimensions = {'natm','nstra+1'};

output.tot_mol_b2.value = scan_ft_real_grid(fid,ver,'pdenm_int_b2',[nmol,nstra+1]);
output.tot_mol_b2.description = 'Total number of molecules over the B2.5 grid';
output.tot_mol_b2.unit = '-';
output.tot_mol_b2.dimensions = {'nmol','nstra+1'};

output.tot_ion_b2.value = scan_ft_real_grid(fid,ver,'pdeni_int_b2',[nion,nstra+1]);
output.tot_ion_b2.description = 'Total number of test ions over the B2.5 grid';
output.tot_ion_b2.unit = '-';
output.tot_ion_b2.dimensions = {'nion','nstra+1'};

output.tot_en_atm_eirene.value = scan_ft_real_grid(fid,ver,'edena_int',[natm,nstra+1]);
output.tot_en_atm_eirene.description = 'Total energy carried by atoms over the EIRENE grid';
output.tot_en_atm_eirene.unit = 'J';
output.tot_en_atm_eirene.dimensions = {'natm','nstra+1'};

output.tot_en_mol_eirene.value = scan_ft_real_grid(fid,ver,'edenm_int',[nmol,nstra+1]);
output.tot_en_mol_eirene.description = 'Total energy carried by molecules over the EIRENE grid';
output.tot_en_mol_eirene.unit = 'J';
output.tot_en_mol_eirene.dimensions = {'nmol','nstra+1'};

output.tot_en_ion_eirene.value = scan_ft_real_grid(fid,ver,'edeni_int',[nion,nstra+1]);
output.tot_en_ion_eirene.description = 'Total energy carried by test ions over the EIRENE grid';
output.tot_en_ion_eirene.unit = 'J';
output.tot_en_ion_eirene.dimensions = {'nion','nstra+1'};

output.tot_en_atm_b2.value = scan_ft_real_grid(fid,ver,'edena_int_b2',[natm,nstra+1]);
output.tot_en_atm_b2.description = 'Total energy carried by atoms over the B2.5 grid';
output.tot_en_atm_b2.unit = 'J';
output.tot_en_atm_b2.dimensions = {'natm','nstra+1'};

output.tot_en_mol_b2.value = scan_ft_real_grid(fid,ver,'edenm_int_b2',[nmol,nstra+1]);
output.tot_en_mol_b2.description = 'Total energy carried by molecules over the B2.5 grid';
output.tot_en_mol_b2.unit = 'J';
output.tot_en_mol_b2.dimensions = {'nmol','nstra+1'};

output.tot_en_ion_b2.value = scan_ft_real_grid(fid,ver,'edeni_int_b2',[nion,nstra+1]);
output.tot_en_ion_b2.description = 'Total energy carried by test ions over the B2.5 grid';
output.tot_en_ion_b2.unit = 'J';
output.tot_en_ion_b2.dimensions = {'nion','nstra+1'};

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
output.surface_type.description = 'ILIIN surface type variable';
output.surface_type.unit = '-';
output.surface_type.dimensions = {'nlim+nsts'};

output.area.value = scan_ft_real_wall(fid,ver,'wlarea',[nlim+nsts]);
output.area.description = 'surface area';
output.area.unit = 'm^2';
output.area.dimensions = {'nlim+nsts'};

frewind(fid);

% Wall loading, reflection

output.kin_power.value(:,1) = scan_ft_real_wall(fid,ver,'wldnek(0)',[nlim+nsts]);
output.kin_power.description = 'kinetic energy transfered by neutrals to the surface';
output.kin_power.unit = 'W';
output.kin_power.dimensions = {'nlim+nsts','nstra+1'};

output.pot_power.value(:,1) = scan_ft_real_wall(fid,ver,'wldnep(0)',[nlim+nsts]);
output.pot_power.description = 'potential energy released by neutrals on the surface';
output.pot_power.unit = 'W';
output.pot_power.dimensions = {'nlim+nsts','nstra+1'};

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
output.fn_atm.description = 'flux of atoms impinging on the surface';
output.fn_atm.unit = 'A';
output.fn_atm.dimensions = {'nlim+nsts','nstra+1','natm'};

output.en_atm.description = 'average energy of atoms impinging on the surface';
output.en_atm.unit = 'eV';
output.en_atm.dimensions = {'nlim+nsts','nstra+1','natm'};

output.fn_atm_ref.description = 'flux of atoms reflected from the surface';
output.fn_atm_ref.unit = 'A';
output.fn_atm_ref.dimensions = {'nlim+nsts','nstra+1','natm'};

for i = 1:nmol
    output.fn_mol.value(:,:,i) = fn_mol_temp(1+(nlim+nsts)*(i-1):(nlim+nsts)*i,:);
    output.en_mol.value(:,:,i) = en_mol_temp(1+(nlim+nsts)*(i-1):(nlim+nsts)*i,:);
    output.fn_mol_ref.value(:,:,i) = fn_mol_ref_temp(1+(nlim+nsts)*(i-1):(nlim+nsts)*i,:);
end
output.fn_mol.description = 'flux of molecules impinging on the surface';
output.fn_mol.unit = 'A';
output.fn_mol.dimensions = {'nlim+nsts','nstra+1','nmol'};

output.en_mol.description = 'average energy of molecules impinging on the surface';
output.en_mol.unit = 'eV';
output.en_mol.dimensions = {'nlim+nsts','nstra+1','nmol'};

output.fn_mol_ref.description = 'flux of molecules reflected from the surface';
output.fn_mol_ref.unit = 'A';
output.fn_mol_ref.dimensions = {'nlim+nsts','nstra+1','nmol'};

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
output.fn_pls.description = 'flux of plasma ions impinging on the surface';
output.fn_pls.unit = 'A';
output.fn_pls.dimensions = {'nlim+nsts','nstra+1','npls'};

for i = 1:natm
    output.fn_atm_em.value(:,:,i) = fn_atm_em_temp(1+(nlim+nsts)*(i-1):(nlim+nsts)*i,:);
    output.fn_sput_atm.value(:,:,i) = fn_sput_atm_temp(1+(nlim+nsts)*(i-1):(nlim+nsts)*i,:);
end
output.fn_atm_em.description = 'flux of atoms emitted from the surface';
output.fn_atm_em.unit = 'A';
output.fn_atm_em.dimensions = {'nlim+nsts','nstra+1','natm'};

output.fn_sput_atm.description = 'flux of sputtered wall material per atom';
output.fn_sput_atm.unit = 'A';
output.fn_sput_atm.dimensions = {'nlim+nsts','nstra+1','natm'};

for i = 1:nmol
    output.fn_mol_em.value(:,:,i) = fn_mol_em_temp(1+(nlim+nsts)*(i-1):(nlim+nsts)*i,:);
    output.fn_sput_mol.value(:,:,i) = fn_sput_mol_temp(1+(nlim+nsts)*(i-1):(nlim+nsts)*i,:);
end
output.fn_mol_em.description = 'flux of molecules emitted from the surface';
output.fn_mol_em.unit = 'A';
output.fn_mol_em.dimensions = {'nlim+nsts','nstra+1','nmol'};

output.fn_sput_mol.description = 'flux of sputtered wall material per molecule';
output.fn_sput_mol.unit = 'A';
output.fn_sput_mol.dimensions = {'nlim+nsts','nstra+1','nmol'};

output.power_em.value = power_em_temp;
output.power_em.description = 'power carried by particles emitted from the surface';
output.power_em.unit = 'W';
output.power_em.dimensions = {'nlim+nsts','nstra+1'};

output.fn_sput.description = 'flux of sputtered wall material';
output.fn_sput.unit = 'A';
output.fn_sput.dimensions = {'nlim+nsts','nstra+1'};

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
output.abs_rate_atm.description = 'absoption rate for atoms';
output.abs_rate_atm.unit = '-';
output.abs_rate_atm.dimensions = {'nlim+nsts','natm'};

output.pump_atm.description = 'pumped flux for atoms';
output.pump_atm.unit = 'A';
output.pump_atm.dimensions = {'nlim+nsts','natm'};

for i = 1:nmol
    output.abs_rate_mol.value(:,i) = abs_rate_mol_temp(i,:);
    output.pump_mol.value(:,i) = pump_mol_temp(i,:);  
end
output.abs_rate_mol.description = 'absoption rate for molecules';
output.abs_rate_mol.unit = '-';
output.abs_rate_mol.dimensions = {'nlim+nsts','nmol'};

output.pump_mol.description = 'pumped flux for molecules';
output.pump_mol.unit = 'A';
output.pump_mol.dimensions = {'nlim+nsts','nmol'};

for i = 1:nion
    output.abs_rate_ion.value(:,i) = abs_rate_ion_temp(i,:);
    output.pump_ion.value(:,i) = pump_ion_temp(i,:);  
end
output.abs_rate_ion.description = 'absoption rate for test ions';
output.abs_rate_ion.unit = '-';
output.abs_rate_ion.dimensions = {'nlim+nsts','nion'};

output.pump_ion.description = 'pumped flux for test ions';
output.pump_ion.unit = 'A';
output.pump_ion.dimensions = {'nlim+nsts','nion'};

frewind(fid);

fclose(fid);

fprintf('Eirene wall data from fort.44 read\n');

elseif strcmp(version,'unstructured')

    %TODO

end

end

end
