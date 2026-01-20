function [measurements_midplane_experiment,data_avail] = read_measurements_midplane_experiment(simulation,PLOT_EXP_DATA,PLOT_EXP_PROFILES,COORDINATE)

% read_measurements_midplane_experiment reads the experimental midplane plasma measurements,
% namely electron density, electron temperature, ion temperature and ion species density

%% READ EXPERIMENTAL DATA FROM RUN DIRECTORY

try
    exp_data = read_exp_data_json(simulation);
    data_avail = true;
catch
    data_avail = false;
end

measurements_midplane_experiment = struct();

if data_avail

    switch exp_data.DEVICE

        case 'AUG'

            %% CHECK THAT THE AUG LIBRARY LOCALLY EXISTS

            if ~isfolder(sprintf('%s/scripts.local/MATLAB_analysis_AUG',simulation.SOLPSTOP))
                error(sprintf('Error: MATLAB library for reading AUG experimental data does not exist locally. Get it running the command ''clone_matlab_exp_libraries AUG'''));
            end
            addpath(genpath(sprintf('%s/scripts.local/MATLAB_analysis_AUG',simulation.SOLPSTOP)));

            %% LOAD EXPERIMENTAL DATA FOR AUG

            SHOTFILES_BASEPATH_LOCAL = '';

            for i = 1:numel(AUG_config().SHOTFILES_BASEPATH_LOCAL)
                if isfolder(AUG_config().SHOTFILES_BASEPATH_LOCAL{i})
                    SHOTFILES_BASEPATH_LOCAL = AUG_config().SHOTFILES_BASEPATH_LOCAL{i};
                    break
                end
            end

            % Load shotfiles containing diagnostic data

            if PLOT_EXP_DATA

                % Electron density data

                if isempty(exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.VERSION)

                    for i = 1:length(exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SOURCE)

                        exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.VERSION{i} = 0;

                    end

                end

                for i = 1:length(exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SOURCE)

                    if strcmp(exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SOURCE{i},'LIN')

                        % Lithium beam emission spectroscopy

                        [~,TIMEBASES_ne_DATA{i},AREABASES_ne_DATA{i},SIGNALS_ne_DATA{i}] = load_aug_shotfile(...
                            exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SOURCE{i}, ...
                            exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHOT{i},...
                            'experiment',exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.EXPERIMENT{i},...
                            'edition',exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.VERSION{i},...
                            'signals',{'ne'});

                    elseif strcmp(exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SOURCE{i},'VTA')

                        % Vertical Thomson scattering (raw data)

                        [~,TIMEBASES_ne_DATA{i},AREABASES_ne_DATA{i},SIGNALS_ne_DATA{i}] = load_aug_shotfile(...
                            exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SOURCE{i}, ...
                            exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHOT{i},...
                            'experiment',exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.EXPERIMENT{i},...
                            'edition',exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.VERSION{i},...
                            'signals',{'Ne_c','Ne_e','Z_core','Z_edge','R_core','R_edge'});

                    elseif strcmp(exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SOURCE{i},'IDA')

                        % Vertical Thomson scattering (from IDA shotfile)

                        [~,TIMEBASES_ne_DATA{i},AREABASES_ne_DATA{i},SIGNALS_ne_DATA{i}] = load_aug_shotfile(...
                            exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SOURCE{i}, ...
                            exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHOT{i},...
                            'experiment',exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.EXPERIMENT{i},...
                            'edition',exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.VERSION{i},...
                            'signals',{'ne','ne_unc','Te','Te_unc','Ntscprof','Ntseprof','tsdatcne','tsdatene','Ntscprof','Ntseprof','tsdatcte','tsdatete'});

                    elseif strcmp(exp_data.ELECTRON_DENSITY_DATA_MIDPLANE_SOURCES{i},'ELM')

                        % ELM-synchronized data (custom .nc file)

                        SIGNALS_ne_DATA{i} = sprintf('%s/custom/ELM/%d.nc',...
                            SHOTFILES_BASEPATH_LOCAL,exp_data.ELECTRON_DENSITY_DATA_MIDPLANE_SHOT);

                    end

                end

                % Electron temperature data

                if isempty(exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.VERSION)

                    for i = 1:length(exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SOURCE)

                        exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.VERSION{i} = 0;

                    end

                end

                for i = 1:length(exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SOURCE)

                    if strcmp(exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SOURCE{i},'VTA')

                        % Vertical Thomson scattering (raw data)

                        [~,TIMEBASES_Te_DATA{i},AREABASES_Te_DATA{i},SIGNALS_Te_DATA{i}] = load_aug_shotfile(...
                            exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SOURCE{i}, ...
                            exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHOT{i},...
                            'experiment',exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.EXPERIMENT{i},...
                            'edition',exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.VERSION{i},...
                            'signals',{'Te_c','Te_e','Z_core','Z_edge','R_core','R_edge'});

                    elseif strcmp(exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SOURCE{i},'IDA')

                        % Vertical Thomson scattering (from IDA shotfile)

                        [~,TIMEBASES_Te_DATA{i},AREABASES_Te_DATA{i},SIGNALS_Te_DATA{i}] = load_aug_shotfile(...
                            exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SOURCE{i}, ...
                            exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHOT{i},...
                            'experiment',exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.EXPERIMENT{i},...
                            'edition',exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.VERSION{i},...
                            'signals',{'ne','ne_unc','Te','Te_unc','Ntscprof','Ntseprof','tsdatcne','tsdatene','Ntscprof','Ntseprof','tsdatcte','tsdatete'});

                    elseif strcmp(exp_data.ELECTRON_TEMPERATURE_DATA_MIDPLANE_SOURCES{i},'ELM')

                        % ELM-synchronized data (custom .nc file)

                        SIGNALS_Te_DATA{i} = sprintf('%s/custom/ELM/%d.nc',...
                            SHOTFILES_BASEPATH_LOCAL,exp_data.ELECTRON_TEMPERATURE_DATA_MIDPLANE_SHOT);

                    end

                end

                % Ion temperature data

                if isempty(exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.VERSION)

                    for i = 1:length(exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SOURCE)

                        exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.VERSION{i} = 0;

                    end

                end

                for i = 1:length(exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SOURCE)

                    if strcmp(exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SOURCE{i},'CEZ')

                        % Charge-exchange recombination spectroscopy (core system)

                        [~,TIMEBASES_Ti_DATA{i},AREABASES_Ti_DATA{i},SIGNALS_Ti_DATA{i}] = load_aug_shotfile(...
                            exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SOURCE{i}, ...
                            exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHOT{i},...
                            'experiment',exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.EXPERIMENT{i},...
                            'edition',exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.VERSION{i},...
                            'signals',{'Ti_c'});

                    elseif strcmp(exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SOURCE{i},'CMZ')

                        % Charge-exchange recombination spectroscopy (edge system)

                        [~,TIMEBASES_Ti_DATA{i},AREABASES_Ti_DATA{i},SIGNALS_Ti_DATA{i}] = load_aug_shotfile(...
                            exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SOURCE{i}, ...
                            exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHOT{i},...
                            'experiment',exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.EXPERIMENT{i},...
                            'edition',exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.VERSION{i},...
                            'signals',{'Ti_c'});

                    elseif strcmp(exp_data.ION_TEMPERATURE_DATA_MIDPLANE_SOURCES{i},'ELM')

                        % ELM-synchronized data (custom .nc file)

                        SIGNALS_Ti_DATA{i} = sprintf('%s/custom/ELM/%d.nc',...
                            SHOTFILES_BASEPATH_LOCAL,exp_data.ION_TEMPERATURE_DATA_MIDPLANE_SHOT);

                    end

                end

            end 

            % Load shotfiles containing diagnostic profiles

            if PLOT_EXP_PROFILES

                % Electron density profiles

                if isempty(exp_data.MIDPLANE.PROFILES.ELECTRON_DENSITY_MIDPLANE.VERSION)

                    for i = 1:length(exp_data.MIDPLANE.PROFILES.ELECTRON_DENSITY_MIDPLANE.SOURCE)

                        exp_data.MIDPLANE.PROFILES.ELECTRON_DENSITY_MIDPLANE.VERSION{i} = 0;

                    end

                end

                for i = 1:length(exp_data.MIDPLANE.PROFILES.ELECTRON_DENSITY_MIDPLANE.SOURCE)

                    if strcmp(exp_data.MIDPLANE.PROFILES.ELECTRON_DENSITY_MIDPLANE.SOURCE{i},'IDA')

                        % Integrated data analysis
        
                        [~,TIMEBASES_ne_PROFILES{i},AREABASES_ne_PROFILES{i},SIGNALS_ne_PROFILES{i}] = load_aug_shotfile(...
                            exp_data.MIDPLANE.PROFILES.ELECTRON_DENSITY_MIDPLANE.SOURCE{i}, ...
                            exp_data.MIDPLANE.PROFILES.ELECTRON_DENSITY_MIDPLANE.SHOT{i},...
                            'experiment',exp_data.MIDPLANE.PROFILES.ELECTRON_DENSITY_MIDPLANE.EXPERIMENT{i},...
                            'edition',exp_data.MIDPLANE.PROFILES.ELECTRON_DENSITY_MIDPLANE.VERSION{i},...
                            'signals',{'ne','ne_unc','Te','Te_unc','Ntscprof','Ntseprof','tsdatcne','tsdatene','Ntscprof','Ntseprof','tsdatcte','tsdatete'});

                    end

                end

                % Electron temperature profiles

                if isempty(exp_data.MIDPLANE.PROFILES.ELECTRON_TEMPERATURE_MIDPLANE.VERSION)

                    for i = 1:length(exp_data.MIDPLANE.PROFILES.ELECTRON_TEMPERATURE_MIDPLANE.SOURCE)

                        exp_data.MIDPLANE.PROFILES.ELECTRON_TEMPERATURE_MIDPLANE.VERSION{i} = 0;

                    end

                end

                for i = 1:length(exp_data.MIDPLANE.PROFILES.ELECTRON_TEMPERATURE_MIDPLANE.SOURCE)

                    if strcmp(exp_data.MIDPLANE.PROFILES.ELECTRON_TEMPERATURE_MIDPLANE.SOURCE{i},'IDA')

                        % Integrated data analysis

                        if strcmp(exp_data.MIDPLANE.PROFILES.ELECTRON_TEMPERATURE_MIDPLANE.SOURCE{i},exp_data.MIDPLANE.PROFILES.ELECTRON_DENSITY_MIDPLANE.SOURCE{i}) && ...
                                strcmp(exp_data.MIDPLANE.PROFILES.ELECTRON_TEMPERATURE_MIDPLANE.EXPERIMENT{i},exp_data.MIDPLANE.PROFILES.ELECTRON_DENSITY_MIDPLANE.EXPERIMENT{i}) && ...
                                exp_data.MIDPLANE.PROFILES.ELECTRON_TEMPERATURE_MIDPLANE.SHOT{i}==exp_data.MIDPLANE.PROFILES.ELECTRON_DENSITY_MIDPLANE.SHOT{i}
        
                            TIMEBASES_Te_PROFILES{i} = TIMEBASES_ne_PROFILES{i};
                            AREABASES_Te_PROFILES{i} = AREABASES_ne_PROFILES{i};
                            SIGNALS_Te_PROFILES{i} = SIGNALS_ne_PROFILES{i};
        
                        else
        
                            [~,TIMEBASES_Te_PROFILES{i},AREABASES_Te_PROFILES{i},SIGNALS_Te_PROFILES{i}] = load_aug_shotfile(...
                                exp_data.MIDPLANE.PROFILES.ELECTRON_TEMPERATURE_MIDPLANE.SOURCE{i}, ...
                                exp_data.MIDPLANE.PROFILES.ELECTRON_TEMPERATURE_MIDPLANE.SHOT{i},...
                                'experiment',exp_data.MIDPLANE.PROFILES.ELECTRON_TEMPERATURE_MIDPLANE.EXPERIMENT{i},...
                                'edition',exp_data.MIDPLANE.PROFILES.ELECTRON_TEMPERATURE_MIDPLANE.VERSION{i},...
                                'signals',{'ne','ne_unc','Te','Te_unc','Ntscprof','Ntseprof','tsdatcne','tsdatene','Ntscprof','Ntseprof','tsdatcte','tsdatete'});
        
                        end

                    end

                end

            end

            %% EXTRACT EXPERIMENTAL DATA FOR AUG

            % Extract diagnostic data

            if PLOT_EXP_DATA

                % Electron density data

                for i = 1:length(exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SOURCE)

                    if strcmp(exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SOURCE{i},'LIN')

                        % Lithium beam emission spectroscopy

                        time_data_ne{i} = TIMEBASES_ne_DATA{i}.time.value;
                        values_data_ne{i} = SIGNALS_ne_DATA{i}.ne.value;
                        unit_data_ne{i} = SIGNALS_ne_DATA{i}.ne.unit;

                    elseif strcmp(exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SOURCE{i},'VTA') && strcmp(exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SIGNAL{i},'Ne_c')

                        % Core Thomson scattering (raw data)

                        time_data_ne{i} = TIMEBASES_ne_DATA{i}.TIM_CORE.value;
                        values_data_ne{i} = transpose(SIGNALS_ne_DATA{i}.Ne_c.value);
                        unit_data_ne{i} = SIGNALS_ne_DATA{i}.Ne_c.unit;

                    elseif strcmp(exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SOURCE{i},'IDA') && strcmp(exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SIGNAL{i},'tsdatcne')

                        % Core Thomson scattering (from IDA shotfile)

                        time_data_ne{i} = TIMEBASES_ne_DATA{i}.time.value;
                        for j = 1:size(SIGNALS_ne_DATA{i}.tsdatcne.value,3)
                            values_data_ne{i}(:,j) = SIGNALS_ne_DATA{i}.tsdatcne.value(:,SIGNALS_ne_DATA{i}.Ntscprof.value(j),j);
                            for k = 1:size(values_data_ne{i}(:,j),1)
                                if values_data_ne{i}(k,j) == 0 || values_data_ne{i}(k,j) < 0
                                    values_data_ne{i}(k,j) = NaN;
                                end
                            end
                        end
                        unit_data_ne{i} = SIGNALS_ne_DATA{i}.tsdatcne.unit;

                    elseif strcmp(exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SOURCE{i},'VTA') && strcmp(exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SIGNAL{i},'Ne_e')

                        % Edge Thomson scattering (raw data)

                        time_data_ne{i} = TIMEBASES_ne_DATA{i}.TIM_EDGE.value;
                        values_data_ne{i} = transpose(SIGNALS_ne_DATA{i}.Ne_e.value);
                        unit_data_ne{i} = SIGNALS_ne_DATA{i}.Ne_e.unit;

                    elseif strcmp(exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SOURCE{i},'IDA') && strcmp(exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SIGNAL{i},'tsdatene')

                        % Edge Thomson scattering (from IDA shotfile)

                        time_data_ne{i} = TIMEBASES_ne_DATA{i}.time.value;
                        for j = 1:size(SIGNALS_ne_DATA{i}.tsdatene.value,3)
                            values_data_ne{i}(:,j) = SIGNALS_ne_DATA{i}.tsdatene.value(:,SIGNALS_ne_DATA{i}.Ntseprof.value(j),j);
                            for k = 1:size(values_data_ne{i}(:,j),1)
                                if values_data_ne{i}(k,j) == 0 || values_data_ne{i}(k,j) < 0
                                    values_data_ne{i}(k,j) = NaN;
                                end
                            end
                        end
                        unit_data_ne{i} = SIGNALS_ne_DATA{i}.tsdatene.unit;

                    elseif strcmp(exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SOURCE{i},'ELM')

                        % ELM-synchronized data (from custom .nc file)

                        time_data_ne{i} = ncread(SIGNALS_ne_DATA{i},'IDA/time');
                        values_data_ne{i} = ncread(SIGNALS_ne_DATA{i},'IDA/ne');
                        unit_data_ne{i} = 'm^-3';

                    end

                    measurements_midplane_experiment.ne_data{i}.name = exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.NAME_DISPLAY{i};
                    [measurements_midplane_experiment.ne_data{i}.times,measurements_midplane_experiment.ne_data{i}.values] = ...
                        extract_values('data',time_data_ne{i}, values_data_ne{i},...
                        exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.TIME_START{i},exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.TIME_END{i},...
                        exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.REDUCED_SET_TIME_DELTA{i});
                    measurements_midplane_experiment.ne_data{i}.unit = unit_data_ne{i};

                end

                % Electron temperature data

                for i = 1:length(exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SOURCE)

                    if strcmp(exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SOURCE{i},'VTA') && strcmp(exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SIGNAL{i},'Te_c')

                        % Core Thomson scattering (raw data)

                        time_data_Te{i} = TIMEBASES_Te_DATA{i}.TIM_CORE.value;
                        values_data_Te{i} = transpose(SIGNALS_Te_DATA{i}.Te_c.value);
                        unit_data_Te{i} = SIGNALS_Te_DATA{i}.Te_c.unit;

                    elseif strcmp(exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SOURCE{i},'IDA') && strcmp(exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SIGNAL{i},'tsdatcte')

                        % Core Thomson scattering (from IDA shotfile)

                        time_data_Te{i} = TIMEBASES_Te_DATA{i}.time.value;
                        for j = 1:size(SIGNALS_Te_DATA{i}.tsdatcte.value,3)
                            values_data_Te{i}(:,j) = SIGNALS_Te_DATA{i}.tsdatcte.value(:,SIGNALS_Te_DATA{i}.Ntscprof.value(j),j);
                            for k = 1:size(values_data_Te{i}(:,j),1)
                                if values_data_Te{i}(k,j) == 0 || values_data_Te{i}(k,j) < 0
                                    values_data_Te{i}(k,j) = NaN;
                                end
                            end
                        end
                        unit_data_Te{i} = SIGNALS_Te_DATA{i}.tsdatcte.unit;

                    elseif strcmp(exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SOURCE{i},'VTA') && strcmp(exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SIGNAL{i},'Te_e')

                        % Edge Thomson scattering (raw data)

                        time_data_Te{i} = TIMEBASES_Te_DATA{i}.TIM_EDGE.value;
                        values_data_Te{i} = transpose(SIGNALS_Te_DATA{i}.Te_e.value);
                        unit_data_Te{i} = SIGNALS_Te_DATA{i}.Te_e.unit;

                    elseif strcmp(exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SOURCE{i},'IDA') && strcmp(exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SIGNAL{i},'tsdatete')

                        % Edge Thomson scattering (from IDA shotfile)

                        time_data_Te{i} = TIMEBASES_Te_DATA{i}.time.value;
                        for j = 1:size(SIGNALS_Te_DATA{i}.tsdatete.value,3)
                            values_data_Te{i}(:,j) = SIGNALS_Te_DATA{i}.tsdatete.value(:,SIGNALS_Te_DATA{i}.Ntseprof.value(j),j);
                            for k = 1:size(values_data_Te{i}(:,j),1)
                                if values_data_Te{i}(k,j) == 0 || values_data_Te{i}(k,j) < 0
                                    values_data_Te{i}(k,j) = NaN;
                                end
                            end
                        end
                        unit_data_Te{i} = SIGNALS_Te_DATA{i}.tsdatete.unit;

                    elseif strcmp(exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SOURCE{i},'ELM')

                        % ELM-synchronized data (from custom .nc file)

                        time_data_Te{i} = ncread(SIGNALS_Te_DATA{i},'IDA/time');
                        values_data_Te{i} = ncread(SIGNALS_Te_DATA{i},'IDA/Te');
                        unit_data_Te{i} = 'eV';

                    end

                    measurements_midplane_experiment.Te_data{i}.name = exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.NAME_DISPLAY{i};
                    [measurements_midplane_experiment.Te_data{i}.times,measurements_midplane_experiment.Te_data{i}.values] = ...
                        extract_values('data',time_data_Te{i}, values_data_Te{i},...
                        exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.TIME_START{i},exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.TIME_END{i},...
                        exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.REDUCED_SET_TIME_DELTA{i});
                    measurements_midplane_experiment.Te_data{i}.unit = unit_data_Te{i};

                end

                % Ion temperature data

                for i = 1:length(exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SOURCE)

                    if strcmp(exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SOURCE{i},'CEZ') || strcmp(exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SOURCE{i},'CMZ')

                        % Core and edge charge-exchange recombination spectroscopy

                        time_data_Ti{i} = TIMEBASES_Ti_DATA{i}.time.value;
                        values_data_Ti{i} = transpose(SIGNALS_Ti_DATA{i}.Ti_c.value);
                        unit_data_Ti{i} = SIGNALS_Ti_DATA{i}.Ti_c.unit;

                        measurements_midplane_experiment.Ti_data{i}.name = exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.NAME_DISPLAY{i};
                        [measurements_midplane_experiment.Ti_data{i}.times,measurements_midplane_experiment.Ti_data{i}.values] = ...
                            extract_values('data',time_data_Ti{i}, values_data_Ti{i},...
                            exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.TIME_START{i},exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.TIME_END{i},...
                            exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.REDUCED_SET_TIME_DELTA{i});
                        measurements_midplane_experiment.Ti_data{i}.unit = unit_data_Ti{i};

                    elseif strcmp(exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SOURCE{i},'ELM') && strcmp(exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SIGNAL{i},'Ti_CMZ')

                        % ELM-synchronized data (CMZ, from custom .nc file)

                        time_data_Ti{i} = ncread(SIGNALS_Ti_DATA{i},'CMZ/time');
                        values_data_Ti{i} = ncread(SIGNALS_Ti_DATA{i},'CMZ/Ti');
                        unit_data_Ti{i} = 'eV';

                        measurements_midplane_experiment.Ti_data{i}.name = exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.NAME_DISPLAY{i};
                        [measurements_midplane_experiment.Ti_data{i}.times,measurements_midplane_experiment.Ti_data{i}.values] = ...
                            extract_values('data',time_data_Ti{i}, values_data_Ti{i},...
                            exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.TIME_START{i},exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.TIME_END{i},...
                            exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.REDUCED_SET_TIME_DELTA{i});
                        measurements_midplane_experiment.Ti_data{i}.unit = unit_data_Ti{i};

                    elseif strcmp(exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SOURCE{i},'ELM') && strcmp(exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SIGNAL{i},'Ti_CPZ')

                        % ELM-synchronized data (CPZ, from custom .nc file)

                        time_data_Ti{i} = ncread(SIGNALS_Ti_DATA{i},'CPZ/time');
                        values_data_Ti{i} = ncread(SIGNALS_Ti_DATA{i},'CPZ/Ti');
                        unit_data_Ti{i} = 'eV';

                        measurements_midplane_experiment.Ti_data{i}.name = exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.NAME_DISPLAY{i};
                        [measurements_midplane_experiment.Ti_data{i}.times,measurements_midplane_experiment.Ti_data{i}.values] = ...
                            extract_values('data',time_data_Ti{i}, values_data_Ti{i},...
                            exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.TIME_START{i},exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.TIME_END{i},...
                            exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.REDUCED_SET_TIME_DELTA{i});
                        measurements_midplane_experiment.Ti_data{i}.unit = unit_data_Ti{i};

                    end

                end

            end

            % Extract diagnostic profiles

            if PLOT_EXP_PROFILES

                % Electron density profiles

                for i = 1:length(exp_data.MIDPLANE.PROFILES.ELECTRON_DENSITY_MIDPLANE.SOURCE)

                    if strcmp(exp_data.MIDPLANE.PROFILES.ELECTRON_DENSITY_MIDPLANE.SOURCE{i},'IDA')

                        % Integrated data analysis

                        time_profiles_ne{i} = TIMEBASES_ne_PROFILES{i}.time.value;
                        values_profiles_ne{i} = SIGNALS_ne_PROFILES{i}.ne.value;
                        values_profiles_ne_uncertainty{i} = SIGNALS_ne_PROFILES{i}.ne_unc.value;
                        unit_profiles_ne{i} = SIGNALS_ne_PROFILES{i}.ne.unit;
        
                        measurements_midplane_experiment.ne_profile{i}.name = exp_data.MIDPLANE.PROFILES.ELECTRON_DENSITY_MIDPLANE.NAME_DISPLAY{i};
                        [measurements_midplane_experiment.ne_profile{i}.times,measurements_midplane_experiment.ne_profile{i}.values] = ...
                            extract_values('profile',time_profiles_ne{i},values_profiles_ne{i},...
                            exp_data.MIDPLANE.PROFILES.ELECTRON_DENSITY_MIDPLANE.TIME_START{i},exp_data.MIDPLANE.PROFILES.ELECTRON_DENSITY_MIDPLANE.TIME_END{i},[]);
                        [measurements_midplane_experiment.ne_profile{i}.times,measurements_midplane_experiment.ne_profile{i}.values_unc] = ...
                            extract_values('profile',time_profiles_ne{i},values_profiles_ne_uncertainty{i},...
                            exp_data.MIDPLANE.PROFILES.ELECTRON_DENSITY_MIDPLANE.TIME_START{i},exp_data.MIDPLANE.PROFILES.ELECTRON_DENSITY_MIDPLANE.TIME_END{i},[]);
                        measurements_midplane_experiment.ne_profile{i}.unit = unit_profiles_ne{i};

                    end

                end

                % Electron temperature profiles

                for i = 1:length(exp_data.MIDPLANE.PROFILES.ELECTRON_TEMPERATURE_MIDPLANE.SOURCE)

                    if strcmp(exp_data.MIDPLANE.PROFILES.ELECTRON_TEMPERATURE_MIDPLANE.SOURCE{i},'IDA')

                        % Integrated data analysis

                        time_profiles_Te{i} = TIMEBASES_Te_PROFILES{i}.time.value;
                        values_profiles_Te{i} = SIGNALS_Te_PROFILES{i}.Te.value;
                        values_profiles_Te_uncertainty{i} = SIGNALS_Te_PROFILES{i}.Te_unc.value;
                        unit_profiles_Te{i} = SIGNALS_Te_PROFILES{i}.Te.unit;
        
                        measurements_midplane_experiment.Te_profile{i}.name = exp_data.MIDPLANE.PROFILES.ELECTRON_TEMPERATURE_MIDPLANE.NAME_DISPLAY{i};
                        [measurements_midplane_experiment.Te_profile{i}.times,measurements_midplane_experiment.Te_profile{i}.values] = ...
                            extract_values('profile',time_profiles_Te{i},values_profiles_Te{i},...
                            exp_data.MIDPLANE.PROFILES.ELECTRON_TEMPERATURE_MIDPLANE.TIME_START{i},exp_data.MIDPLANE.PROFILES.ELECTRON_TEMPERATURE_MIDPLANE.TIME_END{i},[]);
                        [measurements_midplane_experiment.Te_profile{i}.times,measurements_midplane_experiment.Te_profile{i}.values_unc] = ...
                            extract_values('profile',time_profiles_Te{i},values_profiles_Te_uncertainty{i},...
                            exp_data.MIDPLANE.PROFILES.ELECTRON_TEMPERATURE_MIDPLANE.TIME_START{i},exp_data.MIDPLANE.PROFILES.ELECTRON_TEMPERATURE_MIDPLANE.TIME_END{i},[]);
                        measurements_midplane_experiment.Te_profile{i}.unit = unit_profiles_Te{i};

                    end

                end

            end

            %% CALCULATE COORDINATES FOR AUG

            % Calculate coordinates for diagnostic data

            if PLOT_EXP_DATA

                % Electron density profile

                for i = 1:length(exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SOURCE)

                    if strcmp(exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SOURCE{i},'LIN')

                        % Lithium beam emission spectroscopy

                        coordinate_shotfile = ...
                            extract_coordinates(time_data_ne{i},AREABASES_ne_DATA{i}.rhop.value,...
                            exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.TIME_START{i},exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.TIME_END{i},...
                            exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.REDUCED_SET_TIME_DELTA{i});

                        [measurements_midplane_experiment.ne_data{i}.coordinate,~] = shift_convert_coordinate(...
                            exp_data.DEVICE,measurements_midplane_experiment.ne_data{i}.times,[],...
                            exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHOT{i},coordinate_shotfile,[],'rhop',COORDINATE,i,...
                            exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_RHOP,...
                            exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_DSSEP,...
                            exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_R);

                        measurements_midplane_experiment.ne_data{i}.coordinate_type = COORDINATE;

                    elseif strcmp(exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SOURCE{i},'VTA') && strcmp(exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SIGNAL{i},'Ne_c')

                        % Core Thomson scattering (raw data)

                        coordinate_shotfile = mean(SIGNALS_ne_DATA{i}.R_core.value)*ones(length(SIGNALS_ne_DATA{i}.Z_core.value),1);
                        z_coordinate_shotfile = SIGNALS_ne_DATA{i}.Z_core.value';

                        [measurements_midplane_experiment.ne_data{i}.coordinate,measurements_midplane_experiment.ne_data{i}.values] = shift_convert_coordinate(...
                            exp_data.DEVICE,measurements_midplane_experiment.ne_data{i}.times,measurements_midplane_experiment.ne_data{i}.values,...
                            exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHOT{i},coordinate_shotfile,z_coordinate_shotfile,'R',COORDINATE,i,...
                            exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_RHOP,...
                            exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_DSSEP,...
                            exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_R);

                        measurements_midplane_experiment.ne_data{i}.coordinate_type = COORDINATE;

                    elseif strcmp(exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SOURCE{i},'IDA') && strcmp(exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SIGNAL{i},'tsdatcne')

                        % Core Thomson scattering (from IDA shotfile)

                        coordinate_shotfile = ...
                            extract_coordinates(time_data_ne{i},AREABASES_ne_DATA{i}.x_ts_co.value,...
                            exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.TIME_START{i},exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.TIME_END{i},...
                            exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.REDUCED_SET_TIME_DELTA{i});

                        [measurements_midplane_experiment.ne_data{i}.coordinate,~] = shift_convert_coordinate(...
                            exp_data.DEVICE,measurements_midplane_experiment.ne_data{i}.times,[],...
                            exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHOT{i},coordinate_shotfile,[],'rhop',COORDINATE,i,...
                            exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_RHOP,...
                            exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_DSSEP,...
                            exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_R);

                        measurements_midplane_experiment.ne_data{i}.coordinate_type = COORDINATE;

                    elseif strcmp(exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SOURCE{i},'VTA') && strcmp(exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SIGNAL{i},'Ne_e')

                        % Edge Thomson scattering (raw data)

                        coordinate_shotfile = mean(SIGNALS_ne_DATA{i}.R_edge.value)*ones(length(SIGNALS_ne_DATA{i}.Z_edge.value),1);
                        z_coordinate_shotfile = SIGNALS_ne_DATA{i}.Z_edge.value';

                        [measurements_midplane_experiment.ne_data{i}.coordinate,measurements_midplane_experiment.ne_data{i}.values] = shift_convert_coordinate(...
                            exp_data.DEVICE,measurements_midplane_experiment.ne_data{i}.times,measurements_midplane_experiment.ne_data{i}.values,...
                            exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHOT{i},coordinate_shotfile,z_coordinate_shotfile,'R',COORDINATE,i,...
                            exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_RHOP,...
                            exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_DSSEP,...
                            exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_R);

                        measurements_midplane_experiment.ne_data{i}.coordinate_type = COORDINATE;

                    elseif strcmp(exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SOURCE{i},'IDA') && strcmp(exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SIGNAL{i},'tsdatene')

                        % Edge Thomson scattering (from IDA shotfile)

                        coordinate_shotfile = ...
                            extract_coordinates(time_data_ne{i},AREABASES_ne_DATA{i}.x_ts_ed.value,...
                            exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.TIME_START{i},exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.TIME_END{i},...
                            exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.REDUCED_SET_TIME_DELTA{i});

                        [measurements_midplane_experiment.ne_data{i}.coordinate,~] = shift_convert_coordinate(...
                            exp_data.DEVICE,measurements_midplane_experiment.ne_data{i}.times,[],...
                            exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHOT{i},coordinate_shotfile,[],'rhop',COORDINATE,i,...
                            exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_RHOP,...
                            exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_DSSEP,...
                            exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_R);

                        measurements_midplane_experiment.ne_data{i}.coordinate_type = COORDINATE;

                    elseif strcmp(exp_data.ELECTRON_DENSITY_DATA_MIDPLANE_SOURCES{i},'ELM')

                        % ELM-synchronized data (from custom .nc file)

                        coordinate_shotfile = ...
                            extract_coordinates(time_data_ne{i},ncread(SIGNALS_ne_DATA{i},'IDA/rho'),...
                            exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.TIME_START{i},exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.TIME_END{i},...
                            exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.REDUCED_SET_TIME_DELTA{i});

                        [measurements_midplane_experiment.ne_data{i}.coordinate,~] = shift_convert_coordinate(...
                            exp_data.DEVICE,measurements_midplane_experiment.ne_data{i}.times,[],...
                            exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHOT{i},coordinate_shotfile,[],'rhop',COORDINATE,i,...
                            exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_RHOP,...
                            exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_DSSEP,...
                            exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_R);

                        measurements_midplane_experiment.ne_data{i}.coordinate_type = COORDINATE;

                    end

                end

                % Electron temperature data

                for i = 1:length(exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SOURCE)

                    if strcmp(exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SOURCE{i},'VTA') && strcmp(exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SIGNAL{i},'Te_c')

                        % Core Thomson scattering (raw data)

                        coordinate_shotfile = mean(SIGNALS_Te_DATA{i}.R_core.value)*ones(length(SIGNALS_Te_DATA{i}.Z_core.value),1);
                        z_coordinate_shotfile = SIGNALS_Te_DATA{i}.Z_core.value;

                        [measurements_midplane_experiment.Te_data{i}.coordinate,measurements_midplane_experiment.Te_data{i}.values] = shift_convert_coordinate(...
                            exp_data.DEVICE,measurements_midplane_experiment.Te_data{i}.times,measurements_midplane_experiment.Te_data{i}.values,...
                            exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHOT{i},coordinate_shotfile,z_coordinate_shotfile,'R',COORDINATE,i,...
                            exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_RHOP,...
                            exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_DSSEP,...
                            exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_R);

                        measurements_midplane_experiment.ne_data{i}.coordinate_type = COORDINATE;

                    elseif strcmp(exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SOURCE{i},'IDA') && strcmp(exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SIGNAL{i},'tsdatcte')

                        % Core Thomson scattering (from IDA shotfile)

                        coordinate_shotfile = ...
                            extract_coordinates(time_data_Te{i},AREABASES_Te_DATA{i}.x_ts_co.value,...
                            exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.TIME_START{i},exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.TIME_END{i},...
                            exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.REDUCED_SET_TIME_DELTA{i});

                        [measurements_midplane_experiment.Te_data{i}.coordinate,~] = shift_convert_coordinate(...
                            exp_data.DEVICE,measurements_midplane_experiment.Te_data{i}.times,[],...
                            exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHOT{i},coordinate_shotfile,[],'rhop',COORDINATE,i,...
                            exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_RHOP,...
                            exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_DSSEP,...
                            exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_R);

                        measurements_midplane_experiment.Te_data{i}.coordinate_type = COORDINATE;

                    elseif strcmp(exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SOURCE{i},'VTA') && strcmp(exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SIGNAL{i},'Te_e')

                        % Edge Thomson scattering (raw data)

                        coordinate_shotfile = mean(SIGNALS_Te_DATA{i}.R_edge.value)*ones(length(SIGNALS_Te_DATA{i}.Z_edge.value),1);
                        z_coordinate_shotfile = SIGNALS_Te_DATA{i}.Z_edge.value';

                        [measurements_midplane_experiment.Te_data{i}.coordinate,measurements_midplane_experiment.Te_data{i}.values] = shift_convert_coordinate(...
                            exp_data.DEVICE,measurements_midplane_experiment.Te_data{i}.times,measurements_midplane_experiment.Te_data{i}.values,...
                            exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHOT{i},coordinate_shotfile,z_coordinate_shotfile,'R',COORDINATE,i,...
                            exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_RHOP,...
                            exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_DSSEP,...
                            exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_R);

                        measurements_midplane_experiment.ne_data{i}.coordinate_type = COORDINATE;

                    elseif strcmp(exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SOURCE{i},'IDA') && strcmp(exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SIGNAL{i},'tsdatete')

                        % Edge Thomson scattering (from IDA shotfile)

                        coordinate_shotfile = ...
                            extract_coordinates(time_data_Te{i},AREABASES_Te_DATA{i}.x_ts_ed.value,...
                            exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.TIME_START{i},exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.TIME_END{i},...
                            exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.REDUCED_SET_TIME_DELTA{i});

                        [measurements_midplane_experiment.Te_data{i}.coordinate,~] = shift_convert_coordinate(...
                            exp_data.DEVICE,measurements_midplane_experiment.Te_data{i}.times,[],...
                            exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHOT{i},coordinate_shotfile,[],'rhop',COORDINATE,i,...
                            exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_RHOP,...
                            exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_DSSEP,...
                            exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_R);

                        measurements_midplane_experiment.Te_data{i}.coordinate_type = COORDINATE;

                    elseif strcmp(exp_data.ELECTRON_TEMPERATURE_DATA_MIDPLANE_SOURCES{i},'ELM')

                        % ELM-synchronized data (from custom .nc file)

                        coordinate_shotfile = ...
                            extract_coordinates(time_data_Te{i},ncread(SIGNALS_Te_DATA{i},'IDA/rho'),...
                            exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.TIME_START{i},exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.TIME_END{i},...
                            exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.REDUCED_SET_TIME_DELTA{i});

                        [measurements_midplane_experiment.Te_data{i}.coordinate,~] = shift_convert_coordinate(...
                            exp_data.DEVICE,measurements_midplane_experiment.Te_data{i}.times,[],...
                            exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHOT{i},coordinate_shotfile,[],'rhop',COORDINATE,i,...
                            exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_RHOP,...
                            exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_DSSEP,...
                            exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_R);

                        measurements_midplane_experiment.Te_data{i}.coordinate_type = COORDINATE;

                    end

                end

                % Ion temperature data

                for i = 1:length(exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SOURCE)

                    if strcmp(exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SOURCE{i},'CEZ') || strcmp(exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SOURCE{i},'CMZ')

                       % Core and edge charge-exchange recombination spectroscopy

                        coordinate_shotfile = AREABASES_Ti_DATA{i}.R.value;
                        z_coordinate_shotfile = AREABASES_Ti_DATA{i}.z.value;

                        [measurements_midplane_experiment.Ti_data{i}.coordinate,measurements_midplane_experiment.Ti_data{i}.values] = shift_convert_coordinate(...
                            exp_data.DEVICE,measurements_midplane_experiment.Ti_data{i}.times,measurements_midplane_experiment.Ti_data{i}.values,...
                            exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHOT{i},coordinate_shotfile,z_coordinate_shotfile,'R',COORDINATE,i,...
                            exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHIFT_RHOP,...
                            exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHIFT_DSSEP,...
                            exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHIFT_R);

                        measurements_midplane_experiment.Ti_data{i}.coordinate_type = COORDINATE;

                    elseif strcmp(exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SOURCE{i},'ELM') && strcmp(exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SIGNAL{i},'Ti_CMZ')

                        % ELM-synchronized data (CMZ, from custom .nc file)

                        coordinate_shotfile = ...
                            extract_coordinates(time_data_Ti{i},ncread(SIGNALS_Ti_DATA{i},'CMZ/rho'),...
                            exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.TIME_START{i},exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.TIME_END{i},...
                            exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.REDUCED_SET_TIME_DELTA{i});

                        [measurements_midplane_experiment.Ti_data{i}.coordinate,~] = shift_convert_coordinate(...
                            exp_data.DEVICE,measurements_midplane_experiment.Ti_data{i}.times,[],...
                            exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHOT{i},coordinate_shotfile,[],'rhop',COORDINATE,i,...
                            exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHIFT_RHOP,...
                            exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHIFT_DSSEP,...
                            exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHIFT_R);

                        measurements_midplane_experiment.Ti_data{i}.coordinate_type = COORDINATE;

                    elseif strcmp(exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SOURCE{i},'ELM') && strcmp(exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SIGNAL{i},'Ti_CPZ')

                        % ELM-synchronized data (CPZ, from custom .nc file)

                        coordinate_shotfile = ...
                            extract_coordinates(time_data_Ti{i},ncread(SIGNALS_Ti_DATA{i},'CPZ/rho'),...
                            exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.TIME_START{i},exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.TIME_END{i},...
                            exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.REDUCED_SET_TIME_DELTA{i});

                        [measurements_midplane_experiment.Ti_data{i}.coordinate,~] = shift_convert_coordinate(...
                            exp_data.DEVICE,measurements_midplane_experiment.Ti_data{i}.times,[],...
                            exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHOT{i},coordinate_shotfile,[],'rhop',COORDINATE,i,...
                            exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHIFT_RHOP,...
                            exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHIFT_DSSEP,...
                            exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHIFT_R);

                        measurements_midplane_experiment.Ti_data{i}.coordinate_type = COORDINATE;

                    end

                end

            end

            % Calculate coordinates for diagnostic profiles

            if PLOT_EXP_PROFILES

                % Electron density profiles

                for i = 1:length(exp_data.MIDPLANE.PROFILES.ELECTRON_DENSITY_MIDPLANE.SOURCE)

                    if strcmp(exp_data.MIDPLANE.PROFILES.ELECTRON_DENSITY_MIDPLANE.SOURCE{i},'IDA')

                        % Integrated data analysis

                        coordinate_shotfile = mean(AREABASES_ne_PROFILES{i}.rhop.value,2);

                        [measurements_midplane_experiment.ne_profile{i}.coordinate,~] = shift_convert_coordinate(...
                            exp_data.DEVICE,measurements_midplane_experiment.ne_profile{i}.times,[],...
                            exp_data.MIDPLANE.PROFILES.ELECTRON_DENSITY_MIDPLANE.SHOT{i},coordinate_shotfile',[],'rhop',COORDINATE,i,...
                            exp_data.MIDPLANE.PROFILES.ELECTRON_DENSITY_MIDPLANE.SHIFT_RHOP,...
                            exp_data.MIDPLANE.PROFILES.ELECTRON_DENSITY_MIDPLANE.SHIFT_DSSEP,...
                            exp_data.MIDPLANE.PROFILES.ELECTRON_DENSITY_MIDPLANE.SHIFT_R);

                        measurements_midplane_experiment.ne_profile{i}.coordinate_type = COORDINATE;

                    end

                end

                % Electron temperature profiles

                for i = 1:length(exp_data.MIDPLANE.PROFILES.ELECTRON_TEMPERATURE_MIDPLANE.SOURCE)

                    if strcmp(exp_data.MIDPLANE.PROFILES.ELECTRON_TEMPERATURE_MIDPLANE.SOURCE{i},'IDA')

                        % Integrated data analysis

                        coordinate_shotfile = mean(AREABASES_Te_PROFILES{i}.rhop.value,2);

                        [measurements_midplane_experiment.Te_profile{i}.coordinate,~] = shift_convert_coordinate(...
                            exp_data.DEVICE,measurements_midplane_experiment.Te_profile{i}.times,[],...
                            exp_data.MIDPLANE.PROFILES.ELECTRON_TEMPERATURE_MIDPLANE.SHOT{i},coordinate_shotfile',[],'rhop',COORDINATE,i,...
                            exp_data.MIDPLANE.PROFILES.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_RHOP,...
                            exp_data.MIDPLANE.PROFILES.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_DSSEP,...
                            exp_data.MIDPLANE.PROFILES.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_R);

                        measurements_midplane_experiment.Te_profile{i}.coordinate_type = COORDINATE;

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

function [time_output,values_output] = extract_values(type,time,values,time_start,time_end,reduced_set_time_delta)

% Inputs:
%   type = 'profile' (values_output = single profile, obtained with a median over all data included between time_start and time_end)
%          'data' (values_output = distinct profiles for different time values included between time_start and time_end)
%   time = array with the original time steps of the experimental data
%   values = matrix with the original values of the experimental data (must be function of 1) space dimension and 2) time dimension)
%   time_start = start of the time window from which to extract the experimental data
%   time_end = end of the time window from which to extract the experimental data
%   reduced_set_time_delta = if non empty, then extracts averaged data only from a subset of times, between time_start and time_end
%                            with value determining the length of the individual time windows, between time_start and time_end, 
%                            within which to average the original data (only relevant if type='data')

if strcmp(type,'profile')

    [~,time_start_index] = min(abs(time_start-time));
    [~,time_end_index] = min(abs(time_end-time));
    for j = 1:(time_end_index-time_start_index+1)
        values_interval(:,j) = values(:,j+time_start_index-1);
        time_output(j) = time(time_start_index+j-1);
    end
    for j = 1:size(values_interval,1)
        values_output(j) = median(values_interval(j,:),'omitnan');
    end

elseif strcmp(type,'data')

    if not(isempty(reduced_set_time_delta))
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

    time_output = (time_output(1:end-1) + time_output(2:end)) / 2;

end

end

%% AUXILIARY FUNCTION TO EXTRACT COORDINATES

function coordinate_output = extract_coordinates(time,coordinate,time_start,time_end,reduced_set_time_delta)

% Inputs:
%   time = array with the original time steps of the experimental data
%   coordinate = matrix with the original coordinate of the experimental data (must be function of 1) space dimension and 2) time dimension)
%   time_start = start of the time window from which to extract the experimental data
%   time_end = end of the time window from which to extract the experimental data
%   reduced_set_time_delta = if non empty, then extracts averaged data only from a subset of times, between time_start and time_end
%                            with value determining the length of the individual time windows, between time_start and time_end, 
%                            within which to average the original data (only relevant if type='data')

if not(isempty(reduced_set_time_delta))
    time_interval(1) = time_start;
    k = 1;
    while time_interval(k) < time_end-1e-10
        time_interval(k+1) = time_interval(k)+reduced_set_time_delta;
        [~,time_start_index] = min(abs(time_interval(k)-time));
        [~,time_end_index] = min(abs(time_interval(k+1)-time));
        for j = 1:(time_end_index-time_start_index+1)
            coordinate_delta_interval{k}(j,:) = coordinate(:,j+time_start_index-1);
        end
        coordinate_interval(k,:) = median(coordinate_delta_interval{k}(:,:),1,'omitnan');
        k = k+1;
    end
    coordinate_output = coordinate_interval;
else
    [~,time_start_index] = min(abs(time_start-time));
    [~,time_end_index] = min(abs(time_end-time));
    for j = 1:(time_end_index-time_start_index+1)
        coordinate_output(:,j) = coordinate(:,j+time_start_index-1);
    end
    coordinate_output = coordinate_output';
end

end

%% AUXILIARY FUNCTION TO SHIFT AND CONVERT COORDINATES

function [coordinate_output,data_output] = shift_convert_coordinate(device,times,data_values,shot,coordinate_input,z_coordinate_input,type_input,type_output,index,rhop_shift,dssep_shift,R_shift)

data_output = [];

if strcmp(type_input,type_output)

   switch type_output

       case 'rhop'

            if not(isempty(rhop_shift))
                coordinate_output = coordinate_input + rhop_shift{index};
            else
                coordinate_output = coordinate_input;
            end

       case 'dssep'

            if not(isempty(dssep_shift))
                coordinate_output = coordinate_input + dssep_shift{index};
            else
                coordinate_output = coordinate_input;
            end

       case 'R'

            if not(isempty(R_shift))
                coordinate_output = coordinate_input + R_shift{index};
            else
                coordinate_output = coordinate_input;
            end

       otherwise

           error('Error: supported coordinates in read_measurements_midplane_experiment are ''rhop'', ''dssep'', ''R''');

   end

else

   switch type_input

       case 'rhop'

            if not(isempty(rhop_shift))
                coordinate_input = coordinate_input + rhop_shift{index};
            end

            switch type_output

                case 'dssep'

                    coordinate_output = rhop_to_dssep(device,coordinate_input,times,shot);
                    if not(isempty(dssep_shift))
                        coordinate_output = coordinate_output + dssep_shift{index};
                    end

                case 'R'

                    coordinate_output = rhop_to_Rz(device,coordinate_input,times,shot);
                    if not(isempty(R_shift))
                        coordinate_output = coordinate_output + R_shift{index};
                    end

            end

       case 'dssep'

            if not(isempty(dssep_shift))
                coordinate_input = coordinate_input + dssep_shift{index};
            end

            switch type_output

                case 'rhop'

                    coordinate_output = dssep_to_rhop(device,coordinate_input,times,shot);
                    if not(isempty(rhop_shift))
                        coordinate_output = coordinate_output + rhop_shift{index};
                    end

                case 'R'

                    coordinate_output = dssep_to_Rz(device,coordinate_input,times,shot);
                    if not(isempty(R_shift))
                        coordinate_output = coordinate_output + R_shift{index};
                    end

            end

       case 'R'

            if not(isempty(R_shift))
                coordinate_input = coordinate_input + R_shift{index};
            end

            switch type_output

                case 'rhop'

                    [coordinate_output,data_output] = Rz_to_rhop(device,coordinate_input,z_coordinate_input,data_values,times,shot);
                    if not(isempty(rhop_shift))
                        coordinate_output = coordinate_output + rhop_shift{index};
                    end

                case 'dssep'

                    [coordinate_output,data_output] = Rz_to_dssep(device,coordinate_input,z_coordinate_input,data_values,times,shot);
                    if not(isempty(dssep_shift))
                        coordinate_output = coordinate_output + dssep_shift{index};
                    end

            end

       otherwise

           error('Error: supported coordinates in read_measurements_midplane_experiment are ''rhop'', ''dssep'', ''R''');

   end

end

end

%% AUXILIARY FUNCTIONS TO PERFORM COORDINATES MAPPING

function [rhop_output,data_output] = Rz_to_rhop(device,R,z,data,time,shot)

    switch device
    
        case 'AUG'
    
            temp = find(data(1,:)==0, 1, 'first');
            if not(isempty(temp))
                data(:,temp:end) = [];
                R(temp:end) = [];
                z(temp:end) = [];
            end
            
            data_output = data;
            
            equ = EQU(shot, 'diag', 'EQI',  'tbeg', time(1), 'tend', time(end));
            rhop_output = equ.rz2rho(R, z, 't_in', time, 'coord_out', 'rho_pol', 'extrapolate', 'true');
    
    end

end

function [dssep_output,data_output] = Rz_to_dssep(device,R,z,data,time,shot)

    switch device
    
        case 'AUG'
    
            temp = find(data(1,:)==0, 1, 'first');
            if not(isempty(temp))
                data(:,temp:end) = [];
                R(temp:end) = [];
                z(temp:end) = [];
            end
            
            data_output = data;

            equ = EQU(shot, 'diag', 'EQI',  'tbeg', time(1), 'tend', time(end));
            
            for i = 1:length(time)
                [R_sep(i), z] = equ.rhoTheta2rz(1, 0, 't_in', time(i), 'coord_in', 'rho_pol');
            end

            dssep_output = (R - R_sep)';
    
    end

end

function R_output = rhop_to_Rz(device,rhop,time,shot)

    switch device
    
        case 'AUG'
        
            equ = EQU(shot, 'diag', 'EQI',  'tbeg', time(1), 'tend', time(end));
            
            if size(rhop,1) == 1
                [R_output(1,:), z] = equ.rhoTheta2rz(rhop(1,:), 0, 't_in', (time(1)+time(end))/2, 'coord_in', 'rho_pol');
            else
                for i = 1:length(time)
                    [R_output(i,:), z] = equ.rhoTheta2rz(rhop(i,:), 0, 't_in', time(i), 'coord_in', 'rho_pol');
                end
            end
        
        end

end

function R_output = rhop_to_dssep(device,rhop,time,shot)

    switch device
    
        case 'AUG'
        
            equ = EQU(shot, 'diag', 'EQI',  'tbeg', time(1), 'tend', time(end));

            if size(rhop,1) == 1
                [R_sep, z] = equ.rhoTheta2rz(1, 0, 't_in', (time(1)+time(end))/2, 'coord_in', 'rho_pol');
                [R_output(1,:), z] = equ.rhoTheta2rz(rhop(1,:), 0, 't_in', (time(1)+time(end))/2, 'coord_in', 'rho_pol');
                R_output(1,:) = R_output(1,:) - R_sep;
            else
                for i = 1:length(time)
                    [R_sep, z] = equ.rhoTheta2rz(1, 0, 't_in', time(i), 'coord_in', 'rho_pol');
                    [R_output(i,:), z] = equ.rhoTheta2rz(rhop(i,:), 0, 't_in', time(i), 'coord_in', 'rho_pol');
                    R_output(i,:) = R_output(i,:) - R_sep;
                end
            end
    
    end

end
