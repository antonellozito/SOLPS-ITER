function [rb,pb] = balance_part(balfile,indbal,isplot,gmtry,axbal,axstrat,default_region,areaend,areatype,radbaldist,polbaldist,strata_plot,residuals)
%
% balance_part plots the particle balance, for a single species or summer over all the species                    
%                                                                                                              
% balfile:        Full path to balance.nc file    
% indbal:         Logical matrix of size nx*ny that is true for cells where the balances should be performed   
% isplot:         Species index to be plotted                                                                  
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

if length(isplot)>1
   fprintf('Particle balance over:  %s\n',sprintf('%s  ',gmtry.species{isplot}));   
else
   fprintf('Particle balance over: %s\n',gmtry.species{isplot});
end

%% READ THE REQUIRED ARRAYS FROM THE BALANCE FILE

% Geometry variables
nx = gmtry.nx;
ny = gmtry.ny;
nstra = gmtry.nstra;
rightix = gmtry.rightix+1;
rightiy = gmtry.rightiy+1;

% Particle fluxes

tmp = ncread(balfile,'fna_pll'); % Parallel convection
fnbx_pll = sum(tmp(:,:,1,isplot),4);
fnby_pll = sum(tmp(:,:,2,isplot),4);
tmp = ncread(balfile,'fna_drift'); % ExB drift
fnbx_drift = sum(tmp(:,:,1,isplot),4);
fnby_drift = sum(tmp(:,:,2,isplot),4);
tmp = ncread(balfile,'fna_pschused'); % Diamagnetic drift
fnbx_pschused = sum(tmp(:,:,1,isplot),4);
fnby_pschused = sum(tmp(:,:,2,isplot),4);
tmp = ncread(balfile,'fna_pinch'); % Anomalous pinch
fnbx_pinch = sum(tmp(:,:,1,isplot),4);
fnby_pinch = sum(tmp(:,:,2,isplot),4);
tmp = ncread(balfile,'fna_ch'); % Current-related flux
fnbx_ch = sum(tmp(:,:,1,isplot),4);
fnby_ch = sum(tmp(:,:,2,isplot),4);
tmp = ncread(balfile,'fna_nanom'); % Anomalous density diffusion
fnbx_nanom = sum(tmp(:,:,1,isplot),4);
fnby_nanom = sum(tmp(:,:,2,isplot),4);
tmp = ncread(balfile,'fna_panom'); % Anomalous pressure diffusion
fnbx_panom = sum(tmp(:,:,1,isplot),4);
fnby_panom = sum(tmp(:,:,2,isplot),4);

% Particle sources (fluid)
b2stel_sna_ion_bal = ncread(balfile,'b2stel_sna_ion_bal'); % Calc. ion. sink to next ion. state and ion. source from previous ion. state
izhigh = [find(diff(gmtry.za)<1)',gmtry.ns];
izlow = [1,izhigh(1:end-1)+1];
b2stel_sna_ion_prev = zeros(nx,ny,gmtry.ns);
b2stel_sna_ion_next = zeros(nx,ny,gmtry.ns);
for is1=1:length(izhigh)
    for is2=izhigh(is1):-1:izlow(is1)
        if is2==izhigh(is1)
            b2stel_sna_ion_next(:,:,is2) = 0;
            b2stel_sna_ion_prev(:,:,is2) = b2stel_sna_ion_bal(:,:,is2);
        else
            b2stel_sna_ion_next(:,:,is2) = -b2stel_sna_ion_prev(:,:,is2+1);
            b2stel_sna_ion_prev(:,:,is2) = b2stel_sna_ion_bal(:,:,is2)-b2stel_sna_ion_next(:,:,is2);
        end
    end
end
b2stel_sna_ion_prev = sum(b2stel_sna_ion_prev(:,:,isplot),3);
b2stel_sna_ion_next = sum(b2stel_sna_ion_next(:,:,isplot),3);
b2stel_sna_rec_bal = ncread(balfile,'b2stel_sna_rec_bal'); % Calc. rec. sink to previous ion. state and rec. source from next ion. state
b2stel_sna_rec_prev = zeros(nx,ny,gmtry.ns);
b2stel_sna_rec_next = zeros(nx,ny,gmtry.ns);
for is1=1:length(izhigh)
    for is2=izhigh(is1):-1:izlow(is1)
        if is2==izhigh(is1)
            b2stel_sna_rec_next(:,:,is2) = 0;
            b2stel_sna_rec_prev(:,:,is2) = b2stel_sna_rec_bal(:,:,is2);
        else
            b2stel_sna_rec_next(:,:,is2) = -b2stel_sna_rec_prev(:,:,is2+1);
            b2stel_sna_rec_prev(:,:,is2) = b2stel_sna_rec_bal(:,:,is2)-b2stel_sna_rec_next(:,:,is2);
        end
    end
end
b2stel_sna_rec_prev = sum(b2stel_sna_rec_prev(:,:,isplot),3);
b2stel_sna_rec_next = sum(b2stel_sna_rec_next(:,:,isplot),3);
tmp = ncread(balfile,'b2stcx_sna_bal'); % Charge-exchange source
b2stcx_sna = sum(tmp(:,:,isplot),3);

% Particle sources (EIRENE)
if (gmtry.b2mndr_eirene~=0)
    tmp = ncread(balfile,'eirene_mc_papl_sna_bal'); % Plasma-atom collisions
    eirene_mc_papl_sna = sum(tmp(:,:,isplot,:),3);
    tmp = ncread(balfile,'eirene_mc_pmpl_sna_bal'); % Plasma-molecule collisions
    eirene_mc_pmpl_sna = sum(tmp(:,:,isplot,:),3);
    tmp = ncread(balfile,'eirene_mc_pipl_sna_bal'); % Plasma-test ion collisions
    eirene_mc_pipl_sna = sum(tmp(:,:,isplot,:),3);
    tmp = ncread(balfile,'eirene_mc_pppl_sna_bal'); % Recombination
    eirene_mc_pppl_sna = sum(tmp(:,:,isplot,:),3);
else
    eirene_mc_papl_sna = zeros(nx,ny,1,nstra);
    eirene_mc_pmpl_sna = zeros(nx,ny,1,nstra);
    eirene_mc_pipl_sna = zeros(nx,ny,1,nstra);
    eirene_mc_pppl_sna = zeros(nx,ny,1,nstra);
end

% Boudary sources
tmp = ncread(balfile,'b2stbc_sna_bal');
b2stbc_sna = sum(tmp(:,:,isplot),3);

% Recycling sources
tmp = ncread(balfile,'b2stbr_phys_sna_bal');
b2stbr_phys_sna = sum(tmp(:,:,isplot),3);
tmp = ncread(balfile,'b2stbr_bas_sna_bal');
b2stbr_bas_sna = sum(tmp(:,:,isplot),3);
tmp = ncread(balfile,'b2stbr_first_flight_sna_bal');
b2stbr_first_flight_sna = sum(tmp(:,:,isplot),3);

% Other sources
tmp = ncread(balfile,'b2stbm_sna_bal');
b2stbm_sna = sum(tmp(:,:,isplot),3);
tmp = ncread(balfile,'ext_sna_bal');
ext_sna = sum(tmp(:,:,isplot),3);
tmp = ncread(balfile,'b2srsm_sna_bal');
b2srsm_sna = sum(tmp(:,:,isplot),3);
tmp = ncread(balfile,'b2srdt_sna_bal');
b2srdt_sna = sum(tmp(:,:,isplot),3);
tmp = ncread(balfile,'b2srst_sna_bal');
b2srst_sna = sum(tmp(:,:,isplot),3);

% Residual    
tmp = ncread(balfile,'resco');
rescb = sum(tmp(:,:,isplot),3);

%% CREATE THE UNITS STRINGS

switch areatype
    case 'contact'
        units = 'm^{-2}s^{-1}';
    case 'none'
        units = 's^{-1}';
    otherwise
        error('Error: Area type ''%s'' not supported.',areatype);
end

%% CALCULATE THE POLOIDAL DIVERGENCES

poldiv_pll = zeros(nx,ny);
poldiv_ExB = zeros(nx,ny);
poldiv_dia = zeros(nx,ny);
poldiv_pinch = zeros(nx,ny);
poldiv_ch = zeros(nx,ny);
poldiv_nanom = zeros(nx,ny);
poldiv_panom = zeros(nx,ny);

for ix=1:nx
    for iy=1:ny
        if rightix(ix,iy)>nx
            continue;
        end
        poldiv_pll(ix,iy) = fnbx_pll(ix,iy)-fnbx_pll(rightix(ix,iy),rightiy(ix,iy));
        poldiv_ExB(ix,iy) = fnbx_drift(ix,iy)-fnbx_drift(rightix(ix,iy),rightiy(ix,iy));
        poldiv_dia(ix,iy) = fnbx_pschused(ix,iy)-fnbx_pschused(rightix(ix,iy),rightiy(ix,iy));
        poldiv_pinch(ix,iy) = fnbx_pinch(ix,iy)-fnbx_pinch(rightix(ix,iy),rightiy(ix,iy));
        poldiv_ch(ix,iy) = fnbx_ch(ix,iy)-fnbx_ch(rightix(ix,iy),rightiy(ix,iy));
        poldiv_nanom(ix,iy) = fnbx_nanom(ix,iy)-fnbx_nanom(rightix(ix,iy),rightiy(ix,iy));
        poldiv_panom(ix,iy) = fnbx_panom(ix,iy)-fnbx_panom(rightix(ix,iy),rightiy(ix,iy));
    end
end

%% PRODUCE THE PLOTS

% Radial balance
rb = radial_balance(...
    cat(3,...
        fnby_pll,... % Parallel convection
        fnby_drift,... % ExB drift
        fnby_pschused,... % Diamagnetic drift
        fnby_pinch,... % Anomalous pinch
        fnby_ch,... % Current-related flux
        fnby_nanom,... % Anomalous density diffusion
        fnby_panom),... % Anomalous pressure diffusion
    cat(3,...
        poldiv_pll+poldiv_ExB+poldiv_dia+poldiv_ch+poldiv_pinch+poldiv_nanom+poldiv_panom,... % Parallel losses
        b2stel_sna_ion_prev+b2stel_sna_ion_next+b2stel_sna_rec_prev+b2stel_sna_rec_next+b2stcx_sna,... % Atomic processes (B2)
        sum(eirene_mc_papl_sna,4)+sum(eirene_mc_pmpl_sna,4)+sum(eirene_mc_pipl_sna,4),... % Plasma-neutral collisions (EIRENE)
        sum(eirene_mc_pppl_sna,4),... % Recombinations (EIRENE)
        b2stbc_sna,... % Boundary source
        b2stbr_phys_sna+b2stbr_bas_sna+b2stbr_first_flight_sna,... % Recycling source
        b2stbm_sna+ext_sna+b2srdt_sna+b2srsm_sna+b2srst_sna),... % Additional + numeric sources
    rescb,...
{'Total poloidally-integrated particle flux',...
 'Total poloidally-integrated particle source',...
 'Poloidally-integrated residual'},...
{'Parallel convection',...
 'ExB drift',...
 'Diamagnetic drift',...
 'Anomalous pinch',... 
 'Current-related flux',...
 'Anomalous density diffusion',...
 'Anomalous pressure diffusion'},...
{'Parallel losses',...
 'Atomic processes (B2)',...
 'Plasma-neutral collisions (EIRENE)',...
 'Recombinations (EIRENE)',...
 'Boundary source',...
 'Recycling source',...
 'Additional + numeric sources'},...
gmtry,indbal,false,axbal(1:3),units,default_region,areaend,areatype,radbaldist,residuals);

% Poloidal balance
pb = poloidal_balance(...
    cat(3,...
        fnby_pll,... % Parallel convection
        fnby_drift,... % ExB drift
        fnby_pschused,... % Diamagnetic drifts
        fnby_pinch,... % Anomalous pinch
        fnby_ch,... % Current-related flux
        fnby_nanom,... % Anomalous density diffusion
        fnby_panom),... % Anomalous pressure diffusion
	cat(3,...
        poldiv_pll+poldiv_ExB+poldiv_dia+poldiv_ch+poldiv_pinch+poldiv_nanom+poldiv_panom,... % Parallel losses
        b2stel_sna_ion_prev+b2stel_sna_ion_next+b2stel_sna_rec_prev+b2stel_sna_rec_next+b2stcx_sna,... % Atomic processes (B2)
        sum(eirene_mc_papl_sna,4)+sum(eirene_mc_pmpl_sna,4)+sum(eirene_mc_pipl_sna,4),... % Plasma-neutral collisions (EIRENE)
        sum(eirene_mc_pppl_sna,4),... % Recombinations (EIRENE)
        b2stbc_sna,... % Boundary source
        b2stbr_phys_sna+b2stbr_bas_sna+b2stbr_first_flight_sna,... % Recycling source
        b2stbm_sna+ext_sna+b2srdt_sna+b2srsm_sna+b2srst_sna),... % Additional + numeric sources
	rescb,...
{'Total separatrix particle flux',...
 'Total wall boundary particle flux',...
 'Total radially-integrated particle source',...
 'Radially-integrated residual'},...
{'Parallel convection',...
 'ExB drift',...
 'Diamagnetic drifts',...
 'Anomalous pinch',...
 'Current-related flux',...
 'Anomalous density diffusion',...
 'Anomalous pressure diffusion'},...
{'Parallel losses',...
 'Atomic processes (B2)',...
 'Plasma-neutral collisions (EIRENE)',...
 'Recombinations (EIRENE)',...
 'Boundary source',...
 'Recycling source',...
 'Additional + numeric sources'},...
gmtry,indbal,false,axbal(4:7),units,default_region,areaend,areatype,polbaldist,residuals);

% Strata decomposition
if strata_plot
    strata_plots({squeeze(eirene_mc_papl_sna)},{squeeze(eirene_mc_pmpl_sna)},{squeeze(eirene_mc_pipl_sna)},{squeeze(eirene_mc_pppl_sna)},...
                      {'Strata decomposition of the total poloidally-integrated EIRENE particle source',...
                       'Strata decomposition of the total radially-integrated EIRENE particle source'},...
                      {''},gmtry,indbal,nstra,axstrat,axbal,rb.Radial_coordinate_cell,pb.Poloidal_coordinate,rb.area_divide_rad,pb.area_divide_pol,false);
end              

end