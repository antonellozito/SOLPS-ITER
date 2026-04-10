function state = read_b2fstate(simulation)
%
% read_b2fstate reads the final plasma state file created by B2.5
% Output is a struct "state" with all the data fields in the b2fstate file
%
% input: main simulation structure
%
%% PRELIMINARY OPERATIONS

% Load the files and read the version

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

    dim = scan_b2_int(fid,'nCv,nFc,ns',3);
    nCv  = dim(1);
    nFc  = dim(2);
    ns   = dim(3);

    state.nCv = nCv;
    state.nFc = nFc;
    state.ns = ns;

    [state.species,~,~] = read_species(simulation);

    statedim  = [nCv,1];
    statedims = [nCv,ns];

    fluxdim   = [nFc,2];
    fluxdimp  = [nFc,2];
    fluxdims  = [nFc,2,ns];

    % Dimension labels for unstructured grids
    statedim_labels = {'nCv'};
    statedims_labels = {'nCv','ns'};
    fluxdim_labels = {'nFc',2};
    fluxdimp_labels = {'nFc',2};
    fluxdims_labels = {'nFc',2,'ns'};

else

    dim = scan_b2_int(fid,'nx,ny,ns',3);
    nx  = dim(1);
    ny  = dim(2);
    ns  = dim(3);

    state.nx = nx;
    state.ny = ny;
    state.ns = ns;

    [state.species,~,~] = read_species(simulation);

    statedim  = [nx+2,ny+2];
    statedims = [nx+2,ny+2,ns];
    fluxdim  = [nx+2,ny+2,2];
    fluxdimp = [nx+2,ny+2];
    fluxdims = [nx+2,ny+2,2,ns];
    if version >= '03.001.000'
        fluxdim  = [nx+2,ny+2,2,2];
        fluxdimp = fluxdim;
        fluxdims = [nx+2,ny+2,2,2,ns];
    end

    % Dimension labels for structured grids
    statedim_labels = {'nx+2','ny+2'};
    statedims_labels = {'nx+2','ny+2','ns'};
    if version >= '03.001.000'
        fluxdim_labels = {'nx+2','ny+2',2,2};
        fluxdimp_labels = {'nx+2','ny+2',2,2};
        fluxdims_labels = {'nx+2','ny+2',2,2,'ns'};
    else
        fluxdim_labels = {'nx+2','ny+2',2};
        fluxdimp_labels = {'nx+2','ny+2'};
        fluxdims_labels = {'nx+2','ny+2',2,'ns'};
    end

end

% Charges and masses

state = set_b2_real_field(state, fid, 'zamin', 'zamin', ns, ...
    'Minimum atomic charge', '-', {'ns'});
state = set_b2_real_field(state, fid, 'zamax', 'zamax', ns, ...
    'Maximum atomic charge', '-', {'ns'});
state = set_b2_real_field(state, fid, 'zn', 'zn   ', ns, ...
    'Nuclear charge', '-', {'ns'});
state = set_b2_real_field(state, fid, 'am', 'am   ', ns, ...
    'Atomic mass', 'AMU', {'ns'});

%% READ THE DATA

% State variables

state = set_b2_real_field(state, fid, 'na', 'na', statedims, ...
    'Ion density', 'm^-3', statedims_labels);
state = set_b2_real_field(state, fid, 'ne', 'ne', statedim, ...
    'Electron density', 'm^-3', statedim_labels);
state = set_b2_real_field(state, fid, 'ua', 'ua', statedims, ...
    'Ion parallel velocity', 'm s^-1', statedims_labels);
state = set_b2_real_field(state, fid, 'uadia', 'uadia', fluxdims, ...
    'Total drift velocity', 'm s^-1', fluxdims_labels);
state = set_b2_real_field(state, fid, 'Te', 'te', statedim, ...
    'Electron temperature', 'eV', statedim_labels, 6.242e18);
state = set_b2_real_field(state, fid, 'Ti', 'ti', statedim, ...
    'Ion temperature', 'eV', statedim_labels, 6.242e18);
state = set_b2_real_field(state, fid, 'po', 'po', statedim, ...
    'Electric potential', 'V', statedim_labels);

% Fluxes

state = set_b2_real_field(state, fid, 'fna', 'fna', fluxdims, ...
    'Particle flux', 's^-1', fluxdims_labels);
state = set_b2_real_field(state, fid, 'fhe', 'fhe', fluxdim, ...
    'Electron heat flux', 'W', fluxdim_labels);
state = set_b2_real_field(state, fid, 'fhi', 'fhi', fluxdim, ...
    'Ion heat flux', 'W', fluxdim_labels);
state = set_b2_real_field(state, fid, 'fch', 'fch', fluxdim, ...
    'Electric current', 'A', fluxdim_labels);

frewind(fid);

fclose(fid);

if not(fid_state == -1)
    fprintf('Plasma solution from b2fstate read\n');
elseif (fid_state == -1) && not(fid_stati == -1)
    fprintf('Plasma solution from b2fstati read (b2fstate not found)\n');
end

end
