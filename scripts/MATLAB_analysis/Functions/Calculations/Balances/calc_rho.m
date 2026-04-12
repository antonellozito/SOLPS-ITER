function x_rad = calc_rho(varargin)

if nargin < 1
    cell_region = 'center';
else
    cell_region = varargin{1};
end

if nargin < 1
    cell_region = 'center';
end

SIMULATION = evalin('base', 'SIMULATION');

geometry = read_b2fgmtry(SIMULATION);
equilibrium = read_equilibrium(SIMULATION);

radial_index = geometry.omp+2;

switch cell_region
    case 'center'
        R_input = geometry.crx_left(radial_index,:);
        z_input = geometry.cry_left(radial_index,:);
    case 'edge'
        R_input = geometry.crx(radial_index,:,3);
        z_input = geometry.cry(radial_index,:,3);
end

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

temp = length(coordinate)/2;

switch cell_region
    case 'center'
        x_rad = coordinate(temp+1:temp*2-1);
    case 'edge'
        x_rad = coordinate(temp:temp*2-1);
end
