function coeff = read_adas_adf11(varargin)
%
% read_adas_adf11 reads the collisional-radiative coefficients
% for various atoms from the ADAS adf11 database
% Output is a struct "coeff" containing information and coefficients
% for all the ionization stages of a specific atom, for the given
% desired coefficient
%
% Syntax : read_adas_adf11(simulation,atom,prefix,(library))
%
%  simulation:   1st input: main simulation structure
%
%  atom:      2nd input: defines the element whose data are requested
%             the options are:
%             - 'h': hydrogen (libraries: 89, 93, 96)
%             - 'he': helium (libraries: 89, 96)
%             - 'li': lithium (libraries: 89, 96)
%             - 'be': berillium (libraries: 89, 93, 96)
%             - 'b': boron (libraries: 89)
%             - 'c': carbon (libraries: 89, 93, 96)
%             - 'n': nitrogen (libraries: 89, 96)
%             - 'o': oxygen (libraries: 89, 93, 96)
%             - 'f': fluorine (libraries: 89)
%             - 'ne': neon (libraries: 89, 96)
%             - 'al': aluminium (libraries: 89)
%             - 'si': silicon (libraries: 89, 96)
%             - 's': sulfur (libraries: 89)
%             - 'cl': chlorine (libraries: 89)
%             - 'ar': argon (libraries: 89)
%             - 'cr': chromium (libraries: 89)
%             - 'fe': iron (libraries: 89, 93)
%             - 'ni': nickel (libraries: 89)
%             - 'cu': copper (libraries: 89)
%             - 'ge': germanium (libraries: 89)
%             - 'kr': krypton (libraries: 89)
%             - 'mo': molybdenum (libraries: 89)
%             - 'sn': tin (libraries: 89)
%             - 'xe': xenon (libraries: 89)
%             - 'w': tungsten (libraries: 89)
%
%  prefix:    3rd input: indicates the type of data file to be read
%             the options are:
%             - 'scd': effective ionization coefficients
%             - 'acd': effective recombination coefficients
%             - 'ccd': effective charge-exchange-recombination coefficients (with hydrogen)
%             - 'plt': line power driven by excitation
%             - 'prb': continuum and line power driven by recombination and bremsstrahlung
%             - 'prc': line power due to charge-exchange (with hydrogen)
%
%  library:   4th input: version of the specific data file depending on the source of the data
%             (Optional. If not specified, then the default library is loaded)
%
%% PRELIMINARY OPERATIONS

% Find the adf11 folder

SIMULATION = varargin{1};
adf11_folder = sprintf('%s/adf11',SIMULATION.ADAS_DATABASE);

% Desired species and reaction

atom = varargin{2};
prefix = varargin{3};

% Desired library (explicit or default)

if length(varargin) == 4
    library = varargin{4};
else
    adf11_default_libraries = load_filelist_adas_adf11(SIMULATION);
    index = find(ismember({adf11_default_libraries.(prefix).atom},atom));
    library = adf11_default_libraries.(prefix)(index).library;
end

% Open the desired library

data_folder = sprintf('%s/%s%d',adf11_folder,prefix,library);
if ~isfolder(data_folder)
    error('Error: The library ''%s%d'' from the ADAS adf11 datafiles does not exist',prefix,library);
end

% Load the desired datafile

data_file = sprintf('%s/%s%d_%s.dat',data_folder,prefix,library,atom);
if ~isfile(data_file)
    error('Error: The ADAS adf11 datafile %s%d_%s.dat from the library ''%s%d'' does not exist',prefix,library,atom,prefix,library);
end

fid = fopen(data_file);

%% READ THE DATA

% Read the header and the number of transitions

switch prefix
    case 'scd'
        coeff.type = 'effective ionization coefficients';
    case 'acd'
        coeff.type = 'effective recombination coefficients';
    case 'ccd'
        coeff.type = 'effective charge-exchange-recombination coefficients (with hydrogen)';
    case 'plt'
        coeff.type = 'line power driven by excitation';
    case 'prb'
        coeff.type = 'continuum and line power driven by recombination and bremsstrahlung';
    case 'prc'
        coeff.type = 'line power due to charge-exchange (with hydrogen)';
end

line = fgetl(fid);
header = textscan(line,'%d%d %d %d %d /%s /%s');
coeff.species = header{6}{1};
coeff.Z = header{1}(1);
Z_max = header{5};
ndens = header{2};
nte = header{3};
coeff.data = struct;
line = fgetl(fid);

% Read the density points
logne = fscanf(fid,'%e',ndens);
ne = (10.^logne).*1e6;

% Read the temperature points
logTe = fscanf(fid,'%e',nte);
Te = (10.^logTe);

line = fgetl(fid);

for state = 1:Z_max

% Read the main informations for each state

line = fgetl(fid);
z1 = state;

coeff.data(state).ionizing_state_index = z1-1;
coeff.data(state).recombining_state_index = z1;
coeff.data(state).ionizing_state_index = z1-1;
coeff.data(state).recombining_state_index = z1;
coeff.data(state).ne = ne;
coeff.data(state).Te = Te;

% Read the data grid
for j = 1:nte
    logdata(:,j) = fscanf(fid,'%e',ndens);
end
coeff.data(state).(prefix) = (10.^logdata).*1e-6;

line = fgetl(fid);

end

fprintf('ADAS adf11 datafile %s%d_%s.dat from the library ''%s%d'' read.\n',prefix,library,atom,prefix,library);

%% CLOSE THE FILE

fclose(fid);

end