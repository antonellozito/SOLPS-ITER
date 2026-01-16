function [info,PEC] = read_photon_emission_coefficients(varargin)
%
% read_photon_emission_coefficients calculates the photon emissivity for
% a [ne;Te] array for a specific process of a specific transition of a given
% ionization state of a specific atom, interpolating from the ADAS adf15 data
% Output is a struct "info" containing informations about the transition and the
% initial/final states, and a "PEC" vector corresponding to the input [ne;Te] array
%
% Syntax : read_photon_emission_coefficients(simulation,ne,Te,atom,ion_state,wavel,type,(prefix),(library))
%
%  simulation:   1st input: main simulation structure
%
%  ne:        2nd input: input array for the electron density
%
%  Te:        3rd input: input array for the electron temperature
%
%  atom:      4th input: defines the element whose data are requested
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
%  ion_state: 5th input: ionization state to be considered, which might be from 0 (neutral atom) to Z-1
%
%  wavel:     6th input: value (in angstrom) of the wavelenght emission of the desired transition
%
%  type:      7th input: type of process for which the PEC is requested
%             the options are:
%             - 'EXCIT': excitation processes
%             - 'RECOM': recombination processes
%             - 'CHEXC': charge-exchange processes
%
%  prefix:   8th input:  indicates the type of data file to be read
%             the options are:
%             - 'llu': low-level, metastable-unresolved
%             - 'llr': low-level, metastable-resolved
%             - 'pju': including projection matrices, metastable-unresolved
%             - 'pjr': including projection matrices, metastable-resolved
%             (Optional. If not specified, then the default type is loaded)
%
%  library:   9th input: version of the specific data file depending on the source of the data
%             (Optional. If not specified, then the default library is loaded)
%

SIMULATION = varargin{1};
ne = varargin{2};
Te = varargin{3};
atom = varargin{4};
ion_state = varargin{5};
wavel = varargin{6};
type = varargin{7};
if length(varargin) == 8 && ischar(varargin{8})
    prefix = varargin{8};
elseif length(varargin) == 8 && isnumeric(varargin{8})
    library = varargin{8};
elseif length(varargin) == 9
    prefix = varargin{8};
    library = varargin{9};
end

% Read the data file

if length(varargin) == 8 && ischar(varargin{8})
    data = read_adas_adf15(SIMULATION,atom,ion_state,prefix);
elseif length(varargin) == 8 && isnumeric(varargin{8})
    data = read_adas_adf15(SIMULATION,atom,ion_state,library);
elseif length(varargin) == 9
    data = read_adas_adf15(SIMULATION,atom,ion_state,prefix,library);
else
    data = read_adas_adf15(SIMULATION,atom,ion_state);
end

% Find the specific transition 

for i = 1:data.nsel
    if strcmp(data.data(i).type,type)
    diff(i) = abs(wavel-data.data(i).wavelength);
    else
        diff(i) = nan;
    end
end

% Find the index of the specific transition

[d,index] = min(diff);

% Read the info of the transition

info.wavelenght = data.data(index).wavelength;
info.transition = data.data(index).transition;
info.type = data.data(index).type;
info.unit = 'Ph m^3 s^-1';
info.initial_state = data.states(data.data(index).initial_state_index).name;
info.final_state = data.states(data.data(index).final_state_index).name;
info.initial_energy = data.states(data.data(index).initial_state_index).energy;
info.final_energy = data.states(data.data(index).final_state_index).energy;

% Extract the data

ne_adas = data.data(index).ne;
Te_adas = data.data(index).Te;
PEC_adas = data.data(index).PEC;

ne_adas_log = log10(ne_adas);
Te_adas_log = log10(Te_adas);
PEC_adas_log = log10(PEC_adas);

% [ne_interp_log,Te_interp_log,PEC_interp_log] = interp_ADAS_data(ne_adas_log,Te_adas_log,PEC_adas_log,200,200,order);
% 
% ne_interp = 10.^(ne_interp_log);
% Te_interp = 10.^(Te_interp_log);
% PEC_interp = 10.^(PEC_interp_log);

% Calculate the PEC for the input density/temperature points

PEC_table = struct;
PEC_table.logNe = ne_adas_log;
PEC_table.logT = Te_adas_log;
PEC_table.logdata = PEC_adas_log;

PEC = interp_ADAS_table(PEC_table, log10(ne), log10(Te), false, false);

% for i = 1:length(ne)
% 
% ne(i) = min(ne(i),ne_interp(end-1));
% 
% temp = max(ne_interp-ne(i),0);
% temp(temp == 0) = nan;
% [d,ne_index_upper] = min(temp);
% ne_index_lower = ne_index_upper - 1;
% 
% densities = [ne_interp(ne_index_lower) ne_interp(ne_index_upper)];
% for j = 1:length(Te_interp)
%     temp = [PEC_interp(ne_index_lower,j) PEC_interp(ne_index_upper,j)];
%     PEC_vector(j) = interp1(densities,temp,ne(i));
% end
% 
% Te(i) = min(Te(i),Te_interp(end-1));
% 
% temp = max(Te_interp-Te(i),0);
% temp(temp == 0) = nan;
% [d,Te_index_upper] = min(temp);
% Te_index_lower = Te_index_upper - 1;
% 
% temperatures = [Te_interp(Te_index_lower) Te_interp(Te_index_upper)];
% temp = [PEC_vector(Te_index_lower) PEC_vector(Te_index_upper)];
% PEC(i) = interp1(temperatures,temp,Te(i));
% 
% end

end
