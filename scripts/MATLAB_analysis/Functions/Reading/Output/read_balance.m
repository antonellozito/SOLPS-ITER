function output = read_balance(varargin)
%
% read_balance reads the balance.nc file created by B2.5
% Output is the structs "fluxes" and "sources" with all the flux and source fields in the balance.nc file
%
% 1st input: main simulation structure
%
% Following inputs: strings which specify which subsets of fields
%                   should be read:
%                   - 'STATE'
%                   - 'FLUXES'
%                   - 'SOURCES'
%                   - 'RESIDUALS'

%% PRELIMINARY OPERATIONS

% Load the file

simulation = varargin{1};

index = find(contains({simulation.run.name},'balance.nc'));
if isempty(index)
   error('Error: balance.nc not found');
end
file = simulation.run(index).file;
fid = fopen(file);
if (fid == -1)
   error('Error: balance.nc not found');
end

% Select which group of fields to read

READ_STATE = false;
READ_FLUXES = false;
READ_SOURCES = false;
READ_RESIDUALS = false;
if numel(varargin) == 1
    READ_STATE = true;
    READ_FLUXES = true;
    READ_SOURCES = true;
    READ_RESIDUALS = true;
else
    if any(strcmp(varargin,'STATE'))
        READ_STATE = true;
    end
    if any(strcmp(varargin,'FLUXES'))
        READ_FLUXES = true;  
    end
    if any(strcmp(varargin,'SOURCES'))
        READ_SOURCES = true;
    end
    if any(strcmp(varargin,'RESIDUALS'))
        READ_RESIDUALS = true;  
    end
end

%% READ THE STATE VARIABLES

if READ_STATE

output.nx = size(ncread(file,'na'),1) - 2;
output.ny = size(ncread(file,'na'),2) - 2;
output.ns = size(ncread(file,'na'),3);

temp = ncread(file,'species');
output.species = {};
for i=1:output.ns
    output.species{i} = strtrim(temp(:,i)');
end

output.na = ncread(file,'na');                                     % atomic density for each species, m^-3
output.ne = ncread(file,'ne');                                     % electron density, m^-3

output.ua = ncread(file,'ua');                                     % parallel velocity, m s^-1

Te = ncread(file,'te');                                                     % electron temperature, J
output.Te(:,:)        = Te.*6.242e18;                              % electron temperature, eV

Ti = ncread(file,'ti');                                                     % ion temperature, J
output.Ti(:,:)        = Ti.*6.242e18;                              % ion temperature, eV

output.po = ncread(file,'po');                                     % electric potential, V

output.n_atm = ncread(file,'dab2');                                % atomic density, m^-3
output.n_atm(end,:) = []; output.n_atm(end,:) = [];
output.T_atm = ncread(file,'tab2');                                % atomic temperature, eV
output.T_atm(end,:) = []; output.T_atm(end,:) = [];
output.n_mol = ncread(file,'dmb2');                                % molecular density, m^-3
output.n_mol(end,:) = []; output.n_mol(end,:) = [];
output.T_mol = ncread(file,'tmb2');                                % molecular temperature, eV
output.T_mol(end,:) = []; output.T_mol(end,:) = [];

output.fn_atm_y = ncread(file,'rfluxa');                           % atomic radial flux density, m^-2 s^-1
output.fn_atm_y(end,:) = []; output.fn_atm_y(end,:) = [];
output.fn_mol_y = ncread(file,'rfluxm');                           % molecular radial flux density, m^-2 s^-1
output.fn_mol_y(end,:) = []; output.fn_mol_y(end,:) = [];
output.fn_atm_x = ncread(file,'pfluxa');                           % atomic poloidal flux density, m^-2 s^-1
output.fn_atm_x(end,:) = []; output.fn_atm_x(end,:) = [];
output.fn_mol_x = ncread(file,'pfluxm');                           % molecular poloidal flux density, m^-2 s^-1
output.fn_mol_x(end,:) = []; output.fn_mol_x(end,:) = [];
output.fe_atm_y = ncread(file,'refluxa');                          % atomic radial energy flux density, W m^-2
output.fe_atm_y(end,:) = []; output.fe_atm_y(end,:) = [];
output.fe_mol_y = ncread(file,'refluxm');                          % molecular radial energy flux density, W m^-2
output.fe_mol_y(end,:) = []; output.fe_mol_y(end,:) = [];
output.fe_atm_x = ncread(file,'pefluxa');                          % atomic poloidal energy flux density, W m^-2
output.fe_atm_x(end,:) = []; output.fe_atm_x(end,:) = [];
output.fe_mol_x = ncread(file,'pefluxm');                          % molecular poloidal energy flux density, W m^-2
output.fe_mol_x(end,:) = []; output.fe_mol_x(end,:) = [];

fprintf('State variables from balance.nc read\n');

end

%% READ THE FLUXES

if READ_FLUXES

% Particle fluxes from B2.5

output.fna_pll = ncread(file,'fna_pll');                     % parallel convection component, s^-1
output.fna_pinch = ncread(file,'fna_pinch');                 % anomalous pinch velocity component, s^-1
output.fna_drift = ncread(file,'fna_drift');                 % drift-related flux component, s^-1
output.fna_ch = ncread(file,'fna_ch');                       % current-related flux component, s^-1
output.fna_nanom = ncread(file,'fna_nanom');                 % anomalous density diffusion flux component, s^-1
output.fna_panom = ncread(file,'fna_panom');                 % anomalous pressure diffusion flux component, s^-1
output.fna_pschused = ncread(file,'fna_pschused');           % pfirsch-schlueter flux component, s^-1
output.fna_tot = ncread(file,'fna_tot');                     % total flux, s^-1

% Momentum fluxes from B2.5

output.fmo_flua = ncread(file,'fmo_flua');                   % convected flux, N
output.fmo_cvsa = ncread(file,'fmo_cvsa');                   % viscous flux, N
output.fmo_hybr = ncread(file,'fmo_hybr');                   % viscous flux, hybrid part, N
output.fmo_b2nxfv = ncread(file,'fmo_b2nxfv');               % correction term, N
output.fmo_tot = ncread(file,'fmo_tot');                     % total flux, N
output.pstat_bal = ncread(file,'b2sigp_pstat_bal');          % total static pressure
output.pstati_bal = ncread(file,'b2sigp_pstati_bal');        % ion static pressure
output.pstate_bal = ncread(file,'b2sigp_pstate_bal');        % electron static pressure

% Electron energy fluxes from B2.5

output.fhe_32   = ncread(file,'fhe_32');             % parallel convection + diffusive flux, W
output.fhe_52   = ncread(file,'fhe_52');             % 5/2 component flux, W
output.fhe_ecrb   = ncread(file,'fhe_ecrb');         % ExB-drift-related flux, W
output.fhe_dia   = ncread(file,'fhe_dia');           % diamagnetic-drift-related flux, W
output.fhe_thermj   = ncread(file,'fhe_thermj');     % current-related flux, W
output.fhe_pschused   = ncread(file,'fhe_pschused'); % pfirsch-schlueter flux component, W
output.fhe_cond   = ncread(file,'fhe_cond');         % conductive flux, W

% Ion energy fluxes from B2.5

output.fhi_32   = ncread(file,'fhi_32');              % parallel convection + diffusive flux, W
output.fhi_52   = ncread(file,'fhi_52');              % 5/2 component flux, W
output.fhi_ecrb   = ncread(file,'fhi_ecrb');          % ExB-drift-related flux, W
output.fhi_dia   = ncread(file,'fhi_dia');            % diamagnetic-drift-related flux, W
output.fhi_pschused   = ncread(file,'fhi_pschused'); % pfirsch-schlueter flux component, W
output.fhi_inert   = ncread(file,'fhi_inert');        % inertial-current-related flux, W
output.fhi_vispar   = ncread(file,'fhi_vispar');      % parallel-viscosity-current-related flux, W
output.fhi_visper   = ncread(file,'fhi_visper');      % perpendicular-viscosity-current-related flux, W
output.fhi_visq   = ncread(file,'fhi_visq');          % ...-viscosity-current-related flux, W
output.fhi_anml   = ncread(file,'fhi_anml');          % anomalous-current-related flux, W
output.fhi_kevis   = ncread(file,'fhi_kevis');        % kinetic energy flux, W
output.fhi_cond   = ncread(file,'fhi_cond');          % conductive flux, W

% Others

output.za   = ncread(file,'za');            % 
output.kinrgy   = ncread(file,'kinrgy');    % 
output.rpt   = ncread(file,'rpt');          % 
output.fne   = ncread(file,'fne');          % 

fprintf('Fluxes from balance.nc read\n');

end

%% READ THE SOURCES

if READ_SOURCES

% Particle sources from B2.5

output.b2stel_sna_ion           = ncread(file,'b2stel_sna_ion_bal');          % ionization source, s^-1

output.b2stel_sna_rec           = ncread(file,'b2stel_sna_rec_bal');          % recombination source, s^-1

output.b2stcx_sna               = ncread(file,'b2stcx_sna_bal');              % charge-exchange source, s^-1

output.b2stbc_sna               = ncread(file,'b2stbc_sna_bal');              % boundary source, s^-1

output.b2stbr_phys_sna          = ncread(file,'b2stbr_phys_sna_bal');         % recycling sources, s^-1
try
output.b2stbr_bas_sna           = ncread(file,'b2stbr_bas_sna_bal');
catch
end
output.b2stbr_first_flight_sna  = ncread(file,'b2stbr_first_flight_sna_bal');

output.b2stbm_sna               = ncread(file,'b2stbm_sna_bal');              % additional + external sources, s^-1
output.ext_sna                  = ncread(file,'ext_sna_bal');

output.b2srdt_snal              = ncread(file,'b2srdt_sna_bal');              % numerics sources, s^-1
output.b2srsm_sna               = ncread(file,'b2srsm_sna_bal');
output.b2srst_sna               = ncread(file,'b2srst_sna_bal');

% Momentum sources from B2.5

output.b2sigp_smogpi     = ncread(file,'b2sigp_smogpi_bal');     % static pressure gradients, N
output.b2sigp_smogpe     = ncread(file,'b2sigp_smogpe_bal');
output.b2sigp_smogp      = ncread(file,'b2sigp_smogp_bal');

output.b2stel_smq_ion    = ncread(file,'b2stel_smq_ion_bal');    % ionization source, N

output.b2stel_smq_rec    = ncread(file,'b2stel_smq_rec_bal');    % recombination source, N

output.b2stcx_smq        = ncread(file,'b2stcx_smq_bal');        % charge-exhange source, N

output.b2sifr_smoch      = ncread(file,'b2sifr_smoch_bal');      % friction force (b2sigp_style=='1'), N

output.b2sifr_smotf_ehxp = ncread(file,'b2sifr_smotf_ehxp_bal'); % thermal forces (b2sigp_style=='1'), N
output.b2sifr_smotf_cthe = ncread(file,'b2sifr_smotf_cthe_bal');
output.b2sifr_smotf_cthi = ncread(file,'b2sifr_smotf_cthi_bal');

output.b2sifr_smofrea    = ncread(file,'b2sifr_smofrea_bal');    % friction forces (b2sigp_style=='2'), N
output.b2sifr_smofria    = ncread(file,'b2sifr_smofria_bal');

output.b2sifr_smotfea    = ncread(file,'b2sifr_smotfea_bal');    % thermal forces (b2sigp_style=='2'), N
output.b2sifr_smotfia    = ncread(file,'b2sifr_smotfia_bal');

output.b2siav_smovh      = ncread(file,'b2siav_smovh_bal');      % additional viscosity source, N
output.b2siav_smovv      = ncread(file,'b2siav_smovv_bal');

output.b2sicf_smo        = ncread(file,'b2sicf_smo_bal');        % other sorces, N
output.b2sian_smo        = ncread(file,'b2sian_smo_bal');
output.b2nxdv_smo        = ncread(file,'b2nxdv_smo_bal');

output.b2stbc_smo        = ncread(file,'b2stbc_smo_bal');        % boundary source, N

output.b2stbr_phys_smo   = ncread(file,'b2stbr_phys_smo_bal');   % recycling sources, N
try
output.b2stbr_bas_smo    = ncread(file,'b2stbr_bas_smo_bal');
catch
end

output.b2stbm_smo        = ncread(file,'b2stbm_smo_bal');        % additional + external sources, N
output.ext_smo           = ncread(file,'ext_smo_bal');

output.b2srdt_smo        = ncread(file,'b2srdt_smo_bal');        % numerics sources, N
output.b2srsm_smo        = ncread(file,'b2srsm_smo_bal');
output.b2srst_smo        = ncread(file,'b2srst_smo_bal');

% Electron energy sources from B2.5

output.b2sihs_divue            = ncread(file,'b2sihs_divue_bal');            % parallel-velocity-gradient heating, W

output.b2stel_she              = ncread(file,'b2stel_she_bal');              % atomic processes + radiation soruces, W

output.b2sihs_joule            = ncread(file,'b2sihs_joule_bal');            % joule heating, W

output.b2sihs_diae             = ncread(file,'b2sihs_diae_bal');             % drift-related-heating, W
output.b2sihs_exbe             = ncread(file,'b2sihs_exbe_bal');

output.b2npht_she              =-ncread(file,'b2npht_shei_bal');             % temperature-equilibration source, W

output.b2stbc_she              = ncread(file,'b2stbc_she_bal');              % boundary source, W

output.b2stbr_phys_she         = ncread(file,'b2stbr_phys_she_bal');         % recycling sources, W
try
output.b2stbr_bas_she          = ncread(file,'b2stbr_bas_she_bal');
catch
end
output.b2stbr_first_flight_she = ncread(file,'b2stbr_first_flight_she_bal');

output.b2stbm_she              = ncread(file,'b2stbm_she_bal');              % additional + external sources, W
output.ext_she                 = ncread(file,'ext_she_bal');

output.b2srdt_she              = ncread(file,'b2srdt_she_bal');              % numerics sources, W
output.b2srsm_she              = ncread(file,'b2srsm_she_bal'); 
output.b2srst_she              = ncread(file,'b2srst_she_bal'); 

% Ion energy sources from B2.5

output.b2sihs_divua            = ncread(file,'b2sihs_divua_bal');            % parallel-velocity-gradient heating, W

output.b2sihs_visa             = ncread(file,'b2sihs_visa_bal');             % viscosity heating, W

output.b2stel_shi_ion          = ncread(file,'b2stel_shi_ion_bal');          % atomic processes, W
output.b2stel_shi_rec          = ncread(file,'b2stel_shi_rec_bal');
output.b2stcx_shi              = ncread(file,'b2stcx_shi_bal');

output.b2sihs_fraa             = ncread(file,'b2sihs_fraa_bal');             % friction heating, W

output.b2sihs_diaa             = ncread(file,'b2sihs_diaa_bal');             % drift-related-heating, W
output.b2sihs_exba             = ncread(file,'b2sihs_exba_bal');

output.b2npht_shi              = ncread(file,'b2npht_shei_bal');             % temperature-equilibration source, W

output.b2stbc_shi              = ncread(file,'b2stbc_shi_bal');              % boundary source, W

output.b2stbr_phys_shi         = ncread(file,'b2stbr_phys_shi_bal');         % recycling sources, W
try
output.b2stbr_bas_shi          = ncread(file,'b2stbr_bas_shi_bal');
catch
end
output.b2stbr_first_flight_shi = ncread(file,'b2stbr_first_flight_shi_bal');

output.b2stbm_shi              = ncread(file,'b2stbm_shi_bal');              % additional + external sources, W
output.ext_shi                 = ncread(file,'ext_shi_bal');

output.b2srdt_shi              = ncread(file,'b2srdt_shi_bal');              % numerics sources, W
output.b2srsm_shi              = ncread(file,'b2srsm_shi_bal'); 
output.b2srst_shi              = ncread(file,'b2srst_shi_bal'); 

% Particle sources from EIRENE

output.eirene_papl_sna  = ncread(file,'eirene_mc_papl_sna_bal'); % source from atom-plasma collisions, s^-1
output.eirene_pmpl_sna  = ncread(file,'eirene_mc_pmpl_sna_bal'); % source from molecule-plasma collisions, s^-1
output.eirene_pipl_sna  = ncread(file,'eirene_mc_pipl_sna_bal'); % source from test ion-plasma collisions, s^-1
output.eirene_pppl_sna  = ncread(file,'eirene_mc_pppl_sna_bal'); % recombination source, s^-1
output.eirene_core_sna  = ncread(file,'eirene_mc_core_sna_bal'); % core source, s^-1

% Momentum sources from EIRENE

output.eirene_mapl_smo  = ncread(file,'eirene_mc_mapl_smo_bal'); % source from atom-plasma collisions, N
output.eirene_mmpl_smo  = ncread(file,'eirene_mc_mmpl_smo_bal'); % source from molecule-plasma collisions, N
output.eirene_mipl_smo = ncread(file,'eirene_mc_mipl_smo_bal'); % source from test ion-plasma collisions, N
try
    output.eirene_mppl_smo  = ncread(file,'eirene_mc_cppv_smo_bal'); % recombination source, N
catch
    output.eirene_mppl_smo  = ncread(file,'eirene_mc_mppl_smo_bal'); % recombination source, N
end

% Electron energy sources from EIRENE

output.eirene_eael_she  = ncread(file,'eirene_mc_eael_she_bal'); % source from atom-plasma collisions, W
output.eirene_emel_she  = ncread(file,'eirene_mc_emel_she_bal'); % source from molecule-plasma collisions, W
output.eirene_eiel_she  = ncread(file,'eirene_mc_eiel_she_bal'); % source from test ion-plasma collisions, W
output.eirene_epel_she  = ncread(file,'eirene_mc_epel_she_bal'); % recombination source, W

% Ion energy sources from EIRENE

output.eirene_eapl_shi  = ncread(file,'eirene_mc_eapl_shi_bal'); % source from atom-plasma collisions, W
output.eirene_empl_shi  = ncread(file,'eirene_mc_empl_shi_bal'); % source from molecule-plasma collisions, W
output.eirene_eipl_shi  = ncread(file,'eirene_mc_eipl_shi_bal'); % source from test ion-plasma collisions, W
output.eirene_eppl_shi  = ncread(file,'eirene_mc_eppl_shi_bal'); % recombination source, W

fprintf('Sources from balance.nc read\n');

end

%% READ THE RESIDUALS

if READ_RESIDUALS

output.resco = ncread(file,'resco'); % residuals of the particle balance equation, s^-1

output.resmo = ncread(file,'resmo'); % residuals of the momentum balance equation, N

output.reshe = ncread(file,'reshe'); % residuals of the electron energy balance equation, W

output.reshi = ncread(file,'reshi'); % residuals of the ion energy balance equation, W

fprintf('Residuals from balance.nc read\n');

end

fclose(fid);

end