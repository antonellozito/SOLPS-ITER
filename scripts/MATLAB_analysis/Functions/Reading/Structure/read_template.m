function template = read_template(simulation)
%
% read_template reads the template file containing details on the device structure
% Output is a struct "template" containing the coordinate of the various structures
%
%% PRELIMINARY OPERATIONS

% Load the file

index = find(contains({simulation.structure.name},'template'));
if isempty(index)
   error('Error: template not found');
end
fid = simulation.structure(index).fid;
if (fid == -1)
   error('Error: template not found');
end

%% READ THE DATA

% Init structure
template = struct('r',{},'z',{});

% In the ogr-file, polygons are separated by blank lines, and number of
% points per polygon not specied
line = fgetl(fid);
i    = 0;
while line ~= -1

    coords = [];
    while (length(line) > 1) & (line ~= -1) % scan until next blank line (or EOF)
        point  = textscan(line,'%f',2);
        coords = [coords;point{:}'];
        line = fgetl(fid);
    end

    % Store this polygon in ogr
    i = i+1;
    template(i).r   = coords(:,1)*0.001; % Convert to m
    template(i).z   = coords(:,2)*0.001; % Convert to m

    % Read next line
    line = fgetl(fid);

end

frewind(fid);

end
