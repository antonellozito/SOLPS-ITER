function output = read_output(varargin)

% read_output reads the output .dat files containing
% all the terms of the fluid equations as solved by B2.5
%
% 1st input: main simulation structure
%
% Following inputs: strings which specify the equations whose
%                   corresponding fields should be read:
%                   - 'particles'
%                   - 'momentum'
%                   - 'electron_energy'
%                   - 'ion_energy'
%                   - 'current'

% TODO: add the options for reading the fields from momentum equation,
% energy equations and current equation

%% PRELIMINARY OPERATIONS

% Read dimensions from b2fstate

simulation = varargin{1};

index = find(contains({simulation.run.name},'b2fstate'));
if isempty(index)
   error('Error: b2fstate not found');
end
fid = simulation.run(index).fid;
if (fid == -1)
   error('Error: b2fstate not found');
end

dim = scan_b2_int(fid,'nx,ny,ns',3);
nx  = dim(1);
ny  = dim(2);
ns  = dim(3);

%% FILE NAMES

filenames_state_single_species = {'ne'};
filenames_state_single_species_multiple_options = {'te','ti','po'};
filenames_state_multi_species = {'b2npmo_ua'};
filenames_state_multi_species_multiple_options = {'na'};

filenames_particles_single_species = {'b2tfnb_vbecrbx001','b2tfnb_vbecrby001'};
filenames_particles_single_species_multiple_options = {};
filenames_particles_multi_species = {'b2stel_sna_ion','b2stel_sna_rec','b2stcx_sna_','b2stbr_sna_eir','b2stbc_phys_sna',...
    'b2tfnb_bxuanax','b2tfnb_vaecrbnax','b2tfnb_vaecrbnay','b2tfnb_dpccornax','b2tfnb_cvlbnay','b2tfnb_dPat_mdf_gradnax','b2tfnb_dPat_mdf_gradnay',...
    'b2tfnb_dgradpbx','b2tfnb_dgradpby','b2tfnb_fnbPSchx','b2tfnb_fnbPSchy','b2trno_cdnax','b2trno_cdnay','b2trno_cdpax','b2trno_cdpay',...
    'b2tqna_dna0','b2tqna_dpa0','b2tfnb_wbdiax','b2tfnb_wbdiay','b2tfnb_vbdiax','b2tfnb_vbdiay','b2tfnb_vadianax','b2tfnb_vadianay',...
    'b2tfnb_kbnrgy','b2tqna_vla0y','b2tfnb_fnbx','b2tfnb_fnby'};
filenames_particles_multi_species_multiple_options = {'sna','dnadt','fnax','fnay','resco'};

filenames_momentum_single_species = {};
filenames_momentum_single_species_multiple_options = {};
filenames_momentum_multi_species = {};
filenames_momentum_multi_species_multiple_options = {};

filenames_electron_energy_single_species = {};
filenames_electron_energy_single_species_multiple_options = {};
filenames_electron_energy_multi_species = {};
filenames_electron_energy_multi_species_multiple_options = {};

filenames_ion_energy_single_species = {};
filenames_ion_energy_single_species_multiple_options = {};
filenames_ion_energy_multi_species = {};
filenames_ion_energy_multi_species_multiple_options = {};

filenames_current_single_species = {'b2tfch__fchanmly','b2tfch__fchinerty','b2tfch__fchvispary','b2tfch__fchvispery','b2tfch__fchvisqy'};
filenames_current_single_species_multiple_options = {};
filenames_current_multi_species = {};
filenames_current_multi_species_multiple_options = {};

%% READ STATE VARIABLES

% Single species variables with fixed name

filenames_single_species = filenames_state_single_species;

for i = 1:length(filenames_single_species)
    output.state_variables.(filenames_single_species{i}) = zeros(ny+2,nx+2);
    filename{i} = append(filenames_single_species{i},'.dat');
    index = find(contains({simulation.output.name},filename{i}));
    fid = simulation.output(index).fid;
    line = fgetl(fid);
    for j = 1:ny+2
        line = fgetl(fid);
        temp = sscanf(line,'%e',nx+3);
        output.state_variables.(filenames_single_species{i})(j,:) = temp(2:end); 
    end
    output.state_variables.(filenames_single_species{i}) = output.state_variables.(filenames_single_species{i})';
    output.state_variables.(filenames_single_species{i}) = flip(output.state_variables.(filenames_single_species{i}),2);
    frewind(fid);
end

% Single species variables with unfixed name

filenames_single_species = filenames_state_single_species_multiple_options;

for i = 1:length(filenames_single_species)
    name_file{i} = try_file(filenames_single_species{i},simulation);
    if ~strcmp(name_file{i},'none')
    output.state_variables.(name_file{i}) = zeros(ny+2,nx+2);
    filename{i} = append(name_file{i},'.dat');
    index = find(contains({simulation.output.name},filename{i}));
    fid = simulation.output(index).fid;
    line = fgetl(fid);
    for j = 1:ny+2
        line = fgetl(fid);
        temp = sscanf(line,'%e',nx+3);
        output.state_variables.(name_file{i})(j,:) = temp(2:end); 
    end
    output.state_variables.(name_file{i}) = output.state_variables.(name_file{i})';
    output.state_variables.(name_file{i}) = flip(output.state_variables.(name_file{i}),2);
    frewind(fid);
    end
end

% Multiple species variables with fixed name

filenames_multi_species = filenames_state_multi_species;

for i = 1:length(filenames_multi_species)
    for k = 1:ns
        name_file{i} = sprintf('%s%03d',filenames_multi_species{i},k-1);
        if ~strcmp(name_file{i},'none')
        output.state_variables.(name_file{i}) = zeros(ny+2,nx+2);
        filename{i} = append(name_file{i},'.dat');
        index = find(contains({simulation.output.name},filename{i}));
        fid = simulation.output(index).fid;
        line = fgetl(fid);
        for j = 1:ny+2
            line = fgetl(fid);
            temp = sscanf(line,'%e',nx+3);
            output.state_variables.(name_file{i})(j,:) = temp(2:end);
        end
        output.state_variables.(name_file{i}) = output.state_variables.(name_file{i})';
        output.state_variables.(name_file{i}) = flip(output.state_variables.(name_file{i}),2);
        frewind(fid);
        end
    end
end

% Multiple species variables with unfixed name

filenames_multi_species = filenames_state_multi_species_multiple_options;

for i = 1:length(filenames_multi_species)
    for k = 1:ns
        temp = sprintf('%s%03d',filenames_multi_species{i},k-1);
        name_file{i} = try_file(temp,simulation);
        if ~strcmp(name_file{i},'none')
        output.state_variables.(name_file{i}) = zeros(ny+2,nx+2);
        filename{i} = append(name_file{i},'.dat');
        index = find(contains({simulation.output.name},filename{i}));
        fid = simulation.output(index).fid;
        line = fgetl(fid);
        for j = 1:ny+2
            line = fgetl(fid);
            temp = sscanf(line,'%e',nx+3);
            output.state_variables.(name_file{i})(j,:) = temp(2:end);
        end
        output.state_variables.(name_file{i}) = output.state_variables.(name_file{i})';
        output.state_variables.(name_file{i}) = flip(output.state_variables.(name_file{i}),2);
        frewind(fid);
        end
    end
end

%% READ DATA FOR ANY EQUATIONS

for k = 2:length(varargin)

    switch varargin{k}
        case 'particles'
            filenames_single_species = filenames_particles_single_species;
            filenames_multi_species = filenames_particles_multi_species;
            filenames_single_species_multiple_options = filenames_particles_single_species_multiple_options;
            filenames_multi_species_multiple_options = filenames_particles_multi_species_multiple_options;
        case 'momentum'
            filenames_single_species = filenames_momentum_single_species;
            filenames_multi_species = filenames_momentum_multi_species;
            filenames_single_species_multiple_options = filenames_momentum_single_species_multiple_options;
            filenames_multi_species_multiple_options = filenames_momentum_multi_species_multiple_options;
        case 'electron_energy'
            filenames_single_species = filenames_electron_energy_single_species;
            filenames_multi_species = filenames_electron_energy_multi_species;
            filenames_single_species_multiple_options = filenames_electron_energy_single_species_multiple_options;
            filenames_multi_species_multiple_options = filenames_electron_energy_multi_species_multiple_options;
        case 'ion_energy'
            filenames_single_species = filenames_ion_energy_single_species;
            filenames_multi_species = filenames_ion_energy_multi_species;  
            filenames_single_species_multiple_options = filenames_ion_energy_single_species_multiple_options;
            filenames_multi_species_multiple_options = filenames_ion_energy_multi_species_multiple_options;  
        case 'current'
            filenames_single_species = filenames_current_single_species;
            filenames_multi_species = filenames_current_multi_species;
            filenames_single_species_multiple_options = filenames_current_single_species_multiple_options;
            filenames_multi_species_multiple_options = filenames_current_multi_species_multiple_options;
    end

% Single species variables with fixed name

for i = 1:length(filenames_single_species)
    output.(sprintf('%s_equation',varargin{k})).(filenames_single_species{i}) = zeros(ny+2,nx+2);
    filename{i} = append(filenames_single_species{i},'.dat');
    index = find(contains({simulation.output.name},filename{i}));
    fid = simulation.output(index).fid;
    line = fgetl(fid);
    for j = 1:ny+2
        line = fgetl(fid);
        temp = sscanf(line,'%e',nx+3);
        output.(sprintf('%s_equation',varargin{k})).(filenames_single_species{i})(j,:) = temp(2:end);
    end
    output.(sprintf('%s_equation',varargin{k})).(filenames_single_species{i}) = ...
        output.(sprintf('%s_equation',varargin{k})).(filenames_single_species{i})';
    output.(sprintf('%s_equation',varargin{k})).(filenames_single_species{i}) = ...
        flip(output.(sprintf('%s_equation',varargin{k})).(filenames_single_species{i}),2);
    frewind(fid);
end

% Single species variables with unfixed name

for i = 1:length(filenames_single_species_multiple_options)
    name_file{i} = try_file(filenames_single_species_multiple_options{i},simulation);
    if ~strcmp(name_file{i},'none')
    output.state_variables.(name_file{i}) = zeros(ny+2,nx+2);
    filename{i} = append(name_file{i},'.dat');
    index = find(contains({simulation.output.name},filename{i}));
    fid = simulation.output(index).fid;
    line = fgetl(fid);
    for j = 1:ny+2
        line = fgetl(fid);
        temp = sscanf(line,'%e',nx+3);
        output.(sprintf('%s_equation',varargin{k})).(name_file{i})(j,:) = temp(2:end);
    end
    output.(sprintf('%s_equation',varargin{k})).(name_file{i}) = ...
        output.(sprintf('%s_equation',varargin{k})).(name_file{i})';
    output.(sprintf('%s_equation',varargin{k})).(name_file{i}) = ...
        flip(output.(sprintf('%s_equation',varargin{k})).(name_file{i}),2);
    frewind(fid);
    end
end

% Multiple species variables with fixed name

for i = 1:length(filenames_multi_species)
    for w = 1:ns
        name_file{i} = sprintf('%s%03d',filenames_multi_species{i},w-1);
        if ~strcmp(name_file{i},'none')
        output.(sprintf('%s_equation',varargin{k})).(name_file{i}) = zeros(ny+2,nx+2);
        filename{i} = append(name_file{i},'.dat');
        index = find(contains({simulation.output.name},filename{i}));
        if ~isempty(index)
            fid = simulation.output(index).fid;
            line = fgetl(fid);
            for j = 1:ny+2
                line = fgetl(fid);
                temp = sscanf(line,'%e',nx+3);
                output.(sprintf('%s_equation',varargin{k})).(name_file{i})(j,:) = temp(2:end);
            end
            output.(sprintf('%s_equation',varargin{k})).(name_file{i}) = ...
                output.(sprintf('%s_equation',varargin{k})).(name_file{i})';
            output.(sprintf('%s_equation',varargin{k})).(name_file{i}) = ...
                flip(output.(sprintf('%s_equation',varargin{k})).(name_file{i}),2);
        else
            output.(sprintf('%s_equation',varargin{k})).(name_file{i}) = ...
               output.(sprintf('%s_equation',varargin{k})).(name_file{i})';
        end
        frewind(fid);
        end
    end
end

% Multiple species variables with unfixed name

for i = 1:length(filenames_multi_species_multiple_options)
    for w = 1:ns
        temp = sprintf('%s%03d',filenames_multi_species_multiple_options{i},w-1);
        name_file{i} = try_file(temp,simulation);
        if ~strcmp(name_file{i},'none')
        output.(sprintf('%s_equation',varargin{k})).(name_file{i}) = zeros(ny+2,nx+2);
        filename{i} = append(name_file{i},'.dat');
        index = find(contains({simulation.output.name},filename{i}));
        fid = simulation.output(index).fid;
        line = fgetl(fid);
        for j = 1:ny+2
            line = fgetl(fid);
            temp = sscanf(line,'%e',nx+3);
            output.(sprintf('%s_equation',varargin{k})).(name_file{i})(j,:) = temp(2:end);
        end
        output.(sprintf('%s_equation',varargin{k})).(name_file{i}) = ...
            output.(sprintf('%s_equation',varargin{k})).(name_file{i})';
        output.(sprintf('%s_equation',varargin{k})).(name_file{i}) = ...
            flip(output.(sprintf('%s_equation',varargin{k})).(name_file{i}),2);
        frewind(fid);
        end
    end
end

end

end

function name_file = try_file(field,simulation)

if contains(field,'na') || contains(field,'sna') || contains(field,'dnadt') || contains(field,'fnax') || contains(field,'fnay') || contains(field,'resco')
    possible_routines = {'b2npco','b2npc7','b2npc9','b2npc11'};
elseif contains(field,'te') || contains(field,'ti')
    possible_routines = {'b2npht','b2nph9'};
elseif contains(field,'po')
    possible_routines = {'b2nppo','b2npp7'};
end

name_file = 'none';

for i = 1:length(possible_routines)
    name = sprintf('%s_%s.',possible_routines{i},field);
    for j = 1:length({simulation.output.name})
        if contains(simulation.output(j).name,name)
            name_file = simulation.output(j).name(1:end-4);
        end
    end
end

end
