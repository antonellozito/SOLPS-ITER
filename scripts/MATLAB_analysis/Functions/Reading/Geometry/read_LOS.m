function chords = read_LOS(device,diagnostic,LOS)
%
% read_LOS reads the *.mat file contining data on the diagnostic chords
% from a given device
% Output is a struct "chr" containing the coordinate of the chords
%
% diagnostic: name of the diagnostic
%
% LOS : cell array containing the names of the LOS to be plotted

%% PRELIMINARY OPERATIONS

if strcmp(device,'aug')

    % the options for 'diagnostic' are:
    %   'diode_bolometer'
    %   'foil_bolometer'
    %   'helium_beam_divertor'
    %   'helium_beam_midplane'
    %   'lithium_beam'
    %   'spectroscopy_divertor'
    %   'thomson_scattering_divertor'

    temp = load_aug_database('diagnostics',diagnostic);
    temp = load(temp);
    storedvars = fieldnames(temp);
    FirstVarName = storedvars{1};
    LOS_struct = temp.(FirstVarName);
    
    LOS_names = {LOS_struct.LOS_channel};

% elseif strcmp(device,'cmod')

    % TODO

% elseif strcmp(device,'d3d')

    % TODO

% elseif strcmp(device,'east')

    % TODO

% elseif strcmp(device,'iter')

    % TODO

% elseif strcmp(device,'jet')

    % TODO

% elseif strcmp(device,'mastu')

    % TODO

% elseif strcmp(device,'sparc')

    % TODO

% elseif strcmp(device,'tcv')

    % TODO

else 

    error('Error: Device %s not recognized.');

end

%% READ THE DATA

chords = struct;

for i = 1:length(LOS)
    index=find(ismember(LOS_names,sprintf('%s',LOS{i})));
    chords.r(i,1) = LOS_struct(index).R_start;
    chords.r(i,2) = LOS_struct(index).R_end;
    chords.z(i,1) = LOS_struct(index).z_start;
    chords.z(i,2) = LOS_struct(index).z_end;
    chords.phi(i,1) = LOS_struct(index).phi_start;
    chords.phi(i,2) = LOS_struct(index).phi_end;
    clear index;
end

end