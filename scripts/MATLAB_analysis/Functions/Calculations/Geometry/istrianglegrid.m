function val = istrianglegrid(triangles)
%
% Function that checks whether the structure triangles contains the 
% necessary fields to be a 'triangle grid' from Eirene
%
% For now, the routine simply checks whether the structure contains the
% fields typically needed for the plotting routines. No consistency
% checking on the data is done
%
% Returns 1 if triangles is a triangle grid, 0 otherwise.
%

val = 0;
if isfield(triangles,'nodes') && isfield(triangles,'cells')
    val = 1;
end