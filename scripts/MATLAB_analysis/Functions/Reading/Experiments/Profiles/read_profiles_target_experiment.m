function [profiles_target_experiment,data_avail] = read_profiles_target_experiment(simulation)

% read_profiles_target_experiment reads the experimental target plasma profiles,
% namely electron density, electron temperature, particle flux density and energy flux density

% TODO: for AUG, add possibility of different experiments instead of the default augd

%% READ EXPERIMENTAL DATA FROM RUN DIRECTORY

try
    exp_data = read_exp_data(simulation);
    data_avail = true;
catch
    data_avail = false;
end

profiles_target_experiment = struct();

if data_avail

switch exp_data.DEVICE

case 'AUG'

%% LOAD EXPERIMENTAL DATA FOR AUG

    % Fields '*_SHOT' mean the discharge number
    % Fields '*_EXPERIMENT(S)' mean the user experiment (default: 'augd')
    % Fields '*_SOURCE(S)' mean the shotfile name

    % Load shotfiles containing diagnostic data

    if strcmp(exp_data.DATA_TARGETS_SOURCE,'LSD')

        % Langmuir probes

        [PARAMETERS,TIMEBASES,~,SIGNALS] = load_aug_shotfile(...
            exp_data.DATA_TARGETS_SOURCE, ...
            exp_data.DATA_TARGETS_SHOT);

    end

%% EXTRACT EXPERIMENTAL DATA FOR AUG

    % Extract diagnostic data

    if strcmp(exp_data.DATA_TARGETS_SOURCE,'LSD')

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

        % Time

        time = TIMEBASES.time_lsd.value;

        % Extract probe parameters - outer target
    
        position_probes_outer = struct;
        k = 1;
        for j = 1:length(PARAMETERS.position.items)
            if strcmp(PARAMETERS.position.items(j).location,'Outer divertor')
                position_probes_outer(k).name = PARAMETERS.position.items(j).name;
                position_probes_outer(k).R = PARAMETERS.position.items(j).R;
                position_probes_outer(k).z = PARAMETERS.position.items(j).z;
                k = k+1;
            end
        end

        % Extract probe parameters - inner target

        position_probes_inner = struct;
        k = 1;
        for j = 1:length(PARAMETERS.position.items)
            if strcmp(PARAMETERS.position.items(j).location,'Inner divertor')
                position_probes_inner(k).name = PARAMETERS.position.items(j).name;
                position_probes_inner(k).R = PARAMETERS.position.items(j).R;
                position_probes_inner(k).z = PARAMETERS.position.items(j).z;
                k = k+1;
            end
        end
    
        % Extract data - outer target
    
        for j = 1:length(position_probes_outer)
    
            probe_name_outer{j} = position_probes_outer(j).name;
    
            signal_name{j} = append('ne_',probe_name_outer{j});
            data_ne_outer(j,:) = SIGNALS.(signal_name{j}).value;
    
            signal_name{j} = append('te_',probe_name_outer{j});
            data_Te_outer(j,:) = SIGNALS.(signal_name{j}).value;
    
            signal_name{j} = append('ang_',probe_name_outer{j});
            data_ang_outer(j,:) = SIGNALS.(signal_name{j}).value;
    
            data_cs_outer(j,:) = sqrt((qe*(gamma_e.*data_Te_outer(j,:)+gamma_i.*(2.*data_Te_outer(j,:))))./(2*mp));
            data_gamma_outer(j,:) = data_ne_outer(j,:).*data_cs_outer(j,:).*sin((pi/180).*data_ang_outer(j,:));
    
            sheath_coeff_el = 2/(1-delta_e)-0.5*log((2*pi*(me/(2*mp)))*(1+2)*((1-delta_e)^(-2)))+0.5;
            sheath_coeff_ion = 2;
            data_E0(j,:) = sheath_coeff_ion.*(2.*data_Te_outer(j,:)) + 2.85.*data_Te_outer(j,:);
            data_epsilon(j,:) = data_E0(j,:)./epsilon_L;
            data_R_e(j,:) = ((refl_coeffs(1)).*data_epsilon(j,:).^(refl_coeffs(2)))./(1+refl_coeffs(3).*data_epsilon(j,:).^(refl_coeffs(4)));
            data_sheath_coeff_outer(j,:) = (2*sheath_coeff_ion*(1-data_R_e(j,:))+sheath_coeff_el-2.85.*data_R_e(j,:));
            data_q_outer(j,:) = data_gamma_outer(j,:).*((data_sheath_coeff_outer(j,:).*data_Te_outer(j,:)+ion_energy+diss_energy)*qe)./1e6; 
        
        end

        profiles_target_experiment.ne_outer_data.name = exp_data.DATA_TARGETS_NAME_DISPLAY;
        [profiles_target_experiment.ne_outer_data.times,profiles_target_experiment.ne_outer_data.values] = ...
            extract_values(time, data_ne_outer,...
            exp_data.DATA_TARGETS_TIME_START,exp_data.DATA_TARGETS_TIME_END,...
            exp_data.DATA_TARGETS_REDUCED_SET,exp_data.DATA_TARGETS_REDUCED_SET_TIME_DELTA);

        profiles_target_experiment.Te_outer_data.name = exp_data.DATA_TARGETS_NAME_DISPLAY;
        [profiles_target_experiment.Te_outer_data.times,profiles_target_experiment.Te_outer_data.values] = ...
            extract_values(time, data_Te_outer,...
            exp_data.DATA_TARGETS_TIME_START,exp_data.DATA_TARGETS_TIME_END,...
            exp_data.DATA_TARGETS_REDUCED_SET,exp_data.DATA_TARGETS_REDUCED_SET_TIME_DELTA);

        profiles_target_experiment.gamma_outer_data.name = exp_data.DATA_TARGETS_NAME_DISPLAY;
        [profiles_target_experiment.gamma_outer_data.times,profiles_target_experiment.gamma_outer_data.values] = ...
            extract_values(time, data_gamma_outer,...
            exp_data.DATA_TARGETS_TIME_START,exp_data.DATA_TARGETS_TIME_END,...
            exp_data.DATA_TARGETS_REDUCED_SET,exp_data.DATA_TARGETS_REDUCED_SET_TIME_DELTA);

        profiles_target_experiment.q_outer_data.name = exp_data.DATA_TARGETS_NAME_DISPLAY;
        [profiles_target_experiment.q_outer_data.times,profiles_target_experiment.q_outer_data.values] = ...
            extract_values(time, data_q_outer,...
            exp_data.DATA_TARGETS_TIME_START,exp_data.DATA_TARGETS_TIME_END,...
            exp_data.DATA_TARGETS_REDUCED_SET,exp_data.DATA_TARGETS_REDUCED_SET_TIME_DELTA);

        % Extract data - inner target
    
        for j = 1:length(position_probes_inner)
    
            probe_name_inner{j} = position_probes_inner(j).name;
    
            signal_name{j} = append('ne_',probe_name_inner{j});
            data_ne_inner(j,:) = SIGNALS.(signal_name{j}).value;
    
            signal_name{j} = append('te_',probe_name_inner{j});
            data_Te_inner(j,:) = SIGNALS.(signal_name{j}).value;
    
            signal_name{j} = append('ang_',probe_name_inner{j});
            data_ang_inner(j,:) = SIGNALS.(signal_name{j}).value;
    
            data_cs_inner(j,:) = sqrt((qe*(gamma_e.*data_Te_inner(j,:)+gamma_i.*(2.*data_Te_inner(j,:))))./(2*mp));
            data_gamma_inner(j,:) = data_ne_inner(j,:).*data_cs_inner(j,:).*sin((pi/180).*data_ang_inner(j,:));
    
            sheath_coeff_el = 2/(1-delta_e)-0.5*log((2*pi*(me/(2*mp)))*(1+2)*((1-delta_e)^(-2)))+0.5;
            sheath_coeff_ion = 2;
    
            data_E0(j,:) = sheath_coeff_ion.*(2.*data_Te_inner(j,:)) + 2.85.*data_Te_inner(j,:);
            data_epsilon(j,:) = data_E0(j,:)./epsilon_L;
            data_R_e(j,:) = ((refl_coeffs(1)).*data_epsilon(j,:).^(refl_coeffs(2)))./(1+refl_coeffs(3).*data_epsilon(j,:).^(refl_coeffs(4)));
            data_sheath_coeff_inner(j,:) = (2*sheath_coeff_ion*(1-data_R_e(j,:))+sheath_coeff_el-2.85.*data_R_e(j,:));
            data_q_inner(j,:) = data_gamma_inner(j,:).*((data_sheath_coeff_inner(j,:).*data_Te_inner(j,:)+ion_energy+diss_energy)*qe)./1e6;
    
        end

        profiles_target_experiment.ne_inner_data.name = exp_data.DATA_TARGETS_NAME_DISPLAY;
        [profiles_target_experiment.ne_inner_data.times,profiles_target_experiment.ne_inner_data.values] = ...
            extract_values(time, data_ne_inner,...
            exp_data.DATA_TARGETS_TIME_START,exp_data.DATA_TARGETS_TIME_END,...
            exp_data.DATA_TARGETS_REDUCED_SET,exp_data.DATA_TARGETS_REDUCED_SET_TIME_DELTA);

        profiles_target_experiment.Te_inner_data.name = exp_data.DATA_TARGETS_NAME_DISPLAY;
        [profiles_target_experiment.Te_inner_data.times,profiles_target_experiment.Te_inner_data.values] = ...
            extract_values(time, data_Te_inner,...
            exp_data.DATA_TARGETS_TIME_START,exp_data.DATA_TARGETS_TIME_END,...
            exp_data.DATA_TARGETS_REDUCED_SET,exp_data.DATA_TARGETS_REDUCED_SET_TIME_DELTA);

        profiles_target_experiment.gamma_inner_data.name = exp_data.DATA_TARGETS_NAME_DISPLAY;
        [profiles_target_experiment.gamma_inner_data.times,profiles_target_experiment.gamma_inner_data.values] = ...
            extract_values(time, data_gamma_inner,...
            exp_data.DATA_TARGETS_TIME_START,exp_data.DATA_TARGETS_TIME_END,...
            exp_data.DATA_TARGETS_REDUCED_SET,exp_data.DATA_TARGETS_REDUCED_SET_TIME_DELTA);

        profiles_target_experiment.q_inner_data.name = exp_data.DATA_TARGETS_NAME_DISPLAY;
        [profiles_target_experiment.q_inner_data.times,profiles_target_experiment.q_inner_data.values] = ...
            extract_values(time, data_q_inner,...
            exp_data.DATA_TARGETS_TIME_START,exp_data.DATA_TARGETS_TIME_END,...
            exp_data.DATA_TARGETS_REDUCED_SET,exp_data.DATA_TARGETS_REDUCED_SET_TIME_DELTA);

    end

%% CALCULATE COORDINATES FOR AUG

    % Calculate coordinates for diagnostic data

    if strcmp(exp_data.DATA_TARGETS_SOURCE,'LSD')

        % Langmuir probes - outer target

        for j = 1:length(position_probes_outer)
            R_outer(j) = position_probes_outer(j).R;
            z_outer(j) = position_probes_outer(j).z;
        end

        profiles_target_experiment.ne_outer_data.rho = ...
            Rz_to_rho(R_outer',z_outer',profiles_target_experiment.ne_outer_data.times,exp_data.DATA_TARGETS_SHOT);

        profiles_target_experiment.ne_outer_data.rho = profiles_target_experiment.ne_outer_data.rho + ...
            exp_data.DATA_TARGETS_SEPARATRIX_SHIFT;

        profiles_target_experiment.Te_outer_data.rho = profiles_target_experiment.ne_outer_data.rho;

        profiles_target_experiment.gamma_outer_data.rho = profiles_target_experiment.ne_outer_data.rho;

        profiles_target_experiment.q_outer_data.rho = profiles_target_experiment.ne_outer_data.rho;

        % Langmuir probes - inner target

        for j = 1:length(position_probes_inner)
            R_inner(j) = position_probes_inner(j).R;
            z_inner(j) = position_probes_inner(j).z;
        end

        profiles_target_experiment.ne_inner_data.rho = ...
            Rz_to_rho(R_inner',z_inner',profiles_target_experiment.ne_inner_data.times,exp_data.DATA_TARGETS_SHOT);

        profiles_target_experiment.ne_inner_data.rho = profiles_target_experiment.ne_inner_data.rho + ...
            exp_data.DATA_TARGETS_SEPARATRIX_SHIFT;

        profiles_target_experiment.Te_inner_data.rho = profiles_target_experiment.ne_inner_data.rho;

        profiles_target_experiment.gamma_inner_data.rho = profiles_target_experiment.ne_inner_data.rho;

        profiles_target_experiment.q_inner_data.rho = profiles_target_experiment.ne_inner_data.rho;

    end

case 'JET'

%% LOAD EXPERIMENTAL DATA FOR JET

% TODO

%% EXTRACT EXPERIMENTAL DATA FOR JET

% TODO

%% CALCULATE COORDINATES FOR JET

% TODO

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

%% AUXILIARY FUNCTION TO EXTRACT RHO COORDINATE

function rho_output = Rz_to_rho(R,z,time,shot)

    Rz_cell = {}; time_cell = {};

    for i = 1:(length(time)-1)
        Rz_cell{end+1} = [R';z'];
        time_cell{end+1} = [time(i) time(i+1)];
    end
    [~,rho_temp] = map_equilibrium('rzPF',Rz_cell,'H',shot,time_cell);
    for i = 1:(length(time)-1)
          rho(:,i) = rho_temp{i};
    end

    rho_output = rho';

end
