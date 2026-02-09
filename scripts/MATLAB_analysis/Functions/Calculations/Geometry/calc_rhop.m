function coordinate = calc_rhop(geometry,equilibrium,region)

if not(isunstructuredgrid(geometry))

    % Structured grid

    if isnumeric(region) && isscalar(region) && mod(region,1) == 0

        radial_index = region;

    else

        switch geometry.geometry_type
    
            case {'Limiter','Lower single null'}
    
                switch region
                    case 'inner_target'
                        radial_index = 1;
                    case 'inner_midplane'
                        radial_index = geometry.imp+2;
                    case 'outer_midplane'
                        radial_index = geometry.omp+2;
                    case 'outer_target'
                        radial_index = geometry.nx;
                    otherwise
                        error(['Error: allowed radial regions for %s geometry are:\n' ...
                            '''inner_target'',''inner_midplane'',' ...
                            '''outer_midplane'',''outer_target'''],geometry.geometry_type);
                end
    
            case {'Upper single null'}
    
                switch region
                    case 'inner_target'
                        radial_index = geometry.nx;
                    case 'inner_midplane'
                        radial_index = geometry.omp+2;
                    case 'outer_midplane'
                        radial_index = geometry.imp+2;
                    case 'outer_target'
                        radial_index = 1;
                    otherwise
                        error(['Error: allowed radial regions for %s geometry are:\n' ...
                            '''inner_target'',''inner_midplane'',' ...
                            '''outer_midplane'',''outer_target'''],geometry.geometry_type);
                end
    
            case {'Connected double null','Disconnected double null'}
    
                xcut = find(diff(geometry.leftix(:,1))<1);
    
                switch region
                    case 'lower_inner_target'
                        radial_index = 1;
                    case 'inner_midplane'
                        radial_index = geometry.imp+2;
                    case 'upper_inner_target'
                        radial_index = xcut(3);
                    case 'upper_outer_target'
                        radial_index = xcut(3)+1;
                    case 'outer_midplane'
                        radial_index = geometry.omp+2;
                    case 'lower_outer_target'
                        radial_index = geometry.nx;
                    otherwise
                        error(['Error: allowed radial regions for %s geometry are:\n' ...
                            '''lower_inner_target'',''inner_midplane'',''upper_inner_target'',' ...
                            '''upper_outer_target'',''outer_midplane'',''lower_outer_target'''],geometry.geometry_type);
                end
    
            case {'Lower LFS snowflake'}
    
                xcut = find(diff(geometry.leftix(:,1))<1);
    
                switch region
                    case 'inner_target'
                        radial_index = 1;
                    case 'inner_midplane'
                        radial_index = geometry.imp+2;
                    case 'far_SOL_outer_target'
                        radial_index = xcut(4);
                    case 'secondary_outer_target'
                        radial_index = xcut(4)+1;
                    case 'outer_midplane'
                        radial_index = geometry.omp+2;
                    case 'primary_outer_target'
                        radial_index = geometry.nx;
                    otherwise
                        error(['Error: allowed radial regions for %s geometry are:\n' ...
                            '''inner_target'',''inner_midplane'',''far_SOL_outer_target'',' ...
                            '''secondary_outer_target'',''outer_midplane'',''primary_outer_target'''],geometry.geometry_type);
                end

            case {'Upper LFS snowflake'}
    
                % TODO
    
        end

    end

    coordinate_X_center(1,:) = geometry.crx_center(radial_index,:);
    coordinate_X_center(2,:) = geometry.cry_center(radial_index,:);

    radial_length = size(coordinate_X_center,2);

    R_input = geometry.crx_left(radial_index,:);
    z_input = geometry.cry_left(radial_index,:);

    [R_grid,z_grid] = meshgrid(equilibrium.R,equilibrium.z);

    % --- Find magnetic axis and separatrix flux ---
    [PF_axis, PF_sep] = find_axis_and_separatrix(equilibrium, R_grid, z_grid);

    % --- Local high-resolution grid for point evaluation (original logic) ---
    temp = equilibrium.R-min(R_input);
    temp = min(temp,0); temp(temp==0) = []; index_min_R = length(temp);
    temp = equilibrium.R-max(R_input);
    temp = max(temp,0); index_max_R = find(temp,1,'first');
    temp = equilibrium.z-min(z_input);
    temp = min(temp,0); temp(temp==0) = []; index_min_z = length(temp);
    temp = equilibrium.z-max(z_input);
    temp = max(temp,0); index_max_z = find(temp,1,'first');

    [R_grid_local,z_grid_local] = meshgrid(equilibrium.R(index_min_R:index_max_R),equilibrium.z(index_min_z:index_max_z));

    R_equilibrium = linspace(min(R_input),max(R_input),5000);
    z_equilibrium = linspace(min(z_input),max(z_input),5000);
    [R_interp,z_interp] = meshgrid(R_equilibrium,z_equilibrium);

    temp = equilibrium.PF(index_min_R:index_max_R,index_min_z:index_max_z);
    PFM_interp_temp(:,:) = interp2(R_grid_local,z_grid_local,temp',R_interp,z_interp,'spline');
    PFM_interp(:,:) = PFM_interp_temp(:,:)';

    for i = 1:length(R_input)
        [temp,R_input_index(i)] = min(abs(R_equilibrium-R_input(i)));
        [temp,z_input_index(i)] = min(abs(z_equilibrium-z_input(i)));
        PF(i) = PFM_interp(R_input_index(i),z_input_index(i));
        rho_pol(i) = sqrt(abs((PF(i)-PF_axis)/(PF_sep-PF_axis)));
    end

    coordinate = rho_pol;

else

    % Unstructured grid

    if isnumeric(region) && isscalar(region) && mod(region,1) == 0

        volumes_list = region;

    else

        switch geometry.geometry_type
    
            case {'Limiter','Lower single null','Lower single null (DDN-like grid)'}
    
                switch region
                    case 'inner_target'
                        volumes_list = geometry.cvlistl;
                    case 'inner_midplane'
                        volumes_list = geometry.cvlisti;
                    case 'outer_midplane'
                        volumes_list = geometry.cvlista;
                    case 'outer_target'
                        volumes_list = geometry.cvlistr;
                    otherwise
                        error(['Error: allowed radial regions for %s geometry are:\n' ...
                            '''inner_target'',''inner_midplane'',' ...
                            '''outer_midplane'',''outer_target'''],geometry.geometry_type);
                end
    
            case {'Upper single null','Upper single null (DDN-like grid)'}
    
                switch region
                    case 'inner_target'
                        volumes_list = geometry.cvlistr;
                    case 'inner_midplane'
                        volumes_list = geometry.cvlista;
                    case 'outer_midplane'
                        volumes_list = geometry.cvlisti;
                    case 'outer_target'
                        volumes_list = geometry.cvlistl;
                    otherwise
                        error(['Error: allowed radial regions for %s geometry are:\n' ...
                            '''inner_target'',''inner_midplane'',' ...
                            '''outer_midplane'',''outer_target'''],geometry.geometry_type);
                end
    
            case {'Connected double null','Disconnected double null'}
    
                switch region
                    case 'lower_inner_target'
                        volumes_list = geometry.cvlistl;
                    case 'inner_midplane'
                        volumes_list = geometry.cvlisti;
                    case 'upper_inner_target'
                        volumes_list = geometry.cvlisttl;
                    case 'upper_outer_target'
                        volumes_list = geometry.cvlisttr;
                    case 'outer_midplane'
                        volumes_list = geometry.cvlista;
                    case 'lower_outer_target'
                        volumes_list = geometry.cvlistr;
                    otherwise
                        error(['Error: allowed radial regions for %s geometry are:\n' ...
                            '''lower_inner_target'',''inner_midplane'',''upper_inner_target'',' ...
                            '''upper_outer_target'',''outer_midplane'',''lower_outer_target'''],geometry.geometry_type);
                end
    
            case {'Lower LFS snowflake'}
    
                switch region
                    case 'inner_target'
                        volumes_list = geometry.cvlistl;
                    case 'inner_midplane'
                        volumes_list = geometry.cvlisti;
                    case 'far_SOL_outer_target'
                        volumes_list = geometry.cvlisttl;
                    case 'secondary_outer_target'
                        volumes_list = geometry.cvlisttr;
                    case 'outer_midplane'
                        volumes_list = geometry.cvlista;
                    case 'primary_outer_target'
                        volumes_list = geometry.cvlistr;
                    otherwise
                        error(['Error: allowed radial regions for %s geometry are:\n' ...
                            '''inner_target'',''inner_midplane'',''far_SOL_outer_target'',' ...
                            '''secondary_outer_target'',''outer_midplane'',''primary_outer_target'''],geometry.geometry_type);
                end

            case {'Upper LFS snowflake'}
    
                % TODO
    
        end

    end

    coordinate_X_center(1,:) = geometry.cvX([volumes_list]);
    coordinate_X_center(2,:) = geometry.cvY([volumes_list]);

    radial_length = size(coordinate_X_center,2);

    R_input = coordinate_X_center(1,:);
    z_input = coordinate_X_center(2,:);

    [R_grid,z_grid] = meshgrid(equilibrium.R,equilibrium.z);

    % --- Find magnetic axis and separatrix flux ---
    [PF_axis, PF_sep] = find_axis_and_separatrix(equilibrium, R_grid, z_grid);

    % --- Local high-resolution grid for point evaluation (original logic) ---
    temp = equilibrium.R-min(R_input);
    temp = min(temp,0); temp(temp==0) = []; index_min_R = size(temp,1);
    temp = equilibrium.R-max(R_input);
    temp = max(temp,0); index_max_R = find(temp,1,'first');
    temp = equilibrium.z-min(z_input);
    temp = min(temp,0); temp(temp==0) = []; index_min_z = size(temp,1);
    temp = equilibrium.z-max(z_input);
    temp = max(temp,0); index_max_z = find(temp,1,'first');

    [R_grid_local,z_grid_local] = meshgrid(equilibrium.R(index_min_R:index_max_R),equilibrium.z(index_min_z:index_max_z));

    R_equilibrium = linspace(min(R_input),max(R_input),5000);
    z_equilibrium = linspace(min(z_input),max(z_input),5000);
    [R_interp,z_interp] = meshgrid(R_equilibrium,z_equilibrium);

    temp = equilibrium.PF(index_min_R:index_max_R,index_min_z:index_max_z);
    PFM_interp_temp(:,:) = interp2(R_grid_local,z_grid_local,temp',R_interp,z_interp,'spline');
    PFM_interp(:,:) = PFM_interp_temp(:,:)';

    for i = 1:size(R_input,2)
        [temp,R_input_index(i)] = min(abs(R_equilibrium-R_input(i)));
        [temp,z_input_index(i)] = min(abs(z_equilibrium-z_input(i)));
        PF(i) = PFM_interp(R_input_index(i),z_input_index(i));
        rho_pol(i) = sqrt(abs((PF(i)-PF_axis)/(PF_sep-PF_axis)));
    end

    coordinate = rho_pol;

end

end


function [PF_axis, PF_sep] = find_axis_and_separatrix(equilibrium, R_grid, z_grid)
% find_axis_and_separatrix finds the poloidal flux at the magnetic axis
% (O-point) and at the primary separatrix (X-point or limiter boundary)

    R = linspace(min(equilibrium.R), max(equilibrium.R), equilibrium.size_R * 8);
    z = linspace(min(equilibrium.z), max(equilibrium.z), equilibrium.size_z * 8);
    [R_interp, z_interp] = meshgrid(R, z);
    PFM_interp_temp = interp2(R_grid, z_grid, equilibrium.PF', R_interp, z_interp, 'spline');
    PFM_interp = PFM_interp_temp';

    PF_fun = @(r, zz) interp2(R_grid, z_grid, equilibrium.PF', r, zz, 'spline');
    eps_fd = 1e-6;
    grad2_fun = @(x) ...
        ((PF_fun(x(1)+eps_fd, x(2)) - PF_fun(x(1)-eps_fd, x(2))) / (2*eps_fd))^2 + ...
        ((PF_fun(x(1), x(2)+eps_fd) - PF_fun(x(1), x(2)-eps_fd)) / (2*eps_fd))^2;
    opts_refine = optimset('TolX', 1e-12, 'TolFun', 1e-16, 'MaxFunEvals', 5000, 'Display', 'off');

    dR = R(2) - R(1);
    dz = z(2) - z(1);
    [dPF_dR, dPF_dz] = gradient(PFM_interp', dR, dz);
    grad_mag = sqrt(dPF_dR.^2 + dPF_dz.^2);
    [d2PF_dR2, ~]  = gradient(dPF_dR, dR, dz);
    [~, d2PF_dz2]  = gradient(dPF_dz, dR, dz);
    [d2PF_dRdz, ~] = gradient(dPF_dz, dR, dz);
    hess_det = d2PF_dR2 .* d2PF_dz2 - d2PF_dRdz.^2;

    mR = round(0.05 * length(R));
    mz = round(0.05 * length(z));
    border_mask = false(size(grad_mag));
    border_mask(mz:end-mz, mR:end-mR) = true;

    grad_O = inf(size(grad_mag));
    mR_int = round(0.2 * length(R));
    mz_int = round(0.2 * length(z));
    interior_mask = false(size(grad_mag));
    interior_mask(mz_int:end-mz_int, mR_int:end-mR_int) = true;
    opoint_mask = interior_mask & (hess_det > 0);
    grad_O(opoint_mask) = grad_mag(opoint_mask);
    [~, idx_O] = min(grad_O(:));
    [iz_O, iR_O] = ind2sub(size(grad_mag), idx_O);
    x_O = fminsearch(grad2_fun, [R(iR_O), z(iz_O)], opts_refine);
    PF_axis = PF_fun(x_O(1), x_O(2));

    grad_median = median(grad_mag(:));
    grad_xpoint_thresh = 0.01 * grad_median;

    xpoint_mask = border_mask & (hess_det < 0);
    grad_X = inf(size(grad_mag));
    grad_X(xpoint_mask) = grad_mag(xpoint_mask);
    grad_X(grad_X > 0.1 * grad_median) = inf;

    xpoint_PFs = [];
    grad_X_work = grad_X;
    for ix = 1:5
        [gmin, idx_X] = min(grad_X_work(:));
        if isinf(gmin)
            break;
        end
        [iz_X, iR_X] = ind2sub(size(grad_mag), idx_X);
        x_ref = fminsearch(grad2_fun, [R(iR_X), z(iz_X)], opts_refine);
        grad_at_xpoint = sqrt(grad2_fun(x_ref));
        if grad_at_xpoint < grad_xpoint_thresh
            xpoint_PFs(end+1) = PF_fun(x_ref(1), x_ref(2));
        end
        r_blank = max(round(0.05 * length(R)), 5);
        z_blank = max(round(0.05 * length(z)), 5);
        iz_lo = max(1, iz_X - z_blank);
        iz_hi = min(size(grad_mag,1), iz_X + z_blank);
        iR_lo = max(1, iR_X - r_blank);
        iR_hi = min(size(grad_mag,2), iR_X + r_blank);
        grad_X_work(iz_lo:iz_hi, iR_lo:iR_hi) = inf;
    end

    if ~isempty(xpoint_PFs)
        [~, idx_primary] = min(abs(xpoint_PFs - PF_axis));
        PF_sep = xpoint_PFs(idx_primary);
    else
        % Limiter fallback
        PF_axis = max(PFM_interp(:));
        PF_sep = 0;
    end

end
