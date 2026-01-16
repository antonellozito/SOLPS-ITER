function [rchord_out,zchord_out,phichord_out,prof_out] = line_profile(gmtry,field,chords,nint)
%
% Computes the line profile of field along the specified chords
% Chords is a structure array typically read from a *.chr file, containing
% data on nchord chords
%
% prof is a cell of lenght nchords containing the line profiles of field
% along each chord
% 
% gmtry is either a gmtry-struct (read from a b2fgmtry-file), or a
% triangles-struct (read from fort.33, fort.34, fort.35 files) 
%
% field is assumed to be defined in cell centers (in case of a plasma 
% grid), or in triangle centers (in case of a triangle grid)
% 
% nint (optional) specifies the number of intervals used per 
% chord to evaluate the line profile. Default: 1000
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
    phichord = chords.phi(i,1)*(1-t) + chords.phi(i,2)*t;
    
    % Rotate back to the poloidal plane (assuming toroidal symmetry)
    xchord = rchord .* cos(phichord./(180/pi));
    ychord = rchord .* sin(phichord./(180/pi));
    rhocord = (xchord.^2 + ychord.^2).^0.5;
  
    % Evaluate field along the chord
    prof = line_interp(gmtry,field,rhocord,zchord);

    % Neglect portions of the chords outside the solution (i.e. where prof=0)
    rchord_out{i} = rchord(prof ~= 0);
    zchord_out{i} = zchord(prof ~= 0);
    phichord_out{i} = phichord(prof ~= 0);
    prof_out{i} = prof(prof ~= 0);

end
