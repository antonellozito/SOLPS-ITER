function angle = calc_incidence_angle(geometry,target)

nx = geometry.nx;
ny = geometry.ny;
bb = geometry.bb;


dtor = pi/180;

R = input(1,:);
z = input(2,:);

inclination = inclination.*dtor;
tilt = tilt.*dtor;

for i = 1:length(tilt)
cs(i) = cos(tilt(i));
ss(i) = sin(tilt(i));
cp(i) = cos(inclination(i));
sp(i) = sin(inclination(i));
n_t(i) = ss(i)*cp(i);
n_z(i) = sp(i);
n_r(i) = cs(i)*cp(i);
end

[Btot,Br,Bz,Bt] = calculate_magnetic_field(input,diag,shot,time);

for i = 1:length(tilt)
n_dot_B(i) = n_t(i)*Bt(i) + n_z(i)*Bz(i) + n_r(i)*Br(i);
temp(i) = acos(abs(n_dot_B(i)/Btot(i)));
angle(i) = pi/2-temp(i);
angle(i) = angle(i)/dtor;
end

end
