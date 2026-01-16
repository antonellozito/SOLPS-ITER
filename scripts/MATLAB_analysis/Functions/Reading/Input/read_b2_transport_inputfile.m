function b2_transport_inputfile = read_b2_transport_inputfile(simulation)
%
% b2_transport_inputfile reads the b2.transport.inputfile containing the
% specified radial variation of the anomalous transport coefficients
% Output is a struct "b2_transport_inputfile" with all the data fields
% in the b2.transport.inputfile file
%
%% PRELIMINARY OPERATIONS

% Load the files and read the version

index = find(contains({simulation.run.name},'b2.transport.inputfile'));
if isempty(index)
   error('Error: b2.transport.inputfile not found');
end
fid = simulation.run(index).fid;
if (fid == -1)
   error('Error: b2.transport.inputfile not found');
end

%% READ THE DATA

line = fgetl(fid);

i = 1;

while ~isempty(line)

while ~contains(line,'ndata')
    line = fgetl(fid);
    if line == -1
        break;
    end
end

if line == -1
    break;
end

block = textscan(line,'ndata(1,%d,%d)=%d');
coefficient = block{1};
species = block{2};
lines = block{3};

if coefficient == 1
    b2_transport_inputfile(i).coefficient = 'dna0';
elseif coefficient == 2
    b2_transport_inputfile(i).coefficient = 'dpa0';
elseif coefficient == 3
    b2_transport_inputfile(i).coefficient = 'hci0';
elseif coefficient == 4
    b2_transport_inputfile(i).coefficient = 'hce0';
elseif coefficient == 5
    b2_transport_inputfile(i).coefficient = 'vla0_x';
elseif coefficient == 6
    b2_transport_inputfile(i).coefficient = 'vla0_y';
elseif coefficient == 7
    b2_transport_inputfile(i).coefficient = 'vsa0';
elseif coefficient == 8
    b2_transport_inputfile(i).coefficient = 'sig0';
elseif coefficient == 9
    b2_transport_inputfile(i).coefficient = 'alf0';
end
    
b2_transport_inputfile(i).species = species;

while ~contains(line,'tdata')
    line = fgetl(fid);
    if line == -1
        break;
    end
end

for j = 1:lines
    line(isspace(line)) = [];
    data = textscan(line,'tdata(1,%d,%d,%d)=%.3f,tdata(2,%d,%d,%d)=%.3f');
    position = data{4};
    value = data{8};
    b2_transport_inputfile(i).data.position(j) = position;
    b2_transport_inputfile(i).data.value(j) = value;
    line = fgetl(fid);
end

i = i+1;

end

frewind(fid);

end

