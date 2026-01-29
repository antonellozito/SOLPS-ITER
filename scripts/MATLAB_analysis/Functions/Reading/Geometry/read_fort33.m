function nodes = read_fort33(simulation,ntrfrm)
%
% read_fort33 reads the fort.33 file (nodes) created by EIRENE
% Output is a struct "nodes" containing the coordinates of the nodes of the triangular mesh
%
%% PRELIMINARY OPERATIONS

% Load the file

index = find(contains({simulation.geometry.name},'fort.33'));
if isempty(index)
   error('Error: fort.33 not found');
end
file = simulation.geometry(index).file;
fid = fopen(file);
if (fid == -1)
   error('Error: fort.33 not found');
end

%% READ THE DATA

nnodes = fscanf(fid,'%d',1);
nodes  = zeros(nnodes,2);

switch ntrfrm
    
    case 0
        
        nodes(:,1) = fscanf(fid,'%f',nnodes);
        nodes(:,2) = fscanf(fid,'%f',nnodes);

    case 1
        
        for i = 1:nnodes
            
            data = fscanf(fid,'%f',3);
            nodes(i,1) = data(2);
            nodes(i,2) = data(3);
            
        end
        
    otherwise
        
        error('Error: read_ft33: wrong ntrfrm.');
        
end

nodes = nodes*1e-2;

frewind(fid);

fclose(fid);

end