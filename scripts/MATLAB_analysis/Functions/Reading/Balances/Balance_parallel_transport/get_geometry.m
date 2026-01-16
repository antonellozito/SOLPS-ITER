function gmtry = get_geometry(filename)
%
% get_geometry gets commonly used geomertry variables for a simulation and puts them in a single structure
%
%% BASIC DATA

% Dimensions
finfo = ncinfo(filename);
dimNames = {finfo.Dimensions.Name};
dimMatch = strcmp(dimNames,'nx_plus2');
gmtry.nx = finfo.Dimensions(dimMatch).Length;
dimMatch = strcmp(dimNames,'ny_plus2');
gmtry.ny = finfo.Dimensions(dimMatch).Length;
dimMatch = strcmp(dimNames,'ns');
gmtry.ns = finfo.Dimensions(dimMatch).Length;
dimMatch = strcmp(dimNames,'nstra');
gmtry.nstra = finfo.Dimensions(dimMatch).Length;

% Species string:
tmp = ncread(filename,'species');
gmtry.species = {};
for i=1:gmtry.ns
    gmtry.species{i} = strtrim(tmp(:,i)');
    display(sprintf('Species %d: %s',i,gmtry.species{i}));
end

% Info about coupled run:
gmtry.b2mndr_eirene = ncread(filename,'b2mndr_eirene');
gmtry.b2mndr_hz = ncread(filename,'b2mndr_hz');

% Basic physics quantities:
gmtry.bb = ncread(filename,'bb');
gmtry.za = ncread(filename,'za');
gmtry.am = ncread(filename,'am');
gmtry.mp = ncread(filename,'mp');
gmtry.ev = ncread(filename,'ev');

%% GEOMETRY DATA

% Basic geometric quantities
gmtry.dv = ncread(filename,'vol');
gmtry.hx = ncread(filename,'hx');
gmtry.hy = ncread(filename,'hy');
gmtry.hz = ncread(filename,'hz');
gmtry.gs = ncread(filename,'gs');

% Cell coordinates
gmtry.r = ncread(filename,'crx');
gmtry.z = ncread(filename,'cry');
gmtry.cr = mean(gmtry.r,3);
gmtry.cz = mean(gmtry.z,3);
gmtry.cr_x = zeros(gmtry.nx-1,gmtry.ny);
gmtry.cz_x = zeros(gmtry.nx-1,gmtry.ny);
gmtry.cr_y = zeros(gmtry.nx,gmtry.ny-1);
gmtry.cz_y = zeros(gmtry.nx,gmtry.ny-1);
for iy = 1:gmtry.ny
    for ix = 1:gmtry.nx-1
        gmtry.cr_x(ix,iy)=(gmtry.r(ix+1,iy,1)+gmtry.r(ix+1,iy,3))/2;
        gmtry.cz_x(ix,iy)=(gmtry.z(ix+1,iy,1)+gmtry.z(ix+1,iy,3))/2;
    end
end
for iy = 1:gmtry.ny-1
    for ix = 1:gmtry.nx
        gmtry.cr_y(ix,iy)=(gmtry.r(ix,iy+1,1)+gmtry.r(ix,iy+1,2))/2;
        gmtry.cz_y(ix,iy)=(gmtry.z(ix,iy+1,1)+gmtry.z(ix,iy+1,2))/2;
    end
end

% Neighbouring indices
gmtry.rightix = ncread(filename,'rightix')+1;
gmtry.leftix = ncread(filename,'leftix')+1;
gmtry.rightiy = ncread(filename,'rightiy')+1;
gmtry.leftiy = ncread(filename,'leftiy')+1;
gmtry.topix = ncread(filename,'topix')+1;
gmtry.bottomix = ncread(filename,'bottomix')+1;
gmtry.topiy = ncread(filename,'topiy')+1;
gmtry.bottomiy = ncread(filename,'bottomiy')+1;

% Midplane and separatrix indeces
gmtry.imp = ncread(filename,'jxi')+1;
gmtry.omp = ncread(filename,'jxa')+1;
gmtry.sep = ncread(filename,'jsep')+1;

% Poloidal and parallel distances of the left edge of the cells from the inner target
bb = gmtry.bb;
hx = gmtry.hx;
gmtry.dspoledge = zeros(gmtry.nx,gmtry.ny);
gmtry.dsparedge = zeros(gmtry.nx,gmtry.ny);
for iy=1:gmtry.ny
    gmtry.dspoledge(1,iy)=-hx(1,iy);
    gmtry.dsparedge(1,iy)=-hx(1,iy)*abs(bb(1,iy,4)/bb(1,iy,1));
    for ix=2:gmtry.nx
      gmtry.dspoledge(ix,iy)=gmtry.dspoledge(ix-1,iy)+hx(ix-1,iy);
      gmtry.dsparedge(ix,iy)=gmtry.dsparedge(ix-1,iy)+hx(ix-1,iy)*abs(bb(ix-1,iy,4)/bb(ix-1,iy,1));
    end
end

% Poloidal and parallel distances of the center of the cells from the inner target
gmtry.dspol = zeros(gmtry.nx,gmtry.ny);
gmtry.dspar = zeros(gmtry.nx,gmtry.ny);
gmtry.dspol(1:end-1,:) = 0.5*(gmtry.dspoledge(1:end-1,:)+gmtry.dspoledge(2:end,:));
gmtry.dspol(end,:) = gmtry.dspoledge(end,:)+0.5*hx(end,:);
gmtry.dspar(1:end-1,:) = 0.5*(gmtry.dsparedge(1:end-1,:)+gmtry.dsparedge(2:end,:));
gmtry.dspar(end,:) = gmtry.dsparedge(end,:)+0.5*hx(end,:)*abs(bb(end,:,4)/bb(end,:,1));

%% PLOTTING COLORMAP

gmtry.cmap = ([0.0000    0.4470    0.7410;...
                0.8500    0.3250    0.0980;...
                0.9290    0.6940    0.1250;...
                0.4940    0.1840    0.5560;...
                0.4660    0.6740    0.1880;...
                0.3010    0.7450    0.9330;...
                0.6350    0.0780    0.1840]);
            
end