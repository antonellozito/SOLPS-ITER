function area_divide = calc_area(gmtry,areatype)
%
% calc_area calculates the type of area that radial fluxes are divided by
%
%% SELECTION OF THE AREA

switch areatype
   case 'contact'
      area_divide = gmtry.gs(:,:,2); % Radial contact area
      units = 'm^{-2}s^{-1}';
   case 'none'
      area_divide = ones(gmtry.nx,gmtry.ny); % No division by area
      units = 's^{-1}';
   otherwise
      error('Error: Area type ''%s'' not supported.',areatype);
end

end