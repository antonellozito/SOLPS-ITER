function sources = distribution_sources_part(balfile,indbal,isplot,gmtry,reverse,default_region,areaend,areatype,radbaldist,index_start,index_end)
%
% balance_part plots the particle balance, for a single species or summer over all the species                    
%
% balfile:        Full path to balance.nc file
% indbal:         Logical matrix of size nx*ny that is true for cells where the balances should be performed   
% gmtry:          Structure containing commonly-used variables
% reverse:        True if the right-most end of the balance volume is upstream of the left-most end, otherwise false
% default_region: Definition of the region which the balance is performed                                      
% areaend:        Defines the radial end of the balance region at which areas will be calculated               
% areatype:       The type of area that poloidal fluxes are divided by           
% radbaldist:     Defines the distance used on the x-axis of the radial balance plots   
%

%% READ THE REQUIRED ARRAYS FROM THE BALANCE FILE

% Geometry variables
nx = gmtry.nx;
ny = gmtry.ny;
nstra = gmtry.nstra;
topix = gmtry.topix+1;
topiy = gmtry.topiy+1;

% Particle fluxes

tmp = ncread(balfile,'fna_pll'); % Parallel convection
fnbx_pll = sum(tmp(:,:,1,isplot),4);
fnby_pll = sum(tmp(:,:,2,isplot),4);
tmp = ncread(balfile,'fna_drift'); % ExB + diamagnetic drifts
fnbx_drift = sum(tmp(:,:,1,isplot),4);
fnby_drift = sum(tmp(:,:,2,isplot),4);
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
    case 'parallel'        
        units = 'm^{-2}s^{-1}';
    case 'contact'
        units = 'm^{-2}s^{-1}';
    case 'none'
        units = 's^{-1}';
    otherwise
        error('Error: Area type ''%s'' not supported.',areatype);
end

%% CALCULATE THE RADIAL DIVERGENCES

raddiv_pll = zeros(nx,ny);
raddiv_drift = zeros(nx,ny);
raddiv_pinch = zeros(nx,ny);
raddiv_ch = zeros(nx,ny);
raddiv_nanom = zeros(nx,ny);
raddiv_panom = zeros(nx,ny);

for iy=1:ny
    for ix=1:nx
        if topiy(ix,iy)>ny
            continue;
        end
        raddiv_pll(ix,iy) = fnby_pll(ix,iy)-fnby_pll(topix(ix,iy),topiy(ix,iy));
        raddiv_drift(ix,iy) = fnby_drift(ix,iy)-fnby_drift(topix(ix,iy),topiy(ix,iy));
        raddiv_pinch(ix,iy) = fnby_pinch(ix,iy)-fnby_pinch(topix(ix,iy),topiy(ix,iy));
        raddiv_ch(ix,iy) = fnby_ch(ix,iy)-fnby_ch(topix(ix,iy),topiy(ix,iy));        
        raddiv_nanom(ix,iy) = fnby_nanom(ix,iy)-fnby_nanom(topix(ix,iy),topiy(ix,iy));
        raddiv_panom(ix,iy) = fnby_panom(ix,iy)-fnby_panom(topix(ix,iy),topiy(ix,iy));
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
        fnbx_pll,... % Parallel convection
        fnbx_drift,... % ExB + diamagnetic drifts
        fnbx_pinch,... % Anomalous pinch
        fnbx_ch,... % Current-related flux
        fnbx_nanom,... % Anomalous density diffusion
        fnbx_panom),... % Anomalous pressure diffusion
    	cat(3,...
        raddiv_pll+raddiv_drift+raddiv_ch+raddiv_pinch+raddiv_nanom+raddiv_panom,... % Radial transport
        b2stel_sna_ion_prev+b2stel_sna_ion_next+b2stel_sna_rec_prev+b2stel_sna_rec_next+b2stcx_sna,... % Atomic processes (B2)
        sum(eirene_mc_papl_sna,4)+sum(eirene_mc_pmpl_sna,4)+sum(eirene_mc_pipl_sna,4),... % Plasma-neutral collisions(EIRENE)
        sum(eirene_mc_pppl_sna,4),... % Recombinations (EIRENE)
        b2stbc_sna,... % Boundary source
        b2stbr_phys_sna+b2stbr_bas_sna+b2stbr_first_flight_sna,... % Recycling source
        b2stbm_sna+ext_sna+b2srdt_sna+b2srsm_sna+b2srst_sna),... % Additional + numeric sources
    	rescb,...
        {'Total upstream particle flux',...
        'Total downstream particle flux',...
        'Total poloidally-integrated particle source',...
        'Poloidally-integrated residual'},...
        {'Parallel convection',...
        'ExB + diamagnetic drifts',...
        'Anomalous pinch',...
        'Current-related flux',...
        'Anomalous density diffusion',...
        'Anomalous pressure diffusion'},...
        {'Radial transport',...
        'Atomic processes (B2)',...
        'Plasma-neutral collisions (EIRENE)',...
        'Recombinations (EIRENE)',...
        'Boundary source',...
        'Recycling source',...
        'Additional + numeric sources'},...
        gmtry,indbal,false,units,default_region,reverse,areaend,areatype,radbaldist);
    j = j+1;
end

end