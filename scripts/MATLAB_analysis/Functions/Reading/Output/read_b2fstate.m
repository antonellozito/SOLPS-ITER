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

state.zamin.value = scan_b2_real(fid,'zamin',ns);
state.zamin.description = 'Minimum atomic charge';
state.zamin.unit = '-';
state.zamin.dimensions = {'ns'};

state.zamax.value = scan_b2_real(fid,'zamax',ns);
state.zamax.description = 'Maximum atomic charge';
state.zamax.unit = '-';
state.zamax.dimensions = {'ns'};

state.zn.value = scan_b2_real(fid,'zn   ',ns);
state.zn.description = 'Nuclear charge';
state.zn.unit = '-';
state.zn.dimensions = {'ns'};

state.am.value = scan_b2_real(fid,'am   ',ns);
state.am.description = 'Atomic mass';
state.am.unit = 'AMU';
state.am.dimensions = {'ns'};

%% READ THE DATA

% State variables

state.na.value = scan_b2_real(fid,'na'    ,statedims);
state.na.description = 'Ion density';
state.na.unit = 'm^-3';
state.na.dimensions = statedims_labels;

state.ne.value = scan_b2_real(fid,'ne'    ,statedim);
state.ne.description = 'Electron density';
state.ne.unit = 'm^-3';
state.ne.dimensions = statedim_labels;

state.ua.value = scan_b2_real(fid,'ua'    ,statedims);
state.ua.description = 'Ion parallel velocity';
state.ua.unit = 'm s^-1';
state.ua.dimensions = statedims_labels;

state.uadia.value = scan_b2_real(fid,'uadia' ,fluxdims);
state.uadia.description = 'Total drift velocity';
state.uadia.unit = 'm s^-1';
state.uadia.dimensions = fluxdims_labels;

Te = scan_b2_real(fid,'te'    ,statedim);
state.Te.value = Te.*6.242e18;
state.Te.description = 'Electron temperature';
state.Te.unit = 'eV';
state.Te.dimensions = statedim_labels;

Ti = scan_b2_real(fid,'ti'    ,statedim);
state.Ti.value = Ti.*6.242e18;
state.Ti.description = 'Ion temperature';
state.Ti.unit = 'eV';
state.Ti.dimensions = statedim_labels;

state.po.value = scan_b2_real(fid,'po'    ,statedim);
state.po.description = 'Electric potential';
state.po.unit = 'V';
state.po.dimensions = statedim_labels;

% Fluxes

state.fna.value = scan_b2_real(fid,'fna'   ,fluxdims);
state.fna.description = 'Particle flux';
state.fna.unit = 's^-1';
state.fna.dimensions = fluxdims_labels;

state.fhe.value = scan_b2_real(fid,'fhe'   ,fluxdim);
state.fhe.description = 'Electron heat flux';
state.fhe.unit = 'W';
state.fhe.dimensions = fluxdim_labels;

state.fhi.value = scan_b2_real(fid,'fhi'   ,fluxdim);
state.fhi.description = 'Ion heat flux';
state.fhi.unit = 'W';
state.fhi.dimensions = fluxdim_labels;

state.fch.value = scan_b2_real(fid,'fch'   ,fluxdim);
state.fch.description = 'Electric current';
state.fch.unit = 'A';
state.fch.dimensions = fluxdim_labels;

frewind(fid);

fclose(fid);

if not(fid_state == -1)
    fprintf('Structure STATE from b2fstate read.\n');
elseif (fid_state == -1) && not(fid_stati == -1)
    fprintf('Structure STATE from b2fstati read (b2fstate not found).\n');
end

end
