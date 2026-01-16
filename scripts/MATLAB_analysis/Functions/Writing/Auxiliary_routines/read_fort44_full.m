function [neutrals_grid,wall] = read_fort44_full(fid,simulation)
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

%% READ THE DATA ON THE COMPUTATIONAL GRID

neutrals_grid = [];

% Read the dimensions

dims = fscanf(fid,'%d',3);
nx   = dims(1);
ny   = dims(2);
ver  = dims(3);

neutrals_grid.nx = nx;
neutrals_grid.ny = ny;

% if ver ~= 20081111 && ver ~= 20160829 && ver ~= 20170328
%     error('Error: read_ft44: unknown format of fort.44 file');
% end

line = fgetl(fid);

while ~contains(line,'wldnek(0)')
    prevline = line;
    line = fgetl(fid);
end

dims  = sscanf(prevline,'%d',3);
nlim  = dims(1);
nsts  = dims(2);
nstra = dims(3);
neutrals_grid.nstra = nstra;

frewind(fid);

% Read the names of the strata

temp = find(contains({simulation.run.name},'b2.neutrals.parameters'));
fid_neut_par = simulation.run(temp).fid;
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

% Read the number of species

fgetl(fid);

dims = fscanf(fid,'%d',3);
natm = dims(1);
nmol = dims(2);
nion = dims(3);
neutrals_grid.natm = natm;
neutrals_grid.nmol = nmol;
neutrals_grid.nion = nion;

% Write the names of strata and species

neutrals_grid.strata = stratum_name;

line = fgetl(fid);
for i = 1:natm
    line = fgetl(fid);
    neutrals_grid.species_atm{i} = strtrim(line);
end
for i = 1:nmol
    line = fgetl(fid);
    neutrals_grid.species_mol{i} = strtrim(line);
end
for i = 1:nion
    line = fgetl(fid);
    neutrals_grid.species_ion{i} = strtrim(line);
end

% State variables

neutrals_grid.dab2       = scan_ft_real_grid(fid,ver,'dab2',[nx,ny,natm]); % atomic density, m^-3
neutrals_grid.tab2       = scan_ft_real_grid(fid,ver,'tab2',[nx,ny,natm]); % atomic temperature, eV
neutrals_grid.dmb2       = scan_ft_real_grid(fid,ver,'dmb2',[nx,ny,nmol]); % molecular density, m^-3
neutrals_grid.tmb2       = scan_ft_real_grid(fid,ver,'tmb2',[nx,ny,nmol]); % molecular temperature, eV
neutrals_grid.dib2       = scan_ft_real_grid(fid,ver,'dib2',[nx,ny,nion]); % test ions density, m^-3
neutrals_grid.tib2       = scan_ft_real_grid(fid,ver,'tib2',[nx,ny,nion]); % test ions temperature, eV

% Fluxes

neutrals_grid.rfluxa     = scan_ft_real_grid(fid,ver,'rfluxa',[nx,ny,natm]); % atomic radial flux density, m^-2 s^-1
neutrals_grid.rfluxm     = scan_ft_real_grid(fid,ver,'rfluxm',[nx,ny,nmol]); % molecular radial flux density, m^-2 s^-1
neutrals_grid.pfluxa     = scan_ft_real_grid(fid,ver,'pfluxa',[nx,ny,natm]); % atomic poloidal flux density, m^-2 s^-1
neutrals_grid.pfluxm     = scan_ft_real_grid(fid,ver,'pfluxm',[nx,ny,nmol]); % molecular poloidal flux density, m^-2 s^-1
neutrals_grid.refluxa    = scan_ft_real_grid(fid,ver,'refluxa',[nx,ny,natm]); % atomic radial energy flux density, W m^-2
neutrals_grid.refluxm    = scan_ft_real_grid(fid,ver,'refluxm',[nx,ny,nmol]); % molecular radial energy flux density, W m^-2
neutrals_grid.pefluxa    = scan_ft_real_grid(fid,ver,'pefluxa',[nx,ny,natm]); % atomic poloidal energy flux density, W m^-2
neutrals_grid.pefluxm    = scan_ft_real_grid(fid,ver,'pefluxm',[nx,ny,nmol]); % molecular poloidal energy flux density, W m^-2

% Radiation, emissivity and dissociation

neutrals_grid.emiss       = scan_ft_real_grid(fid,ver,'emiss',[nx,ny,1]); % atomic H_alpha emissivity, photons m^-3 s^-1
neutrals_grid.emissmol    = scan_ft_real_grid(fid,ver,'emissmol',[nx,ny,1]); % molecular H_alpha emissivity, photons m^-3 s^-1
neutrals_grid.srcml       = scan_ft_real_grid(fid,ver,'srcml',[nx,ny,nmol]); % molecule particle source, A
neutrals_grid.edissml     = scan_ft_real_grid(fid,ver,'edissml',[nx,ny,nmol]); % energy for hydrogenic molecular dissociation, W
neutrals_grid.eneutrad    = scan_ft_real_grid(fid,ver,'eneutrad',[nx,ny,natm]); % radiation rate due to atoms, W
neutrals_grid.emolrad     = scan_ft_real_grid(fid,ver,'emolrad',[nx,ny,nmol]); % radiation rate due to molecules, W
neutrals_grid.eionrad     = scan_ft_real_grid(fid,ver,'eionrad',[nx,ny,nion]); % radiation rate due to test ions, W

% Integral quantities

neutrals_grid.pdena_int   = scan_ft_real_grid(fid,ver,'pdena_int',[natm,nstra+1]); % Total number of atoms over the EIRENE grid
neutrals_grid.pdenm_int   = scan_ft_real_grid(fid,ver,'pdenm_int',[nmol,nstra+1]); % Total number of molecules over the EIRENE grid
neutrals_grid.pdeni_int   = scan_ft_real_grid(fid,ver,'pdeni_int',[nion,nstra+1]); % Total number of test ions over the EIRENE grid
neutrals_grid.pdena_int_b2    = scan_ft_real_grid(fid,ver,'pdena_int_b2',[natm,nstra+1]); % Total number of atoms over the B2.5 grid
neutrals_grid.pdenm_int_b2    = scan_ft_real_grid(fid,ver,'pdenm_int_b2',[nmol,nstra+1]); % Total number of molecules over the B2.5 grid
neutrals_grid.pdeni_int_b2    = scan_ft_real_grid(fid,ver,'pdeni_int_b2',[nion,nstra+1]); % Total number of test ions over the B2.5 grid

neutrals_grid.edena_int   = scan_ft_real_grid(fid,ver,'edena_int',[natm,nstra+1]); % Total energy carried by atoms over the EIRENE grid, J
neutrals_grid.edenm_int   = scan_ft_real_grid(fid,ver,'edenm_int',[nmol,nstra+1]); % Total energy carried by molecules over the EIRENE grid, J
neutrals_grid.edeni_int   = scan_ft_real_grid(fid,ver,'edeni_int',[nion,nstra+1]); % Total energy carried by test ions over the EIRENE grid, J
neutrals_grid.edena_int_b2    = scan_ft_real_grid(fid,ver,'edena_int_b2',[natm,nstra+1]); % Total energy carried by atoms over the B2.5 grid, J
neutrals_grid.edenm_int_b2    = scan_ft_real_grid(fid,ver,'edenm_int_b2',[nmol,nstra+1]); % Total energy carried by molecules over the B2.5 grid, J
neutrals_grid.edeni_int_b2    = scan_ft_real_grid(fid,ver,'edeni_int_b2',[nion,nstra+1]); % Total energy carried by test ions over the B2.5 grid, J

frewind(fid);

%% READ WALL DATA

wall = [];

% To do

end
