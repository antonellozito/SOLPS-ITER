function [x_rad,x_radedge] = calc_radialcoordinate(transport_mode,gmtry,indbal,default_region,radbaldist)
%
% balance_calc_radialcoordinate calculates the radial coordinate of the radial balance plots
%
%% CALCULATION

transport_mode = lower(char(transport_mode));

indbaledge = indbal;
topix = gmtry.topix+1;
topiy = gmtry.topiy+1;
for ix = 1:gmtry.nx
    iylast = find(indbal(ix,:),1,'last');
    if ~isempty(iylast)
        indbaledge(topix(ix,iylast),topiy(ix,iylast)) = true;
    end
end

switch transport_mode
    case 'parallel'
        region_side = default_region(2);
    case 'radial'
        region_side = default_region(1);
    otherwise
        error('Error: Transport mode ''%s'' not supported.',transport_mode);
end

x_rad = [];
x_radedge = [];

switch region_side
    case 'i'
        side = 'inner';
        ixmid = gmtry.imp;
        ixxpoint = find(diff(gmtry.leftix(:,1))<1);
        if ~isempty(ixxpoint)
            ixxpoint = ixxpoint(1)-1;
        end
        ixtarget = 1;
    case 'o'
        side = 'outer';
        ixmid = gmtry.omp;
        ixxpoint = find(diff(gmtry.leftix(:,1))<1);
        if ~isempty(ixxpoint)
            ixxpoint = ixxpoint(2)+1;
        end
        ixtarget = size(gmtry.cr,1);
    otherwise
        error('Error: Region side ''%s'' not supported.',region_side);
end

switch radbaldist
    case 'midplane'
        values_edge = [0,cumsum(sqrt(diff(gmtry.cr(ixmid,:)).^2+diff(gmtry.cz(ixmid,:)).^2))];
        values_edge = values_edge-values_edge(gmtry.sep+2);
        dys1 = sqrt(diff(gmtry.cr_y(ixmid,gmtry.sep+1:gmtry.sep+2))^2+diff(gmtry.cz_y(ixmid,gmtry.sep+1:gmtry.sep+2))^2);
        values_cell = values_edge+dys1/2;
    case 'x-point'
        values_edge = [0,cumsum(sqrt(diff(gmtry.cr(ixxpoint,:)).^2+diff(gmtry.cz(ixxpoint,:)).^2))];
        values_edge = values_edge-values_edge(gmtry.sep+2);
        dys1 = sqrt(diff(gmtry.cr_y(ixxpoint,gmtry.sep+1:gmtry.sep+2))^2+diff(gmtry.cz_y(ixxpoint,gmtry.sep+1:gmtry.sep+2))^2);
        values_cell = values_edge+dys1/2;
    case 'target'
        values_edge = [0,cumsum(sqrt(diff(gmtry.cr(ixtarget,:)).^2+diff(gmtry.cz(ixtarget,:)).^2))];
        values_edge = values_edge-values_edge(gmtry.sep+2);
        dys1 = sqrt(diff(gmtry.cr_y(ixtarget,gmtry.sep+1:gmtry.sep+2))^2+diff(gmtry.cz_y(ixtarget,gmtry.sep+1:gmtry.sep+2))^2);
        values_cell = values_edge+dys1/2;
    case 'rho'
        switch transport_mode
            case 'parallel'
                x_rad = calc_rho('center');
                x_radedge = [];
            case 'radial'
                x_radedge = calc_rho('edge');
                x_rad = calc_rho('center');
        end
    otherwise
        error('Error: Radial balance distance ''%s'' not supported.',radbaldist);
end

if ~strcmp(radbaldist,'rho')
    coordinate_edge = [];
    coordinate_cell = [];
    for iy = 1:gmtry.ny
        switch transport_mode
            case 'parallel'
                ixedge = find(indbaledge(:,iy),1,'first');
                ixcell = find(indbal(:,iy),1,'first');
            case 'radial'
                switch side
                    case 'inner'
                        ixedge = gmtry.imp;
                        ixcell = gmtry.imp;
                    case 'outer'
                        ixedge = gmtry.omp+1;
                        ixcell = gmtry.omp+1;
                end
        end
        if ~isempty(ixedge) && indbaledge(ixedge,iy)
            coordinate_edge = [coordinate_edge,values_edge(iy)];
        end
        if ~isempty(ixcell) && indbal(ixcell,iy)
            coordinate_cell = [coordinate_cell,values_cell(iy)];
        end
    end
    x_radedge = coordinate_edge;
    x_rad = coordinate_cell;

    if ~isempty(x_rad)
        x_rad = 100*x_rad;
    end
    if ~isempty(x_radedge)
        x_radedge = 100*x_radedge;
    end

end

end
