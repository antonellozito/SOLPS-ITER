function [info,coeff] = read_atomic_reactions_coefficients(varargin)
%
% read_atomic_reactions_coefficients calculates the atomic reactions
% coefficients, from the collisional-radiative model, for a [ne;Te] array
% for a specific reaction of a specific ionization state of
% a given of a specific atom, interpolating from the ADAS adf11 data
% Output is a struct "info" containing informations about the reaction,
% and a "coeff" vector corresponding to the input [ne;Te] array
%
% Syntax : read_atomic_reactions_coefficients(simulation,ne,Te,atom,ion_state,prefix,(library))
%
%  simulation:   1st input: main simulation structure
%
%  ne:        2nd input: input array for the electron density
%
%  Te:        3rd input: input array for the electron temperature
%
%  atom:      4th input: defines the element whose data are requested
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
%  ion_state: 5th input: ionization state to be considered, which might be from 0 (neutral atom) to Z-1
%
%  prefix:    6th input: indicates the type of data file to be read
%             the options are:
%             - 'scd': effective ionization coefficients
%             - 'acd': effective recombination coefficients
%             - 'ccd': effective charge-exchange-recombination coefficients (with hydrogen)
%
%  library:   7th input: version of the specific data file depending on the source of the data
%             (Optional. If not specified, then the default library is loaded)
%

SIMULATION = varargin{1};
ne = varargin{2};
Te = varargin{3};
atom = varargin{4};
ion_state = varargin{5};
prefix = varargin{6};
if length(varargin) == 7
    library = varargin{7};
end

% Read the data file

if length(varargin) == 7
    data = read_adas_adf11(SIMULATION,atom,prefix,library);
else
    data = read_adas_adf11(SIMULATION,atom,prefix);
end

% Read the info of the reaction

info.type = data.type;
info.unit = 'm^3 s^-1';
info.species = data.species;
info.ionizing_state_index = data.data(ion_state+1).ionizing_state_index;
info.recombining_state_index = data.data(ion_state+1).recombining_state_index;

% Extract the data

ne_adas = data.data(ion_state+1).ne;
Te_adas = data.data(ion_state+1).Te;
coeff_adas = data.data(ion_state+1).(prefix);

ne_adas_log = log10(ne_adas);
Te_adas_log = log10(Te_adas);
coeff_adas_log = log10(coeff_adas);

% [ne_interp_log,Te_interp_log,coeff_interp_log] = interp_ADAS_data(ne_adas_log,Te_adas_log,coeff_adas_log,200,200,order);
% 
% ne_interp = 10.^(ne_interp_log);
% Te_interp = 10.^(Te_interp_log);
% coeff_interp = 10.^(coeff_interp_log);

% Calculate the coefficients for the input density/temperature points

atom_table = struct;
atom_table.logNe = ne_adas_log;
atom_table.logT = Te_adas_log;
atom_table.logdata = coeff_adas_log;

coeff = interp_ADAS_table(atom_table, log10(ne), log10(Te), false, false);

end
