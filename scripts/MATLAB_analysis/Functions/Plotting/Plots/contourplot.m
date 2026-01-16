function [Ch] = contourplot(grid,field,xinterval,yinterval,scale,fmin,fmax,ncont,balance)
%
% Routine to make contourplot of cell centered quantity.
% 
% Input arguments:
%
% - grid : struct read from b2fgmtry or triangles files
%
% - field : cell centered field to be plotted
%
% - xinterval : poloidal interval of cells to be plotted (optional)
%
% - yinterval : radial interval of cells to be plotted (optional)
%
% - scale : scale factor for data in field (optional)
% 
% - fmin  : min. contour value (optional)
% 
% - fmax  : max. contour value (optional)
% 
% - ncont : number of contour levels (optional)
%
% - balance : 'true' if contourfplot is called by the balance routines (optional)
%
% Output arguments:
%
% - Ch  : struct, length 3 (1 = Core, 2 = SOL, 3 = PFR), with fields
%         * Ch(i).C: matrix with contour levels (see CONTOURC)
%         * Ch(i).h: handles to the CONTOURGROUP objects
% 

% Set default values for some arguments, if not supplied

if ~exist('scale','var') || isempty(scale)
  scale = 1;
end
if ~exist('ncont','var') || isempty(ncont)
    ncont = 50;
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
    error('Error: contourplot: fmin > fmax.');
end

% Rescale field

field = field/scale;

% Determine contour levels

if ncont > 1
    if fmin > 0
        fcont = [0,fmin:(fmax-fmin)/ncont:fmax];
    elseif fmax < 0
        fcont = [fmin:(fmax-fmin)/ncont:fmax,0];
    else
        fcont = [(fmin:(fmax-fmin)/ncont:fmax)];
    end
elseif ncont == 1
    if fmin ~= fmax
        error('Error: contourplot: ncont == 1 & fmin ~= fmax.');
    end
    fcont = [fmin,fmax];
else
    error('Error: contourplot: ncont < 1.');
end

% Set up the plot for plasmagrid or trianglegrid

if isplasmagrid(grid)

    % Copy data into guard cell in case of data from fort.44

    if (size(field,1) == size(grid.crx,1) - 2) & ...
            (size(field,2) == size(grid.crx,2) - 2)
        fieldtmp = zeros(size(field,1)+2,size(field,2)+2);
        fieldtmp(2:end-1,2:end-1) = field;
        fieldtmp(1,2:end-1)   = fieldtmp(2,2:end-1);
        fieldtmp(end,2:end-1) = fieldtmp(end-1,2:end-1);
        fieldtmp(:,1)   = fieldtmp(:,2);
        fieldtmp(:,end) = fieldtmp(:,end-1);
        field = fieldtmp;
    end

    % Compute cell center coordinates

    %r = mean(grid.crx,3);
    %z = mean(grid.cry,3);
    r = grid.crx(:,:,3);
    z = grid.cry(:,:,3);

    % Check current status of hold

    hs = ishold;

    % Init output

    Ch = struct('C',[],'h',[]);

    if ( ~exist('xinterval','var') || isempty(xinterval) ) && ( ~exist('yinterval','var') || isempty(yinterval) )

        % SOL
        zC = z(:,grid.topcut(1)+1:end);
        rC = r(:,grid.topcut(1)+1:end);
        f  = field(:,grid.topcut(1)+1:end);
        [Ch(2).C,Ch(2).h] = contour(rC,zC,f,fcont);

        hold on;

        % Core
        zC = [z(grid.leftcut(1)+2:grid.rightcut(1)+1,1:grid.topcut(1)+1);z(grid.leftcut(1)+2,1:grid.topcut(1)+1)];
        rC = [r(grid.leftcut(1)+2:grid.rightcut(1)+1,1:grid.topcut(1)+1);r(grid.leftcut(1)+2,1:grid.topcut(1)+1)];
        f  = [field(grid.leftcut(1)+2:grid.rightcut(1)+1,1:grid.topcut(1)+1);field(grid.leftcut(1)+2,1:grid.topcut(1)+1)];
        [Ch(1).C,Ch(1).h] = contour(rC,zC,f,fcont);

        hold on;

        % PFR
        zC = [z(1:grid.leftcut(1)+1,1:grid.topcut(1)+1);z(grid.rightcut(1)+2:end,1:grid.topcut(1)+1)];
        rC = [r(1:grid.leftcut(1)+1,1:grid.topcut(1)+1);r(grid.rightcut(1)+2:end,1:grid.topcut(1)+1)];
        f  = [field(1:grid.leftcut(1)+1,1:grid.topcut(1)+1);field(grid.rightcut(1)+2:end,1:grid.topcut(1)+1)];
        [Ch(3).C,Ch(3).h] = contour(rC,zC,f,fcont);

    elseif ( exist('xinterval','var') || ~isempty(xinterval) ) && ( ~exist('yinterval','var') || isempty(yinterval) )

        zC = z(xinterval,:);
        rC = r(xinterval,:);
        f  = field(xinterval,:);
        [Ch.C,Ch.h] = contour(rC,zC,f,fcont);

    elseif ( ~exist('xinterval','var') || isempty(xinterval) ) && ( exist('yinterval','var') || ~isempty(yinterval) )

        zC = z(:,yinterval);
        rC = r(:,yinterval);
        f  = field(:,yinterval);
        [Ch.C,Ch.h] = contour(rC,zC,f,fcont);

    elseif ( exist('xinterval','var') || ~isempty(xinterval) ) && ( exist('yinterval','var') || ~isempty(yinterval) )

        zC = z(xinterval,yinterval);
        rC = r(xinterval,yinterval);
        if balance
            f  = field;
        else
            f  = field(xinterval,yinterval);
        end
        [Ch.C,Ch.h] = contour(rC,zC,f,fcont);

    end

elseif isunstructuredgrid(grid)

    % Check vertex order and reorder cell connections
    is_ordered = check_vert_order_us(grid);
    grid = reoder_cell_connection_us(grid,is_ordered);

    % Compute cell center coordinates and extract field values
    r = zeros(grid.nCi,1);
    z = zeros(grid.nCi,1);
    f = zeros(grid.nCi,1);
    
    for iCv = 1:grid.nCi
        r_sum = 0;
        z_sum = 0;
        for i = 1:grid.cvVxP(iCv,2)
            iVx = grid.cvVx(grid.cvVxP(iCv,1)+i-1);
            r_sum = r_sum + grid.vxX(iVx);
            z_sum = z_sum + grid.vxY(iVx);
        end
        r(iCv) = r_sum / grid.cvVxP(iCv,2);
        z(iCv) = z_sum / grid.cvVxP(iCv,2);
        f(iCv) = field(iCv);
    end

    % Create grid for interpolation
    unique_r = unique(grid.vxX);
    unique_z = unique(grid.vxY);
    
    grid_r = linspace(min(unique_r),max(unique_r),1000);
    grid_z = linspace(min(unique_z),max(unique_z),1000);
    
    % Create meshgrid
    [Xr,Yr] = meshgrid(grid_r,grid_z);
    
    % Interpolate field onto regular grid
    Wr = griddata(r,z,f,Xr,Yr);
    
    % Check current status of hold
    hs = ishold;
    
    % Init output
    Ch = struct('C',[],'h',[]);
    
    % Create contour plot
    [Ch.C,Ch.h] = contour(Xr,Yr,Wr,fcont);

elseif istrianglegrid(grid)

    hs = ishold;

    field_interp = pdeprtni(grid.nodes',grid.cells',field');

    [Xr,Yr,Wr] = griddata(grid.nodes(:,1),grid.nodes(:,2),field_interp,unique(grid.nodes(:,1)),unique(grid.nodes(:,2))');
    [Ch.C,Ch.h] = contour(Xr,Yr,Wr,fcont);

else

    error('Error: contourplot: wrong geometric structure');

end

% Reset status of hold

if ~hs, hold off;
end

if ncont > 1
    caxis([fmin,fmax]);
end

end
