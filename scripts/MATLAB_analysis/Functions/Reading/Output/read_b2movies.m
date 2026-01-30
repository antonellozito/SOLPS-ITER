function output = read_b2movies(varargin)
%
% read_b2movies reads the b2movies.nc file created by B2.5
% Output is the structs "state_variables_movies", ""fluxes_movies
% and "sources_movies" with the 2D distributions of state variables,
% fluxes and sources (for both B2.5 and Eirene) on the B2.5 grid
% at all simulated times
%
% 1st input: main simulation structure
%
% Following inputs: strings which specify which subsets of fields
%                   should be read:
%                   - 'B25_STATE_VARIABLES'
%                   - 'B25_FLUXES'
%                   - 'B25_SOURCES'
%                   - 'EIRENE_STATE_VARIABLES'
%                   - 'EIRENE_FLUXES'
%                   - 'EIRENE_SOURCES'

%% PRELIMINARY OPERATIONS

% Load the files (b2fstate/b2fstati)

simulation = varargin{1};

index_state = find(contains({simulation.run.name},'b2fstate'));
index_stati = find(contains({simulation.run.name},'b2fstati'));
if isempty(index_state) && isempty(index_stati)
    error('Error: b2fstate/b2fstati not found');
end
file_state = simulation.run(index_state).file;
file_stati = simulation.run(index_stati).file;
fid_state = fopen(file_state);
fid_stati = fopen(file_stati);
if (fid_state == -1) && (fid_stati == -1)
    error('Error: b2fstate/b2fstati not found');
end
if not(fid_state == -1)
    fid = fid_state;
    fclose(fid_stati);
elseif (fid_state == -1) && not(fid_stati == -1)
    fid = fid_stati;
end

line    = fgetl(fid);
version = line(8:17);

% Select which group of fields to read

READ_B25_STATE_VARIABLES = false;
READ_B25_FLUXES = false;
READ_B25_SOURCES = false;
READ_EIRENE_STATE_VARIABLES = false;
READ_EIRENE_FLUXES = false;
READ_EIRENE_SOURCES = false;

if numel(varargin) == 1
    READ_B25_STATE_VARIABLES = true;
    READ_B25_FLUXES = true;
    READ_B25_SOURCES = true;
    READ_EIRENE_STATE_VARIABLES = true;
    READ_EIRENE_FLUXES = true;
    READ_EIRENE_SOURCES = true;
else
    if any(strcmp(varargin,'B25_STATE_VARIABLES'))
        READ_B25_STATE_VARIABLES = true;
    end
    if any(strcmp(varargin,'B25_FLUXES'))
        READ_B25_FLUXES = true;  
    end
    if any(strcmp(varargin,'B25_SOURCES'))
        READ_B25_SOURCES = true;
    end
    if any(strcmp(varargin,'EIRENE_STATE_VARIABLES'))
        READ_EIRENE_STATE_VARIABLES = true;  
    end
    if any(strcmp(varargin,'EIRENE_FLUXES'))
        READ_EIRENE_FLUXES = true;
    end
    if any(strcmp(varargin,'EIRENE_SOURCES'))
        READ_EIRENE_SOURCES = true;
    end
end

% Read the dimensions

if str2num(strrep(version,'.','')) >= str2num(strrep('03.002.000','.',''))

    version = 'unstructured';

    dim = scan_b2_int(fid,'nCv,nFc,ns',3);
    nCv  = dim(1);
    nFc  = dim(2);
    ns   = dim(3);

    b2fstate_nCv = nCv;
    b2fstate_nFc = nFc;
    b2fstate_ns = ns;

else

    version = 'structured';

    dim = scan_b2_int(fid,'nx,ny,ns',3);
    nx  = dim(1);
    ny  = dim(2);
    ns  = dim(3);

    b2fstate_nx = nx;
    b2fstate_ny = ny;
    b2fstate_ns = ns;

end

frewind(fid);

if READ_EIRENE_STATE_VARIABLES || READ_EIRENE_FLUXES || READ_EIRENE_SOURCES

    % Load the file (fort.44)

    simulation = varargin{1};

    index = find(contains({simulation.run.name},'fort.44'));
    if isempty(index)
        error('Error: fort.44 not found');
    end
    file = simulation.run(index).file;
    fid = fopen(file);
    if (fid == -1)
        error('Error: fort.44 not found');
    end

    line = fgetl(fid);
    countEntries = @(str) sum(~cellfun(@isempty, strsplit(str)));
    n = countEntries(line);
    if n==4
        version = 'structured';
    elseif n==3
        version = 'unstructured';
    end

    frewind(fid);

    if strcmp(version,'structured')

        dims = fscanf(fid,'%d',3);
        nx   = dims(1);
        ny   = dims(2);

        fort_44_nx = nx;
        fort_44_ny = ny;

    elseif strcmp(version,'unstructured')

        dims = fscanf(fid,'%d',3);
        nCv   = dims(1);

        fort_44_nCv = nCv;

    end

    frewind(fid);

    % Read the number of species (fort.44)

    fgetl(fid);

    dims = fscanf(fid,'%d',3);
    natm = dims(1);
    nmol = dims(2);
    nion = dims(3);
    fort_44_natm = natm;
    fort_44_nmol = nmol;
    fort_44_nion = nion;

    line = fgetl(fid);
    for i = 1:natm
        line = fgetl(fid);
        fort_44_species_atm{i} = strtrim(line);
    end
    for i = 1:nmol
        line = fgetl(fid);
        fort_44_species_mol{i} = strtrim(line);
    end
    for i = 1:nion
        line = fgetl(fid);
        fort_44_species_ion{i} = strtrim(line);
    end

    fclose(fid);

end

% Load the file (b2movies.nc)

simulation = varargin{1};

index = find(contains({simulation.run.name},'b2movies.nc'));
if isempty(index)
    error('Error: b2movies.nc not found');
end
file = simulation.run(index).file;
fid = fopen(file);
if (fid == -1)
    error('Error: b2movies.nc not found');
end

%% READ THE STATE VARIABLES

if READ_B25_STATE_VARIABLES || READ_EIRENE_STATE_VARIABLES

    output.times = ncread(file,'times');

    if READ_B25_STATE_VARIABLES

        try

            if strcmp(version,'structured')

                output.nx = b2fstate_nx;
                output.ny = b2fstate_ny;
                output.ns = b2fstate_ns;

            elseif strcmp(version,'unstructured')

                output.nCv = b2fstate_nCv;
                output.nFc = b2fstate_nFc;
                output.ns = b2fstate_ns;

            end

            [output.species,~,~] = read_species(simulation);

            output.na.value = ncread(file,'na');
            info = ncinfo(file,'na');
            output.na.description = ncreadatt(file,'na','long_name');
            output.na.unit = ncreadatt(file,'na','units');
            output.na.dimensions = {info.Dimensions.Name};

            output.ne.value = ncread(file,'ne');
            info = ncinfo(file,'ne');
            output.ne.description = ncreadatt(file,'ne','long_name');
            output.ne.unit = ncreadatt(file,'ne','units');
            output.ne.dimensions = {info.Dimensions.Name};

            try
                output.ua.value = ncread(file,'ua');
                info = ncinfo(file,'ua');
                output.ua.description = ncreadatt(file,'ua','long_name');
                output.ua.unit = ncreadatt(file,'ua','units');
                output.ua.dimensions = {info.Dimensions.Name};
            catch
            end

            output.Te.value = ncread(file,'te');
            info = ncinfo(file,'te');
            output.Te.description = ncreadatt(file,'te','long_name');
            output.Te.unit = ncreadatt(file,'te','units');
            output.Te.dimensions = {info.Dimensions.Name};

            output.Ti.value = ncread(file,'ti');
            info = ncinfo(file,'ti');
            output.Ti.description = ncreadatt(file,'ti','long_name');
            output.Ti.unit = ncreadatt(file,'ti','units');
            output.Ti.dimensions = {info.Dimensions.Name};

            output.po.value = ncread(file,'po');
            info = ncinfo(file,'po');
            output.po.description = ncreadatt(file,'po','long_name');
            output.po.unit = ncreadatt(file,'po','units');
            output.po.dimensions = {info.Dimensions.Name};

        catch
        end

    end

    if READ_EIRENE_STATE_VARIABLES

        try

            if strcmp(version,'structured')

                output.nx = fort_44_nx;
                output.ny = fort_44_ny;

            elseif strcmp(version,'unstructured')

                output.nCv = fort_44_nCv;

            end

            output.natm = fort_44_natm;
            output.nmol = fort_44_nmol;
            output.nion = fort_44_nion;
            output.species_atm = fort_44_species_atm;
            output.species_mol = fort_44_species_mol;
            output.species_ion = fort_44_species_ion;

            output.n_atm.value = ncread(file,'dab2');
            info = ncinfo(file,'dab2');
            output.n_atm.description = ncreadatt(file,'dab2','long_name');
            output.n_atm.unit = ncreadatt(file,'dab2','units');
            output.n_atm.dimensions = {info.Dimensions.Name};

            output.T_atm.value = ncread(file,'tab2');
            info = ncinfo(file,'tab2');
            output.T_atm.description = ncreadatt(file,'tab2','long_name');
            output.T_atm.unit = ncreadatt(file,'tab2','units');
            output.T_atm.dimensions = {info.Dimensions.Name};

            output.n_mol.value = ncread(file,'dmb2');
            info = ncinfo(file,'dmb2');
            output.n_mol.description = ncreadatt(file,'dmb2','long_name');
            output.n_mol.unit = ncreadatt(file,'dmb2','units');
            output.n_mol.dimensions = {info.Dimensions.Name};

            output.T_mol.value = ncread(file,'tmb2');
            info = ncinfo(file,'tmb2');
            output.T_mol.description = ncreadatt(file,'tmb2','long_name');
            output.T_mol.unit = ncreadatt(file,'tmb2','units');
            output.T_mol.dimensions = {info.Dimensions.Name};

        catch
        end

    end

    fprintf('Time-dependent state variables from b2movies.nc read\n');

end

%% READ THE FLUXES

fluxes_movies = [];

if READ_B25_FLUXES || READ_EIRENE_FLUXES

    output.times = ncread(file,'times');

    if READ_B25_FLUXES

        try

            if strcmp(version,'structured')

                output.nx = b2fstate_nx;
                output.ny = b2fstate_ny;
                output.ns = b2fstate_ns;

            elseif strcmp(version,'unstructured')

                output.nCv = b2fstate_nCv;
                output.nFc = b2fstate_nFc;
                output.ns = b2fstate_ns;

            end

            [output.species,~,~] = read_species(simulation);

            output.fnax.value = ncread(file,'fnax');
            info = ncinfo(file,'fnax');
            output.fnax.description = ncreadatt(file,'fnax','long_name');
            output.fnax.unit = ncreadatt(file,'fnax','units');
            output.fnax.dimensions = {info.Dimensions.Name};

            output.fnay.value = ncread(file,'fnay');
            info = ncinfo(file,'fnay');
            output.fnay.description = ncreadatt(file,'fnay','long_name');
            output.fnay.unit = ncreadatt(file,'fnay','units');
            output.fnay.dimensions = {info.Dimensions.Name};

            output.fhex.value = ncread(file,'fhex');
            info = ncinfo(file,'fhex');
            output.fhex.description = ncreadatt(file,'fhex','long_name');
            output.fhex.unit = ncreadatt(file,'fhex','units');
            output.fhex.dimensions = {info.Dimensions.Name};

            output.fhey.value = ncread(file,'fhey');
            info = ncinfo(file,'fhey');
            output.fhey.description = ncreadatt(file,'fhey','long_name');
            output.fhey.unit = ncreadatt(file,'fhey','units');
            output.fhey.dimensions = {info.Dimensions.Name};

            output.fhix.value = ncread(file,'fhix');
            info = ncinfo(file,'fhix');
            output.fhix.description = ncreadatt(file,'fhix','long_name');
            output.fhix.unit = ncreadatt(file,'fhix','units');
            output.fhix.dimensions = {info.Dimensions.Name};

            output.fhiy.value = ncread(file,'fhiy');
            info = ncinfo(file,'fhiy');
            output.fhiy.description = ncreadatt(file,'fhiy','long_name');
            output.fhiy.unit = ncreadatt(file,'fhiy','units');
            output.fhiy.dimensions = {info.Dimensions.Name};

            output.fchx.value = ncread(file,'fchx');
            info = ncinfo(file,'fchx');
            output.fchx.description = ncreadatt(file,'fchx','long_name');
            output.fchx.unit = ncreadatt(file,'fchx','units');
            output.fchx.dimensions = {info.Dimensions.Name};

            output.fchy.value = ncread(file,'fchy');
            info = ncinfo(file,'fchy');
            output.fchy.description = ncreadatt(file,'fchy','long_name');
            output.fchy.unit = ncreadatt(file,'fchy','units');
            output.fchy.dimensions = {info.Dimensions.Name};

        catch
        end

    end

    if READ_EIRENE_FLUXES

        try

            if strcmp(version,'structured')

                output.nx = fort_44_nx;
                output.ny = fort_44_ny;

            elseif strcmp(version,'unstructured')

                output.nCv = fort_44_nCv;

            end

            output.natm = fort_44_natm;
            output.nmol = fort_44_nmol;
            output.nion = fort_44_nion;
            output.species_atm = fort_44_species_atm;
            output.species_mol = fort_44_species_mol;
            output.species_ion = fort_44_species_ion;

            output.fn_atm_y.value = ncread(file,'rfluxa');
            info = ncinfo(file,'rfluxa');
            output.fn_atm_y.description = ncreadatt(file,'rfluxa','long_name');
            output.fn_atm_y.unit = ncreadatt(file,'rfluxa','units');
            output.fn_atm_y.dimensions = {info.Dimensions.Name};

            output.fn_atm_x.value = ncread(file,'pfluxa');
            info = ncinfo(file,'pfluxa');
            output.fn_atm_x.description = ncreadatt(file,'pfluxa','long_name');
            output.fn_atm_x.unit = ncreadatt(file,'pfluxa','units');
            output.fn_atm_x.dimensions = {info.Dimensions.Name};

            output.fe_atm_y.value = ncread(file,'refluxa');
            info = ncinfo(file,'refluxa');
            output.fe_atm_y.description = ncreadatt(file,'refluxa','long_name');
            output.fe_atm_y.unit = ncreadatt(file,'refluxa','units');
            output.fe_atm_y.dimensions = {info.Dimensions.Name};

            output.fe_atm_x.value = ncread(file,'pefluxa');
            info = ncinfo(file,'pefluxa');
            output.fe_atm_x.description = ncreadatt(file,'pefluxa','long_name');
            output.fe_atm_x.unit = ncreadatt(file,'pefluxa','units');
            output.fe_atm_x.dimensions = {info.Dimensions.Name};

            output.fn_mol_y.value = ncread(file,'rfluxm');
            info = ncinfo(file,'rfluxm');
            output.fn_mol_y.description = ncreadatt(file,'rfluxm','long_name');
            output.fn_mol_y.unit = ncreadatt(file,'rfluxm','units');
            output.fn_mol_y.dimensions = {info.Dimensions.Name};

            output.fn_mol_x.value = ncread(file,'pfluxm');
            info = ncinfo(file,'pfluxm');
            output.fn_mol_x.description = ncreadatt(file,'pfluxm','long_name');
            output.fn_mol_x.unit = ncreadatt(file,'pfluxm','units');
            output.fn_mol_x.dimensions = {info.Dimensions.Name};

            output.fe_mol_y.value = ncread(file,'refluxm');
            info = ncinfo(file,'refluxm');
            output.fe_mol_y.description = ncreadatt(file,'refluxm','long_name');
            output.fe_mol_y.unit = ncreadatt(file,'refluxm','units');
            output.fe_mol_y.dimensions = {info.Dimensions.Name};

            output.fe_mol_x.value = ncread(file,'pefluxm');
            info = ncinfo(file,'pefluxm');
            output.fe_mol_x.description = ncreadatt(file,'pefluxm','long_name');
            output.fe_mol_x.unit = ncreadatt(file,'pefluxm','units');
            output.fe_mol_x.dimensions = {info.Dimensions.Name};

        catch
        end

    end

    fprintf('Time-dependent fluxes from b2movies.nc read\n');

end

%% READ THE SOURCES

if READ_B25_SOURCES || READ_EIRENE_SOURCES

    output.times = ncread(file,'times');

    if READ_B25_SOURCES

        try

            if strcmp(version,'structured')

                output.nx = b2fstate_nx;
                output.ny = b2fstate_ny;
                output.ns = b2fstate_ns;

            elseif strcmp(version,'unstructured')

                output.nCv = b2fstate_nCv;
                output.nFc = b2fstate_nFc;
                output.ns = b2fstate_ns;

            end

            [output.species,~,~] = read_species(simulation);

            output.rsana.value = ncread(file,'rsana');
            info = ncinfo(file,'rsana');
            output.rsana.description = ncreadatt(file,'rsana','long_name');
            output.rsana.unit = ncreadatt(file,'rsana','units');
            output.rsana.dimensions = {info.Dimensions.Name};

            output.rsahi.value = ncread(file,'rsahi');
            info = ncinfo(file,'rsahi');
            output.rsahi.description = ncreadatt(file,'rsahi','long_name');
            output.rsahi.unit = ncreadatt(file,'rsahi','units');
            output.rsahi.dimensions = {info.Dimensions.Name};

            output.rsahisum.value = ncread(file,'rsahisum');
            info = ncinfo(file,'rsahisum');
            output.rsahisum.description = ncreadatt(file,'rsahisum','long_name');
            output.rsahisum.unit = ncreadatt(file,'rsahisum','units');
            output.rsahisum.dimensions = {info.Dimensions.Name};

            output.rrana.value = ncread(file,'rrana');
            info = ncinfo(file,'rrana');
            output.rrana.description = ncreadatt(file,'rrana','long_name');
            output.rrana.unit = ncreadatt(file,'rrana','units');
            output.rrana.dimensions = {info.Dimensions.Name};

            output.rrahi.value = ncread(file,'rrahi');
            info = ncinfo(file,'rrahi');
            output.rrahi.description = ncreadatt(file,'rrahi','long_name');
            output.rrahi.unit = ncreadatt(file,'rrahi','units');
            output.rrahi.dimensions = {info.Dimensions.Name};

            output.rrahisum.value = ncread(file,'rrahisum');
            info = ncinfo(file,'rrahisum');
            output.rrahisum.description = ncreadatt(file,'rrahisum','long_name');
            output.rrahisum.unit = ncreadatt(file,'rrahisum','units');
            output.rrahisum.dimensions = {info.Dimensions.Name};

            output.rcxna.value = ncread(file,'rcxna');
            info = ncinfo(file,'rcxna');
            output.rcxna.description = ncreadatt(file,'rcxna','long_name');
            output.rcxna.unit = ncreadatt(file,'rcxna','units');
            output.rcxna.dimensions = {info.Dimensions.Name};

            output.rcxhi.value = ncread(file,'rcxhi');
            info = ncinfo(file,'rcxhi');
            output.rcxhi.description = ncreadatt(file,'rcxhi','long_name');
            output.rcxhi.unit = ncreadatt(file,'rcxhi','units');
            output.rcxhi.dimensions = {info.Dimensions.Name};

            output.rcxhisum.value = ncread(file,'rcxhisum');
            info = ncinfo(file,'rcxhisum');
            output.rcxhisum.description = ncreadatt(file,'rcxhisum','long_name');
            output.rcxhisum.unit = ncreadatt(file,'rcxhisum','units');
            output.rcxhisum.dimensions = {info.Dimensions.Name};

            output.rqahe.value = ncread(file,'rqahe');
            info = ncinfo(file,'rqahe');
            output.rqahe.description = ncreadatt(file,'rqahe','long_name');
            output.rqahe.unit = ncreadatt(file,'rqahe','units');
            output.rqahe.dimensions = {info.Dimensions.Name};

            output.rqahesum.value = ncread(file,'rqahesum');
            info = ncinfo(file,'rqahesum');
            output.rqahesum.description = ncreadatt(file,'rqahesum','long_name');
            output.rqahesum.unit = ncreadatt(file,'rqahesum','units');
            output.rqahesum.dimensions = {info.Dimensions.Name};

            output.rqrad.value = ncread(file,'rqrad');
            info = ncinfo(file,'rqrad');
            output.rqrad.description = ncreadatt(file,'rqrad','long_name');
            output.rqrad.unit = ncreadatt(file,'rqrad','units');
            output.rqrad.dimensions = {info.Dimensions.Name};

            output.rqradsum.value = ncread(file,'rqradsum');
            info = ncinfo(file,'rqradsum');
            output.rqradsum.description = ncreadatt(file,'rqradsum','long_name');
            output.rqradsum.unit = ncreadatt(file,'rqradsum','units');
            output.rqradsum.dimensions = {info.Dimensions.Name};

        catch
        end

    end

    if READ_EIRENE_SOURCES

        try

            if strcmp(version,'structured')

                output.nx = b2fstate_nx;
                output.ny = b2fstate_ny;
                output.ns = b2fstate_ns;

            elseif strcmp(version,'unstructured')

                output.nCv = b2fstate_nCv;
                output.nFc = b2fstate_nFc;
                output.ns = b2fstate_ns;

            end

            output.natm = fort_44_natm;
            output.nmol = fort_44_nmol;
            output.nion = fort_44_nion;
            output.species_atm = fort_44_species_atm;
            output.species_mol = fort_44_species_mol;
            output.species_ion = fort_44_species_ion;

            output.eirene_papl_sna.value = ncread(file,'eirene_papl_sna');
            info = ncinfo(file,'eirene_papl_sna');
            output.eirene_papl_sna.description = ncreadatt(file,'eirene_papl_sna','long_name');
            output.eirene_papl_sna.unit = ncreadatt(file,'eirene_papl_sna','units');
            output.eirene_papl_sna.dimensions = {info.Dimensions.Name};

            output.eirene_pmpl_sna.value = ncread(file,'eirene_pmpl_sna');
            info = ncinfo(file,'eirene_pmpl_sna');
            output.eirene_pmpl_sna.description = ncreadatt(file,'eirene_pmpl_sna','long_name');
            output.eirene_pmpl_sna.unit = ncreadatt(file,'eirene_pmpl_sna','units');
            output.eirene_pmpl_sna.dimensions = {info.Dimensions.Name};

            output.eirene_pppl_sna.value = ncread(file,'eirene_pppl_sna');
            info = ncinfo(file,'eirene_pppl_sna');
            output.eirene_pppl_sna.description = ncreadatt(file,'eirene_pppl_sna','long_name');
            output.eirene_pppl_sna.unit = ncreadatt(file,'eirene_pppl_sna','units');
            output.eirene_pppl_sna.dimensions = {info.Dimensions.Name};

            output.eirene_eael_sna.value = ncread(file,'eirene_eael_she');
            info = ncinfo(file,'eirene_eael_she');
            output.eirene_eael_sna.description = ncreadatt(file,'eirene_eael_she','long_name');
            output.eirene_eael_sna.unit = ncreadatt(file,'eirene_eael_she','units');
            output.eirene_eael_sna.dimensions = {info.Dimensions.Name};

            output.eirene_emel_sna.value = ncread(file,'eirene_emel_she');
            info = ncinfo(file,'eirene_emel_she');
            output.eirene_emel_sna.description = ncreadatt(file,'eirene_emel_she','long_name');
            output.eirene_emel_sna.unit = ncreadatt(file,'eirene_emel_she','units');
            output.eirene_emel_sna.dimensions = {info.Dimensions.Name};

            output.eirene_epel_sna.value = ncread(file,'eirene_epel_she');
            info = ncinfo(file,'eirene_epel_she');
            output.eirene_epel_sna.description = ncreadatt(file,'eirene_epel_she','long_name');
            output.eirene_epel_sna.unit = ncreadatt(file,'eirene_epel_she','units');
            output.eirene_epel_sna.dimensions = {info.Dimensions.Name};

            output.eirene_eapl_sna.value = ncread(file,'eirene_eapl_shi');
            info = ncinfo(file,'eirene_eapl_shi');
            output.eirene_eapl_sna.description = ncreadatt(file,'eirene_eapl_shi','long_name');
            output.eirene_eapl_sna.unit = ncreadatt(file,'eirene_eapl_shi','units');
            output.eirene_eapl_sna.dimensions = {info.Dimensions.Name};

            output.eirene_empl_sna.value = ncread(file,'eirene_empl_shi');
            info = ncinfo(file,'eirene_empl_shi');
            output.eirene_empl_sna.description = ncreadatt(file,'eirene_empl_shi','long_name');
            output.eirene_empl_sna.unit = ncreadatt(file,'eirene_empl_shi','units');
            output.eirene_empl_sna.dimensions = {info.Dimensions.Name};

            output.eirene_eppl_sna.value = ncread(file,'eirene_eppl_shi');
            info = ncinfo(file,'eirene_eppl_shi');
            output.eirene_eppl_sna.description = ncreadatt(file,'eirene_eppl_shi','long_name');
            output.eirene_eppl_sna.unit = ncreadatt(file,'eirene_eppl_shi','units');
            output.eirene_eppl_sna.dimensions = {info.Dimensions.Name};

            output.rad_atm.value = ncread(file,'eneutrad');
            info = ncinfo(file,'eneutrad');
            output.rad_atm.description = ncreadatt(file,'eneutrad','long_name');
            output.rad_atm.unit = ncreadatt(file,'eneutrad','units');
            output.rad_atm.dimensions = {info.Dimensions.Name};

            output.rad_atm_sum.value = ncread(file,'eneutradsum');
            info = ncinfo(file,'eneutradsum');
            output.rad_atm_sum.description = ncreadatt(file,'eneutradsum','long_name');
            output.rad_atm_sum.unit = ncreadatt(file,'eneutradsum','units');
            output.rad_atm_sum.dimensions = {info.Dimensions.Name};

            output.rad_mol.value = ncread(file,'emolrad');
            info = ncinfo(file,'emolrad');
            output.rad_mol.description = ncreadatt(file,'emolrad','long_name');
            output.rad_mol.unit = ncreadatt(file,'emolrad','units');
            output.rad_mol.dimensions = {info.Dimensions.Name};

            output.rad_mol_sum.value = ncread(file,'emolradsum');
            info = ncinfo(file,'emolradsum');
            output.rad_mol_sum.description = ncreadatt(file,'emolradsum','long_name');
            output.rad_mol_sum.unit = ncreadatt(file,'emolradsum','units');
            output.rad_mol_sum.dimensions = {info.Dimensions.Name};

        catch
        end

    end

    fprintf('Time-dependent sources from b2movies.nc read\n');

end

fclose(fid);

end
