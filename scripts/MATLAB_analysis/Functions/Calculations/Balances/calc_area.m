function area_divide = calc_area(transport_mode,gmtry,areatype)
%
% balance_calc_area calculates the type of area that transport fluxes are divided by
%
%% SELECTION OF THE AREA

transport_mode = lower(char(transport_mode));

switch transport_mode
    case 'parallel'
        % Geometry variables:
        nx = gmtry.nx;
        ny = gmtry.ny;
        leftix = gmtry.leftix+1;
        leftiy = gmtry.leftiy+1;
        dv = gmtry.dv;
        hx = gmtry.hx;
        B = gmtry.bb;

        switch areatype
            case 'parallel'
                apll = dv./hx.*abs(B(:,:,1)./B(:,:,4)); % Parallel area at cell centres
                area_divide = zeros(nx,ny);
                for iy = 1:ny
                    for ix = 1:nx
                        if leftix(ix,iy) < 1
                            continue;
                        end
                        area_divide(ix,iy) = (apll(leftix(ix,iy),leftiy(ix,iy))*dv(ix,iy)+...
                                              apll(ix,iy)*dv(leftix(ix,iy),leftiy(ix,iy)))/...
                                             (dv(ix,iy)+dv(leftix(ix,iy),leftiy(ix,iy))); % Map to left cell face
                    end
                end
            case 'contact'
                area_divide = gmtry.gs(:,:,1); % Poloidal contact area
            case 'none'
                area_divide = ones(gmtry.nx,gmtry.ny); % No division by area
            otherwise
                error('Error: Area type ''%s'' not supported.',areatype);
        end
    case 'radial'
        switch areatype
            case 'contact'
                area_divide = gmtry.gs(:,:,2); % Radial contact area
            case 'none'
                area_divide = ones(gmtry.nx,gmtry.ny); % No division by area
            otherwise
                error('Error: Area type ''%s'' not supported.',areatype);
        end
    otherwise
        error('Error: Transport mode ''%s'' not supported.',transport_mode);
end

end
