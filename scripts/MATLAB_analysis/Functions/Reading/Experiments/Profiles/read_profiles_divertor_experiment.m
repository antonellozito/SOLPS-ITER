function [profiles_chords_experiment,data_avail] = read_profiles_divertor_experiment(simulation)

% read_profiles_divertor_experiment reads the experimental plasma profiles,
% namely electron density and electron/ion temperature, on divertor chords as measured
% by different diagnostics

% TODO: for AUG, add possibility of different experiments instead of the default augd

%% READ EXPERIMENTAL DATA FROM RUN DIRECTORY

try
    exp_data = read_exp_data(simulation);
    data_avail = true;
catch
    data_avail = false;
end

profiles_chords_experiment = struct();

if data_avail

    switch exp_data.DEVICE

        case 'AUG'

            %% CHECK THAT THE AUG LIBRARY LOCALLY EXISTS

            if ~isfolder(sprintf('%s/scripts.local/MATLAB_analysis_AUG',simulation.SOLPSTOP))
                error(sprintf('Error: MATLAB library for reading AUG experimental data does not exist locally. Get it running the command ''clone_matlab_exp_libraries AUG'''));
            end
            if ~isdeployed
                addpath(genpath(sprintf('%s/scripts.local/MATLAB_analysis/AUG',simulation.SOLPSTOP)));
            end

            %% LOAD EXPERIMENTAL DATA FOR AUG

            % Fields '*_SHOT' mean the discharge number
            % Fields '*_EXPERIMENT(S)' mean the user experiment (default: 'augd')
            % Fields '*_SOURCE(S)' mean the shotfile name
            % Fields '*_SIGNAL(S)' mean the signal/signalgroup name

            % Electron density data

            for i = 1:length(exp_data.ELECTRON_DENSITY_DATA_CHORDS_SOURCES)

                if strcmp(exp_data.ELECTRON_DENSITY_DATA_CHORDS_SOURCES{i},'DTN')

                    % Divertor Thomson scattering

                    [~,TIMEBASES_ne_DATA{i},~,SIGNALS_ne_DATA{i}] = load_aug_shotfile(...
                        exp_data.ELECTRON_DENSITY_DATA_CHORDS_SOURCES{i}, ...
                        exp_data.ELECTRON_DENSITY_DATA_CHORDS_SHOT,...
                        'signals',{'Ne_ld','R_ld','Z_ld'});

                end

            end

            % Electron temperature data

            for i = 1:length(exp_data.ELECTRON_TEMPERATURE_DATA_CHORDS_SOURCES)

                if strcmp(exp_data.ELECTRON_TEMPERATURE_DATA_CHORDS_SOURCES{i},'DTN')

                    % Divertor Thomson scattering

                    [~,TIMEBASES_Te_DATA{i},~,SIGNALS_Te_DATA{i}] = load_aug_shotfile(...
                        exp_data.ELECTRON_TEMPERATURE_DATA_CHORDS_SOURCES{i}, ...
                        exp_data.ELECTRON_TEMPERATURE_DATA_CHORDS_SHOT,...
                        'signals',{'Te_ld','R_ld','Z_ld'});

                end

            end

            % Ion temperature data

            for i = 1:length(exp_data.ION_TEMPERATURE_DATA_CHORDS_SOURCES)

            end

            %% EXTRACT EXPERIMENTAL DATA FOR AUG

            % Electron density data

            for i = 1:length(exp_data.ELECTRON_DENSITY_DATA_CHORDS_SOURCES)

                if strcmp(exp_data.ELECTRON_DENSITY_DATA_CHORDS_SOURCES{i},'DTN') && strcmp(exp_data.ELECTRON_DENSITY_DATA_CHORDS_SIGNALS{i},'Ne_ld')

                    % Divertor Thomson scattering

                    time_data_ne{i} = TIMEBASES_ne_DATA{i}.Time_ld.value;
                    values_data_ne{i} = transpose(SIGNALS_ne_DATA{i}.Ne_ld.value);

                end

                profiles_chords_experiment.ne_data{i}.name = exp_data.ELECTRON_DENSITY_DATA_CHORDS_NAMES_DISPLAY{i};
                [profiles_chords_experiment.ne_data{i}.times,profiles_chords_experiment.ne_data{i}.values] = ...
                    extract_values(time_data_ne{i}, values_data_ne{i},...
                    exp_data.ELECTRON_DENSITY_DATA_CHORDS_TIME_START,exp_data.ELECTRON_DENSITY_DATA_CHORDS_TIME_END,...
                    exp_data.ELECTRON_DENSITY_DATA_CHORDS_REDUCED_SET,exp_data.ELECTRON_DENSITY_DATA_CHORDS_REDUCED_SET_TIME_DELTA);

            end

            % Electron temperature data

            for i = 1:length(exp_data.ELECTRON_TEMPERATURE_DATA_CHORDS_SOURCES)

                if strcmp(exp_data.ELECTRON_TEMPERATURE_DATA_CHORDS_SOURCES{i},'DTN') && strcmp(exp_data.ELECTRON_TEMPERATURE_DATA_CHORDS_SIGNALS{i},'Te_ld')

                    % Divertor Thomson scattering

                    time_data_Te{i} = TIMEBASES_Te_DATA{i}.Time_ld.value;
                    values_data_Te{i} = transpose(SIGNALS_Te_DATA{i}.Te_ld.value);

                end

                profiles_chords_experiment.Te_data{i}.name = exp_data.ELECTRON_TEMPERATURE_DATA_CHORDS_NAMES_DISPLAY{i};
                [profiles_chords_experiment.Te_data{i}.times,profiles_chords_experiment.Te_data{i}.values] = ...
                    extract_values(time_data_Te{i}, values_data_Te{i},...
                    exp_data.ELECTRON_TEMPERATURE_DATA_CHORDS_TIME_START,exp_data.ELECTRON_TEMPERATURE_DATA_CHORDS_TIME_END,...
                    exp_data.ELECTRON_TEMPERATURE_DATA_CHORDS_REDUCED_SET,exp_data.ELECTRON_TEMPERATURE_DATA_CHORDS_REDUCED_SET_TIME_DELTA);

            end

            % Ion temperature data

            for i = 1:length(exp_data.ION_TEMPERATURE_DATA_CHORDS_SOURCES)

            end

            %% CALCULATE COORDINATES FOR AUG

            % Electron density profile

            for i = 1:length(exp_data.ELECTRON_DENSITY_DATA_CHORDS_SOURCES)

                if strcmp(exp_data.ELECTRON_DENSITY_DATA_CHORDS_SOURCES{i},'DTN') && strcmp(exp_data.ELECTRON_DENSITY_DATA_CHORDS_SIGNALS{i},'Ne_ld')

                    % Divertor Thomson scattering

                    profiles_chords_experiment.ne_data{i}.R = SIGNALS_ne_DATA{i}.R_ld.value;
                    profiles_chords_experiment.ne_data{i}.z = SIGNALS_ne_DATA{i}.Z_ld.value;

                end

            end

            % Electron temperature data

            for i = 1:length(exp_data.ELECTRON_TEMPERATURE_DATA_CHORDS_SOURCES)

                if strcmp(exp_data.ELECTRON_TEMPERATURE_DATA_CHORDS_SOURCES{i},'DTN') && strcmp(exp_data.ELECTRON_TEMPERATURE_DATA_CHORDS_SIGNALS{i},'Te_ld')

                    % Divertor Thomson scattering

                    profiles_chords_experiment.Te_data{i}.R = SIGNALS_Te_DATA{i}.R_ld.value;
                    profiles_chords_experiment.Te_data{i}.z = SIGNALS_Te_DATA{i}.Z_ld.value;

                end

            end

            % Ion temperature data

            for i = 1:length(exp_data.ION_TEMPERATURE_DATA_CHORDS_SOURCES)

            end

        case 'CMOD'

            %% CHECK THAT THE CMOD LIBRARY LOCALLY EXISTS

            error(sprintf('Error: Methods for reading CMOD experimental data not yet implemented'));

            %% LOAD EXPERIMENTAL DATA FOR CMOD

            % TODO

            %% EXTRACT EXPERIMENTAL DATA FOR CMOD

            % TODO

            %% CALCULATE COORDINATES FOR CMOD

            % TODO

        case 'D3D'

            %% CHECK THAT THE D3D LIBRARY LOCALLY EXISTS

            error(sprintf('Error: Methods for reading D3D experimental data not yet implemented'));

            %% LOAD EXPERIMENTAL DATA FOR D3D

            % TODO

            %% EXTRACT EXPERIMENTAL DATA FOR D3D

            % TODO

            %% CALCULATE COORDINATES FOR D3D

            % TODO

        case 'EAST'

            %% CHECK THAT THE EAST LIBRARY LOCALLY EXISTS

            error(sprintf('Error: Methods for reading EAST experimental data not yet implemented'));

            %% LOAD EXPERIMENTAL DATA FOR EAST

            % TODO

            %% EXTRACT EXPERIMENTAL DATA FOR EAST

            % TODO

            %% CALCULATE COORDINATES FOR EAST

            % TODO

        case 'JET'

            %% CHECK THAT THE JET LIBRARY LOCALLY EXISTS

            error(sprintf('Error: Methods for reading JET experimental data not yet implemented'));

            %% LOAD EXPERIMENTAL DATA FOR JET

            % TODO

            %% EXTRACT EXPERIMENTAL DATA FOR JET

            % TODO

            %% CALCULATE COORDINATES FOR JET

            % TODO

        case 'MASTU'

            %% CHECK THAT THE MASTU LIBRARY LOCALLY EXISTS

            error(sprintf('Error: Methods for reading MASTU experimental data not yet implemented'));

            %% LOAD EXPERIMENTAL DATA FOR MASTU

            % TODO

            %% EXTRACT EXPERIMENTAL DATA FOR MASTU

            % TODO

            %% CALCULATE COORDINATES FOR MASTU

            % TODO

        case 'TCV'

            %% CHECK THAT THE TCV LIBRARY LOCALLY EXISTS

            error(sprintf('Error: Methods for reading TCV experimental data not yet implemented'));

            %% LOAD EXPERIMENTAL DATA FOR TCV

            % TODO

            %% EXTRACT EXPERIMENTAL DATA FOR TCV

            % TODO

            %% CALCULATE COORDINATES FOR TCV

            % TODO

        otherwise

            error(sprintf('Error: Device %s not existing'),exp_data.DEVICE);

    end

end

end

%% AUXILIARY FUNCTION TO EXTRACT VALUES

function [time_output,values_output] = extract_values(time,values,time_start,time_end,reduced_set,reduced_set_time_delta)

% Inputs:
%   time = array with the original time steps of the experimental data
%   values = matrix with the original values of the experimental data (must be function of 1) space dimension and 2) time dimension)
%   time_start = start of the time window from which to extract the experimental data
%   time_end = end of the time window from which to extract the experimental data
%   reduced_set = true (for extracting averaged data only from a subset of times, between time_start and time_end)
%                 false (for extracting original data from all the times between time_start and time_end)
%   reduced_set_time_delta = length of the individual time windows, between time_start and time_end,
%                            within which to average the original data, if reduced_set = 'true'

if reduced_set
    time_interval(1) = time_start;
    k = 1;
    while time_interval(k) < time_end-1e-10
        time_interval(k+1) = time_interval(k)+reduced_set_time_delta;
        [~,time_start_index] = min(abs(time_interval(k)-time));
        [~,time_end_index] = min(abs(time_interval(k+1)-time));
        for j = 1:(time_end_index-time_start_index+1)
            values_delta_interval{k}(j,:) = values(:,j+time_start_index-1);
        end
        values_interval(k,:) = median(values_delta_interval{k}(:,:),1,'omitnan');
        k = k+1;
    end
    time_output = time_interval;
    values_output = values_interval;
else
    [~,time_start_index] = min(abs(time_start-time));
    [~,time_end_index] = min(abs(time_end-time));
    for j = 1:(time_end_index-time_start_index+1)
        time_interval(j) = time(j+time_start_index-1);
        values_interval(j,:) = values(:,j+time_start_index-1);
    end
    time_output = time_interval;
    values_output = values_interval;
end

end
