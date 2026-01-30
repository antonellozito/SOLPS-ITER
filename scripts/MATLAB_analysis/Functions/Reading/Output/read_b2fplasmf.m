function output = read_b2fplasmf(varargin)
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
file = simulation.run(index).file;
fid = fopen(file);
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

% Select which group of fields to read

READ_STATE = false;
READ_TRANSPORT = false;
READ_FLUXES = false;
READ_SOURCES = false;
READ_RESIDUALS = false;

if numel(varargin) == 1
    READ_STATE = true;
    READ_TRANSPORT = true;
    READ_FLUXES = true;
    READ_SOURCES = true;
    READ_RESIDUALS = true;
else
    if any(strcmp(varargin,'STATE'))
        READ_STATE = true;
    end
    if any(strcmp(varargin,'TRANSPORT'))
        READ_TRANSPORT = true;  
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

% Read the dimensions

if strcmp(version,'structured')

    index_state = find(contains({simulation.run.name},'b2fstate'));
    if isempty(index_state)
       error('Error: b2fstate not found');
    end
    file_state = simulation.run(index_state).file;
    fid_state = fopen(file_state);
    if (fid_state == -1)
       error('Error: b2fstate not found');
    end
    
    dim = scan_b2_int(fid_state,'nx,ny,ns',3);
    nx  = dim(1);
    ny  = dim(2);
    ns  = dim(3);
    
    frewind(fid_state);

    fclose(fid_state);
    
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

if READ_STATE

if strcmp(version,'structured')

output.na              = scan_b2_real(fid,'na'    ,[nx+2,ny+2,ns]); % atomic density for each species, m^-3
output.ne              = scan_b2_real(fid,'ne'    ,[nx+2,ny+2]);    % electron density, m^-3
output.ni              = scan_b2_real(fid,'ni'    ,[nx+2,ny+2,2]);  % total atomic densities, m^-3

output.po              = scan_b2_real(fid,'po'    ,[nx+2,ny+2]);    % electric potential, V

Te                    = scan_b2_real(fid,'te'    ,[nx+2,ny+2]);    % electron temperature, J
output.Te(:,:)         = Te.*6.242e18;                              % electron temperature, eV
Ti                    = scan_b2_real(fid,'ti'    ,[nx+2,ny+2]);    % ion temperature, J
output.Ti(:,:)         = Ti.*6.242e18;                              % ion temperature, eV

output.ua              = scan_b2_real(fid,'ua'    ,[nx+2,ny+2,ns]); % parallel velocity, m s^-1
output.uadia           = scan_b2_real(fid,'uadia' ,fluxdims);       % total drift velocity components, m s^-1
output.wadia           = scan_b2_real(fid,'wadia' ,fluxdims);       % diamagnetic drift velocity components, m s^-1
output.vaecrb          = scan_b2_real(fid,'vaecrb',fluxdims);       % ExB drift velocity components, m s^-1 

elseif strcmp(version,'unstructured')

output.na     = scan_b2_real(fid,'na'    ,statedims);
output.ne     = scan_b2_real(fid,'ne'    ,statedim);
output.ua     = scan_b2_real(fid,'ua'    ,statedims);
output.uadia  = scan_b2_real(fid,'uadia' ,fluxdims);
Te           = scan_b2_real(fid,'te'    ,statedim);
output.Te(:,:)         = Te.*6.242e18;  
Ti           = scan_b2_real(fid,'ti'    ,statedim);
output.Ti(:,:)         = Ti.*6.242e18;  
output.tn     = scan_b2_real(fid,'tn'    ,statedim);
output.po     = scan_b2_real(fid,'po'    ,statedim);
output.kt     = scan_b2_real(fid,'kt'    ,statedim);
output.vaecrb = scan_b2_real(fid,'vaecrb' ,fluxdims);
output.vadia  = scan_b2_real(fid,'vadia'  ,fluxdims);
output.wadia  = scan_b2_real(fid,'wadia'  ,fluxdims);
output.veecrb = scan_b2_real(fid,'veecrb' ,fluxdim);
output.vedia  = scan_b2_real(fid,'vedia'  ,fluxdim);

end

fprintf('State variables from b2fplasmf read\n');

frewind(fid);

end

%% READ THE TRANSPORT COEFFICIENTS

if READ_TRANSPORT

if strcmp(version,'structured')

output.sig0         = scan_b2_real(fid,'sig0'        ,[nx+2,ny+2]);      % anomalous electrical conductivity, S m^-2
output.hce0         = scan_b2_real(fid,'hce0'        ,[nx+2,ny+2]);      % anomalous electron thermal diffusivity, m^2 s^-1
output.alf0         = scan_b2_real(fid,'alf0'        ,[nx+2,ny+2]);      % anomalous thermo-electric coefficient, m V^-1 s^-1
output.hci0         = scan_b2_real(fid,'hcib'        ,[nx+2,ny+2,ns]);   % anomalous ion thermal diffusivity, m^2 s^-1
output.dpa0         = scan_b2_real(fid,'dpa0'        ,[nx+2,ny+2,ns]);   % anomalous pressure-driven particle diffusivity, m^2 s^-1
output.dna0         = scan_b2_real(fid,'dna0'        ,[nx+2,ny+2,ns]);   % anomalous density-driven particle diffusivity, m^2 s^-1
output.vsa0         = scan_b2_real(fid,'vsa0'        ,[nx+2,ny+2,ns]);   % anomalous viscosity, m^2 s-1
output.vla0         = scan_b2_real(fid,'vla0'        ,[nx+2,ny+2,2,ns]); % anomalous pinch velocity, m s^-1

elseif strcmp(version,'unstructured')

output.sig0     = scan_b2_real(fid,'sig0'    ,[nCv]);
output.hce0     = scan_b2_real(fid,'hce0'    ,[nCv]);
output.alf0     = scan_b2_real(fid,'alf0'    ,[nCv]);
output.hci0     = scan_b2_real(fid,'hci0'    ,[nCv]);
output.hcib     = scan_b2_real(fid,'hcib'    ,statedims);
output.dpa0     = scan_b2_real(fid,'dpa0'    ,statedims);
output.dna0     = scan_b2_real(fid,'dna0'    ,statedims);
output.vsa0     = scan_b2_real(fid,'vsa0'    ,statedims);
output.vla0     = scan_b2_real(fid,'vla0'    ,[nCv 2 ns]);
output.dkt0     = scan_b2_real(fid,'dkt0'    ,[nCv]);
output.dna_ExB     = scan_b2_real(fid,'dna_ExB'    ,[nCv]);
output.hce_ExB     = scan_b2_real(fid,'hce_ExB'    ,[nCv]);
output.hci_ExB     = scan_b2_real(fid,'hci_ExB'    ,[nCv]);

end

fprintf('Transport coefficients from b2fplasmf read\n');

frewind(fid);

end

%% READ THE FLUXES

if READ_FLUXES

if strcmp(version,'structured')

output.fch                         = scan_b2_real(fid,'fch'   ,fluxdim);
output.fchp                        = scan_b2_real(fid,'fchp'  ,fluxdim);
output.fhe                         = scan_b2_real(fid,'fhe'   ,fluxdim);
output.fhep                        = scan_b2_real(fid,'fhep'  ,fluxdim);
output.fhet                        = scan_b2_real(fid,'fhet'  ,fluxdim);
output.fhi                         = scan_b2_real(fid,'fhi'   ,fluxdim);
output.fhip                        = scan_b2_real(fid,'fhip'  ,fluxdim);
output.fhit                        = scan_b2_real(fid,'fhit'  ,fluxdim);
output.fna                         = scan_b2_real(fid,'fna'   ,fluxdims);    
output.fne                         = scan_b2_real(fid,'fne'   ,fluxdim);
output.fni                         = scan_b2_real(fid,'fni'   ,fluxdim);
output.fchdia                      = scan_b2_real(fid,'fchdia',fluxdim);
output.fmo                         = scan_b2_real(fid,'fmo'   ,fluxdims);
output.fna_32                      = scan_b2_real(fid,'fna_32',fluxdims);
output.fna_52                      = scan_b2_real(fid,'fna_52',fluxdims);
output.fni_32                      = scan_b2_real(fid,'fni_32',fluxdim);
output.fni_52                      = scan_b2_real(fid,'fni_52',fluxdim);
output.fne_32                      = scan_b2_real(fid,'fne_32',fluxdim);
output.fne_52                      = scan_b2_real(fid,'fne_52',fluxdim);
output.fchvispar                   = scan_b2_real(fid,'fchvispar'   ,fluxdim);
output.fchvisper                   = scan_b2_real(fid,'fchvisper'   ,fluxdim);
output.fchin                       = scan_b2_real(fid,'fchin'       ,fluxdim);
output.fna_nodrift                 = scan_b2_real(fid,'fna_nodrift' ,fluxdims);
output.fna_mdf                     = scan_b2_real(fid,'fna_mdf'     ,fluxdims);
output.fhe_mdf                     = scan_b2_real(fid,'fhe_mdf'     ,fluxdim);
output.fhi_mdf                     = scan_b2_real(fid,'fhi_mdf'     ,fluxdim);
output.fnaPSch                     = scan_b2_real(fid,'fnaPSch'     ,fluxdims);
output.fhePSch                     = scan_b2_real(fid,'fhePSch'     ,fluxdim);
output.fhiPSch                     = scan_b2_real(fid,'fhiPSch'     ,fluxdim);
output.fna_fcor                    = scan_b2_real(fid,'fna_fcor'    ,fluxdims);
output.fna_he                      = scan_b2_real(fid,'fna_he'      ,fluxdims);
output.fchvisq                     = scan_b2_real(fid,'fchvisq'     ,fluxdim);
output.fchinert                    = scan_b2_real(fid,'fchinert'    ,fluxdim);
output.fht                         = scan_b2_real(fid,'fht'  ,fluxdim);
output.fhj                         = scan_b2_real(fid,'fhj'  ,fluxdim);
output.fhm                         = scan_b2_real(fid,'fhm'  ,fluxdims);
output.fhp                         = scan_b2_real(fid,'fhp'  ,fluxdims);

elseif strcmp(version,'unstructured')

output.fna    = scan_b2_real(fid,'fna'   ,fluxdims);
output.fne    = scan_b2_real(fid,'fne'   ,fluxdim);
output.fhe    = scan_b2_real(fid,'fhe'   ,fluxdim);
output.fhi    = scan_b2_real(fid,'fhi'   ,fluxdim);
output.fhn    = scan_b2_real(fid,'fhn'   ,fluxdim);
output.fch    = scan_b2_real(fid,'fch'   ,fluxdim);
output.fch_32 = scan_b2_real(fid,'fch_32',fluxdim);
output.fch_52 = scan_b2_real(fid,'fch_52',fluxdim);
output.kinrgy = scan_b2_real(fid,'kinrgy',statedims);
output.fkt = scan_b2_real(fid,'fkt',fluxdim);
output.fch_p  = scan_b2_real(fid,'fch_p' ,fluxdimp);
output.fna_mdf     = scan_b2_real(fid,'fna_mdf'    ,fluxdims);
output.fhe_mdf     = scan_b2_real(fid,'fhe_mdf'    ,fluxdim);
output.fhi_mdf     = scan_b2_real(fid,'fhi_mdf'    ,fluxdim);
output.fna_fcor    = scan_b2_real(fid,'fna_fcor'   ,fluxdims);
output.fna_nodrift = scan_b2_real(fid,'fna_nodrift',fluxdims);
output.fna_he      = scan_b2_real(fid,'fna_he'     ,fluxdims);
output.fnaPSch     = scan_b2_real(fid,'fnaPSch'    ,fluxdims);
output.fhePSch     = scan_b2_real(fid,'fhePSch'    ,fluxdim);
output.fhiPSch     = scan_b2_real(fid,'fhiPSch'    ,fluxdim);
output.fna_eir     = scan_b2_real(fid,'fna_eir'    ,fluxdims);
output.fne_eir     = scan_b2_real(fid,'fne_eir'    ,fluxdim);
output.fhe_eir     = scan_b2_real(fid,'fhe_eir'    ,fluxdim);
output.fhi_eir     = scan_b2_real(fid,'fhi_eir'    ,fluxdim);
output.fna_32      = scan_b2_real(fid,'fna_32'     ,fluxdims);
output.fna_52      = scan_b2_real(fid,'fna_52'     ,fluxdims);
output.fni_32      = scan_b2_real(fid,'fni_32'     ,fluxdim);
output.fni_52      = scan_b2_real(fid,'fni_52'     ,fluxdim);
output.fne_32      = scan_b2_real(fid,'fne_32'     ,fluxdim);
output.fne_52      = scan_b2_real(fid,'fne_52'     ,fluxdim);
output.fchdia      = scan_b2_real(fid,'fchdia'     ,fluxdim);
output.fchin       = scan_b2_real(fid,'fchin'      ,fluxdim);
output.fchvispar   = scan_b2_real(fid,'fchvispar'  ,fluxdim);
output.fchvisper   = scan_b2_real(fid,'fchvisper'  ,fluxdim);
output.fchvisq     = scan_b2_real(fid,'fchvisq'    ,fluxdim);
output.fchinert    = scan_b2_real(fid,'fchinert'   ,fluxdim);
output.fchanml     = scan_b2_real(fid,'fchanml'    ,fluxdim);
output.fht         = scan_b2_real(fid,'fht'        ,fluxdim);
output.fhj         = scan_b2_real(fid,'fhj'        ,fluxdim);
output.fhm         = scan_b2_real(fid,'fhm'        ,fluxdims);
output.fhp         = scan_b2_real(fid,'fhp'        ,fluxdims);

end

fprintf('Fluxes from b2fplasmf read\n');

frewind(fid);

end

%% READ THE SOURCES

if READ_SOURCES

if strcmp(version,'structured')

output.sch          = scan_b2_real(fid,'sch'         ,[nx+2,ny+2,4]);    % total current source, A
output.she          = scan_b2_real(fid,'she'         ,[nx+2,ny+2,4]);    % total electron energy source, W
output.shi          = scan_b2_real(fid,'shi'         ,[nx+2,ny+2,4]);    % total ion energy source, W
output.smo          = scan_b2_real(fid,'smo'         ,[nx+2,ny+2,4,ns]); % total momentum source, N
output.smq          = scan_b2_real(fid,'smq'         ,[nx+2,ny+2,4,ns]); % total momentum source, N
output.sna          = scan_b2_real(fid,'sna'         ,[nx+2,ny+2,2,ns]); % total atomic particle source, s^-1
output.sne          = scan_b2_real(fid,'sne'         ,[nx+2,ny+2,2]);    % total electron source, s^-1

output.rsana        = scan_b2_real(fid,'rsana'       ,[nx+2,ny+2,ns]);   % ionization atomic particle source, s^-1
output.rsahi        = scan_b2_real(fid,'rsahi'       ,[nx+2,ny+2,ns]);   % ionization ion energy source, W
output.rsamo        = scan_b2_real(fid,'rsamo'       ,[nx+2,ny+2,ns]);   % ionization momentum source, N
output.rrana        = scan_b2_real(fid,'rrana'       ,[nx+2,ny+2,ns]);   % recombination atomic particle source, s^-1
output.rrahi        = scan_b2_real(fid,'rrahi'       ,[nx+2,ny+2,ns]);   % recombination ion energy source, W
output.rramo        = scan_b2_real(fid,'rramo'       ,[nx+2,ny+2,ns]);   % recombination momentum source, N
output.rqahe        = scan_b2_real(fid,'rqahe'       ,[nx+2,ny+2,ns]);   % electron cooling rate, W
output.rqrad        = scan_b2_real(fid,'rqrad'       ,[nx+2,ny+2,ns]);   % line radiation rate, W
output.rqbrm        = scan_b2_real(fid,'rqbrm'       ,[nx+2,ny+2,ns]);   % bremmstrahlung radiation rate, W
output.rcxna        = scan_b2_real(fid,'rcxna'       ,[nx+2,ny+2,ns]);   % charge-exchange atomic particle source, s^-1
output.rcxhi        = scan_b2_real(fid,'rcxhi'       ,[nx+2,ny+2,ns]);   % charge-exchange ion energy source, W
output.rcxmo        = scan_b2_real(fid,'rcxmo'       ,[nx+2,ny+2,ns]);   % charge-exchange momentum source, N

output.b2stbr_sna   = scan_b2_real(fid,'b2stbr_sna'  ,[nx+2,ny+2,ns]);   % recycling atomic particle source, s^-1
output.b2stbr_smo   = scan_b2_real(fid,'b2stbr_smo'  ,[nx+2,ny+2,ns]);   % recycling momentum source, N
output.b2stbr_she   = scan_b2_real(fid,'b2stbr_she'  ,[nx+2,ny+2]);      % recycling electron energy source, W
output.b2stbr_shi   = scan_b2_real(fid,'b2stbr_shi'  ,[nx+2,ny+2]);      % recycling ion energy source, W
output.b2stbr_sch   = scan_b2_real(fid,'b2stbr_sch'  ,[nx+2,ny+2]);      % recycling current source, A
output.b2stbr_sne   = scan_b2_real(fid,'b2stbr_sne'  ,[nx+2,ny+2]);      % recycling electron source, s^-1

output.b2stbc_sna   = scan_b2_real(fid,'b2stbc_sna'  ,[nx+2,ny+2,ns]);   % boundary atomic particle source, s^-1
output.b2stbc_smo   = scan_b2_real(fid,'b2stbc_smo'  ,[nx+2,ny+2,ns]);   % boundary momentum source, N
output.b2stbc_she   = scan_b2_real(fid,'b2stbc_she'  ,[nx+2,ny+2]);      % boundary electron energy source, W
output.b2stbc_shi   = scan_b2_real(fid,'b2stbc_shi'  ,[nx+2,ny+2]);      % boundary ion energy source, W
output.b2stbc_sch   = scan_b2_real(fid,'b2stbc_sch'  ,[nx+2,ny+2]);      % boundary current source, A
output.b2stbc_sne   = scan_b2_real(fid,'b2stbc_sne'  ,[nx+2,ny+2]);      % boundary electron source, s^-1

output.b2stbm_sna   = scan_b2_real(fid,'b2stbm_sna'  ,[nx+2,ny+2,ns]);   % additional atomic particle source, s^-1
output.b2stbm_smo   = scan_b2_real(fid,'b2stbm_smo'  ,[nx+2,ny+2,ns]);   % additional momentum source, N
output.b2stbm_she   = scan_b2_real(fid,'b2stbm_she'  ,[nx+2,ny+2]);      % additional electron energy source, W
output.b2stbm_shi   = scan_b2_real(fid,'b2stbm_shi'  ,[nx+2,ny+2]);      % additional ion energy source, W
output.b2stbm_sch   = scan_b2_real(fid,'b2stbm_sch'  ,[nx+2,ny+2]);      % additional current source, A
output.b2stbm_sne   = scan_b2_real(fid,'b2stbm_sne'  ,[nx+2,ny+2]);      % additional electron source, s^-1

output.b2sihs_divue = scan_b2_real(fid,'b2sihs_divue',[nx+2,ny+2]);      % parallel-velocity-gradient electron heating, W
output.b2sihs_divua = scan_b2_real(fid,'b2sihs_divua',[nx+2,ny+2]);      % parallel-velocity-gradient ion heating, W
output.b2sihs_exbe  = scan_b2_real(fid,'b2sihs_exbe' ,[nx+2,ny+2]);      % ExB electron heating, W
output.b2sihs_exba  = scan_b2_real(fid,'b2sihs_exba' ,[nx+2,ny+2]);      % ExB ion heating, W
output.b2sihs_visa  = scan_b2_real(fid,'b2sihs_visa' ,[nx+2,ny+2]);      % viscosity heating, W
output.b2sihs_joule = scan_b2_real(fid,'b2sihs_joule',[nx+2,ny+2]);      % joule heating, W
output.b2sihs_fraa  = scan_b2_real(fid,'b2sihs_fraa' ,[nx+2,ny+2]);      % friction heating, W
output.b2sihs_str   = scan_b2_real(fid,'b2sihs_str ' ,[nx+2,ny+2]);      % strange heating, W

output.b2npmo_smaf  = scan_b2_real(fid,'b2npmo_smaf' ,[nx+2,ny+2,4,ns]); % friction momentum source, N
output.b2npmo_smag  = scan_b2_real(fid,'b2npmo_smag' ,[nx+2,ny+2,4,ns]); % pressure-gradient momentum source, N
output.b2npmo_smav  = scan_b2_real(fid,'b2npmo_smav' ,[nx+2,ny+2,4,ns]); % viscosity momentum source, N
output.smpr         = scan_b2_real(fid,'smpr'        ,[nx+2,ny+2,ns]);   % electrostatic force, N
output.smpt         = scan_b2_real(fid,'smpt'        ,[nx+2,ny+2,ns]);   % thermal force, N
output.smfr         = scan_b2_real(fid,'smfr'        ,[nx+2,ny+2,ns]);   % friction force, N
output.smcf         = scan_b2_real(fid,'smcf'        ,[nx+2,ny+2,ns]);   % centrifugal force, N

output.ext_sna      = scan_b2_real(fid,'ext_sna'     ,[nx+2,ny+2,ns]);   % external atomic particle source, s^-1
output.ext_smo      = scan_b2_real(fid,'ext_smo'     ,[nx+2,ny+2,ns]);   % external momentum source, N
output.ext_she      = scan_b2_real(fid,'ext_she'     ,[nx+2,ny+2]);      % external electron energy source, W
output.ext_shi      = scan_b2_real(fid,'ext_shi'     ,[nx+2,ny+2]);      % external ion energy source, W
output.ext_sch      = scan_b2_real(fid,'ext_sch'     ,[nx+2,ny+2]);      % external current source, A
output.ext_sne      = scan_b2_real(fid,'ext_sne'     ,[nx+2,ny+2]);      % external electron source, s^-1

elseif strcmp(version,'unstructured')

output.sna  = scan_b2_real(fid,'sna' ,[nCv,2,ns]);
output.smo  = scan_b2_real(fid,'smo' ,[nCv,4,ns]);
output.smq  = scan_b2_real(fid,'smq' ,[nCv,4,ns]);
output.shi  = scan_b2_real(fid,'shi' ,[nCv,4]);
output.she  = scan_b2_real(fid,'she' ,[nCv,4]);
output.shn  = scan_b2_real(fid,'shn' ,[nCv,4]);
output.skt  = scan_b2_real(fid,'skt' ,[nCv,4]);
output.skt_prod  = scan_b2_real(fid,'skt_prod' ,[nCv]);
output.skt_diss  = scan_b2_real(fid,'skt_diss' ,[nCv]);

output.rsana        = scan_b2_real(fid,'rsana'       ,[nCv,ns]);   % ionization atomic particle source, s^-1
output.rrana        = scan_b2_real(fid,'rrana'       ,[nCv,ns]);   % recombination atomic particle source, s^-1
output.rcxna        = scan_b2_real(fid,'rcxna'       ,[nCv,ns]);   % charge-exchange atomic particle source, s^-1
output.rsamo        = scan_b2_real(fid,'rsamo'       ,[nCv,ns]);   % ionization momentum source, N
output.rramo        = scan_b2_real(fid,'rramo'       ,[nCv,ns]);   % recombination momentum source, N
output.rcxmo        = scan_b2_real(fid,'rcxmo'       ,[nCv,ns]);   % charge-exchange momentum source, N
output.rsahi        = scan_b2_real(fid,'rsahi'       ,[nCv,ns]);   % ionization ion energy source, W
output.rrahi        = scan_b2_real(fid,'rrahi'       ,[nCv,ns]);   % recombination ion energy source, W
output.rcxhi        = scan_b2_real(fid,'rcxhi'       ,[nCv,ns]);   % charge-exchange ion energy source, W
output.rqahe        = scan_b2_real(fid,'rqahe'       ,[nCv,ns]);   % electron cooling rate, W
output.rqrad        = scan_b2_real(fid,'rqrad'       ,[nCv,ns]);   % line radiation rate, W
output.rqbrm        = scan_b2_real(fid,'rqbrm'       ,[nCv,ns]);   % bremmstrahlung radiation rate, W

output.b2stbc_sna   = scan_b2_real(fid,'b2stbc_sna'  ,[nCv,ns]);   % boundary atomic particle source, s^-1
output.b2stbr_sna   = scan_b2_real(fid,'b2stbr_sna'  ,[nCv,ns]);   % recycling atomic particle source, s^-1
output.b2stbm_sna   = scan_b2_real(fid,'b2stbm_sna'  ,[nCv,ns]);   % additional atomic particle source, s^-1
output.b2stbc_smo   = scan_b2_real(fid,'b2stbc_smo'  ,[nCv,ns]);   % boundary momentum source, N
output.b2stbr_smo   = scan_b2_real(fid,'b2stbr_smo'  ,[nCv,ns]);   % recycling momentum source, N
output.b2stbm_smo   = scan_b2_real(fid,'b2stbm_smo'  ,[nCv,ns]);   % additional momentum source, N
output.b2stbc_she   = scan_b2_real(fid,'b2stbc_she'  ,[nCv]);      % boundary electron energy source, W
output.b2stbr_she   = scan_b2_real(fid,'b2stbr_she'  ,[nCv]);      % recycling electron energy source, W
output.b2stbm_she   = scan_b2_real(fid,'b2stbm_she'  ,[nCv]);      % additional electron energy source, W
output.b2stbc_shi   = scan_b2_real(fid,'b2stbc_shi'  ,[nCv]);      % boundary ion energy source, W
output.b2stbr_shi   = scan_b2_real(fid,'b2stbr_shi'  ,[nCv]);      % recycling ion energy source, W
output.b2stbm_shi   = scan_b2_real(fid,'b2stbm_shi'  ,[nCv]);      % additional ion energy source, W
output.b2stbc_sch   = scan_b2_real(fid,'b2stbc_sch'  ,[nCv]);      % boundary current source, A
output.b2stbr_sch   = scan_b2_real(fid,'b2stbr_sch'  ,[nCv]);      % recycling current source, A
output.b2stbc_sne   = scan_b2_real(fid,'b2stbc_sne'  ,[nCv]);      % boundary electron source, s^-1
output.b2stbr_sne   = scan_b2_real(fid,'b2stbr_sne'  ,[nCv]);      % recycling electron source, s^-1
output.b2stbm_sne   = scan_b2_real(fid,'b2stbm_sne'  ,[nCv]);      % additional electron source, s^-1

output.b2sihs_divua = scan_b2_real(fid,'b2sihs_divua',[nCv]);      % parallel-velocity-gradient ion heating, W
output.b2sihs_divue = scan_b2_real(fid,'b2sihs_divue',[nCv]);      % parallel-velocity-gradient electron heating, W
output.b2sihs_exba  = scan_b2_real(fid,'b2sihs_exba' ,[nCv]);      % ExB ion heating, W
output.b2sihs_exbe  = scan_b2_real(fid,'b2sihs_exbe' ,[nCv]);      % ExB electron heating, W
output.b2sihs_fraa  = scan_b2_real(fid,'b2sihs_fraa' ,[nCv]);      % friction heating, W
output.b2sihs_joule = scan_b2_real(fid,'b2sihs_joule',[nCv]);      % joule heating, W
output.b2sihs_str   = scan_b2_real(fid,'b2sihs_str ' ,[nCv]);      % strange heating, W
output.b2sihs_visa  = scan_b2_real(fid,'b2sihs_visa' ,[nCv]);      % viscosity heating, W


output.b2npmo_smaf  = scan_b2_real(fid,'b2npmo_smaf' ,[nCv,4,ns]); % friction momentum source, N
output.b2npmo_smag  = scan_b2_real(fid,'b2npmo_smag' ,[nCv,4,ns]); % pressure-gradient momentum source, N
output.b2npmo_smav  = scan_b2_real(fid,'b2npmo_smav' ,[nCv,4,ns]); % viscosity momentum source, N
output.smcf         = scan_b2_real(fid,'smcf'        ,[nCv,ns]);   % centrifugal force, N
output.smfr         = scan_b2_real(fid,'smfr'        ,[nCv,ns]);   % friction force, N
output.smpr         = scan_b2_real(fid,'smpr'        ,[nCv,ns]);   % electrostatic force, N
output.smpt         = scan_b2_real(fid,'smpt'        ,[nCv,ns]);   % thermal force, N

end

fprintf('Sources from b2fplasmf read\n');

frewind(fid);

end

%% READ THE RESIDUALS

if READ_RESIDUALS

if strcmp(version,'structured')

output.resco        = scan_b2_real(fid,'resco'       ,[nx+2,ny+2,ns]);  % continuity equation resitual, s^-1
output.reshe        = scan_b2_real(fid,'reshe'       ,[nx+2,ny+2]);     % electron energy equation resitual, W
output.reshi        = scan_b2_real(fid,'reshi'       ,[nx+2,ny+2]);     % ion energy equation resitual, W
output.resmo        = scan_b2_real(fid,'resmo'       ,[nx+2,ny+2,ns]);  % momentum equation resitual, N
output.resmt        = scan_b2_real(fid,'resmt'       ,[nx+2,ny+2]);     % total momentum equation resitual, N
output.respo        = scan_b2_real(fid,'respo'       ,[nx+2,ny+2]);     % potential equation resitual, A

elseif strcmp(version,'unstructured')

output.resco  = scan_b2_real(fid,'resco' ,[nCv,ns]);
output.reshe  = scan_b2_real(fid,'reshe' ,[nCv]);
output.reshi  = scan_b2_real(fid,'reshi' ,[nCv]);
output.reshn  = scan_b2_real(fid,'reshn' ,[nCv]);
output.resmo  = scan_b2_real(fid,'resmo' ,[nCv,ns]);
output.resmt  = scan_b2_real(fid,'resmt' ,[nCv]);
output.respo  = scan_b2_real(fid,'respo' ,[nCv]);
output.reskt  = scan_b2_real(fid,'reskt' ,[nCv]);

end

fprintf('Residuals from b2fplasmf read\n');

frewind(fid);

fclose(fid);

end

end