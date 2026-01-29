function [state_variables_movies,fluxes_movies,sources_movies] = read_b2movies(varargin)
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

if any(strcmp(varargin,'EIRENE_STATE_VARIABLES')) || any(strcmp(varargin,'EIRENE_FLUXES')) || any(strcmp(varargin,'EIRENE_SOURCES'))

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

state_variables_movies = [];

if any(strcmp(varargin,'B25_STATE_VARIABLES')) || any(strcmp(varargin,'EIRENE_STATE_VARIABLES'))

    state_variables_movies.times = ncread(file,'times');

    if any(strcmp(varargin,'B25_STATE_VARIABLES'))

        try

            if strcmp(version,'structured')

                state_variables_movies.nx = b2fstate_nx;
                state_variables_movies.ny = b2fstate_ny;
                state_variables_movies.ns = b2fstate_ns;

            elseif strcmp(version,'unstructured')

                state_variables_movies.nCv = b2fstate_nCv;
                state_variables_movies.nFc = b2fstate_nFc;
                state_variables_movies.ns = b2fstate_ns;

            end

            [state_variables_movies.species,~,~] = read_species(simulation);

            state_variables_movies.na.value = ncread(file,'na');
            info = ncinfo(file,'na');
            state_variables_movies.na.description = ncreadatt(file,'na','long_name');
            state_variables_movies.na.unit = ncreadatt(file,'na','units');
            state_variables_movies.na.dimensions = {info.Dimensions.Name};

            state_variables_movies.ne.value = ncread(file,'ne');
            info = ncinfo(file,'ne');
            state_variables_movies.ne.description = ncreadatt(file,'ne','long_name');
            state_variables_movies.ne.unit = ncreadatt(file,'ne','units');
            state_variables_movies.ne.dimensions = {info.Dimensions.Name};

            try
                state_variables_movies.ua.value = ncread(file,'ua');
                info = ncinfo(file,'ua');
                state_variables_movies.ua.description = ncreadatt(file,'ua','long_name');
                state_variables_movies.ua.unit = ncreadatt(file,'ua','units');
                state_variables_movies.ua.dimensions = {info.Dimensions.Name};
            catch
            end

            state_variables_movies.Te.value = ncread(file,'te');
            info = ncinfo(file,'te');
            state_variables_movies.Te.description = ncreadatt(file,'te','long_name');
            state_variables_movies.Te.unit = ncreadatt(file,'te','units');
            state_variables_movies.Te.dimensions = {info.Dimensions.Name};

            state_variables_movies.Ti.value = ncread(file,'ti');
            info = ncinfo(file,'ti');
            state_variables_movies.Ti.description = ncreadatt(file,'ti','long_name');
            state_variables_movies.Ti.unit = ncreadatt(file,'ti','units');
            state_variables_movies.Ti.dimensions = {info.Dimensions.Name};

            state_variables_movies.po.value = ncread(file,'po');
            info = ncinfo(file,'po');
            state_variables_movies.po.description = ncreadatt(file,'po','long_name');
            state_variables_movies.po.unit = ncreadatt(file,'po','units');
            state_variables_movies.po.dimensions = {info.Dimensions.Name};

        catch
        end

    end

    if any(strcmp(varargin,'EIRENE_STATE_VARIABLES'))

        try

            if strcmp(version,'structured')

                state_variables_movies.nx = fort_44_nx;
                state_variables_movies.ny = fort_44_ny;

            elseif strcmp(version,'unstructured')

                state_variables_movies.nCv = fort_44_nCv;

            end

            state_variables_movies.natm = fort_44_natm;
            state_variables_movies.nmol = fort_44_nmol;
            state_variables_movies.nion = fort_44_nion;
            state_variables_movies.species_atm = fort_44_species_atm;
            state_variables_movies.species_mol = fort_44_species_mol;
            state_variables_movies.species_ion = fort_44_species_ion;

            state_variables_movies.n_atm.value = ncread(file,'dab2');
            info = ncinfo(file,'dab2');
            state_variables_movies.n_atm.description = ncreadatt(file,'dab2','long_name');
            state_variables_movies.n_atm.unit = ncreadatt(file,'dab2','units');
            state_variables_movies.n_atm.dimensions = {info.Dimensions.Name};

            state_variables_movies.T_atm.value = ncread(file,'tab2');
            info = ncinfo(file,'tab2');
            state_variables_movies.T_atm.description = ncreadatt(file,'tab2','long_name');
            state_variables_movies.T_atm.unit = ncreadatt(file,'tab2','units');
            state_variables_movies.T_atm.dimensions = {info.Dimensions.Name};

            state_variables_movies.n_mol.value = ncread(file,'dmb2');
            info = ncinfo(file,'dmb2');
            state_variables_movies.n_mol.description = ncreadatt(file,'dmb2','long_name');
            state_variables_movies.n_mol.unit = ncreadatt(file,'dmb2','units');
            state_variables_movies.n_mol.dimensions = {info.Dimensions.Name};

            state_variables_movies.T_mol.value = ncread(file,'tmb2');
            info = ncinfo(file,'tmb2');
            state_variables_movies.T_mol.description = ncreadatt(file,'tmb2','long_name');
            state_variables_movies.T_mol.unit = ncreadatt(file,'tmb2','units');
            state_variables_movies.T_mol.dimensions = {info.Dimensions.Name};

        catch
        end

    end

    fprintf('Structure STATE_VARIABLES_MOVIES from b2movies.nc read.\n');

end

%% READ THE FLUXES

fluxes_movies = [];

if any(strcmp(varargin,'B25_FLUXES')) || any(strcmp(varargin,'EIRENE_FLUXES'))

    fluxes_movies.times = ncread(file,'times');

    if any(strcmp(varargin,'B25_FLUXES'))

        try

            if strcmp(version,'structured')

                fluxes_movies.nx = b2fstate_nx;
                fluxes_movies.ny = b2fstate_ny;
                fluxes_movies.ns = b2fstate_ns;

            elseif strcmp(version,'unstructured')

                fluxes_movies.nCv = b2fstate_nCv;
                fluxes_movies.nFc = b2fstate_nFc;
                fluxes_movies.ns = b2fstate_ns;

            end

            [fluxes_movies.species,~,~] = read_species(simulation);

            fluxes_movies.fnax.value = ncread(file,'fnax');
            info = ncinfo(file,'fnax');
            fluxes_movies.fnax.description = ncreadatt(file,'fnax','long_name');
            fluxes_movies.fnax.unit = ncreadatt(file,'fnax','units');
            fluxes_movies.fnax.dimensions = {info.Dimensions.Name};

            fluxes_movies.fnay.value = ncread(file,'fnay');
            info = ncinfo(file,'fnay');
            fluxes_movies.fnay.description = ncreadatt(file,'fnay','long_name');
            fluxes_movies.fnay.unit = ncreadatt(file,'fnay','units');
            fluxes_movies.fnay.dimensions = {info.Dimensions.Name};

            fluxes_movies.fhex.value = ncread(file,'fhex');
            info = ncinfo(file,'fhex');
            fluxes_movies.fhex.description = ncreadatt(file,'fhex','long_name');
            fluxes_movies.fhex.unit = ncreadatt(file,'fhex','units');
            fluxes_movies.fhex.dimensions = {info.Dimensions.Name};

            fluxes_movies.fhey.value = ncread(file,'fhey');
            info = ncinfo(file,'fhey');
            fluxes_movies.fhey.description = ncreadatt(file,'fhey','long_name');
            fluxes_movies.fhey.unit = ncreadatt(file,'fhey','units');
            fluxes_movies.fhey.dimensions = {info.Dimensions.Name};

            fluxes_movies.fhix.value = ncread(file,'fhix');
            info = ncinfo(file,'fhix');
            fluxes_movies.fhix.description = ncreadatt(file,'fhix','long_name');
            fluxes_movies.fhix.unit = ncreadatt(file,'fhix','units');
            fluxes_movies.fhix.dimensions = {info.Dimensions.Name};

            fluxes_movies.fhiy.value = ncread(file,'fhiy');
            info = ncinfo(file,'fhiy');
            fluxes_movies.fhiy.description = ncreadatt(file,'fhiy','long_name');
            fluxes_movies.fhiy.unit = ncreadatt(file,'fhiy','units');
            fluxes_movies.fhiy.dimensions = {info.Dimensions.Name};

            fluxes_movies.fchx.value = ncread(file,'fchx');
            info = ncinfo(file,'fchx');
            fluxes_movies.fchx.description = ncreadatt(file,'fchx','long_name');
            fluxes_movies.fchx.unit = ncreadatt(file,'fchx','units');
            fluxes_movies.fchx.dimensions = {info.Dimensions.Name};

            fluxes_movies.fchy.value = ncread(file,'fchy');
            info = ncinfo(file,'fchy');
            fluxes_movies.fchy.description = ncreadatt(file,'fchy','long_name');
            fluxes_movies.fchy.unit = ncreadatt(file,'fchy','units');
            fluxes_movies.fchy.dimensions = {info.Dimensions.Name};

        catch
        end

    end

    if any(strcmp(varargin,'EIRENE_FLUXES'))

        try

            if strcmp(version,'structured')

                fluxes_movies.nx = fort_44_nx;
                fluxes_movies.ny = fort_44_ny;

            elseif strcmp(version,'unstructured')

                fluxes_movies.nCv = fort_44_nCv;

            end

            fluxes_movies.natm = fort_44_natm;
            fluxes_movies.nmol = fort_44_nmol;
            fluxes_movies.nion = fort_44_nion;
            fluxes_movies.species_atm = fort_44_species_atm;
            fluxes_movies.species_mol = fort_44_species_mol;
            fluxes_movies.species_ion = fort_44_species_ion;

            fluxes_movies.fn_atm_y.value = ncread(file,'rfluxa');
            info = ncinfo(file,'rfluxa');
            fluxes_movies.fn_atm_y.description = ncreadatt(file,'rfluxa','long_name');
            fluxes_movies.fn_atm_y.unit = ncreadatt(file,'rfluxa','units');
            fluxes_movies.fn_atm_y.dimensions = {info.Dimensions.Name};

            fluxes_movies.fn_atm_x.value = ncread(file,'pfluxa');
            info = ncinfo(file,'pfluxa');
            fluxes_movies.fn_atm_x.description = ncreadatt(file,'pfluxa','long_name');
            fluxes_movies.fn_atm_x.unit = ncreadatt(file,'pfluxa','units');
            fluxes_movies.fn_atm_x.dimensions = {info.Dimensions.Name};

            fluxes_movies.fe_atm_y.value = ncread(file,'refluxa');
            info = ncinfo(file,'refluxa');
            fluxes_movies.fe_atm_y.description = ncreadatt(file,'refluxa','long_name');
            fluxes_movies.fe_atm_y.unit = ncreadatt(file,'refluxa','units');
            fluxes_movies.fe_atm_y.dimensions = {info.Dimensions.Name};

            fluxes_movies.fe_atm_x.value = ncread(file,'pefluxa');
            info = ncinfo(file,'pefluxa');
            fluxes_movies.fe_atm_x.description = ncreadatt(file,'pefluxa','long_name');
            fluxes_movies.fe_atm_x.unit = ncreadatt(file,'pefluxa','units');
            fluxes_movies.fe_atm_x.dimensions = {info.Dimensions.Name};

            fluxes_movies.fn_mol_y.value = ncread(file,'rfluxm');
            info = ncinfo(file,'rfluxm');
            fluxes_movies.fn_mol_y.description = ncreadatt(file,'rfluxm','long_name');
            fluxes_movies.fn_mol_y.unit = ncreadatt(file,'rfluxm','units');
            fluxes_movies.fn_mol_y.dimensions = {info.Dimensions.Name};

            fluxes_movies.fn_mol_x.value = ncread(file,'pfluxm');
            info = ncinfo(file,'pfluxm');
            fluxes_movies.fn_mol_x.description = ncreadatt(file,'pfluxm','long_name');
            fluxes_movies.fn_mol_x.unit = ncreadatt(file,'pfluxm','units');
            fluxes_movies.fn_mol_x.dimensions = {info.Dimensions.Name};

            fluxes_movies.fe_mol_y.value = ncread(file,'refluxm');
            info = ncinfo(file,'refluxm');
            fluxes_movies.fe_mol_y.description = ncreadatt(file,'refluxm','long_name');
            fluxes_movies.fe_mol_y.unit = ncreadatt(file,'refluxm','units');
            fluxes_movies.fe_mol_y.dimensions = {info.Dimensions.Name};

            fluxes_movies.fe_mol_x.value = ncread(file,'pefluxm');
            info = ncinfo(file,'pefluxm');
            fluxes_movies.fe_mol_x.description = ncreadatt(file,'pefluxm','long_name');
            fluxes_movies.fe_mol_x.unit = ncreadatt(file,'pefluxm','units');
            fluxes_movies.fe_mol_x.dimensions = {info.Dimensions.Name};

        catch
        end

    end

    fprintf('Structure FLUXES_MOVIES from b2movies.nc read.\n');

end

%% READ THE SOURCES

sources_movies = [];

if any(strcmp(varargin,'B25_SOURCES')) || any(strcmp(varargin,'EIRENE_SOURCES'))

    sources_movies.times = ncread(file,'times');

    if any(strcmp(varargin,'B25_SOURCES'))

        try

            if strcmp(version,'structured')

                sources_movies.nx = b2fstate_nx;
                sources_movies.ny = b2fstate_ny;
                sources_movies.ns = b2fstate_ns;

            elseif strcmp(version,'unstructured')

                sources_movies.nCv = b2fstate_nCv;
                sources_movies.nFc = b2fstate_nFc;
                sources_movies.ns = b2fstate_ns;

            end

            [sources_movies.species,~,~] = read_species(simulation);

            sources_movies.rsana.value = ncread(file,'rsana');
            info = ncinfo(file,'rsana');
            sources_movies.rsana.description = ncreadatt(file,'rsana','long_name');
            sources_movies.rsana.unit = ncreadatt(file,'rsana','units');
            sources_movies.rsana.dimensions = {info.Dimensions.Name};

            sources_movies.rsahi.value = ncread(file,'rsahi');
            info = ncinfo(file,'rsahi');
            sources_movies.rsahi.description = ncreadatt(file,'rsahi','long_name');
            sources_movies.rsahi.unit = ncreadatt(file,'rsahi','units');
            sources_movies.rsahi.dimensions = {info.Dimensions.Name};

            sources_movies.rsahisum.value = ncread(file,'rsahisum');
            info = ncinfo(file,'rsahisum');
            sources_movies.rsahisum.description = ncreadatt(file,'rsahisum','long_name');
            sources_movies.rsahisum.unit = ncreadatt(file,'rsahisum','units');
            sources_movies.rsahisum.dimensions = {info.Dimensions.Name};

            sources_movies.rrana.value = ncread(file,'rrana');
            info = ncinfo(file,'rrana');
            sources_movies.rrana.description = ncreadatt(file,'rrana','long_name');
            sources_movies.rrana.unit = ncreadatt(file,'rrana','units');
            sources_movies.rrana.dimensions = {info.Dimensions.Name};

            sources_movies.rrahi.value = ncread(file,'rrahi');
            info = ncinfo(file,'rrahi');
            sources_movies.rrahi.description = ncreadatt(file,'rrahi','long_name');
            sources_movies.rrahi.unit = ncreadatt(file,'rrahi','units');
            sources_movies.rrahi.dimensions = {info.Dimensions.Name};

            sources_movies.rrahisum.value = ncread(file,'rrahisum');
            info = ncinfo(file,'rrahisum');
            sources_movies.rrahisum.description = ncreadatt(file,'rrahisum','long_name');
            sources_movies.rrahisum.unit = ncreadatt(file,'rrahisum','units');
            sources_movies.rrahisum.dimensions = {info.Dimensions.Name};

            sources_movies.rcxna.value = ncread(file,'rcxna');
            info = ncinfo(file,'rcxna');
            sources_movies.rcxna.description = ncreadatt(file,'rcxna','long_name');
            sources_movies.rcxna.unit = ncreadatt(file,'rcxna','units');
            sources_movies.rcxna.dimensions = {info.Dimensions.Name};

            sources_movies.rcxhi.value = ncread(file,'rcxhi');
            info = ncinfo(file,'rcxhi');
            sources_movies.rcxhi.description = ncreadatt(file,'rcxhi','long_name');
            sources_movies.rcxhi.unit = ncreadatt(file,'rcxhi','units');
            sources_movies.rcxhi.dimensions = {info.Dimensions.Name};

            sources_movies.rcxhisum.value = ncread(file,'rcxhisum');
            info = ncinfo(file,'rcxhisum');
            sources_movies.rcxhisum.description = ncreadatt(file,'rcxhisum','long_name');
            sources_movies.rcxhisum.unit = ncreadatt(file,'rcxhisum','units');
            sources_movies.rcxhisum.dimensions = {info.Dimensions.Name};

            sources_movies.rqahe.value = ncread(file,'rqahe');
            info = ncinfo(file,'rqahe');
            sources_movies.rqahe.description = ncreadatt(file,'rqahe','long_name');
            sources_movies.rqahe.unit = ncreadatt(file,'rqahe','units');
            sources_movies.rqahe.dimensions = {info.Dimensions.Name};

            sources_movies.rqahesum.value = ncread(file,'rqahesum');
            info = ncinfo(file,'rqahesum');
            sources_movies.rqahesum.description = ncreadatt(file,'rqahesum','long_name');
            sources_movies.rqahesum.unit = ncreadatt(file,'rqahesum','units');
            sources_movies.rqahesum.dimensions = {info.Dimensions.Name};

            sources_movies.rqrad.value = ncread(file,'rqrad');
            info = ncinfo(file,'rqrad');
            sources_movies.rqrad.description = ncreadatt(file,'rqrad','long_name');
            sources_movies.rqrad.unit = ncreadatt(file,'rqrad','units');
            sources_movies.rqrad.dimensions = {info.Dimensions.Name};

            sources_movies.rqradsum.value = ncread(file,'rqradsum');
            info = ncinfo(file,'rqradsum');
            sources_movies.rqradsum.description = ncreadatt(file,'rqradsum','long_name');
            sources_movies.rqradsum.unit = ncreadatt(file,'rqradsum','units');
            sources_movies.rqradsum.dimensions = {info.Dimensions.Name};

        catch
        end

    end

    if any(strcmp(varargin,'EIRENE_SOURCES'))

        try

            if strcmp(version,'structured')

                sources_movies.nx = b2fstate_nx;
                sources_movies.ny = b2fstate_ny;
                sources_movies.ns = b2fstate_ns;

            elseif strcmp(version,'unstructured')

                sources_movies.nCv = b2fstate_nCv;
                sources_movies.nFc = b2fstate_nFc;
                sources_movies.ns = b2fstate_ns;

            end

            sources_movies.natm = fort_44_natm;
            sources_movies.nmol = fort_44_nmol;
            sources_movies.nion = fort_44_nion;
            sources_movies.species_atm = fort_44_species_atm;
            sources_movies.species_mol = fort_44_species_mol;
            sources_movies.species_ion = fort_44_species_ion;

            sources_movies.eirene_papl_sna.value = ncread(file,'eirene_papl_sna');
            info = ncinfo(file,'eirene_papl_sna');
            sources_movies.eirene_papl_sna.description = ncreadatt(file,'eirene_papl_sna','long_name');
            sources_movies.eirene_papl_sna.unit = ncreadatt(file,'eirene_papl_sna','units');
            sources_movies.eirene_papl_sna.dimensions = {info.Dimensions.Name};

            sources_movies.eirene_pmpl_sna.value = ncread(file,'eirene_pmpl_sna');
            info = ncinfo(file,'eirene_pmpl_sna');
            sources_movies.eirene_pmpl_sna.description = ncreadatt(file,'eirene_pmpl_sna','long_name');
            sources_movies.eirene_pmpl_sna.unit = ncreadatt(file,'eirene_pmpl_sna','units');
            sources_movies.eirene_pmpl_sna.dimensions = {info.Dimensions.Name};

            sources_movies.eirene_pppl_sna.value = ncread(file,'eirene_pppl_sna');
            info = ncinfo(file,'eirene_pppl_sna');
            sources_movies.eirene_pppl_sna.description = ncreadatt(file,'eirene_pppl_sna','long_name');
            sources_movies.eirene_pppl_sna.unit = ncreadatt(file,'eirene_pppl_sna','units');
            sources_movies.eirene_pppl_sna.dimensions = {info.Dimensions.Name};

            sources_movies.eirene_eael_sna.value = ncread(file,'eirene_eael_she');
            info = ncinfo(file,'eirene_eael_she');
            sources_movies.eirene_eael_sna.description = ncreadatt(file,'eirene_eael_she','long_name');
            sources_movies.eirene_eael_sna.unit = ncreadatt(file,'eirene_eael_she','units');
            sources_movies.eirene_eael_sna.dimensions = {info.Dimensions.Name};

            sources_movies.eirene_emel_sna.value = ncread(file,'eirene_emel_she');
            info = ncinfo(file,'eirene_emel_she');
            sources_movies.eirene_emel_sna.description = ncreadatt(file,'eirene_emel_she','long_name');
            sources_movies.eirene_emel_sna.unit = ncreadatt(file,'eirene_emel_she','units');
            sources_movies.eirene_emel_sna.dimensions = {info.Dimensions.Name};

            sources_movies.eirene_epel_sna.value = ncread(file,'eirene_epel_she');
            info = ncinfo(file,'eirene_epel_she');
            sources_movies.eirene_epel_sna.description = ncreadatt(file,'eirene_epel_she','long_name');
            sources_movies.eirene_epel_sna.unit = ncreadatt(file,'eirene_epel_she','units');
            sources_movies.eirene_epel_sna.dimensions = {info.Dimensions.Name};

            sources_movies.eirene_eapl_sna.value = ncread(file,'eirene_eapl_shi');
            info = ncinfo(file,'eirene_eapl_shi');
            sources_movies.eirene_eapl_sna.description = ncreadatt(file,'eirene_eapl_shi','long_name');
            sources_movies.eirene_eapl_sna.unit = ncreadatt(file,'eirene_eapl_shi','units');
            sources_movies.eirene_eapl_sna.dimensions = {info.Dimensions.Name};

            sources_movies.eirene_empl_sna.value = ncread(file,'eirene_empl_shi');
            info = ncinfo(file,'eirene_empl_shi');
            sources_movies.eirene_empl_sna.description = ncreadatt(file,'eirene_empl_shi','long_name');
            sources_movies.eirene_empl_sna.unit = ncreadatt(file,'eirene_empl_shi','units');
            sources_movies.eirene_empl_sna.dimensions = {info.Dimensions.Name};

            sources_movies.eirene_eppl_sna.value = ncread(file,'eirene_eppl_shi');
            info = ncinfo(file,'eirene_eppl_shi');
            sources_movies.eirene_eppl_sna.description = ncreadatt(file,'eirene_eppl_shi','long_name');
            sources_movies.eirene_eppl_sna.unit = ncreadatt(file,'eirene_eppl_shi','units');
            sources_movies.eirene_eppl_sna.dimensions = {info.Dimensions.Name};

            sources_movies.rad_atm.value = ncread(file,'eneutrad');
            info = ncinfo(file,'eneutrad');
            sources_movies.rad_atm.description = ncreadatt(file,'eneutrad','long_name');
            sources_movies.rad_atm.unit = ncreadatt(file,'eneutrad','units');
            sources_movies.rad_atm.dimensions = {info.Dimensions.Name};

            sources_movies.rad_atm_sum.value = ncread(file,'eneutradsum');
            info = ncinfo(file,'eneutradsum');
            sources_movies.rad_atm_sum.description = ncreadatt(file,'eneutradsum','long_name');
            sources_movies.rad_atm_sum.unit = ncreadatt(file,'eneutradsum','units');
            sources_movies.rad_atm_sum.dimensions = {info.Dimensions.Name};

            sources_movies.rad_mol.value = ncread(file,'emolrad');
            info = ncinfo(file,'emolrad');
            sources_movies.rad_mol.description = ncreadatt(file,'emolrad','long_name');
            sources_movies.rad_mol.unit = ncreadatt(file,'emolrad','units');
            sources_movies.rad_mol.dimensions = {info.Dimensions.Name};

            sources_movies.rad_mol_sum.value = ncread(file,'emolradsum');
            info = ncinfo(file,'emolradsum');
            sources_movies.rad_mol_sum.description = ncreadatt(file,'emolradsum','long_name');
            sources_movies.rad_mol_sum.unit = ncreadatt(file,'emolradsum','units');
            sources_movies.rad_mol_sum.dimensions = {info.Dimensions.Name};

        catch
        end

    end

    fprintf('Structure SOURCES_MOVIES from b2movies.nc read.\n');

end

fclose(fid);

end
