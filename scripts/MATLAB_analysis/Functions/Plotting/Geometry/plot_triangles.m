function h = plot_triangles(tri,varargin)
%
% Routine to plot triangle grid. Interface to Matlab triplot command.
%
% Input arguments:
%
% - triangles : struct read from fort.33, fort.34, fort.35 files
%               (function read_triangle_mesh.m)
% - options   : list of plot options compatible with Matlab triplot command
%
% Output arguments:
%
% - h       : handle to the plot object
%

h = triplot(tri.cells,tri.nodes(:,1),tri.nodes(:,2),varargin{:});
