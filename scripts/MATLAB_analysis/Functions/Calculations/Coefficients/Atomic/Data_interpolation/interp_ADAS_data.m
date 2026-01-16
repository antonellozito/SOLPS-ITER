function [x_interp,y_interp,data_interp] = interp_ADAS_data(x,y,data,nx_interp,ny_interp,order)

% Calculate bivariate spline for the 2D dataset 'data' with dimensions 'x','y'

knotsy = augknt(linspace(min(y),max(y),length(y)/2),order);
sp = spap2(knotsy,order,y,data);
coefsy = fnbrk(sp,'c');

knotsx = augknt(linspace(min(x),max(x),length(x)/2),order);
sp2 = spap2(knotsx,order,x,coefsy.');
coefs = fnbrk(sp2,'c').';

x_interp = linspace(min(x),max(x),nx_interp);
y_interp = linspace(min(y),max(y),ny_interp);
data_interp = spcol(knotsx,order,x_interp)*coefs*spcol(knotsy,order,y_interp).';

end

