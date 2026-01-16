function flux = calc_neutral_flux(grid,uu,vv,surfaces)

uu_interp = pdeprtni(grid.nodes',grid.cells',uu');
vv_interp = pdeprtni(grid.nodes',grid.cells',vv');

grid_x = linspace(surfaces(1),surfaces(2),100);
grid_y = linspace(surfaces(3),surfaces(4),100);

[Xr,Yr,vx] = griddata(grid.nodes(:,1),grid.nodes(:,2),uu_interp,grid_x,grid_y');
[Xr,Yr,vy] = griddata(grid.nodes(:,1),grid.nodes(:,2),vv_interp,grid_x,grid_y');

h = quiver(Xr,Yr,vx,vy);

s = [surfaces(2) - surfaces(1); surfaces(4) - surfaces(3)];
surface_area = sqrt(s(1)^2+s(2)^2)*2*pi*(mean([surfaces(1),surfaces(2)]));
n = [-s(2); s(1)];
n_norm = n / norm(n);

UData = h.UData;
VData = h.VData;

for i = 1:size(UData,1)
    UData_surface(i) = UData(i,i); 
    VData_surface(i) = VData(i,i);
    v{i} = [UData_surface(i); VData_surface(i)];
    projection{i} = (dot(v{i}, n_norm)) * n_norm;
    intensity(i) = sqrt((projection{i}(1))^2+(projection{i}(2))^2);
end

flux_density = mean(intensity(1:end-1));
flux = flux_density*surface_area;

end
