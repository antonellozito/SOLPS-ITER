function surfaces = plot_flux_surfaces(equilibrium,levels,linestyle,linewidth,color)

% plot_flux_surfaces plots the magnetic flux surfaces (contour levels at constant
% rho_poloidal) from the equilibrium file on which the B2.5 grid is based
%
% Syntax : plot_flux_surfaces(equilibrium,levels,linestyle,linewidth,color)
%
%  equilibrium:     structure containing data from the equilibrium file
%
%  levels:          vector containing the contour levels of rho_poloidal to be plotted
%
%  linestyle:       linestyle of contour levels
%
%  linewidth:       linewidth of contour levels
%
%  color:           color of contour levels

[R_grid,z_grid] = meshgrid(equilibrium.R,equilibrium.z);

R = linspace(min(equilibrium.R),max(equilibrium.R),equilibrium.size_R*8);
z = linspace(min(equilibrium.z),max(equilibrium.z),equilibrium.size_z*8);
[R_interp,z_interp] = meshgrid(R,z);

PFM_interp_temp = interp2(R_grid, z_grid, equilibrium.PF', R_interp, z_interp, 'spline');
PFM_interp      = PFM_interp_temp';

PF_axis = max(PFM_interp(:));
rho_pol = sqrt((PFM_interp - PF_axis) ./ (-PF_axis));

for i = 1:length(levels)
    [surfaces.C{i},surfaces.h{i}] = contour(R,z,rho_pol',[levels(i) levels(i)]);
    surfaces.h{i}.LineStyle = linestyle;
    surfaces.h{i}.LineWidth = linewidth;
    surfaces.h{i}.Color = color;
end

end