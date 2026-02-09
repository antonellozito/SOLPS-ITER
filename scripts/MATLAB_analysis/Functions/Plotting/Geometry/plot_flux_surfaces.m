function surfaces = plot_flux_surfaces(equilibrium, levels, linestyle, linewidth, color)
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
[R_grid, z_grid] = meshgrid(equilibrium.R, equilibrium.z);
R = linspace(min(equilibrium.R), max(equilibrium.R), equilibrium.size_R * 8);
z = linspace(min(equilibrium.z), max(equilibrium.z), equilibrium.size_z * 8);
[R_interp, z_interp] = meshgrid(R, z);
PFM_interp_temp = interp2(R_grid, z_grid, equilibrium.PF', R_interp, z_interp, 'spline');
PFM_interp = PFM_interp_temp'; % [nR x nZ]
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
% --- Find O-point (magnetic axis) and refine ---
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
% --- Find X-points ---
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
    % Diverted case
    [~, idx_primary] = min(abs(xpoint_PFs - PF_axis));
    PF_sep = xpoint_PFs(idx_primary);
    rho_pol = sqrt(abs((PFM_interp - PF_axis) ./ (PF_sep - PF_axis)));
else
    % Limiter case: original algorithm
    PF_axis_lim = max(PFM_interp(:));
    rho_pol = sqrt((PFM_interp - PF_axis_lim) ./ (-PF_axis_lim));
end
for i = 1:length(levels)
    [surfaces.C{i}, surfaces.h{i}] = contour(R, z, rho_pol', [levels(i) levels(i)]);
    surfaces.h{i}.LineStyle = linestyle;
    surfaces.h{i}.LineWidth = linewidth;
    surfaces.h{i}.Color = color;
end
end