function adf11_default_libraries = load_filelist_adas_adf11(SIMULATION)
%
% load_filelist_adas_adf11 loads the default libraries to be read when
% requesting ADAS adf11 data, as specified in the
% %SOLPSTOP/modules/B2.5/Database/ratadas.filelist file
%
%% PRELIMINARY OPERATIONS

adf11_default_filelist = sprintf('%s/ratadas.filelist',SIMULATION.B25_DATABASE);
fid = fopen(adf11_default_filelist);

%% READ THE DATA

line = fgetl(fid);
line = fgetl(fid);

temp = textscan(line,'%d');
number_atoms = double(temp{1});

for i = 1:number_atoms
    line = fgetl(fid);
    temp = textscan(line,'''%d'' ''%d'' ''%d'' ''%d'' ''%d'' ''%d'' ''%d'' ''%2s''');
    adf11_default_libraries.scd(i).atom = char(temp{8});
    adf11_default_libraries.acd(i).atom = char(temp{8});
    adf11_default_libraries.ccd(i).atom = char(temp{8});
    adf11_default_libraries.plt(i).atom = char(temp{8});
    adf11_default_libraries.prb(i).atom = char(temp{8});
    adf11_default_libraries.prc(i).atom = char(temp{8});
    adf11_default_libraries.scd(i).library = double(temp{2});
    adf11_default_libraries.acd(i).library = double(temp{1});
    adf11_default_libraries.ccd(i).library = double(temp{3});
    adf11_default_libraries.plt(i).library = double(temp{5});
    adf11_default_libraries.prb(i).library = double(temp{4});
    adf11_default_libraries.prc(i).library = adf11_default_libraries.prb(i).library;
end

%% CLOSE THE FILE

fclose(fid);

end
