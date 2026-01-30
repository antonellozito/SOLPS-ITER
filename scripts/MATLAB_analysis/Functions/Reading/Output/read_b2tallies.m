function output = read_b2tallies(varargin)
%
% read_tallies reads the b2tallies.nc file created by B2.5
% Output is a struct "surface_tallies" with all the x- and y- directed region surface tallies in the b2tallies.nc file
% and a struct "volume_tallies" with all volume tallies in the b2tallies.nc file
%
% 1st input: main simulation structure
%
% Following inputs: strings which specify which subsets of fields
%                   should be read:
%                   - 'SURFACE_TALLIES'
%                   - 'VOLUME_TALLIES'

%% PRELIMINARY OPERATIONS

% Load the file

simulation = varargin{1};

index = find(contains({simulation.run.name},'b2tallies.nc'));
if isempty(index)
   error('Error: b2tallies.nc not found');
end
file = simulation.run(index).file;
fid = fopen(file);
if (fid == -1)
   error('Error: b2tallies.nc not found');
end

% Select which group of fields to read

READ_SURFACE_TALLIES = false;
READ_VOLUME_TALLIES = false;

if numel(varargin) == 1
    READ_SURFACE_TALLIES = true;
    READ_VOLUME_TALLIES = true;
else
    if any(strcmp(varargin,'SURFACE_TALLIES'))
        READ_SURFACE_TALLIES = true;
    end
    if any(strcmp(varargin,'VOLUME_TALLIES'))
        READ_VOLUME_TALLIES = true;  
    end
end

%% READ SURFACE TALLIES

if READ_SURFACE_TALLIES

% Poloidal fluxes across each poloidal-directed surface

output.fnaxreg = ncread(file,'fnaxreg'); % Poloidal particle flux, s^-1
output.fhexreg = ncread(file,'fhexreg'); % Poloidal electron thermal energy flux, W
output.fhixreg = ncread(file,'fhixreg'); % Poloidal ion thermal energy flux, W
output.fhmxreg = ncread(file,'fhmxreg'); % Poloidal parallel kinetic energy flux, W
output.fhpxreg = ncread(file,'fhpxreg'); % Poloidal ionization energy flux, W
output.fhjxreg = ncread(file,'fhjxreg'); % Poloidal electrostatic energy flux, W
output.fhtxreg = ncread(file,'fhtxreg'); % Poloidal total energy flux, W
output.fchxreg = ncread(file,'fchxreg'); % Poloidal current, A

% Radial fluxes across each radial-directed surface

output.fnayreg = ncread(file,'fnayreg'); % Radial particle flux, s^-1
output.fheyreg = ncread(file,'fheyreg'); % Radial electron thermal energy flux, W
output.fhiyreg = ncread(file,'fhiyreg'); % Radial ion thermal energy flux, W
output.fhmyreg = ncread(file,'fhmyreg'); % Radial parallel kinetic energy flux, W
output.fhpyreg = ncread(file,'fhpyreg'); % Radial ionization energy flux, W
output.fhjyreg = ncread(file,'fhjyreg'); % Radial electrostatic energy flux, W
output.fhtyreg = ncread(file,'fhtyreg'); % Radial total energy flux, W
output.fchyreg = ncread(file,'fchyreg'); % Radial current, A

end

fprintf('Time-dependent surface tallies from b2tallies.nc read\n');

%% READ VOLUME TALLIES

if READ_VOLUME_TALLIES

output.b2stbc_sna_reg = ncread(file,'b2stbc_sna_reg'); % Boundary particle source, s^-1
output.b2stbc_sne_reg = ncread(file,'b2stbc_sne_reg'); % Boundary electron source, s^-1
output.b2stbc_smo_reg = ncread(file,'b2stbc_smo_reg'); % Boundary parallel momentum source, kg m s^-1
output.b2stbc_she_reg = ncread(file,'b2stbc_she_reg'); % Boundary electron energy source, W
output.b2stbc_shi_reg = ncread(file,'b2stbc_shi_reg'); % Boundary ion energy source, W
output.b2stbc_sch_reg = ncread(file,'b2stbc_sch_reg'); % Boundary charge source, A

output.b2stbr_sna_reg = ncread(file,'b2stbr_sna_reg'); % Recycling particle source, s^-1
output.b2stbr_sne_reg = ncread(file,'b2stbr_sne_reg'); % Recycling electron source, s^-1
output.b2stbr_smo_reg = ncread(file,'b2stbr_smo_reg'); % Recycling parallel momentum source, kg m s^-1
output.b2stbr_she_reg = ncread(file,'b2stbr_she_reg'); % Recycling electron energy source, W
output.b2stbr_shi_reg = ncread(file,'b2stbr_shi_reg'); % Recycling ion energy source, W
output.b2stbr_sch_reg = ncread(file,'b2stbr_sch_reg'); % Recycling charge source, A

output.b2stbm_sna_reg = ncread(file,'b2stbm_sna_reg'); % Additional particle source, s^-1
output.b2stbm_sne_reg = ncread(file,'b2stbm_sne_reg'); % Additional electron source, s^-1
output.b2stbm_smo_reg = ncread(file,'b2stbm_smo_reg'); % Additional parallel momentum source, kg m s^-1
output.b2stbm_she_reg = ncread(file,'b2stbm_she_reg'); % Additional electron energy source, W
output.b2stbm_shi_reg = ncread(file,'b2stbm_shi_reg'); % Additional ion energy source, W
output.b2stbm_sch_reg = ncread(file,'b2stbm_sch_reg'); % Additional charge source, A

output.b2sext_sna_reg = ncread(file,'b2sext_sna_reg'); % External particle source, s^-1
output.b2sext_sne_reg = ncread(file,'b2sext_sne_reg'); % External electron source, s^-1
output.b2sext_smo_reg = ncread(file,'b2sext_smo_reg'); % External parallel momentum source, kg m s^-1
output.b2sext_she_reg = ncread(file,'b2sext_she_reg'); % External electron energy source, W
output.b2sext_shi_reg = ncread(file,'b2sext_shi_reg'); % External ion energy source, W
output.b2sext_sch_reg = ncread(file,'b2sext_sch_reg'); % External charge source, A

output.rcxnareg = ncread(file,'rcxnareg'); % Charge-exchange particle source, s^-1
output.rcxmoreg = ncread(file,'rcxmoreg'); % Charge-exchange parallel momentum source, s^-1
output.rcxhireg = ncread(file,'rcxhireg'); % Charge-exchange (ion) energy source, s^-1

output.rranareg = ncread(file,'rranareg'); % Recombination particle source, s^-1
output.rramoreg = ncread(file,'rramoreg'); % Recombination parallel momentum source, s^-1
output.rrahireg = ncread(file,'rrahireg'); % Recombination (ion) energy source, s^-1

output.rsanareg = ncread(file,'rsanareg'); % Ionization particle source, s^-1
output.rsamoreg = ncread(file,'rsamoreg'); % Ionization parallel momentum source, s^-1
output.rsahireg = ncread(file,'rsahireg'); % Ionization (ion) energy source, s^-1

output.b2divua = ncread(file,'b2divua'); % Ion velocity gradient heating, W
output.b2divue = ncread(file,'b2divue'); % Electron velocity gradient heating, W
output.b2exba = ncread(file,'b2exba'); % Ion ExB heating, W
output.b2exbe = ncread(file,'b2exbe'); % Electron ExB heating, W
output.b2fraa = ncread(file,'b2fraa'); % Inter-species friction heating, W
output.b2joule = ncread(file,'b2joule'); % Joule heating, W
output.b2qie = ncread(file,'b2qie'); % Electron/ion heat exchange, W
output.b2str = ncread(file,'b2str'); % Strange heating, W
output.b2visa = ncread(file,'b2visa'); % Ion viscous heating, W
output.b2bremreg = ncread(file,'b2bremreg'); % Bremsstrahlung radiation, W
output.b2radreg = ncread(file,'b2radreg'); % Line radiation, W
output.rdneureg = ncread(file,'rdneureg'); % Radiation from EIRENE neutrals, W

output.resco_reg = ncread(file,'resco_reg'); % Continuity equations residuals
output.resmo_reg = ncread(file,'resmo_reg'); % Parallel momentum equations residuals
output.reshe_reg = ncread(file,'reshe_reg'); % Electron energy equation residuals
output.reshi_reg = ncread(file,'reshi_reg'); % Ion energy equation residuals
output.respo_reg = ncread(file,'respo_reg'); % Potential equation residuals

fprintf('Time-dependent volume tallies from b2tallies.nc read\n');

end

fclose(fid);

end