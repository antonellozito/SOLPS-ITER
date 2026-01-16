function PEC = read_adas_adf15(varargin)
%
% read_adas_adf15 reads the photon emissivity coefficients
% for various atoms from the ADAS adf15 database
% Output is a struct "PEC" containing information and coefficients
% for all the transitions for a specific ionization state of a
% specific atom, metastable-resolved or -unresolved
%
% Syntax : read_adas_adf15(atom,ion_state,(prefix),(library))
%
%  simulation:   1st input: main simulation structure
%
%  atom:      2nd input: defines the element whose data are requested
%             the options are:
%             - 'h': hydrogen (libraries: 96)
%             - 'he': helium (libraries: 93, 96)
%             - 'li': lithium (libraries: 96)
%             - 'be': berillium (libraries: 93, 96)
%             - 'b': boron (libraries: 93)
%             - 'c': carbon (libraries: 93, 96)
%             - 'n': nitrogen (libraries: 93, 96)
%             - 'o': oxygen (libraries: 93, 96)
%             - 'ne': neon (libraries: 96)
%             - 'si': silicon (libraries: 96)
%             - 'cr': chromium (libraries: 93)
%             - 'mo': molybdenum (libraries: 93)
%
%  ion_state: 3rd input: ionization state to be considered, which might be from 0 (neutral atom) to Z-1
%
%  prefix:    4th input: indicates the type of data file to be read
%             the options are:
%             - 'llu': low-level, metastable-unresolved
%             - 'llr': low-level, metastable-resolved
%             - 'pju': including projection matrices, metastable-unresolved
%             - 'pjr': including projection matrices, metastable-
%             (Optional. If not specified, then the default type is loaded)
%
%  library:   5th input: version of the specific data file depending on the source of the data
%             (Optional. If not specified, then the default library is loaded)
%
%% PRELIMINARY OPERATIONS

% Find the adf15 folder

SIMULATION = varargin{1};
adf15_folder = sprintf('%s/adf15',SIMULATION.ADAS_DATABASE);

% Desired species and ion state

atom = varargin{2};
ion_state = varargin{3};

% Desired type and library (explicit or default)

adf15_default_libraries = load_filelist_adas_adf15(SIMULATION);
index = find(ismember({adf15_default_libraries.atom},atom));

if length(varargin) == 4 && ischar(varargin{4})
    prefix = varargin{4};
    library = adf15_default_libraries(index).library;
elseif length(varargin) == 4 && isnumeric(varargin{4})
    prefix = adf15_default_libraries(index).prefix;
    library = varargin{4};
elseif length(varargin) == 5
    prefix = varargin{4};
    library = varargin{5};
else
    prefix = adf15_default_libraries(index).prefix;
    library = adf15_default_libraries(index).library;
end

% Open the desired library

data_folder = sprintf('%s/pec%d#%s',adf15_folder,library,atom);
if ~isfolder(data_folder)
    error('Error: The library ''pec%d'' from the ADAS adf15 datafiles for the atom ''%s'' does not exist',library,atom);
end

% Load the desired datafile

data_file = sprintf('%s/pec%d#%s_%s#%s%d.dat',data_folder,library,atom,prefix,atom,ion_state);
if ~isfile(data_file)
    error('Error: The ADAS adf15 datafile %s#%s%d.dat from the library ''pec%d'' does not exist',prefix,atom,ion_state,library);
end

fid = fopen(data_file);

%% READ THE DATA

% Read the header and the number of transitions

line = fgetl(fid);
if ~strcmp(atom,'h')
header = textscan(line,' %5d  /%36c/');
else
header = textscan(line,' %5d  /%37c/');
end
PEC.species = header{2};
PEC.nsel = header{1};
PEC.data = struct;
if library == 96
    if ~strcmp(atom,'h')
        PEC.states = struct;
    end
end

for isel = 1:PEC.nsel

% Read the main informations for each transition

line = fgetl(fid);
if strcmp(atom,'h')
    info = textscan(line,'%.1fA%4d%4d/FILMEM =%7c/TYPE =%8c/INDM =%d/ISEL =%5d');
else
    info = textscan(line,'%.1fA%4d%4d/FILMEM =%8c/TYPE =%8c/INDM =%d/ISEL =%5d');
end
wavel = info{1};
ndens = info{2};
nte = info{3};
filemem = strtrim(info{4});
type = strtrim(info{5});
indm = info{6};
isel_data = info{7};

PEC.data(isel).initial_state_index = [];
PEC.data(isel).final_state_index = [];
PEC.data(isel).wavelength = wavel;
PEC.data(isel).transition = [];
PEC.data(isel).type = type;
if ((strcmp(prefix,'llr') || strcmp(prefix,'pjr'))) && ~strcmp(atom,'h')
    PEC.data(isel).metastable_state = [];
    if strcmp(type,'EXCIT')
        PEC.data(isel).imet = indm;
        PEC.data(isel).ip = [];
    elseif (strcmp(type,'RECOM') || strcmp(type,'CHEXC'))
        PEC.data(isel).imet = [];
        PEC.data(isel).ip = indm;
    end
end

% Read the density points
PEC.data(isel).ne = fscanf(fid,'%e',ndens);
PEC.data(isel).ne = PEC.data(isel).ne.*1e6;

% Read the temperature points
PEC.data(isel).Te = fscanf(fid,'%e',nte);

% Read the PEC grid
for j = 1:ndens
    PEC.data(isel).PEC(j,:) = fscanf(fid,'%e',nte);
end
PEC.data(isel).PEC = PEC.data(isel).PEC.*1e-6;

line = fgetl(fid);

end

%% READ THE STATE DETAILS

if library == 96

while ~contains(line,'Configuration')
    line = fgetl(fid);
end
line = fgetl(fid);

while ~strcmp(line,'C')
    index = str2num(line(5:7));
    name = line(11:26);
    configuration = line(32:41);
    energy = str2double(line(42:end));
    PEC.states(index).name = strtrim(name);
    PEC.states(index).configuration = configuration;
    PEC.states(index).energy = energy * 100 * (1/8.065543e5);
    line = fgetl(fid);
end

end

%% READ THE TRANSITION DETAILS

if strcmp(atom,'h')

while ~contains(line,'PHOTON EMISSIVITY COEFFICIENT LIST:')
    line = fgetl(fid);
end
line = fgetl(fid);
line = fgetl(fid);
line = fgetl(fid);
line = fgetl(fid);

for isel = 1:PEC.nsel
    transition = line(32:42);
    state_index_1 = str2num(line(34:35));
    state_configuration_1 = line(32:35);
    state_index_2 = str2num(line(41:42));
    state_configuration_2 = line(39:42);
    PEC.data(isel).initial_state_index = state_index_1;
    PEC.data(isel).final_state_index = state_index_2;
    PEC.data(isel).transition = transition;
    line = fgetl(fid);
end

else

while ~strcmp(line,'C  ISEL  WAVELENGTH      TRANSITION            TYPE    METASTABLE  IMET NMET  IP')
    line = fgetl(fid);
end
line = fgetl(fid);
line = fgetl(fid);

for isel = 1:PEC.nsel
    transition = line(21:45);
    state_index_1 = str2num(transition(1:2));
    state_configuration_1 = transition(3:12);
    state_index_2 = str2num(transition(14:15));
    state_configuration_2 = transition(16:25);
    if ((strcmp(prefix,'llr') || strcmp(prefix,'pjr'))) && strcmp(line(48:52),'EXCIT')
        PEC.data(isel).metastable_state = line(56:66);
    end
    PEC.data(isel).initial_state_index = state_index_1;
    PEC.data(isel).final_state_index = state_index_2;
    PEC.data(isel).transition = sprintf('%s --> %s',state_configuration_1,state_configuration_2);
    line = fgetl(fid);
end

end

fprintf('ADAS adf15 datafile %s#%s%d.dat from the library ''pec%d'' read.\n',prefix,atom,ion_state,library);

%% CLOSE THE FILE

fclose(fid);

end
