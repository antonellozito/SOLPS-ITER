function [hs,hq] = quiverstreamlineplot_multiple(grid,uu_multiple,vv_multiple,startx,starty,linewidth_streamlines,linestyle_streamlines,color_streamlines,normalize,scale,linewidth_arrows,color_arrows,colormap_arrows,fmin,fmax)
%
% Routine to make combined quiver and streamline plot of the velocity field (uu,vv)
% 
% Input arguments:
%
% - grid            : struct read from triangles files
% - uu              : x velocity component (cell centered)
% - vv              : y velocity component (cell centered)
% - startx          : vector with R-coords of streamlines to be followed (optional)
% - starty          : vector with Z-coords of streamlines to be followed (optional)
% - linewidth_streamlines : adjusts the linewidth of the streamlines (optional)
% - linestyle_streamlines : adjusts the linestyle of the streamlines (optional)
% - color_streamlines     : adjusts a fixed color of the streamlines (optional)
% - normalize       : select wether normalize the length of the arrows (optional)
% - scale           : adjusts the length of the arrows (optional)
% - linewidth_arrows : adjusts the linewidth of the arrows (optional)
% - color_arrows    : adjusts a fixed color of the arrows (optional)
% - colormap_arrows : adjusts a variable color of the arrows as function of their magnitude (optional)
% - fmin            : min. arrow color, in case of colormap (optional)
% - fmax            : max. arrow color, in case of colormap (optional)
%
% Output arguments:
%
% - hs              : handle to the streamline plot
% - hq              : handle to the quiver plot
%

% Check current status of hold
hss = ishold;

if istrianglegrid(grid)

    for k = 1:length(uu_multiple)
        uu = uu_multiple{k};
        vv = vv_multiple{k};

        uu_interp = pdeprtni(grid.nodes',grid.cells',uu');
        vv_interp = pdeprtni(grid.nodes',grid.cells',vv');
    
        unique_x = unique(grid.nodes(:,1));
        unique_y = unique(grid.nodes(:,2));
    
        grid_x = linspace(min(unique_x),max(unique_x),2000);
        grid_y = linspace(min(unique_y),max(unique_y),2000);
    
        [Xr,Yr,vx] = griddata(grid.nodes(:,1),grid.nodes(:,2),uu_interp,grid_x,grid_y');
        [Xr,Yr,vy] = griddata(grid.nodes(:,1),grid.nodes(:,2),vv_interp,grid_x,grid_y');
    
        % Streamline plot
        hs = streamline(grid_x,grid_y,vx,vy,startx,starty); hold on;
        plot(startx,starty,'ro');

        if exist('linewidth_streamlines','var')
             for i = 1:length(hs)
                hs(i).LineWidth = linewidth_streamlines;
             end
        end
        if exist('linestyle_streamlines','var')
             for i = 1:length(hs)
                hs(i).LineStyle = linestyle_streamlines;
             end
        end
        if exist('color_streamlines','var')
             for i = 1:length(hs)
                hs(i).Color = color_streamlines;
             end
        end

    end

    % Quiver plot

    x_points = [];
    y_points = [];
    vx_points = [];
    vy_points = [];
    
    for k = 1:length(uu_multiple)

        uu = uu_multiple{k};
        vv = vv_multiple{k};

        uu_interp = pdeprtni(grid.nodes',grid.cells',uu');
        vv_interp = pdeprtni(grid.nodes',grid.cells',vv');
    
        unique_x = unique(grid.nodes(:,1));
        unique_y = unique(grid.nodes(:,2));
    
        grid_x = linspace(min(unique_x),max(unique_x),2000);
        grid_y = linspace(min(unique_y),max(unique_y),2000);
    
        [Xr,Yr,vx] = griddata(grid.nodes(:,1),grid.nodes(:,2),uu_interp,grid_x,grid_y');
        [Xr,Yr,vy] = griddata(grid.nodes(:,1),grid.nodes(:,2),vv_interp,grid_x,grid_y');

        x_points = [x_points,startx];
        y_points = [y_points,starty];

        for i = 1:length(startx)
            [d,ix] = min(abs(grid_x-startx(i)));
            [d,iy] = min(abs(grid_y-starty(i)));
            vx_points = [vx_points, vx(iy,ix)];
            vy_points = [vy_points, vy(iy,ix)];
        end

    end

    v = sqrt(vx_points.^2+vy_points.^2);

    vxn=(vx_points./sqrt(vx_points.^2+vy_points.^2))./2;
    vyn=(vy_points./sqrt(vx_points.^2+vy_points.^2))./2;

    if normalize
        hq = quiver(x_points,y_points,vxn,vyn,scale,...
            'LineWidth',linewidth_arrows,...
            'Color',color_arrows);
    else
        hq = quiver(x_points,y_points,vx_points,vy_points,scale,...
            'LineWidth',linewidth_arrows,...
            'Color',color_arrows);
    end

    if exist('colormap_arrows','var') && ~isempty(colormap_arrows)
        eval(sprintf('colors = colormap(%s);',colormap_arrows));
        colorbar;
        if exist('fmin','var') && ~isempty(fmin) && exist('fmax','var') && ~isempty(fmax)
            setquivercolor(hq,colors,'mags',v,'range',[fmin,fmax]);
        else
            setquivercolor(hq,colors,'mags',v);
        end
        if exist('fmin','var') && ~isempty(fmin) && exist('fmax','var') && ~isempty(fmax)
            caxis([fmin fmax]);
        else
            caxis([min(v(:)) max(v(:))]);
        end
    end

else
    
    error('Error: quiverstreamlineplot_multiple: wrong geometric structure');

end
    
% Reset status of hold
if ~hss, hold off; end;
