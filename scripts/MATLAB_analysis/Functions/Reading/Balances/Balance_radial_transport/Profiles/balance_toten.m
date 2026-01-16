function [rb,pb] = balance_toten(balfile,indbal,gmtry,axbal,axstrat,default_region,areaend,areatype,radbaldist,polbaldist,strata_plot,residuals)
%
% balance_toten plots the total energy balance
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

fprintf('Total energy balance\n');

%% READ THE REQUIRED ARRAYS FROM THE BALANCE FILE

% Geometry variables
nx = gmtry.nx;
ny = gmtry.ny;
nstra = gmtry.nstra;
rightix = gmtry.rightix+1;
rightiy = gmtry.rightiy+1;

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

% Ion energy fluxes
tmp = ncread(balfile,'fhi_cond'); % Heat conduction
fhix_cond = tmp(:,:,1);
fhiy_cond = tmp(:,:,2);
tmp = ncread(balfile,'fhi_32'); % Heat convection
fhix_32 = tmp(:,:,1);
fhiy_32 = tmp(:,:,2);
tmp = ncread(balfile,'fhi_dia'); % ExB drift
fhix_dia = tmp(:,:,1);
fhiy_dia = tmp(:,:,2);
tmp = ncread(balfile,'fhi_ecrb'); % Diamagnetic drift
fhix_ecrb = tmp(:,:,1);
fhiy_ecrb = tmp(:,:,2);
tmp = ncread(balfile,'fhi_inert'); % Inertial-current-related flux
fhix_inert = tmp(:,:,1);
fhiy_inert = tmp(:,:,2);
tmp = ncread(balfile,'fhi_vispar'); % Parallel-viscosity-current-related flux
fhix_vispar = tmp(:,:,1);
fhiy_vispar = tmp(:,:,2);
tmp = ncread(balfile,'fhi_anml'); % Anomalous-current-related flux
fhix_anml = tmp(:,:,1);
fhiy_anml = tmp(:,:,2);
try
    tmp = ncread(balfile,'fhi_vzh'); % Ion-velocity-related flux
catch
    tmp=zeros(nx,ny,2);
end
fhix_vzh = tmp(:,:,1);
fhiy_vzh = tmp(:,:,2);

% Electron energy sources (fluid)
b2sihs_divue = ncread(balfile,'b2sihs_divue_bal'); % Parallel electron velocity gradient heating
tmp = ncread(balfile,'b2stel_she_bal');
dim = [size(tmp)];
b2stel_she = sum(tmp(:,:,[1:dim(3)]),3); % Atomic processes + radiation
b2sihs_joule = ncread(balfile,'b2sihs_joule_bal'); % Joule heating
b2sihs_exbe = ncread(balfile,'b2sihs_exbe_bal'); % ExB drift heating
b2sihs_diae = ncread(balfile,'b2sihs_diae_bal'); % Diamagnetic drift heating

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

% Ion energy sources (fluid)
b2sihs_divua = ncread(balfile,'b2sihs_divua_bal'); % Parallel ion velocity gradient heating
b2sihs_visa = ncread(balfile,'b2sihs_visa_bal'); % Viscosity heating
b2stel_shi_ion = ncread(balfile,'b2stel_shi_ion_bal'); % Atomic processes
b2stel_shi_rec = ncread(balfile,'b2stel_shi_rec_bal');
b2stcx_shi = ncread(balfile,'b2stcx_shi_bal');
b2sihs_fraa = ncread(balfile,'b2sihs_fraa_bal'); % Friction heating
b2sihs_exba = ncread(balfile,'b2sihs_exba_bal'); % ExB drift heating
b2sihs_diaa = ncread(balfile,'b2sihs_diaa_bal'); % Diamagnetic drift heating

% Ion energy sources (EIRENE)
if (gmtry.b2mndr_eirene~=0)
    eirene_mc_eapl_shi = ncread(balfile,'eirene_mc_eapl_shi_bal'); % Plasma-atom collisions
    eirene_mc_empl_shi = ncread(balfile,'eirene_mc_empl_shi_bal'); % Plasma-molecule collisions
    eirene_mc_eipl_shi = ncread(balfile,'eirene_mc_eipl_shi_bal'); % Plasma-test ion collisions
    eirene_mc_eppl_shi = ncread(balfile,'eirene_mc_eppl_shi_bal'); % Recombination
else
    eirene_mc_eapl_shi = zeros(nx,ny,nstra);
    eirene_mc_empl_shi = zeros(nx,ny,nstra);
    eirene_mc_eipl_shi = zeros(nx,ny,nstra);
    eirene_mc_eppl_shi = zeros(nx,ny,nstra);
end

% Boundary sources
b2stbc_she = ncread(balfile,'b2stbc_she_bal');
b2stbc_shi = ncread(balfile,'b2stbc_shi_bal');

% Recycling sources
b2stbr_phys_she = ncread(balfile,'b2stbr_phys_she_bal');
b2stbr_bas_she = ncread(balfile,'b2stbr_bas_she_bal');
b2stbr_first_flight_she = ncread(balfile,'b2stbr_first_flight_she_bal');
b2stbr_phys_shi = ncread(balfile,'b2stbr_phys_shi_bal');
b2stbr_bas_shi = ncread(balfile,'b2stbr_bas_shi_bal');
b2stbr_first_flight_shi = ncread(balfile,'b2stbr_first_flight_shi_bal');

% Other sources
b2stbm_she = ncread(balfile,'b2stbm_she_bal');
ext_she = ncread(balfile,'ext_she_bal');
b2srsm_she = ncread(balfile,'b2srsm_she_bal');
b2srdt_she = ncread(balfile,'b2srdt_she_bal');
b2srst_she = ncread(balfile,'b2srst_she_bal');
b2stbm_shi = ncread(balfile,'b2stbm_shi_bal');
ext_shi = ncread(balfile,'ext_shi_bal');
b2srsm_shi = ncread(balfile,'b2srsm_shi_bal');
b2srdt_shi = ncread(balfile,'b2srdt_shi_bal');
b2srst_shi = ncread(balfile,'b2srst_shi_bal');

% Residual
reshe = ncread(balfile,'reshe');
reshi = ncread(balfile,'reshi');

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

poldivi_cond = zeros(nx,ny);
poldivi_32 = zeros(nx,ny);
poldivi_dia = zeros(nx,ny);
poldivi_ecrb = zeros(nx,ny);
poldivi_inert = zeros(nx,ny);
poldivi_vispar = zeros(nx,ny);
poldivi_anml = zeros(nx,ny);
poldivi_vzh = zeros(nx,ny);

for ix=1:nx
    for iy=1:ny
        if rightix(ix,iy)>nx
            continue;
        end
        poldivi_cond(ix,iy) = fhix_cond(ix,iy)-fhix_cond(rightix(ix,iy),rightiy(ix,iy));
        poldivi_32(ix,iy) = fhix_32(ix,iy)-fhix_32(rightix(ix,iy),rightiy(ix,iy));
        poldivi_dia(ix,iy) = fhix_dia(ix,iy)-fhix_dia(rightix(ix,iy),rightiy(ix,iy));
        poldivi_ecrb(ix,iy) = fhix_ecrb(ix,iy)-fhix_ecrb(rightix(ix,iy),rightiy(ix,iy));
        poldivi_inert(ix,iy) = fhix_inert(ix,iy)-fhix_inert(rightix(ix,iy),rightiy(ix,iy));
        poldivi_vispar(ix,iy) = fhix_vispar(ix,iy)-fhix_vispar(rightix(ix,iy),rightiy(ix,iy));
        poldivi_anml(ix,iy) = fhix_anml(ix,iy)-fhix_anml(rightix(ix,iy),rightiy(ix,iy));
        poldivi_vzh(ix,iy) = fhix_vzh(ix,iy)-fhix_vzh(rightix(ix,iy),rightiy(ix,iy));
    end
end

%% PPRODUCE THE PLOTS

% Radial balance
rb = radial_balance(...
    cat(3,...
        fhey_cond,... % Electron heat conduction
        fhiy_cond,... % Ion heat conduction
        fhey_32,... % Electron heat convection
        fhiy_32,... % Ion heat convection
        fhey_ecrb+fhey_dia+fhiy_dia+fhiy_ecrb,... % Drift-related heat convection
        fhey_thermj+fhiy_inert+fhiy_vispar+fhiy_anml,... % Current-related heat convection
        fhiy_vzh)/1E6,... % Ion-velocity-related heat flux
    cat(3,...
        poldive_32+poldive_ecrb+poldive_dia+poldive_cond+poldive_thermj+poldivi_cond+poldivi_32+poldivi_dia+poldivi_ecrb+poldivi_inert+poldivi_vispar+poldivi_anml+poldivi_vzh,... % Parallel losses
        b2sihs_divue + b2sihs_divua,... % Parallel velocity gradient heating
        b2stel_she+b2stel_shi_ion+b2stel_shi_rec+b2stcx_shi,... % Atomic processes (B2) + radiation
        b2sihs_joule,... % Joule heating
        b2sihs_visa,... % Viscosity heating
        b2sihs_fraa,... % Friction heating
        b2sihs_diae+b2sihs_exbe+b2sihs_diaa+b2sihs_exba,... % Drift heating
        sum(eirene_mc_eael_she,3)+sum(eirene_mc_emel_she,3)+sum(eirene_mc_eiel_she,3)+sum(eirene_mc_eapl_shi,3)+sum(eirene_mc_empl_shi,3)+sum(eirene_mc_eipl_shi,3),... % Plasma-neutral collisions (EIRENE)
        sum(eirene_mc_epel_she,3)+sum(eirene_mc_eppl_shi,3),... % Recombinations (EIRENE)
        b2stbc_she+b2stbc_shi,... % Boundary source
        b2stbr_phys_she+b2stbr_bas_she+b2stbr_first_flight_she+b2stbr_phys_shi+b2stbr_bas_shi+b2stbr_first_flight_shi,... % Recycling source
        b2stbm_she+ext_she+b2srsm_she+b2srdt_she+b2srst_she+b2stbm_shi+ext_shi+b2srsm_shi+b2srdt_shi+b2srst_shi)/1E6,... % Additional + numeric sources
    (reshe+reshi)/1E6,...
{'Total poloidally-integrated energy flux',...
 'Total poloidally-integrated energy source',...
 'Poloidally-integrated residual'},...
{'Electron heat conduction',...
 'Ion heat conduction',...
 'Electron heat convection',...
 'Ion heat convection',...
 'Drift-related heat convection',...
 'Current-related heat convection',...
 'Ion-velocity-related heat flux'},...
{'Parallel losses',...
 'Parallel velocity gradient heating',...
 'Atomic processes (B2) + radiation',...
 'Joule heating',...
 'Viscosity heating',...
 'Friction heating',...
 'Drift heating',...
 'Plasma-neutral collisions (EIRENE)',...
 'Recombinations (EIRENE)',...
 'Boundary source',...
 'Recycling source',...
 'Additional + numeric sources'},...
 gmtry,indbal,false,axbal(1:3),units,default_region,areaend,areatype,radbaldist,residuals);

% Poloidal balance
pb = poloidal_balance(...
    cat(3,...
        fhey_cond,... % Electron heat conduction
        fhiy_cond,... % Ion heat conduction
        fhey_32,... % Electron heat convection
        fhiy_32,... % Ion heat convection
        fhey_ecrb+fhey_dia+fhiy_dia+fhiy_ecrb,... % Drift-related heat convection
        fhey_thermj+fhiy_inert+fhiy_vispar+fhiy_anml,... % Current-related heat convection
        fhiy_vzh)/1E6,... % Ion-velocity-related heat flux
    cat(3,...
        poldive_32+poldive_ecrb+poldive_dia+poldive_cond+poldive_thermj+poldivi_cond+poldivi_32+poldivi_dia+poldivi_ecrb+poldivi_inert+poldivi_vispar+poldivi_anml+poldivi_vzh,... % Parallel losses
        b2sihs_divue + b2sihs_divua,... % Parallel velocity gradient heating
        b2stel_she+b2stel_shi_ion+b2stel_shi_rec+b2stcx_shi,... % Atomic processes (B2) + radiation
        b2sihs_joule,... % Joule heating
        b2sihs_visa,... % Viscosity heating
        b2sihs_fraa,... % Friction heating
        b2sihs_diae+b2sihs_exbe+b2sihs_diaa+b2sihs_exba,... % Drift heating
        sum(eirene_mc_eael_she,3)+sum(eirene_mc_emel_she,3)+sum(eirene_mc_eiel_she,3)+sum(eirene_mc_eapl_shi,3)+sum(eirene_mc_empl_shi,3)+sum(eirene_mc_eipl_shi,3),... % Plasma-neutral collisions (EIRENE)
        sum(eirene_mc_epel_she,3)+sum(eirene_mc_eppl_shi,3),... % Recombinations (EIRENE)
        b2stbc_she+b2stbc_shi,... % Boundary source
        b2stbr_phys_she+b2stbr_bas_she+b2stbr_first_flight_she+b2stbr_phys_shi+b2stbr_bas_shi+b2stbr_first_flight_shi,... % Recycling source
        b2stbm_she+ext_she+b2srsm_she+b2srdt_she+b2srst_she+b2stbm_shi+ext_shi+b2srsm_shi+b2srdt_shi+b2srst_shi)/1E6,... % Additional + numeric sources
    (reshe+reshi)/1E6,...
{'Total separatrix energy flux',...
 'Total wall boundary energy flux',...
 'Total radially-integrated energy source',...
 'Radially-integrated residual'},...
{'Electron heat conduction',...
 'Ion heat conduction',...
 'Electron heat convection',...
 'Ion heat convection',...
 'Drift-related heat convection',...
 'Current-related heat convection',...
 'Ion-velocity-related heat flux'},...
{'Parallel losses',...
 'Parallel velocity gradient heating',...
 'Atomic processes (B2) + radiation',...
 'Joule heating',...
 'Viscosity heating',...
 'Friction heating',...
 'Drift heating',...
 'Plasma-neutral collisions (EIRENE)',...
 'Recombinations (EIRENE)',...
 'Boundary source',...
 'Recycling source',...
 'Additional + numeric sources'},...
 gmtry,indbal,false,axbal(4:7),units,default_region,areaend,areatype,polbaldist,residuals);

% Strata decomposition
if strata_plot
    strata_plots({eirene_mc_eael_she/1E6+eirene_mc_eapl_shi/1E6},{eirene_mc_emel_she/1E6+eirene_mc_empl_shi/1E6},...
                      {eirene_mc_eiel_she/1E6+eirene_mc_eipl_shi/1E6},{eirene_mc_epel_she/1E6+eirene_mc_eppl_shi/1E6},...
                      {'Strata decomposition of the total poloidally-integrated EIRENE total energy source',...
                       'Strata decomposition of the total radially-integrated EIRENE total energy source'},...
                      {''},gmtry,indbal,nstra,axstrat,axbal,rb.Radial_coordinate_cell,pb.Poloidal_coordinate,rb.area_divide_rad,pb.area_divide_pol,false);
end              

end