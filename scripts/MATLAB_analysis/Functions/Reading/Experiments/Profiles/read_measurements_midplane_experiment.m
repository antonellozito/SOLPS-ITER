function [measurements_midplane_experiment,exp_data_avail] = read_measurements_midplane_experiment(simulation)

% read_measurements_midplane_experiment reads the experimental midplane plasma measurements,
% namely electron density, electron temperature, ion temperature and ion species density

%% READ EXPERIMENTAL DATA FROM RUN DIRECTORY

try
    exp_data = read_exp_data_json(simulation);
    exp_data_avail = true;
catch
    exp_data_avail = false;
end

measurements_midplane_experiment = struct();

if exp_data_avail

    % Check if the same requested experimental data were already stored in
    % a .mat file in the run directory from a previous call of this function

    mat_file_name = sprintf('%s/exp_data_midplane.mat',simulation.RUN_DIRECTORY);
    old_store_data_found = false;

    if isfile(mat_file_name)

        % Check if, within exp_data_midplane.mat, there is already a stored
        % version of the experimental data identical to the one requested now

        load(mat_file_name);
        mat_file_name_old_editions = length(measurements_midplane_experiment_file);

        i = 1;
        while i <= mat_file_name_old_editions
            [structs_equal, diffReport] = compare_structures(exp_data, measurements_midplane_experiment_file(i).exp_data_namelist);
            if structs_equal
                old_store_data_found = true;
                measurements_midplane_experiment = ...
                    measurements_midplane_experiment_file(i).exp_data_measurements;
                fprintf('Requested midplane experimental data found in exp_data_midplane.mat, version %d\n',i);
                break;
            end
            i = i + 1;
        end

    end

    if not(old_store_data_found)

        fprintf('Requested midplane experimental not stored in any edition of exp_data_midplane.mat: fetching them now\n');

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

                % Electron density data

                for i = 1:length(exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SOURCE)

                    if strcmp(exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SOURCE{i},'LIN')

                        % Lithium beam emission spectroscopy

                        try

                            [~,TIMEBASES_ne_DATA{i},AREABASES_ne_DATA{i},SIGNALS_ne_DATA{i}] = load_aug_shotfile(...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SOURCE{i}, ...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHOT{i},...
                                'experiment',exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.EXPERIMENT{i},...
                                'edition',exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.VERSION{i},...
                                'signals',{'ne'});

                            fprintf('AUG shotfile for LiBES electron density data correctly fetched\n');

                            READ_ne_DATA{i} = true;

                        catch

                            fprintf('LiBES electron density data from AUG (shot %d, shotfile %s, experiment %s, edition %d) requested but not found\n',...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHOT{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SOURCE{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.EXPERIMENT{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.VERSION{i});
                            fprintf('Try to set another shot/shotfile/experiment/edition for MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE within exp_data.json\n');

                            READ_ne_DATA{i} = false;

                        end

                    elseif strcmp(exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SOURCE{i},'VTA')

                        % Vertical Thomson scattering (raw data)

                        try

                            [~,TIMEBASES_ne_DATA{i},AREABASES_ne_DATA{i},SIGNALS_ne_DATA{i}] = load_aug_shotfile(...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SOURCE{i}, ...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHOT{i},...
                                'experiment',exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.EXPERIMENT{i},...
                                'edition',exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.VERSION{i},...
                                'signals',{'Ne_c','Ne_e','Z_core','Z_edge','R_core','R_edge'});

                            fprintf('AUG shotfile for TS electron density data correctly fetched\n');

                            READ_ne_DATA{i} = true;

                        catch

                            fprintf('TS electron density data from AUG (shot %d, shotfile %s, experiment %s, edition %d) requested but not found\n',...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHOT{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SOURCE{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.EXPERIMENT{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.VERSION{i});
                            fprintf('Try to set another shot/shotfile/experiment/edition for MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE within exp_data.json\n');

                            READ_ne_DATA{i} = false;

                        end

                    elseif strcmp(exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SOURCE{i},'IDA')

                        % Vertical Thomson scattering (from IDA shotfile)

                        try

                            [~,TIMEBASES_ne_DATA{i},AREABASES_ne_DATA{i},SIGNALS_ne_DATA{i}] = load_aug_shotfile(...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SOURCE{i}, ...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHOT{i},...
                                'experiment',exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.EXPERIMENT{i},...
                                'edition',exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.VERSION{i},...
                                'signals',{'Ntscprof','Ntseprof','tsdatcne','tsdatene'});

                            fprintf('AUG shotfile for TS electron density data correctly fetched\n');

                            READ_ne_DATA{i} = true;

                        catch

                            fprintf('TS electron density data from AUG (shot %d, shotfile %s, experiment %s, edition %d) requested but not found\n',...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHOT{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SOURCE{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.EXPERIMENT{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.VERSION{i});
                            fprintf('Try to set another shot/shotfile/experiment/edition for MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE within exp_data.json\n');

                            READ_ne_DATA{i} = false;

                        end

                    elseif strcmp(exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SOURCE{i},'ELM')

                        % ELM-synchronized data (custom .nc file)

                        try

                            SIGNALS_ne_DATA{i} = sprintf('%s/custom/ELM/%d.nc',...
                                SHOTFILES_BASEPATH_LOCAL,exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHOT{i});

                            if ~isfile(SIGNALS_ne_DATA{i})
                                error();
                            end

                            fprintf('NetCDF file for ELM-synchronized electron density data correctly fetched\n');

                            READ_ne_DATA{i} = true;

                        catch

                            fprintf('ELM-synchronized electron density data from AUG (shot %d) requested but not found\n',...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHOT{i});
                            fprintf('Check the path for the custom ELM shotfile\n');

                            READ_ne_DATA{i} = false;

                        end

                    end

                end

                % Electron temperature data

                for i = 1:length(exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SOURCE)

                    if strcmp(exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SOURCE{i},'VTA')

                        % Vertical Thomson scattering (raw data)

                        try

                            [~,TIMEBASES_Te_DATA{i},AREABASES_Te_DATA{i},SIGNALS_Te_DATA{i}] = load_aug_shotfile(...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SOURCE{i}, ...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHOT{i},...
                                'experiment',exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.EXPERIMENT{i},...
                                'edition',exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.VERSION{i},...
                                'signals',{'Te_c','Te_e','Z_core','Z_edge','R_core','R_edge'});

                            fprintf('AUG shotfile for TS electron temperature data correctly fetched\n');

                            READ_Te_DATA{i} = true;

                        catch

                            fprintf('TS electron temperature data from AUG (shot %d, shotfile %s, experiment %s, edition %d) requested but not found\n',...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHOT{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SOURCE{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.EXPERIMENT{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.VERSION{i});
                            fprintf('Try to set another shot/shotfile/experiment/edition for MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE within exp_data.json\n');

                            READ_Te_DATA{i} = false;

                        end

                    elseif strcmp(exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SOURCE{i},'IDA')

                        % Vertical Thomson scattering (from IDA shotfile)

                        try

                            [~,TIMEBASES_Te_DATA{i},AREABASES_Te_DATA{i},SIGNALS_Te_DATA{i}] = load_aug_shotfile(...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SOURCE{i}, ...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHOT{i},...
                                'experiment',exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.EXPERIMENT{i},...
                                'edition',exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.VERSION{i},...
                                'signals',{'Ntscprof','Ntseprof','tsdatcte','tsdatete'});

                            fprintf('AUG shotfile for TS electron temperature data correctly fetched\n');

                            READ_Te_DATA{i} = true;

                        catch

                            fprintf('TS electron temperature data from AUG (shot %d, shotfile %s, experiment %s, edition %d) requested but not found\n',...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHOT{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SOURCE{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.EXPERIMENT{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.VERSION{i});
                            fprintf('Try to set another shot/shotfile/experiment/edition for MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE within exp_data.json\n');

                            READ_Te_DATA{i} = false;

                        end

                    elseif strcmp(exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHOT{i},'ELM')

                        % ELM-synchronized data (custom .nc file)

                        try

                            SIGNALS_Te_DATA{i} = sprintf('%s/custom/ELM/%d.nc',...
                                SHOTFILES_BASEPATH_LOCAL,exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHOT{i});

                            if ~isfile(SIGNALS_Te_DATA{i})
                                error();
                            end

                            fprintf('NetCDF file for ELM-synchronized electron temperature data correctly fetched\n');

                            READ_Te_DATA{i} = true;

                        catch

                            fprintf('ELM-synchronized electron temperature data from AUG (shot %d) requested but not found\n',...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHOT{i});
                            fprintf('Check the path for the custom ELM shotfile\n');

                            READ_Te_DATA{i} = false;

                        end

                    end

                end

                % Ion temperature data

                for i = 1:length(exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SOURCE)

                    if strcmp(exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SOURCE{i},'CEZ')

                        % Charge-exchange recombination spectroscopy (core system)

                        try

                            [~,TIMEBASES_Ti_DATA{i},AREABASES_Ti_DATA{i},SIGNALS_Ti_DATA{i}] = load_aug_shotfile(...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SOURCE{i}, ...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHOT{i},...
                                'experiment',exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.EXPERIMENT{i},...
                                'edition',exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.VERSION{i},...
                                'signals',{'Ti_c'});

                            fprintf('AUG shotfile for CXRS core ion temperature data correctly fetched\n');

                            READ_Ti_DATA{i} = true;

                        catch

                            fprintf('CXRS core ion temperature data from AUG (shot %d, shotfile %s, experiment %s, edition %d) requested but not found\n',...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHOT{i},...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SOURCE{i},...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.EXPERIMENT{i},...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.VERSION{i});
                            fprintf('Try to set another shot/shotfile/experiment/edition for MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE within exp_data.json\n');

                            READ_Ti_DATA{i} = false;

                        end

                    elseif strcmp(exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SOURCE{i},'CMZ')

                        % Charge-exchange recombination spectroscopy (edge system)

                        try

                            [~,TIMEBASES_Ti_DATA{i},AREABASES_Ti_DATA{i},SIGNALS_Ti_DATA{i}] = load_aug_shotfile(...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SOURCE{i}, ...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHOT{i},...
                                'experiment',exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.EXPERIMENT{i},...
                                'edition',exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.VERSION{i},...
                                'signals',{'Ti_c'});

                            fprintf('AUG shotfile for CXRS edge ion temperature data correctly fetched\n');

                            READ_Ti_DATA{i} = true;

                        catch

                            fprintf('CXRS edge ion temperature data from AUG (shot %d, shotfile %s, experiment %s, edition %d) requested but not found\n',...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHOT{i},...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SOURCE{i},...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.EXPERIMENT{i},...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.VERSION{i});
                            fprintf('Try to set another shot/shotfile/experiment/edition for MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE within exp_data.json\n');

                            READ_Ti_DATA{i} = false;

                        end

                    elseif strcmp(exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SOURCE{i},'ELM')

                        % ELM-synchronized data (custom .nc file)

                        try

                            SIGNALS_Ti_DATA{i} = sprintf('%s/custom/ELM/%d.nc',...
                                SHOTFILES_BASEPATH_LOCAL,exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHOT{i});

                            if ~isfile(SIGNALS_Te_DATA{i})
                                error();
                            end

                            fprintf('NetCDF file for ELM-synchronized ion temperature data correctly fetched\n');

                            READ_Ti_DATA{i} = true;

                        catch

                            fprintf('ELM-synchronized ion temperature data from AUG (shot %d) requested but not found\n',...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHOT{i});
                            fprintf('Check the path for the custom ELM shotfile\n');

                            READ_Ti_DATA{i} = false;

                        end

                    end

                end

                % Load shotfiles containing diagnostic profiles

                % Electron density profiles

                for i = 1:length(exp_data.MIDPLANE.PROFILES.ELECTRON_DENSITY_MIDPLANE.SOURCE)

                    if strcmp(exp_data.MIDPLANE.PROFILES.ELECTRON_DENSITY_MIDPLANE.SOURCE{i},'IDA')

                        % Integrated data analysis

                        try

                            [~,TIMEBASES_ne_PROFILES{i},AREABASES_ne_PROFILES{i},SIGNALS_ne_PROFILES{i}] = load_aug_shotfile(...
                                exp_data.MIDPLANE.PROFILES.ELECTRON_DENSITY_MIDPLANE.SOURCE{i}, ...
                                exp_data.MIDPLANE.PROFILES.ELECTRON_DENSITY_MIDPLANE.SHOT{i},...
                                'experiment',exp_data.MIDPLANE.PROFILES.ELECTRON_DENSITY_MIDPLANE.EXPERIMENT{i},...
                                'edition',exp_data.MIDPLANE.PROFILES.ELECTRON_DENSITY_MIDPLANE.VERSION{i},...
                                'signals',{'ne','ne_unc'});

                            fprintf('AUG shotfile for IDA electron density profiles correctly fetched\n');

                            READ_ne_PROFILES{i} = true;

                        catch

                            fprintf('IDA electron density profiles from AUG (shot %d, shotfile %s, experiment %s, edition %d) requested but not found\n',...
                                exp_data.MIDPLANE.PROFILES.ELECTRON_DENSITY_MIDPLANE.SHOT{i},...
                                exp_data.MIDPLANE.PROFILES.ELECTRON_DENSITY_MIDPLANE.SOURCE{i},...
                                exp_data.MIDPLANE.PROFILES.ELECTRON_DENSITY_MIDPLANE.EXPERIMENT{i},...
                                exp_data.MIDPLANE.PROFILES.ELECTRON_DENSITY_MIDPLANE.VERSION{i});
                            fprintf('Try to set another shot/shotfile/experiment/edition for MIDPLANE.PROFILES.ELECTRON_DENSITY_MIDPLANE within exp_data.json\n');

                            READ_ne_PROFILES{i} = false;

                        end

                    end

                end

                % Electron temperature profiles

                for i = 1:length(exp_data.MIDPLANE.PROFILES.ELECTRON_TEMPERATURE_MIDPLANE.SOURCE)

                    if strcmp(exp_data.MIDPLANE.PROFILES.ELECTRON_TEMPERATURE_MIDPLANE.SOURCE{i},'IDA')

                        % Integrated data analysis

                        try

                            [~,TIMEBASES_Te_PROFILES{i},AREABASES_Te_PROFILES{i},SIGNALS_Te_PROFILES{i}] = load_aug_shotfile(...
                                exp_data.MIDPLANE.PROFILES.ELECTRON_TEMPERATURE_MIDPLANE.SOURCE{i}, ...
                                exp_data.MIDPLANE.PROFILES.ELECTRON_TEMPERATURE_MIDPLANE.SHOT{i},...
                                'experiment',exp_data.MIDPLANE.PROFILES.ELECTRON_TEMPERATURE_MIDPLANE.EXPERIMENT{i},...
                                'edition',exp_data.MIDPLANE.PROFILES.ELECTRON_TEMPERATURE_MIDPLANE.VERSION{i},...
                                'signals',{'Te','Te_unc'});

                            fprintf('AUG shotfile for IDA electron temperature profiles correctly fetched\n');

                            READ_Te_PROFILES{i} = true;

                        catch

                            fprintf('IDA electron temperature profiles from AUG (shot %d, shotfile %s, experiment %s, edition %d) requested but not found\n',...
                                exp_data.MIDPLANE.PROFILES.ELECTRON_TEMPERATURE_MIDPLANE.SHOT{i},...
                                exp_data.MIDPLANE.PROFILES.ELECTRON_TEMPERATURE_MIDPLANE.SOURCE{i},...
                                exp_data.MIDPLANE.PROFILES.ELECTRON_TEMPERATURE_MIDPLANE.EXPERIMENT{i},...
                                exp_data.MIDPLANE.PROFILES.ELECTRON_TEMPERATURE_MIDPLANE.VERSION{i});
                            fprintf('Try to set another shot/shotfile/experiment/edition for MIDPLANE.PROFILES.ELECTRON_TEMPERATURE_MIDPLANE within exp_data.json\n');

                            READ_Te_PROFILES{i} = false;

                        end

                    end

                end

                %% EXTRACT EXPERIMENTAL DATA FOR AUG

                % Extract diagnostic data

                % Electron density data

                for i = 1:length(exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SOURCE)

                    if READ_ne_DATA{i}

                        if strcmp(exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SOURCE{i},'LIN')

                            % Lithium beam emission spectroscopy

                            time_data_ne{i} = TIMEBASES_ne_DATA{i}.time.value;
                            values_data_ne{i} = SIGNALS_ne_DATA{i}.ne.value;
                            unit_data_ne{i} = SIGNALS_ne_DATA{i}.ne.unit;

                            fprintf('LiBES electron density data from AUG (shot %d, time window [%.2f,%.2f] s) correctly extracted\n',...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHOT{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.TIME_START{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.TIME_END{i});

                        elseif strcmp(exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SOURCE{i},'VTA') && strcmp(exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SIGNAL{i},'Ne_c')

                            % Core Thomson scattering (raw data)

                            time_data_ne{i} = TIMEBASES_ne_DATA{i}.TIM_CORE.value;
                            values_data_ne{i} = transpose(SIGNALS_ne_DATA{i}.Ne_c.value);
                            unit_data_ne{i} = SIGNALS_ne_DATA{i}.Ne_c.unit;

                            fprintf('Core TS electron density data from AUG (shot %d, time window [%.2f,%.2f] s) correctly extracted\n',...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHOT{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.TIME_START{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.TIME_END{i});

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

                            fprintf('Core TS electron density data from AUG (shot %d, time window [%.2f,%.2f] s) correctly extracted\n',...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHOT{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.TIME_START{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.TIME_END{i});

                        elseif strcmp(exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SOURCE{i},'VTA') && strcmp(exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SIGNAL{i},'Ne_e')

                            % Edge Thomson scattering (raw data)

                            time_data_ne{i} = TIMEBASES_ne_DATA{i}.TIM_EDGE.value;
                            values_data_ne{i} = transpose(SIGNALS_ne_DATA{i}.Ne_e.value);
                            unit_data_ne{i} = SIGNALS_ne_DATA{i}.Ne_e.unit;

                            fprintf('Edge TS electron density data from AUG (shot %d, time window [%.2f,%.2f] s) correctly extracted\n',...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHOT{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.TIME_START{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.TIME_END{i});

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

                            fprintf('Edge TS electron density data from AUG (shot %d, time window [%.2f,%.2f] s) correctly extracted\n',...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHOT{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.TIME_START{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.TIME_END{i});

                        elseif strcmp(exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SOURCE{i},'ELM')

                            % ELM-synchronized data (from custom .nc file)

                            time_data_ne{i} = ncread(SIGNALS_ne_DATA{i},'IDA/time');
                            values_data_ne{i} = ncread(SIGNALS_ne_DATA{i},'IDA/ne');
                            unit_data_ne{i} = 'm^-3';

                            fprintf('ELM-synchronized electron density data from AUG (shot %d, time window [%.2f,%.2f] s) correctly extracted\n',...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHOT{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.TIME_START{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.TIME_END{i});

                        end

                        measurements_midplane_experiment.ne_data{i}.name = exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.NAME_DISPLAY{i};
                        [measurements_midplane_experiment.ne_data{i}.times,measurements_midplane_experiment.ne_data{i}.values] = ...
                            extract_values('data',time_data_ne{i}, values_data_ne{i},...
                            exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.TIME_START{i},exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.TIME_END{i},...
                            exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.REDUCED_SET_TIME_DELTA{i});
                        measurements_midplane_experiment.ne_data{i}.unit = unit_data_ne{i};

                    end

                end

                % Electron temperature data

                for i = 1:length(exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SOURCE)

                    if READ_Te_DATA{i}

                        if strcmp(exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SOURCE{i},'VTA') && strcmp(exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SIGNAL{i},'Te_c')

                            % Core Thomson scattering (raw data)

                            time_data_Te{i} = TIMEBASES_Te_DATA{i}.TIM_CORE.value;
                            values_data_Te{i} = transpose(SIGNALS_Te_DATA{i}.Te_c.value);
                            unit_data_Te{i} = SIGNALS_Te_DATA{i}.Te_c.unit;

                            fprintf('Core TS electron temperature data from AUG (shot %d, time window [%.2f,%.2f] s) correctly extracted\n',...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHOT{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.TIME_START{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.TIME_END{i});

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

                            fprintf('Core TS electron temperature data from AUG (shot %d, time window [%.2f,%.2f] s) correctly extracted\n',...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHOT{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.TIME_START{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.TIME_END{i});

                        elseif strcmp(exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SOURCE{i},'VTA') && strcmp(exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SIGNAL{i},'Te_e')

                            % Edge Thomson scattering (raw data)

                            time_data_Te{i} = TIMEBASES_Te_DATA{i}.TIM_EDGE.value;
                            values_data_Te{i} = transpose(SIGNALS_Te_DATA{i}.Te_e.value);
                            unit_data_Te{i} = SIGNALS_Te_DATA{i}.Te_e.unit;

                            fprintf('Edge TS electron temperature data from AUG (shot %d, time window [%.2f,%.2f] s) correctly extracted\n',...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHOT{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.TIME_START{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.TIME_END{i});

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

                            fprintf('Edge TS electron temperature data from AUG (shot %d, time window [%.2f,%.2f] s) correctly extracted\n',...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHOT{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.TIME_START{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.TIME_END{i});

                        elseif strcmp(exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SOURCE{i},'ELM')

                            % ELM-synchronized data (from custom .nc file)

                            time_data_Te{i} = ncread(SIGNALS_Te_DATA{i},'IDA/time');
                            values_data_Te{i} = ncread(SIGNALS_Te_DATA{i},'IDA/Te');
                            unit_data_Te{i} = 'eV';

                            fprintf('ELM-synchronized electron temperature data from AUG (shot %d, time window [%.2f,%.2f] s) correctly extracted\n',...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHOT{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.TIME_START{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.TIME_END{i});

                        end

                        measurements_midplane_experiment.Te_data{i}.name = exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.NAME_DISPLAY{i};
                        [measurements_midplane_experiment.Te_data{i}.times,measurements_midplane_experiment.Te_data{i}.values] = ...
                            extract_values('data',time_data_Te{i}, values_data_Te{i},...
                            exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.TIME_START{i},exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.TIME_END{i},...
                            exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.REDUCED_SET_TIME_DELTA{i});
                        measurements_midplane_experiment.Te_data{i}.unit = unit_data_Te{i};

                    end

                end

                % Ion temperature data

                for i = 1:length(exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SOURCE)

                    if READ_Ti_DATA{i}

                        if strcmp(exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SOURCE{i},'CEZ')

                            % Core charge-exchange recombination spectroscopy

                            time_data_Ti{i} = TIMEBASES_Ti_DATA{i}.time.value;
                            values_data_Ti{i} = transpose(SIGNALS_Ti_DATA{i}.Ti_c.value);
                            unit_data_Ti{i} = SIGNALS_Ti_DATA{i}.Ti_c.unit;

                            measurements_midplane_experiment.Ti_data{i}.name = exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.NAME_DISPLAY{i};
                            [measurements_midplane_experiment.Ti_data{i}.times,measurements_midplane_experiment.Ti_data{i}.values] = ...
                                extract_values('data',time_data_Ti{i}, values_data_Ti{i},...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.TIME_START{i},exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.TIME_END{i},...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.REDUCED_SET_TIME_DELTA{i});
                            measurements_midplane_experiment.Ti_data{i}.unit = unit_data_Ti{i};

                            fprintf('Core CXRS ion temperature data from AUG (shot %d, time window [%.2f,%.2f] s) correctly extracted\n',...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHOT{i},...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.TIME_START{i},...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.TIME_END{i});

                        elseif strcmp(exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SOURCE{i},'CMZ')

                            % Edge charge-exchange recombination spectroscopy

                            time_data_Ti{i} = TIMEBASES_Ti_DATA{i}.time.value;
                            values_data_Ti{i} = transpose(SIGNALS_Ti_DATA{i}.Ti_c.value);
                            unit_data_Ti{i} = SIGNALS_Ti_DATA{i}.Ti_c.unit;

                            measurements_midplane_experiment.Ti_data{i}.name = exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.NAME_DISPLAY{i};
                            [measurements_midplane_experiment.Ti_data{i}.times,measurements_midplane_experiment.Ti_data{i}.values] = ...
                                extract_values('data',time_data_Ti{i}, values_data_Ti{i},...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.TIME_START{i},exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.TIME_END{i},...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.REDUCED_SET_TIME_DELTA{i});
                            measurements_midplane_experiment.Ti_data{i}.unit = unit_data_Ti{i};

                            fprintf('Edge CXRS ion temperature data from AUG (shot %d, time window [%.2f,%.2f] s) correctly extracted\n',...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHOT{i},...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.TIME_START{i},...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.TIME_END{i});

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

                            fprintf('ELM-synchronized ion temperature data from AUG (shot %d, time window [%.2f,%.2f] s) correctly extracted\n',...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHOT{i},...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.TIME_START{i},...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.TIME_END{i});

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

                            fprintf('ELM-synchronized ion temperature data from AUG (shot %d, time window [%.2f,%.2f] s) correctly extracted\n',...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHOT{i},...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.TIME_START{i},...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.TIME_END{i});

                        end

                    end

                end

                % Extract diagnostic profiles

                % Electron density profiles

                for i = 1:length(exp_data.MIDPLANE.PROFILES.ELECTRON_DENSITY_MIDPLANE.SOURCE)

                    if READ_ne_PROFILES{i}

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

                            fprintf('IDA electron density profiles from AUG (shot %d, time window [%.2f,%.2f] s) correctly extracted\n',...
                                exp_data.MIDPLANE.PROFILES.ELECTRON_DENSITY_MIDPLANE.SHOT{i},...
                                exp_data.MIDPLANE.PROFILES.ELECTRON_DENSITY_MIDPLANE.TIME_START{i},...
                                exp_data.MIDPLANE.PROFILES.ELECTRON_DENSITY_MIDPLANE.TIME_END{i});

                        end

                    end

                end

                % Electron temperature profiles

                for i = 1:length(exp_data.MIDPLANE.PROFILES.ELECTRON_TEMPERATURE_MIDPLANE.SOURCE)

                    if READ_Te_PROFILES{i}

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

                            fprintf('IDA electron temperature profiles from AUG (shot %d, time window [%.2f,%.2f] s) correctly extracted\n',...
                                exp_data.MIDPLANE.PROFILES.ELECTRON_TEMPERATURE_MIDPLANE.SHOT{i},...
                                exp_data.MIDPLANE.PROFILES.ELECTRON_TEMPERATURE_MIDPLANE.TIME_START{i},...
                                exp_data.MIDPLANE.PROFILES.ELECTRON_TEMPERATURE_MIDPLANE.TIME_END{i});

                        end

                    end

                end

                %% CALCULATE COORDINATES FOR AUG

                % Calculate coordinates for diagnostic data

                % Electron density profile

                for i = 1:length(exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SOURCE)

                    if READ_ne_DATA{i}

                        if strcmp(exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SOURCE{i},'LIN')

                            % Lithium beam emission spectroscopy

                            coordinate_shotfile = ...
                                extract_coordinates(time_data_ne{i},AREABASES_ne_DATA{i}.rhop.value,...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.TIME_START{i},exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.TIME_END{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.REDUCED_SET_TIME_DELTA{i});

                            [measurements_midplane_experiment.ne_data{i}.rhop,~] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_midplane_experiment.ne_data{i}.times,[],...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHOT{i},coordinate_shotfile,[],'rhop','rhop',...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_RHOP{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_DSSEP{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_R{i});

                            [measurements_midplane_experiment.ne_data{i}.dssep,~] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_midplane_experiment.ne_data{i}.times,[],...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHOT{i},coordinate_shotfile,[],'rhop','dssep',...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_RHOP{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_DSSEP{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_R{i});

                            [measurements_midplane_experiment.ne_data{i}.R,~] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_midplane_experiment.ne_data{i}.times,[],...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHOT{i},coordinate_shotfile,[],'rhop','R',...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_RHOP{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_DSSEP{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_R{i});

                            fprintf('Radial coordinates for LiBES electron density data correctly converted\n');

                        elseif strcmp(exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SOURCE{i},'VTA') && strcmp(exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SIGNAL{i},'Ne_c')

                            % Core Thomson scattering (raw data)

                            coordinate_shotfile = mean(SIGNALS_ne_DATA{i}.R_core.value)*ones(length(SIGNALS_ne_DATA{i}.Z_core.value),1);
                            z_coordinate_shotfile = SIGNALS_ne_DATA{i}.Z_core.value';

                            values_original = measurements_midplane_experiment.ne_data{i}.values;

                            [measurements_midplane_experiment.ne_data{i}.rhop,measurements_midplane_experiment.ne_data{i}.values] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_midplane_experiment.ne_data{i}.times,values_original,...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHOT{i},coordinate_shotfile,z_coordinate_shotfile,'R','rhop',...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_RHOP{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_DSSEP{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_R{i});

                            [measurements_midplane_experiment.ne_data{i}.dssep,~] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_midplane_experiment.ne_data{i}.times,values_original,...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHOT{i},coordinate_shotfile,z_coordinate_shotfile,'R','dssep',...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_RHOP{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_DSSEP{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_R{i});

                            [measurements_midplane_experiment.ne_data{i}.R,~] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_midplane_experiment.ne_data{i}.times,values_original,...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHOT{i},coordinate_shotfile,z_coordinate_shotfile,'R','R',...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_RHOP{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_DSSEP{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_R{i});

                            fprintf('Radial coordinates for Core TS electron density data correctly converted\n');

                        elseif strcmp(exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SOURCE{i},'IDA') && strcmp(exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SIGNAL{i},'tsdatcne')

                            % Core Thomson scattering (from IDA shotfile)

                            coordinate_shotfile = ...
                                extract_coordinates(time_data_ne{i},AREABASES_ne_DATA{i}.x_ts_co.value,...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.TIME_START{i},exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.TIME_END{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.REDUCED_SET_TIME_DELTA{i});

                            [measurements_midplane_experiment.ne_data{i}.rhop,~] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_midplane_experiment.ne_data{i}.times,[],...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHOT{i},coordinate_shotfile,[],'rhop','rhop',...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_RHOP{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_DSSEP{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_R{i});

                            [measurements_midplane_experiment.ne_data{i}.dssep,~] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_midplane_experiment.ne_data{i}.times,[],...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHOT{i},coordinate_shotfile,[],'rhop','dssep',...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_RHOP{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_DSSEP{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_R{i});

                            [measurements_midplane_experiment.ne_data{i}.R,~] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_midplane_experiment.ne_data{i}.times,[],...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHOT{i},coordinate_shotfile,[],'rhop','R',...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_RHOP{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_DSSEP{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_R{i});

                            fprintf('Radial coordinates for Core TS electron density data correctly converted\n');

                        elseif strcmp(exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SOURCE{i},'VTA') && strcmp(exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SIGNAL{i},'Ne_e')

                            % Edge Thomson scattering (raw data)

                            coordinate_shotfile = mean(SIGNALS_ne_DATA{i}.R_edge.value)*ones(length(SIGNALS_ne_DATA{i}.Z_edge.value),1);
                            z_coordinate_shotfile = SIGNALS_ne_DATA{i}.Z_edge.value';

                            values_original = measurements_midplane_experiment.ne_data{i}.values;

                            [measurements_midplane_experiment.ne_data{i}.rhop,measurements_midplane_experiment.ne_data{i}.values] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_midplane_experiment.ne_data{i}.times,values_original,...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHOT{i},coordinate_shotfile,z_coordinate_shotfile,'R','rhop',...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_RHOP{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_DSSEP{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_R{i});

                            [measurements_midplane_experiment.ne_data{i}.dssep,~] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_midplane_experiment.ne_data{i}.times,values_original,...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHOT{i},coordinate_shotfile,z_coordinate_shotfile,'R','dssep',...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_RHOP{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_DSSEP{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_R{i});

                            [measurements_midplane_experiment.ne_data{i}.R,~] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_midplane_experiment.ne_data{i}.times,values_original,...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHOT{i},coordinate_shotfile,z_coordinate_shotfile,'R','R',...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_RHOP{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_DSSEP{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_R{i});

                            fprintf('Radial coordinates for Edge TS electron density data correctly converted\n');

                        elseif strcmp(exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SOURCE{i},'IDA') && strcmp(exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SIGNAL{i},'tsdatene')

                            % Edge Thomson scattering (from IDA shotfile)

                            coordinate_shotfile = ...
                                extract_coordinates(time_data_ne{i},AREABASES_ne_DATA{i}.x_ts_ed.value,...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.TIME_START{i},exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.TIME_END{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.REDUCED_SET_TIME_DELTA{i});

                            [measurements_midplane_experiment.ne_data{i}.rhop,~] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_midplane_experiment.ne_data{i}.times,[],...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHOT{i},coordinate_shotfile,[],'rhop','rhop',...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_RHOP{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_DSSEP{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_R{i});

                            [measurements_midplane_experiment.ne_data{i}.dssep,~] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_midplane_experiment.ne_data{i}.times,[],...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHOT{i},coordinate_shotfile,[],'rhop','dssep',...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_RHOP{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_DSSEP{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_R{i});

                            [measurements_midplane_experiment.ne_data{i}.R,~] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_midplane_experiment.ne_data{i}.times,[],...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHOT{i},coordinate_shotfile,[],'rhop','R',...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_RHOP{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_DSSEP{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_R{i});

                             fprintf('Radial coordinates for Edge TS electron density data correctly converted\n');

                        elseif strcmp(exp_data.ELECTRON_DENSITY_DATA_MIDPLANE_SOURCES{i},'ELM')

                            % ELM-synchronized data (from custom .nc file)

                            coordinate_shotfile = ...
                                extract_coordinates(time_data_ne{i},ncread(SIGNALS_ne_DATA{i},'IDA/rho'),...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.TIME_START{i},exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.TIME_END{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.REDUCED_SET_TIME_DELTA{i});

                            [measurements_midplane_experiment.ne_data{i}.rhop,~] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_midplane_experiment.ne_data{i}.times,[],...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHOT{i},coordinate_shotfile,[],'rhop','rhop',...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_RHOP{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_DSSEP{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_R{i});

                            [measurements_midplane_experiment.ne_data{i}.dssep,~] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_midplane_experiment.ne_data{i}.times,[],...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHOT{i},coordinate_shotfile,[],'rhop','dssep',...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_RHOP{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_DSSEP{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_R{i});

                            [measurements_midplane_experiment.ne_data{i}.R,~] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_midplane_experiment.ne_data{i}.times,[],...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHOT{i},coordinate_shotfile,[],'rhop','R',...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_RHOP{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_DSSEP{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_DENSITY_MIDPLANE.SHIFT_R{i});

                            fprintf('Radial coordinates for ELM-synchronized electron density data correctly converted\n');

                        end

                    end

                end

                % Electron temperature data

                for i = 1:length(exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SOURCE)

                    if READ_Te_DATA{i}

                        if strcmp(exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SOURCE{i},'VTA') && strcmp(exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SIGNAL{i},'Te_c')

                            % Core Thomson scattering (raw data)

                            coordinate_shotfile = mean(SIGNALS_Te_DATA{i}.R_core.value)*ones(length(SIGNALS_Te_DATA{i}.Z_core.value),1);
                            z_coordinate_shotfile = SIGNALS_Te_DATA{i}.Z_core.value;

                            values_original = measurements_midplane_experiment.Te_data{i}.values;

                            [measurements_midplane_experiment.Te_data{i}.rhop,measurements_midplane_experiment.Te_data{i}.values] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_midplane_experiment.Te_data{i}.times,values_original,...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHOT{i},coordinate_shotfile,z_coordinate_shotfile,'R','rhop',...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_RHOP{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_DSSEP{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_R{i});

                            [measurements_midplane_experiment.Te_data{i}.dssep,~] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_midplane_experiment.Te_data{i}.times,values_original,...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHOT{i},coordinate_shotfile,z_coordinate_shotfile,'R','dssep',...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_RHOP{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_DSSEP{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_R{i});

                            [measurements_midplane_experiment.Te_data{i}.R,~] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_midplane_experiment.Te_data{i}.times,values_original,...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHOT{i},coordinate_shotfile,z_coordinate_shotfile,'R','R',...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_RHOP{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_DSSEP{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_R{i});

                            fprintf('Radial coordinates for Core TS electron temperature data correctly converted\n');

                        elseif strcmp(exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SOURCE{i},'IDA') && strcmp(exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SIGNAL{i},'tsdatcte')

                            % Core Thomson scattering (from IDA shotfile)

                            coordinate_shotfile = ...
                                extract_coordinates(time_data_Te{i},AREABASES_Te_DATA{i}.x_ts_co.value,...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.TIME_START{i},exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.TIME_END{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.REDUCED_SET_TIME_DELTA{i});

                            [measurements_midplane_experiment.Te_data{i}.rhop,~] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_midplane_experiment.Te_data{i}.times,[],...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHOT{i},coordinate_shotfile,[],'rhop','rhop',...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_RHOP{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_DSSEP{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_R{i});

                            [measurements_midplane_experiment.Te_data{i}.dssep,~] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_midplane_experiment.Te_data{i}.times,[],...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHOT{i},coordinate_shotfile,[],'rhop','dssep',...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_RHOP{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_DSSEP{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_R{i});

                            [measurements_midplane_experiment.Te_data{i}.R,~] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_midplane_experiment.Te_data{i}.times,[],...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHOT{i},coordinate_shotfile,[],'rhop','R',...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_RHOP{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_DSSEP{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_R{i});

                            fprintf('Radial coordinates for Core TS electron temperature data correctly converted\n');

                        elseif strcmp(exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SOURCE{i},'VTA') && strcmp(exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SIGNAL{i},'Te_e')

                            % Edge Thomson scattering (raw data)

                            coordinate_shotfile = mean(SIGNALS_Te_DATA{i}.R_edge.value)*ones(length(SIGNALS_Te_DATA{i}.Z_edge.value),1);
                            z_coordinate_shotfile = SIGNALS_Te_DATA{i}.Z_edge.value';

                            values_original = measurements_midplane_experiment.Te_data{i}.values;

                            [measurements_midplane_experiment.Te_data{i}.rhop,measurements_midplane_experiment.Te_data{i}.values] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_midplane_experiment.Te_data{i}.times,values_original,...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHOT{i},coordinate_shotfile,z_coordinate_shotfile,'R','rhop',...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_RHOP{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_DSSEP{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_R{i});

                            [measurements_midplane_experiment.Te_data{i}.dssep,~] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_midplane_experiment.Te_data{i}.times,values_original,...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHOT{i},coordinate_shotfile,z_coordinate_shotfile,'R','dssep',...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_RHOP{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_DSSEP{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_R{i});

                            [measurements_midplane_experiment.Te_data{i}.R,~] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_midplane_experiment.Te_data{i}.times,values_original,...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHOT{i},coordinate_shotfile,z_coordinate_shotfile,'R','R',...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_RHOP{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_DSSEP{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_R{i});

                            fprintf('Radial coordinates for Edge TS electron temperature data correctly converted\n');

                        elseif strcmp(exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SOURCE{i},'IDA') && strcmp(exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SIGNAL{i},'tsdatete')

                            % Edge Thomson scattering (from IDA shotfile)

                            coordinate_shotfile = ...
                                extract_coordinates(time_data_Te{i},AREABASES_Te_DATA{i}.x_ts_ed.value,...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.TIME_START{i},exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.TIME_END{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.REDUCED_SET_TIME_DELTA{i});

                            [measurements_midplane_experiment.Te_data{i}.rhop,~] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_midplane_experiment.Te_data{i}.times,[],...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHOT{i},coordinate_shotfile,[],'rhop','rhop',...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_RHOP{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_DSSEP{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_R{i});

                            [measurements_midplane_experiment.Te_data{i}.dssep,~] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_midplane_experiment.Te_data{i}.times,[],...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHOT{i},coordinate_shotfile,[],'rhop','dssep',...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_RHOP{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_DSSEP{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_R{i});

                            [measurements_midplane_experiment.Te_data{i}.R,~] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_midplane_experiment.Te_data{i}.times,[],...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHOT{i},coordinate_shotfile,[],'rhop','R',...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_RHOP{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_DSSEP{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_R{i});

                            fprintf('Radial coordinates for Edge TS electron temperature data correctly converted\n');

                        elseif strcmp(exp_data.ELECTRON_TEMPERATURE_DATA_MIDPLANE_SOURCES{i},'ELM')

                            % ELM-synchronized data (from custom .nc file)

                            coordinate_shotfile = ...
                                extract_coordinates(time_data_Te{i},ncread(SIGNALS_Te_DATA{i},'IDA/rho'),...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.TIME_START{i},exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.TIME_END{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.REDUCED_SET_TIME_DELTA{i});

                            [measurements_midplane_experiment.Te_data{i}.rhop,~] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_midplane_experiment.Te_data{i}.times,[],...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHOT{i},coordinate_shotfile,[],'rhop','rhop',...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_RHOP{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_DSSEP{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_R{i});

                            [measurements_midplane_experiment.Te_data{i}.dssep,~] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_midplane_experiment.Te_data{i}.times,[],...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHOT{i},coordinate_shotfile,[],'rhop','dssep',...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_RHOP{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_DSSEP{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_R{i});

                            [measurements_midplane_experiment.Te_data{i}.R,~] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_midplane_experiment.Te_data{i}.times,[],...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHOT{i},coordinate_shotfile,[],'rhop','R',...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_RHOP{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_DSSEP{i},...
                                exp_data.MIDPLANE.DATA.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_R{i});

                            fprintf('Radial coordinates for ELM-synchronized electron temperature data correctly converted\n');

                        end

                    end

                end

                % Ion temperature data

                for i = 1:length(exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SOURCE)

                    if READ_Ti_DATA{i}

                        if strcmp(exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SOURCE{i},'CEZ')

                            % Core and edge charge-exchange recombination spectroscopy

                            coordinate_shotfile = AREABASES_Ti_DATA{i}.R.value';
                            z_coordinate_shotfile = AREABASES_Ti_DATA{i}.z.value';

                            coordinate_shotfile = repmat(coordinate_shotfile,length(measurements_midplane_experiment.Ti_data{i}.times),1);
                            z_coordinate_shotfile = repmat(z_coordinate_shotfile,length(measurements_midplane_experiment.Ti_data{i}.times),1);

                            values_original = measurements_midplane_experiment.Ti_data{i}.values;

                            [measurements_midplane_experiment.Ti_data{i}.rhop,measurements_midplane_experiment.Ti_data{i}.values] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_midplane_experiment.Ti_data{i}.times,values_original,...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHOT{i},coordinate_shotfile,z_coordinate_shotfile,'R','rhop',...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHIFT_RHOP{i},...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHIFT_DSSEP{i},...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHIFT_R{i});

                            [measurements_midplane_experiment.Ti_data{i}.dssep,~] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_midplane_experiment.Ti_data{i}.times,values_original,...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHOT{i},coordinate_shotfile,z_coordinate_shotfile,'R','dssep',...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHIFT_RHOP{i},...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHIFT_DSSEP{i},...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHIFT_R{i});

                            [measurements_midplane_experiment.Ti_data{i}.R,~] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_midplane_experiment.Ti_data{i}.times,values_original,...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHOT{i},coordinate_shotfile,z_coordinate_shotfile,'R','R',...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHIFT_RHOP{i},...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHIFT_DSSEP{i},...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHIFT_R{i});

                            fprintf('Radial coordinates for Core CXRS ion temperature data correctly converted\n');
                        
                        elseif strcmp(exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SOURCE{i},'CMZ')

                            % Edge charge-exchange recombination spectroscopy

                            coordinate_shotfile = AREABASES_Ti_DATA{i}.R.value';
                            z_coordinate_shotfile = AREABASES_Ti_DATA{i}.z.value';

                            coordinate_shotfile = repmat(coordinate_shotfile,length(measurements_midplane_experiment.Ti_data{i}.times),1);
                            z_coordinate_shotfile = repmat(z_coordinate_shotfile,length(measurements_midplane_experiment.Ti_data{i}.times),1);

                            values_original = measurements_midplane_experiment.Ti_data{i}.values;

                            [measurements_midplane_experiment.Ti_data{i}.rhop,measurements_midplane_experiment.Ti_data{i}.values] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_midplane_experiment.Ti_data{i}.times,values_original,...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHOT{i},coordinate_shotfile,z_coordinate_shotfile,'R','rhop',...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHIFT_RHOP{i},...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHIFT_DSSEP{i},...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHIFT_R{i});

                            [measurements_midplane_experiment.Ti_data{i}.dssep,~] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_midplane_experiment.Ti_data{i}.times,values_original,...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHOT{i},coordinate_shotfile,z_coordinate_shotfile,'R','dssep',...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHIFT_RHOP{i},...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHIFT_DSSEP{i},...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHIFT_R{i});

                            [measurements_midplane_experiment.Ti_data{i}.R,~] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_midplane_experiment.Ti_data{i}.times,values_original,...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHOT{i},coordinate_shotfile,z_coordinate_shotfile,'R','R',...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHIFT_RHOP{i},...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHIFT_DSSEP{i},...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHIFT_R{i});

                            fprintf('Radial coordinates for Edge CXRS ion temperature data correctly converted\n');

                        elseif strcmp(exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SOURCE{i},'ELM') && strcmp(exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SIGNAL{i},'Ti_CMZ')

                            % ELM-synchronized data (CMZ, from custom .nc file)

                            coordinate_shotfile = ...
                                extract_coordinates(time_data_Ti{i},ncread(SIGNALS_Ti_DATA{i},'CMZ/rho'),...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.TIME_START{i},exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.TIME_END{i},...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.REDUCED_SET_TIME_DELTA{i});

                            [measurements_midplane_experiment.Ti_data{i}.rhop,~] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_midplane_experiment.Ti_data{i}.times,[],...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHOT{i},coordinate_shotfile,[],'rhop','rhop',...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHIFT_RHOP{i},...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHIFT_DSSEP{i},...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHIFT_R{i});

                            [measurements_midplane_experiment.Ti_data{i}.dssep,~] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_midplane_experiment.Ti_data{i}.times,[],...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHOT{i},coordinate_shotfile,[],'rhop','dssep',...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHIFT_RHOP{i},...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHIFT_DSSEP{i},...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHIFT_R{i});

                            [measurements_midplane_experiment.Ti_data{i}.R,~] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_midplane_experiment.Ti_data{i}.times,[],...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHOT{i},coordinate_shotfile,[],'rhop','R',...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHIFT_RHOP{i},...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHIFT_DSSEP{i},...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHIFT_R{i});

                            fprintf('Radial coordinates for ELM-synchronized ion temperature data correctly converted\n');

                        elseif strcmp(exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SOURCE{i},'ELM') && strcmp(exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SIGNAL{i},'Ti_CPZ')

                            % ELM-synchronized data (CPZ, from custom .nc file)

                            coordinate_shotfile = ...
                                extract_coordinates(time_data_Ti{i},ncread(SIGNALS_Ti_DATA{i},'CPZ/rho'),...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.TIME_START{i},exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.TIME_END{i},...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.REDUCED_SET_TIME_DELTA{i});

                            [measurements_midplane_experiment.Ti_data{i}.rhop,~] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_midplane_experiment.Ti_data{i}.times,[],...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHOT{i},coordinate_shotfile,[],'rhop','rhop',...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHIFT_RHOP{i},...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHIFT_DSSEP{i},...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHIFT_R{i});

                            [measurements_midplane_experiment.Ti_data{i}.dssep,~] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_midplane_experiment.Ti_data{i}.times,[],...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHOT{i},coordinate_shotfile,[],'rhop','dssep',...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHIFT_RHOP{i},...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHIFT_DSSEP{i},...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHIFT_R{i});

                            [measurements_midplane_experiment.Ti_data{i}.R,~] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_midplane_experiment.Ti_data{i}.times,[],...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHOT{i},coordinate_shotfile,[],'rhop','R',...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHIFT_RHOP{i},...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHIFT_DSSEP{i},...
                                exp_data.MIDPLANE.DATA.ION_TEMPERATURE_MIDPLANE.SHIFT_R{i});

                            fprintf('Radial coordinates for ELM-synchronized ion temperature data correctly converted\n');

                        end

                    end

                end

                % Calculate coordinates for diagnostic profiles

                % Electron density profiles

                for i = 1:length(exp_data.MIDPLANE.PROFILES.ELECTRON_DENSITY_MIDPLANE.SOURCE)

                    if READ_ne_PROFILES{i}

                        if strcmp(exp_data.MIDPLANE.PROFILES.ELECTRON_DENSITY_MIDPLANE.SOURCE{i},'IDA')

                            % Integrated data analysis

                            coordinate_shotfile = mean(AREABASES_ne_PROFILES{i}.rhop.value,2);

                            [measurements_midplane_experiment.ne_profile{i}.rhop,~] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_midplane_experiment.ne_profile{i}.times,[],...
                                exp_data.MIDPLANE.PROFILES.ELECTRON_DENSITY_MIDPLANE.SHOT{i},coordinate_shotfile',[],'rhop','rhop',...
                                exp_data.MIDPLANE.PROFILES.ELECTRON_DENSITY_MIDPLANE.SHIFT_RHOP{i},...
                                exp_data.MIDPLANE.PROFILES.ELECTRON_DENSITY_MIDPLANE.SHIFT_DSSEP{i},...
                                exp_data.MIDPLANE.PROFILES.ELECTRON_DENSITY_MIDPLANE.SHIFT_R{i});

                            [measurements_midplane_experiment.ne_profile{i}.dssep,~] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_midplane_experiment.ne_profile{i}.times,[],...
                                exp_data.MIDPLANE.PROFILES.ELECTRON_DENSITY_MIDPLANE.SHOT{i},coordinate_shotfile',[],'rhop','dssep',...
                                exp_data.MIDPLANE.PROFILES.ELECTRON_DENSITY_MIDPLANE.SHIFT_RHOP{i},...
                                exp_data.MIDPLANE.PROFILES.ELECTRON_DENSITY_MIDPLANE.SHIFT_DSSEP{i},...
                                exp_data.MIDPLANE.PROFILES.ELECTRON_DENSITY_MIDPLANE.SHIFT_R{i});

                            [measurements_midplane_experiment.ne_profile{i}.R,~] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_midplane_experiment.ne_profile{i}.times,[],...
                                exp_data.MIDPLANE.PROFILES.ELECTRON_DENSITY_MIDPLANE.SHOT{i},coordinate_shotfile',[],'rhop','R',...
                                exp_data.MIDPLANE.PROFILES.ELECTRON_DENSITY_MIDPLANE.SHIFT_RHOP{i},...
                                exp_data.MIDPLANE.PROFILES.ELECTRON_DENSITY_MIDPLANE.SHIFT_DSSEP{i},...
                                exp_data.MIDPLANE.PROFILES.ELECTRON_DENSITY_MIDPLANE.SHIFT_R{i});

                            fprintf('Radial coordinates for IDA electron density profiles correctly converted\n');

                        end

                    end

                end

                % Electron temperature profiles

                for i = 1:length(exp_data.MIDPLANE.PROFILES.ELECTRON_TEMPERATURE_MIDPLANE.SOURCE)

                    if READ_Te_PROFILES{i}

                        if strcmp(exp_data.MIDPLANE.PROFILES.ELECTRON_TEMPERATURE_MIDPLANE.SOURCE{i},'IDA')

                            % Integrated data analysis

                            coordinate_shotfile = mean(AREABASES_Te_PROFILES{i}.rhop.value,2);

                            [measurements_midplane_experiment.Te_profile{i}.rhop,~] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_midplane_experiment.Te_profile{i}.times,[],...
                                exp_data.MIDPLANE.PROFILES.ELECTRON_TEMPERATURE_MIDPLANE.SHOT{i},coordinate_shotfile',[],'rhop','rhop',...
                                exp_data.MIDPLANE.PROFILES.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_RHOP{i},...
                                exp_data.MIDPLANE.PROFILES.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_DSSEP{i},...
                                exp_data.MIDPLANE.PROFILES.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_R{i});

                            [measurements_midplane_experiment.Te_profile{i}.dssep,~] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_midplane_experiment.Te_profile{i}.times,[],...
                                exp_data.MIDPLANE.PROFILES.ELECTRON_TEMPERATURE_MIDPLANE.SHOT{i},coordinate_shotfile',[],'rhop','dssep',...
                                exp_data.MIDPLANE.PROFILES.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_RHOP{i},...
                                exp_data.MIDPLANE.PROFILES.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_DSSEP{i},...
                                exp_data.MIDPLANE.PROFILES.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_R{i});

                            [measurements_midplane_experiment.Te_profile{i}.R,~] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_midplane_experiment.Te_profile{i}.times,[],...
                                exp_data.MIDPLANE.PROFILES.ELECTRON_TEMPERATURE_MIDPLANE.SHOT{i},coordinate_shotfile',[],'rhop','R',...
                                exp_data.MIDPLANE.PROFILES.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_RHOP{i},...
                                exp_data.MIDPLANE.PROFILES.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_DSSEP{i},...
                                exp_data.MIDPLANE.PROFILES.ELECTRON_TEMPERATURE_MIDPLANE.SHIFT_R{i});

                            fprintf('Radial coordinates for IDA electron temperature profiles correctly converted\n');

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

%% SAVE ALL EXTRACTED EXPERIMENTAL DATA AS A .MAT FILE TO THE RUN DIRECTORY

        if isfile(mat_file_name)

            measurements_midplane_experiment_file(mat_file_name_old_editions+1).edition = mat_file_name_old_editions + 1;
            measurements_midplane_experiment_file(mat_file_name_old_editions+1).exp_data_namelist = exp_data;
            measurements_midplane_experiment_file(mat_file_name_old_editions+1).exp_data_measurements = measurements_midplane_experiment;
            save(mat_file_name,'measurements_midplane_experiment_file');
            fprintf('Requested midplane experimental data saved in exp_data_midplane.mat, version %d, for future usage\n',mat_file_name_old_editions+1);

        else
    
            measurements_midplane_experiment_file = struct;
            measurements_midplane_experiment_file(1).edition = 1;
            measurements_midplane_experiment_file(1).exp_data_namelist = exp_data;
            measurements_midplane_experiment_file(1).exp_data_measurements = measurements_midplane_experiment;
            save(mat_file_name,'measurements_midplane_experiment_file');
            fprintf('Requested midplane experimental data saved in exp_data_midplane.mat, version 1, for future usage\n');

        end

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

function [coordinate_output,data_output] = shift_convert_coordinate(device,times,data_values,shot,coordinate_input,z_coordinate_input,type_input,type_output,rhop_shift,dssep_shift,R_shift)

data_output = [];

if strcmp(type_input,type_output)

   switch type_output

       case 'rhop'

            if not(isempty(data_values))
                temp = find(data_values(1,:)==0, 1, 'first');
                if not(isempty(temp))
                    data_values(:,temp:end) = [];
                    coordinate_input(:,temp:end) = [];
                end
                data_output = data_values;
            end

            if not(isempty(rhop_shift))
                coordinate_output = coordinate_input + rhop_shift;
            else
                coordinate_output = coordinate_input;
            end

       case 'dssep'

            if not(isempty(dssep_shift))
                coordinate_output = coordinate_input + dssep_shift;
            else
                coordinate_output = coordinate_input;
            end

       case 'R'
            
            if not(isempty(data_values))
                temp = find(data_values(1,:)==0, 1, 'first');
                if not(isempty(temp))
                    data_values(:,temp:end) = [];
                    coordinate_input(:,temp:end) = [];
                end
                data_output = data_values;
            end

            if not(isempty(R_shift))
                coordinate_output = coordinate_input + R_shift;
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
                coordinate_input = coordinate_input + rhop_shift;
            end

            switch type_output

                case 'dssep'

                    coordinate_output = rhop_to_dssep(device,coordinate_input,times,shot);
                    if not(isempty(dssep_shift))
                        coordinate_output = coordinate_output + dssep_shift;
                    end

                case 'R'

                    coordinate_output = rhop_to_Rz(device,coordinate_input,times,shot);
                    if not(isempty(R_shift))
                        coordinate_output = coordinate_output + R_shift;
                    end

            end

       case 'dssep'

            if not(isempty(dssep_shift))
                coordinate_input = coordinate_input + dssep_shift;
            end

            switch type_output

                case 'rhop'

                    coordinate_output = dssep_to_rhop(device,coordinate_input,times,shot);
                    if not(isempty(rhop_shift))
                        coordinate_output = coordinate_output + rhop_shift;
                    end

                case 'R'

                    coordinate_output = dssep_to_Rz(device,coordinate_input,times,shot);
                    if not(isempty(R_shift))
                        coordinate_output = coordinate_output + R_shift;
                    end

            end

       case 'R'

            if not(isempty(R_shift))
                coordinate_input = coordinate_input + R_shift;
            end

            switch type_output

                case 'rhop'

                    [coordinate_output,data_output] = Rz_to_rhop(device,coordinate_input,z_coordinate_input,data_values,times,shot);
                    if not(isempty(rhop_shift))
                        coordinate_output = coordinate_output + rhop_shift;
                    end

                case 'dssep'

                    [coordinate_output,data_output] = Rz_to_dssep(device,coordinate_input,z_coordinate_input,data_values,times,shot);
                    if not(isempty(dssep_shift))
                        coordinate_output = coordinate_output + dssep_shift;
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
            
            equ = EQU(shot, 'diag', 'EQH',  'tbeg', time(1), 'tend', time(end));
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

            equ = EQU(shot, 'diag', 'EQH',  'tbeg', time(1), 'tend', time(end));
            
            for i = 1:length(time)
                [R_sep(i), z] = equ.rhoTheta2rz(1, 0, 't_in', time(i), 'coord_in', 'rho_pol');
            end

            dssep_output = (R - R_sep');
    
    end

end

function R_output = rhop_to_Rz(device,rhop,time,shot)

    switch device
    
        case 'AUG'
        
            equ = EQU(shot, 'diag', 'EQH',  'tbeg', time(1), 'tend', time(end));
            
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
        
            equ = EQU(shot, 'diag', 'EQH',  'tbeg', time(1), 'tend', time(end));

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
