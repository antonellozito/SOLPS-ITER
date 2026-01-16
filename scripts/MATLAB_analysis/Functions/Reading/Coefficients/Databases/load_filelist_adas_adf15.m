function adf15_default_libraries = load_filelist_adas_adf15(SIMULATION)
%
% load_filelist_adas_adf15 loads the default libraries to be read when
% requesting ADAS adf15 data, as specified in the
% %SOLPSTOP/modules/adas/filelist.adas.adf15 file
%
%% PRELIMINARY OPERATIONS

adf15_default_filelist = sprintf('%s/filelist.adas.adf15',SIMULATION.ADAS_DATABASE);
fid = fopen(adf15_default_filelist);

%% READ THE DATA

line = fgetl(fid);
line = fgetl(fid);

temp = textscan(line,'%d');
number_atoms = double(temp{1});

for i = 1:number_atoms
    line = fgetl(fid);
    temp = textscan(line,'''%8s'' ''%3s'' ''%s'' ''%2s'' ''  ''');
    try
        adf15_default_libraries(i).atom = char(temp{1}{1}(7:end));
        adf15_default_libraries(i).prefix = char(temp{2});
        adf15_default_libraries(i).library = str2double(temp{1}{1}(4:5));
    catch
    end
end

%% CLOSE THE FILE

fclose(fid);

end
