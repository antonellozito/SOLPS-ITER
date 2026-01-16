function sources = distribution_sources_totpress(balfile,indbal,gmtry,reverse,default_region,areatype,radbaldist,index_start,index_end)
%
% balance_totpress plots the total pressure balance, summer over all the species                    
%                                                                                                              
% balfile:        Full path to balance.nc file                                                                 
% indbal:         Logical matrix of size nx*ny that is true for cells where the balances should be performed   
% gmtry:          Structure containing commonly-used variables
% reverse:        True if the right-most end of the balance volume is upstream of the left-most end, otherwise false
% default_region: Definition of the region which the balance is performed
% radbaldist:     Defines the distance used on the x-axis of the radial balance plots   
%

%% READ THE REQUIRED ARRAYS FROM THE BALANCE FILE

% Geometry variables
nx = gmtry.nx;
ny = gmtry.ny;
nstra = gmtry.nstra;
topix = gmtry.topix+1;
topiy = gmtry.topiy+1;
leftix = gmtry.leftix+1;
leftiy = gmtry.leftiy+1;
rightix = gmtry.rightix+1;
rightiy = gmtry.rightiy+1;
za = gmtry.za;
dv = gmtry.dv;
hx = gmtry.hx;
gs = gmtry.gs;
B = gmtry.bb;

% Momentum fluxes
tmp = ncread(balfile,'fmo_flua'); % Convected flux
fmox_flua = sum(tmp(:,:,1,za>0),4);
fmoy_flua = sum(tmp(:,:,2,za>0),4);
tmp = ncread(balfile,'fmo_cvsa'); % Viscous flux
fmox_cvsa = sum(tmp(:,:,1,za>0),4);
fmoy_cvsa = sum(tmp(:,:,2,za>0),4);
tmp = ncread(balfile,'fmo_hybr'); % Viscous flux, hybrid
fmox_hybr = sum(tmp(:,:,1,za>0),4);
fmoy_hybr = sum(tmp(:,:,2,za>0),4);

% Static pressure gradient
tmp = ncread(balfile,'b2sigp_smogpi_bal');
b2sigp_smogpi = sum(tmp(:,:,za>0),3);
tmp = ncread(balfile,'b2sigp_smogpe_bal');
b2sigp_smogpe = sum(tmp(:,:,za>0),3);
tmp = ncread(balfile,'b2sigp_smogpgr_bal');
b2sigp_smogpgr = sum(tmp(:,:,za>0),3);

% Momentum sources (fluid)
tmp = ncread(balfile,'b2stel_smq_ion_bal'); % Ionization source
b2stel_smq_ion = sum(tmp(:,:,za>0),3);
tmp = ncread(balfile,'b2stel_smq_rec_bal'); % Recombination source
b2stel_smq_rec = sum(tmp(:,:,za>0),3);
tmp = ncread(balfile,'b2stcx_smq_bal'); % Charge-exchange source
b2stcx_smq = sum(tmp(:,:,za>0),3);
% if b2sigp_style=='1'
    tmp = ncread(balfile,'b2sifr_smoch_bal'); % Friction force
    b2sifr_smoch = sum(tmp(:,:,za>0),3);
    tmp = ncread(balfile,'b2sifr_smotf_ehxp_bal'); % E-hat thermal force
    b2sifr_smotf_ehxb = sum(tmp(:,:,za>0),3);
    tmp = ncread(balfile,'b2sifr_smotf_cthe_bal'); % Electron thermal force
    b2sifr_smotf_cthe = sum(tmp(:,:,za>0),3);
    tmp = ncread(balfile,'b2sifr_smotf_cthi_bal'); % Ion thermal force
    b2sifr_smotf_cthi = sum(tmp(:,:,za>0),3);
% if b2sigp_style=='2'
    tmp = ncread(balfile,'b2sifr_smofrea_bal'); % Electron-ion friction force
    b2sifr_smofrea = sum(tmp(:,:,za>0),3);
    tmp = ncread(balfile,'b2sifr_smofria_bal'); % Ion-ion friction force
    b2sifr_smofria = sum(tmp(:,:,za>0),3);
    tmp = ncread(balfile,'b2sifr_smotfea_bal'); % Electron thermal force
    b2sifr_smotfea = sum(tmp(:,:,za>0),3);
    tmp = ncread(balfile,'b2sifr_smotfia_bal'); % Ion thermal force
    b2sifr_smotfia = sum(tmp(:,:,za>0),3);
tmp = ncread(balfile,'b2siav_smovh_bal'); % Additional viscosity
b2siav_smovh = sum(tmp(:,:,za>0),3);
tmp = ncread(balfile,'b2siav_smovv_bal'); % Additional viscosity
b2siav_smovv = sum(tmp(:,:,za>0),3);    
tmp = ncread(balfile,'b2sicf_smo_bal'); % Centrifugal force
b2sicf_smo = sum(tmp(:,:,za>0),3);
tmp = ncread(balfile,'b2sian_smo_bal'); % Source due to the anomalous current
b2sian_smo = sum(tmp(:,:,za>0),3);
tmp = ncread(balfile,'b2nxdv_smo_bal'); % Correction term
b2nxdv_smo = sum(tmp(:,:,za>0),3);    
    
% Momentum sources (EIRENE)    
if (gmtry.b2mndr_eirene~=0)
    tmp = ncread(balfile,'eirene_mc_mapl_smo_bal'); % Plasma-acom collisions
    eirene_mc_mapl_smo = sum(tmp(:,:,za>0,:),3);
    tmp = ncread(balfile,'eirene_mc_mmpl_smo_bal'); % Plasma-molecule collisions
    eirene_mc_mmpl_smo = sum(tmp(:,:,za>0,:),3);
    tmp = ncread(balfile,'eirene_mc_mipl_smo_bal'); % Plasma-test ion collisions
    eirene_mc_mipl_smo = sum(tmp(:,:,za>0,:),3);
    try
        tmp = ncread(balfile,'eirene_mc_cppv_smo_bal'); % Recombination
    catch
        tmp = ncread(balfile,'eirene_mc_mppl_smo_bal'); % Recombination
    end
    eirene_mc_cppv_smo = sum(tmp(:,:,za>0,:),3);
else
    eirene_mc_mapl_smo = zeros(nx,ny,1,nstra);
    eirene_mc_mmpl_smo = zeros(nx,ny,1,nstra);
    eirene_mc_mipl_smo = zeros(nx,ny,1,nstra);
    eirene_mc_cppv_smo = zeros(nx,ny,1,nstra);
end

% Boundary sources
tmp = ncread(balfile,'b2stbc_smo_bal');
b2stbc_smo = sum(tmp(:,:,za>0),3);

% Recycling sources
tmp = ncread(balfile,'b2stbr_phys_smo_bal');
b2stbr_phys_smo = sum(tmp(:,:,za>0),3);
tmp = ncread(balfile,'b2stbr_bas_smo_bal');
b2stbr_bas_smo = sum(tmp(:,:,za>0),3);

% Other sources
tmp = ncread(balfile,'b2stbm_smo_bal');
b2stbm_smo = sum(tmp(:,:,za>0),3);
tmp = ncread(balfile,'ext_smo_bal');
ext_smo = sum(tmp(:,:,za>0),3);
tmp = ncread(balfile,'b2srsm_smo_bal');
b2srsm_smo = sum(tmp(:,:,za>0),3);
tmp = ncread(balfile,'b2srdt_smo_bal');
b2srdt_smo = sum(tmp(:,:,za>0),3);
tmp = ncread(balfile,'b2srst_smo_bal');
b2srst_smo = sum(tmp(:,:,za>0),3);

% Residual
tmp = ncread(balfile,'resmo');
resmo = sum(tmp(:,:,za>0),3);

%% CALCULATE THE PARALLEL AREA AT THE CELL CENTRES

% Parallel area
hz = (1-gmtry.b2mndr_hz)+gmtry.b2mndr_hz*(dv./gs(:,:,3));
apll = dv.*hz./hx.*abs(B(:,:,1)./B(:,:,4));

% Map to left cell face
apllx = zeros(nx,ny);
for iy=1:ny
    for ix=1:nx
        if leftix(ix,iy)<1
            continue;
        end
        apllx(ix,iy) = (apll(leftix(ix,iy),leftiy(ix,iy))*dv(ix,iy)+...
                        apll(ix,iy)*dv(leftix(ix,iy),leftiy(ix,iy)))/...
                       (dv(ix,iy)+dv(leftix(ix,iy),leftiy(ix,iy)));
    end
end

% Mat to the cell centre
apllc = zeros(nx,ny);
for iy=1:ny
    for ix=1:nx
        if rightix(ix,iy)>nx
            continue;
        end
        apllc(ix,iy) = 0.5*(apllx(ix,iy)+apllx(rightix(ix,iy),rightiy(ix,iy)));
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

%% CALCULATE THE POLOIDAL DIVERGENCES

poldiv_visc = zeros(nx,ny);
poldiv_hybr = zeros(nx,ny);
for iy=1:ny
    for ix=1:nx
        if rightix(ix,iy)>nx
            continue;
        end
        poldiv_visc(ix,iy) = fmox_cvsa(ix,iy)-fmox_cvsa(rightix(ix,iy),rightiy(ix,iy));
        poldiv_hybr(ix,iy) = fmox_hybr(ix,iy)-fmox_hybr(rightix(ix,iy),rightiy(ix,iy));
    end
end

%% CALCULATE THE GEOMETRIC TERM

geomterm = zeros(nx,ny);
for iy=1:ny
    for ix=1:nx
        if rightix(ix,iy)>nx
            continue;
        end
        geomterm(ix,iy) = 0.5*(fmox_flua(ix,iy)/apllx(ix,iy)+...
                                fmox_flua(rightix(ix,iy),rightiy(ix,iy))/apllx(rightix(ix,iy),rightiy(ix,iy)))*...
                           (apllx(ix,iy)-apllx(rightix(ix,iy),rightiy(ix,iy)));
    end
end

%% CALCULATE THE STATIC PRESSURE ON THE POLOIDAL CELL FACES

ne = ncread(balfile,'ne');
te = ncread(balfile,'te');
na = ncread(balfile,'na');
ti = ncread(balfile,'ti');
pe = ne.*te;
pi = ti.*sum(na(:,:,za>0),3);
pex = zeros(nx,ny);
pex(end,:) = -pe(end,:);
pix = zeros(nx,ny);
pix(end,:) = -pi(end,:);
for iy=1:ny
    ix = nx-1;
    while true
        pex(ix,iy) = pex(rightix(ix,iy),rightiy(ix,iy))+b2sigp_smogpe(ix,iy)/apllc(ix,iy);
        pix(ix,iy) = pix(rightix(ix,iy),rightiy(ix,iy))+b2sigp_smogpi(ix,iy)/apllc(ix,iy);
        ix = leftix(ix,iy);
        if ix<1
            break;
        end
    end
end

%% PRODUCE THE PLOTS

j = 1;
for i = index_start-1:index_end-1
    indbal = zeros(size(indbal,1),size(indbal,2));
    indbal(i,gmtry.sep+2:gmtry.ny-1) = 1;
    indbal(i+1,gmtry.sep+2:gmtry.ny-1) = 1;
    sources{j} = radial_flux_distribution(...
        cat(3,...
        fmox_flua./apllx,... % Dynamic pressure
        pex+pix),... % Static pressure
    	cat(3,...
        poldiv_visc./apllc+poldiv_hybr./apllc,... % Poloidal viscosity
        raddiv_visc./apllc+raddiv_hybr./apllc,... % Radial viscosity
        raddiv_flua./apllc,... % Radial transport
        geomterm./apllc,... % Flux expansion effect
        b2stel_smq_ion./apllc+b2stel_smq_rec./apllc+b2stcx_smq./apllc,...% Atomic processes (B2)
        b2sifr_smoch./apllc,... % Friction force (b2sigp_style=='1')
        b2sifr_smotf_ehxb./apllc+b2sifr_smotf_cthe./apllc+b2sifr_smotf_cthi./apllc,... % Thermal forces (b2sigp_style=='1')
        b2sifr_smofrea./apllc+b2sifr_smofria./apllc,... % Friction force (b2sigp_style=='2')
        b2sifr_smotfea./apllc+b2sifr_smotfia./apllc,... % Thermal forces (b2sigp_style=='2')
        b2siav_smovh./apllc+b2siav_smovv./apllc,... % Additional viscosity
        b2sicf_smo./apllc+b2sian_smo./apllc+b2nxdv_smo./apllc,... % Other sources
        sum(eirene_mc_mapl_smo,4)./apllc+sum(eirene_mc_mmpl_smo,4)./apllc+sum(eirene_mc_mipl_smo,4)./apllc,... % Plasma-neutral collisions (EIRENE)
        sum(eirene_mc_cppv_smo,4)./apllc,... % Recombinations (EIRENE)
        b2stbc_smo./apllc,... % Boundary source
        b2stbr_phys_smo./apllc+b2stbr_bas_smo./apllc,... % Recycling source
        b2sigp_smogpgr./apllc+b2stbm_smo./apllc+ext_smo./apllc+b2srsm_smo./apllc+b2srdt_smo./apllc+b2srst_smo./apllc),... % Additional + numeric sources
        resmo./apllc,...
        {'Total upstream pressure',...
        'Total downstream prassure',...
        'Total poloidally-integrated pressure source',...
        'Poloidally-integrated residual'},...
        {'Dynamic pressure',...
        'Static pressure'},...
        {'Poloidal viscosity',...
        'Radial viscosity',...
        'Radial transport',...
        'Flux expansion effect',...
        'Atomic processes (B2)',...
        'Friction force',...
        'Thermal forces',...
        'Friction force',...
        'Thermal forces',...
        'Additional viscosity',...
        'Other sources',...
        'Plasma-neutral collisions (EIRENE)',...
        'Recombinations (EIRENE)',...
        'Boundary source',...
        'Recycling source',...
        'Additional + numeric sources'},...
        gmtry,indbal,true,'Nm^{-2}',default_region,reverse,'right',areatype,radbaldist);
    j = j+1;
end

end