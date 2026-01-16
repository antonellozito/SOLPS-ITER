function av = cells_average(gmtry,field,x_interval,y_interval)
%
% Computes the volume average of field into the specified volume
% given as a portion of the B2 grid
%
% av is the volume average of field along into vol
% 
% gmtry is the gmtry-struct (read from a b2fgmtry-file)
%
% field is assumed to be defined in cell centers
%
% Routine uses quadv for the actual integration.
%

% Integrate on the volume
int = sum(field(x_interval(1):x_interval(2),y_interval(1):y_interval(2)).*gmtry.vol(x_interval(1):x_interval(2),y_interval(1):y_interval(2)));
vol = sum(gmtry.vol(x_interval(1):x_interval(2),y_interval(1):y_interval(2)));

% Compute the volume average,
av = int / vol;
