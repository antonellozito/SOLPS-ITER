function val = isplasmagrid(gmtry)
%
% Function that checks whether the structure gmtry contains the necessary
% fields to be a 'plasma grid' from B2.5
%
% For now, the routine simply checks whether the structure contains the
% fields typically needed for the plotting routines. No consistency
% checking on the data is done
%
% Returns 1 if gmtry is a plasma grid, 0 otherwise
%

val = 0;
if isfield(gmtry,'crx') && isfield(gmtry,'cry')
    val = 1;
end