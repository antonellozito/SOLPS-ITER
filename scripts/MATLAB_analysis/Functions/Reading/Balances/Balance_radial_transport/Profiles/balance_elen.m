function [rb,pb] = balance_elen(balfile,indbal,gmtry,axbal,axstrat,default_region,areaend,areatype,radbaldist,polbaldist,strata_plot,residuals)
%
% balance_elen plots the electron energy balance
%                                                                                                              
% balfile:        Full path to balance.nc file                                                                 
% indbal:         Logical matrix of size nx*ny that is true for cells where the balances should be performed   
% gmtry:          Structure containing commonly-used variables
% axbal:          Array of axes into which balance plots will be placed                                        
% axstrat:        Array of axes into which strata plots will be placed                                         
% default_region: Definition of the region which the balance is performed                                      
% areaend:        Defines the radial end of the balance region at which areas will be calculated               
% areatype:       The type of area that radial fluxes are divided by
% radbaldist:     Defines the distance used on the x-axis of the radial balance plots   
% polbaldist:     Defines the distance used on the x-axis of the poloidal balance plots                        
% strata_plot:    If true then divide the EIRENE source into components from each stratum (in a new figure)    
% residuals:      If true then residual are also plotted in the poloidal balance plots                         
%

fprintf('Electron energy balance\n');

%% READ THE REQUIRED ARRAYS FROM THE BALANCE FILE

% Geometry variables
nx = gmtry.nx;
ny = gmtry.ny;
nstra = gmtry.nstra;
rightix = gmtry.rightix+1;
rightiy = gmtry.rightiy+1;

% Species
S = ncread(balfile,'species');
numSpecies = size(S,2);
species = cell(1,numSpecies);
for k = 1:numSpecies
    col = S(:,k)'; 
    col(col==' ') = [];
    species{k} = col;
end
atomLabels = cellfun(@(s) regexp(s,'^[A-Za-z]+','match'), species, 'UniformOutput', false);
atomLabels = [atomLabels{:}];
atoms = unique(atomLabels,'stable');
natm = numel(atoms);
groups = cell(1,natm);
for k = 1:natm
    groups{k} = find(strcmp(atomLabels, atoms{k}));
    radiation_label{k} = sprintf('Line radiation (%s)',atoms{k});
end

% Electron energy fluxes
tmp = ncread(balfile,'fhe_cond'); % Heat conduction
fhex_cond = tmp(:,:,1);
fhey_cond = tmp(:,:,2);
tmp = ncread(balfile,'fhe_32'); % Heat convection
fhex_32 = tmp(:,:,1);
fhey_32 = tmp(:,:,2);
tmp = ncread(balfile,'fhe_ecrb'); % ExB drift
fhex_ecrb = tmp(:,:,1);
fhey_ecrb = tmp(:,:,2);
tmp = ncread(balfile,'fhe_dia'); % Diamagnetic drift
fhex_dia = tmp(:,:,1);
fhey_dia = tmp(:,:,2);
tmp = ncread(balfile,'fhe_thermj'); % Current-related flux
fhex_thermj = tmp(:,:,1);
fhey_thermj = tmp(:,:,2);

% Electron energy sources (fluid)
b2sihs_divue = ncread(balfile,'b2sihs_divue_bal'); % Parallel electron velocity gradient heating
tmp = ncread(balfile,'b2stel_she_bal');
for i = 1:natm
    b2stel_she{i} = sum(tmp(:,:,groups{i}),3); % Line radiation
end
b2sihs_joule = ncread(balfile,'b2sihs_joule_bal'); % Joule heating
b2sihs_exbe = ncread(balfile,'b2sihs_exbe_bal'); % ExB drift heating
b2sihs_diae = ncread(balfile,'b2sihs_diae_bal'); % Diamagnetic drift heating
b2npht_shei = -ncread(balfile,'b2npht_shei_bal'); % Electron-ion temperature equilibration

% Electron energy sources (EIRENE)
if (gmtry.b2mndr_eirene~=0)
    eirene_mc_eael_she = ncread(balfile,'eirene_mc_eael_she_bal'); % Plasma-atom collisions
    eirene_mc_emel_she = ncread(balfile,'eirene_mc_emel_she_bal'); % Plasma-molecule collisions
    eirene_mc_eiel_she = ncread(balfile,'eirene_mc_eiel_she_bal'); % Plasma-test ion collisions
    eirene_mc_epel_she = ncread(balfile,'eirene_mc_epel_she_bal'); % Recombination
else
    eirene_mc_eael_she = zeros(nx,ny,nstra);
    eirene_mc_emel_she = zeros(nx,ny,nstra);
    eirene_mc_eiel_she = zeros(nx,ny,nstra);
    eirene_mc_epel_she = zeros(nx,ny,nstra);
end

% Boundary sources
b2stbc_she = ncread(balfile,'b2stbc_she_bal');

% Recycling sources
b2stbr_phys_she = ncread(balfile,'b2stbr_phys_she_bal');
b2stbr_bas_she = ncread(balfile,'b2stbr_bas_she_bal');
b2stbr_first_flight_she = ncread(balfile,'b2stbr_first_flight_she_bal');

% Other sources
b2stbm_she = ncread(balfile,'b2stbm_she_bal');
ext_she = ncread(balfile,'ext_she_bal');
b2srsm_she = ncread(balfile,'b2srsm_she_bal');
b2srdt_she = ncread(balfile,'b2srdt_she_bal');
b2srst_she = ncread(balfile,'b2srst_she_bal');

% Residual
reshe = ncread(balfile,'reshe');

%% CREATE THE UNITS STRINGS

switch areatype
    case 'contact'
        units = 'MWm^{-2}';
    case 'none'
        units = 'MW';
    otherwise
        error('Error: Area type ''%s'' not supported.',areatype);
end

%% CALCULATE THE POLOIDAL DIVERGENCES

poldive_cond = zeros(nx,ny);
poldive_32 = zeros(nx,ny);
poldive_ecrb = zeros(nx,ny);
poldive_dia = zeros(nx,ny);
poldive_thermj = zeros(nx,ny);

for ix=1:nx
    for iy=1:ny
        if rightix(ix,iy)>nx
            continue;
        end
        poldive_cond(ix,iy) = fhex_cond(ix,iy)-fhex_cond(rightix(ix,iy),rightiy(ix,iy));
        poldive_32(ix,iy) = fhex_32(ix,iy)-fhex_32(rightix(ix,iy),rightiy(ix,iy));
        poldive_ecrb(ix,iy) = fhex_ecrb(ix,iy)-fhex_ecrb(rightix(ix,iy),rightiy(ix,iy));
        poldive_dia(ix,iy) = fhex_dia(ix,iy)-fhex_dia(rightix(ix,iy),rightiy(ix,iy));
        poldive_thermj(ix,iy) = fhex_thermj(ix,iy)-fhex_thermj(rightix(ix,iy),rightiy(ix,iy));
    end
end

%% PRODUCE THE PLOTS

% Radial balance
rb = radial_balance(...
    cat(3,...
        fhey_cond,... % Heat conduction
        fhey_32,... % Heat convection
        fhey_ecrb+fhey_dia,... % Drift-related heat convection
        fhey_thermj)/1E6,... % Current-related heat convection
    cat(3,...
        poldive_32+poldive_ecrb+poldive_dia+poldive_cond+poldive_thermj,... % Parallel losses
        b2sihs_divue,... % Parallel electron velocity gradient heating
        b2stel_she{:},... % Line radiation
        b2sihs_joule,... % Joule heating
        b2sihs_diae+b2sihs_exbe,... % Drift heating
        b2npht_shei,... % e-i temperature equilibration
        sum(eirene_mc_eael_she,3)+sum(eirene_mc_emel_she,3)+sum(eirene_mc_eiel_she,3),... % Plasma-neutral collisions (EIRENE)
        sum(eirene_mc_epel_she,3),... % Recombinations (EIRENE)
        b2stbc_she,... % Boundary source
        b2stbr_phys_she+b2stbr_bas_she+b2stbr_first_flight_she,... % Recycling source
        b2stbm_she+ext_she+b2srsm_she+b2srdt_she+b2srst_she)/1E6,... % Additional + numeric sources
    reshe/1E6,...
{'Total poloidally-integrated el. energy flux',...
 'Total poloidally-integrated el. energy source',...
 'Poloidally-integrated residual'},...
{'Heat conduction',...
 'Heat convection',...
 'Drift-related heat convection',...
 'Current-related heat convection'},...
{'Parallel losses',...
 'Parallel el. velocity gradient heating',...
 radiation_label{:},...
 'Joule heating',...
 'Drift heating',...
 'e-i temperature equilibration',...
 'Plasma-neutral collisions (EIRENE)',...
 'Recombinations (EIRENE)',...
 'Boundary source',...
 'Recycling source',...
 'Additional + numeric sources'},...
 gmtry,indbal,false,axbal(1:3),units,default_region,areaend,areatype,radbaldist,residuals);

% Poloidal balance
pb = poloidal_balance(...
    cat(3,...
        fhey_cond,... % Heat conduction
        fhey_32,... % Heat convection
        fhey_ecrb+fhey_dia,... % Drift-related heat convection
        fhey_thermj)/1E6,... % Current-related heat convection
    cat(3,...
        poldive_32+poldive_ecrb+poldive_dia+poldive_cond+poldive_thermj,... % Radial transport
        b2sihs_divue,... % Parallel electron velocity gradient heating
        b2stel_she{:},... % Line radiation
        b2sihs_joule,... % Joule heating
        b2sihs_diae+b2sihs_exbe,... % Drift heating
        b2npht_shei,... % e-i temperature equilibration
        sum(eirene_mc_eael_she,3)+sum(eirene_mc_emel_she,3)+sum(eirene_mc_eiel_she,3),... % Plasma-neutral collisions (EIRENE)
        sum(eirene_mc_epel_she,3),... % Recombinations (EIRENE)
        b2stbc_she,... % Boundary source
        b2stbr_phys_she+b2stbr_bas_she+b2stbr_first_flight_she,... % Recycling source
        b2stbm_she+ext_she+b2srsm_she+b2srdt_she+b2srst_she)/1E6,... % Additional + numeric sources
    reshe/1E6,....
{'Total separatrix el. energy flux',...
 'Total wall boundary el. energy flux',...
 'Total radially-integrated el. energy source',...
 'Radially-integrated residual'},...
{'Heat conduction',...
 'Heat convection',...
 'Drift-related heat convection',...
 'Current-related heat convection'},...
{'Parallel losses',...
 'Parallel el. velocity gradient heating',...
 radiation_label{:},...
 'Joule heating',...
 'Drift heating',...
 'e-i temperature equilibration',...
 'Plasma-neutral collisions (EIRENE)',...
 'Recombinations (EIRENE)',...
 'Boundary source',...
 'Recycling source',...
 'Additional + numeric sources'},...
 gmtry,indbal,false,axbal(4:7),units,default_region,areaend,areatype,polbaldist,residuals);

% Strata decomposition
if strata_plot
    strata_plots({eirene_mc_eael_she/1E6},{eirene_mc_emel_she/1E6},{eirene_mc_eiel_she/1E6},{eirene_mc_epel_she/1E6},...
                      {'Strata decomposition of the total poloidally-integrated EIRENE el. energy source',...
                       'Strata decomposition of the total radially-integrated EIRENE el. energy source'},...
                      {''},gmtry,indbal,nstra,axstrat,axbal,rb.Radial_coordinate_cell,pb.Poloidal_coordinate,rb.area_divide_rad,pb.area_divide_pol,false);
end              

end