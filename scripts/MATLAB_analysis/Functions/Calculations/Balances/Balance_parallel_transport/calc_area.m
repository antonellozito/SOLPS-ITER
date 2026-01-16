function area_divide = calc_area(gmtry,areatype)
%
% calc_area calculates the type of area that poloidal fluxes are divided by
%
%% SELECTION OF THE AREA

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
        apll = dv./hx.*abs(B(:,:,1)./B(:,:,4)); % Parallel area at cell centres:
        area_divide = zeros(nx,ny);
        for iy=1:ny
            for ix=1:nx
                if leftix(ix,iy)<1
                    continue;
                end
                    area_divide(ix,iy) = (apll(leftix(ix,iy),leftiy(ix,iy))*dv(ix,iy)+...
                                          apll(ix,iy)*dv(leftix(ix,iy),leftiy(ix,iy)))/...
                                         (dv(ix,iy)+dv(leftix(ix,iy),leftiy(ix,iy))); % Map to left cell face:
            end
        end
        units = 'm^{-2}s^{-1}';
	case 'contact'
        area_divide = gmtry.gs(:,:,1); % Poloidal contact area
        units = 'm^{-2}s^{-1}';
	case 'none'
        area_divide = ones(gmtry.nx,gmtry.ny); % No division by area
        units = 's^{-1}';
    otherwise
        error('Error: Area type ''%s'' not supported.',areatype);
end

end