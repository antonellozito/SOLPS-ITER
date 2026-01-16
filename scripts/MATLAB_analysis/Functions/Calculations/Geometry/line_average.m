function av = line_average(gmtry,field,chords,nint)
%
% Computes the line average of field along the specified chords
% Chords is a structure array typically read from a *.chr file, containing
% data on nchord chords
%
% av is an vector of lenght nchords containing the line average of field
% along each chord
% 
% gmtry is either a gmtry-struct (read from a b2fgmtry-file), or a
% triangles-struct (read from fort.33, fort.34, fort.35 files) 
%
% field is assumed to be defined in cell centers (in case of a plasma 
% grid), or in triangle centers (in case of a triangle grid)
% 
% nint (optional) specifies the number of intervals used per 
% chord to evaluate the line average. Default: 1000
%
% Routine uses quadv for the actual integration.
%

% Set default values for some arguments, if not supplied
if ~exist('nint','var') || isempty(nint)
  nint = 1000;
end

% Initialize output
int = zeros(size(chords.r,1),1);

% Perform integration
t = 0:1/nint:1;

for i = 1:size(chords.r,1)
    
    % 1D function along chord
    rchord = chords.r(i,1)*(1-t) + chords.r(i,2)*t;
    zchord = chords.z(i,1)*(1-t) + chords.z(i,2)*t;
    phicord = chords.phi(i,1)*(1-t) + chords.phi(i,2)*t;
    
    % Rotate back to the poloidal plane (assuming toroidal symmetry)
    xchord = rchord .* cos(phicord./(180/pi));
    ychord = rchord .* sin(phicord./(180/pi));
    rhocord = (xchord.^2 + ychord.^2).^0.5;
  
    % Evaluate field along the chord
    f = line_interp(gmtry,field,rhocord,zchord);

    % Neglect portions of the chords outside the solution (i.e. where f=0)
    xchord = xchord(f ~= 0);
    ychord = ychord(f ~= 0);
    zchord = zchord(f ~= 0);
    f = f(f ~= 0);
    
    % Integrate along chord segment, simple Simpson rule
    dx = sqrt((xchord(1) - xchord(end))^2 + ...
              (ychord(1) - ychord(end))^2 + ...
              (zchord(1) - zchord(end))^2)/(length(f)-1);
    int(i) = 0.5*sum(f(1:end-1) + f(2:end))*dx;

    % Compute the line average
    av(i) = int(i) ./ (dx*(length(f)-1));

end
