function [rb,pb] = balance_force(balfile,indbal,isplot,gmtry,reverse,axbal,axstrat,default_region,areaend,areatype,radbaldist,polbaldist,strata_plot,residuals)
%
% balance_force plots the force balance, for a single species or summer over all the species                    
%                                                                                                              
% balfile:        Full path to balance.nc file                                                                 
% indbal:         Logical matrix of size nx*ny that is true for cells where the balances should be performed   
% isplot:         Species index to be plotted                                                                  
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

if length(isplot)>1
   fprintf('Force balance over:  %s\n',sprintf('%s  ',gmtry.species{isplot}));   
else
   fprintf('Force balance over: %s\n',gmtry.species{isplot});
end

%% READ THE REQUIRED ARRAYS FROM THE BALANCE FILE

% Geometry variables
nx = gmtry.nx;
ny = gmtry.ny;
nstra = gmtry.nstra;
topix = gmtry.topix+1;
topiy = gmtry.topiy+1;
rightix = gmtry.rightix+1;
rightiy = gmtry.rightiy+1;

% Species density
tmp = ncread(balfile,'na'); % Ion density
na = sum(tmp(:,:,isplot),3);

% Momentum fluxes
tmp = ncread(balfile,'fmo_flua'); % Convected flux
fmox_flua = sum(tmp(:,:,1,isplot),4);
fmoy_flua = sum(tmp(:,:,2,isplot),4);
tmp = ncread(balfile,'fmo_cvsa'); % Viscous flux
fmox_cvsa = sum(tmp(:,:,1,isplot),4);
fmoy_cvsa = sum(tmp(:,:,2,isplot),4);
tmp = ncread(balfile,'fmo_hybr'); % Viscous flux, hybrid
fmox_hybr = sum(tmp(:,:,1,isplot),4);
fmoy_hybr = sum(tmp(:,:,2,isplot),4);

% Static pressure gradient
tmp = ncread(balfile,'b2sigp_smogpe_bal'); % Static electron pressure gradient
b2sigp_smogpe = sum(tmp(:,:,isplot),3);
tmp = ncread(balfile,'b2sigp_smogpi_bal'); % Static ion pressure gradient
b2sigp_smogpi = sum(tmp(:,:,isplot),3);
tmp = ncread(balfile,'b2sigp_smogpgr_bal'); % Restriction term
b2sigp_smogpgr = sum(tmp(:,:,isplot),3);

% Momentum sources (fluid)
tmp = ncread(balfile,'b2stel_smq_ion_bal'); % Ionization source
b2stel_smq_ion = sum(tmp(:,:,isplot),3);
tmp = ncread(balfile,'b2stel_smq_rec_bal'); % Recombination source
b2stel_smq_rec = sum(tmp(:,:,isplot),3);
tmp = ncread(balfile,'b2stcx_smq_bal'); % Charge-exchange source
b2stcx_smq = sum(tmp(:,:,isplot),3);
% if b2sigp_style=='1'
    tmp = ncread(balfile,'b2sifr_smoch_bal'); % Friction force
    b2sifr_smoch = sum(tmp(:,:,isplot),3);
    tmp = ncread(balfile,'b2sifr_smotf_ehxp_bal'); % E-hat thermal force
    b2sifr_smotf_ehxb = sum(tmp(:,:,isplot),3);
    tmp = ncread(balfile,'b2sifr_smotf_cthe_bal'); % Electron thermal force
    b2sifr_smotf_cthe = sum(tmp(:,:,isplot),3);
    tmp = ncread(balfile,'b2sifr_smotf_cthi_bal'); % Ion thermal source
    b2sifr_smotf_cthi = sum(tmp(:,:,isplot),3);
% if b2sigp_style=='2'
    tmp = ncread(balfile,'b2sifr_smofrea_bal'); % Electron-ion friction force
    b2sifr_smofrea = sum(tmp(:,:,isplot),3);
    tmp = ncread(balfile,'b2sifr_smofria_bal'); % Ion-ion friction force
    b2sifr_smofria = sum(tmp(:,:,isplot),3);
    tmp = ncread(balfile,'b2sifr_smotfea_bal'); % Electron thermal force
    b2sifr_smotfea = sum(tmp(:,:,isplot),3);
    tmp = ncread(balfile,'b2sifr_smotfia_bal'); % Ion thermal force
    b2sifr_smotfia = sum(tmp(:,:,isplot),3);
tmp = ncread(balfile,'b2siav_smovh_bal'); % Additional viscosity
b2siav_smovh = sum(tmp(:,:,isplot),3);
tmp = ncread(balfile,'b2siav_smovv_bal'); % Additional viscosity
b2siav_smovv = sum(tmp(:,:,isplot),3);
tmp = ncread(balfile,'b2sicf_smo_bal'); % Centrifugal force
b2sicf_smo = sum(tmp(:,:,isplot),3);
tmp = ncread(balfile,'b2sian_smo_bal'); % Source due to anomalous current
b2sian_smo = sum(tmp(:,:,isplot),3);
tmp = ncread(balfile,'b2nxdv_smo_bal'); % Correction term
b2nxdv_smo = sum(tmp(:,:,isplot),3);

% Momentum sources (EIRENE)
if (gmtry.b2mndr_eirene~=0)
    tmp = ncread(balfile,'eirene_mc_mapl_smo_bal'); % Plasma-atom collisions
    eirene_mc_mapl_smo = sum(tmp(:,:,isplot,:),3);
    tmp = ncread(balfile,'eirene_mc_mmpl_smo_bal'); % Plasma-molecule collisions
    eirene_mc_mmpl_smo = sum(tmp(:,:,isplot,:),3);
    tmp = ncread(balfile,'eirene_mc_mipl_smo_bal'); % Plasma-test ion collisions
    eirene_mc_mipl_smo = sum(tmp(:,:,isplot,:),3);
    try
        tmp = ncread(balfile,'eirene_mc_cppv_smo_bal'); % Recombination
    catch
        tmp = ncread(balfile,'eirene_mc_mppl_smo_bal'); % Recombination
    end
    eirene_mc_cppv_smo = sum(tmp(:,:,isplot,:),3);
else
    eirene_mc_mapl_smo = zeros(nx,ny,1,nstra);
    eirene_mc_mmpl_smo = zeros(nx,ny,1,nstra);
    eirene_mc_mipl_smo = zeros(nx,ny,1,nstra);
    eirene_mc_cppv_smo = zeros(nx,ny,1,nstra);
end

% Boundary sources
tmp = ncread(balfile,'b2stbc_smo_bal');
b2stbc_smo = sum(tmp(:,:,isplot),3);

% Recycling sources
tmp = ncread(balfile,'b2stbr_phys_smo_bal');
b2stbr_phys_smo = sum(tmp(:,:,isplot),3);
tmp = ncread(balfile,'b2stbr_bas_smo_bal');
b2stbr_bas_smo = sum(tmp(:,:,isplot),3);

% Other sources
tmp = ncread(balfile,'b2stbm_smo_bal');
b2stbm_smo = sum(tmp(:,:,isplot),3);
tmp = ncread(balfile,'ext_smo_bal');
ext_smo = sum(tmp(:,:,isplot),3);
tmp = ncread(balfile,'b2srsm_smo_bal');
b2srsm_smo = sum(tmp(:,:,isplot),3);
tmp = ncread(balfile,'b2srdt_smo_bal');
b2srdt_smo = sum(tmp(:,:,isplot),3);
tmp = ncread(balfile,'b2srst_smo_bal');
b2srst_smo = sum(tmp(:,:,isplot),3);

% Residual
tmp = ncread(balfile,'resmo');
resmo = sum(tmp(:,:,isplot),3);

%% CREATE THE UNITS STRINGS

units = 'N / ion';

%% CALCULATE THE POLOIDAL DIVERGENCES

poldiv_visc = zeros(nx,ny);
poldiv_hybr = zeros(nx,ny);

for ix=1:nx
    for iy=1:ny
        if rightix(ix,iy)>nx
            continue;
        end
        poldiv_visc(ix,iy) = fmox_cvsa(ix,iy)-fmox_cvsa(rightix(ix,iy),rightiy(ix,iy));
        poldiv_hybr(ix,iy) = fmox_hybr(ix,iy)-fmox_hybr(rightix(ix,iy),rightiy(ix,iy));
    end
end

%% CALCULATE THE RADIAL DIVERGENCES

raddiv_flua = zeros(nx,ny);
raddiv_visc = zeros(nx,ny);
raddiv_hybr = zeros(nx,ny);

for iy=1:ny
    for ix=1:nx
        if topiy(ix,iy)>ny
            continue;
        end
        raddiv_flua(ix,iy) = fmoy_flua(ix,iy)-fmoy_flua(topix(ix,iy),topiy(ix,iy));
        raddiv_visc(ix,iy) = fmoy_cvsa(ix,iy)-fmoy_cvsa(topix(ix,iy),topiy(ix,iy));
        raddiv_hybr(ix,iy) = fmoy_hybr(ix,iy)-fmoy_hybr(topix(ix,iy),topiy(ix,iy));
    end
end

%% PRODUCE THE PLOTS

% Radial balance
rb = radial_balance(...
    cat(3,...
        fmox_flua),... % Convected momentum flux
    cat(3,...
        poldiv_visc+poldiv_hybr,... % Poloidal viscosity
        raddiv_visc+raddiv_hybr,... % Radial viscosity
        raddiv_flua,... % Radial transport
        b2sigp_smogpi+b2sigp_smogpgr,... % Static ion pressure gradient
        b2sigp_smogpe,... % Static electron pressure gradient (b2sigp_style=='1') or electrostatic force (b2sigp_style=='2')
        b2sifr_smotf_ehxb, ... % Electrostatic force (b2sigp_style=='2')
        b2stel_smq_ion+b2stel_smq_rec+b2stcx_smq,... % Atomic processes (B2)
        b2sifr_smoch,... % Friction forces (b2sigp_style=='1')
        b2sifr_smofrea+b2sifr_smofria,... % Friction forces (b2sigp_style=='2')
        b2sifr_smotf_cthe,... % Electron thermal force (b2sigp_style=='1')
        b2sifr_smotf_cthi,... % Ion thermal force (b2sigp_style=='1')
        b2sifr_smotfea,... % Electron thermal force (b2sigp_style=='2')
        b2sifr_smotfia,... % Ion thermal force (b2sigp_style=='2')
        b2siav_smovh+b2siav_smovv,... % Additional viscosity
        b2sicf_smo+b2sian_smo+b2nxdv_smo,... % Other sources
        sum(eirene_mc_mapl_smo,4)+sum(eirene_mc_mmpl_smo,4)+sum(eirene_mc_mipl_smo,4),... % Plasma-neutral collisions (EIRENE)
        sum(eirene_mc_cppv_smo,4),... % Recombinations (EIRENE)
        b2stbc_smo,... % Boundary source
        b2stbr_phys_smo+b2stbr_bas_smo,... % Recycling source
        b2stbm_smo+ext_smo+b2srdt_smo+b2srsm_smo+b2srst_smo),... % Additional + numeric sources
    resmo,...
{'Total upstream convected momentum flux',...
 'Total downstream convected momentum flux',...
 'Total poloidally-integrated force',...
 'Poloidally-integrated residual'},...
{'Convected momentum flux'},...
{'Poloidal viscosity',...
 'Radial viscosity',...
 'Radial transport',...
 'Static ion pressure gradient',...
 'Electrostatic force',...
 'Electrostatic force',...
 'Atomic processes (B2)',...
 'Friction forces',...
 'Friction forces',...
 'Electron thermal force',...
 'Ion thermal force',...
 'Electron thermal force',...
 'Ion thermal force',...
 'Additional viscosity',...
 'Other sources',...
 'Plasma-neutral collisions (EIRENE)',...
 'Recombinations (EIRENE)',...
 'Boundary source',...
 'Recycling source',...
 'Additional + numeric sources'},...
 gmtry,indbal,true,axbal(1:4),units,default_region,reverse,areaend,areatype,radbaldist,residuals);

% Poloidal balance
pb = poloidal_balance(...
    cat(3,...
        fmox_flua),... % Convected momentum flux
    cat(3,...
        poldiv_visc+poldiv_hybr,... % Poloidal viscosity
        raddiv_visc+raddiv_hybr,... % Radial viscosity
        raddiv_flua,... % Radial transport
        b2sigp_smogpi+b2sigp_smogpgr,... % Static ion pressure gradient
        b2sigp_smogpe,... % Static electron pressure gradient (b2sigp_style=='1') or electrostatic force (b2sigp_style=='2')
        b2sifr_smotf_ehxb, ... % Electrostatic force (b2sigp_style=='2')
        b2stel_smq_ion+b2stel_smq_rec+b2stcx_smq,... % Atomic processes (B2)
        b2sifr_smoch,... % Friction forces (b2sigp_style=='1')
        b2sifr_smofrea+b2sifr_smofria,... % Friction forces (b2sigp_style=='2')
        b2sifr_smotf_cthe,... % Electron thermal force (b2sigp_style=='1')
        b2sifr_smotf_cthi,... % Ion thermal force (b2sigp_style=='1')
        b2sifr_smotfea,... % Electron thermal force (b2sigp_style=='2')
        b2sifr_smotfia,... % Ion thermal force (b2sigp_style=='2')
        b2siav_smovh+b2siav_smovv,... % Additional viscosity
        b2sicf_smo+b2sian_smo+b2nxdv_smo,... % Other sources
        sum(eirene_mc_mapl_smo,4)+sum(eirene_mc_mmpl_smo,4)+sum(eirene_mc_mipl_smo,4),... % Plasma-neutral collisions (EIRENE)
        sum(eirene_mc_cppv_smo,4),... % Recombinations (EIRENE)
        b2stbc_smo,... % Boundary source
        b2stbr_phys_smo+b2stbr_bas_smo,... % Recycling source
        b2stbm_smo+ext_smo+b2srdt_smo+b2srsm_smo+b2srst_smo),... % Additional + numeric sources
    resmo,...
{'Total radially-integrated convected momentum flux',...
 'Total radially-integrated force',...
 'Radially-integrated residual'},...
{'Convected momentum flux'},...
{'Poloidal viscosity',...
 'Radial viscosity',...
 'Radial transport',...
 'Static ion pressure gradient',...
 'Electrostatic force',...
 'Electrostatic force',...
 'Atomic processes (B2)',...
 'Friction forces',...
 'Friction forces',...
 'Electron thermal force',...
 'Ion thermal force',...
 'Electron thermal force',...
 'Ion thermal force',...
 'Additional viscosity',...
 'Other sources',...
 'Plasma-neutral collisions (EIRENE)',...
 'Recombinations (EIRENE)',...
 'Boundary source',...
 'Recycling source',...
 'Additional + numeric sources'},...
 gmtry,indbal,true,axbal(5:7),units,default_region,reverse,areaend,areatype,polbaldist,residuals);

% Strata decomposition
if strata_plot
    strata_plots({squeeze(eirene_mc_mapl_smo)},{squeeze(eirene_mc_mmpl_smo)},{squeeze(eirene_mc_mipl_smo)},{squeeze(eirene_mc_cppv_smo)},...
                      {'Strata decomposition of the total poloidally-integrated EIRENE momentum source',...
                       'Strata decomposition of the total radially-integrated EIRENE momentum source'},...
                      {''},gmtry,indbal,nstra,axstrat,axbal,rb.Radial_coordinate_cell,pb.Poloidal_coordinate_cell,rb.area_divide_rad,pb.area_divide_pol,reverse,true);
end    

end