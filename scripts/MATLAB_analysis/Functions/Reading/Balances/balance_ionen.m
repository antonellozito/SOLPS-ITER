function [rb,pb] = balance_ionen(transport_mode,varargin)

transport_mode = lower(char(transport_mode));

switch transport_mode
    case 'parallel'
        [balfile,indbal,gmtry,reverse,axbal,axstrat,default_region,areaend,areatype,radbaldist,polbaldist,strata_plot,residuals] = deal(varargin{:});
%
% balance_ionen plots the ion energy balance                    
%                                                                                                              
% balfile:        Full path to balance.nc file                                                                 
% indbal:         Logical matrix of size nx*ny that is true for cells where the balances should be performed   
% gmtry:          Structure containing commonly-used variables
% reverse:        True if the right-most end of the balance volume is upstream of the left-most end, otherwise false
% axbal:          Array of axes into which balance plots will be placed                                        
% axstrat:        Array of axes into which strata plots will be placed                                         
% default_region: Definition of the region which the balance is performed                                      
% areaend:        Defines the radial end of the balance region at which areas will be calculated               
% areatype:       The type of area that poloidal fluxes are divided by           
% radbaldist:     Defines the distance used on the x-axis of the radial balance plots   
% polbaldist:     Defines the distance used on the x-axis of the poloidal balance plots                        
% strata_plot:    If true then divide the EIRENE source into components from each stratum (in a new figure)    
% residuals:      If true then residual are also plotted in the poloidal balance plots                         
%

fprintf('Ion energy balance\n');

%% READ THE REQUIRED ARRAYS FROM THE BALANCE FILE

% Geometry variables
nx = gmtry.nx;
ny = gmtry.ny;
nstra = gmtry.nstra;
topix = gmtry.topix+1;
topiy = gmtry.topiy+1;

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

% Ion energy sources (fluid)
b2sihs_divua = ncread(balfile,'b2sihs_divua_bal'); % Parallel ion velocity gradient heating
b2sihs_visa = ncread(balfile,'b2sihs_visa_bal'); % Viscosity heating
b2stel_shi_ion = ncread(balfile,'b2stel_shi_ion_bal'); % Atomic processes
b2stel_shi_rec = ncread(balfile,'b2stel_shi_rec_bal');
b2stcx_shi = ncread(balfile,'b2stcx_shi_bal');
b2sihs_fraa = ncread(balfile,'b2sihs_fraa_bal'); % Friction heating
b2sihs_exba = ncread(balfile,'b2sihs_exba_bal'); % ExB drift heating
b2sihs_diaa = ncread(balfile,'b2sihs_diaa_bal'); % Diamagnetic drift heating
b2npht_shei = ncread(balfile,'b2npht_shei_bal'); % Electron-ion temperature equilibration

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
b2stbc_shi = ncread(balfile,'b2stbc_shi_bal');

% Recycling sources
b2stbr_phys_shi = ncread(balfile,'b2stbr_phys_shi_bal');
b2stbr_bas_shi = ncread(balfile,'b2stbr_bas_shi_bal');
b2stbr_first_flight_shi = ncread(balfile,'b2stbr_first_flight_shi_bal');

% Other sources
b2stbm_shi = ncread(balfile,'b2stbm_shi_bal');
ext_shi = ncread(balfile,'ext_shi_bal');
b2srsm_shi = ncread(balfile,'b2srsm_shi_bal');
b2srdt_shi = ncread(balfile,'b2srdt_shi_bal');
b2srst_shi = ncread(balfile,'b2srst_shi_bal');

% Residual
reshi = ncread(balfile,'reshi');

%% CREATE THE UNITS STRINGS

switch areatype
    case 'parallel'        
        units = 'MWm^{-2}';
    case 'contact'
        units = 'MWm^{-2}';
    case 'none'
        units = 'MW';
    otherwise
        error('Error: Area type ''%s'' not supported.',areatype);
end

%% CALCULATE THE RADIAL DIVERGENCES

raddivi_cond = zeros(nx,ny);
raddivi_32 = zeros(nx,ny);
raddivi_dia = zeros(nx,ny);
raddivi_ecrb = zeros(nx,ny);
raddivi_inert = zeros(nx,ny);
raddivi_vispar = zeros(nx,ny);
raddivi_anml = zeros(nx,ny);
raddivi_vzh = zeros(nx,ny);

for iy=1:ny
    for ix=1:nx
        if topiy(ix,iy)>ny
            continue;
        end
        raddivi_cond(ix,iy) = fhiy_cond(ix,iy)-fhiy_cond(topix(ix,iy),topiy(ix,iy));
        raddivi_32(ix,iy) = fhiy_32(ix,iy)-fhiy_32(topix(ix,iy),topiy(ix,iy));
        raddivi_dia(ix,iy) = fhiy_dia(ix,iy)-fhiy_dia(topix(ix,iy),topiy(ix,iy));
        raddivi_ecrb(ix,iy) = fhiy_ecrb(ix,iy)-fhiy_ecrb(topix(ix,iy),topiy(ix,iy));
        raddivi_inert(ix,iy) = fhiy_inert(ix,iy)-fhiy_inert(topix(ix,iy),topiy(ix,iy));
        raddivi_vispar(ix,iy) = fhiy_vispar(ix,iy)-fhiy_vispar(topix(ix,iy),topiy(ix,iy));
        raddivi_anml(ix,iy) = fhiy_anml(ix,iy)-fhiy_anml(topix(ix,iy),topiy(ix,iy));
        raddivi_vzh(ix,iy) = fhiy_vzh(ix,iy)-fhiy_vzh(topix(ix,iy),topiy(ix,iy));
    end
end

%% PRODUCE THE PLOTS

% Radial balance
rb = radial_balance(transport_mode,...
    cat(3,...
        fhix_cond,... % Heat conduction
        fhix_32,... % Heat convection
        fhix_dia+fhix_ecrb,... % Drift-related heat convection
        fhix_inert+fhix_vispar+fhix_anml,... % Current-related heat convection
        fhix_vzh)/1E6,... % Ion-velocity-related heat flux
    cat(3,...
        raddivi_cond+raddivi_32+raddivi_dia+raddivi_ecrb+raddivi_inert+raddivi_vispar+raddivi_anml+raddivi_vzh,... % Radial transport
        b2sihs_divua,... % Parallel ion velocity gradient heating
        b2sihs_visa,... % Viscosity heating
        b2stel_shi_ion+b2stel_shi_rec+b2stcx_shi,... % Atomic processes (B2)
        b2sihs_fraa,... % Friction heating
        b2sihs_diaa+b2sihs_exba,... % Drift heating
        b2npht_shei,... % e-i temperature equilibration
        sum(eirene_mc_eapl_shi,3)+sum(eirene_mc_empl_shi,3)+sum(eirene_mc_eipl_shi,3),... % Plasma-neutral collisions (EIRENE)
        sum(eirene_mc_eppl_shi,3),... % Recombinations (EIRENE)
        b2stbc_shi,... % Boundary source
        b2stbr_phys_shi+b2stbr_bas_shi+b2stbr_first_flight_shi,... % Recycling source
        b2stbm_shi+ext_shi+b2srsm_shi+b2srdt_shi+b2srst_shi)/1E6,... % Additional + numeric sources
    reshi/1E6,...
{'Total upstream ion energy flux',...
 'Total downstream ion energy flux',...
 'Total poloidally-integrated ion energy source',...
 'Poloidally-integrated residual'},...
{'Heat conduction',...
 'Heat convection',...
 'Drift-related heat convection',...
 'Current-related heat convection',...
 'Ion-velocity-related heat flux'},...
{'Radial transport',...
 'Parallel ion velocity gradient heating',...
 'Viscosity heating',...
 'Atomic processes (B2)',...
 'Friction heating',...
 'Drift heating',...
 'e-i temperature equilibration',...
 'Plasma-neutral collisions (EIRENE)',...
 'Recombinations (EIRENE)',...
 'Boundary source',...
 'Recycling source',...
 'Additional + numeric sources'},... 
 gmtry,indbal,false,axbal(1:4),units,default_region,reverse,areaend,areatype,radbaldist,residuals);

% Poloidal balance
pb = poloidal_balance(transport_mode,...
    cat(3,...
        fhix_cond,... % Heat conduction
        fhix_32,... % Heat convection
        fhix_dia+fhix_ecrb,... % Drift-related heat convection
        fhix_inert+fhix_vispar+fhix_anml,... % Current-related heat convection
        fhix_vzh)/1E6,... % Ion-velocity-related heat convection
    cat(3,...
        raddivi_cond+raddivi_32+raddivi_dia+raddivi_ecrb+raddivi_inert+raddivi_vispar+raddivi_anml+raddivi_vzh,... % Radial transport
        b2sihs_divua,... % Parallel ion velocity gradient heating
        b2sihs_visa,... % Viscosity heating
        b2stel_shi_ion+b2stel_shi_rec+b2stcx_shi,... % Atomic processes (B2)
        b2sihs_fraa,... % Friction heating
        b2sihs_diaa+b2sihs_exba,... % Drift heating
        b2npht_shei,... % e-i temperature equilibration
        sum(eirene_mc_eapl_shi,3)+sum(eirene_mc_empl_shi,3)+sum(eirene_mc_eipl_shi,3),... % Plasma-neutral collisions (EIRENE)
        sum(eirene_mc_eppl_shi,3),... % Recombinations (EIRENE)
        b2stbc_shi,... % Boundary source
        b2stbr_phys_shi+b2stbr_bas_shi+b2stbr_first_flight_shi,... % Recycling source
        b2stbm_shi+ext_shi+b2srsm_shi+b2srdt_shi+b2srst_shi)/1E6,... % Additional + numeric sources
    reshi/1E6,...
{'Total radially-integrated ion energy flux',...
 'Total radially-integrated ion energy source',...
 'Radially-integrated residual'},...
{'Heat conduction',...
 'Heat convection',...
 'Drift-related heat convection',...
 'Current-related heat convection',...
 'Ion-velocity-related heat flux'},...
{'Radial transport',...
 'Parallel ion velocity gradient heating',...
 'Viscosity heating',...
 'Atomic processes (B2)',...
 'Friction heating',...
 'Drift heating',...
 'e-i temperature equilibration',...
 'Plasma-neutral collisions (EIRENE)',...
 'Recombinations (EIRENE)',...
 'Boundary source',...
 'Recycling source',...
 'Additional + numeric sources'},... 
 gmtry,indbal,false,axbal(5:7),units,default_region,reverse,areaend,areatype,polbaldist,residuals);

% Strata decomposition
if strata_plot
    strata_plots(transport_mode,{eirene_mc_eapl_shi/1E6},{eirene_mc_empl_shi/1E6},{eirene_mc_eipl_shi/1E6},{eirene_mc_eppl_shi/1E6},...
                      {'Strata decomposition of the total poloidally-integrated EIRENE ion energy source',...
                       'Strata decomposition of the total radially-integrated EIRENE ion energy source'},...
                      {''},gmtry,indbal,nstra,axstrat,axbal,rb.Radial_coordinate_cell,pb.Poloidal_coordinate_cell,rb.area_divide_rad,pb.area_divide_pol,reverse,false);
end              

    case 'radial'
        [balfile,indbal,gmtry,axbal,axstrat,default_region,areaend,areatype,radbaldist,polbaldist,strata_plot,residuals] = deal(varargin{:});
%
% balance_ionen plots the ion energy balance                    
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

fprintf('Ion energy balance\n');

%% READ THE REQUIRED ARRAYS FROM THE BALANCE FILE

% Geometry variables
nx = gmtry.nx;
ny = gmtry.ny;
nstra = gmtry.nstra;
rightix = gmtry.rightix+1;
rightiy = gmtry.rightiy+1;

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

% Ion energy sources (fluid)
b2sihs_divua = ncread(balfile,'b2sihs_divua_bal'); % Parallel ion velocity gradient heating
b2sihs_visa = ncread(balfile,'b2sihs_visa_bal'); % Viscosity heating
b2stel_shi_ion = ncread(balfile,'b2stel_shi_ion_bal'); % Atomic processes
b2stel_shi_rec = ncread(balfile,'b2stel_shi_rec_bal');
b2stcx_shi = ncread(balfile,'b2stcx_shi_bal');
b2sihs_fraa = ncread(balfile,'b2sihs_fraa_bal'); % Friction heating
b2sihs_exba = ncread(balfile,'b2sihs_exba_bal'); % ExB drift heating
b2sihs_diaa = ncread(balfile,'b2sihs_diaa_bal'); % Diamagnetic drift heating
b2npht_shei = ncread(balfile,'b2npht_shei_bal'); % Electron-ion temperature equilibration

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
b2stbc_shi = ncread(balfile,'b2stbc_shi_bal');

% Recycling sources
b2stbr_phys_shi = ncread(balfile,'b2stbr_phys_shi_bal');
b2stbr_bas_shi = ncread(balfile,'b2stbr_bas_shi_bal');
b2stbr_first_flight_shi = ncread(balfile,'b2stbr_first_flight_shi_bal');

% Other sources
b2stbm_shi = ncread(balfile,'b2stbm_shi_bal');
ext_shi = ncread(balfile,'ext_shi_bal');
b2srsm_shi = ncread(balfile,'b2srsm_shi_bal');
b2srdt_shi = ncread(balfile,'b2srdt_shi_bal');
b2srst_shi = ncread(balfile,'b2srst_shi_bal');

% Residual
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

%% PRODUCE THE PLOTS

% Radial balance
rb = radial_balance(transport_mode,...
    cat(3,...
        fhiy_cond,... % Heat conduction
        fhiy_32,... % Heat convection
        fhiy_dia+fhiy_ecrb,... % Drift-related heat convection
        fhiy_inert+fhiy_vispar+fhiy_anml,... % Current-related heat convection
        fhiy_vzh)/1E6,... % Ion-velocity-related heat flux
    cat(3,...
        poldivi_cond+poldivi_32+poldivi_dia+poldivi_ecrb+poldivi_inert+poldivi_vispar+poldivi_anml+poldivi_vzh,... % Parallel losses
        b2sihs_divua,... % Parallel ion velocity gradient heating
        b2sihs_visa,... % Viscosity heating
        b2stel_shi_ion+b2stel_shi_rec+b2stcx_shi,... % Atomic processes (B2)
        b2sihs_fraa,... % Friction heating
        b2sihs_diaa+b2sihs_exba,... % Drift heating
        b2npht_shei,... % e-i temperature equilibration
        sum(eirene_mc_eapl_shi,3)+sum(eirene_mc_empl_shi,3)+sum(eirene_mc_eipl_shi,3),... % Plasma-neutral collisions (EIRENE)
        sum(eirene_mc_eppl_shi,3),... % Recombinations (EIRENE)
        b2stbc_shi,... % Boundary source
        b2stbr_phys_shi+b2stbr_bas_shi+b2stbr_first_flight_shi,... % Recycling source
        b2stbm_shi+ext_shi+b2srsm_shi+b2srdt_shi+b2srst_shi)/1E6,... % Additional + numeric sources
    reshi/1E6,...
{'Total poloidally-integrated ion energy flux',...
 'Total poloidally-integrated ion energy source',...
 'Poloidally-integrated residual'},...
{'Heat conduction',...
 'Heat convection',...
 'Drift-related heat convection',...
 'Current-related heat convection',...
 'Ion-velocity-related heat flux'},...
{'Parallel losses',...
 'Parallel ion velocity gradient heating',...
 'Viscosity heating',...
 'Atomic processes (B2)',...
 'Friction heating',...
 'Drift heating',...
 'e-i temperature equilibration',...
 'Plasma-neutral collisions (EIRENE)',...
 'Recombinations (EIRENE)',...
 'Boundary source',...
 'Recycling source',...
 'Additional + numeric sources'},... 
 gmtry,indbal,false,axbal(1:3),units,default_region,areaend,areatype,radbaldist,residuals);

% Poloidal balance
pb = poloidal_balance(transport_mode,...
    cat(3,...
        fhiy_cond,... % Heat conduction
        fhiy_32,... % Heat convection
        fhiy_dia+fhiy_ecrb,... % Drift-related heat convection
        fhiy_inert+fhiy_vispar+fhiy_anml,...%  Current-related heat convection
        fhiy_vzh)/1E6,... % Ion-velocity-related heat flux
    cat(3,...
        poldivi_cond+poldivi_32+poldivi_dia+poldivi_ecrb+poldivi_inert+poldivi_vispar+poldivi_anml+poldivi_vzh,... % Parallel losses
        b2sihs_divua,... % Parallel ion velocity gradient heating
        b2sihs_visa,... % Viscosity heating
        b2stel_shi_ion+b2stel_shi_rec+b2stcx_shi,... % Atomic processes (B2)
        b2sihs_fraa,... % Friction heating
        b2sihs_diaa+b2sihs_exba,... % Drift heating
        b2npht_shei,... % e-i temperature equilibration
        sum(eirene_mc_eapl_shi,3)+sum(eirene_mc_empl_shi,3)+sum(eirene_mc_eipl_shi,3),... % Plasma-neutral collisions (EIRENE)
        sum(eirene_mc_eppl_shi,3),... % Recombinations (EIRENE)
        b2stbc_shi,... % Boundary source
        b2stbr_phys_shi+b2stbr_bas_shi+b2stbr_first_flight_shi,... % Recycling source
        b2stbm_shi+ext_shi+b2srsm_shi+b2srdt_shi+b2srst_shi)/1E6,... % Additional + numeric sources
    reshi/1E6,...
{'Total separatrix ion energy flux',...
 'Total wall boundary ion energy flux',...
 'Total radially-integrated ion energy source',...
 'Radially-integrated residual'},...
{'Heat conduction',...
 'Heat convection',...
 'Drift-related heat convection',...
 'Current-related heat convection',...
 'Ion-velocity-related heat flux'},...
{'Parallel losses',...
 'Parallel ion velocity gradient heating',...
 'Viscosity heating',...
 'Atomic processes (B2)',...
 'Friction heating',...
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
    strata_plots(transport_mode,{eirene_mc_eapl_shi/1E6},{eirene_mc_empl_shi/1E6},{eirene_mc_eipl_shi/1E6},{eirene_mc_eppl_shi/1E6},...
                      {'Strata decomposition of the total poloidally-integrated EIRENE ion energy source',...
                       'Strata decomposition of the total radially-integrated EIRENE ion energy source'},...
                      {''},gmtry,indbal,nstra,axstrat,axbal,rb.Radial_coordinate_cell,pb.Poloidal_coordinate,rb.area_divide_rad,pb.area_divide_pol,false);
end              
    otherwise
        error('Error: Transport mode ''%s'' not supported.',transport_mode);
end
