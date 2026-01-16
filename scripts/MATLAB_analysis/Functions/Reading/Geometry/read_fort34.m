function cells = read_fort34(simulation)
%
% read_fort34 reads the fort.34 file (cells) created by EIRENE
% Output is a struct "cells" containing the coordinates of the cell faces of the triangular mesh
%
%% PRELIMINARY OPERATIONS

% Load the file

index = find(contains({simulation.geometry.name},'fort.34'));
if isempty(index)
   error('Error: fort.34 not found');
end
fid = simulation.geometry(index).fid;
if (fid == -1)
   error('Error: fort.34 not found');
end

%% READ THE DATA

ntria = fscanf(fid,'%d',1);

cells = zeros(ntria,3);

for i = 1:ntria
    data = fscanf(fid,'%d',4);
    cells(i,:) = data(2:end);
end

frewind(fid);

end