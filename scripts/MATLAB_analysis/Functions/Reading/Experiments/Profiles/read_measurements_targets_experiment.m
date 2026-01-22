function [measurements_targets_experiment,exp_data_avail] = read_measurements_targets_experiment(simulation)

% read_measurements_targets_experiment reads the experimental inner and outer target plasma and flux measurements,
% namely electron density, electron temperature, particle flux density and energy flux density

%% READ EXPERIMENTAL DATA FROM RUN DIRECTORY

try
    exp_data = read_exp_data_json(simulation);
    exp_data_avail = true;
catch
    exp_data_avail = false;
end

measurements_targets_experiment = struct();
measurements_targets_experiment.lower_inner = struct();
measurements_targets_experiment.lower_outer = struct();
measurements_targets_experiment.upper_inner = struct();
measurements_targets_experiment.upper_outer = struct();

if exp_data_avail

    % Check if the same requested experimental data were already stored in
    % a .mat file in the run directory from a previous call of this function

    mat_file_name = sprintf('%s/exp_data_targets.mat',simulation.RUN_DIRECTORY);
    old_store_data_found = false;

    if isfile(mat_file_name)

        % Check if, within exp_data_targets.mat, there is already a stored
        % version of the experimental data identical to the one requested now

        load(mat_file_name);
        mat_file_name_old_editions = length(measurements_targets_experiment_file);

        i = 1;
        while i <= mat_file_name_old_editions
            [structs_equal, diffReport] = compare_structures(exp_data, measurements_targets_experiment_file(i).exp_data_namelist);
            if structs_equal
                old_store_data_found = true;
                measurements_targets_experiment = ...
                    measurements_targets_experiment_file(i).exp_data_measurements;
                fprintf('Requested targets experimental data found in exp_data_targets.mat, version %d\n',i);
                break;
            end
            i = i + 1;
        end

    end

    if not(old_store_data_found)

        fprintf('Requested targets experimental data not stored in any edition of exp_data_targets.mat: fetching them now\n');

        switch exp_data.DEVICE

            case 'AUG'

                %% CHECK THAT THE AUG LIBRARY LOCALLY EXISTS

                if ~isfolder(sprintf('%s/scripts.local/MATLAB_analysis_AUG',simulation.SOLPSTOP))
                    error(sprintf('Error: MATLAB library for reading AUG experimental data does not exist locally. Get it running the command ''clone_matlab_exp_libraries AUG'''));
                end
                addpath(genpath(sprintf('%s/scripts.local/MATLAB_analysis_AUG',simulation.SOLPSTOP)));

                %% LOAD EXPERIMENTAL DATA FOR AUG

                % INNER TARGET

                % Electron density data

                for i = 1:length(exp_data.TARGETS.LOWER_INNER.ELECTRON_DENSITY.SOURCE)

                    if strcmp(exp_data.TARGETS.LOWER_INNER.ELECTRON_DENSITY.SOURCE{i},'LSD')

                        % Langmuir probes

                        try

                            [PARAMETERS_ne_DATA{i},TIMEBASES_ne_DATA{i},~,SIGNALS_ne_DATA{i}] = load_aug_shotfile(...
                                exp_data.TARGETS.LOWER_INNER.ELECTRON_DENSITY.SOURCE{i}, ...
                                exp_data.TARGETS.LOWER_INNER.ELECTRON_DENSITY.SHOT{i},...
                                'experiment',exp_data.TARGETS.LOWER_INNER.ELECTRON_DENSITY.EXPERIMENT{i},...
                                'edition',exp_data.TARGETS.LOWER_INNER.ELECTRON_DENSITY.VERSION{i});

                            fprintf('AUG shotfile for inner target Langmuir probes electron density data correctly fetched\n');

                            READ_ne_DATA{i} = true;

                        catch

                            fprintf('Langmuir probes inner target electron density data from AUG (shot %d, shotfile %s, experiment %s, edition %d) requested but not found\n',...
                                exp_data.TARGETS.LOWER_INNER.ELECTRON_DENSITY.SHOT{i},...
                                exp_data.TARGETS.LOWER_INNER.ELECTRON_DENSITY.SOURCE{i},...
                                exp_data.TARGETS.LOWER_INNER.ELECTRON_DENSITY.EXPERIMENT{i},...
                                exp_data.TARGETS.LOWER_INNER.ELECTRON_DENSITY.VERSION{i});
                            fprintf('Try to set another shot/shotfile/experiment/edition for TARGETS.LOWER_INNER.ELECTRON_DENSITY within exp_data.json\n');

                            READ_ne_DATA{i} = false;

                        end

                    end

                end

                % Electron temperature data

                for i = 1:length(exp_data.TARGETS.LOWER_INNER.ELECTRON_TEMPERATURE.SOURCE)

                    if strcmp(exp_data.TARGETS.LOWER_INNER.ELECTRON_TEMPERATURE.SOURCE{i},'LSD')

                        % Langmuir probes

                        try

                            [PARAMETERS_Te_DATA{i},TIMEBASES_Te_DATA{i},~,SIGNALS_Te_DATA{i}] = load_aug_shotfile(...
                                exp_data.TARGETS.LOWER_INNER.ELECTRON_TEMPERATURE.SOURCE{i}, ...
                                exp_data.TARGETS.LOWER_INNER.ELECTRON_TEMPERATURE.SHOT{i},...
                                'experiment',exp_data.TARGETS.LOWER_INNER.ELECTRON_TEMPERATURE.EXPERIMENT{i},...
                                'edition',exp_data.TARGETS.LOWER_INNER.ELECTRON_TEMPERATURE.VERSION{i});

                            fprintf('AUG shotfile for inner target Langmuir probes electron temperature data correctly fetched\n');

                            READ_Te_DATA{i} = true;

                        catch

                            fprintf('Langmuir probes inner target electron temperature data from AUG (shot %d, shotfile %s, experiment %s, edition %d) requested but not found\n',...
                                exp_data.TARGETS.LOWER_INNER.ELECTRON_TEMPERATURE.SHOT{i},...
                                exp_data.TARGETS.LOWER_INNER.ELECTRON_TEMPERATURE.SOURCE{i},...
                                exp_data.TARGETS.LOWER_INNER.ELECTRON_TEMPERATURE.EXPERIMENT{i},...
                                exp_data.TARGETS.LOWER_INNER.ELECTRON_TEMPERATURE.VERSION{i});
                            fprintf('Try to set another shot/shotfile/experiment/edition for TARGETS.LOWER_INNER.ELECTRON_TEMPERATURE within exp_data.json\n');

                            READ_Te_DATA{i} = false;

                        end

                    end

                end

                % Particle flux density

                for i = 1:length(exp_data.TARGETS.LOWER_INNER.PARTICLE_FLUX_DENSITY.SOURCE)

                    if strcmp(exp_data.TARGETS.LOWER_INNER.PARTICLE_FLUX_DENSITY.SOURCE{i},'LSD')

                        % Langmuir probes

                        try

                            [PARAMETERS_gamma_DATA{i},TIMEBASES_gamma_DATA{i},~,SIGNALS_gamma_DATA{i}] = load_aug_shotfile(...
                                exp_data.TARGETS.LOWER_INNER.PARTICLE_FLUX_DENSITY.SOURCE{i}, ...
                                exp_data.TARGETS.LOWER_INNER.PARTICLE_FLUX_DENSITY.SHOT{i},...
                                'experiment',exp_data.TARGETS.LOWER_INNER.PARTICLE_FLUX_DENSITY.EXPERIMENT{i},...
                                'edition',exp_data.TARGETS.LOWER_INNER.PARTICLE_FLUX_DENSITY.VERSION{i});

                            fprintf('AUG shotfile for inner target Langmuir probes particle flux density data correctly fetched\n');

                            READ_gamma_DATA{i} = true;

                        catch

                            fprintf('Langmuir probes inner target particle flux density data from AUG (shot %d, shotfile %s, experiment %s, edition %d) requested but not found\n',...
                                exp_data.TARGETS.LOWER_INNER.PARTICLE_FLUX_DENSITY.SHOT{i},...
                                exp_data.TARGETS.LOWER_INNER.PARTICLE_FLUX_DENSITY.SOURCE{i},...
                                exp_data.TARGETS.LOWER_INNER.PARTICLE_FLUX_DENSITY.EXPERIMENT{i},...
                                exp_data.TARGETS.LOWER_INNER.PARTICLE_FLUX_DENSITY.VERSION{i});
                            fprintf('Try to set another shot/shotfile/experiment/edition for TARGETS.LOWER_INNER.PARTICLE_FLUX_DENSITY within exp_data.json\n');

                            READ_gamma_DATA{i} = false;

                        end

                    end

                end

                % Energy flux density

                for i = 1:length(exp_data.TARGETS.LOWER_INNER.ENERGY_FLUX_DENSITY.SOURCE)

                    if strcmp(exp_data.TARGETS.LOWER_INNER.ENERGY_FLUX_DENSITY.SOURCE{i},'LSD')

                        % Langmuir probes

                        try

                            [PARAMETERS_q_DATA{i},TIMEBASES_q_DATA{i},~,SIGNALS_q_DATA{i}] = load_aug_shotfile(...
                                exp_data.TARGETS.LOWER_INNER.ENERGY_FLUX_DENSITY.SOURCE{i}, ...
                                exp_data.TARGETS.LOWER_INNER.ENERGY_FLUX_DENSITY.SHOT{i},...
                                'experiment',exp_data.TARGETS.LOWER_INNER.ENERGY_FLUX_DENSITY.EXPERIMENT{i},...
                                'edition',exp_data.TARGETS.LOWER_INNER.ENERGY_FLUX_DENSITY.VERSION{i});

                            fprintf('AUG shotfile for inner target Langmuir probes energy flux density data correctly fetched\n');

                            READ_q_DATA{i} = true;

                        catch

                            fprintf('Langmuir probes inner target energy flux density data from AUG (shot %d, shotfile %s, experiment %s, edition %d) requested but not found\n',...
                                exp_data.TARGETS.LOWER_INNER.ENERGY_FLUX_DENSITY.SHOT{i},...
                                exp_data.TARGETS.LOWER_INNER.ENERGY_FLUX_DENSITY.SOURCE{i},...
                                exp_data.TARGETS.LOWER_INNER.ENERGY_FLUX_DENSITY.EXPERIMENT{i},...
                                exp_data.TARGETS.LOWER_INNER.ENERGY_FLUX_DENSITY.VERSION{i});
                            fprintf('Try to set another shot/shotfile/experiment/edition for TARGETS.LOWER_INNER.ENERGY_FLUX_DENSITY within exp_data.json\n');

                            READ_q_DATA{i} = false;

                        end

                    end

                end

                % OUTER TARGET

                % Electron density data

                for i = 1:length(exp_data.TARGETS.LOWER_OUTER.ELECTRON_DENSITY.SOURCE)

                    if strcmp(exp_data.TARGETS.LOWER_OUTER.ELECTRON_DENSITY.SOURCE{i},'LSD')

                        % Langmuir probes

                        try

                            [PARAMETERS_ne_DATA{i},TIMEBASES_ne_DATA{i},~,SIGNALS_ne_DATA{i}] = load_aug_shotfile(...
                                exp_data.TARGETS.LOWER_OUTER.ELECTRON_DENSITY.SOURCE{i}, ...
                                exp_data.TARGETS.LOWER_OUTER.ELECTRON_DENSITY.SHOT{i},...
                                'experiment',exp_data.TARGETS.LOWER_OUTER.ELECTRON_DENSITY.EXPERIMENT{i},...
                                'edition',exp_data.TARGETS.LOWER_OUTER.ELECTRON_DENSITY.VERSION{i});

                            fprintf('AUG shotfile for outer target Langmuir probes electron density data correctly fetched\n');

                            READ_ne_DATA{i} = true;

                        catch

                            fprintf('Langmuir probes outer target electron density data from AUG (shot %d, shotfile %s, experiment %s, edition %d) requested but not found\n',...
                                exp_data.TARGETS.LOWER_OUTER.ELECTRON_DENSITY.SHOT{i},...
                                exp_data.TARGETS.LOWER_OUTER.ELECTRON_DENSITY.SOURCE{i},...
                                exp_data.TARGETS.LOWER_OUTER.ELECTRON_DENSITY.EXPERIMENT{i},...
                                exp_data.TARGETS.LOWER_OUTER.ELECTRON_DENSITY.VERSION{i});
                            fprintf('Try to set another shot/shotfile/experiment/edition for TARGETS.LOWER_OUTER.ELECTRON_DENSITY within exp_data.json\n');

                            READ_ne_DATA{i} = false;

                        end

                    end

                end

                % Electron temperature data

                for i = 1:length(exp_data.TARGETS.LOWER_OUTER.ELECTRON_TEMPERATURE.SOURCE)

                    if strcmp(exp_data.TARGETS.LOWER_OUTER.ELECTRON_TEMPERATURE.SOURCE{i},'LSD')

                        % Langmuir probes

                        try

                            [PARAMETERS_Te_DATA{i},TIMEBASES_Te_DATA{i},~,SIGNALS_Te_DATA{i}] = load_aug_shotfile(...
                                exp_data.TARGETS.LOWER_OUTER.ELECTRON_TEMPERATURE.SOURCE{i}, ...
                                exp_data.TARGETS.LOWER_OUTER.ELECTRON_TEMPERATURE.SHOT{i},...
                                'experiment',exp_data.TARGETS.LOWER_OUTER.ELECTRON_TEMPERATURE.EXPERIMENT{i},...
                                'edition',exp_data.TARGETS.LOWER_OUTER.ELECTRON_TEMPERATURE.VERSION{i});

                            fprintf('AUG shotfile for outer target Langmuir probes electron temperature data correctly fetched\n');

                            READ_Te_DATA{i} = true;

                        catch

                            fprintf('Langmuir probes outer target electron temperature data from AUG (shot %d, shotfile %s, experiment %s, edition %d) requested but not found\n',...
                                exp_data.TARGETS.LOWER_OUTER.ELECTRON_TEMPERATURE.SHOT{i},...
                                exp_data.TARGETS.LOWER_OUTER.ELECTRON_TEMPERATURE.SOURCE{i},...
                                exp_data.TARGETS.LOWER_OUTER.ELECTRON_TEMPERATURE.EXPERIMENT{i},...
                                exp_data.TARGETS.LOWER_OUTER.ELECTRON_TEMPERATURE.VERSION{i});
                            fprintf('Try to set another shot/shotfile/experiment/edition for TARGETS.LOWER_OUTER.ELECTRON_TEMPERATURE within exp_data.json\n');

                            READ_Te_DATA{i} = false;

                        end

                    end

                end

                % Particle flux density

                for i = 1:length(exp_data.TARGETS.LOWER_OUTER.PARTICLE_FLUX_DENSITY.SOURCE)

                    if strcmp(exp_data.TARGETS.LOWER_OUTER.PARTICLE_FLUX_DENSITY.SOURCE{i},'LSD')

                        % Langmuir probes

                        try

                            [PARAMETERS_gamma_DATA{i},TIMEBASES_gamma_DATA{i},~,SIGNALS_gamma_DATA{i}] = load_aug_shotfile(...
                                exp_data.TARGETS.LOWER_OUTER.PARTICLE_FLUX_DENSITY.SOURCE{i}, ...
                                exp_data.TARGETS.LOWER_OUTER.PARTICLE_FLUX_DENSITY.SHOT{i},...
                                'experiment',exp_data.TARGETS.LOWER_OUTER.PARTICLE_FLUX_DENSITY.EXPERIMENT{i},...
                                'edition',exp_data.TARGETS.LOWER_OUTER.PARTICLE_FLUX_DENSITY.VERSION{i});

                            fprintf('AUG shotfile for outer target Langmuir probes particle flux density data correctly fetched\n');

                            READ_gamma_DATA{i} = true;

                        catch

                            fprintf('Langmuir probes outer target particle flux density data from AUG (shot %d, shotfile %s, experiment %s, edition %d) requested but not found\n',...
                                exp_data.TARGETS.LOWER_OUTER.PARTICLE_FLUX_DENSITY.SHOT{i},...
                                exp_data.TARGETS.LOWER_OUTER.PARTICLE_FLUX_DENSITY.SOURCE{i},...
                                exp_data.TARGETS.LOWER_OUTER.PARTICLE_FLUX_DENSITY.EXPERIMENT{i},...
                                exp_data.TARGETS.LOWER_OUTER.PARTICLE_FLUX_DENSITY.VERSION{i});
                            fprintf('Try to set another shot/shotfile/experiment/edition for TARGETS.LOWER_OUTER.PARTICLE_FLUX_DENSITY within exp_data.json\n');

                            READ_gamma_DATA{i} = false;

                        end

                    end

                end

                % Energy flux density

                for i = 1:length(exp_data.TARGETS.LOWER_OUTER.ENERGY_FLUX_DENSITY.SOURCE)

                    if strcmp(exp_data.TARGETS.LOWER_OUTER.ENERGY_FLUX_DENSITY.SOURCE{i},'LSD')

                        % Langmuir probes

                        try

                            [PARAMETERS_q_DATA{i},TIMEBASES_q_DATA{i},~,SIGNALS_q_DATA{i}] = load_aug_shotfile(...
                                exp_data.TARGETS.LOWER_OUTER.ENERGY_FLUX_DENSITY.SOURCE{i}, ...
                                exp_data.TARGETS.LOWER_OUTER.ENERGY_FLUX_DENSITY.SHOT{i},...
                                'experiment',exp_data.TARGETS.LOWER_OUTER.ENERGY_FLUX_DENSITY.EXPERIMENT{i},...
                                'edition',exp_data.TARGETS.LOWER_OUTER.ENERGY_FLUX_DENSITY.VERSION{i});

                            fprintf('AUG shotfile for outer target Langmuir probes energy flux density data correctly fetched\n');

                            READ_q_DATA{i} = true;

                        catch

                            fprintf('Langmuir probes outer target energy flux density data from AUG (shot %d, shotfile %s, experiment %s, edition %d) requested but not found\n',...
                                exp_data.TARGETS.LOWER_OUTER.ENERGY_FLUX_DENSITY.SHOT{i},...
                                exp_data.TARGETS.LOWER_OUTER.ENERGY_FLUX_DENSITY.SOURCE{i},...
                                exp_data.TARGETS.LOWER_OUTER.ENERGY_FLUX_DENSITY.EXPERIMENT{i},...
                                exp_data.TARGETS.LOWER_OUTER.ENERGY_FLUX_DENSITY.VERSION{i});
                            fprintf('Try to set another shot/shotfile/experiment/edition for TARGETS.LOWER_OUTER.ENERGY_FLUX_DENSITY within exp_data.json\n');

                            READ_q_DATA{i} = false;

                        end

                    end

                end

                %% EXTRACT EXPERIMENTAL DATA FOR AUG

                % INNER TARGET

                % Electron density data

                for i = 1:length(exp_data.TARGETS.LOWER_INNER.ELECTRON_DENSITY.SOURCE)

                    if READ_ne_DATA{i}

                        if strcmp(exp_data.TARGETS.LOWER_INNER.ELECTRON_DENSITY.SOURCE{i},'LSD')

                            % Langmuir probes

                            me = 9.1093837e-31;
                            mp = 1.6726217e-27;
                            qe = 1.6021766e-19;
                            gamma_e = 1;
                            gamma_i = 5/3;
                            delta_e = 0.5;
                            epsilon_L = 9.92326e3;
                            refl_coeffs = [2.547e-1, -1.146e-1, 1.195, 1.259];
                            ion_energy = 13.6;
                            diss_energy = 4.5/2;

                            position_probes_inner = struct;
                            k = 1;
                            for j = 1:length(PARAMETERS_ne_DATA{i}.position.items)
                                if strcmp(PARAMETERS_ne_DATA{i}.position.items(j).location,'Inner divertor')
                                    position_probes_inner(k).name = PARAMETERS_ne_DATA{i}.position.items(j).name;
                                    position_probes_inner(k).R = PARAMETERS_ne_DATA{i}.position.items(j).R;
                                    position_probes_inner(k).z = PARAMETERS_ne_DATA{i}.position.items(j).z;
                                    k = k+1;
                                end
                            end

                            time_data_ne{i} = TIMEBASES_ne_DATA{i}.time_lsd.value;

                            for j = 1:length(position_probes_inner)
                                
                                probe_name_inner{j} = position_probes_inner(j).name;
            
                                signal_name{j} = append('ne_',probe_name_inner{j});
                                values_data_ne{i}(j,:) = SIGNALS_ne_DATA{i}.(signal_name{j}).value;

                            end

                            values_data_ne_uncertainty{i} = nan(size(values_data_ne{i}));

                            unit_data_ne{i} = 'm^-3';

                        end

                        measurements_targets_experiment.lower_inner.ne_data{i}.name = exp_data.TARGETS.LOWER_INNER.ELECTRON_DENSITY.NAME_DISPLAY{i};
                        [measurements_targets_experiment.lower_inner.ne_data{i}.times,measurements_targets_experiment.lower_inner.ne_data{i}.values] = ...
                            extract_values(time_data_ne{i}, values_data_ne{i},...
                            exp_data.TARGETS.LOWER_INNER.ELECTRON_DENSITY.TIME_START{i},exp_data.TARGETS.LOWER_INNER.ELECTRON_DENSITY.TIME_END{i},...
                            exp_data.TARGETS.LOWER_INNER.ELECTRON_DENSITY.REDUCED_SET_TIME_DELTA{i});
                        if all(isnan(values_data_ne_uncertainty{i}))
                            measurements_targets_experiment.lower_inner.ne_data{i}.values_unc = NaN(size(measurements_targets_experiment.lower_inner.ne_data{i}.values));
                        else
                            [measurements_targets_experiment.lower_inner.ne_data{i}.times,measurements_targets_experiment.lower_inner.ne_data{i}.values_unc] = ...
                            extract_values(time_data_ne{i},values_data_ne_uncertainty{i},...
                            exp_data.TARGETS.LOWER_INNER.ELECTRON_DENSITY.TIME_START{i},exp_data.TARGETS.LOWER_INNER.ELECTRON_DENSITY.TIME_END{i},...
                            exp_data.TARGETS.LOWER_INNER.ELECTRON_DENSITY.REDUCED_SET_TIME_DELTA{i});
                        end
                        measurements_targets_experiment.lower_inner.ne_data{i}.unit = unit_data_ne{i};

                        fprintf('Inner target Langmuir probes electron density data from AUG (shot %d, time window [%.2f,%.2f] s) correctly extracted\n',...
                            exp_data.TARGETS.LOWER_INNER.ELECTRON_DENSITY.SHOT{i},...
                            exp_data.TARGETS.LOWER_INNER.ELECTRON_DENSITY.TIME_START{i},...
                            exp_data.TARGETS.LOWER_INNER.ELECTRON_DENSITY.TIME_END{i});

                    end

                end

                % Electron temperature data

                for i = 1:length(exp_data.TARGETS.LOWER_INNER.ELECTRON_TEMPERATURE.SOURCE)

                    if READ_Te_DATA{i}

                        if strcmp(exp_data.TARGETS.LOWER_INNER.ELECTRON_TEMPERATURE.SOURCE{i},'LSD')

                            % Langmuir probes

                            me = 9.1093837e-31;
                            mp = 1.6726217e-27;
                            qe = 1.6021766e-19;
                            gamma_e = 1;
                            gamma_i = 5/3;
                            delta_e = 0.5;
                            epsilon_L = 9.92326e3;
                            refl_coeffs = [2.547e-1, -1.146e-1, 1.195, 1.259];
                            ion_energy = 13.6;
                            diss_energy = 4.5/2;

                            position_probes_inner = struct;
                            k = 1;
                            for j = 1:length(PARAMETERS_Te_DATA{i}.position.items)
                                if strcmp(PARAMETERS_Te_DATA{i}.position.items(j).location,'Inner divertor')
                                    position_probes_inner(k).name = PARAMETERS_Te_DATA{i}.position.items(j).name;
                                    position_probes_inner(k).R = PARAMETERS_Te_DATA{i}.position.items(j).R;
                                    position_probes_inner(k).z = PARAMETERS_Te_DATA{i}.position.items(j).z;
                                    k = k+1;
                                end
                            end

                            time_data_Te{i} = TIMEBASES_Te_DATA{i}.time_lsd.value;

                            for j = 1:length(position_probes_inner)
                                
                                probe_name_inner{j} = position_probes_inner(j).name;
            
                                signal_name{j} = append('te_',probe_name_inner{j});
                                values_data_Te{i}(j,:) = SIGNALS_Te_DATA{i}.(signal_name{j}).value;

                            end

                            values_data_Te_uncertainty{i} = nan(size(values_data_Te{i}));

                            unit_data_Te{i} = 'eV';

                        end

                        measurements_targets_experiment.lower_inner.Te_data{i}.name = exp_data.TARGETS.LOWER_INNER.ELECTRON_TEMPERATURE.NAME_DISPLAY{i};
                        [measurements_targets_experiment.lower_inner.Te_data{i}.times,measurements_targets_experiment.lower_inner.Te_data{i}.values] = ...
                            extract_values(time_data_Te{i}, values_data_Te{i},...
                            exp_data.TARGETS.LOWER_INNER.ELECTRON_TEMPERATURE.TIME_START{i},exp_data.TARGETS.LOWER_INNER.ELECTRON_TEMPERATURE.TIME_END{i},...
                            exp_data.TARGETS.LOWER_INNER.ELECTRON_TEMPERATURE.REDUCED_SET_TIME_DELTA{i});
                        if all(isnan(values_data_Te_uncertainty{i}))
                            measurements_targets_experiment.lower_inner.Te_data{i}.values_unc = NaN(size(measurements_targets_experiment.lower_inner.Te_data{i}.values));
                        else
                            [measurements_targets_experiment.lower_inner.Te_data{i}.times,measurements_targets_experiment.lower_inner.Te_data{i}.values_unc] = ...
                            extract_values(time_data_Te{i},values_data_Te_uncertainty{i},...
                            exp_data.TARGETS.LOWER_INNER.ELECTRON_TEMPERATURE.TIME_START{i},exp_data.TARGETS.LOWER_INNER.ELECTRON_TEMPERATURE.TIME_END{i},...
                            exp_data.TARGETS.LOWER_INNER.ELECTRON_TEMPERATURE.REDUCED_SET_TIME_DELTA{i});
                        end
                        measurements_targets_experiment.lower_inner.Te_data{i}.unit = unit_data_Te{i};

                        fprintf('Inner target Langmuir probes electron temperature data from AUG (shot %d, time window [%.2f,%.2f] s) correctly extracted\n',...
                            exp_data.TARGETS.LOWER_INNER.ELECTRON_TEMPERATURE.SHOT{i},...
                            exp_data.TARGETS.LOWER_INNER.ELECTRON_TEMPERATURE.TIME_START{i},...
                            exp_data.TARGETS.LOWER_INNER.ELECTRON_TEMPERATURE.TIME_END{i});

                    end

                end

                % Particle flux density data

                for i = 1:length(exp_data.TARGETS.LOWER_INNER.PARTICLE_FLUX_DENSITY.SOURCE)

                    if READ_gamma_DATA{i}

                        if strcmp(exp_data.TARGETS.LOWER_INNER.PARTICLE_FLUX_DENSITY.SOURCE{i},'LSD')

                            % Langmuir probes

                            me = 9.1093837e-31;
                            mp = 1.6726217e-27;
                            qe = 1.6021766e-19;
                            gamma_e = 1;
                            gamma_i = 5/3;
                            delta_e = 0.5;
                            epsilon_L = 9.92326e3;
                            refl_coeffs = [2.547e-1, -1.146e-1, 1.195, 1.259];
                            ion_energy = 13.6;
                            diss_energy = 4.5/2;

                            position_probes_inner = struct;
                            k = 1;
                            for j = 1:length(PARAMETERS_gamma_DATA{i}.position.items)
                                if strcmp(PARAMETERS_gamma_DATA{i}.position.items(j).location,'Inner divertor')
                                    position_probes_inner(k).name = PARAMETERS_gamma_DATA{i}.position.items(j).name;
                                    position_probes_inner(k).R = PARAMETERS_gamma_DATA{i}.position.items(j).R;
                                    position_probes_inner(k).z = PARAMETERS_gamma_DATA{i}.position.items(j).z;
                                    k = k+1;
                                end
                            end

                            time_data_gamma{i} = TIMEBASES_gamma_DATA{i}.time_lsd.value;

                            for j = 1:length(position_probes_inner)
                                
                                probe_name_inner{j} = position_probes_inner(j).name;
            
                                signal_name{j} = append('ne_',probe_name_inner{j});
                                values_data_ne{i}(j,:) = SIGNALS_gamma_DATA{i}.(signal_name{j}).value;

                                signal_name{j} = append('te_',probe_name_inner{j});
                                values_data_Te{i}(j,:) = SIGNALS_gamma_DATA{i}.(signal_name{j}).value;

                                signal_name{j} = append('ang_',probe_name_inner{j});
                                values_data_ang{i}(j,:) =  SIGNALS_gamma_DATA{i}.(signal_name{j}).value;
            
                                data_cs_inner(j,:) = sqrt((qe*(gamma_e.*values_data_Te{i}(j,:)+gamma_i.*(2.*values_data_Te{i}(j,:))))./(2*mp));

                                values_data_gamma{i}(j,:) = values_data_ne{i}(j,:).*data_cs_inner(j,:).*sin((pi/180).*values_data_ang{i}(j,:));

                            end

                            values_data_gamma_uncertainty{i} = nan(size(values_data_gamma{i}));

                            unit_data_gamma{i} = 'm^-2 s^-1';

                        end

                        measurements_targets_experiment.lower_inner.gamma_data{i}.name = exp_data.TARGETS.LOWER_INNER.PARTICLE_FLUX_DENSITY.NAME_DISPLAY{i};
                        [measurements_targets_experiment.lower_inner.gamma_data{i}.times,measurements_targets_experiment.lower_inner.gamma_data{i}.values] = ...
                            extract_values(time_data_gamma{i}, values_data_gamma{i},...
                            exp_data.TARGETS.LOWER_INNER.PARTICLE_FLUX_DENSITY.TIME_START{i},exp_data.TARGETS.LOWER_INNER.PARTICLE_FLUX_DENSITY.TIME_END{i},...
                            exp_data.TARGETS.LOWER_INNER.PARTICLE_FLUX_DENSITY.REDUCED_SET_TIME_DELTA{i});
                        if all(isnan(values_data_gamma_uncertainty{i}))
                            measurements_targets_experiment.lower_inner.gamma_data{i}.values_unc = NaN(size(measurements_targets_experiment.lower_inner.gamma_data{i}.values));
                        else
                            [measurements_targets_experiment.lower_inner.gamma_data{i}.times,measurements_targets_experiment.lower_inner.gamma_data{i}.values_unc] = ...
                            extract_values(time_data_gamma{i},values_data_gamma_uncertainty{i},...
                            exp_data.TARGETS.LOWER_INNER.PARTICLE_FLUX_DENSITY.TIME_START{i},exp_data.TARGETS.LOWER_INNER.PARTICLE_FLUX_DENSITY.TIME_END{i},...
                            exp_data.TARGETS.LOWER_INNER.PARTICLE_FLUX_DENSITY.REDUCED_SET_TIME_DELTA{i});
                        end
                        measurements_targets_experiment.lower_inner.gamma_data{i}.unit = unit_data_gamma{i};

                        fprintf('Inner target Langmuir probes particle flux density data from AUG (shot %d, time window [%.2f,%.2f] s) correctly extracted\n',...
                            exp_data.TARGETS.LOWER_INNER.PARTICLE_FLUX_DENSITY.SHOT{i},...
                            exp_data.TARGETS.LOWER_INNER.PARTICLE_FLUX_DENSITY.TIME_START{i},...
                            exp_data.TARGETS.LOWER_INNER.PARTICLE_FLUX_DENSITY.TIME_END{i});

                    end

                end

                % Energy flux density data

                for i = 1:length(exp_data.TARGETS.LOWER_INNER.ENERGY_FLUX_DENSITY.SOURCE)

                    if READ_q_DATA{i}

                        if strcmp(exp_data.TARGETS.LOWER_INNER.ENERGY_FLUX_DENSITY.SOURCE{i},'LSD')

                            % Langmuir probes

                            me = 9.1093837e-31;
                            mp = 1.6726217e-27;
                            qe = 1.6021766e-19;
                            gamma_e = 1;
                            gamma_i = 5/3;
                            delta_e = 0.5;
                            epsilon_L = 9.92326e3;
                            refl_coeffs = [2.547e-1, -1.146e-1, 1.195, 1.259];
                            ion_energy = 13.6;
                            diss_energy = 4.5/2;

                            position_probes_inner = struct;
                            k = 1;
                            for j = 1:length(PARAMETERS_q_DATA{i}.position.items)
                                if strcmp(PARAMETERS_q_DATA{i}.position.items(j).location,'Inner divertor')
                                    position_probes_inner(k).name = PARAMETERS_q_DATA{i}.position.items(j).name;
                                    position_probes_inner(k).R = PARAMETERS_q_DATA{i}.position.items(j).R;
                                    position_probes_inner(k).z = PARAMETERS_q_DATA{i}.position.items(j).z;
                                    k = k+1;
                                end
                            end

                            time_data_q{i} = TIMEBASES_gamma_DATA{i}.time_lsd.value;

                            for j = 1:length(position_probes_inner)
                                
                                probe_name_inner{j} = position_probes_inner(j).name;
            
                                signal_name{j} = append('ne_',probe_name_inner{j});
                                values_data_ne{i}(j,:) = SIGNALS_q_DATA{i}.(signal_name{j}).value;

                                signal_name{j} = append('te_',probe_name_inner{j});
                                values_data_Te{i}(j,:) = SIGNALS_q_DATA{i}.(signal_name{j}).value;

                                signal_name{j} = append('ang_',probe_name_inner{j});
                                values_data_ang{i}(j,:) =  SIGNALS_q_DATA{i}.(signal_name{j}).value;

                                data_cs_inner(j,:) = sqrt((qe*(gamma_e.*values_data_Te{i}(j,:)+gamma_i.*(2.*values_data_Te{i}(j,:))))./(2*mp));
                                
                                values_data_gamma{i}(j,:) = values_data_ne{i}(j,:).*data_cs_inner(j,:).*sin((pi/180).*values_data_ang{i}(j,:));
            
                                sheath_coeff_el = 2/(1-delta_e)-0.5*log((2*pi*(me/(2*mp)))*(1+2)*((1-delta_e)^(-2)))+0.5;
                                sheath_coeff_ion = 2;
                                data_E0(j,:) = sheath_coeff_ion.*(2.*values_data_Te{i}(j,:)) + 2.85.*values_data_Te{i}(j,:);
                                data_epsilon(j,:) = data_E0(j,:)./epsilon_L;
                                data_R_e(j,:) = ((refl_coeffs(1)).*data_epsilon(j,:).^(refl_coeffs(2)))./(1+refl_coeffs(3).*data_epsilon(j,:).^(refl_coeffs(4)));
                                data_sheath_coeff_inner(j,:) = (2*sheath_coeff_ion*(1-data_R_e(j,:))+sheath_coeff_el-2.85.*data_R_e(j,:));
                                
                                values_data_q{i}(j,:) = values_data_gamma{i}(j,:).*((data_sheath_coeff_inner(j,:).*values_data_Te{i}(j,:)+ion_energy+diss_energy)*qe);

                            end

                            values_data_q_uncertainty{i} = nan(size(values_data_q{i}));

                            unit_data_q{i} = 'W m^-2';

                        end

                        measurements_targets_experiment.lower_inner.q_data{i}.name = exp_data.TARGETS.LOWER_INNER.ENERGY_FLUX_DENSITY.NAME_DISPLAY{i};
                        [measurements_targets_experiment.lower_inner.q_data{i}.times,measurements_targets_experiment.lower_inner.q_data{i}.values] = ...
                            extract_values(time_data_q{i}, values_data_q{i},...
                            exp_data.TARGETS.LOWER_INNER.ENERGY_FLUX_DENSITY.TIME_START{i},exp_data.TARGETS.LOWER_INNER.ENERGY_FLUX_DENSITY.TIME_END{i},...
                            exp_data.TARGETS.LOWER_INNER.ENERGY_FLUX_DENSITY.REDUCED_SET_TIME_DELTA{i});
                        if all(isnan(values_data_q_uncertainty{i}))
                            measurements_targets_experiment.lower_inner.q_data{i}.values_unc = NaN(size(measurements_targets_experiment.lower_inner.q_data{i}.values));
                        else
                            [measurements_targets_experiment.lower_inner.q_data{i}.times,measurements_targets_experiment.lower_inner.q_data{i}.values_unc] = ...
                            extract_values(time_data_q{i},values_data_q_uncertainty{i},...
                            exp_data.TARGETS.LOWER_INNER.ENERGY_FLUX_DENSITY.TIME_START{i},exp_data.TARGETS.LOWER_INNER.ENERGY_FLUX_DENSITY.TIME_END{i},...
                            exp_data.TARGETS.LOWER_INNER.ENERGY_FLUX_DENSITY.REDUCED_SET_TIME_DELTA{i});
                        end
                        measurements_targets_experiment.lower_inner.q_data{i}.unit = unit_data_q{i};

                        fprintf('Inner target Langmuir probes energy flux density data from AUG (shot %d, time window [%.2f,%.2f] s) correctly extracted\n',...
                            exp_data.TARGETS.LOWER_INNER.ENERGY_FLUX_DENSITY.SHOT{i},...
                            exp_data.TARGETS.LOWER_INNER.ENERGY_FLUX_DENSITY.TIME_START{i},...
                            exp_data.TARGETS.LOWER_INNER.ENERGY_FLUX_DENSITY.TIME_END{i});

                    end

                end

                % OUTER TARGET

                % Electron density data

                for i = 1:length(exp_data.TARGETS.LOWER_OUTER.ELECTRON_DENSITY.SOURCE)

                    if READ_ne_DATA{i}

                        if strcmp(exp_data.TARGETS.LOWER_OUTER.ELECTRON_DENSITY.SOURCE{i},'LSD')

                            % Langmuir probes

                            me = 9.1093837e-31;
                            mp = 1.6726217e-27;
                            qe = 1.6021766e-19;
                            gamma_e = 1;
                            gamma_i = 5/3;
                            delta_e = 0.5;
                            epsilon_L = 9.92326e3;
                            refl_coeffs = [2.547e-1, -1.146e-1, 1.195, 1.259];
                            ion_energy = 13.6;
                            diss_energy = 4.5/2;

                            position_probes_outer = struct;
                            k = 1;
                            for j = 1:length(PARAMETERS_ne_DATA{i}.position.items)
                                if strcmp(PARAMETERS_ne_DATA{i}.position.items(j).location,'Outer divertor')
                                    position_probes_outer(k).name = PARAMETERS_ne_DATA{i}.position.items(j).name;
                                    position_probes_outer(k).R = PARAMETERS_ne_DATA{i}.position.items(j).R;
                                    position_probes_outer(k).z = PARAMETERS_ne_DATA{i}.position.items(j).z;
                                    k = k+1;
                                end
                            end

                            time_data_ne{i} = TIMEBASES_ne_DATA{i}.time_lsd.value;

                            for j = 1:length(position_probes_outer)
                                
                                probe_name_outer{j} = position_probes_outer(j).name;
            
                                signal_name{j} = append('ne_',probe_name_outer{j});
                                values_data_ne{i}(j,:) = SIGNALS_ne_DATA{i}.(signal_name{j}).value;

                            end

                            values_data_ne_uncertainty{i} = nan(size(values_data_ne{i}));

                            unit_data_ne{i} = 'm^-3';

                        end

                        measurements_targets_experiment.lower_outer.ne_data{i}.name = exp_data.TARGETS.LOWER_OUTER.ELECTRON_DENSITY.NAME_DISPLAY{i};
                        [measurements_targets_experiment.lower_outer.ne_data{i}.times,measurements_targets_experiment.lower_outer.ne_data{i}.values] = ...
                            extract_values(time_data_ne{i}, values_data_ne{i},...
                            exp_data.TARGETS.LOWER_OUTER.ELECTRON_DENSITY.TIME_START{i},exp_data.TARGETS.LOWER_OUTER.ELECTRON_DENSITY.TIME_END{i},...
                            exp_data.TARGETS.LOWER_OUTER.ELECTRON_DENSITY.REDUCED_SET_TIME_DELTA{i});
                        if all(isnan(values_data_ne_uncertainty{i}))
                            measurements_targets_experiment.lower_outer.ne_data{i}.values_unc = NaN(size(measurements_targets_experiment.lower_outer.ne_data{i}.values));
                        else
                            [measurements_targets_experiment.lower_outer.ne_data{i}.times,measurements_targets_experiment.lower_outer.ne_data{i}.values_unc] = ...
                            extract_values(time_data_ne{i},values_data_ne_uncertainty{i},...
                            exp_data.TARGETS.LOWER_OUTER.ELECTRON_DENSITY.TIME_START{i},exp_data.TARGETS.LOWER_OUTER.ELECTRON_DENSITY.TIME_END{i},...
                            exp_data.TARGETS.LOWER_OUTER.ELECTRON_DENSITY.REDUCED_SET_TIME_DELTA{i});
                        end
                        measurements_targets_experiment.lower_outer.ne_data{i}.unit = unit_data_ne{i};

                        fprintf('Outer target Langmuir probes electron density data from AUG (shot %d, time window [%.2f,%.2f] s) correctly extracted\n',...
                            exp_data.TARGETS.LOWER_OUTER.ELECTRON_DENSITY.SHOT{i},...
                            exp_data.TARGETS.LOWER_OUTER.ELECTRON_DENSITY.TIME_START{i},...
                            exp_data.TARGETS.LOWER_OUTER.ELECTRON_DENSITY.TIME_END{i});

                    end

                end

                % Electron temperature data

                for i = 1:length(exp_data.TARGETS.LOWER_OUTER.ELECTRON_TEMPERATURE.SOURCE)

                    if READ_Te_DATA{i}

                        if strcmp(exp_data.TARGETS.LOWER_OUTER.ELECTRON_TEMPERATURE.SOURCE{i},'LSD')

                            % Langmuir probes

                            me = 9.1093837e-31;
                            mp = 1.6726217e-27;
                            qe = 1.6021766e-19;
                            gamma_e = 1;
                            gamma_i = 5/3;
                            delta_e = 0.5;
                            epsilon_L = 9.92326e3;
                            refl_coeffs = [2.547e-1, -1.146e-1, 1.195, 1.259];
                            ion_energy = 13.6;
                            diss_energy = 4.5/2;

                            position_probes_outer = struct;
                            k = 1;
                            for j = 1:length(PARAMETERS_Te_DATA{i}.position.items)
                                if strcmp(PARAMETERS_Te_DATA{i}.position.items(j).location,'Outer divertor')
                                    position_probes_outer(k).name = PARAMETERS_Te_DATA{i}.position.items(j).name;
                                    position_probes_outer(k).R = PARAMETERS_Te_DATA{i}.position.items(j).R;
                                    position_probes_outer(k).z = PARAMETERS_Te_DATA{i}.position.items(j).z;
                                    k = k+1;
                                end
                            end

                            time_data_Te{i} = TIMEBASES_Te_DATA{i}.time_lsd.value;

                            for j = 1:length(position_probes_outer)
                                
                                probe_name_outer{j} = position_probes_outer(j).name;
            
                                signal_name{j} = append('te_',probe_name_outer{j});
                                values_data_Te{i}(j,:) = SIGNALS_Te_DATA{i}.(signal_name{j}).value;

                            end

                            values_data_Te_uncertainty{i} = nan(size(values_data_Te{i}));

                            unit_data_Te{i} = 'eV';

                        end

                        measurements_targets_experiment.lower_outer.Te_data{i}.name = exp_data.TARGETS.LOWER_OUTER.ELECTRON_TEMPERATURE.NAME_DISPLAY{i};
                        [measurements_targets_experiment.lower_outer.Te_data{i}.times,measurements_targets_experiment.lower_outer.Te_data{i}.values] = ...
                            extract_values(time_data_Te{i}, values_data_Te{i},...
                            exp_data.TARGETS.LOWER_OUTER.ELECTRON_TEMPERATURE.TIME_START{i},exp_data.TARGETS.LOWER_OUTER.ELECTRON_TEMPERATURE.TIME_END{i},...
                            exp_data.TARGETS.LOWER_OUTER.ELECTRON_TEMPERATURE.REDUCED_SET_TIME_DELTA{i});
                        if all(isnan(values_data_Te_uncertainty{i}))
                            measurements_targets_experiment.lower_outer.Te_data{i}.values_unc = NaN(size(measurements_targets_experiment.lower_outer.Te_data{i}.values));
                        else
                            [measurements_targets_experiment.lower_outer.Te_data{i}.times,measurements_targets_experiment.lower_outer.Te_data{i}.values_unc] = ...
                            extract_values(time_data_Te{i},values_data_Te_uncertainty{i},...
                            exp_data.TARGETS.LOWER_OUTER.ELECTRON_TEMPERATURE.TIME_START{i},exp_data.TARGETS.LOWER_OUTER.ELECTRON_TEMPERATURE.TIME_END{i},...
                            exp_data.TARGETS.LOWER_OUTER.ELECTRON_TEMPERATURE.REDUCED_SET_TIME_DELTA{i});
                        end
                        measurements_targets_experiment.lower_outer.Te_data{i}.unit = unit_data_Te{i};

                        fprintf('Outer target Langmuir probes electron temperature data from AUG (shot %d, time window [%.2f,%.2f] s) correctly extracted\n',...
                            exp_data.TARGETS.LOWER_OUTER.ELECTRON_TEMPERATURE.SHOT{i},...
                            exp_data.TARGETS.LOWER_OUTER.ELECTRON_TEMPERATURE.TIME_START{i},...
                            exp_data.TARGETS.LOWER_OUTER.ELECTRON_TEMPERATURE.TIME_END{i});

                    end

                end

                % Particle flux density data

                for i = 1:length(exp_data.TARGETS.LOWER_OUTER.PARTICLE_FLUX_DENSITY.SOURCE)

                    if READ_gamma_DATA{i}

                        if strcmp(exp_data.TARGETS.LOWER_OUTER.PARTICLE_FLUX_DENSITY.SOURCE{i},'LSD')

                            % Langmuir probes

                            me = 9.1093837e-31;
                            mp = 1.6726217e-27;
                            qe = 1.6021766e-19;
                            gamma_e = 1;
                            gamma_i = 5/3;
                            delta_e = 0.5;
                            epsilon_L = 9.92326e3;
                            refl_coeffs = [2.547e-1, -1.146e-1, 1.195, 1.259];
                            ion_energy = 13.6;
                            diss_energy = 4.5/2;

                            position_probes_outer = struct;
                            k = 1;
                            for j = 1:length(PARAMETERS_gamma_DATA{i}.position.items)
                                if strcmp(PARAMETERS_gamma_DATA{i}.position.items(j).location,'Outer divertor')
                                    position_probes_outer(k).name = PARAMETERS_gamma_DATA{i}.position.items(j).name;
                                    position_probes_outer(k).R = PARAMETERS_gamma_DATA{i}.position.items(j).R;
                                    position_probes_outer(k).z = PARAMETERS_gamma_DATA{i}.position.items(j).z;
                                    k = k+1;
                                end
                            end

                            time_data_gamma{i} = TIMEBASES_gamma_DATA{i}.time_lsd.value;

                            for j = 1:length(position_probes_outer)
                                
                                probe_name_outer{j} = position_probes_outer(j).name;
            
                                signal_name{j} = append('ne_',probe_name_outer{j});
                                values_data_ne{i}(j,:) = SIGNALS_gamma_DATA{i}.(signal_name{j}).value;

                                signal_name{j} = append('te_',probe_name_outer{j});
                                values_data_Te{i}(j,:) = SIGNALS_gamma_DATA{i}.(signal_name{j}).value;

                                signal_name{j} = append('ang_',probe_name_outer{j});
                                values_data_ang{i}(j,:) =  SIGNALS_gamma_DATA{i}.(signal_name{j}).value;
            
                                data_cs_outer(j,:) = sqrt((qe*(gamma_e.*values_data_Te{i}(j,:)+gamma_i.*(2.*values_data_Te{i}(j,:))))./(2*mp));

                                values_data_gamma{i}(j,:) = values_data_ne{i}(j,:).*data_cs_outer(j,:).*sin((pi/180).*values_data_ang{i}(j,:));

                            end

                            values_data_gamma_uncertainty{i} = nan(size(values_data_gamma{i}));

                            unit_data_gamma{i} = 'm^-2 s^-1';

                        end

                        measurements_targets_experiment.lower_outer.gamma_data{i}.name = exp_data.TARGETS.LOWER_OUTER.PARTICLE_FLUX_DENSITY.NAME_DISPLAY{i};
                        [measurements_targets_experiment.lower_outer.gamma_data{i}.times,measurements_targets_experiment.lower_outer.gamma_data{i}.values] = ...
                            extract_values(time_data_gamma{i}, values_data_gamma{i},...
                            exp_data.TARGETS.LOWER_OUTER.PARTICLE_FLUX_DENSITY.TIME_START{i},exp_data.TARGETS.LOWER_OUTER.PARTICLE_FLUX_DENSITY.TIME_END{i},...
                            exp_data.TARGETS.LOWER_OUTER.PARTICLE_FLUX_DENSITY.REDUCED_SET_TIME_DELTA{i});
                        if all(isnan(values_data_gamma_uncertainty{i}))
                            measurements_targets_experiment.lower_outer.gamma_data{i}.values_unc = NaN(size(measurements_targets_experiment.lower_outer.gamma_data{i}.values));
                        else
                            [measurements_targets_experiment.lower_outer.gamma_data{i}.times,measurements_targets_experiment.lower_outer.gamma_data{i}.values_unc] = ...
                            extract_values(time_data_gamma{i},values_data_gamma_uncertainty{i},...
                            exp_data.TARGETS.LOWER_OUTER.PARTICLE_FLUX_DENSITY.TIME_START{i},exp_data.TARGETS.LOWER_OUTER.PARTICLE_FLUX_DENSITY.TIME_END{i},...
                            exp_data.TARGETS.LOWER_OUTER.PARTICLE_FLUX_DENSITY.REDUCED_SET_TIME_DELTA{i});
                        end
                        measurements_targets_experiment.lower_outer.gamma_data{i}.unit = unit_data_gamma{i};

                        fprintf('Outer target Langmuir probes particle flux density data from AUG (shot %d, time window [%.2f,%.2f] s) correctly extracted\n',...
                            exp_data.TARGETS.LOWER_OUTER.PARTICLE_FLUX_DENSITY.SHOT{i},...
                            exp_data.TARGETS.LOWER_OUTER.PARTICLE_FLUX_DENSITY.TIME_START{i},...
                            exp_data.TARGETS.LOWER_OUTER.PARTICLE_FLUX_DENSITY.TIME_END{i});

                    end

                end

                % Energy flux density data

                for i = 1:length(exp_data.TARGETS.LOWER_OUTER.ENERGY_FLUX_DENSITY.SOURCE)

                    if READ_q_DATA{i}

                        if strcmp(exp_data.TARGETS.LOWER_OUTER.ENERGY_FLUX_DENSITY.SOURCE{i},'LSD')

                            % Langmuir probes

                            me = 9.1093837e-31;
                            mp = 1.6726217e-27;
                            qe = 1.6021766e-19;
                            gamma_e = 1;
                            gamma_i = 5/3;
                            delta_e = 0.5;
                            epsilon_L = 9.92326e3;
                            refl_coeffs = [2.547e-1, -1.146e-1, 1.195, 1.259];
                            ion_energy = 13.6;
                            diss_energy = 4.5/2;

                            position_probes_outer = struct;
                            k = 1;
                            for j = 1:length(PARAMETERS_q_DATA{i}.position.items)
                                if strcmp(PARAMETERS_q_DATA{i}.position.items(j).location,'Outer divertor')
                                    position_probes_outer(k).name = PARAMETERS_q_DATA{i}.position.items(j).name;
                                    position_probes_outer(k).R = PARAMETERS_q_DATA{i}.position.items(j).R;
                                    position_probes_outer(k).z = PARAMETERS_q_DATA{i}.position.items(j).z;
                                    k = k+1;
                                end
                            end

                            time_data_q{i} = TIMEBASES_gamma_DATA{i}.time_lsd.value;

                            for j = 1:length(position_probes_outer)
                                
                                probe_name_outer{j} = position_probes_outer(j).name;
            
                                signal_name{j} = append('ne_',probe_name_outer{j});
                                values_data_ne{i}(j,:) = SIGNALS_q_DATA{i}.(signal_name{j}).value;

                                signal_name{j} = append('te_',probe_name_outer{j});
                                values_data_Te{i}(j,:) = SIGNALS_q_DATA{i}.(signal_name{j}).value;

                                signal_name{j} = append('ang_',probe_name_outer{j});
                                values_data_ang{i}(j,:) =  SIGNALS_q_DATA{i}.(signal_name{j}).value;

                                data_cs_outer(j,:) = sqrt((qe*(gamma_e.*values_data_Te{i}(j,:)+gamma_i.*(2.*values_data_Te{i}(j,:))))./(2*mp));
                                
                                values_data_gamma{i}(j,:) = values_data_ne{i}(j,:).*data_cs_outer(j,:).*sin((pi/180).*values_data_ang{i}(j,:));
            
                                sheath_coeff_el = 2/(1-delta_e)-0.5*log((2*pi*(me/(2*mp)))*(1+2)*((1-delta_e)^(-2)))+0.5;
                                sheath_coeff_ion = 2;
                                data_E0(j,:) = sheath_coeff_ion.*(2.*values_data_Te{i}(j,:)) + 2.85.*values_data_Te{i}(j,:);
                                data_epsilon(j,:) = data_E0(j,:)./epsilon_L;
                                data_R_e(j,:) = ((refl_coeffs(1)).*data_epsilon(j,:).^(refl_coeffs(2)))./(1+refl_coeffs(3).*data_epsilon(j,:).^(refl_coeffs(4)));
                                data_sheath_coeff_outer(j,:) = (2*sheath_coeff_ion*(1-data_R_e(j,:))+sheath_coeff_el-2.85.*data_R_e(j,:));
                                
                                values_data_q{i}(j,:) = values_data_gamma{i}(j,:).*((data_sheath_coeff_outer(j,:).*values_data_Te{i}(j,:)+ion_energy+diss_energy)*qe);

                            end

                            values_data_q_uncertainty{i} = nan(size(values_data_q{i}));

                            unit_data_q{i} = 'W m^-2';

                        end

                        measurements_targets_experiment.lower_outer.q_data{i}.name = exp_data.TARGETS.LOWER_OUTER.ENERGY_FLUX_DENSITY.NAME_DISPLAY{i};
                        [measurements_targets_experiment.lower_outer.q_data{i}.times,measurements_targets_experiment.lower_outer.q_data{i}.values] = ...
                            extract_values(time_data_q{i}, values_data_q{i},...
                            exp_data.TARGETS.LOWER_OUTER.ENERGY_FLUX_DENSITY.TIME_START{i},exp_data.TARGETS.LOWER_OUTER.ENERGY_FLUX_DENSITY.TIME_END{i},...
                            exp_data.TARGETS.LOWER_OUTER.ENERGY_FLUX_DENSITY.REDUCED_SET_TIME_DELTA{i});
                        if all(isnan(values_data_q_uncertainty{i}))
                            measurements_targets_experiment.lower_outer.q_data{i}.values_unc = NaN(size(measurements_targets_experiment.lower_outer.q_data{i}.values));
                        else
                            [measurements_targets_experiment.lower_outer.q_data{i}.times,measurements_targets_experiment.lower_outer.q_data{i}.values_unc] = ...
                            extract_values(time_data_q{i},values_data_q_uncertainty{i},...
                            exp_data.TARGETS.LOWER_OUTER.ENERGY_FLUX_DENSITY.TIME_START{i},exp_data.TARGETS.LOWER_OUTER.ENERGY_FLUX_DENSITY.TIME_END{i},...
                            exp_data.TARGETS.LOWER_OUTER.ENERGY_FLUX_DENSITY.REDUCED_SET_TIME_DELTA{i});
                        end
                        measurements_targets_experiment.lower_outer.q_data{i}.unit = unit_data_q{i};

                        fprintf('Outer target Langmuir probes energy flux density data from AUG (shot %d, time window [%.2f,%.2f] s) correctly extracted\n',...
                            exp_data.TARGETS.LOWER_OUTER.ENERGY_FLUX_DENSITY.SHOT{i},...
                            exp_data.TARGETS.LOWER_OUTER.ENERGY_FLUX_DENSITY.TIME_START{i},...
                            exp_data.TARGETS.LOWER_OUTER.ENERGY_FLUX_DENSITY.TIME_END{i});

                    end

                end

                %% CALCULATE COORDINATES FOR AUG

                % INNER TARGET

                % Electron density data

                for i = 1:length(exp_data.TARGETS.LOWER_INNER.ELECTRON_DENSITY.SOURCE)

                    if READ_ne_DATA{i}

                        if strcmp(exp_data.TARGETS.LOWER_INNER.ELECTRON_DENSITY.SOURCE{i},'LSD')

                            % Langmuir probes

                            for j = 1:length(position_probes_inner)
                                coordinate_shotfile_ne_inner(j) = position_probes_inner(j).R';
                                z_coordinate_shotfile_ne_inner(j) = position_probes_inner(j).z';
                            end

                            coordinate_shotfile_ne_inner = repmat(coordinate_shotfile_ne_inner,length(measurements_targets_experiment.lower_inner.ne_data{i}.times),1);
                            z_coordinate_shotfile_ne_inner = repmat(z_coordinate_shotfile_ne_inner,length(measurements_targets_experiment.lower_inner.ne_data{i}.times),1);

                            values_original = measurements_targets_experiment.lower_inner.ne_data{i}.values;
                            values_unc_original = measurements_targets_experiment.lower_inner.ne_data{i}.values_unc;

                            [measurements_targets_experiment.lower_inner.ne_data{i}.rhop,measurements_targets_experiment.lower_inner.ne_data{i}.values] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_targets_experiment.lower_inner.ne_data{i}.times,values_original,values_unc_original,...
                                exp_data.TARGETS.LOWER_INNER.ELECTRON_DENSITY.SHOT{i},coordinate_shotfile_ne_inner,z_coordinate_shotfile_ne_inner,'R','rhop',...
                                exp_data.TARGETS.LOWER_INNER.ELECTRON_DENSITY.SHIFT{i});

                            [measurements_targets_experiment.lower_inner.ne_data{i}.dssep,~,~] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_targets_experiment.lower_inner.ne_data{i}.times,values_original,values_unc_original,...
                                exp_data.TARGETS.LOWER_INNER.ELECTRON_DENSITY.SHOT{i},coordinate_shotfile_ne_inner,z_coordinate_shotfile_ne_inner,'R','dssep',...
                                exp_data.TARGETS.LOWER_INNER.ELECTRON_DENSITY.SHIFT{i});

                            [measurements_targets_experiment.lower_inner.ne_data{i}.R,~,~] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_targets_experiment.lower_inner.ne_data{i}.times,values_original,values_unc_original,...
                                exp_data.TARGETS.LOWER_INNER.ELECTRON_DENSITY.SHOT{i},coordinate_shotfile_ne_inner,z_coordinate_shotfile_ne_inner,'R','R',...
                                exp_data.TARGETS.LOWER_INNER.ELECTRON_DENSITY.SHIFT{i});

                            fprintf('Radial coordinates for inner target Langmuir probes electron density data correctly converted\n');

                        end

                    end

                end

                % Electron temperature data

                for i = 1:length(exp_data.TARGETS.LOWER_INNER.ELECTRON_TEMPERATURE.SOURCE)

                    if READ_Te_DATA{i}

                        if strcmp(exp_data.TARGETS.LOWER_INNER.ELECTRON_TEMPERATURE.SOURCE{i},'LSD')

                            % Langmuir probes

                            for j = 1:length(position_probes_inner)
                                coordinate_shotfile_Te_inner(j) = position_probes_inner(j).R';
                                z_coordinate_shotfile_Te_inner(j) = position_probes_inner(j).z';
                            end

                            coordinate_shotfile_Te_inner = repmat(coordinate_shotfile_Te_inner,length(measurements_targets_experiment.lower_inner.Te_data{i}.times),1);
                            z_coordinate_shotfile_Te_inner = repmat(z_coordinate_shotfile_Te_inner,length(measurements_targets_experiment.lower_inner.Te_data{i}.times),1);

                            values_original = measurements_targets_experiment.lower_inner.Te_data{i}.values;
                            values_unc_original = measurements_targets_experiment.lower_inner.Te_data{i}.values_unc;

                            [measurements_targets_experiment.lower_inner.Te_data{i}.rhop,measurements_targets_experiment.lower_inner.Te_data{i}.values,measurements_targets_experiment.lower_inner.Te_data{i}.values_unc] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_targets_experiment.lower_inner.Te_data{i}.times,values_original,values_unc_original,...
                                exp_data.TARGETS.LOWER_INNER.ELECTRON_TEMPERATURE.SHOT{i},coordinate_shotfile_Te_inner,z_coordinate_shotfile_Te_inner,'R','rhop',...
                                exp_data.TARGETS.LOWER_INNER.ELECTRON_TEMPERATURE.SHIFT{i});

                            [measurements_targets_experiment.lower_inner.Te_data{i}.dssep,~,~] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_targets_experiment.lower_inner.Te_data{i}.times,values_original,values_unc_original,...
                                exp_data.TARGETS.LOWER_INNER.ELECTRON_TEMPERATURE.SHOT{i},coordinate_shotfile_Te_inner,z_coordinate_shotfile_Te_inner,'R','dssep',...
                                exp_data.TARGETS.LOWER_INNER.ELECTRON_TEMPERATURE.SHIFT{i});

                            [measurements_targets_experiment.lower_inner.Te_data{i}.R,~,~] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_targets_experiment.lower_inner.Te_data{i}.times,values_original,values_unc_original,...
                                exp_data.TARGETS.LOWER_INNER.ELECTRON_TEMPERATURE.SHOT{i},coordinate_shotfile_Te_inner,z_coordinate_shotfile_Te_inner,'R','R',...
                                exp_data.TARGETS.LOWER_INNER.ELECTRON_TEMPERATURE.SHIFT{i});

                            fprintf('Radial coordinates for inner target Langmuir probes electron temperature data correctly converted\n');

                        end

                    end

                end

                % Particle flux density data

                for i = 1:length(exp_data.TARGETS.LOWER_INNER.PARTICLE_FLUX_DENSITY.SOURCE)

                    if READ_gamma_DATA{i}

                        if strcmp(exp_data.TARGETS.LOWER_INNER.PARTICLE_FLUX_DENSITY.SOURCE{i},'LSD')

                            % Langmuir probes

                            for j = 1:length(position_probes_inner)
                                coordinate_shotfile_gamma_inner(j) = position_probes_inner(j).R';
                                z_coordinate_shotfile_gamma_inner(j) = position_probes_inner(j).z';
                            end

                            coordinate_shotfile_gamma_inner = repmat(coordinate_shotfile_gamma_inner,length(measurements_targets_experiment.lower_inner.gamma_data{i}.times),1);
                            z_coordinate_shotfile_gamma_inner = repmat(z_coordinate_shotfile_gamma_inner,length(measurements_targets_experiment.lower_inner.gamma_data{i}.times),1);

                            values_original = measurements_targets_experiment.lower_inner.gamma_data{i}.values;
                            values_unc_original = measurements_targets_experiment.lower_inner.gamma_data{i}.values_unc;

                            [measurements_targets_experiment.lower_inner.gamma_data{i}.rhop,measurements_targets_experiment.lower_inner.gamma_data{i}.values,measurements_targets_experiment.lower_inner.gamma_data{i}.values_unc] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_targets_experiment.lower_inner.gamma_data{i}.times,values_original,values_unc_original,...
                                exp_data.TARGETS.LOWER_INNER.PARTICLE_FLUX_DENSITY.SHOT{i},coordinate_shotfile_gamma_inner,z_coordinate_shotfile_gamma_inner,'R','rhop',...
                                exp_data.TARGETS.LOWER_INNER.PARTICLE_FLUX_DENSITY.SHIFT{i});

                            [measurements_targets_experiment.lower_inner.gamma_data{i}.dssep,~,~] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_targets_experiment.lower_inner.gamma_data{i}.times,values_original,values_unc_original,...
                                exp_data.TARGETS.LOWER_INNER.PARTICLE_FLUX_DENSITY.SHOT{i},coordinate_shotfile_gamma_inner,z_coordinate_shotfile_gamma_inner,'R','dssep',...
                                exp_data.TARGETS.LOWER_INNER.PARTICLE_FLUX_DENSITY.SHIFT{i});

                            [measurements_targets_experiment.lower_inner.gamma_data{i}.R,~,~] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_targets_experiment.lower_inner.gamma_data{i}.times,values_original,values_unc_original,...
                                exp_data.TARGETS.LOWER_INNER.PARTICLE_FLUX_DENSITY.SHOT{i},coordinate_shotfile_gamma_inner,z_coordinate_shotfile_gamma_inner,'R','R',...
                                exp_data.TARGETS.LOWER_INNER.PARTICLE_FLUX_DENSITY.SHIFT{i});

                            fprintf('Radial coordinates for inner target Langmuir probes particle flux density data correctly converted\n');

                        end

                    end

                end

                % Energy flux density data

                for i = 1:length(exp_data.TARGETS.LOWER_INNER.ENERGY_FLUX_DENSITY.SOURCE)

                    if READ_q_DATA{i}

                        if strcmp(exp_data.TARGETS.LOWER_INNER.ENERGY_FLUX_DENSITY.SOURCE{i},'LSD')

                            % Langmuir probes

                            for j = 1:length(position_probes_inner)
                                coordinate_shotfile_q_inner(j) = position_probes_inner(j).R';
                                z_coordinate_shotfile_q_inner(j) = position_probes_inner(j).z';
                            end

                            coordinate_shotfile_q_inner = repmat(coordinate_shotfile_q_inner,length(measurements_targets_experiment.lower_inner.q_data{i}.times),1);
                            z_coordinate_shotfile_q_inner = repmat(z_coordinate_shotfile_q_inner,length(measurements_targets_experiment.lower_inner.q_data{i}.times),1);

                            values_original = measurements_targets_experiment.lower_inner.q_data{i}.values;
                            values_unc_original = measurements_targets_experiment.lower_inner.q_data{i}.values_unc;

                            [measurements_targets_experiment.lower_inner.q_data{i}.rhop,measurements_targets_experiment.lower_inner.q_data{i}.values,measurements_targets_experiment.lower_inner.q_data{i}.values_unc] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_targets_experiment.lower_inner.q_data{i}.times,values_original,values_unc_original,...
                                exp_data.TARGETS.LOWER_INNER.ENERGY_FLUX_DENSITY.SHOT{i},coordinate_shotfile_q_inner,z_coordinate_shotfile_q_inner,'R','rhop',...
                                exp_data.TARGETS.LOWER_INNER.ENERGY_FLUX_DENSITY.SHIFT{i});

                            [measurements_targets_experiment.lower_inner.q_data{i}.dssep,~,~] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_targets_experiment.lower_inner.q_data{i}.times,values_original,values_unc_original,...
                                exp_data.TARGETS.LOWER_INNER.ENERGY_FLUX_DENSITY.SHOT{i},coordinate_shotfile_q_inner,z_coordinate_shotfile_q_inner,'R','dssep',...
                                exp_data.TARGETS.LOWER_INNER.ENERGY_FLUX_DENSITY.SHIFT{i});

                            [measurements_targets_experiment.lower_inner.q_data{i}.R,~,~] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_targets_experiment.lower_inner.q_data{i}.times,values_original,values_unc_original,...
                                exp_data.TARGETS.LOWER_INNER.ENERGY_FLUX_DENSITY.SHOT{i},coordinate_shotfile_q_inner,z_coordinate_shotfile_q_inner,'R','R',...
                                exp_data.TARGETS.LOWER_INNER.ENERGY_FLUX_DENSITY.SHIFT{i});

                            fprintf('Radial coordinates for inner target Langmuir probes energy flux density data correctly converted\n');

                        end

                    end

                end

                % OUTER TARGET

                % Electron density data

                for i = 1:length(exp_data.TARGETS.LOWER_OUTER.ELECTRON_DENSITY.SOURCE)

                    if READ_ne_DATA{i}

                        if strcmp(exp_data.TARGETS.LOWER_OUTER.ELECTRON_DENSITY.SOURCE{i},'LSD')

                            % Langmuir probes

                            for j = 1:length(position_probes_outer)
                                coordinate_shotfile_ne_outer(j) = position_probes_outer(j).R';
                                z_coordinate_shotfile_ne_outer(j) = position_probes_outer(j).z';
                            end

                            coordinate_shotfile_ne_outer = repmat(coordinate_shotfile_ne_outer,length(measurements_targets_experiment.lower_outer.ne_data{i}.times),1);
                            z_coordinate_shotfile_ne_outer = repmat(z_coordinate_shotfile_ne_outer,length(measurements_targets_experiment.lower_outer.ne_data{i}.times),1);

                            values_original = measurements_targets_experiment.lower_outer.ne_data{i}.values;
                            values_unc_original = measurements_targets_experiment.lower_outer.ne_data{i}.values_unc;

                            [measurements_targets_experiment.lower_outer.ne_data{i}.rhop,measurements_targets_experiment.lower_outer.ne_data{i}.values,measurements_targets_experiment.lower_outer.ne_data{i}.values_unc] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_targets_experiment.lower_outer.ne_data{i}.times,values_original,values_unc_original,...
                                exp_data.TARGETS.LOWER_OUTER.ELECTRON_DENSITY.SHOT{i},coordinate_shotfile_ne_outer,z_coordinate_shotfile_ne_outer,'R','rhop',...
                                exp_data.TARGETS.LOWER_OUTER.ELECTRON_DENSITY.SHIFT{i});

                            [measurements_targets_experiment.lower_outer.ne_data{i}.dssep,~,~] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_targets_experiment.lower_outer.ne_data{i}.times,values_original,values_unc_original,...
                                exp_data.TARGETS.LOWER_OUTER.ELECTRON_DENSITY.SHOT{i},coordinate_shotfile_ne_outer,z_coordinate_shotfile_ne_outer,'R','dssep',...
                                exp_data.TARGETS.LOWER_OUTER.ELECTRON_DENSITY.SHIFT{i});

                            [measurements_targets_experiment.lower_outer.ne_data{i}.R,~,~] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_targets_experiment.lower_outer.ne_data{i}.times,values_original,values_unc_original,...
                                exp_data.TARGETS.LOWER_OUTER.ELECTRON_DENSITY.SHOT{i},coordinate_shotfile_ne_outer,z_coordinate_shotfile_ne_outer,'R','R',...
                                exp_data.TARGETS.LOWER_OUTER.ELECTRON_DENSITY.SHIFT{i});

                            fprintf('Radial coordinates for outer target Langmuir probes electron density data correctly converted\n');

                        end

                    end

                end

                % Electron temperature data

                for i = 1:length(exp_data.TARGETS.LOWER_OUTER.ELECTRON_TEMPERATURE.SOURCE)

                    if READ_Te_DATA{i}

                        if strcmp(exp_data.TARGETS.LOWER_OUTER.ELECTRON_TEMPERATURE.SOURCE{i},'LSD')

                            % Langmuir probes

                            for j = 1:length(position_probes_outer)
                                coordinate_shotfile_Te_outer(j) = position_probes_outer(j).R';
                                z_coordinate_shotfile_Te_outer(j) = position_probes_outer(j).z';
                            end

                            coordinate_shotfile_Te_outer = repmat(coordinate_shotfile_Te_outer,length(measurements_targets_experiment.lower_outer.Te_data{i}.times),1);
                            z_coordinate_shotfile_Te_outer = repmat(z_coordinate_shotfile_Te_outer,length(measurements_targets_experiment.lower_outer.Te_data{i}.times),1);

                            values_original = measurements_targets_experiment.lower_outer.Te_data{i}.values;
                            values_unc_original = measurements_targets_experiment.lower_outer.Te_data{i}.values_unc;

                            [measurements_targets_experiment.lower_outer.Te_data{i}.rhop,measurements_targets_experiment.lower_outer.Te_data{i}.values,measurements_targets_experiment.lower_outer.Te_data{i}.values_unc] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_targets_experiment.lower_outer.Te_data{i}.times,values_original,values_unc_original,...
                                exp_data.TARGETS.LOWER_OUTER.ELECTRON_TEMPERATURE.SHOT{i},coordinate_shotfile_Te_outer,z_coordinate_shotfile_Te_outer,'R','rhop',...
                                exp_data.TARGETS.LOWER_OUTER.ELECTRON_TEMPERATURE.SHIFT{i});

                            [measurements_targets_experiment.lower_outer.Te_data{i}.dssep,~,~] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_targets_experiment.lower_outer.Te_data{i}.times,values_original,values_unc_original,...
                                exp_data.TARGETS.LOWER_OUTER.ELECTRON_TEMPERATURE.SHOT{i},coordinate_shotfile_Te_outer,z_coordinate_shotfile_Te_outer,'R','dssep',...
                                exp_data.TARGETS.LOWER_OUTER.ELECTRON_TEMPERATURE.SHIFT{i});

                            [measurements_targets_experiment.lower_outer.Te_data{i}.R,~,~] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_targets_experiment.lower_outer.Te_data{i}.times,values_original,values_unc_original,...
                                exp_data.TARGETS.LOWER_OUTER.ELECTRON_TEMPERATURE.SHOT{i},coordinate_shotfile_Te_outer,z_coordinate_shotfile_Te_outer,'R','R',...
                                exp_data.TARGETS.LOWER_OUTER.ELECTRON_TEMPERATURE.SHIFT{i});

                            fprintf('Radial coordinates for outer target Langmuir probes electron temperature data correctly converted\n');

                        end

                    end

                end

                % Particle flux density data

                for i = 1:length(exp_data.TARGETS.LOWER_OUTER.PARTICLE_FLUX_DENSITY.SOURCE)

                    if READ_gamma_DATA{i}

                        if strcmp(exp_data.TARGETS.LOWER_OUTER.PARTICLE_FLUX_DENSITY.SOURCE{i},'LSD')

                            % Langmuir probes

                            for j = 1:length(position_probes_outer)
                                coordinate_shotfile_gamma_outer(j) = position_probes_outer(j).R';
                                z_coordinate_shotfile_gamma_outer(j) = position_probes_outer(j).z';
                            end

                            coordinate_shotfile_gamma_outer = repmat(coordinate_shotfile_gamma_outer,length(measurements_targets_experiment.lower_outer.gamma_data{i}.times),1);
                            z_coordinate_shotfile_gamma_outer = repmat(z_coordinate_shotfile_gamma_outer,length(measurements_targets_experiment.lower_outer.gamma_data{i}.times),1);

                            values_original = measurements_targets_experiment.lower_outer.gamma_data{i}.values;
                            values_unc_original = measurements_targets_experiment.lower_outer.gamma_data{i}.values_unc;

                            [measurements_targets_experiment.lower_outer.gamma_data{i}.rhop,measurements_targets_experiment.lower_outer.gamma_data{i}.values,measurements_targets_experiment.lower_outer.gamma_data{i}.values_unc] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_targets_experiment.lower_outer.gamma_data{i}.times,values_original,values_unc_original,...
                                exp_data.TARGETS.LOWER_OUTER.PARTICLE_FLUX_DENSITY.SHOT{i},coordinate_shotfile_gamma_outer,z_coordinate_shotfile_gamma_outer,'R','rhop',...
                                exp_data.TARGETS.LOWER_OUTER.PARTICLE_FLUX_DENSITY.SHIFT{i});

                            [measurements_targets_experiment.lower_outer.gamma_data{i}.dssep,~,~] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_targets_experiment.lower_outer.gamma_data{i}.times,values_original,values_unc_original,...
                                exp_data.TARGETS.LOWER_OUTER.PARTICLE_FLUX_DENSITY.SHOT{i},coordinate_shotfile_gamma_outer,z_coordinate_shotfile_gamma_outer,'R','dssep',...
                                exp_data.TARGETS.LOWER_OUTER.PARTICLE_FLUX_DENSITY.SHIFT{i});

                            [measurements_targets_experiment.lower_outer.gamma_data{i}.R,~,~] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_targets_experiment.lower_outer.gamma_data{i}.times,values_original,values_unc_original,...
                                exp_data.TARGETS.LOWER_OUTER.PARTICLE_FLUX_DENSITY.SHOT{i},coordinate_shotfile_gamma_outer,z_coordinate_shotfile_gamma_outer,'R','R',...
                                exp_data.TARGETS.LOWER_OUTER.PARTICLE_FLUX_DENSITY.SHIFT{i});

                            fprintf('Radial coordinates for outer target Langmuir probes particle flux density data correctly converted\n');

                        end

                    end

                end

                % Energy flux density data

                for i = 1:length(exp_data.TARGETS.LOWER_OUTER.ENERGY_FLUX_DENSITY.SOURCE)

                    if READ_q_DATA{i}

                        if strcmp(exp_data.TARGETS.LOWER_OUTER.ENERGY_FLUX_DENSITY.SOURCE{i},'LSD')

                            % Langmuir probes

                            for j = 1:length(position_probes_outer)
                                coordinate_shotfile_q_outer(j) = position_probes_outer(j).R';
                                z_coordinate_shotfile_q_outer(j) = position_probes_outer(j).z';
                            end

                            coordinate_shotfile_q_outer = repmat(coordinate_shotfile_q_outer,length(measurements_targets_experiment.lower_outer.q_data{i}.times),1);
                            z_coordinate_shotfile_q_outer = repmat(z_coordinate_shotfile_q_outer,length(measurements_targets_experiment.lower_outer.q_data{i}.times),1);

                            values_original = measurements_targets_experiment.lower_outer.q_data{i}.values;
                            values_unc_original = measurements_targets_experiment.lower_outer.q_data{i}.values_unc;

                            [measurements_targets_experiment.lower_outer.q_data{i}.rhop,measurements_targets_experiment.lower_outer.q_data{i}.values,measurements_targets_experiment.lower_outer.q_data{i}.values_unc] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_targets_experiment.lower_outer.q_data{i}.times,values_original,values_unc_original,...
                                exp_data.TARGETS.LOWER_OUTER.ENERGY_FLUX_DENSITY.SHOT{i},coordinate_shotfile_q_outer,z_coordinate_shotfile_q_outer,'R','rhop',...
                                exp_data.TARGETS.LOWER_OUTER.ENERGY_FLUX_DENSITY.SHIFT{i});

                            [measurements_targets_experiment.lower_outer.q_data{i}.dssep,~,~] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_targets_experiment.lower_outer.q_data{i}.times,values_original,values_unc_original,...
                                exp_data.TARGETS.LOWER_OUTER.ENERGY_FLUX_DENSITY.SHOT{i},coordinate_shotfile_q_outer,z_coordinate_shotfile_q_outer,'R','dssep',...
                                exp_data.TARGETS.LOWER_OUTER.ENERGY_FLUX_DENSITY.SHIFT{i});

                            [measurements_targets_experiment.lower_outer.q_data{i}.R,~,~] = shift_convert_coordinate(...
                                exp_data.DEVICE,measurements_targets_experiment.lower_outer.q_data{i}.times,values_original,values_unc_original,...
                                exp_data.TARGETS.LOWER_OUTER.ENERGY_FLUX_DENSITY.SHOT{i},coordinate_shotfile_q_outer,z_coordinate_shotfile_q_outer,'R','R',...
                                exp_data.TARGETS.LOWER_OUTER.ENERGY_FLUX_DENSITY.SHIFT{i});

                            fprintf('Radial coordinates for outer target Langmuir probes energy flux density data correctly converted\n');

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

            measurements_targets_experiment_file(mat_file_name_old_editions+1).edition = mat_file_name_old_editions + 1;
            measurements_targets_experiment_file(mat_file_name_old_editions+1).exp_data_namelist = exp_data;
            measurements_targets_experiment_file(mat_file_name_old_editions+1).exp_data_measurements = measurements_targets_experiment;
            save(mat_file_name,'measurements_targets_experiment_file');
            fprintf('Requested targets experimental data saved in exp_data_targets.mat, version %d, for future usage\n',mat_file_name_old_editions+1);

        else
    
            measurements_targets_experiment_file = struct;
            measurements_targets_experiment_file(1).edition = 1;
            measurements_targets_experiment_file(1).exp_data_namelist = exp_data;
            measurements_targets_experiment_file(1).exp_data_measurements = measurements_targets_experiment;
            save(mat_file_name,'measurements_targets_experiment_file');
            fprintf('Requested targets experimental data saved in exp_data_targets.mat, version 1, for future usage\n');

        end

    end

end

end

%% AUXILIARY FUNCTION TO EXTRACT VALUES

function [time_output,values_output] = extract_values(time,values,time_start,time_end,reduced_set_time_delta)

% Inputs:
%   time = array with the original time steps of the experimental data
%   values = matrix with the original values of the experimental data (must be function of 1) space dimension and 2) time dimension)
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

%% AUXILIARY FUNCTION TO SHIFT AND CONVERT COORDINATES

function [coordinate_output,data_output,data_output_unc] = shift_convert_coordinate(device,times,data_values,data_values_unc,shot,coordinate_input,z_coordinate_input,type_input,type_output,shift)

data_output = [];
data_output_unc = [];

if strcmp(type_input,type_output)

   switch type_output

       case 'rhop'

            if not(isempty(data_values))
                temp = find(data_values(1,:)==0, 1, 'first');
                if not(isempty(temp))
                    data_values(:,temp:end) = [];
                    data_values_unc(:,temp:end) = [];
                    coordinate_input(:,temp:end) = [];
                end
                data_output = data_values;
                data_output_unc = data_values_unc;
            end

            if not(isempty(shift))
                coordinate_output = coordinate_input + shift;
            else
                coordinate_output = coordinate_input;
            end

       case 'dssep'

            if not(isempty(shift))
                coordinate_output = coordinate_input + shift;
            else
                coordinate_output = coordinate_input;
            end

       case 'R'

            if not(isempty(data_values))
                temp = find(data_values(1,:)==0, 1, 'first');
                if not(isempty(temp))
                    data_values(:,temp:end) = [];
                    data_values_unc(:,temp:end) = [];
                    coordinate_input(:,temp:end) = [];
                end
                data_output = data_values;
                data_output_unc = data_values_unc;
            end

            if not(isempty(shift))
                coordinate_output = coordinate_input + shift;
            else
                coordinate_output = coordinate_input;
            end

       otherwise

           error('Error: supported coordinates in read_measurements_targets_experiment are ''rhop'', ''dssep'', ''R''');

   end

else

   switch type_input

       case 'rhop'

            if not(isempty(shift))
                coordinate_input = coordinate_input + shift;
            end

            switch type_output

                case 'dssep'

                    coordinate_output = rhop_to_dssep(device,coordinate_input,times,shot);

                case 'R'

                    coordinate_output = rhop_to_Rz(device,coordinate_input,times,shot);

            end

       case 'dssep'

            if not(isempty(shift))
                coordinate_input = coordinate_input + shift;
            end

            switch type_output

                case 'rhop'

                    coordinate_output = dssep_to_rhop(device,coordinate_input,times,shot);

                case 'R'

                    coordinate_output = dssep_to_Rz(device,coordinate_input,times,shot);

            end

       case 'R'

            if not(isempty(shift))
                coordinate_input = coordinate_input + shift;
            end

            switch type_output

                case 'rhop'

                    [coordinate_output,data_output,data_output_unc] = Rz_to_rhop(device,coordinate_input,z_coordinate_input,data_values,data_values_unc,times,shot);

                case 'dssep'

                    [coordinate_output,data_output,data_output_unc] = Rz_to_dssep(device,coordinate_input,z_coordinate_input,data_values,data_values_unc,times,shot);

            end

       otherwise

           error('Error: supported coordinates in read_measurements_targets_experiment are ''rhop'', ''dssep'', ''R''');

   end

end

end

%% AUXILIARY FUNCTIONS TO PERFORM COORDINATES MAPPING

function [rhop_output,data_output,data_output_unc] = Rz_to_rhop(device,R,z,data,data_unc,time,shot)

    switch device
    
        case 'AUG'
    
            temp = find(data(1,:)==0, 1, 'first');
            if not(isempty(temp))
                data(:,temp:end) = [];
                data_unc(:,temp:end) = [];
                R(:,temp:end) = [];
                z(:,temp:end) = [];
            end
            
            data_output = data;
            data_output_unc = data_unc;
            
            equ = EQU(shot, 'diag', 'EQH',  'tbeg', time(1), 'tend', time(end));
            rhop_output = equ.rz2rho(R, z, 't_in', time, 'coord_out', 'rho_pol', 'extrapolate', 'true');
    
    end

end

function [dssep_output,data_output,data_output_unc] = Rz_to_dssep(device,R,z,data,data_unc,time,shot)

    switch device
    
        case 'AUG'

            temp = find(data(1,:)==0, 1, 'first');
            if not(isempty(temp))
                data(:,temp:end) = [];
                data_unc(:,temp:end) = [];
                R(:,temp:end) = [];
                z(:,temp:end) = [];
            end

            data_output = data;
            data_output_unc = data_unc;

            equ = EQU(shot, 'diag', 'EQH',  'tbeg', time(1), 'tend', time(end));
            
            nt = size(R,1);
            R1 = R(1,:);
            z1 = z(1,:);
            dS = sqrt(diff(R1).^2 + diff(z1).^2);
            S1 = [0, cumsum(dS)];
            S = repmat(S1, nt, 1);

            [R_sep, z_sep] = equ.cross_surf('rho', 1.0, 'target', 'custom', 'R', R(1,:), 'Z', z(1,:), 't_in', time, 'coord_in', 'rho_pol');

            dssep_output = zeros(size(S));
            for i = 1:length(time)
                S_sep = interp1(R(i,:),S(i,:),R_sep(i),'linear','extrap');
                dssep_output(i,:) = S(i,:) - S_sep;
            end
    
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
        
            % equ = EQU(shot, 'diag', 'EQH',  'tbeg', time(1), 'tend', time(end));
            % 
            % if size(rhop,1) == 1
            %     [R_sep, z] = equ.rhoTheta2rz(1, 0, 't_in', (time(1)+time(end))/2, 'coord_in', 'rho_pol');
            %     [R_output(1,:), z] = equ.rhoTheta2rz(rhop(1,:), 0, 't_in', (time(1)+time(end))/2, 'coord_in', 'rho_pol');
            %     R_output(1,:) = R_output(1,:) - R_sep;
            % else
            %     for i = 1:length(time)
            %         [R_sep, z] = equ.rhoTheta2rz(1, 0, 't_in', time(i), 'coord_in', 'rho_pol');
            %         [R_output(i,:), z] = equ.rhoTheta2rz(rhop(i,:), 0, 't_in', time(i), 'coord_in', 'rho_pol');
            %         R_output(i,:) = R_output(i,:) - R_sep;
            %     end
            % end
    
    end

end
