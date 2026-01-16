function p = patchplot(grid,field,xinterval,yinterval,scale,fmin,fmax,balance)
%
% Routine to make patchplot of cell centered quantity.
% 
% Input arguments:
%
% - grid : struct read from b2fgmtry or triangles files
% 
% - field : cell centered field to be plotted
%
% - xinterval : poloidal interval of cells to be plotted (optional, only for structured grid)
%
% - yinterval : radial interval of cells to be plotted (optional, only for structured grid)
% 
% - scale : scale factor for data in field (optional)
% 
% - fmin  : min. contour value (optional)
% 
% - fmax  : max. contour value (optional)
%
% - balance : 'true' if contourfplot is called by the balance routines (optional)
%
% Output arguments:
%
% - p       : handle to the patch plot object
% 

% Set default values for some arguments, if not supplied

if ~exist('scale','var') || isempty(scale)
  scale = 1;
end
if ~exist('fmin','var') || isempty(fmin)
    fmin = min(min(field/scale));
end
if ~exist('fmax','var') || isempty(fmax)
    fmax = max(max(field/scale));
end
if ~exist('balance','var') || isempty(balance)
    balance = false;
end

% Consistency checks

if fmin > fmax
    error('Error: patchplot: fmin > fmax.');
end

% Crop and scale field

field = max(min(field/scale,fmax),fmin);

% Set up the plot for plasmagrid or trianglegrid

if isplasmagrid(grid)
    
    if ( ~exist('xinterval','var') || isempty(xinterval) ) && ( ~exist('yinterval','var') || isempty(yinterval) )
        crx = grid.crx;
        cry = grid.cry;
        ff = field;
    elseif ( exist('xinterval','var') || ~isempty(xinterval) ) && ( ~exist('yinterval','var') || isempty(yinterval) )
        crx = grid.crx(xinterval,:,:);
        cry = grid.cry(xinterval,:,:);
        ff = field(xinterval,:);
    elseif ( ~exist('xinterval','var') || isempty(xinterval) ) && ( exist('yinterval','var') || ~isempty(yinterval) )
        crx = grid.crx(:,yinterval,:);
        cry = grid.cry(:,yinterval,:);
        ff = field(:,yinterval);
    elseif ( exist('xinterval','var') || ~isempty(xinterval) ) && ( exist('yinterval','var') || ~isempty(yinterval) )
        if balance
            crx = grid.crx(xinterval,yinterval(2:end),:);
            cry = grid.cry(xinterval,yinterval(2:end),:);
            ff = field(:,1:end-1);
        else
            crx = grid.crx(xinterval,yinterval,:);
            cry = grid.cry(xinterval,yinterval,:);
            ff = field(xinterval,yinterval);
        end
    end

    nx2 = size(crx,1);
    ny2 = size(crx,2);
    
    % Resize for patch plot
    if nx2-size(ff,1) == 2 && ny2-size(ff,2) == 2
        X = reshape(crx(2:end-1,2:end-1,:),(nx2-2)*(ny2-2),4)';
        Y = reshape(cry(2:end-1,2:end-1,:),(nx2-2)*(ny2-2),4)';
        f = reshape(ff,(nx2-2)*(ny2-2),1)';
    else
        X = reshape(crx,nx2*ny2,4)';
        Y = reshape(cry,nx2*ny2,4)';
        f = reshape(ff,nx2*ny2,1)';
    end

    % Resize for patch plot
    %X = reshape(grid.crx,nx2*ny2,4)';
    %Y = reshape(grid.cry,nx2*ny2,4)';
    %f = reshape(field,nx2*ny2,1)';
    
    % Create closed polygon from vertex coordinates
    X(3:4,:) = X(4:-1:3,:);
    Y(3:4,:) = Y(4:-1:3,:);

    % Create patch plot
    
    p = patch(X,Y,f,'LineStyle','none');

elseif isunstructuredgrid(grid)

    % Maybe add CheckVertOrder and ReOrderCellConn but need refactoring
    is_ordered = check_vert_order_us(grid);
    grid = reoder_cell_connection_us(grid,is_ordered);

    S = struct([]);
    for iCv = 1:grid.nCi
        S(iCv).XData = [];
        S(iCv).YData = [];
        S(iCv).ZData = field(iCv);
        iVx1 = grid.cvVx(grid.cvVxP(iCv,1));
        for i = 1:grid.cvVxP(iCv,2)
            iVx = grid.cvVx(grid.cvVxP(iCv,1)+i-1);

            S(iCv).XData = [S(iCv).XData;grid.vxX(iVx)];
            S(iCv).YData = [S(iCv).YData;grid.vxY(iVx)];
        end
        S(iCv).XData = [S(iCv).XData;grid.vxX(iVx1)];
        S(iCv).YData = [S(iCv).YData;grid.vxY(iVx1)];
        %S(iCv).XData(end-2:end-1) = [S(iCv).XData(end-1);S(iCv).XData(end-2)];
        %S(iCv).YData(end-2:end-1) = [S(iCv).YData(end-1);S(iCv).YData(end-2)];
    end

    % Create patch plot
    
    for i = 1:length(S)
        p = patch(S(i).XData',S(i).YData',S(i).ZData,'LineStyle','none');
    end
    
elseif istrianglegrid(grid)
    
    % Construct the triangles as polygons for patch
    X = zeros(3,size(grid.cells,1));
    Y = zeros(3,size(grid.cells,1));
    for j = 1:3
        for i = 1:size(grid.cells,1)
            X(j,i) = grid.nodes(grid.cells(i,j),1);
            Y(j,i) = grid.nodes(grid.cells(i,j),2);
        end
    end
    
    f = field';

    % Create patch plot
    
    p = patch(X,Y,f,'LineStyle','none');

else
    
    error('Error: patchplot: wrong geometric structure');

end

% Set axis to fmin and fmax

caxis([fmin fmax]);

end
