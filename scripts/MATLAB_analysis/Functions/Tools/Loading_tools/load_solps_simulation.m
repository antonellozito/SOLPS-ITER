function SIMULATION = load_solps_simulation(RUN)

% load_solps_simulation reads the relevant simulation files and stores their
% absolute path and their file ID for following use in MATLAB.
% Output is a structure SIMULATIONS containing, as substructures, the
% absolute paths and the file IDs of such files.

%% SELECT PATH OF SIMULATION FILES AND CHECK IF THE SIMULATION EXISTS

warning('off');

% Retrieve environment variable with one or more SOLPSTOP directories set

SOLPSTOP_FULL = getenv('SOLPSTOP');

if isempty(SOLPSTOP_FULL)
    error('Error: The environment variable ''SOLPSTOP'' is not defined. Set it to your SOLPSTOP directory/directories');
end

% Split into the separate possible SOLPSTOP directories

SOLPSTOP_FOLDERS = strsplit(SOLPSTOP_FULL,':');

% Check the existence of the declared SOLPSTOP(s)

if strcmp(SOLPSTOP_FOLDERS,SOLPSTOP_FULL) 
    if not(isfolder(SOLPSTOP_FULL))
        error('Error: The folder ''%s'' does not exists. Set the environment variable ''SOLPSTOP'' to an existing folder',SOLPSTOP_FULL);
    end
else
    if ~any(isfolder(SOLPSTOP_FOLDERS))
        error( ...
            'Error: None of the folders below exists:\n%s\n\nSet the environment variable ''SOLPSTOP'' to an existing folder', ...
            strjoin(SOLPSTOP_FOLDERS,newline) ...
        );
    end
end

% Recursively search until a SOLPSTOP with the requested simulation is found

RUN_DIRECTORY = '';
SOLPSTOP_EXISTING = {};

for i = 1:numel(SOLPSTOP_FOLDERS)

    % Check if SOLPSTOP exists

    SOLPSTOP = SOLPSTOP_FOLDERS{i};
    if ~isfolder(SOLPSTOP)
        continue;
    end
    SOLPSTOP_EXISTING{end+1} = SOLPSTOP;
    
    % Check if simulation exists within existing SOLPSTOP

    if isfolder(sprintf('%s/runs/%s',SOLPSTOP,RUN))
        RUN_DIRECTORY = sprintf('%s/runs/%s',SOLPSTOP,RUN);
        break
    end

end

if isempty(RUN_DIRECTORY)
    if strcmp(SOLPSTOP,SOLPSTOP_FULL) 
        error('Error: The simulation ''%s'' does not exists within the SOLPSTOP folder ''%s''',RUN,SOLPSTOP);    
    else
        error('Error: The simulation ''%s'' does not exists within any of the SOLPSTOP folders below:\n%s',RUN,strjoin(SOLPSTOP_EXISTING,newline));        
    end
end

[parent_dir, ~, ~] = fileparts(RUN_DIRECTORY);
BASERUN_DIRECTORY = fullfile(parent_dir, 'baserun');

fprintf('SOLPSTOP: ''%s''\n',SOLPSTOP);
fprintf('Simulation: ''%s''\n',RUN);

%% NAMELISTS OF SIMULATION FILES

structure_files = ...
    {'structure.dat'};

geometry_files = ...
    {'rzpsi.dat',...
     'b2fgmtry',...
     'fort.33',...
     'fort.34',...
     'fort.35'};

atomic_rates_files = ...
    {'b2frates',...
     'AMJUEL',...
     'AMMONX',...
     'HYDHEL'};

run_files = ...
    {'b2.boundary.parameters',...
     'b2.neutrals.parameters',...
     'b2.numerics.parameters',...
     'b2.sources.profile',...
     'b2.transport.inputfile',...
     'b2.transport.parameters',...
     'b2.user.parameters',...
     'b2.neoclassical_transport.parameters',...
     'b2.wall_save.parameters',...
     'b2us.boundary.parameters',...
     'b2us.neutrals.parameters',...
     'b2us.midplane.parameters',...
     'b2us.regions.parameters',...
     'b2us.user.parameters',...
     'b2favere',...
     'b2fgmtry',...
     'b2fmovie',...
     'b2fparam',...
     'b2fplasma',...
     'b2fplasmf',...
     'b2fstati',...
     'b2fstate',...
     'b2ftrace',...
     'b2mn.exe.dir/b2ftrace',...
     'b2mn.dat',...
     'b2mn.prt',...
     'b2batch.nc',...
     'b2movies.nc',...
     'b2tallies.nc',...
     'b2time.nc',...
     'b2wall.nc',...
     'b2neo.nc',...
     'balance.nc',...
     'eirenemovies.nc',...
     'fort.13',...
     'b2mn.exe.dir/fort.13',...
     'fort.15',...
     'b2mn.exe.dir/fort.15',...
     'fort.30',...
     'b2mn.exe.dir/fort.30',...
     'fort.31',...
     'b2mn.exe.dir/fort.31',...
     'fort.44',...
     'b2mn.exe.dir/fort.44',...
     'fort.46',...
     'b2mn.exe.dir/fort.46',...
     'input.dat',...
     'fort.1',...
     'tracing/blnn_SPb.trc',...
     'b2mn.exe.dir/tracing/blnn_SPb.trc',...
     'tracing/blne.trc',...
     'b2mn.exe.dir/tracing/blne.trc',...
     'run.log',...
     'run.log.gz',...
     'run.log.last10',...
     'exp_data.json',...
     'exp_data'};

%% CREATE SIMULATION STRUCTURE

SIMULATION = struct;

%% WRITE $SOLPSTOP PATH AND DATABASES DIRECTORIES

SIMULATION.SOLPSTOP = SOLPSTOP;

SIMULATION.BASERUN_DIRECTORY = BASERUN_DIRECTORY;

SIMULATION.RUN_DIRECTORY = RUN_DIRECTORY;

SIMULATION.ADAS_DATABASE = sprintf('%s/modules/adas',SOLPSTOP);

SIMULATION.B25_DATABASE = sprintf('%s/modules/B2.5/Database',SOLPSTOP);

SIMULATION.EIRENE_DATABASE = sprintf('%s/modules/Eirene/Database',SOLPSTOP);

%% LOAD STRUCTURE FILES

i = 1;

while i <= length(structure_files)
    SIMULATION.structure(i).name = structure_files{i};
    file_path = fullfile(BASERUN_DIRECTORY, structure_files{i});
    SIMULATION.structure(i).file = file_path;
    if exist(file_path, 'file')
        SIMULATION.structure(i).status = 'found';
    else
        SIMULATION.structure(i).status = 'not found';
    end
    i = i + 1;
end

%% LOAD GEOMETRY FILES

i = 1;

while i <= length(geometry_files)
    SIMULATION.geometry(i).name = geometry_files{i};
    file_base = fullfile(BASERUN_DIRECTORY, geometry_files{i});
    if exist(file_base, 'file')
        SIMULATION.geometry(i).file = file_base;
        SIMULATION.geometry(i).status = 'found';
    else
        file_run = fullfile(RUN_DIRECTORY, geometry_files{i});
        if exist(file_run, 'file')
            SIMULATION.geometry(i).file = file_run;
            SIMULATION.geometry(i).status = 'found';
        else
            SIMULATION.geometry(i).file = file_run;
            SIMULATION.geometry(i).status = 'not found';
        end
    end
    i = i + 1;
end

%% LOAD ATOMIC RATES FILES

i = 1;

while i <= length(atomic_rates_files)
    SIMULATION.atomic_rates(i).name = atomic_rates_files{i};
    file_path = fullfile(BASERUN_DIRECTORY, atomic_rates_files{i});
    SIMULATION.atomic_rates(i).file = file_path;
    if exist(file_path, 'file')
        SIMULATION.atomic_rates(i).status = 'found';
    else
        SIMULATION.atomic_rates(i).status = 'not found';
    end
    i = i + 1;
end

%% LOAD RUN FILES

i = 1;

while i <= length(run_files)
    SIMULATION.run(i).name = run_files{i};
    file_path = fullfile(RUN_DIRECTORY, run_files{i});
    SIMULATION.run(i).file = file_path;
    if exist(file_path, 'file')
        SIMULATION.run(i).status = 'found';
    else
        SIMULATION.run(i).status = 'not found';
    end  
    i = i + 1;
end

%% READ SPECIES AND TYPE OF GEOMETRY

try
    [NREG,species,isonuclear_species] = find_nreg_species(SIMULATION);
catch
    experiment_directory = regexprep(RUN_DIRECTORY, '/[^/]*$', '');
    temp = strtrim(fileread(sprintf('%s/NREG',experiment_directory)));
    NREG = str2double(temp);
    temp = strtrim(fileread(sprintf('%s/SOLPS_FLUIDS',experiment_directory)));
    species = strsplit(temp);
    temp = cellfun(@(s) regexp(s, '^[A-Za-z]+', 'match'), species, 'UniformOutput', false);
    isonuclear_species = unique([temp{:}]);
end

species = cellfun(@(s) strrep(s, '+', ''), species, 'UniformOutput', false);
SIMULATION.species = species;
fprintf('Species: %s\n', strjoin(isonuclear_species, ', '));

if NREG(1) == 2
    SIMULATION.geometry_type = 'Limiter';
elseif NREG(1) == 4
    SN_type = detect_LSN_USN(SIMULATION);
    if strcmp(SN_type,'LSN')
        SIMULATION.geometry_type = 'Lower single null';
    elseif strcmp(SN_type,'USN')
        SIMULATION.geometry_type = 'Upper single null';
    end
elseif NREG(1) == 8 && (NREG(2) == 12 || NREG(2) == 26)
    SIMULATION.geometry_type = 'Connected double null';
elseif NREG(1) == 8 && (NREG(2) == 13 || NREG(2) == 27)
    SIMULATION.geometry_type = 'Disconnected double null';
elseif NREG(1) == 8 && (NREG(2) == 24)
    SN_type = detect_LSN_USN(SIMULATION);
    if strcmp(SN_type,'LSN')
        SIMULATION.geometry_type = 'Lower single null (CDN-like grid)';
    elseif strcmp(SN_type,'USN')
        SIMULATION.geometry_type = 'Upper single null (CDN-like grid)';
    end
elseif NREG(1) == 7
    SIMULATION.geometry_type = 'Snowflake';
end

if numel(NREG) == 1 || numel(NREG) == 3
    SIMULATION.grid_version = sprintf('Structured');
elseif numel(NREG) == 2
    SIMULATION.grid_version = sprintf('Unstructured');
end

if not(NREG(end) == 0)

    if NREG(1) == 2
        SIMULATION.volume_regions = [
        "+-------------------------------+" newline ...
        "|                               |" newline ...
        "|               2               |" newline ...
        "|                               |" newline ...
        "+/-----------------------------\+" newline ...
        "||                             ||" newline ...
        "||              1              ||" newline ...
        "||                             ||" newline ...
        "++-----------------------------++"
        ];
        SIMULATION.volume_regions_names{1} = 'Core';
        SIMULATION.volume_regions_names{2} = 'SOL';
        if numel(NREG) == 3
            SIMULATION.X_directed_regions = [
            "+-------------------------------+" newline ...
            "|                               |" newline ...
            "1                               2" newline ...
            "|                               |" newline ...
            "+/-----------------------------\+" newline ...
            "||                             ||" newline ...
            "||3                            ||" newline ...
            "||                             ||" newline ...
            "++-----------------------------++"
            ];
            SIMULATION.X_directed_regions_names{1} = 'Left target';
            SIMULATION.X_directed_regions_names{2} = 'Right target';
            SIMULATION.X_directed_regions_names{3} = 'Connection between core sides';
            SIMULATION.Y_directed_regions = [
            "+---------------3---------------+" newline ...
            "|                               |" newline ...
            "|                               |" newline ...
            "|                               |" newline ...
            "+/--------------2--------------\\+" newline ...
            "||                             ||" newline ...
            "||                             ||" newline ...
            "||                             ||" newline ...
            "++--------------1--------------++"
            ];
            SIMULATION.Y_directed_regions_names{1} = 'Core boundary';
            SIMULATION.Y_directed_regions_names{2} = 'Separatrix';
            SIMULATION.Y_directed_regions_names{3} = 'Main wall boundary';
        elseif numel(NREG) == 2
            SIMULATION.face_directed_regions = [
            "+---------------6---------------+" newline ...
            "|                               |" newline ...
            "1                               2" newline ...
            "|                               |" newline ...
            "+/--------------5--------------\\+" newline ...
            "||                             ||" newline ...
            "||3                            ||" newline ...
            "||                             ||" newline ...
            "++--------------4--------------++"
            ];
            SIMULATION.face_regions_names{1} = 'Left target';
            SIMULATION.face_regions_names{2} = 'Right target';
            SIMULATION.face_regions_names{3} = 'Connection between core sides';
            SIMULATION.face_regions_names{4} = 'Core boundary';
            SIMULATION.face_regions_names{5} = 'Separatrix';
            SIMULATION.face_regions_names{6} = 'Main wall boundary';
        end
    elseif NREG(1) == 4
        SIMULATION.volume_regions = [
        "+-------+---------------+-------+" newline ...
        "|       :               :       |" newline ...
        "|       :       2       :       |" newline ...
        "|       :               :       |" newline ...
        "|   3   +---------------+   4   |" newline ...
        "|       |               |       |" newline ...
        "|       |       1       |       |" newline ...
        "|       |               |       |" newline ...
        "+-------+---------------+-------+"
        ];
        if strcmp(SN_type,'LSN')
            SIMULATION.volume_regions_names{1} = 'Core';
            SIMULATION.volume_regions_names{2} = 'SOL';
            SIMULATION.volume_regions_names{3} = 'Inner divertor';
            SIMULATION.volume_regions_names{4} = 'Outer divertor';
        elseif strcmp(SN_type,'USN')
            SIMULATION.volume_regions_names{1} = 'Core';
            SIMULATION.volume_regions_names{2} = 'SOL';
            SIMULATION.volume_regions_names{3} = 'Outer divertor';
            SIMULATION.volume_regions_names{4} = 'Inner divertor';
        end
        if numel(NREG) == 3
            SIMULATION.X_directed_regions = [
            "+-------+---------------+-------+" newline ...
            "|       :               :       |" newline ...
            "|       2               3       |" newline ...
            "|       :               :       |" newline ...
            "1       +---------------+       4" newline ...
            "|       |               |       |" newline ...
            "|       |5              |6      |" newline ...
            "|       |               |       |" newline ...
            "+-------+---------------+-------+"
            ];
            if strcmp(SN_type,'LSN')
                SIMULATION.X_directed_regions_names{1} = 'Inner divertor target';
                SIMULATION.X_directed_regions_names{2} = 'Entrance to inner divertor';
                SIMULATION.X_directed_regions_names{3} = 'Entrance to outer divertor';
                SIMULATION.X_directed_regions_names{4} = 'Outer divertor target';
                SIMULATION.X_directed_regions_names{5} = 'Connection between core sides';
                SIMULATION.X_directed_regions_names{6} = 'Connection between bdivertor sides';
            elseif strcmp(SN_type,'USN')
                SIMULATION.X_directed_regions_names{1} = 'Outer divertor target';
                SIMULATION.X_directed_regions_names{2} = 'Entrance to outer divertor';
                SIMULATION.X_directed_regions_names{3} = 'Entrance to inner divertor';
                SIMULATION.X_directed_regions_names{4} = 'Inner divertor target';
                SIMULATION.X_directed_regions_names{5} = 'Connection between core sides';
                SIMULATION.X_directed_regions_names{6} = 'Connection between bdivertor sides';
            end
            SIMULATION.Y_directed_regions = [
            "+---5---+-------6-------+---7---+" newline ...
            "|       :               :       |" newline ...
            "|       :               :       |" newline ...
            "|       :               :       |" newline ...
            "|       +-------4-------+       |" newline ...
            "|       |               |       |" newline ...
            "|       |               |       |" newline ...
            "|       |               |       |" newline ...
            "+---1---+-------2-------+---3---+"
            ];
            if strcmp(SN_type,'LSN')
                SIMULATION.Y_directed_regions_names{1} = 'Inner PFR wall boundary';
                SIMULATION.Y_directed_regions_names{2} = 'Core boundary';
                SIMULATION.Y_directed_regions_names{3} = 'Outer PFR wall boundary';
                SIMULATION.Y_directed_regions_names{4} = 'Separatrix';
                SIMULATION.Y_directed_regions_names{5} = 'Inner divertor to main wall boundary';
                SIMULATION.Y_directed_regions_names{6} = 'Main wall boundary';
                SIMULATION.Y_directed_regions_names{7} = 'Outer divertor to main wall boundary';
            elseif strcmp(SN_type,'USN')
                SIMULATION.Y_directed_regions_names{1} = 'Outer PFR wall boundary';
                SIMULATION.Y_directed_regions_names{2} = 'Core boundary';
                SIMULATION.Y_directed_regions_names{3} = 'Inner PFR wall boundary';
                SIMULATION.Y_directed_regions_names{4} = 'Separatrix';
                SIMULATION.Y_directed_regions_names{5} = 'Outer divertor to main wall boundary';
                SIMULATION.Y_directed_regions_names{6} = 'Main wall boundary';
                SIMULATION.Y_directed_regions_names{7} = 'Inner divertor to main wall boundary';
            end
        elseif numel(NREG) == 2
            SIMULATION.face_directed_regions = [
            "+--11---+------12-------+--13---+" newline ...
            "|       :               :       |" newline ...
            "|       2               3       |" newline ...
            "|       :               :       |" newline ...
            "1       +------10-------+       4" newline ...
            "|       |               |       |" newline ...
            "|       |5              |6      |" newline ...
            "|       |               |       |" newline ...
            "+---7---+-------8-------+---9---+"
            ];
            if strcmp(SN_type,'LSN')
                SIMULATION.face_regions_names{1} = 'Inner divertor target';
                SIMULATION.face_regions_names{2} = 'Entrance to inner divertor';
                SIMULATION.face_regions_names{3} = 'Entrance to outer divertor';
                SIMULATION.face_regions_names{4} = 'Outer divertor target';
                SIMULATION.face_regions_names{5} = 'Connection between core sides';
                SIMULATION.face_regions_names{6} = 'Connection between divertor sides';
                SIMULATION.face_regions_names{7} = 'Inner PFR wall boundary';
                SIMULATION.face_regions_names{8} = 'Core boundary';
                SIMULATION.face_regions_names{9} = 'Outer PFR wall boundary';
                SIMULATION.face_regions_names{10} = 'Separatrix';
                SIMULATION.face_regions_names{11} = 'Inner divertor to main wall boundary';
                SIMULATION.face_regions_names{12} = 'Main wall boundary';
                SIMULATION.face_regions_names{13} = 'Outer divertor to main wall boundary';
            elseif strcmp(SN_type,'USN')
                SIMULATION.face_regions_names{1} = 'Outer divertor target';
                SIMULATION.face_regions_names{2} = 'Entrance to outer divertor';
                SIMULATION.face_regions_names{3} = 'Entrance to inner divertor';
                SIMULATION.face_regions_names{4} = 'Inner divertor target';
                SIMULATION.face_regions_names{5} = 'Connection between core sides';
                SIMULATION.face_regions_names{6} = 'Connection between bdivertor sides';
                SIMULATION.face_regions_names{7} = 'Outer PFR wall boundary';
                SIMULATION.face_regions_names{8} = 'Core boundary';
                SIMULATION.face_regions_names{9} = 'Inner PFR wall boundary';
                SIMULATION.face_regions_names{10} = 'Separatrix';
                SIMULATION.face_regions_names{11} = 'Outer divertor to main wall boundary';
                SIMULATION.face_regions_names{12} = 'Main wall boundary';
                SIMULATION.face_regions_names{13} = 'Inner divertor to main wall boundary';
            end
        end
    elseif NREG(1) == 8 && (NREG(2) == 12 || NREG(2) == 26)
        SIMULATION.volume_regions = [
        "+-------+---------------+-------++-------+---------------+-------+" newline ...
        "|       :               :       ||       :               :       |" newline ...
        "|       :       2       :       ||       :       6       :       |" newline ...
        "|       :               :       ||       :               :       |" newline ...
        "|   3   +---------------+   4   ||   7   +---------------+   8   |" newline ...
        "|       |               |       ||       |               |       |" newline ...
        "|       |       1       |       ||       |       5       |       |" newline ...
        "|       |               |       ||       |               |       |" newline ...
        "+-------+---------------+-------++-------+---------------+-------+"
        ];
        SIMULATION.volume_regions_names{1} = 'Left Core';
        SIMULATION.volume_regions_names{2} = 'Left SOL';
        SIMULATION.volume_regions_names{3} = 'Bottom inner divertor';
        SIMULATION.volume_regions_names{4} = 'Top inner divertor';
        SIMULATION.volume_regions_names{5} = 'Right Core';
        SIMULATION.volume_regions_names{6} = 'Right SOL';
        SIMULATION.volume_regions_names{7} = 'Top outer divertor';
        SIMULATION.volume_regions_names{8} = 'Bottom outer divertor';
        if numel(NREG) == 3
            SIMULATION.X_directed_regions = [
            "+-------+---------------+-------++-------+---------------+-------+" newline ...
            "|       :               :       ||       :               :       |" newline ...
            "|       2               3       ||       6               7       |" newline ...
            "|       :               :       ||       :               :       |" newline ...
            "1       +---------------+       45       +---------------+       8" newline ...
            "|       |               |       ||       |               |       |" newline ...
            "|       |9              |10     ||       |11             |12     |" newline ...
            "|       |               |       ||       |               |       |" newline ...
            "+-------+---------------+-------++-------+---------------+-------+"
            ];
            SIMULATION.X_directed_regions_names{1} = 'Bottom inner divertor target';
            SIMULATION.X_directed_regions_names{2} = 'Entrance to bottom inner divertor';
            SIMULATION.X_directed_regions_names{3} = 'Entrance to top inner divertor';
            SIMULATION.X_directed_regions_names{4} = 'Top inner divertor target';
            SIMULATION.X_directed_regions_names{5} = 'Top outer divertor target';
            SIMULATION.X_directed_regions_names{6} = 'Entrance to top outer divertor';
            SIMULATION.X_directed_regions_names{7} = 'Entrance to bottom outer divertor';
            SIMULATION.X_directed_regions_names{8} = 'Bottom outer divertor target';
            SIMULATION.X_directed_regions_names{9} = 'Connection between bottom inner and bottom outer core';
            SIMULATION.X_directed_regions_names{10} = 'Connection between top inner and top outer PFR';
            SIMULATION.X_directed_regions_names{11} = 'Connection between top outer and top inner core';
            SIMULATION.X_directed_regions_names{12} = 'Connection between bottom outer and bottom inner PFR';
            SIMULATION.Y_directed_regions = [
            "+---5---+-------6-------+---7---++--12---+------13-------+--14---+" newline ...
            "|       :               :       ||       :               :       |" newline ...
            "|       :               :       ||       :               :       |" newline ...
            "|       :               :       ||       :               :       |" newline ...
            "|       +-------4-------+       ||       +------11-------+       |" newline ...
            "|       |               |       ||       |               |       |" newline ...
            "|       |               |       ||       |               |       |" newline ...
            "|       |               |       ||       |               |       |" newline ...
            "+---1---+-------2-------+---3---++---8---+-------9-------+--10---+"
            ];
            SIMULATION.Y_directed_regions_names{1} = 'Bottom inner PFR wall boundary';
            SIMULATION.Y_directed_regions_names{2} = 'Left core boundary';
            SIMULATION.Y_directed_regions_names{3} = 'Top inner PFR wall boundary';
            SIMULATION.Y_directed_regions_names{4} = 'Left separatrix';
            SIMULATION.Y_directed_regions_names{5} = 'Bottom inner divertor main wall boundary';
            SIMULATION.Y_directed_regions_names{6} = 'Left SOL main wall boundary';
            SIMULATION.Y_directed_regions_names{7} = 'Top inner divertor main wall boundary';
            SIMULATION.Y_directed_regions_names{8} = 'Top outer PFR wall boundary';
            SIMULATION.Y_directed_regions_names{9} = 'Right core boundary';
            SIMULATION.Y_directed_regions_names{10} = 'Bottom outer PFR wall boundary';
            SIMULATION.Y_directed_regions_names{11} = 'Right separatrix';
            SIMULATION.Y_directed_regions_names{12} = 'Top outer divertor main wall boundary';
            SIMULATION.Y_directed_regions_names{13} = 'Right SOL main wall boundary';
            SIMULATION.Y_directed_regions_names{14} = 'Bottom outer divertor main wall boundary';
        elseif numel(NREG) == 2
            SIMULATION.face_regions = [
            "+---17---+------18------+---19---++---24---+------25------+---26---+" newline ...
            "|        :              :        ||        :              :        |" newline ...
            "|        2              3        ||        6              7        |" newline ...
            "|        :              :        ||        :              :        |" newline ...
            "1        +------16------+        45        +------23------+        8" newline ...
            "|        |              |        ||        |              |        |" newline ...
            "|        |9             |10      ||        |11            |12      |" newline ...
            "|        |              |        ||        |              |        |" newline ...
            "+---13---+------14------+---15---++---20---+------21------+---22---+"
            ];
            SIMULATION.face_regions_names{1} = 'Bottom inner divertor target';
            SIMULATION.face_regions_names{2} = 'Entrance to bottom inner divertor';
            SIMULATION.face_regions_names{3} = 'Entrance to top inner divertor';
            SIMULATION.face_regions_names{4} = 'Top inner divertor target';
            SIMULATION.face_regions_names{5} = 'Top outer divertor target';
            SIMULATION.face_regions_names{6} = 'Entrance to top outer divertor';
            SIMULATION.face_regions_names{7} = 'Entrance to bottom outer divertor';
            SIMULATION.face_regions_names{8} = 'Bottom outer divertor target';
            SIMULATION.face_regions_names{9} = 'Connection between bottom inner and bottom outer core';
            SIMULATION.face_regions_names{10} = 'Connection between top inner and top outer PFR';
            SIMULATION.face_regions_names{11} = 'Connection between top outer and top inner core';
            SIMULATION.face_regions_names{12} = 'Connection between bottom outer and bottom inner PFR';
            SIMULATION.face_regions_names{13} = 'Bottom inner PFR wall boundary';
            SIMULATION.face_regions_names{14} = 'Left core boundary';
            SIMULATION.face_regions_names{15} = 'Top inner PFR wall boundary';
            SIMULATION.face_regions_names{16} = 'Left separatrix';
            SIMULATION.face_regions_names{17} = 'Bottom inner divertor main wall boundary';
            SIMULATION.face_regions_names{18} = 'Left SOL main wall boundary';
            SIMULATION.face_regions_names{19} = 'Top inner divertor main wall boundary';
            SIMULATION.face_regions_names{20} = 'Top outer PFR wall boundary';
            SIMULATION.face_regions_names{21} = 'Right core boundary';
            SIMULATION.face_regions_names{22} = 'Bottom outer PFR wall boundary';
            SIMULATION.face_regions_names{23} = 'Right separatrix';
            SIMULATION.face_regions_names{24} = 'Top outer divertor main wall boundary';
            SIMULATION.face_regions_names{25} = 'Right SOL main wall boundary';
            SIMULATION.face_regions_names{26} = 'Bottom outer divertor main wall boundary';
        end
    elseif NREG(1) == 8 && (NREG(2) == 13 || NREG(2) == 27)
        SIMULATION.volume_regions = [
        "+-------+---------------+-------++-------+---------------+-------+" newline ...
        "|       :               :       ||       :               :       |" newline ...
        "|       :       2       :       ||       :       6       :       |" newline ...
        "|       :               +...4...||...7...+               :       |" newline ...
        "|       :               |       ||       |               :       |" newline ...
        "|...3...+---------------+       ||       +---------------+...8...|" newline ...
        "|       |       1       |       ||       |       5       |       |" newline ...
        "|       |               |       ||       |               |       |" newline ...
        "+-------+---------------+-------++-------+---------------+-------+"
        ];
        SIMULATION.volume_regions_names{1} = 'Left Core';
        SIMULATION.volume_regions_names{2} = 'Left SOL';
        SIMULATION.volume_regions_names{3} = 'Bottom inner divertor';
        SIMULATION.volume_regions_names{4} = 'Top inner divertor';
        SIMULATION.volume_regions_names{5} = 'Right Core';
        SIMULATION.volume_regions_names{6} = 'Right SOL';
        SIMULATION.volume_regions_names{7} = 'Top outer divertor';
        SIMULATION.volume_regions_names{8} = 'Bottom outer divertor';
        if numel(NREG) == 3
            SIMULATION.X_directed_regions = [
            "+--------+--------------+--------++--------+--------------+--------+" newline ...
            "|        :              :        ||        :              :        |" newline ...
            "|        2              3        ||        6              7        |" newline ...
            "|        :              +........45........+              :        |" newline ...
            "|        :              |        ||        |13            :        |" newline ...
            "1........+--------------+10      ||        +--------------+........8" newline ...
            "|        |9             |        ||        |11            |12      |" newline ...
            "|        |              |        ||        |              |        |" newline ...
            "+--------+--------------+--------++--------+--------------+--------+"
            ];
            SIMULATION.X_directed_regions_names{1} = 'Bottom inner divertor target';
            SIMULATION.X_directed_regions_names{2} = 'Entrance to bottom inner divertor';
            SIMULATION.X_directed_regions_names{3} = 'Entrance to top inner divertor';
            SIMULATION.X_directed_regions_names{4} = 'Top inner divertor target';
            SIMULATION.X_directed_regions_names{5} = 'Top outer divertor target';
            SIMULATION.X_directed_regions_names{6} = 'Entrance to top outer divertor';
            SIMULATION.X_directed_regions_names{7} = 'Entrance to bottom outer divertor';
            SIMULATION.X_directed_regions_names{8} = 'Bottom outer divertor target';
            SIMULATION.X_directed_regions_names{9} = 'Connection between bottom inner and bottom outer core';
            SIMULATION.X_directed_regions_names{10} = 'Connection between top inner and top outer PFR';
            SIMULATION.X_directed_regions_names{11} = 'Connection between top outer and top inner core';
            SIMULATION.X_directed_regions_names{12} = 'Connection between bottom outer and bottom inner PFR';
            SIMULATION.X_directed_regions_names{13} = 'Connection between right and left SOL';
            SIMULATION.Y_directed_regions = [
            "+---5---+-------6-------+---7---++--12---+------13-------+--14---+" newline ...
            "|       :               :       ||       :               :       |" newline ...
            "|       :               :       ||       :               :       |" newline ...
            "|       :               +.......||.......+               :       |" newline ...
            "|       :               |       ||       |               :       |" newline ...
            "|.......+-------4-------+       ||       +------11-------+.......|" newline ...
            "|       |               |       ||       |               |       |" newline ...
            "|       |               |       ||       |               |       |" newline ...
            "+---1---+-------2-------+---3---++---8---+-------9-------+--10---+"
            ];
            SIMULATION.Y_directed_regions_names{1} = 'Bottom inner PFR wall boundary';
            SIMULATION.Y_directed_regions_names{2} = 'Left core boundary';
            SIMULATION.Y_directed_regions_names{3} = 'Top inner PFR wall boundary';
            SIMULATION.Y_directed_regions_names{4} = 'Left separatrix';
            SIMULATION.Y_directed_regions_names{5} = 'Bottom inner divertor main wall boundary';
            SIMULATION.Y_directed_regions_names{6} = 'Left SOL main wall boundary';
            SIMULATION.Y_directed_regions_names{7} = 'Top inner divertor main wall boundary';
            SIMULATION.Y_directed_regions_names{8} = 'Top outer PFR wall boundary';
            SIMULATION.Y_directed_regions_names{9} = 'Right core boundary';
            SIMULATION.Y_directed_regions_names{10} = 'Bottom outer PFR wall boundary';
            SIMULATION.Y_directed_regions_names{11} = 'Right separatrix';
            SIMULATION.Y_directed_regions_names{12} = 'Top outer divertor main wall boundary';
            SIMULATION.Y_directed_regions_names{13} = 'Right SOL main wall boundary';
            SIMULATION.Y_directed_regions_names{14} = 'Bottom outer divertor main wall boundary';
        elseif numel(NREG) == 2
            SIMULATION.face_regions = [
            "+---18---+------19------+---20---++---25---+------26------+---27---+" newline ...
            "|        :              :        ||        :              :        |" newline ...
            "|        2              3        ||        6              7        |" newline ...
            "|        :              +........45........+              :        |" newline ...
            "|        :              |        ||        |13            :        |" newline ...
            "1........+------17------+10      ||        +------24------+........8" newline ...
            "|        |9             |        ||        |11            |12      |" newline ...
            "|        |              |        ||        |              |        |" newline ...
            "+---14---+------15------+---16---++---21---+------22------+---23---+"
            ];
            SIMULATION.face_regions_names{1} = 'Bottom inner divertor target';
            SIMULATION.face_regions_names{2} = 'Entrance to bottom inner divertor';
            SIMULATION.face_regions_names{3} = 'Entrance to top inner divertor';
            SIMULATION.face_regions_names{4} = 'Top inner divertor target';
            SIMULATION.face_regions_names{5} = 'Top outer divertor target';
            SIMULATION.face_regions_names{6} = 'Entrance to top outer divertor';
            SIMULATION.face_regions_names{7} = 'Entrance to bottom outer divertor';
            SIMULATION.face_regions_names{8} = 'Bottom outer divertor target';
            SIMULATION.face_regions_names{9} = 'Connection between bottom inner and bottom outer core';
            SIMULATION.face_regions_names{10} = 'Connection between top inner and top outer PFR';
            SIMULATION.face_regions_names{11} = 'Connection between top outer and top inner core';
            SIMULATION.face_regions_names{12} = 'Connection between bottom outer and bottom inner PFR';
            SIMULATION.face_regions_names{13} = 'Connection between right and left SOL';
            SIMULATION.face_regions_names{14} = 'Bottom inner PFR wall boundary';
            SIMULATION.face_regions_names{15} = 'Left core boundary';
            SIMULATION.face_regions_names{16} = 'Top inner PFR wall boundary';
            SIMULATION.face_regions_names{17} = 'Left separatrix';
            SIMULATION.face_regions_names{18} = 'Bottom inner divertor main wall boundary';
            SIMULATION.face_regions_names{19} = 'Left SOL main wall boundary';
            SIMULATION.face_regions_names{20} = 'Top inner divertor main wall boundary';
            SIMULATION.face_regions_names{21} = 'Top outer PFR wall boundary';
            SIMULATION.face_regions_names{22} = 'Right core boundary';
            SIMULATION.face_regions_names{23} = 'Bottom outer PFR wall boundary';
            SIMULATION.face_regions_names{24} = 'Right separatrix';
            SIMULATION.face_regions_names{25} = 'Top outer divertor main wall boundary';
            SIMULATION.face_regions_names{26} = 'Right SOL main wall boundary';
            SIMULATION.face_regions_names{27} = 'Bottom outer divertor main wall boundary';
        end
    elseif NREG(1) == 8 && (NREG(2) == 24)
        SIMULATION.volume_regions = [
        "+-------+---------------+---------------+-------+" newline ...
        "|       :               :               :       |" newline ...
        "|       :       2       :       6       :       |" newline ...
        "|       :               :               :       |" newline ...
        "|       :               :               :       |" newline ...
        "|...3...+---------------+---------------+...8...|" newline ...
        "|       |       1       :       5       |       |" newline ...
        "|       |               :               |       |" newline ...
        "+-------+---------------+---------------+-------+"
        ];
        if strcmp(SN_type,'LSN')
            SIMULATION.volume_regions_names{1} = 'Left Core';
            SIMULATION.volume_regions_names{2} = 'Left SOL';
            SIMULATION.volume_regions_names{3} = 'Inner divertor';
            SIMULATION.volume_regions_names{4} = '-';
            SIMULATION.volume_regions_names{5} = 'Right Core';
            SIMULATION.volume_regions_names{6} = 'Right SOL';
            SIMULATION.volume_regions_names{7} = '-';
            SIMULATION.volume_regions_names{8} = 'Outer divertor';
        elseif strcmp(SN_type,'USN')
            SIMULATION.volume_regions_names{1} = 'Right Core';
            SIMULATION.volume_regions_names{2} = 'Right SOL';
            SIMULATION.volume_regions_names{3} = 'Outer divertor';
            SIMULATION.volume_regions_names{4} = '-';
            SIMULATION.volume_regions_names{5} = 'Left Core';
            SIMULATION.volume_regions_names{6} = 'Left SOL';
            SIMULATION.volume_regions_names{7} = '-';
            SIMULATION.volume_regions_names{8} = 'Inner divertor';
        end
        if numel(NREG) == 2
            SIMULATION.face_regions = [
            "+--------4--------------+--------------5--------+" newline ...
            "|        :              :              :        |" newline ...
            "|        2              13             7        |" newline ...
            "|        :              +              :        |" newline ...
            "|        :              |              :        |" newline ...
            "1........+------17------+------24------+........8" newline ...
            "|        |9             |11            |12      |" newline ...
            "|        |              |              |        |" newline ...
            "+---14---+------15------+------22------+---23---+"
            ];
            if strcmp(SN_type,'LSN')
                SIMULATION.face_regions_names{1} = 'Inner divertor target';
                SIMULATION.face_regions_names{2} = 'Entrance to inner divertor';
                SIMULATION.face_regions_names{3} = '-';
                SIMULATION.face_regions_names{4} = 'Left SOL main wall boundary';
                SIMULATION.face_regions_names{5} = 'Right SOL main wall boundary';
                SIMULATION.face_regions_names{6} = '-';
                SIMULATION.face_regions_names{7} = 'Entrance to outer divertor';
                SIMULATION.face_regions_names{8} = 'Outer divertor target';
                SIMULATION.face_regions_names{9} = 'Connection between bottom inner and bottom outer core';
                SIMULATION.face_regions_names{10} = '-';
                SIMULATION.face_regions_names{11} = 'Connection between top outer and top inner core';
                SIMULATION.face_regions_names{12} = 'Connection between outer and inner PFR';
                SIMULATION.face_regions_names{13} = 'Connection between right and left SOL';
                SIMULATION.face_regions_names{14} = 'Inner PFR wall boundary';
                SIMULATION.face_regions_names{15} = 'Left core boundary';
                SIMULATION.face_regions_names{16} = '-';
                SIMULATION.face_regions_names{17} = 'Left separatrix';
                SIMULATION.face_regions_names{18} = '-';
                SIMULATION.face_regions_names{19} = '-';
                SIMULATION.face_regions_names{20} = '-';
                SIMULATION.face_regions_names{21} = '-';
                SIMULATION.face_regions_names{22} = 'Right core boundary';
                SIMULATION.face_regions_names{23} = 'Outer PFR wall boundary';
                SIMULATION.face_regions_names{24} = 'Right separatrix';
            elseif strcmp(SN_type,'USN')
                SIMULATION.face_regions_names{1} = 'Outer divertor target';
                SIMULATION.face_regions_names{2} = 'Entrance to outer divertor';
                SIMULATION.face_regions_names{3} = '-';
                SIMULATION.face_regions_names{4} = 'Right SOL main wall boundary';
                SIMULATION.face_regions_names{5} = 'Left SOL main wall boundary';
                SIMULATION.face_regions_names{6} = '-';
                SIMULATION.face_regions_names{7} = 'Entrance to inner divertor';
                SIMULATION.face_regions_names{8} = 'Inner divertor target';
                SIMULATION.face_regions_names{9} = 'Connection between top inner and top outer core';
                SIMULATION.face_regions_names{10} = '-';
                SIMULATION.face_regions_names{11} = 'Connection between bottom outer and bottom inner core';
                SIMULATION.face_regions_names{12} = 'Connection between outer and inner PFR';
                SIMULATION.face_regions_names{13} = 'Connection between right and left SOL';
                SIMULATION.face_regions_names{14} = 'Inner PFR wall boundary';
                SIMULATION.face_regions_names{15} = 'Right core boundary';
                SIMULATION.face_regions_names{16} = '-';
                SIMULATION.face_regions_names{17} = 'Right separatrix';
                SIMULATION.face_regions_names{18} = '-';
                SIMULATION.face_regions_names{19} = '-';
                SIMULATION.face_regions_names{20} = '-';
                SIMULATION.face_regions_names{21} = '-';
                SIMULATION.face_regions_names{22} = 'Left core boundary';
                SIMULATION.face_regions_names{23} = 'Outer PFR wall boundary';
                SIMULATION.face_regions_names{24} = 'Left separatrix';
            end
        end
    elseif NREG(1) == 7
        SIMULATION.volume_regions = [
        "+-------+-----------------------+-------+-------++-------+-------+" newline ...
        "|       :                       :       :       ||       :       |" newline ...
        "|       :           2           :       :       ||       :       |" newline ...
        "|       :                       :       +...5...||...6...+...7...|" newline ...
        "|       :                       :       |       ||       |       |" newline ...
        "|...3...+-----------------------+...4...+       ||       |       |" newline ...
        "|       |           1           |       |       ||       |       |" newline ...
        "|       |                       |       |       ||       |       |" newline ...
        "+-------+-----------------------+-------+-------++-------+-------+"
        ];
        SIMULATION.volume_regions_names{1} = 'Core';
        SIMULATION.volume_regions_names{2} = 'SOL';
        SIMULATION.volume_regions_names{3} = 'Inner divertor';
        SIMULATION.volume_regions_names{4} = 'Outer divertor entrance';
        SIMULATION.volume_regions_names{5} = 'Far SOL divertor leg';
        SIMULATION.volume_regions_names{6} = 'Secondary divertor leg';
        SIMULATION.volume_regions_names{7} = 'Primary divertor leg';
        if numel(NREG) == 3
            SIMULATION.X_directed_regions = [
            "+--------+----------------------+--------+--------++--------+--------+" newline ...
            "|        :                      :        :        ||        :        |" newline ...
            "|        2                      3        6        ||        7        |" newline ...
            "|        :                      :        +........45........+........|" newline ...
            "|        :                      :        |        ||        |13      |" newline ...
            "1........+----------------------+........+11      ||        +........8" newline ...
            "|        |9                     |10      |        ||        |12      |" newline ...
            "|        |                      |        |        ||        |        |" newline ...
            "+--------+----------------------+--------+--------++--------+--------+"
            ];
            SIMULATION.X_directed_regions_names{1} = 'Inner divertor target';
            SIMULATION.X_directed_regions_names{2} = 'Entrance to inner divertor';
            SIMULATION.X_directed_regions_names{3} = 'Entrance to outer divertor';
            SIMULATION.X_directed_regions_names{4} = 'Far SOL outer divertor target';
            SIMULATION.X_directed_regions_names{5} = 'Secondary outer divertor target';
            SIMULATION.X_directed_regions_names{6} = 'Entrance to far SOL outer divertor leg';
            SIMULATION.X_directed_regions_names{7} = 'Connection between secondary and primary outer divertor legs';
            SIMULATION.X_directed_regions_names{8} = 'Primary outer divertor target';
            SIMULATION.X_directed_regions_names{9} = 'Connection between left and right core';
            SIMULATION.X_directed_regions_names{10} = 'Connection between left and right primary PFRs';
            SIMULATION.X_directed_regions_names{11} = 'Connection between far SOL and secondary outer divertor legs';
            SIMULATION.X_directed_regions_names{12} = 'Connection between primary PFR and primary outer divertor leg';
            SIMULATION.X_directed_regions_names{13} = 'Connection between primary CFR and primary outer divertor leg';
            SIMULATION.Y_directed_regions = [
            "+---5---+-----------6-----------+---7---+--11---++--12---+---13--+" newline ...
            "|       :                       :       :       ||       :       |" newline ...
            "|       :                       :       :       ||       :       |" newline ...
            "|       :                       :       +.......||.......+.......|" newline ...
            "|       :                       :       |       ||       |       |" newline ...
            "|.......+-----------4-----------+.......+       ||       |       |" newline ...
            "|       |                       |       |       ||       |       |" newline ...
            "|       |                       |       |       ||       |       |" newline ...
            "+---1---+-----------2-----------+---3---+---8---++---9---+---10--+"
            ];
            SIMULATION.Y_directed_regions_names{1} = 'Inner PFR wall boundary';
            SIMULATION.Y_directed_regions_names{2} = 'Core boundary';
            SIMULATION.Y_directed_regions_names{3} = 'Outer divertor entrance PFR wall boundary';
            SIMULATION.Y_directed_regions_names{4} = 'Primary separatrix';
            SIMULATION.Y_directed_regions_names{5} = 'Inner divertor main wall boundary';
            SIMULATION.Y_directed_regions_names{6} = 'SOL main wall boundary';
            SIMULATION.Y_directed_regions_names{7} = 'Outer divertor entrance main wall boundary';
            SIMULATION.Y_directed_regions_names{8} = 'Far SOL outer PFR wall boundary';
            SIMULATION.Y_directed_regions_names{9} = 'Secondary outer PFR wall boundary';
            SIMULATION.Y_directed_regions_names{10} = 'Primary outer PFR wall boundary';
            SIMULATION.Y_directed_regions_names{11} = 'Far SOL outer divertor main wall boundary';
            SIMULATION.Y_directed_regions_names{12} = 'Secondary outer divertor main wall boundary';
            SIMULATION.Y_directed_regions_names{13} = 'Primary outer divertor main wall boundary';
        elseif numel(NREG) == 2
            SIMULATION.face_regions = [
            "+---18---+---------19-----------+---20---+---24---++---25---+---26---+" newline ...
            "|        :                      :        :        ||        :        |" newline ...
            "|        2                      3        6        ||        7        |" newline ...
            "|        :                      :        +........45........+........|" newline ...
            "|        :                      :        |        ||        |13      |" newline ...
            "1........+---------17-----------+........+11      ||        +........8" newline ...
            "|        |9                     |10      |        ||        |12      |" newline ...
            "|        |                      |        |        ||        |        |" newline ...
            "+---14---+---------15-----------+---16---+---21---++---22---+---23---+"
            ];
            SIMULATION.face_regions_names{1} = 'Inner divertor target';
            SIMULATION.face_regions_names{2} = 'Entrance to inner divertor';
            SIMULATION.face_regions_names{3} = 'Entrance to outer divertor';
            SIMULATION.face_regions_names{4} = 'Far SOL outer divertor target';
            SIMULATION.face_regions_names{5} = 'Secondary outer divertor target';
            SIMULATION.face_regions_names{6} = 'Entrance to far SOL outer divertor leg';
            SIMULATION.face_regions_names{7} = 'Connection between secondary and primary outer divertor legs';
            SIMULATION.face_regions_names{8} = 'Primary outer divertor target';
            SIMULATION.face_regions_names{9} = 'Connection between left and right core';
            SIMULATION.face_regions_names{10} = 'Connection between left and right primary PFRs';
            SIMULATION.face_regions_names{11} = 'Connection between far SOL and secondary outer divertor legs';
            SIMULATION.face_regions_names{12} = 'Connection between primary PFR and primary outer divertor leg';
            SIMULATION.face_regions_names{13} = 'Connection between primary CFR and primary outer divertor leg';
            SIMULATION.face_regions_names{4} = 'Inner PFR wall boundary';
            SIMULATION.face_regions_names{15} = 'Core boundary';
            SIMULATION.face_regions_names{16} = 'Outer divertor entrance PFR wall boundary';
            SIMULATION.face_regions_names{17} = 'Primary separatrix';
            SIMULATION.face_regions_names{18} = 'Inner divertor main wall boundary';
            SIMULATION.face_regions_names{19} = 'SOL main wall boundary';
            SIMULATION.face_regions_names{20} = 'Outer divertor entrance main wall boundary';
            SIMULATION.face_regions_names{21} = 'Far SOL outer PFR wall boundary';
            SIMULATION.face_regions_names{22} = 'Secondary outer PFR wall boundary';
            SIMULATION.face_regions_names{23} = 'Primary outer PFR wall boundary';
            SIMULATION.face_regions_names{24} = 'Far SOL outer divertor main wall boundary';
            SIMULATION.face_regions_names{25} = 'Secondary outer divertor main wall boundary';
            SIMULATION.face_regions_names{26} = 'Primary outer divertor main wall boundary';
        end
    end

end

fprintf('Geometry: %s (%s grid)\n', SIMULATION.geometry_type,SIMULATION.grid_version);

end
