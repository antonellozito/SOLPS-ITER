function plot_chords(chords,varargin)
%
% Routine to plot diagnostic chords.
% 
% Input arguments:
%
% - chords  : structure array typically read from a *.chr file, containing
% data on nchord chords
% - options : list of plot options compatible with Matlab plot command
%

for i = 1:size(chords.r,1)
    x_start = chords.r(i,1) * cos(chords.phi(i,1)/(180/pi));
    y_start = chords.r(i,1) * sin(chords.phi(i,1)/(180/pi));
    z_start = chords.z(i,1);
    x_end = chords.r(i,2) * cos(chords.phi(i,2)/(180/pi));
    y_end = chords.r(i,2) * sin(chords.phi(i,2)/(180/pi));
    z_end = chords.z(i,2);
    x = linspace(x_start,x_end,10000);
    y = linspace(y_start,y_end,10000);
    z = linspace(z_start,z_end,10000);
    for j = 1:10000
        R(j) = sqrt(x(j)^2+y(j)^2);
    end
    plot(R,z,varargin{:}); hold on;
end
