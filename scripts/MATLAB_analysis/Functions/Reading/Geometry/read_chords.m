function chords = read_chords(file)
%
% read_chr reads the *.chr file contining data on the diagnostic chords
% Output is a struct "chr" containing the coordinate of the chords
%
%% PRELIMINARY OPERATIONS

% Open the file
[fid,msg] = fopen(file);
if (fid == -1)
   error(msg);
end

% Read a label
label     = fgetl(fid);
chords.label = label;

% Initialize empty chords
chords.r   = [];
chords.z   = [];
chords.y   = [];
chords.num = [];

%% READ THE DATA

% Read line per line until end of file
line = fgetl(fid);
while line ~= -1
    chorddata = strread(line,'%f',7);
    chords.r   = [chords.r;chorddata(1), chorddata(4)];
    chords.y   = [chords.y;chorddata(2), chorddata(5)];
    chords.z   = [chords.z;chorddata(3), chorddata(6)];
    chords.num = [chords.num;chorddata(7)];
    
    line = fgetl(fid);
end

%% CLOSE THE FILE

fclose(fid);

end