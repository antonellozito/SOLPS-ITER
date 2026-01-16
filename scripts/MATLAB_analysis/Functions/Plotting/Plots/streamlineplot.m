function h = streamlineplot(grid,uu,vv,startx,starty,linewidth,linestyle,color)
%
% Routine to make streamline plot of the velocity field (uu,vv), where uu
% is the poloidal velocity and vv the radial velocity defined in cell
% centers of grid.
% 
% If starting points are not supplied, 15 streamlines starting at the
% separatrix are followed.
% 
% Input arguments:
%
% - grid   : struct read from b2fgmtry or triangles files
% - uu     : poloidal velocity component (cell centered)
% - vv     : radial velocity component (cell centered)
% - startx : vector with R-coords of streamlines to be followed (optional)
% - starty : vector with Z-coords of streamlines to be followed (optional)
% - linewidth : adjusts the linewidth of the streamlines (optional)
% - linestyle : adjusts the linestyle of the streamlines (optional)
% - color     : adjusts a fixed color of the streamlines (optional)
%
% Output arguments:
%
% - h      : handle to the streamline plot
%

% Check current status of hold
hs = ishold;

if isplasmagrid(grid)

    % If start positions are not supplied, launch 15 streamlines spread around
    % separatrix
    if ~exist('startx','var') || isempty(startx)
        d   = (size(grid.vol,1)-2)/16;
        xsep = floor([d:d:size(grid.vol,1)]);
        ysep = grid.topcut+2; 
        startx  = 0.5*(grid.crx(xsep,ysep,1) + grid.crx(xsep,ysep,2));
        starty  = 0.5*(grid.cry(xsep,ysep,1) + grid.cry(xsep,ysep,2));
    end
    
    % Create Cartesian mesh for streamline plot
    xmin = min(min(min(grid.crx)));
    xmax = max(max(max(grid.crx)));
    ymin = min(min(min(grid.cry)));
    ymax = max(max(max(grid.cry)));
    xI   = [xmin:(xmax-xmin)/200:xmax];
    yI   = [ymin:(ymax-ymin)/400:ymax]';
    
    % Compute poloidal and radial unit vectors in cell centers
    [epx,epy,erx,ery] = mshproj(grid);
    
    % Project velocities onto Cartesian directions
    vx = uu.*epx + vv.*erx;
    vy = uu.*epy + vv.*ery;
    
    % Interpolate flow field to Cartesian mesh
    vxI = line_interp(grid,vx,repmat(xI,length(yI),1),repmat(yI,1,length(xI)));
    vyI = line_interp(grid,vy,repmat(xI,length(yI),1),repmat(yI,1,length(xI)));
    
    % Streamline plot
    h = streamline(xI,yI,vxI,vyI,startx,starty); hold on;
    plot(startx,starty,'ro');

    if exist('linewidth','var')
         for i = 1:length(h)
            h(i).LineWidth = linewidth;
         end
    end
    if exist('linestyle','var')
         for i = 1:length(h)
            h(i).LineStyle = linestyle;
         end
    end
    if exist('color','var')
         for i = 1:length(h)
            h(i).Color = color;
         end
    end

elseif istrianglegrid(grid)

    uu_interp = pdeprtni(grid.nodes',grid.cells',uu');
    vv_interp = pdeprtni(grid.nodes',grid.cells',vv');

    unique_x = unique(grid.nodes(:,1));
    unique_y = unique(grid.nodes(:,2));

    grid_x = linspace(min(unique_x),max(unique_x),500);
    grid_y = linspace(min(unique_y),max(unique_y),500);

    [Xr,Yr,vx] = griddata(grid.nodes(:,1),grid.nodes(:,2),uu_interp,grid_x,grid_y');
    [Xr,Yr,vy] = griddata(grid.nodes(:,1),grid.nodes(:,2),vv_interp,grid_x,grid_y');
    
    % Streamline plot
    h = streamline(grid_x,grid_y,vx,vy,startx,starty); hold on;
    plot(startx,starty,'ro');

else
    
    error('Error: streamlineplot: wrong geometric structure');

end
    
% Reset status of hold
if ~hs, hold off; end;
