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

            output = set_netcdf_fields(output, file, {
                'na', 'na';
                'ne', 'ne';
                'Te', 'te';
                'Ti', 'ti';
                'po', 'po';
            });

            try
                output = set_netcdf_field(output, file, 'ua', 'ua');
            catch
            end

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

            output = set_netcdf_fields(output, file, {
                'n_atm', 'dab2';
                'T_atm', 'tab2';
                'n_mol', 'dmb2';
                'T_mol', 'tmb2';
            });

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

            output = set_netcdf_fields(output, file, {
                'fnax', 'fnax';
                'fnay', 'fnay';
                'fhex', 'fhex';
                'fhey', 'fhey';
                'fhix', 'fhix';
                'fhiy', 'fhiy';
                'fchx', 'fchx';
                'fchy', 'fchy';
            });

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

            output = set_netcdf_fields(output, file, {
                'fn_atm_y', 'rfluxa';
                'fn_atm_x', 'pfluxa';
                'fe_atm_y', 'refluxa';
                'fe_atm_x', 'pefluxa';
                'fn_mol_y', 'rfluxm';
                'fn_mol_x', 'pfluxm';
                'fe_mol_y', 'refluxm';
                'fe_mol_x', 'pefluxm';
            });

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

            output = set_netcdf_fields(output, file, {
                'rsana', 'rsana';
                'rsahi', 'rsahi';
                'rsahisum', 'rsahisum';
                'rrana', 'rrana';
                'rrahi', 'rrahi';
                'rrahisum', 'rrahisum';
                'rcxna', 'rcxna';
                'rcxhi', 'rcxhi';
                'rcxhisum', 'rcxhisum';
                'rqahe', 'rqahe';
                'rqahesum', 'rqahesum';
                'rqrad', 'rqrad';
                'rqradsum', 'rqradsum';
            });

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

            output = set_netcdf_fields(output, file, {
                'eirene_papl_sna', 'eirene_papl_sna';
                'eirene_pmpl_sna', 'eirene_pmpl_sna';
                'eirene_pppl_sna', 'eirene_pppl_sna';
                'eirene_eael_sna', 'eirene_eael_she';
                'eirene_emel_sna', 'eirene_emel_she';
                'eirene_epel_sna', 'eirene_epel_she';
                'eirene_eapl_sna', 'eirene_eapl_shi';
                'eirene_empl_sna', 'eirene_empl_shi';
                'eirene_eppl_sna', 'eirene_eppl_shi';
                'rad_atm', 'eneutrad';
                'rad_atm_sum', 'eneutradsum';
                'rad_mol', 'emolrad';
                'rad_mol_sum', 'emolradsum';
            });

        catch
        end

    end

    fprintf('Time-dependent sources from b2movies.nc read\n');

end

fclose(fid);

end
