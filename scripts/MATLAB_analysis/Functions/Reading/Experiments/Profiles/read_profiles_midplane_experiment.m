function [profiles_midplane_experiment,data_avail] = read_profiles_midplane_experiment(simulation,PLOT_EXP_PROFILES,PLOT_EXP_DATA)

% read_midplane_profiles_experiment reads the experimental midplane plasma profiles,
% namely electron density, electron temperature, ion temperature
% It reads profiles with uncertainties (from statistical data analysis) and
% data clouds from individual diagnostics

% TODO: for AUG, add possibility of different experiments instead of the default augd

%% READ EXPERIMENTAL DATA FROM RUN DIRECTORY

try
    exp_data = read_exp_data(simulation);
    data_avail = true;
catch
    data_avail = false;
end

profiles_midplane_experiment = struct();

if data_avail

    switch exp_data.DEVICE

        case 'AUG'

            %% CHECK THAT THE AUG LIBRARY LOCALLY EXISTS

            if ~isfolder(sprintf('%s/scripts.local/MATLAB_analysis_AUG',simulation.SOLPSTOP))
                error(sprintf('Error: MATLAB library for reading AUG experimental data does not exist locally. Get it running the command ''clone_matlab_exp_libraries AUG'''));
            end
            addpath(genpath(sprintf('%s/scripts.local/MATLAB_analysis_AUG',simulation.SOLPSTOP)));

            %% LOAD EXPERIMENTAL DATA FOR AUG

            % Fields '*_SHOT' mean the discharge number
            % Fields '*_EXPERIMENT(S)' mean the user experiment (default: 'augd')
            % Fields '*_SOURCE(S)' mean the shotfile name
            % Fields '*_SIGNAL(S)' mean the signal/signalgroup name

            % Load shotfiles containing profiles from statistical data analysis

            SHOTFILES_BASEPATH_LOCAL = '';

            for i = 1:numel(AUG_config().SHOTFILES_BASEPATH_LOCAL)
                if isfolder(AUG_config().SHOTFILES_BASEPATH_LOCAL{i})
                    SHOTFILES_BASEPATH_LOCAL = AUG_config().SHOTFILES_BASEPATH_LOCAL{i};
                    break
                end
            end

            if PLOT_EXP_PROFILES

                % Electron density profile

                [~,TIMEBASES_ne_PROFILES,AREABASES_ne_PROFILES,SIGNALS_ne_PROFILES] = load_aug_shotfile(...
                    exp_data.ELECTRON_DENSITY_PROFILE_MIDPLANE_SOURCE, ...
                    exp_data.ELECTRON_DENSITY_PROFILE_MIDPLANE_SHOT,...
                    'signals',{'ne','ne_unc','Te','Te_unc','Ntscprof','Ntseprof','tsdatcne','tsdatene','Ntscprof','Ntseprof','tsdatcte','tsdatete'});

                % Electron temperature profile

                if strcmp(exp_data.ELECTRON_DENSITY_PROFILE_MIDPLANE_SOURCE,exp_data.ELECTRON_TEMPERATURE_PROFILE_MIDPLANE_SOURCE) && ...
                        strcmp(exp_data.ELECTRON_DENSITY_PROFILE_MIDPLANE_EXPERIMENT,exp_data.ELECTRON_TEMPERATURE_PROFILE_MIDPLANE_EXPERIMENT) && ...
                        exp_data.ELECTRON_DENSITY_PROFILE_MIDPLANE_SHOT==exp_data.ELECTRON_TEMPERATURE_PROFILE_MIDPLANE_SHOT

                    TIMEBASES_Te_PROFILES = TIMEBASES_ne_PROFILES;
                    AREABASES_Te_PROFILES = AREABASES_ne_PROFILES;
                    SIGNALS_Te_PROFILES = SIGNALS_ne_PROFILES;

                else

                    [~,TIMEBASES_Te_PROFILES,AREABASES_Te_PROFILES,SIGNALS_Te_PROFILES] = load_aug_shotfile(...
                        exp_data.ELECTRON_TEMPERATURE_PROFILE_MIDPLANE_SOURCE, ...
                        exp_data.ELECTRON_TEMPERATURE_PROFILE_MIDPLANE_SHOT,...
                        'signals',{'ne','ne_unc','Te','Te_unc','Ntscprof','Ntseprof','tsdatcne','tsdatene','Ntscprof','Ntseprof','tsdatcte','tsdatete'});

                end

            end

            % Load shotfiles containing diagnostic data

            if PLOT_EXP_DATA

                % Electron density data

                for i = 1:length(exp_data.ELECTRON_DENSITY_DATA_MIDPLANE_SOURCES)

                    if strcmp(exp_data.ELECTRON_DENSITY_DATA_MIDPLANE_SOURCES{i},'LIN')

                        % Lithium beam emission spectroscopy

                        [~,TIMEBASES_ne_DATA{i},AREABASES_ne_DATA{i},SIGNALS_ne_DATA{i}] = load_aug_shotfile(...
                            exp_data.ELECTRON_DENSITY_DATA_MIDPLANE_SOURCES{i}, ...
                            exp_data.ELECTRON_DENSITY_DATA_MIDPLANE_SHOT,...
                            'signals',{'ne'});

                    elseif strcmp(exp_data.ELECTRON_DENSITY_DATA_MIDPLANE_SOURCES{i},'VTA')

                        % Vertical Thomson scattering (raw data)

                        [~,TIMEBASES_ne_DATA{i},AREABASES_ne_DATA{i},SIGNALS_ne_DATA{i}] = load_aug_shotfile(...
                            exp_data.ELECTRON_DENSITY_DATA_MIDPLANE_SOURCES{i}, ...
                            exp_data.ELECTRON_DENSITY_DATA_MIDPLANE_SHOT,...
                            'signals',{'Ne_c','Ne_e','Z_core','Z_edge','R_core','R_edge'});

                        % Vertical Thomson scattering (IDA)

                    elseif strcmp(exp_data.ELECTRON_DENSITY_DATA_MIDPLANE_SOURCES{i},'IDA')

                        if strcmp(exp_data.ELECTRON_DENSITY_PROFILE_MIDPLANE_SOURCE,exp_data.ELECTRON_DENSITY_DATA_MIDPLANE_SOURCES{i}) && ...
                                strcmp(exp_data.ELECTRON_DENSITY_PROFILE_MIDPLANE_EXPERIMENT,exp_data.ELECTRON_DENSITY_DATA_MIDPLANE_EXPERIMENTS{i}) && ...
                                exp_data.ELECTRON_DENSITY_PROFILE_MIDPLANE_SHOT==exp_data.ELECTRON_DENSITY_DATA_MIDPLANE_SHOT && ...
                                PLOT_EXP_PROFILES

                            TIMEBASES_ne_DATA{i} = TIMEBASES_ne_PROFILES;
                            AREABASES_ne_DATA{i} = AREABASES_ne_PROFILES;
                            SIGNALS_ne_DATA{i} = SIGNALS_ne_PROFILES;

                        else

                            [~,TIMEBASES_ne_DATA{i},AREABASES_ne_DATA{i},SIGNALS_ne_DATA{i}] = load_aug_shotfile(...
                                exp_data.ELECTRON_DENSITY_DATA_MIDPLANE_SOURCES{i}, ...
                                exp_data.ELECTRON_DENSITY_DATA_MIDPLANE_SHOT,...
                                'signals',{'ne','ne_unc','Te','Te_unc','Ntscprof','Ntseprof','tsdatcne','tsdatene','Ntscprof','Ntseprof','tsdatcte','tsdatete'});

                        end

                    elseif strcmp(exp_data.ELECTRON_DENSITY_DATA_MIDPLANE_SOURCES{i},'ELM')

                        % ELM-synchronized data

                        SIGNALS_ne_DATA{i} = sprintf('%s/custom/ELM/%d.nc',...
                            SHOTFILES_BASEPATH_LOCAL,exp_data.ELECTRON_DENSITY_DATA_MIDPLANE_SHOT);

                    end

                end

                % Electron temperature data

                for i = 1:length(exp_data.ELECTRON_TEMPERATURE_DATA_MIDPLANE_SOURCES)

                    if strcmp(exp_data.ELECTRON_TEMPERATURE_DATA_MIDPLANE_SOURCES{i},'VTA')

                        % Vertical Thomson scattering (raw data)

                        [~,TIMEBASES_Te_DATA{i},AREABASES_Te_DATA{i},SIGNALS_Te_DATA{i}] = load_aug_shotfile(...
                            exp_data.ELECTRON_TEMPERATURE_DATA_MIDPLANE_SOURCES{i}, ...
                            exp_data.ELECTRON_TEMPERATURE_DATA_MIDPLANE_SHOT,...
                            'signals',{'Te_c','Te_e','Z_core','Z_edge','R_core','R_edge'});

                    elseif strcmp(exp_data.ELECTRON_TEMPERATURE_DATA_MIDPLANE_SOURCES{i},'IDA')

                        % Vertical Thomson scattering (IDA)

                        if strcmp(exp_data.ELECTRON_TEMPERATURE_PROFILE_MIDPLANE_SOURCE,exp_data.ELECTRON_TEMPERATURE_DATA_MIDPLANE_SOURCES{i}) && ...
                                strcmp(exp_data.ELECTRON_TEMPERATURE_PROFILE_MIDPLANE_EXPERIMENT,exp_data.ELECTRON_TEMPERATURE_DATA_MIDPLANE_EXPERIMENTS{i}) && ...
                                exp_data.ELECTRON_TEMPERATURE_PROFILE_MIDPLANE_SHOT==exp_data.ELECTRON_TEMPERATURE_DATA_MIDPLANE_SHOT && ...
                                PLOT_EXP_PROFILES

                            TIMEBASES_Te_DATA{i} = TIMEBASES_Te_PROFILES;
                            AREABASES_Te_DATA{i} = AREABASES_Te_PROFILES;
                            SIGNALS_Te_DATA{i} = SIGNALS_Te_PROFILES;

                        else

                            [~,TIMEBASES_Te_DATA{i},AREABASES_Te_DATA{i},SIGNALS_Te_DATA{i}] = load_aug_shotfile(...
                                exp_data.ELECTRON_TEMPERATURE_DATA_MIDPLANE_SOURCES{i}, ...
                                exp_data.ELECTRON_TEMPERATURE_DATA_MIDPLANE_SHOT,...
                                'signals',{'ne','ne_unc','Te','Te_unc','Ntscprof','Ntseprof','tsdatcne','tsdatene','Ntscprof','Ntseprof','tsdatcte','tsdatete'});

                        end

                    elseif strcmp(exp_data.ELECTRON_TEMPERATURE_DATA_MIDPLANE_SOURCES{i},'ELM')

                        % ELM-synchronized data

                        SIGNALS_Te_DATA{i} = sprintf('%s/custom/ELM/%d.nc',...
                            SHOTFILES_BASEPATH_LOCAL,exp_data.ELECTRON_TEMPERATURE_DATA_MIDPLANE_SHOT);

                    end

                end

                % Ion temperature data

                for i = 1:length(exp_data.ION_TEMPERATURE_DATA_MIDPLANE_SOURCES)

                    if strcmp(exp_data.ION_TEMPERATURE_DATA_MIDPLANE_SOURCES{i},'CEZ')

                        % Charge-exchange recombination spectroscopy (core system)

                        [~,TIMEBASES_Ti_DATA{i},AREABASES_Ti_DATA{i},SIGNALS_Ti_DATA{i}] = load_aug_shotfile(...
                            exp_data.ION_TEMPERATURE_DATA_MIDPLANE_SOURCES{i}, ...
                            exp_data.ION_TEMPERATURE_DATA_MIDPLANE_SHOT,...
                            'signals',{'Ti_c'});

                    elseif strcmp(exp_data.ION_TEMPERATURE_DATA_MIDPLANE_SOURCES{i},'CMZ')

                        % Charge-exchange recombination spectroscopy (edge system)

                        [~,TIMEBASES_Ti_DATA{i},AREABASES_Ti_DATA{i},SIGNALS_Ti_DATA{i}] = load_aug_shotfile(...
                            exp_data.ION_TEMPERATURE_DATA_MIDPLANE_SOURCES{i}, ...
                            exp_data.ION_TEMPERATURE_DATA_MIDPLANE_SHOT,...
                            'signals',{'Ti_c'});

                    elseif strcmp(exp_data.ION_TEMPERATURE_DATA_MIDPLANE_SOURCES{i},'ELM')

                        % ELM-synchronized data

                        SIGNALS_Ti_DATA{i} = sprintf('%s/custom/ELM/%d.nc',...
                            SHOTFILES_BASEPATH_LOCAL,exp_data.ION_TEMPERATURE_DATA_MIDPLANE_SHOT);

                    end

                end

            end

            %% EXTRACT EXPERIMENTAL DATA FOR AUG

            % Extract profiles from statistical data analysis

            if PLOT_EXP_PROFILES

                % Electron density profile

                time_profiles_ne = TIMEBASES_ne_PROFILES.time.value;
                values_profiles_ne = SIGNALS_ne_PROFILES.ne.value;
                values_profiles_ne_uncertainty = SIGNALS_ne_PROFILES.ne_unc.value;

                profiles_midplane_experiment.ne_profile.name = exp_data.ELECTRON_DENSITY_PROFILE_MIDPLANE_SIGNAL_NAME_DISPLAY;
                [~,profiles_midplane_experiment.ne_profile.values] = ...
                    extract_values('profile',time_profiles_ne,values_profiles_ne,...
                    exp_data.ELECTRON_DENSITY_PROFILE_MIDPLANE_TIME_START,exp_data.ELECTRON_DENSITY_PROFILE_MIDPLANE_TIME_END,false,0);
                [~,profiles_midplane_experiment.ne_profile.values_unc] = ...
                    extract_values('profile',time_profiles_ne,values_profiles_ne_uncertainty,...
                    exp_data.ELECTRON_DENSITY_PROFILE_MIDPLANE_TIME_START,exp_data.ELECTRON_DENSITY_PROFILE_MIDPLANE_TIME_END,false,0);

                % Electron temperature profile

                time_profiles_Te = TIMEBASES_Te_PROFILES.time.value;
                values_profiles_Te = SIGNALS_Te_PROFILES.Te.value;
                values_profiles_Te_uncertainty = SIGNALS_Te_PROFILES.Te_unc.value;

                profiles_midplane_experiment.Te_profile.name = exp_data.ELECTRON_TEMPERATURE_PROFILE_MIDPLANE_SIGNAL_NAME_DISPLAY;
                [~,profiles_midplane_experiment.Te_profile.values] = ...
                    extract_values('profile',time_profiles_Te,values_profiles_Te,...
                    exp_data.ELECTRON_TEMPERATURE_PROFILE_MIDPLANE_TIME_START,exp_data.ELECTRON_TEMPERATURE_PROFILE_MIDPLANE_TIME_END,false,0);
                [~,profiles_midplane_experiment.Te_profile.values_unc] = ...
                    extract_values('profile',time_profiles_Te,values_profiles_Te_uncertainty,...
                    exp_data.ELECTRON_TEMPERATURE_PROFILE_MIDPLANE_TIME_START,exp_data.ELECTRON_TEMPERATURE_PROFILE_MIDPLANE_TIME_END,false,0);

            end

            % Extract diagnostic data

            if PLOT_EXP_DATA

                % Electron density data

                for i = 1:length(exp_data.ELECTRON_DENSITY_DATA_MIDPLANE_SOURCES)

                    if strcmp(exp_data.ELECTRON_DENSITY_DATA_MIDPLANE_SOURCES{i},'LIN')

                        % Lithium beam emission spectroscopy

                        time_data_ne{i} = TIMEBASES_ne_DATA{i}.time.value;
                        values_data_ne{i} = SIGNALS_ne_DATA{i}.ne.value;

                    elseif strcmp(exp_data.ELECTRON_DENSITY_DATA_MIDPLANE_SOURCES{i},'VTA') && strcmp(exp_data.ELECTRON_DENSITY_DATA_MIDPLANE_SIGNALS{i},'Ne_c')

                        % Core Thomson scattering (raw data)

                        time_data_ne{i} = TIMEBASES_ne_DATA{i}.TIM_CORE.value;
                        values_data_ne{i} = transpose(SIGNALS_ne_DATA{i}.Ne_c.value);

                    elseif strcmp(exp_data.ELECTRON_DENSITY_DATA_MIDPLANE_SOURCES{i},'IDA') && strcmp(exp_data.ELECTRON_DENSITY_DATA_MIDPLANE_SIGNALS{i},'tsdatcne')

                        % Core Thomson scattering (IDA)

                        time_data_ne{i} = TIMEBASES_ne_DATA{i}.time.value;
                        for j = 1:size(SIGNALS_ne_DATA{i}.tsdatcne.value,3)
                            values_data_ne{i}(:,j) = SIGNALS_ne_DATA{i}.tsdatcne.value(:,SIGNALS_ne_DATA{i}.Ntscprof.value(j),j);
                            for k = 1:size(values_data_ne{i}(:,j),1)
                                if values_data_ne{i}(k,j) == 0 || values_data_ne{i}(k,j) < 0
                                    values_data_ne{i}(k,j) = NaN;
                                end
                            end
                        end

                    elseif strcmp(exp_data.ELECTRON_DENSITY_DATA_MIDPLANE_SOURCES{i},'VTA') && strcmp(exp_data.ELECTRON_DENSITY_DATA_MIDPLANE_SIGNALS{i},'Ne_e')

                        % Edge Thomson scattering (raw data)

                        time_data_ne{i} = TIMEBASES_ne_DATA{i}.TIM_EDGE.value;
                        values_data_ne{i} = transpose(SIGNALS_ne_DATA{i}.Ne_e.value);

                    elseif strcmp(exp_data.ELECTRON_DENSITY_DATA_MIDPLANE_SOURCES{i},'IDA') && strcmp(exp_data.ELECTRON_DENSITY_DATA_MIDPLANE_SIGNALS{i},'tsdatene')

                        % Edge Thomson scattering (IDA)

                        time_data_ne{i} = TIMEBASES_ne_DATA{i}.time.value;
                        for j = 1:size(SIGNALS_ne_DATA{i}.tsdatene.value,3)
                            values_data_ne{i}(:,j) = SIGNALS_ne_DATA{i}.tsdatene.value(:,SIGNALS_ne_DATA{i}.Ntseprof.value(j),j);
                            for k = 1:size(values_data_ne{i}(:,j),1)
                                if values_data_ne{i}(k,j) == 0 || values_data_ne{i}(k,j) < 0
                                    values_data_ne{i}(k,j) = NaN;
                                end
                            end
                        end

                    elseif strcmp(exp_data.ELECTRON_DENSITY_DATA_MIDPLANE_SOURCES{i},'ELM')

                        % ELM-synchronized data

                        time_data_ne{i} = ncread(SIGNALS_ne_DATA{i},'IDA/time');
                        values_data_ne{i} = ncread(SIGNALS_ne_DATA{i},'IDA/ne');

                    end

                    profiles_midplane_experiment.ne_data{i}.name = exp_data.ELECTRON_DENSITY_DATA_MIDPLANE_NAMES_DISPLAY{i};
                    [profiles_midplane_experiment.ne_data{i}.times,profiles_midplane_experiment.ne_data{i}.values] = ...
                        extract_values('data',time_data_ne{i}, values_data_ne{i},...
                        exp_data.ELECTRON_DENSITY_DATA_MIDPLANE_TIME_START,exp_data.ELECTRON_DENSITY_DATA_MIDPLANE_TIME_END,...
                        exp_data.ELECTRON_DENSITY_DATA_MIDPLANE_REDUCED_SET,exp_data.ELECTRON_DENSITY_DATA_MIDPLANE_REDUCED_SET_TIME_DELTA);

                end

                % Electron temperature data

                for i = 1:length(exp_data.ELECTRON_TEMPERATURE_DATA_MIDPLANE_SOURCES)

                    if strcmp(exp_data.ELECTRON_TEMPERATURE_DATA_MIDPLANE_SOURCES{i},'VTA') && strcmp(exp_data.ELECTRON_TEMPERATURE_DATA_MIDPLANE_SIGNALS{i},'Te_c')

                        % Core Thomson scattering (raw data)

                        time_data_Te{i} = TIMEBASES_Te_DATA{i}.TIM_CORE.value;
                        values_data_Te{i} = transpose(SIGNALS_Te_DATA{i}.Te_c.value);

                    elseif strcmp(exp_data.ELECTRON_TEMPERATURE_DATA_MIDPLANE_SOURCES{i},'IDA') && strcmp(exp_data.ELECTRON_TEMPERATURE_DATA_MIDPLANE_SIGNALS{i},'tsdatcte')

                        % Core Thomson scattering (IDA)

                        time_data_Te{i} = TIMEBASES_Te_DATA{i}.time.value;
                        for j = 1:size(SIGNALS_Te_DATA{i}.tsdatcte.value,3)
                            values_data_Te{i}(:,j) = SIGNALS_Te_DATA{i}.tsdatcte.value(:,SIGNALS_Te_DATA{i}.Ntscprof.value(j),j);
                            for k = 1:size(values_data_Te{i}(:,j),1)
                                if values_data_Te{i}(k,j) == 0 || values_data_Te{i}(k,j) < 0
                                    values_data_Te{i}(k,j) = NaN;
                                end
                            end
                        end

                    elseif strcmp(exp_data.ELECTRON_TEMPERATURE_DATA_MIDPLANE_SOURCES{i},'VTA') && strcmp(exp_data.ELECTRON_TEMPERATURE_DATA_MIDPLANE_SIGNALS{i},'Te_e')

                        % Edge Thomson scattering (raw data)

                        time_data_Te{i} = TIMEBASES_Te_DATA{i}.TIM_EDGE.value;
                        values_data_Te{i} = transpose(SIGNALS_Te_DATA{i}.Te_e.value);

                    elseif strcmp(exp_data.ELECTRON_TEMPERATURE_DATA_MIDPLANE_SOURCES{i},'IDA') && strcmp(exp_data.ELECTRON_TEMPERATURE_DATA_MIDPLANE_SIGNALS{i},'tsdatete')

                        % Edge Thomson scattering (IDA)

                        time_data_Te{i} = TIMEBASES_Te_DATA{i}.time.value;
                        for j = 1:size(SIGNALS_Te_DATA{i}.tsdatete.value,3)
                            values_data_Te{i}(:,j) = SIGNALS_Te_DATA{i}.tsdatete.value(:,SIGNALS_Te_DATA{i}.Ntseprof.value(j),j);
                            for k = 1:size(values_data_Te{i}(:,j),1)
                                if values_data_Te{i}(k,j) == 0 || values_data_Te{i}(k,j) < 0
                                    values_data_Te{i}(k,j) = NaN;
                                end
                            end
                        end

                    elseif strcmp(exp_data.ELECTRON_DENSITY_DATA_MIDPLANE_SOURCES{i},'ELM')

                        % ELM-synchronized data

                        time_data_Te{i} = ncread(SIGNALS_Te_DATA{i},'IDA/time');
                        values_data_Te{i} = ncread(SIGNALS_Te_DATA{i},'IDA/Te');

                    end

                    profiles_midplane_experiment.Te_data{i}.name = exp_data.ELECTRON_TEMPERATURE_DATA_MIDPLANE_NAMES_DISPLAY{i};
                    [profiles_midplane_experiment.Te_data{i}.times,profiles_midplane_experiment.Te_data{i}.values] = ...
                        extract_values('data',time_data_Te{i}, values_data_Te{i},...
                        exp_data.ELECTRON_TEMPERATURE_DATA_MIDPLANE_TIME_START,exp_data.ELECTRON_TEMPERATURE_DATA_MIDPLANE_TIME_END,...
                        exp_data.ELECTRON_TEMPERATURE_DATA_MIDPLANE_REDUCED_SET,exp_data.ELECTRON_TEMPERATURE_DATA_MIDPLANE_REDUCED_SET_TIME_DELTA);

                end

                % Ion temperature data

                for i = 1:length(exp_data.ION_TEMPERATURE_DATA_MIDPLANE_SOURCES)

                    if strcmp(exp_data.ION_TEMPERATURE_DATA_MIDPLANE_SOURCES{i},'CEZ') || strcmp(exp_data.ION_TEMPERATURE_DATA_MIDPLANE_SOURCES{i},'CMZ')

                        % Core and edge charge-exchange recombination spectroscopy

                        time_data_Ti{i} = TIMEBASES_Ti_DATA{i}.time.value;
                        values_data_Ti{i} = transpose(SIGNALS_Ti_DATA{i}.Ti_c.value);

                        profiles_midplane_experiment.Ti_data{i}.name = exp_data.ION_TEMPERATURE_DATA_MIDPLANE_NAMES_DISPLAY{i};
                        [profiles_midplane_experiment.Ti_data{i}.times,profiles_midplane_experiment.Ti_data{i}.values] = ...
                            extract_values('data',time_data_Ti{i}, values_data_Ti{i},...
                            exp_data.ION_TEMPERATURE_DATA_MIDPLANE_TIME_START,exp_data.ION_TEMPERATURE_DATA_MIDPLANE_TIME_END,...
                            exp_data.ION_TEMPERATURE_DATA_MIDPLANE_REDUCED_SET,exp_data.ION_TEMPERATURE_DATA_MIDPLANE_REDUCED_SET_TIME_DELTA);

                    elseif strcmp(exp_data.ION_TEMPERATURE_DATA_MIDPLANE_SOURCES{i},'ELM') && strcmp(exp_data.ION_TEMPERATURE_DATA_MIDPLANE_SIGNALS{i},'Ti_CMZ')

                        % ELM-synchronized data (CMZ)

                        time_data_Ti{i} = ncread(SIGNALS_Ti_DATA{i},'CMZ/time');
                        values_data_Ti{i} = ncread(SIGNALS_Ti_DATA{i},'CMZ/Ti');

                        profiles_midplane_experiment.Ti_data{i}.name = exp_data.ION_TEMPERATURE_DATA_MIDPLANE_NAMES_DISPLAY{i};
                        [profiles_midplane_experiment.Ti_data{i}.times,profiles_midplane_experiment.Ti_data{i}.values] = ...
                            extract_values('data',time_data_Ti{i}, values_data_Ti{i},...
                            exp_data.ION_TEMPERATURE_DATA_MIDPLANE_TIME_START,exp_data.ION_TEMPERATURE_DATA_MIDPLANE_TIME_END,...
                            exp_data.ION_TEMPERATURE_DATA_MIDPLANE_REDUCED_SET,exp_data.ION_TEMPERATURE_DATA_MIDPLANE_REDUCED_SET_TIME_DELTA);

                    elseif strcmp(exp_data.ION_TEMPERATURE_DATA_MIDPLANE_SOURCES{i},'ELM') && strcmp(exp_data.ION_TEMPERATURE_DATA_MIDPLANE_SIGNALS{i},'Ti_CPZ')

                        % ELM-synchronized data (CPZ)

                        time_data_Ti{i} = ncread(SIGNALS_Ti_DATA{i},'CPZ/time');
                        values_data_Ti{i} = ncread(SIGNALS_Ti_DATA{i},'CPZ/Ti');

                        profiles_midplane_experiment.Ti_data{i}.name = exp_data.ION_TEMPERATURE_DATA_MIDPLANE_NAMES_DISPLAY{i};
                        [profiles_midplane_experiment.Ti_data{i}.times,profiles_midplane_experiment.Ti_data{i}.values] = ...
                            extract_values('data',time_data_Ti{i}, values_data_Ti{i},...
                            exp_data.ION_TEMPERATURE_DATA_MIDPLANE_TIME_START,exp_data.ION_TEMPERATURE_DATA_MIDPLANE_TIME_END,...
                            exp_data.ION_TEMPERATURE_DATA_MIDPLANE_REDUCED_SET,exp_data.ION_TEMPERATURE_DATA_MIDPLANE_REDUCED_SET_TIME_DELTA);

                    end

                end

            end

            %% CALCULATE COORDINATES FOR AUG

            % Calculate coordinates for profiles from statistical dana analysis

            if PLOT_EXP_PROFILES

                % Electron density profile

                profiles_midplane_experiment.ne_profile.rho = mean(AREABASES_ne_PROFILES.rhop.value,2) + exp_data.ELECTRON_DENSITY_PROFILE_MIDPLANE_SEPARATRIX_SHIFT;

                % Electron temperature profile

                profiles_midplane_experiment.Te_profile.rho = mean(AREABASES_Te_PROFILES.rhop.value,2) + exp_data.ELECTRON_TEMPERATURE_PROFILE_MIDPLANE_SEPARATRIX_SHIFT;

            end

            % Calculate coordinates for diagnostic data

            if PLOT_EXP_DATA

                % Electron density profile

                for i = 1:length(exp_data.ELECTRON_DENSITY_DATA_MIDPLANE_SOURCES)

                    if strcmp(exp_data.ELECTRON_DENSITY_DATA_MIDPLANE_SOURCES{i},'LIN')

                        % Lithium beam emission spectroscopy

                        profiles_midplane_experiment.ne_data{i}.rho = ...
                            extract_coordinates(time_data_ne{i},AREABASES_ne_DATA{i}.rhop.value,...
                            exp_data.ELECTRON_DENSITY_DATA_MIDPLANE_TIME_START,exp_data.ELECTRON_DENSITY_DATA_MIDPLANE_TIME_END,...
                            exp_data.ELECTRON_DENSITY_DATA_MIDPLANE_REDUCED_SET,exp_data.ELECTRON_DENSITY_DATA_MIDPLANE_REDUCED_SET_TIME_DELTA);

                    elseif strcmp(exp_data.ELECTRON_DENSITY_DATA_MIDPLANE_SOURCES{i},'VTA') && strcmp(exp_data.ELECTRON_DENSITY_DATA_MIDPLANE_SIGNALS{i},'Ne_c')

                        % Core Thomson scattering (raw data)

                        [profiles_midplane_experiment.ne_data{i}.rho,profiles_midplane_experiment.ne_data{i}.values] = Rz_to_rho(...
                            mean(SIGNALS_ne_DATA{i}.R_core.value)*ones(length(SIGNALS_ne_DATA{i}.Z_core.value),1),...
                            SIGNALS_ne_DATA{i}.Z_core.value',...
                            profiles_midplane_experiment.ne_data{i}.values,profiles_midplane_experiment.ne_data{i}.times,...
                            exp_data.ELECTRON_DENSITY_DATA_MIDPLANE_SHOT);

                    elseif strcmp(exp_data.ELECTRON_DENSITY_DATA_MIDPLANE_SOURCES{i},'IDA') && strcmp(exp_data.ELECTRON_DENSITY_DATA_MIDPLANE_SIGNALS{i},'tsdatcne')

                        % Core Thomson scattering (IDA)

                        profiles_midplane_experiment.ne_data{i}.rho = ...
                            extract_coordinates(time_data_ne{i},AREABASES_ne_DATA{i}.x_ts_co.value,...
                            exp_data.ELECTRON_DENSITY_DATA_MIDPLANE_TIME_START,exp_data.ELECTRON_DENSITY_DATA_MIDPLANE_TIME_END,...
                            exp_data.ELECTRON_DENSITY_DATA_MIDPLANE_REDUCED_SET,exp_data.ELECTRON_DENSITY_DATA_MIDPLANE_REDUCED_SET_TIME_DELTA);

                    elseif strcmp(exp_data.ELECTRON_DENSITY_DATA_MIDPLANE_SOURCES{i},'VTA') && strcmp(exp_data.ELECTRON_DENSITY_DATA_MIDPLANE_SIGNALS{i},'Ne_e')

                        % Edge Thomson scattering (raw data)

                        [profiles_midplane_experiment.ne_data{i}.rho,profiles_midplane_experiment.ne_data{i}.values] = Rz_to_rho(...
                            mean(SIGNALS_ne_DATA{i}.R_edge.value)*ones(length(SIGNALS_ne_DATA{i}.Z_edge.value),1),...
                            SIGNALS_ne_DATA{i}.Z_edge.value',...
                            profiles_midplane_experiment.ne_data{i}.values,profiles_midplane_experiment.ne_data{i}.times,...
                            exp_data.ELECTRON_DENSITY_DATA_MIDPLANE_SHOT);

                    elseif strcmp(exp_data.ELECTRON_DENSITY_DATA_MIDPLANE_SOURCES{i},'IDA') && strcmp(exp_data.ELECTRON_DENSITY_DATA_MIDPLANE_SIGNALS{i},'tsdatene')

                        % Edge Thomson scattering (IDA)

                        profiles_midplane_experiment.ne_data{i}.rho = ...
                            extract_coordinates(time_data_ne{i},AREABASES_ne_DATA{i}.x_ts_ed.value,...
                            exp_data.ELECTRON_DENSITY_DATA_MIDPLANE_TIME_START,exp_data.ELECTRON_DENSITY_DATA_MIDPLANE_TIME_END,...
                            exp_data.ELECTRON_DENSITY_DATA_MIDPLANE_REDUCED_SET,exp_data.ELECTRON_DENSITY_DATA_MIDPLANE_REDUCED_SET_TIME_DELTA);

                    elseif strcmp(exp_data.ELECTRON_DENSITY_DATA_MIDPLANE_SOURCES{i},'ELM')

                        % ELM-synchronized data

                        profiles_midplane_experiment.ne_data{i}.rho = ...
                            extract_coordinates(time_data_ne{i},ncread(SIGNALS_ne_DATA{i},'IDA/rho'),...
                            exp_data.ELECTRON_DENSITY_DATA_MIDPLANE_TIME_START,exp_data.ELECTRON_DENSITY_DATA_MIDPLANE_TIME_END,...
                            exp_data.ELECTRON_DENSITY_DATA_MIDPLANE_REDUCED_SET,exp_data.ELECTRON_DENSITY_DATA_MIDPLANE_REDUCED_SET_TIME_DELTA);

                    end

                    profiles_midplane_experiment.ne_data{i}.rho = profiles_midplane_experiment.ne_data{i}.rho...
                        + exp_data.ELECTRON_DENSITY_DATA_MIDPLANE_SEPARATRIX_SHIFT;

                end

                % Electron temperature data

                for i = 1:length(exp_data.ELECTRON_TEMPERATURE_DATA_MIDPLANE_SOURCES)

                    if strcmp(exp_data.ELECTRON_TEMPERATURE_DATA_MIDPLANE_SOURCES{i},'VTA') && strcmp(exp_data.ELECTRON_TEMPERATURE_DATA_MIDPLANE_SIGNALS{i},'Te_c')

                        % Core Thomson scattering (raw data)

                        [profiles_midplane_experiment.Te_data{i}.rho,profiles_midplane_experiment.Te_data{i}.values] = Rz_to_rho(...
                            mean(SIGNALS_Te_DATA{i}.R_core.value)*ones(length(SIGNALS_Te_DATA{i}.Z_core.value),1),...
                            SIGNALS_Te_DATA{i}.Z_core.value',...
                            profiles_midplane_experiment.Te_data{i}.values,profiles_midplane_experiment.Te_data{i}.times,...
                            exp_data.ELECTRON_TEMPERATURE_DATA_MIDPLANE_SHOT);

                    elseif strcmp(exp_data.ELECTRON_TEMPERATURE_DATA_MIDPLANE_SOURCES{i},'IDA') && strcmp(exp_data.ELECTRON_TEMPERATURE_DATA_MIDPLANE_SIGNALS{i},'tsdatcte')

                        % Core Thomson scattering (IDA)

                        profiles_midplane_experiment.Te_data{i}.rho = ...
                            extract_coordinates(time_data_Te{i},AREABASES_Te_DATA{i}.x_ts_co.value,...
                            exp_data.ELECTRON_TEMPERATURE_DATA_MIDPLANE_TIME_START,exp_data.ELECTRON_TEMPERATURE_DATA_MIDPLANE_TIME_END,...
                            exp_data.ELECTRON_TEMPERATURE_DATA_MIDPLANE_REDUCED_SET,exp_data.ELECTRON_TEMPERATURE_DATA_MIDPLANE_REDUCED_SET_TIME_DELTA);

                    elseif strcmp(exp_data.ELECTRON_TEMPERATURE_DATA_MIDPLANE_SOURCES{i},'VTA') && strcmp(exp_data.ELECTRON_TEMPERATURE_DATA_MIDPLANE_SIGNALS{i},'Te_e')

                        % Edge Thomson scattering (raw data)

                        [profiles_midplane_experiment.Te_data{i}.rho,profiles_midplane_experiment.Te_data{i}.values] = Rz_to_rho(...
                            mean(SIGNALS_Te_DATA{i}.R_edge.value)*ones(length(SIGNALS_Te_DATA{i}.Z_edge.value),1),...
                            SIGNALS_Te_DATA{i}.Z_edge.value',...
                            profiles_midplane_experiment.Te_data{i}.values,profiles_midplane_experiment.Te_data{i}.times,...
                            exp_data.ELECTRON_TEMPERATURE_DATA_MIDPLANE_SHOT);

                    elseif strcmp(exp_data.ELECTRON_TEMPERATURE_DATA_MIDPLANE_SOURCES{i},'IDA') && strcmp(exp_data.ELECTRON_TEMPERATURE_DATA_MIDPLANE_SIGNALS{i},'tsdatete')

                        % Edge Thomson scattering (IDA)

                        profiles_midplane_experiment.Te_data{i}.rho = ...
                            extract_coordinates(time_data_Te{i},AREABASES_ne_DATA{i}.x_ts_ed.value,...
                            exp_data.ELECTRON_TEMPERATURE_DATA_MIDPLANE_TIME_START,exp_data.ELECTRON_TEMPERATURE_DATA_MIDPLANE_TIME_END,...
                            exp_data.ELECTRON_TEMPERATURE_DATA_MIDPLANE_REDUCED_SET,exp_data.ELECTRON_TEMPERATURE_DATA_MIDPLANE_REDUCED_SET_TIME_DELTA);

                    elseif strcmp(exp_data.ELECTRON_TEMPERATURE_DATA_MIDPLANE_SOURCES{i},'ELM')

                        % ELM-synchronized data

                        profiles_midplane_experiment.Te_data{i}.rho = ...
                            extract_coordinates(time_data_Te{i},ncread(SIGNALS_Te_DATA{i},'IDA/rho'),...
                            exp_data.ELECTRON_TEMPERATURE_DATA_MIDPLANE_TIME_START,exp_data.ELECTRON_TEMPERATURE_DATA_MIDPLANE_TIME_END,...
                            exp_data.ELECTRON_TEMPERATURE_DATA_MIDPLANE_REDUCED_SET,exp_data.ELECTRON_TEMPERATURE_DATA_MIDPLANE_REDUCED_SET_TIME_DELTA);

                    end

                    profiles_midplane_experiment.Te_data{i}.rho = profiles_midplane_experiment.Te_data{i}.rho...
                        + exp_data.ELECTRON_TEMPERATURE_DATA_MIDPLANE_SEPARATRIX_SHIFT;

                end

                % Ion temperature data

                for i = 1:length(exp_data.ION_TEMPERATURE_DATA_MIDPLANE_SOURCES)

                    if strcmp(exp_data.ION_TEMPERATURE_DATA_MIDPLANE_SOURCES{i},'CEZ') || strcmp(exp_data.ION_TEMPERATURE_DATA_MIDPLANE_SOURCES{i},'CMZ')

                        [profiles_midplane_experiment.Ti_data{i}.rho,profiles_midplane_experiment.Ti_data{i}.values] = ...
                            Rz_to_rho(AREABASES_Ti_DATA{i}.R.value,AREABASES_Ti_DATA{i}.z.value,...
                            profiles_midplane_experiment.Ti_data{i}.values,profiles_midplane_experiment.Ti_data{i}.times,...
                            exp_data.ION_TEMPERATURE_DATA_MIDPLANE_SHOT);

                        profiles_midplane_experiment.Ti_data{i}.rho = profiles_midplane_experiment.Ti_data{i}.rho...
                            + exp_data.ION_TEMPERATURE_DATA_MIDPLANE_SEPARATRIX_SHIFT;

                    elseif strcmp(exp_data.ION_TEMPERATURE_DATA_MIDPLANE_SOURCES{i},'ELM') && strcmp(exp_data.ION_TEMPERATURE_DATA_MIDPLANE_SIGNALS{i},'Ti_CMZ')

                        profiles_midplane_experiment.Ti_data{i}.rho = ...
                            extract_coordinates(time_data_Ti{i},ncread(SIGNALS_Ti_DATA{i},'CMZ/rho'),...
                            exp_data.ION_TEMPERATURE_DATA_MIDPLANE_TIME_START,exp_data.ION_TEMPERATURE_DATA_MIDPLANE_TIME_END,...
                            exp_data.ION_TEMPERATURE_DATA_MIDPLANE_REDUCED_SET,exp_data.ION_TEMPERATURE_DATA_MIDPLANE_REDUCED_SET_TIME_DELTA);

                    elseif strcmp(exp_data.ION_TEMPERATURE_DATA_MIDPLANE_SOURCES{i},'ELM') && strcmp(exp_data.ION_TEMPERATURE_DATA_MIDPLANE_SIGNALS{i},'Ti_CPZ')

                        profiles_midplane_experiment.Ti_data{i}.rho = ...
                            extract_coordinates(time_data_Ti{i},ncread(SIGNALS_Ti_DATA{i},'CPZ/rho'),...
                            exp_data.ION_TEMPERATURE_DATA_MIDPLANE_TIME_START,exp_data.ION_TEMPERATURE_DATA_MIDPLANE_TIME_END,...
                            exp_data.ION_TEMPERATURE_DATA_MIDPLANE_REDUCED_SET,exp_data.ION_TEMPERATURE_DATA_MIDPLANE_REDUCED_SET_TIME_DELTA);

                    end

                end

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

function [time_output,values_output] = extract_values(type,time,values,time_start,time_end,reduced_set,reduced_set_time_delta)

% Inputs:
%   type = 'profile' (values_output = single profile, obtained with a median over all data included between time_start and time_end)
%          'data' (values_output = distinct profiles for different time values included between time_start and time_end)
%   time = array with the original time steps of the experimental data
%   values = matrix with the original values of the experimental data (must be function of 1) space dimension and 2) time dimension)
%   time_start = start of the time window from which to extract the experimental data
%   time_end = end of the time window from which to extract the experimental data
%   reduced_set = true (for extracting averaged data only from a subset of times, between time_start and time_end, if type='data')
%                 false (for extracting original data from all the times between time_start and time_end, if type='data')
%   reduced_set_time_delta = length of the individual time windows, between time_start and time_end,
%                            within which to average the original data, if type='data' and reduced_set = 'true'

if strcmp(type,'profile')

    [~,time_start_index] = min(abs(time_start-time));
    [~,time_end_index] = min(abs(time_end-time));
    for j = 1:(time_end_index-time_start_index+1)
        values_interval(:,j) = values(:,j+time_start_index-1);
    end
    for j = 1:size(values_interval,1)
        values_output(j) = median(values_interval(j,:),'omitnan');
    end
    time_output = [];

elseif strcmp(type,'data')

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

end

%% AUXILIARY FUNCTION TO EXTRACT COORDINATES

function rho_output = extract_coordinates(time,rho,time_start,time_end,reduced_set,reduced_set_time_delta)

% Inputs:
%   time = array with the original time steps of the experimental data
%   rho = matrix with the original rho of the experimental data (must be function of 1) space dimension and 2) time dimension)
%   time_start = start of the time window from which to extract the experimental data
%   time_end = end of the time window from which to extract the experimental data
%   reduced_set = true (for extracting averaged data only from a subset of times, between time_start and time_end, if type='data')
%                 false (for extracting original data from all the times between time_start and time_end, if type='data')
%   reduced_set_time_delta = length of the individual time windows, between time_start and time_end,
%                            within which to average the original data, if type='data' and reduced_set = 'true'

if reduced_set
    time_interval(1) = time_start;
    k = 1;
    while time_interval(k) < time_end-1e-10
        time_interval(k+1) = time_interval(k)+reduced_set_time_delta;
        [~,time_start_index] = min(abs(time_interval(k)-time));
        [~,time_end_index] = min(abs(time_interval(k+1)-time));
        for j = 1:(time_end_index-time_start_index+1)
            rho_delta_interval{k}(j,:) = rho(:,j+time_start_index-1);
        end
        rho_interval(k,:) = median(rho_delta_interval{k}(:,:),1,'omitnan');
        k = k+1;
    end
    rho_output = rho_interval;
else
    [~,time_start_index] = min(abs(time_start-time));
    [~,time_end_index] = min(abs(time_end-time));
    for j = 1:(time_end_index-time_start_index+1)
        rho_output(:,j) = rho(:,j+time_start_index-1);
    end
    rho_output = rho_output';
end

end

%% AUXILIARY FUNCTION TO EXTRACT RHO COORDINATE

function [rho_output,data_output] = Rz_to_rho(R,z,data,time,shot)

temp = find(data(1,:)==0, 1, 'first');
if not(isempty(temp))
    data(:,temp:end) = [];
    R(temp:end) = [];
    z(temp:end) = [];
end

Rz_cell = {}; time_cell = {};

for i = 1:(length(time)-1)
    Rz_cell{end+1} = [R';z'];
    time_cell{end+1} = [time(i) time(i+1)];
end
[~,rho_temp] = map_equilibrium('rzPF',Rz_cell,'H',shot,time_cell);
for i = 1:(length(time)-1)
    rho(:,i) = rho_temp{i};
end

data_output = data;
rho_output = rho';

end
