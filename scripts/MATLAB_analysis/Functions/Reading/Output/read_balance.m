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

output = struct();

%% READ THE STATE VARIABLES

if READ_STATE

output = set_raw_netcdf_value(output, file, 'na', 'na');
output.nx = size(output.na,1) - 2;
output.ny = size(output.na,2) - 2;
output.ns = size(output.na,3);

temp = ncread(file,'species');
output.species = cell(1, output.ns);
for i = 1:output.ns
    output.species{i} = strtrim(temp(:,i)');
end

output = set_raw_netcdf_values(output, file, {
    'ne', [], [];
    'ua', [], [];
    'Te', 'te', @(value) value .* 6.242e18;
    'Ti', 'ti', @(value) value .* 6.242e18;
    'po', [], [];
});

trim_two_rows = @(value) trim_last_rows(value, 2);
output = set_raw_netcdf_values(output, file, {
    'n_atm', 'dab2', trim_two_rows;
    'T_atm', 'tab2', trim_two_rows;
    'n_mol', 'dmb2', trim_two_rows;
    'T_mol', 'tmb2', trim_two_rows;
    'fn_atm_y', 'rfluxa', trim_two_rows;
    'fn_mol_y', 'rfluxm', trim_two_rows;
    'fn_atm_x', 'pfluxa', trim_two_rows;
    'fn_mol_x', 'pfluxm', trim_two_rows;
    'fe_atm_y', 'refluxa', trim_two_rows;
    'fe_mol_y', 'refluxm', trim_two_rows;
    'fe_atm_x', 'pefluxa', trim_two_rows;
    'fe_mol_x', 'pefluxm', trim_two_rows;
});

fprintf('State variables from balance.nc read\n');

end

%% READ THE FLUXES

if READ_FLUXES

output = set_raw_netcdf_values(output, file, {
    'fna_pll', [], [];
    'fna_pinch', [], [];
    'fna_drift', [], [];
    'fna_ch', [], [];
    'fna_nanom', [], [];
    'fna_panom', [], [];
    'fna_pschused', [], [];
    'fna_tot', [], [];
    'fmo_flua', [], [];
    'fmo_cvsa', [], [];
    'fmo_hybr', [], [];
    'fmo_b2nxfv', [], [];
    'fmo_tot', [], [];
    'pstat_bal', 'b2sigp_pstat_bal', [];
    'pstati_bal', 'b2sigp_pstati_bal', [];
    'pstate_bal', 'b2sigp_pstate_bal', [];
    'fhe_32', [], [];
    'fhe_52', [], [];
    'fhe_ecrb', [], [];
    'fhe_dia', [], [];
    'fhe_thermj', [], [];
    'fhe_pschused', [], [];
    'fhe_cond', [], [];
    'fhi_32', [], [];
    'fhi_52', [], [];
    'fhi_ecrb', [], [];
    'fhi_dia', [], [];
    'fhi_pschused', [], [];
    'fhi_inert', [], [];
    'fhi_vispar', [], [];
    'fhi_visper', [], [];
    'fhi_visq', [], [];
    'fhi_anml', [], [];
    'fhi_kevis', [], [];
    'fhi_cond', [], [];
    'za', [], [];
    'kinrgy', [], [];
    'rpt', [], [];
    'fne', [], [];
});

fprintf('Fluxes from balance.nc read\n');

end

%% READ THE SOURCES

if READ_SOURCES

output = set_raw_netcdf_values(output, file, {
    'b2stel_sna_ion', 'b2stel_sna_ion_bal', [];
    'b2stel_sna_rec', 'b2stel_sna_rec_bal', [];
    'b2stcx_sna', 'b2stcx_sna_bal', [];
    'b2stbc_sna', 'b2stbc_sna_bal', [];
    'b2stbr_phys_sna', 'b2stbr_phys_sna_bal', [];
    'b2stbr_first_flight_sna', 'b2stbr_first_flight_sna_bal', [];
    'b2stbm_sna', 'b2stbm_sna_bal', [];
    'ext_sna', 'ext_sna_bal', [];
    'b2srdt_snal', 'b2srdt_sna_bal', [];
    'b2srsm_sna', 'b2srsm_sna_bal', [];
    'b2srst_sna', 'b2srst_sna_bal', [];
    'b2sigp_smogpi', 'b2sigp_smogpi_bal', [];
    'b2sigp_smogpe', 'b2sigp_smogpe_bal', [];
    'b2sigp_smogp', 'b2sigp_smogp_bal', [];
    'b2stel_smq_ion', 'b2stel_smq_ion_bal', [];
    'b2stel_smq_rec', 'b2stel_smq_rec_bal', [];
    'b2stcx_smq', 'b2stcx_smq_bal', [];
    'b2sifr_smoch', 'b2sifr_smoch_bal', [];
    'b2sifr_smotf_ehxp', 'b2sifr_smotf_ehxp_bal', [];
    'b2sifr_smotf_cthe', 'b2sifr_smotf_cthe_bal', [];
    'b2sifr_smotf_cthi', 'b2sifr_smotf_cthi_bal', [];
    'b2sifr_smofrea', 'b2sifr_smofrea_bal', [];
    'b2sifr_smofria', 'b2sifr_smofria_bal', [];
    'b2sifr_smotfea', 'b2sifr_smotfea_bal', [];
    'b2sifr_smotfia', 'b2sifr_smotfia_bal', [];
    'b2siav_smovh', 'b2siav_smovh_bal', [];
    'b2siav_smovv', 'b2siav_smovv_bal', [];
    'b2sicf_smo', 'b2sicf_smo_bal', [];
    'b2sian_smo', 'b2sian_smo_bal', [];
    'b2nxdv_smo', 'b2nxdv_smo_bal', [];
    'b2stbc_smo', 'b2stbc_smo_bal', [];
    'b2stbr_phys_smo', 'b2stbr_phys_smo_bal', [];
    'b2stbm_smo', 'b2stbm_smo_bal', [];
    'ext_smo', 'ext_smo_bal', [];
    'b2srdt_smo', 'b2srdt_smo_bal', [];
    'b2srsm_smo', 'b2srsm_smo_bal', [];
    'b2srst_smo', 'b2srst_smo_bal', [];
    'b2sihs_divue', 'b2sihs_divue_bal', [];
    'b2stel_she', 'b2stel_she_bal', [];
    'b2sihs_joule', 'b2sihs_joule_bal', [];
    'b2sihs_diae', 'b2sihs_diae_bal', [];
    'b2sihs_exbe', 'b2sihs_exbe_bal', [];
    'b2npht_she', 'b2npht_shei_bal', @uminus;
    'b2stbc_she', 'b2stbc_she_bal', [];
    'b2stbr_phys_she', 'b2stbr_phys_she_bal', [];
    'b2stbr_first_flight_she', 'b2stbr_first_flight_she_bal', [];
    'b2stbm_she', 'b2stbm_she_bal', [];
    'ext_she', 'ext_she_bal', [];
    'b2srdt_she', 'b2srdt_she_bal', [];
    'b2srsm_she', 'b2srsm_she_bal', [];
    'b2srst_she', 'b2srst_she_bal', [];
    'b2sihs_divua', 'b2sihs_divua_bal', [];
    'b2sihs_visa', 'b2sihs_visa_bal', [];
    'b2stel_shi_ion', 'b2stel_shi_ion_bal', [];
    'b2stel_shi_rec', 'b2stel_shi_rec_bal', [];
    'b2stcx_shi', 'b2stcx_shi_bal', [];
    'b2sihs_fraa', 'b2sihs_fraa_bal', [];
    'b2sihs_diaa', 'b2sihs_diaa_bal', [];
    'b2sihs_exba', 'b2sihs_exba_bal', [];
    'b2npht_shi', 'b2npht_shei_bal', [];
    'b2stbc_shi', 'b2stbc_shi_bal', [];
    'b2stbr_phys_shi', 'b2stbr_phys_shi_bal', [];
    'b2stbr_first_flight_shi', 'b2stbr_first_flight_shi_bal', [];
    'b2stbm_shi', 'b2stbm_shi_bal', [];
    'ext_shi', 'ext_shi_bal', [];
    'b2srdt_shi', 'b2srdt_shi_bal', [];
    'b2srsm_shi', 'b2srsm_shi_bal', [];
    'b2srst_shi', 'b2srst_shi_bal', [];
    'eirene_papl_sna', 'eirene_mc_papl_sna_bal', [];
    'eirene_pmpl_sna', 'eirene_mc_pmpl_sna_bal', [];
    'eirene_pipl_sna', 'eirene_mc_pipl_sna_bal', [];
    'eirene_pppl_sna', 'eirene_mc_pppl_sna_bal', [];
    'eirene_core_sna', 'eirene_mc_core_sna_bal', [];
    'eirene_mapl_smo', 'eirene_mc_mapl_smo_bal', [];
    'eirene_mmpl_smo', 'eirene_mc_mmpl_smo_bal', [];
    'eirene_mipl_smo', 'eirene_mc_mipl_smo_bal', [];
    'eirene_eael_she', 'eirene_mc_eael_she_bal', [];
    'eirene_emel_she', 'eirene_mc_emel_she_bal', [];
    'eirene_eiel_she', 'eirene_mc_eiel_she_bal', [];
    'eirene_epel_she', 'eirene_mc_epel_she_bal', [];
    'eirene_eapl_shi', 'eirene_mc_eapl_shi_bal', [];
    'eirene_empl_shi', 'eirene_mc_empl_shi_bal', [];
    'eirene_eipl_shi', 'eirene_mc_eipl_shi_bal', [];
    'eirene_eppl_shi', 'eirene_mc_eppl_shi_bal', [];
});

output = try_set_raw_netcdf_value(output, file, 'b2stbr_bas_sna', 'b2stbr_bas_sna_bal');
output = try_set_raw_netcdf_value(output, file, 'b2stbr_bas_smo', 'b2stbr_bas_smo_bal');
output = try_set_raw_netcdf_value(output, file, 'b2stbr_bas_she', 'b2stbr_bas_she_bal');
output = try_set_raw_netcdf_value(output, file, 'b2stbr_bas_shi', 'b2stbr_bas_shi_bal');
output = try_set_raw_netcdf_value(output, file, 'b2stbr_first_flight_smo', 'b2stbr_first_flight_smo_bal');

try
    output = set_raw_netcdf_value(output, file, 'eirene_mppl_smo', 'eirene_mc_cppv_smo_bal');
catch
    output = set_raw_netcdf_value(output, file, 'eirene_mppl_smo', 'eirene_mc_mppl_smo_bal');
end

fprintf('Sources from balance.nc read\n');

end

%% READ THE RESIDUALS

if READ_RESIDUALS

output = set_raw_netcdf_values(output, file, {
    'resco', [], [];
    'resmo', [], [];
    'reshe', [], [];
    'reshi', [], [];
});

fprintf('Residuals from balance.nc read\n');

end

fclose(fid);

end
