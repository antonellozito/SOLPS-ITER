function h = quiverplot(grid,uu,vv,xinterval,yinterval,normalize,scale,linewidth,color,colormap_arrows,fmin,fmax,gaps)
%
% Routine to make quiver plot of the velocity field (uu,vv), where uu
% is the poloidal velocity and vv the radial velocity defined in cell
% centers of gmtry.
% 
% Input arguments:
%
% - grid : struct read from b2fgmtry or triangles files
%
% - uu : poloidal velocity component (cell centered)
%
% - vv : radial velocity component (cell centered)
%
% - xinterval : poloidal interval of cells to be plotted (optional)
%
% - yinterval : radial interval of cells to be plotted (optional)
%
% - normalize : select wether normalize the length of the arrows (optional)
%
% - scale : adjusts the length of the arrows (optional)
%
% - linewidth : adjusts the linewidth of the arrows (optional)
%
% - color : adjusts a fixed color of the arrows (optional)
%
% - colormap_arrows : adjusts a variable color of the arrows as function of their magnitude (optional)
%
% - fmin : min. arrow color, in case of colormap (optional)
%
% - fmax : max. arrow color, in case of colormap (optional)
%
% Output arguments:
%
% - h      : handle to the quiver plot
%

if ~exist('normalize','var') || isempty(normalize)
  normalize = true;
end
if ~exist('scale','var') || isempty(scale)
  scale = 0.5;
end
if ~exist('linewidth','var') || isempty(linewidth)
  linewidth = 1.2;
end
if ~exist('color','var') || isempty(color)
  color = 'Black';
end

% Check current status of hold
hs = ishold;

if isplasmagrid(grid)

    if ( ~exist('xinterval','var') || isempty(xinterval) ) && ( ~exist('yinterval','var') || isempty(yinterval) )
        crx = grid.crx;
        cry = grid.cry;
        uuf = uu;
        vvf = vv;
    elseif ( exist('xinterval','var') || ~isempty(xinterval) ) && ( ~exist('yinterval','var') || isempty(yinterval) )
        crx = grid.crx(xinterval,:,:);
        cry = grid.cry(xinterval,:,:);
        uuf = uu(xinterval,:);
        vvf = vv(xinterval,:);
    elseif ( ~exist('xinterval','var') || isempty(xinterval) ) && ( exist('yinterval','var') || ~isempty(yinterval) )
        crx = grid.crx(:,yinterval,:);
        cry = grid.cry(:,yinterval,:);
        uuf = uu(:,yinterval);
        vvf = vv(:,yinterval);
    elseif ( exist('xinterval','var') || ~isempty(xinterval) ) && ( exist('yinterval','var') || ~isempty(yinterval) )
        crx = grid.crx(xinterval,yinterval,:);
        cry = grid.cry(xinterval,yinterval,:);
        uuf = uu(xinterval,yinterval);
        vvf = vv(xinterval,yinterval);
    end

    % Cell center coordinates
    xc = mean(crx,3);
    yc = mean(cry,3);
    
    % Poloidal and radial unit vectors in cell centers
    [epx,epy,erx,ery] = mshproj(grid);

    if ( ~exist('xinterval','var') || isempty(xinterval) ) && ( ~exist('yinterval','var') || isempty(yinterval) )
        epxf = epx;
        epyf = epy;
        erxf = erx;
        eryf = ery;
    elseif ( exist('xinterval','var') || ~isempty(xinterval) ) && ( ~exist('yinterval','var') || isempty(yinterval) )
        epxf = epx(xinterval,:);
        epyf = epy(xinterval,:);
        erxf = erx(xinterval,:);
        eryf = ery(xinterval,:);
    elseif ( ~exist('xinterval','var') || isempty(xinterval) ) && ( exist('yinterval','var') || ~isempty(yinterval) )
        epxf = epx(:,yinterval);
        epyf = epy(:,yinterval);
        erxf = erx(:,yinterval);
        eryf = ery(:,yinterval);
    elseif ( exist('xinterval','var') || ~isempty(xinterval) ) && ( exist('yinterval','var') || ~isempty(yinterval) )
        epxf = epx(xinterval,yinterval);
        epyf = epy(xinterval,yinterval);
        erxf = erx(xinterval,yinterval);
        eryf = ery(xinterval,yinterval);
    end
    
    % Project velocities onto Cartesian directions
    vx = uuf.*epxf + vvf.*erxf;
    vy = uuf.*epyf + vvf.*eryf;

    v = sqrt(vx.^2+vy.^2);
   
    vxn=(vx./sqrt(vx.^2+vy.^2))./2;
    vyn=(vy./sqrt(vx.^2+vy.^2))./2;
     
    % Quiver plot
    if normalize
        h = quiver(xc,yc,vxn,vyn,scale,...
            'LineWidth',linewidth,...
            'Color',color);
    else
        h = quiver(xc,yc,vx,vy,scale,...
            'LineWidth',linewidth,...
            'Color',color);
    end

    if exist('colormap_arrows','var') && ~isempty(colormap_arrows)
        eval(sprintf('colors = colormap(%s);',colormap_arrows));
        colorbar;
        if exist('fmin','var') && ~isempty(fmin) && exist('fmax','var') && ~isempty(fmax)
            setquivercolor(h,colors,'mags',v,'range',[fmin,fmax]);
        else
            setquivercolor(h,colors,'mags',v);
        end
        if exist('fmin','var') && ~isempty(fmin) && exist('fmax','var') && ~isempty(fmax)
            caxis([fmin fmax]);
        else
            caxis([min(v(:)) max(v(:))]);
        end
    end

elseif istrianglegrid(grid)

    uu_interp = pdeprtni(grid.nodes',grid.cells',uu');
    vv_interp = pdeprtni(grid.nodes',grid.cells',vv');

    unique_x = unique(grid.nodes(:,1));
    unique_y = unique(grid.nodes(:,2));

    grid_x = linspace(min(unique_x),max(unique_x),100);
    grid_y = linspace(min(unique_y),max(unique_y),100);

    [Xr,Yr,vx] = griddata(grid.nodes(:,1),grid.nodes(:,2),uu_interp,grid_x,grid_y');
    [Xr,Yr,vy] = griddata(grid.nodes(:,1),grid.nodes(:,2),vv_interp,grid_x,grid_y');

%     IN = inpolygon(Xr,Yr,grid.nodes(:,1),grid.nodes(:,2));
%     vx(~IN) = NaN;
%     vy(~IN) = NaN;

    v = sqrt(vx.^2+vy.^2);

    vxn=(vx./sqrt(vx.^2+vy.^2))./2;
    vyn=(vy./sqrt(vx.^2+vy.^2))./2;

    % Quiver plot
    if normalize
        h = quiver(Xr,Yr,vxn,vyn,scale,...
            'LineWidth',linewidth,...
            'Color',color);
    else
        h = quiver(Xr,Yr,vx,vy,scale,...
            'LineWidth',linewidth,...
            'Color',color);
    end

    if exist('colormap_arrows','var') && ~isempty(colormap_arrows)
        eval(sprintf('colors = colormap(%s);',colormap_arrows));
        colorbar;
        if exist('fmin','var') && ~isempty(fmin) && exist('fmax','var') && ~isempty(fmax)
            setquivercolor(h,colors,'mags',v,'range',[fmin,fmax]);
        else
            setquivercolor(h,colors,'mags',v);
        end
        if exist('fmin','var') && ~isempty(fmin) && exist('fmax','var') && ~isempty(fmax)
            caxis([fmin fmax]);
        else
            caxis([min(v(:)) max(v(:))]);
        end
    end

else
    
    error('Error: quiverplot: wrong geometric structure');

end

% Reset status of hold
if ~hs, hold off;end;

end



function setquivercolor(q,currentColormap,varargin)
%
% INPUT:
%   q = handle to quiver plot
%   currentColormap = e.g. jet;
% OPTIONAL INPUT ('Field',value):
%   'range' = [min,max]; % Range of the magnitude in the colorbar
%                          (used to possibly saturate or expand the color used compared to the vectors)
%   'mags' = magnitude; % Actual magnitude of the vectors
%

%// Set default values
range = [];
mags = [];

%// Read the optional range value
if find(strcmp('range',varargin))
  range = varargin{ find(strcmp('range',varargin))+1 };
end

qU = q.UData(~isnan(q.UData));
qV = q.VData(~isnan(q.VData));
qW = q.WData(~isnan(q.WData));

%// Compute/read the magnitude of the vectors
if find(strcmp('mags',varargin))
  mags = varargin{ find(strcmp('mags',varargin))+1 };
  mags = mags(~isnan(mags)&~isnan(q.UData));  % This reshapes automatically
else
  mags = sqrt(sum(cat(2, qU, qV, ...
             reshape(qW, numel(qU), [])).^2, 2));
end
%// If range is auto, take range as the min and max of mags
if isstr(range) & strcmp(range,'auto')
  range = [min(mags) max(mags)];
end

%// Change value depending on the desired range
if ~isempty(range) & isnumeric(range) & numel(range)==2
  range = sort(range);
  mags(mags>range(2)) = range(2);
  mags(mags<range(1)) = range(1);
end

%// Now determine the color to make each arrow using a colormap
if ~isempty(range) & isnumeric(range) & numel(range)==2
  Edges = linspace(range(1),range(2),size(currentColormap, 1)+1);
  [~, ~, ind] = histcounts(mags, Edges);
else
  [~, ~, ind] = histcounts(mags, size(currentColormap, 1));
end

%// Now map this to a colormap to get RGB
cmap = uint8(ind2rgb(ind(:), currentColormap) * 255);
cmap(:,:,4) = 255;
cmap = permute(repmat(cmap, [1 3 1]), [2 1 3]);

%// Color data
cd_head = reshape(cmap(1:3,:,:), [], 4).';
cd_tail = reshape(cmap(1:2,:,:), [], 4).';

%// We repeat each color 3 times (using 1:3 below) because each arrow has 3 vertices
set(q.Head, 'ColorBinding', 'interpolated', 'ColorData', cd_head);

%// We repeat each color 2 times (using 1:2 below) because each tail has 2 vertices
set(q.Tail, 'ColorBinding', 'interpolated', 'ColorData', cd_tail);

end
