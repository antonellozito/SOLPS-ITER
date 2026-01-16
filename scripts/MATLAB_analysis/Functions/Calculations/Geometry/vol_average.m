function av = vol_average(gmtry,field,vol,nint)
%
% Computes the volume average of field into the specified volume
% vol is a structure array containing the 4 vertices of the volume
%
% av is the volume average of field along into vol
% 
% gmtry is either a gmtry-struct (read from a b2fgmtry-file), or a
% triangles-struct (read from fort.33, fort.34, fort.35 files) 
%
% field is assumed to be defined in cell centers (in case of a plasma 
% grid), or in triangle centers (in case of a triangle grid)
% 
% nint (optional) specifies the number of intervals used for the 
% grid to evaluate the volume average. Default: 500
%
% Routine uses quadv for the actual integration.
%

% Set default values for some arguments, if not supplied
if ~exist('nint','var') || isempty(nint)
  nint = 200;
end

P0 = [vol.r(1) vol.z(1)];
P1 = [vol.r(2) vol.z(2)];
P2 = [vol.r(3) vol.z(3)];
P3 = [vol.r(4) vol.z(4)];

% Evaluate field into the volume
[R,z,f] = vol_interp(gmtry,field,P0,P1,P2,P3,nint);

% Integrate on the volume
ds = polyarea([R(1,1) R(2,1) R(2,2) R(1,2)],[z(1,1) z(2,1) z(2,2) z(1,2)]);
for i = 1:size(f,2)
    temp(i) = sum(f(1:end,i))*ds;
end
int = sum(temp);

% Compute the volume average, disregarding the portion of the volume which is outside the grid
av = int / (ds*(size(R,1)*size(R,2)-length(f(f==0))));
