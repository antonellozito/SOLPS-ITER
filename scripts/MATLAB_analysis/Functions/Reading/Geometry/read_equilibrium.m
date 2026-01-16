function equilibrium = read_equilibrium(simulation)
%
% read_equilibrium reads the rzpsi.dat file containing details on the magnetic equilibrium
% Output is a struct "equilibrium" containing the magnetic flux function matrix on a (R,z) grid
%
%% PRELIMINARY OPERATIONS

% Load the file

index = find(contains({simulation.geometry.name},'rzpsi.dat'));
if isempty(index)
   error('Error: rzpsi.dat not found');
end
fid = simulation.geometry(index).fid;
if (fid == -1)
   error('Error: rzpsi.dat not found');
end

% Read the dimensions

dims  = fscanf(fid,'%d',2);
nR   = dims(1);
nz   = dims(2);

line = fgetl(fid);
while ~contains(line,'nr=')
    line = fgetl(fid);
    if line == -1
        error(['EOF reached without finding nr=.']);
    end
end
nR0 = strread(line,'%*s%d');
if nR ~= nR0
    error('Error: readrzpsi: inconsistent specification of nR.');
end
R=fscanf(fid, '%f',nR);

line = fgetl(fid);
while ~contains(line,'nz=')
    line = fgetl(fid);
    if line == -1
        error(['EOF reached without finding nz=.']);
    end
end
nz0 = strread(line,'%*s %d');
if nz ~= nz0
    error('Error: readrzpsi: inconsistent specification of nz.');
end
z=fscanf(fid, '%f',nz);

equilibrium.size_R=nR;
equilibrium.size_z=nz;
equilibrium.N=nR*nz;

%% READ THE DATA

PF=zeros(nR,nz);
fscanf(fid, '%*s\n',1);
PF=(fscanf(fid, '%f',[nR,nz]));

equilibrium.R=R;
equilibrium.z=z;
equilibrium.PF=PF./(2*pi);

fprintf('Structure EQUILIBRIUM from rzpsi.dat read.\n');

frewind(fid);

end
