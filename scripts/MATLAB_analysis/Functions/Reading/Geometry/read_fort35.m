function links = read_fort35(simulation)
%
% read_fort35 reads the fort.35 file (links) created by EIRENE
% Output is the structs "nghbr", "side", "cont", "ixiy"
%
%% PRELIMINARY OPERATIONS

% Open the file and read the version

index = find(contains({simulation.geometry.name},'fort.35'));
if isempty(index)
   error('Error: fort.35 not found');
end
fid = simulation.geometry(index).fid;
if (fid == -1)
   error('Error: fort.35 not found');
end

line    = fgetl(fid);
line    = fgetl(fid);
nums = sscanf(line, '%d');
nfields = numel(nums);
if nfields == 12
    version = 'structured';
elseif nfields == 14
    version = 'unstructured';
end
frewind(fid);

%% READ THE DATA

ntria = fscanf(fid,'%d',1);

links.nghbr = zeros(ntria,3);
links.side  = zeros(ntria,3);
links.cont  = zeros(ntria,3);
if strcmp(version,'structured')
    links.ixiy  = zeros(ntria,2);
elseif strcmp(version,'unstructured')
    links.plasma_cell  = zeros(ntria,1);
    links.faces  = zeros(ntria,3);
end

for i = 1:ntria
    if strcmp(version,'structured')
        data = fscanf(fid,'%d',12);
        links.nghbr(i,:) = data(2:3:8);
        links.side(i,:)  = data(3:3:9);
        links.cont(i,:)  = data(4:3:10);
        links.ixiy(i,:)  = data(11:12);
    elseif strcmp(version,'unstructured')
        data = fscanf(fid,'%d',14);
        links.nghbr(i,:) = data(2:3:8);
        links.side(i,:)  = data(3:3:9);
        links.cont(i,:)  = data(4:3:10);
        links.plasma_cell(i,:) = data(11);
        links.faces(i,:) = data(12:14);
    end
end

frewind(fid);

end