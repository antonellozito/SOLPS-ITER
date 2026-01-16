function [state,transport,fluxes,sources,residuals] = read_b2fplasmf(varargin)
%
% read_b2fplasmf reads the formatted b2fplasmf file created by B2.5
% Output is a struct "plasma" with all the data fields in the b2fplasmf file
%
% 1st input: main simulation structure
%
% Following inputs: strings which specify which subsets of fields
%                   should be read:
%                   - 'STATE'
%                   - 'TRANSPORT'
%                   - 'FLUXES'
%                   - 'SOURCES'
%                   - 'RESIDUALS'

%% PRELIMINARY OPERATIONS

% Load the file and read the version

simulation = varargin{1};

index = find(contains({simulation.run.name},'b2fplasmf'));
if isempty(index)
   error('Error: b2fplasmf not found');
end
fid = simulation.run(index).fid;
if (fid == -1)
   error('Error: b2fplasmf not found');
end

line    = fgetl(fid);
version = line(8:17);

if str2num(strrep(version,'.','')) < str2num(strrep('03.002.000','.',''))
    version = 'structured';
else
    version = 'unstructured';
end

% Read the dimensions

if strcmp(version,'structured')

    index_state = find(contains({simulation.run.name},'b2fstate'));
    if isempty(index_state)
       error('Error: b2fstate not found');
    end
    fid_state = simulation.run(index_state).fid;
    if (fid_state == -1)
       error('Error: b2fstate not found');
    end
    
    dim = scan_b2_int(fid_state,'nx,ny,ns',3);
    nx  = dim(1);
    ny  = dim(2);
    ns  = dim(3);
    
    frewind(fid_state);
    
    qcdim = [nx+2,ny+2];
    fluxdim  = [nx+2,ny+2,2];
    fluxdims = [nx+2,ny+2,2,ns];

elseif strcmp(version,'unstructured')

    dim = scan_b2_int(fid,'nCv,nFc,ns',3);
    nCv  = dim(1);
    nFc  = dim(2);
    ns   = dim(3);
    
    statedim  = [nCv,1];
    statedims = [nCv,ns];
    
    fluxdim   = [nFc,2];
    fluxdimp  = [nFc,2];
    fluxdims  = [nFc,2,ns];

end

%% READ THE STATE VARIABLES

state = [];

if any(strcmp(varargin,'STATE'))

if strcmp(version,'structured')

state.na              = scan_b2_real(fid,'na'    ,[nx+2,ny+2,ns]); % atomic density for each species, m^-3
state.ne              = scan_b2_real(fid,'ne'    ,[nx+2,ny+2]);    % electron density, m^-3
state.ni              = scan_b2_real(fid,'ni'    ,[nx+2,ny+2,2]);  % total atomic densities, m^-3

state.po              = scan_b2_real(fid,'po'    ,[nx+2,ny+2]);    % electric potential, V

Te                    = scan_b2_real(fid,'te'    ,[nx+2,ny+2]);    % electron temperature, J
state.Te(:,:)         = Te.*6.242e18;                              % electron temperature, eV
Ti                    = scan_b2_real(fid,'ti'    ,[nx+2,ny+2]);    % ion temperature, J
state.Ti(:,:)         = Ti.*6.242e18;                              % ion temperature, eV

state.ua              = scan_b2_real(fid,'ua'    ,[nx+2,ny+2,ns]); % parallel velocity, m s^-1
state.uadia           = scan_b2_real(fid,'uadia' ,fluxdims);       % total drift velocity components, m s^-1
state.wadia           = scan_b2_real(fid,'wadia' ,fluxdims);       % diamagnetic drift velocity components, m s^-1
state.vaecrb          = scan_b2_real(fid,'vaecrb',fluxdims);       % ExB drift velocity components, m s^-1 

elseif strcmp(version,'unstructured')

state.na     = scan_b2_real(fid,'na'    ,statedims);
state.ne     = scan_b2_real(fid,'ne'    ,statedim);
state.ua     = scan_b2_real(fid,'ua'    ,statedims);
state.uadia  = scan_b2_real(fid,'uadia' ,fluxdims);
Te           = scan_b2_real(fid,'te'    ,statedim);
state.Te(:,:)         = Te.*6.242e18;  
Ti           = scan_b2_real(fid,'ti'    ,statedim);
state.Ti(:,:)         = Ti.*6.242e18;  
state.tn     = scan_b2_real(fid,'tn'    ,statedim);
state.po     = scan_b2_real(fid,'po'    ,statedim);
state.kt     = scan_b2_real(fid,'kt'    ,statedim);
state.vaecrb = scan_b2_real(fid,'vaecrb' ,fluxdims);
state.vadia  = scan_b2_real(fid,'vadia'  ,fluxdims);
state.wadia  = scan_b2_real(fid,'wadia'  ,fluxdims);
state.veecrb = scan_b2_real(fid,'veecrb' ,fluxdim);
state.vedia  = scan_b2_real(fid,'vedia'  ,fluxdim);

end

fprintf('Structure STATE from b2fplasmf read.\n');

frewind(fid);

end

%% READ THE TRANSPORT COEFFICIENTS

transport = [];

if any(strcmp(varargin,'TRANSPORT'))

if strcmp(version,'structured')

transport.sig0         = scan_b2_real(fid,'sig0'        ,[nx+2,ny+2]);      % anomalous electrical conductivity, S m^-2
transport.hce0         = scan_b2_real(fid,'hce0'        ,[nx+2,ny+2]);      % anomalous electron thermal diffusivity, m^2 s^-1
transport.alf0         = scan_b2_real(fid,'alf0'        ,[nx+2,ny+2]);      % anomalous thermo-electric coefficient, m V^-1 s^-1
transport.hci0         = scan_b2_real(fid,'hcib'        ,[nx+2,ny+2,ns]);   % anomalous ion thermal diffusivity, m^2 s^-1
transport.dpa0         = scan_b2_real(fid,'dpa0'        ,[nx+2,ny+2,ns]);   % anomalous pressure-driven particle diffusivity, m^2 s^-1
transport.dna0         = scan_b2_real(fid,'dna0'        ,[nx+2,ny+2,ns]);   % anomalous density-driven particle diffusivity, m^2 s^-1
transport.vsa0         = scan_b2_real(fid,'vsa0'        ,[nx+2,ny+2,ns]);   % anomalous viscosity, m^2 s-1
transport.vla0         = scan_b2_real(fid,'vla0'        ,[nx+2,ny+2,2,ns]); % anomalous pinch velocity, m s^-1

elseif strcmp(version,'unstructured')

transport.sig0     = scan_b2_real(fid,'sig0'    ,[nCv]);
transport.hce0     = scan_b2_real(fid,'hce0'    ,[nCv]);
transport.alf0     = scan_b2_real(fid,'alf0'    ,[nCv]);
transport.hci0     = scan_b2_real(fid,'hci0'    ,[nCv]);
transport.hcib     = scan_b2_real(fid,'hcib'    ,statedims);
transport.dpa0     = scan_b2_real(fid,'dpa0'    ,statedims);
transport.dna0     = scan_b2_real(fid,'dna0'    ,statedims);
transport.vsa0     = scan_b2_real(fid,'vsa0'    ,statedims);
transport.vla0     = scan_b2_real(fid,'vla0'    ,[nCv 2 ns]);
transport.dkt0     = scan_b2_real(fid,'dkt0'    ,[nCv]);
transport.dna_ExB     = scan_b2_real(fid,'dna_ExB'    ,[nCv]);
transport.hce_ExB     = scan_b2_real(fid,'hce_ExB'    ,[nCv]);
transport.hci_ExB     = scan_b2_real(fid,'hci_ExB'    ,[nCv]);

end

fprintf('Structure TRANSPORT from b2fplasmf read.\n');

frewind(fid);

end

%% READ THE FLUXES

fluxes = [];

if any(strcmp(varargin,'FLUXES'))

if strcmp(version,'structured')

fluxes.fch                         = scan_b2_real(fid,'fch'   ,fluxdim);
fluxes.fchp                        = scan_b2_real(fid,'fchp'  ,fluxdim);
fluxes.fhe                         = scan_b2_real(fid,'fhe'   ,fluxdim);
fluxes.fhep                        = scan_b2_real(fid,'fhep'  ,fluxdim);
fluxes.fhet                        = scan_b2_real(fid,'fhet'  ,fluxdim);
fluxes.fhi                         = scan_b2_real(fid,'fhi'   ,fluxdim);
fluxes.fhip                        = scan_b2_real(fid,'fhip'  ,fluxdim);
fluxes.fhit                        = scan_b2_real(fid,'fhit'  ,fluxdim);
fluxes.fna                         = scan_b2_real(fid,'fna'   ,fluxdims);    
fluxes.fne                         = scan_b2_real(fid,'fne'   ,fluxdim);
fluxes.fni                         = scan_b2_real(fid,'fni'   ,fluxdim);
fluxes.fchdia                      = scan_b2_real(fid,'fchdia',fluxdim);
fluxes.fmo                         = scan_b2_real(fid,'fmo'   ,fluxdims);
fluxes.fna_32                      = scan_b2_real(fid,'fna_32',fluxdims);
fluxes.fna_52                      = scan_b2_real(fid,'fna_52',fluxdims);
fluxes.fni_32                      = scan_b2_real(fid,'fni_32',fluxdim);
fluxes.fni_52                      = scan_b2_real(fid,'fni_52',fluxdim);
fluxes.fne_32                      = scan_b2_real(fid,'fne_32',fluxdim);
fluxes.fne_52                      = scan_b2_real(fid,'fne_52',fluxdim);
fluxes.fchvispar                   = scan_b2_real(fid,'fchvispar'   ,fluxdim);
fluxes.fchvisper                   = scan_b2_real(fid,'fchvisper'   ,fluxdim);
fluxes.fchin                       = scan_b2_real(fid,'fchin'       ,fluxdim);
fluxes.fna_nodrift                 = scan_b2_real(fid,'fna_nodrift' ,fluxdims);
fluxes.fna_mdf                     = scan_b2_real(fid,'fna_mdf'     ,fluxdims);
fluxes.fhe_mdf                     = scan_b2_real(fid,'fhe_mdf'     ,fluxdim);
fluxes.fhi_mdf                     = scan_b2_real(fid,'fhi_mdf'     ,fluxdim);
fluxes.fnaPSch                     = scan_b2_real(fid,'fnaPSch'     ,fluxdims);
fluxes.fhePSch                     = scan_b2_real(fid,'fhePSch'     ,fluxdim);
fluxes.fhiPSch                     = scan_b2_real(fid,'fhiPSch'     ,fluxdim);
fluxes.fna_fcor                    = scan_b2_real(fid,'fna_fcor'    ,fluxdims);
fluxes.fna_he                      = scan_b2_real(fid,'fna_he'      ,fluxdims);
fluxes.fchvisq                     = scan_b2_real(fid,'fchvisq'     ,fluxdim);
fluxes.fchinert                    = scan_b2_real(fid,'fchinert'    ,fluxdim);
fluxes.fht                         = scan_b2_real(fid,'fht'  ,fluxdim);
fluxes.fhj                         = scan_b2_real(fid,'fhj'  ,fluxdim);
fluxes.fhm                         = scan_b2_real(fid,'fhm'  ,fluxdims);
fluxes.fhp                         = scan_b2_real(fid,'fhp'  ,fluxdims);

elseif strcmp(version,'unstructured')

fluxes.fna    = scan_b2_real(fid,'fna'   ,fluxdims);
fluxes.fne    = scan_b2_real(fid,'fne'   ,fluxdim);
fluxes.fhe    = scan_b2_real(fid,'fhe'   ,fluxdim);
fluxes.fhi    = scan_b2_real(fid,'fhi'   ,fluxdim);
fluxes.fhn    = scan_b2_real(fid,'fhn'   ,fluxdim);
fluxes.fch    = scan_b2_real(fid,'fch'   ,fluxdim);
fluxes.fch_32 = scan_b2_real(fid,'fch_32',fluxdim);
fluxes.fch_52 = scan_b2_real(fid,'fch_52',fluxdim);
fluxes.kinrgy = scan_b2_real(fid,'kinrgy',statedims);
fluxes.fkt = scan_b2_real(fid,'fkt',fluxdim);
fluxes.fch_p  = scan_b2_real(fid,'fch_p' ,fluxdimp);
fluxes.fna_mdf     = scan_b2_real(fid,'fna_mdf'    ,fluxdims);
fluxes.fhe_mdf     = scan_b2_real(fid,'fhe_mdf'    ,fluxdim);
fluxes.fhi_mdf     = scan_b2_real(fid,'fhi_mdf'    ,fluxdim);
fluxes.fna_fcor    = scan_b2_real(fid,'fna_fcor'   ,fluxdims);
fluxes.fna_nodrift = scan_b2_real(fid,'fna_nodrift',fluxdims);
fluxes.fna_he      = scan_b2_real(fid,'fna_he'     ,fluxdims);
fluxes.fnaPSch     = scan_b2_real(fid,'fnaPSch'    ,fluxdims);
fluxes.fhePSch     = scan_b2_real(fid,'fhePSch'    ,fluxdim);
fluxes.fhiPSch     = scan_b2_real(fid,'fhiPSch'    ,fluxdim);
fluxes.fna_eir     = scan_b2_real(fid,'fna_eir'    ,fluxdims);
fluxes.fne_eir     = scan_b2_real(fid,'fne_eir'    ,fluxdim);
fluxes.fhe_eir     = scan_b2_real(fid,'fhe_eir'    ,fluxdim);
fluxes.fhi_eir     = scan_b2_real(fid,'fhi_eir'    ,fluxdim);
fluxes.fna_32      = scan_b2_real(fid,'fna_32'     ,fluxdims);
fluxes.fna_52      = scan_b2_real(fid,'fna_52'     ,fluxdims);
fluxes.fni_32      = scan_b2_real(fid,'fni_32'     ,fluxdim);
fluxes.fni_52      = scan_b2_real(fid,'fni_52'     ,fluxdim);
fluxes.fne_32      = scan_b2_real(fid,'fne_32'     ,fluxdim);
fluxes.fne_52      = scan_b2_real(fid,'fne_52'     ,fluxdim);
fluxes.fchdia      = scan_b2_real(fid,'fchdia'     ,fluxdim);
fluxes.fchin       = scan_b2_real(fid,'fchin'      ,fluxdim);
fluxes.fchvispar   = scan_b2_real(fid,'fchvispar'  ,fluxdim);
fluxes.fchvisper   = scan_b2_real(fid,'fchvisper'  ,fluxdim);
fluxes.fchvisq     = scan_b2_real(fid,'fchvisq'    ,fluxdim);
fluxes.fchinert    = scan_b2_real(fid,'fchinert'   ,fluxdim);
fluxes.fchanml     = scan_b2_real(fid,'fchanml'    ,fluxdim);
fluxes.fht         = scan_b2_real(fid,'fht'        ,fluxdim);
fluxes.fhj         = scan_b2_real(fid,'fhj'        ,fluxdim);
fluxes.fhm         = scan_b2_real(fid,'fhm'        ,fluxdims);
fluxes.fhp         = scan_b2_real(fid,'fhp'        ,fluxdims);

end

fprintf('Structure FLUXES from b2fplasmf read.\n');

frewind(fid);

end

%% READ THE SOURCES

sources = [];

if any(strcmp(varargin,'SOURCES'))

if strcmp(version,'structured')

sources.sch          = scan_b2_real(fid,'sch'         ,[nx+2,ny+2,4]);    % total current source, A
sources.she          = scan_b2_real(fid,'she'         ,[nx+2,ny+2,4]);    % total electron energy source, W
sources.shi          = scan_b2_real(fid,'shi'         ,[nx+2,ny+2,4]);    % total ion energy source, W
sources.smo          = scan_b2_real(fid,'smo'         ,[nx+2,ny+2,4,ns]); % total momentum source, N
sources.smq          = scan_b2_real(fid,'smq'         ,[nx+2,ny+2,4,ns]); % total momentum source, N
sources.sna          = scan_b2_real(fid,'sna'         ,[nx+2,ny+2,2,ns]); % total atomic particle source, s^-1
sources.sne          = scan_b2_real(fid,'sne'         ,[nx+2,ny+2,2]);    % total electron source, s^-1

sources.rsana        = scan_b2_real(fid,'rsana'       ,[nx+2,ny+2,ns]);   % ionization atomic particle source, s^-1
sources.rsahi        = scan_b2_real(fid,'rsahi'       ,[nx+2,ny+2,ns]);   % ionization ion energy source, W
sources.rsamo        = scan_b2_real(fid,'rsamo'       ,[nx+2,ny+2,ns]);   % ionization momentum source, N
sources.rrana        = scan_b2_real(fid,'rrana'       ,[nx+2,ny+2,ns]);   % recombination atomic particle source, s^-1
sources.rrahi        = scan_b2_real(fid,'rrahi'       ,[nx+2,ny+2,ns]);   % recombination ion energy source, W
sources.rramo        = scan_b2_real(fid,'rramo'       ,[nx+2,ny+2,ns]);   % recombination momentum source, N
sources.rqahe        = scan_b2_real(fid,'rqahe'       ,[nx+2,ny+2,ns]);   % electron cooling rate, W
sources.rqrad        = scan_b2_real(fid,'rqrad'       ,[nx+2,ny+2,ns]);   % line radiation rate, W
sources.rqbrm        = scan_b2_real(fid,'rqbrm'       ,[nx+2,ny+2,ns]);   % bremmstrahlung radiation rate, W
sources.rcxna        = scan_b2_real(fid,'rcxna'       ,[nx+2,ny+2,ns]);   % charge-exchange atomic particle source, s^-1
sources.rcxhi        = scan_b2_real(fid,'rcxhi'       ,[nx+2,ny+2,ns]);   % charge-exchange ion energy source, W
sources.rcxmo        = scan_b2_real(fid,'rcxmo'       ,[nx+2,ny+2,ns]);   % charge-exchange momentum source, N

sources.b2stbr_sna   = scan_b2_real(fid,'b2stbr_sna'  ,[nx+2,ny+2,ns]);   % recycling atomic particle source, s^-1
sources.b2stbr_smo   = scan_b2_real(fid,'b2stbr_smo'  ,[nx+2,ny+2,ns]);   % recycling momentum source, N
sources.b2stbr_she   = scan_b2_real(fid,'b2stbr_she'  ,[nx+2,ny+2]);      % recycling electron energy source, W
sources.b2stbr_shi   = scan_b2_real(fid,'b2stbr_shi'  ,[nx+2,ny+2]);      % recycling ion energy source, W
sources.b2stbr_sch   = scan_b2_real(fid,'b2stbr_sch'  ,[nx+2,ny+2]);      % recycling current source, A
sources.b2stbr_sne   = scan_b2_real(fid,'b2stbr_sne'  ,[nx+2,ny+2]);      % recycling electron source, s^-1

sources.b2stbc_sna   = scan_b2_real(fid,'b2stbc_sna'  ,[nx+2,ny+2,ns]);   % boundary atomic particle source, s^-1
sources.b2stbc_smo   = scan_b2_real(fid,'b2stbc_smo'  ,[nx+2,ny+2,ns]);   % boundary momentum source, N
sources.b2stbc_she   = scan_b2_real(fid,'b2stbc_she'  ,[nx+2,ny+2]);      % boundary electron energy source, W
sources.b2stbc_shi   = scan_b2_real(fid,'b2stbc_shi'  ,[nx+2,ny+2]);      % boundary ion energy source, W
sources.b2stbc_sch   = scan_b2_real(fid,'b2stbc_sch'  ,[nx+2,ny+2]);      % boundary current source, A
sources.b2stbc_sne   = scan_b2_real(fid,'b2stbc_sne'  ,[nx+2,ny+2]);      % boundary electron source, s^-1

sources.b2stbm_sna   = scan_b2_real(fid,'b2stbm_sna'  ,[nx+2,ny+2,ns]);   % additional atomic particle source, s^-1
sources.b2stbm_smo   = scan_b2_real(fid,'b2stbm_smo'  ,[nx+2,ny+2,ns]);   % additional momentum source, N
sources.b2stbm_she   = scan_b2_real(fid,'b2stbm_she'  ,[nx+2,ny+2]);      % additional electron energy source, W
sources.b2stbm_shi   = scan_b2_real(fid,'b2stbm_shi'  ,[nx+2,ny+2]);      % additional ion energy source, W
sources.b2stbm_sch   = scan_b2_real(fid,'b2stbm_sch'  ,[nx+2,ny+2]);      % additional current source, A
sources.b2stbm_sne   = scan_b2_real(fid,'b2stbm_sne'  ,[nx+2,ny+2]);      % additional electron source, s^-1

sources.b2sihs_divue = scan_b2_real(fid,'b2sihs_divue',[nx+2,ny+2]);      % parallel-velocity-gradient electron heating, W
sources.b2sihs_divua = scan_b2_real(fid,'b2sihs_divua',[nx+2,ny+2]);      % parallel-velocity-gradient ion heating, W
sources.b2sihs_exbe  = scan_b2_real(fid,'b2sihs_exbe' ,[nx+2,ny+2]);      % ExB electron heating, W
sources.b2sihs_exba  = scan_b2_real(fid,'b2sihs_exba' ,[nx+2,ny+2]);      % ExB ion heating, W
sources.b2sihs_visa  = scan_b2_real(fid,'b2sihs_visa' ,[nx+2,ny+2]);      % viscosity heating, W
sources.b2sihs_joule = scan_b2_real(fid,'b2sihs_joule',[nx+2,ny+2]);      % joule heating, W
sources.b2sihs_fraa  = scan_b2_real(fid,'b2sihs_fraa' ,[nx+2,ny+2]);      % friction heating, W
sources.b2sihs_str   = scan_b2_real(fid,'b2sihs_str ' ,[nx+2,ny+2]);      % strange heating, W

sources.b2npmo_smaf  = scan_b2_real(fid,'b2npmo_smaf' ,[nx+2,ny+2,4,ns]); % friction momentum source, N
sources.b2npmo_smag  = scan_b2_real(fid,'b2npmo_smag' ,[nx+2,ny+2,4,ns]); % pressure-gradient momentum source, N
sources.b2npmo_smav  = scan_b2_real(fid,'b2npmo_smav' ,[nx+2,ny+2,4,ns]); % viscosity momentum source, N
sources.smpr         = scan_b2_real(fid,'smpr'        ,[nx+2,ny+2,ns]);   % electrostatic force, N
sources.smpt         = scan_b2_real(fid,'smpt'        ,[nx+2,ny+2,ns]);   % thermal force, N
sources.smfr         = scan_b2_real(fid,'smfr'        ,[nx+2,ny+2,ns]);   % friction force, N
sources.smcf         = scan_b2_real(fid,'smcf'        ,[nx+2,ny+2,ns]);   % centrifugal force, N

sources.ext_sna      = scan_b2_real(fid,'ext_sna'     ,[nx+2,ny+2,ns]);   % external atomic particle source, s^-1
sources.ext_smo      = scan_b2_real(fid,'ext_smo'     ,[nx+2,ny+2,ns]);   % external momentum source, N
sources.ext_she      = scan_b2_real(fid,'ext_she'     ,[nx+2,ny+2]);      % external electron energy source, W
sources.ext_shi      = scan_b2_real(fid,'ext_shi'     ,[nx+2,ny+2]);      % external ion energy source, W
sources.ext_sch      = scan_b2_real(fid,'ext_sch'     ,[nx+2,ny+2]);      % external current source, A
sources.ext_sne      = scan_b2_real(fid,'ext_sne'     ,[nx+2,ny+2]);      % external electron source, s^-1

elseif strcmp(version,'unstructured')

sources.sna  = scan_b2_real(fid,'sna' ,[nCv,2,ns]);
sources.smo  = scan_b2_real(fid,'smo' ,[nCv,4,ns]);
sources.smq  = scan_b2_real(fid,'smq' ,[nCv,4,ns]);
sources.shi  = scan_b2_real(fid,'shi' ,[nCv,4]);
sources.she  = scan_b2_real(fid,'she' ,[nCv,4]);
sources.shn  = scan_b2_real(fid,'shn' ,[nCv,4]);
sources.skt  = scan_b2_real(fid,'skt' ,[nCv,4]);
sources.skt_prod  = scan_b2_real(fid,'skt_prod' ,[nCv]);
sources.skt_diss  = scan_b2_real(fid,'skt_diss' ,[nCv]);

sources.rsana        = scan_b2_real(fid,'rsana'       ,[nCv,ns]);   % ionization atomic particle source, s^-1
sources.rrana        = scan_b2_real(fid,'rrana'       ,[nCv,ns]);   % recombination atomic particle source, s^-1
sources.rcxna        = scan_b2_real(fid,'rcxna'       ,[nCv,ns]);   % charge-exchange atomic particle source, s^-1
sources.rsamo        = scan_b2_real(fid,'rsamo'       ,[nCv,ns]);   % ionization momentum source, N
sources.rramo        = scan_b2_real(fid,'rramo'       ,[nCv,ns]);   % recombination momentum source, N
sources.rcxmo        = scan_b2_real(fid,'rcxmo'       ,[nCv,ns]);   % charge-exchange momentum source, N
sources.rsahi        = scan_b2_real(fid,'rsahi'       ,[nCv,ns]);   % ionization ion energy source, W
sources.rrahi        = scan_b2_real(fid,'rrahi'       ,[nCv,ns]);   % recombination ion energy source, W
sources.rcxhi        = scan_b2_real(fid,'rcxhi'       ,[nCv,ns]);   % charge-exchange ion energy source, W
sources.rqahe        = scan_b2_real(fid,'rqahe'       ,[nCv,ns]);   % electron cooling rate, W
sources.rqrad        = scan_b2_real(fid,'rqrad'       ,[nCv,ns]);   % line radiation rate, W
sources.rqbrm        = scan_b2_real(fid,'rqbrm'       ,[nCv,ns]);   % bremmstrahlung radiation rate, W

sources.b2stbc_sna   = scan_b2_real(fid,'b2stbc_sna'  ,[nCv,ns]);   % boundary atomic particle source, s^-1
sources.b2stbr_sna   = scan_b2_real(fid,'b2stbr_sna'  ,[nCv,ns]);   % recycling atomic particle source, s^-1
sources.b2stbm_sna   = scan_b2_real(fid,'b2stbm_sna'  ,[nCv,ns]);   % additional atomic particle source, s^-1
sources.b2stbc_smo   = scan_b2_real(fid,'b2stbc_smo'  ,[nCv,ns]);   % boundary momentum source, N
sources.b2stbr_smo   = scan_b2_real(fid,'b2stbr_smo'  ,[nCv,ns]);   % recycling momentum source, N
sources.b2stbm_smo   = scan_b2_real(fid,'b2stbm_smo'  ,[nCv,ns]);   % additional momentum source, N
sources.b2stbc_she   = scan_b2_real(fid,'b2stbc_she'  ,[nCv]);      % boundary electron energy source, W
sources.b2stbr_she   = scan_b2_real(fid,'b2stbr_she'  ,[nCv]);      % recycling electron energy source, W
sources.b2stbm_she   = scan_b2_real(fid,'b2stbm_she'  ,[nCv]);      % additional electron energy source, W
sources.b2stbc_shi   = scan_b2_real(fid,'b2stbc_shi'  ,[nCv]);      % boundary ion energy source, W
sources.b2stbr_shi   = scan_b2_real(fid,'b2stbr_shi'  ,[nCv]);      % recycling ion energy source, W
sources.b2stbm_shi   = scan_b2_real(fid,'b2stbm_shi'  ,[nCv]);      % additional ion energy source, W
sources.b2stbc_sch   = scan_b2_real(fid,'b2stbc_sch'  ,[nCv]);      % boundary current source, A
sources.b2stbr_sch   = scan_b2_real(fid,'b2stbr_sch'  ,[nCv]);      % recycling current source, A
sources.b2stbc_sne   = scan_b2_real(fid,'b2stbc_sne'  ,[nCv]);      % boundary electron source, s^-1
sources.b2stbr_sne   = scan_b2_real(fid,'b2stbr_sne'  ,[nCv]);      % recycling electron source, s^-1
sources.b2stbm_sne   = scan_b2_real(fid,'b2stbm_sne'  ,[nCv]);      % additional electron source, s^-1

sources.b2sihs_divua = scan_b2_real(fid,'b2sihs_divua',[nCv]);      % parallel-velocity-gradient ion heating, W
sources.b2sihs_divue = scan_b2_real(fid,'b2sihs_divue',[nCv]);      % parallel-velocity-gradient electron heating, W
sources.b2sihs_exba  = scan_b2_real(fid,'b2sihs_exba' ,[nCv]);      % ExB ion heating, W
sources.b2sihs_exbe  = scan_b2_real(fid,'b2sihs_exbe' ,[nCv]);      % ExB electron heating, W
sources.b2sihs_fraa  = scan_b2_real(fid,'b2sihs_fraa' ,[nCv]);      % friction heating, W
sources.b2sihs_joule = scan_b2_real(fid,'b2sihs_joule',[nCv]);      % joule heating, W
sources.b2sihs_str   = scan_b2_real(fid,'b2sihs_str ' ,[nCv]);      % strange heating, W
sources.b2sihs_visa  = scan_b2_real(fid,'b2sihs_visa' ,[nCv]);      % viscosity heating, W


sources.b2npmo_smaf  = scan_b2_real(fid,'b2npmo_smaf' ,[nCv,4,ns]); % friction momentum source, N
sources.b2npmo_smag  = scan_b2_real(fid,'b2npmo_smag' ,[nCv,4,ns]); % pressure-gradient momentum source, N
sources.b2npmo_smav  = scan_b2_real(fid,'b2npmo_smav' ,[nCv,4,ns]); % viscosity momentum source, N
sources.smcf         = scan_b2_real(fid,'smcf'        ,[nCv,ns]);   % centrifugal force, N
sources.smfr         = scan_b2_real(fid,'smfr'        ,[nCv,ns]);   % friction force, N
sources.smpr         = scan_b2_real(fid,'smpr'        ,[nCv,ns]);   % electrostatic force, N
sources.smpt         = scan_b2_real(fid,'smpt'        ,[nCv,ns]);   % thermal force, N

end

fprintf('Structure SOURCES from b2fplasmf read.\n');

frewind(fid);

end

%% READ THE RESIDUALS

residuals = [];

if any(strcmp(varargin,'RESIDUALS'))

if strcmp(version,'structured')

residuals.resco        = scan_b2_real(fid,'resco'       ,[nx+2,ny+2,ns]);  % continuity equation resitual, s^-1
residuals.reshe        = scan_b2_real(fid,'reshe'       ,[nx+2,ny+2]);     % electron energy equation resitual, W
residuals.reshi        = scan_b2_real(fid,'reshi'       ,[nx+2,ny+2]);     % ion energy equation resitual, W
residuals.resmo        = scan_b2_real(fid,'resmo'       ,[nx+2,ny+2,ns]);  % momentum equation resitual, N
residuals.resmt        = scan_b2_real(fid,'resmt'       ,[nx+2,ny+2]);     % total momentum equation resitual, N
residuals.respo        = scan_b2_real(fid,'respo'       ,[nx+2,ny+2]);     % potential equation resitual, A

elseif strcmp(version,'unstructured')

residuals.resco  = scan_b2_real(fid,'resco' ,[nCv,ns]);
residuals.reshe  = scan_b2_real(fid,'reshe' ,[nCv]);
residuals.reshi  = scan_b2_real(fid,'reshi' ,[nCv]);
residuals.reshn  = scan_b2_real(fid,'reshn' ,[nCv]);
residuals.resmo  = scan_b2_real(fid,'resmo' ,[nCv,ns]);
residuals.resmt  = scan_b2_real(fid,'resmt' ,[nCv]);
residuals.respo  = scan_b2_real(fid,'respo' ,[nCv]);
residuals.reskt  = scan_b2_real(fid,'reskt' ,[nCv]);

end

fprintf('Structure RESIDUALS from b2fplasmf read.\n');

frewind(fid);

end

end