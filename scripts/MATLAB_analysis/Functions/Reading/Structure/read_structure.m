function structure = read_structure(simulation)
%
% read_structure reads the structure files containing the coordinate of the physical structures
% Output is a struct "structure" with such radial and height coordinates
%
%% PRELIMINARY OPERATIONS

% Load the file

index = find(contains({simulation.structure.name},'structure.dat'));
if isempty(index)
   error('Error: structure.dat not found');
end
file = simulation.structure(index).file;
fid = fopen(file);
if (fid == -1)
   error('Error: structure.dat not found');
end

% Read the number of structures

nstr = fscanf(fid,'%d',1);

line = fgetl(fid);
while isempty(strfind(line,'$structures'))
    line = fgetl(fid);
    if line == -1
        error('Error: EOF reached without finding $structures.');
    end
end

%% READ THE DATA

structure = struct('nel',{},'r',{},'z',{});

for i = 1:nstr
    
    % Consistency check
    
    line = fgetl(fid);
    [label,istr] = strread(line,'%s %d');
    if (~strcmp(label,'Structure') ||  i ~= istr)
        error('Error: read_structure: inconsistent input.');
    end
    
    % Read number of segments and coordinates
    
    nel    = fscanf(fid,'%d',1);
    coords = fscanf(fid,'%f %f \n',2*abs(nel));
    structure(i).nel = nel;
    structure(i).r   = coords(1:2:end-1);
    structure(i).z   = coords(2:2:end);
    
end

frewind(fid);

fclose(fid);

fprintf('Structure STRUCTURE from structure.dat read.\n');

end