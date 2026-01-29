function geometry = read_b2fgmtry(simulation)
%
% read_b2fgmtry reads the geometry file containing details on the geometry
% Output is a struct "geometry" containing some magnetic geometry and cell variables
%
%% PRELIMINARY OPERATIONS

% Load the files and read the version

index_run = find(contains({simulation.run.name},'b2fgmtry'));
index_baserun = find(contains({simulation.geometry.name},'b2fgmtry'));
if isempty(index_run) && isempty (index_baserun)
   error('Error: b2fgmtry not found');
end

if not(isempty(index_run)) && strcmp(simulation.run(index_run).status,'found')
    index = index_run;
    file = simulation.run(index).file;
elseif not(isempty(index_baserun)) && strcmp(simulation.geometry(index_baserun).status,'found')
    index = index_baserun;
    file = simulation.geometry(index).file;
end

fid = fopen(file);

if (fid == -1)
   error('Error: b2fgmtry not found');
end

line    = fgetl(fid);
version = line(8:17);

line    = fgetl(fid);
if contains(line, 'nx,ny')
    version = 'structured';
elseif contains(line, 'nCi,nCg,nCv,nFc,nVx,nFs,nFt')
    version = 'unstructured';
end
frewind(fid);

try
index_b2time = find(contains({simulation.run.name},'b2time.nc'));
if isempty(index_b2time)
   error('Error: b2time.nc not found');
end
fid_b2time = simulation.run(index_b2time).fid;
file_b2time = simulation.run(index_b2time).file;
if (fid_b2time == -1)
   error('Error: b2time.nc not found');
end
catch
end

% Read type of geometry

geometry.geometry_type = simulation.geometry_type;

% Read dimensions and symmetry

if strcmp(version,'structured')

dim = scan_b2_int(fid,'nx,ny',2);
nx  = dim(1);
ny  = dim(2);

geometry.isymm = scan_b2_int(fid,'isymm',1);
geometry.nx = nx+2;
geometry.ny = ny+2;

elseif strcmp(version,'unstructured')

dim = scan_b2_int(fid,'nCi,nCg,nCv,nFc,nVx,nFs,nFt',7);
nCi  = dim(1);
nCg  = dim(2);
nCv  = dim(3);
nFc  = dim(4);
nVx  = dim(5);
nFs  = dim(6);
nFt  = dim(7);

dim = scan_b2_int(fid,'nCmxVx,nCmxFc,nVmxCv,nVmxFc,nCmx',5);
nCmxVx = dim(1);
nCmxFc = dim(2);
nVmxCv = dim(3);
nVmxFc = dim(4);
nCmxNv = dim(5);

geometry.nCi = nCi;
geometry.nCg = nCg;
geometry.nCv = nCv;
geometry.nFc = nFc;
geometry.nVx = nVx;
geometry.nFs = nFs;
geometry.nFt = nFt;

geometry.nCmxVx = nCmxVx;
geometry.nCmxFc = nCmxFc;
geometry.nVmxCv = nVmxCv;
geometry.nVmxFc = nVmxFc;
geometry.nCmxNv = nCmxNv;

geometry.isClassicalGrid = scan_b2_int(fid,'isClassicalGrid',1);
dim = scan_b2_int(fid,'nx,ny,nncut',3);
nx    = dim(1);
ny    = dim(2);
nncut = dim(3);
geometry.nx=nx+2;
geometry.ny=ny+2;
geometry.nncut=nncut;
geometry.isymm = scan_b2_int(fid,'isymm',1);

end

%% READ THE DATA (STRUCTURED VERSION)

if strcmp(version,'structured')

% Magnetic geometry and cell variables

geometry.crx  = scan_b2_real(fid,'crx' ,[nx+2,ny+2,4]); % x coordinates of the corner of each cell
geometry.cry  = scan_b2_real(fid,'cry' ,[nx+2,ny+2,4]); % y coordinates of the corner of each cell

geometry.crx_center = mean(geometry.crx,3);
geometry.cry_center = mean(geometry.cry,3);
geometry.crx_left = zeros(geometry.nx,geometry.ny);
geometry.cry_left = zeros(geometry.nx,geometry.ny);
geometry.crx_bottom = zeros(geometry.nx,geometry.ny);
geometry.cry_bottom = zeros(geometry.nx,geometry.ny);
for iy = 1:geometry.ny
    for ix = 1:geometry.nx
        geometry.crx_left(ix,iy)=(geometry.crx(ix,iy,1)+geometry.crx(ix,iy,3))/2;
        geometry.cry_left(ix,iy)=(geometry.cry(ix,iy,1)+geometry.cry(ix,iy,3))/2;
    end
end
for iy = 1:geometry.ny
    for ix = 1:geometry.nx
        geometry.crx_bottom(ix,iy)=(geometry.crx(ix,iy,1)+geometry.crx(ix,iy,2))/2;
        geometry.cry_bottom(ix,iy)=(geometry.cry(ix,iy,1)+geometry.cry(ix,iy,2))/2;
    end
end

if str2num(strrep(version,'.','')) >= str2num(strrep('03.002.000','.',''))
    geometry.fpsi = scan_b2_real(fid,'fpsi',[nx+2,ny+2,4,3]); % potentials for the magnetic field components
else
    geometry.fpsi = scan_b2_real(fid,'fpsi',[nx+2,ny+2,4]);   % potentials for the magnetic field components
end
geometry.ffbz = scan_b2_real(fid,'ffbz',[nx+2,ny+2,4]); % field functions for the magnetic field components
geometry.bb   = scan_b2_real(fid,'bb'  ,[nx+2,ny+2,4]); % components of the magnetic field in each cell (x,y,z,absolute), T
geometry.vol  = scan_b2_real(fid,'vol' ,[nx+2,ny+2]);   % volume of each cell, m^-3
geometry.hx   = scan_b2_real(fid,'hx'  ,[nx+2,ny+2]);   % metric coefficients in the x direction, m
geometry.hy   = scan_b2_real(fid,'hy'  ,[nx+2,ny+2]);   % metric coefficients in the y direction, m
geometry.qz   = scan_b2_real(fid,'qz'  ,[nx+2,ny+2,2]); % relative orientation of the cell sides (sin(t), cos(t))
if str2num(strrep(version,'.','')) >= str2num(strrep('03.001.000','.',''))
    geometry.qc   = scan_b2_real(fid,'qc'  ,[nx+2,ny+2,2]);   % angle between x direction of the cell and its left face (cos(t))
    geometry.qs   = scan_b2_real(fid,'qs'  ,[nx+2,ny+2,2]);
else
    geometry.qc   = scan_b2_real(fid,'qc'  ,[nx+2,ny+2]);
    geometry.qs   = [];
end
geometry.gs   = scan_b2_real(fid,'gs'  ,[nx+2,ny+2,3]); % contact areas of the cell (with left neightbor, bottom neighbor, normal to z), m^2

% Other geometric quantities

geometry.nlreg = scan_b2_int(fid,'nlreg',1);           
geometry.nlxlo = scan_b2_int(fid,'nlxlo',geometry.nlreg);
geometry.nlxhi = scan_b2_int(fid,'nlxhi',geometry.nlreg);
geometry.nlylo = scan_b2_int(fid,'nlylo',geometry.nlreg);
geometry.nlyhi = scan_b2_int(fid,'nlyhi',geometry.nlreg);
geometry.nlloc = scan_b2_int(fid,'nlloc',geometry.nlreg);

geometry.nncut     = scan_b2_int(fid,'nncut'    ,1);                 % number of topological cuts
geometry.leftcut   = scan_b2_int(fid,'leftcut'  ,geometry.nncut);    % poloidal index of the cell to the right of the left branch of the cut
geometry.rightcut  = scan_b2_int(fid,'rightcut' ,geometry.nncut);    % poloidal index of the cell to the right of the right branch of the cut
geometry.topcut    = scan_b2_int(fid,'topcut'   ,geometry.nncut);    % radial index of the cell above the cut
geometry.bottomcut = scan_b2_int(fid,'bottomcut',geometry.nncut);    % radial index of the cell below the cut

try

geometry.imp = ncread(file_b2time,'jxi');                           % poloidal index of inner midplane
geometry.omp = ncread(file_b2time,'jxa');                           % poloidal index of outer midplane
geometry.sep = ncread(file_b2time,'jsep');                          % radial index of separatrix

geometry.dsi = ncread(file_b2time,'dsi');
geometry.dsa = ncread(file_b2time,'dsa');
geometry.dsl = ncread(file_b2time,'dsl');
geometry.dsLT = ncread(file_b2time,'dsLT');
geometry.dsLP = ncread(file_b2time,'dsLP');
geometry.dsr = ncread(file_b2time,'dsr');
geometry.dsRT = ncread(file_b2time,'dsRT');
geometry.dsRP = ncread(file_b2time,'dsRP');

if strcmp(simulation.geometry_type,'Connected double null') || ...
        strcmp(simulation.geometry_type,'Disconnected double null') || ...
        strcmp(simulation.geometry_type,'LFS snowflake')
    geometry.dstl = ncread(file_b2time,'dstl');
    geometry.dsTLT = ncread(file_b2time,'dsTLT');
    geometry.dsTLP = ncread(file_b2time,'dsTLP');
    geometry.dstr = ncread(file_b2time,'dstr');
    geometry.dsTRT = ncread(file_b2time,'dsTRT');
    geometry.dsTRP = ncread(file_b2time,'dsTRP');
end

catch
end

geometry.leftix    = scan_b2_int(fid,'leftix'   ,[nx+2,ny+2]);       % poloidal index of left neightbor
geometry.rightix   = scan_b2_int(fid,'rightix'  ,[nx+2,ny+2]);       % poloidal index of right neightbor
geometry.topix     = scan_b2_int(fid,'topix'    ,[nx+2,ny+2]);       % poloidal index of top neightbor
geometry.bottomix  = scan_b2_int(fid,'bottomix' ,[nx+2,ny+2]);       % poloidal index of bottom neightbor
geometry.leftiy    = scan_b2_int(fid,'leftiy'   ,[nx+2,ny+2]);       % radial index of left neighbor
geometry.rightiy   = scan_b2_int(fid,'rightiy'  ,[nx+2,ny+2]);       % radial index of right neighbor
geometry.topiy     = scan_b2_int(fid,'topiy'    ,[nx+2,ny+2]);       % radial index of top neighbor
geometry.bottomiy  = scan_b2_int(fid,'bottomiy' ,[nx+2,ny+2]);       % radial index of bottom neighbor

geometry.region      = scan_b2_int(fid,'region'     ,[nx+2,ny+2,3]); % type of region (volume, x-directed surface, y-directed surface)
geometry.nnreg       = scan_b2_int(fid,'nnreg'      ,3);             % number of regions (volume, x-directed surface, y-directed surface)
geometry.resignore   = scan_b2_int(fid,'resignore'  ,[nx+2,ny+2,2]); % main cell or guard cell
geometry.periodic_bc = scan_b2_int(fid,'periodic_bc',1);             

geometry.pbs  = scan_b2_real(fid,'pbs' ,[nx+2,ny+2,2]);               % effective (i.e. parallel) contact area between left and bottom neightbor, m^2
geometry.wbbl = scan_b2_real(fid,'wbbl',[nx+2,ny+2,4]);               % components of the magnetic field at the midpoint of the left face of each cell (x,y,z,absolute), T
geometry.parg = scan_b2_real(fid,'parg',100);

if str2num(strrep(version,'.','')) >= str2num(strrep('03.002.000','.',''))

    geometry.cflags = scan_b2_int(fid,'cflags' ,[nx+2,ny+2,5]);
    geometry.hc     = scan_b2_real(fid,'hc'     ,[nx+2,ny+2,4]);
    geometry.ht     = scan_b2_real(fid,'ht'     ,[nx+2,ny+2,2]);
    geometry.qac    = scan_b2_real(fid,'qac'    ,[nx+2,ny+2,2]);
    geometry.qas    = scan_b2_real(fid,'qas'    ,[nx+2,ny+2,2]);
    geometry.ebc    = scan_b2_real(fid,'ebc'    ,[nx+2,ny+2,3]);
    
    geometry.vol(geometry.vol > 1e99) = 0;
    geometry.hx (geometry.hx  > 1e99) = 0;
    geometry.hy (geometry.hy  > 1e99) = 0;
    
else
    geometry.cflags = [];
    geometry.hc     = [];
    geometry.ht     = [];
    geometry.qac    = [];
    geometry.qas    = [];
    geometry.ebc    = [];
    
end

% Poloidal and parallel distances of the left edge of the cells from the inner target

geometry.dspoledge = zeros(geometry.nx,geometry.ny);
geometry.dsparedge = zeros(geometry.nx,geometry.ny);
for iy=1:geometry.ny
    geometry.dspoledge(1,iy)=-geometry.hx(1,iy);
    geometry.dsparedge(1,iy)=-geometry.hx(1,iy)*abs(geometry.bb(1,iy,4)/geometry.bb(1,iy,1));
    for ix=2:geometry.nx
      geometry.dspoledge(ix,iy)=geometry.dspoledge(ix-1,iy)+geometry.hx(ix-1,iy);
      geometry.dsparedge(ix,iy)=geometry.dsparedge(ix-1,iy)+geometry.hx(ix-1,iy)*abs(geometry.bb(ix-1,iy,4)/geometry.bb(ix-1,iy,1));
    end
end

% Poloidal and parallel distances of the center of the cells from the inner target

geometry.dspol = zeros(geometry.nx,geometry.ny);
geometry.dspar = zeros(geometry.nx,geometry.ny);
geometry.dspol(1:end-1,:) = 0.5*(geometry.dspoledge(1:end-1,:)+geometry.dspoledge(2:end,:));
geometry.dspol(end,:) = geometry.dspoledge(end,:)+0.5*geometry.hx(end,:);
geometry.dspar(1:end-1,:) = 0.5*(geometry.dsparedge(1:end-1,:)+geometry.dsparedge(2:end,:));
geometry.dspar(end,:) = geometry.dsparedge(end,:)+0.5*geometry.hx(end,:)*abs(geometry.bb(end,:,4)/geometry.bb(end,:,1));

%% READ THE DATA (UNSTRUCTURED VERSION)

elseif strcmp(version,'unstructured')

geometry.cvFcP = scan_b2_int(fid, 'cvFcP', [nCv,2] );
geometry.cvFc  = scan_b2_int(fid, 'cvFc' , [nCmxFc]);
geometry.fcCv  = scan_b2_int(fid, 'fcCv' , [nFc,2] );
geometry.fcVx  = scan_b2_int(fid, 'fcVx' , [nFc,2] );
geometry.cvVxP = scan_b2_int(fid, 'cvVxP', [nCv,2] );
geometry.cvVx  = scan_b2_int(fid, 'cvVx' , [nCmxVx]);
geometry.vxFcP = scan_b2_int(fid, 'vxFcP', [nVx,2] );
geometry.vxFc  = scan_b2_int(fid, 'vxFc' , [nVmxFc]);
geometry.vxCvP = scan_b2_int(fid, 'vxCvP', [nVx,2] );
geometry.vxCv  = scan_b2_int(fid, 'vxCv' , [nVmxCv]);
geometry.ftCvP = scan_b2_int(fid, 'ftCvP', [nFt,2] );
geometry.ftCv  = scan_b2_int(fid, 'ftCv' , [nCv]   );
geometry.ftFcP = scan_b2_int(fid, 'ftFcP', [nFt,2] );
geometry.ftFc  = scan_b2_int(fid, 'ftFc' , [nFc]   );
geometry.cvFt  = scan_b2_int(fid, 'cvFt' , [nCv]   );
geometry.fsFcP = scan_b2_int(fid, 'fsFcP', [nFs,2] );
geometry.fsFc  = scan_b2_int(fid, 'fsFc' , [nFc]   );
geometry.fcReg = scan_b2_int(fid, 'fcReg', [nFc]   );
geometry.cvReg = scan_b2_int(fid, 'cvReg', [nCv]   );
geometry.ftReg = scan_b2_int(fid, 'ftReg', [nFt]   );
geometry.intcellP = scan_b2_real(fid, 'intcellP', [nCmxFc]);
geometry.intcellR = scan_b2_real(fid, 'intcellR', [nCmxFc]);
if geometry.isClassicalGrid == 1
    geometry.imapCv  = scan_b2_int(fid, 'imapCv',  [nx+2,ny+2]   );
    geometry.imapFcx = scan_b2_int(fid, 'imapFcx', [nx+2,ny+2]   );
    geometry.imapFcy = scan_b2_int(fid, 'imapFcy', [nx+2,ny+2]   );
    geometry.imapVx  = scan_b2_int(fid, 'imapVx',  [nx+2,ny+2]   );
    geometry.icornVx = scan_b2_int(fid, 'icornVx',  nx   );
else
    geometry.imapCv  = [];
    geometry.imapFcx = [];
    geometry.imapFcy = [];
    geometry.imapVx  = [];
    geometry.icornVx = [];
end
geometry.fcLbl = scan_b2_int(fid, 'fcLbl', [nFc]);
geometry.cvLbl = scan_b2_int(fid, 'cvLbl', [nCv]);
geometry.ftLbl = scan_b2_int(fid, 'ftLbl', [nFt]);


% cell volumes 
geometry.cvBb   = scan_b2_real(fid, 'cvBb',  [nCv,4]  );
geometry.cvEb   = scan_b2_real(fid, 'cvEb',  [nCv,3]  );
geometry.cvX    = scan_b2_real(fid, 'cvX',   [nCv]    );
geometry.cvY    = scan_b2_real(fid, 'cvY',   [nCv]    );
geometry.cvSz   = scan_b2_real(fid, 'cvSz',  [nCv]    );
geometry.cvHz   = scan_b2_real(fid, 'cvHz',  [nCv]    );
geometry.cvHx   = scan_b2_real(fid, 'cvHx',  [nCv]    );
geometry.cvQgam = scan_b2_real(fid, 'cvQgam',[nCv,2]  );
geometry.cvVol  = scan_b2_real(fid, 'cvVol', [nCv]    );
geometry.vol    = geometry.cvVol;


% face quantities
geometry.fcBb   = scan_b2_real(fid,'fcBb',  [nFc,4]  );
geometry.fcS    = scan_b2_real(fid,'fcS',   [nFc]   );
geometry.fcHc   = scan_b2_real(fid,'fcHc',  [nFc,2] );
geometry.fcHt   = scan_b2_real(fid,'fcHt',  [nFc]   );
geometry.fcQgam = scan_b2_real(fid,'fcQgam',[nFc,2] );
geometry.fcQalf = scan_b2_real(fid,'fcQalf',[nFc,2] );
geometry.fcQbet = scan_b2_real(fid,'fcQbet',[nFc,2] );
geometry.fcPbs  = scan_b2_real(fid,'fcPbs', [nFc]   );

% vertex quantities
geometry.vxBb   = scan_b2_real(fid,'vxBb',  [nVx,4]  );
geometry.vxX    = scan_b2_real(fid,'vxX',   [nVx]    );
geometry.vxY    = scan_b2_real(fid,'vxY',   [nVx]    );
geometry.vxFfbz = scan_b2_real(fid,'vxFfbz',[nVx]    );
geometry.vxFpsi = scan_b2_real(fid,'vxFpsi',[nVx]    );

% flux surface quantities
geometry.cvConn = scan_b2_real(fid,'cvConn',[nCv] );
geometry.fsPsi  = scan_b2_real(fid,'fsPsi',[nFs] );

try

geometry.cvlisti = ncread(file_b2time,'cvlisti');
geometry.cvlista = ncread(file_b2time,'cvlista');
geometry.cvlistl = ncread(file_b2time,'cvlistl');
geometry.cnlistl = ncread(file_b2time,'cnlistl');
geometry.fclistl = ncread(file_b2time,'fclistl');
geometry.cvlistr = ncread(file_b2time,'cvlistr');
geometry.cnlistr = ncread(file_b2time,'cnlistr');
geometry.fclistr = ncread(file_b2time,'fclistr');

geometry.dsi = ncread(file_b2time,'dsi');
geometry.dsa = ncread(file_b2time,'dsa');
geometry.dsl = ncread(file_b2time,'dsl');
geometry.dsLT = ncread(file_b2time,'dsLT');
geometry.dsLP = ncread(file_b2time,'dsLP');
geometry.dsr = ncread(file_b2time,'dsr');
geometry.dsRT = ncread(file_b2time,'dsRT');
geometry.dsRP = ncread(file_b2time,'dsRP');

geometry.icsepimp = ncread(file_b2time,'icsepimp');
geometry.icsepomp = ncread(file_b2time,'icsepomp');

if strcmp(simulation.geometry_type,'Connected double null') || ...
        strcmp(simulation.geometry_type,'Disconnected double null') || ...
        strcmp(simulation.geometry_type,'LFS snowflake')
    geometry.dstl = ncread(file_b2time,'dstl');
    geometry.dsTLT = ncread(file_b2time,'dsTLT');
    geometry.dsTLP = ncread(file_b2time,'dsTLP');
    geometry.dstr = ncread(file_b2time,'dstr');
    geometry.dsTRT = ncread(file_b2time,'dsTRT');
    geometry.dsTRP = ncread(file_b2time,'dsTRP');
end

catch
end

end

fprintf('Structure GEOMETRY from b2fgmtry read.\n');

frewind(fid);

fclose(fid);

end