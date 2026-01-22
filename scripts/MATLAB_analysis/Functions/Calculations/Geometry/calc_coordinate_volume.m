function coordinate = calc_coordinate_volume(geometry,equilibrium,coordinate_type,distance,region,cell_index)

% TODO: fix calculation of rho for upper divertor
% TODO: continue adaptation for WG code

if NREG(1) == 2
    geometry.geometry_type = 'Limiter';
elseif NREG(1) == 4
    geometry.geometry_type = 'Single null';
elseif NREG(1) == 8 && (NREG(2) == 12 || NREG(2) == 26)
    geometry.geometry_type = 'Connected double null';
elseif NREG(1) == 8 && (NREG(2) == 13 || NREG(2) == 27)
    geometry.geometry_type = 'Disconnected double null';
elseif NREG(1) == 7
    geometry.geometry_type = 'LFS snowflake';
end

%% CALCULATION FOR STRUCTURED GRID

if not(isunstructuredgrid(geometry))

    switch coordinate_type

        case 'radial'

            if not(strcmp(region,'none'))
                switch region
                    case 'inner_target'
                        radial_index = 1;
                    case 'inner_X_point'
                        radial_index = geometry.leftcut+2;
                    case 'inner_midplane'
                        radial_index = geometry.imp+2;
                    case 'top'
                        radial_index = geometry.leftcut+2+((geometry.rightcut+2)-(geometry.leftcut+2))/2;
                    case 'outer_midplane'
                        radial_index = geometry.omp+2;
                    case 'outer_X_point'
                        radial_index = geometry.rightcut+1;
                    case 'outer_target'
                        radial_index = geometry.nx;
                    otherwise
                        error(['Error: allowed special radial regions in calc_coordinate are:\n' ...
                            '''inner_target'',''inner_X_point'',''inner_midplane'',''top'',' ...
                            '''outer_midplane'',''outer_X_point'',''outer_target'''])
                end
            else
                radial_index = cell_index;
            end

            coordinate_X_center(1,:) = geometry.crx_center(radial_index,:);
            coordinate_X_center(2,:) = geometry.cry_center(radial_index,:);
            coordinate_X_left_face(1,:) = geometry.crx_left(radial_index,:);
            coordinate_X_left_face(2,:) = geometry.cry_left(radial_index,:);
            coordinate_X_bottom_face(1,:) = geometry.crx_bottom(radial_index,:);
            coordinate_X_bottom_face(2,:) = geometry.cry_bottom(radial_index,:);

            switch distance

                case 'rho'

                    radial_length = size(coordinate_X_center,2);

                    R_input = geometry.crx_left(radial_index,:);
                    z_input = geometry.cry_left(radial_index,:);

                    [R_grid_points,z_grid_points] = meshgrid(equilibrium.R,equilibrium.z);

                    R_points = linspace(min(equilibrium.R),max(equilibrium.R),equilibrium.size_R*32);
                    z_points = linspace(min(equilibrium.z),max(equilibrium.z),equilibrium.size_z*32);
                    [R_interp_points,z_interp_points] = meshgrid(R_points,z_points);

                    temp = equilibrium.PF;
                    PFM_interp_temp_points(:,:) = interp2(R_grid_points,z_grid_points,temp',R_interp_points,z_interp_points,'spline');
                    PFM_interp_points(:,:) = PFM_interp_temp_points(:,:)';

                    PF_axis = max(max(PFM_interp_points));

                    temp = equilibrium.R-min(R_input);
                    temp = min(temp,0); temp(temp==0) = []; index_min_R = length(temp);
                    temp = equilibrium.R-max(R_input);
                    temp = max(temp,0); index_max_R = find(temp,1,'first');
                    temp = equilibrium.z-min(z_input);
                    temp = min(temp,0); temp(temp==0) = []; index_min_z = length(temp);
                    temp = equilibrium.z-max(z_input);
                    temp = max(temp,0); index_max_z = find(temp,1,'first');

                    [R_grid,z_grid] = meshgrid(equilibrium.R(index_min_R:index_max_R),equilibrium.z(index_min_z:index_max_z));

                    R_equilibrium = linspace(min(R_input),max(R_input),5000);
                    z_equilibrium = linspace(min(z_input),max(z_input),5000);
                    [R_interp,z_interp] = meshgrid(R_equilibrium,z_equilibrium);

                    temp = equilibrium.PF(index_min_R:index_max_R,index_min_z:index_max_z);
                    PFM_interp_temp(:,:) = interp2(R_grid,z_grid,temp',R_interp,z_interp,'spline');
                    PFM_interp(:,:) = PFM_interp_temp(:,:)';

                    for i = 1:length(R_input)
                        [temp,R_input_index(i)] = min(abs(R_equilibrium-R_input(i)));
                        [temp,z_input_index(i)] = min(abs(z_equilibrium-z_input(i)));
                        PF(i) = PFM_interp(R_input_index(i),z_input_index(i));
                        rho_pol(i) = sqrt((PF(i)-PF_axis)/(-PF_axis));
                    end

                    coordinate = rho_pol;

                case 'ds'

                    radial_length = size(coordinate_X_center,2);

                    R_separatrix = coordinate_X_bottom_face(1,radial_length/2+1);
                    z_separatrix = coordinate_X_bottom_face(2,radial_length/2+1);

                    coordinate = zeros(1,radial_length);

                    coordinate(radial_length/2) = -sqrt((R_separatrix-coordinate_X_center(1,radial_length/2))^2+(z_separatrix-coordinate_X_center(2,radial_length/2))^2);
                    coordinate(radial_length/2+1) = sqrt((coordinate_X_center(1,radial_length/2+1)-R_separatrix)^2+(coordinate_X_center(2,radial_length/2+1)-z_separatrix)^2);

                    i = radial_length/2-1;
                    while i>0
                        coordinate(i) = coordinate(i+1)-sqrt((coordinate_X_center(1,i+1)-coordinate_X_center(1,i))^2+(coordinate_X_center(2,i+1)-coordinate_X_center(2,i))^2);
                        i = i-1;
                    end

                    i = radial_length/2+2;
                    while i<radial_length+1
                        coordinate(i) = coordinate(i-1)+sqrt((coordinate_X_center(1,i)-coordinate_X_center(1,i-1))^2+(coordinate_X_center(2,i)-coordinate_X_center(2,i-1))^2);
                        i = i+1;
                    end

                otherwise

                    error('Error: allowed special radial distances in calc_coordinate are: ''rho'',''ds''')

            end

        case 'poloidal'

            if not(strcmp(region,'none'))
                switch region
                    case 'core_boundary'
                        error('Error: core boundary still to do in calc_coordinate')
                    case 'separatrix'
                        poloidal_index = geometry.sep+2;
                    case 'wall_boundary'
                        error('Error: Wall boundary still to do in calc_coordinate')
                    otherwise
                        error('Error: allowed special poloidal regions in calc_coordinate are:\n''core_boundary '',''separatrix'',''wall_boundary''')
                end
            else
                poloidal_index = cell_index;

            end

            switch distance

                case 'inner'

                    coordinate = geometry.dspol(:,poloidal_index);

                case 'outer'

                    coordinate = geometry.dspol(:,poloidal_index)-geometry.dspoledge(end,poloidal_index);

                otherwise
                    error('Error: allowed special poloidal distances in calc_coordinate are: ''inner'',''outer''')

            end

        case 'parallel'

            if not(strcmp(region,'none'))
                switch region
                    case 'core_boundary'
                        error('Error: core boundary still to do in calc_coordinate')
                    case 'separatrix'
                        poloidal_index = geometry.sep+2;
                    case 'wall_boundary'
                        error('Error: Wall boundary still to do in calc_coordinate')
                    otherwise
                        error('Error: allowed special parallel regions in calc_coordinate are:\n''core_boundary '',''separatrix'',''wall_boundary''')
                end
            else
                poloidal_index = cell_index;
            end

            switch distance

                case 'inner'

                    coordinate = geometry.dspar(:,poloidal_index);

                case 'outer'

                    coordinate = geometry.dspar(:,poloidal_index)-geometry.dsparedge(end,poloidal_index);

                otherwise
                    error('Error: allowed special parallel distances in calc_coordinate are: ''inner'',''outer''')

            end

    end

%% CALCULATION FOR UNSTRUCTURED GRID

else

    switch coordinate_type

        case 'radial'

            if not(strcmp(region,'none'))
                switch region
                    case 'inner_target'
                        volumes_list = geometry.cvlistl;
                        faces_list = geometry.fclistl;
                        coordinate_ds = geometry.dsl;
                    case 'inner_X_point'
                        error('Error: Still to convert in calc_coordinate for unstructured grids')
                    case 'inner_midplane'
                        volumes_list = geometry.cvlisti;
                        faces_list = geometry.cvlisti;
                        coordinate_ds = geometry.dsi;
                    case 'top'
                        error('Error: Still to convert in calc_coordinate for unstructured grids')
                    case 'outer_midplane'
                        volumes_list = geometry.cvlista;
                        faces_list = geometry.cvlista;
                        coordinate_ds = geometry.dsa;
                    case 'outer_X_point'
                        error('Error: Still to convert in calc_coordinate for unstructured grids')
                    case 'outer_target'
                        volumes_list = geometry.cvlistr;
                        faces_list = geometry.fclistr;
                        coordinate_ds = geometry.dsr;
                    otherwise
                        error(['Error: allowed special radial regions in calc_coordinate are:\n' ...
                            '''inner_target'',''inner_X_point'',''inner_midplane'',''top'',' ...
                            '''outer_midplane'',''outer_X_point'',''outer_target'''])
                end
            else
                volumes_list = cell_index;
            end

            coordinate_X_center(1,:) = geometry.cvX([volumes_list]);
            coordinate_X_center(2,:) = geometry.cvY([volumes_list]);

            switch distance

                case 'rho'

                    radial_length = size(coordinate_X_center,2);

                    R_input = coordinate_X_center(1,:);
                    z_input = coordinate_X_center(2,:);

                    [R_grid_points,z_grid_points] = meshgrid(equilibrium.R,equilibrium.z);

                    R_points = linspace(min(equilibrium.R),max(equilibrium.R),equilibrium.size_R*32);
                    z_points = linspace(min(equilibrium.z),max(equilibrium.z),equilibrium.size_z*32);
                    [R_interp_points,z_interp_points] = meshgrid(R_points,z_points);

                    temp = equilibrium.PF;
                    PFM_interp_temp_points(:,:) = interp2(R_grid_points,z_grid_points,temp',R_interp_points,z_interp_points,'spline');
                    PFM_interp_points(:,:) = PFM_interp_temp_points(:,:)';

                    PF_axis = max(max(PFM_interp_points));

                    temp = equilibrium.R-min(R_input);
                    temp = min(temp,0); temp(temp==0) = []; index_min_R = size(temp,1);
                    temp = equilibrium.R-max(R_input);
                    temp = max(temp,0); index_max_R = find(temp,1,'first');
                    temp = equilibrium.z-min(z_input);
                    temp = min(temp,0); temp(temp==0) = []; index_min_z = size(temp,1);
                    temp = equilibrium.z-max(z_input);
                    temp = max(temp,0); index_max_z = find(temp,1,'first');

                    [R_grid,z_grid] = meshgrid(equilibrium.R(index_min_R:index_max_R),equilibrium.z(index_min_z:index_max_z));

                    R_equilibrium = linspace(min(R_input),max(R_input),5000);
                    z_equilibrium = linspace(min(z_input),max(z_input),5000);
                    [R_interp,z_interp] = meshgrid(R_equilibrium,z_equilibrium);

                    temp = equilibrium.PF(index_min_R:index_max_R,index_min_z:index_max_z);
                    PFM_interp_temp(:,:) = interp2(R_grid,z_grid,temp',R_interp,z_interp,'spline');
                    PFM_interp(:,:) = PFM_interp_temp(:,:)';

                    for i = 1:size(R_input,2)
                        [temp,R_input_index(i)] = min(abs(R_equilibrium-R_input(i)));
                        [temp,z_input_index(i)] = min(abs(z_equilibrium-z_input(i)));
                        PF(i) = PFM_interp(R_input_index(i),z_input_index(i));
                        rho_pol(i) = sqrt((PF(i)-PF_axis)/(-PF_axis));
                    end

                    coordinate = rho_pol;

                case 'ds'

                    coordinate = coordinate_ds;
                    radial_length = size(coordinate_X_center,2);

                otherwise

                    error('Error: allowed special radial distances in calc_coordinate are: ''rho'',''ds''')

            end

        case 'poloidal'

            error('Error: Calculation of poloidal coordinates still to convert in calc_coordinate for unstructured grids')

        case 'parallel'

            error('Error: Calculation of parallel coordinates still to convert in calc_coordinate for unstructured grids')

    end

end

end
