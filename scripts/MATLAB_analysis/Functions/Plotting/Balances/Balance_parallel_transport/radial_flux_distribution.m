function fluxes = radial_flux_distribution(flux,source,res,totname,fluxname,sourcename,gmtry,indbal,ismom,units,default_region,reverse,areaend,areatype,radbaldist)
%
% radial_balance makes balance plots with radial resolution (integrating in the poloidal direction) in a given region            
%                                                                                                                                
% flux:        An (nx*ny*nd) sized matrix, where nd is the number of different fluxes into which the total flux is decomposed    
%              Comprising the flux from each component in the entire grid                                                        
% source:      An (nx*ny*nd) sized matrix, where nd is the number of different sources into which the total source is decomposed 
%              Comprising the source from each component in the entire grid                                                      
% res:         The code residual                                                                                                 
% totname:     A cell of length 4 with strings stating the names of                                                              
%              (1) upstream flux, (2) downsteam flux, (3) source, (4) residual                                                                                
% fluxname:    A cell of length nd with strings stating the names of each flux component                                         
% sourcename:  A cell of length nd with strings stating the names of each source component                                       
% gmtry:       Structure containing commonly-used variables                                                                      
% indbal:      Logical matrix of size nx*ny that is true for cells where balance should be performed                             
% ismom:       True if we are performing momentum balance                                                                        
% units:       String for units given on y axes                                                                                  
% region:      SOL region of the computational grid on which perform the balance
% reverse:     True if the right-most end of the balance volume is upstream of the left-most end, otherwise false
% areaend:     Defines the radial end of the balance region at which areas will be calculated                                    
% areatype:    Type of area that radial fluxes are divided by                                                                     
% radbaldist:  Radial coordinate to which the plotted quantities are to be mapped                                                
%
%% POLOIDAL INTEGRATION OF FLUXES AND SOURCES

% Geometry variables
nx = gmtry.nx;
ny = gmtry.ny;
topix = gmtry.topix+1;
topiy = gmtry.topiy+1;
bottomix = gmtry.bottomix+1;
bottomiy = gmtry.bottomiy+1;
leftix = gmtry.leftix+1;
leftiy = gmtry.leftiy+1;
rightix = gmtry.rightix+1;
rightiy = gmtry.rightiy+1;

% Poloidal fluxes through left-most and right-most surfaces of the balance volume along its radial length
% for each flux component
fluxleft = [];
fluxright = [];
for i=1:size(flux,3)
    fluxleft(:,i) = calc_fluxend(flux(:,:,i),indbal,'left');
    fluxright(:,i) = calc_fluxend(flux(:,:,i),indbal,'right',rightix,rightiy);
end

% Poloidally-integrated sources along the radial length of the balance volume
% for each source component
sourceint = [];
for i=1:size(source,3)
    sourceint(:,i) = sum_poloidal(source(:,:,i),indbal,gmtry);
end

% Poloidally-integrated residual
resint = sum_poloidal(res,indbal,gmtry);

% Account for flux reversal (only for pressure balance) and geometry reversal (only for inner side)
if ~reverse
    reversefac = 1;
    if ismom
        momfac = -1;
    else
        momfac = 1;
    end
else
    reversefac = -1;
    if ismom
        momfac = 1;
    else
        momfac = 1;  
    end
end
% if ~reverse
%     reversefac = 1;
%     momfac = 1;
% elseif ismom
%     reversefac = -1;
%     momfac = -1;
% else
%     reversefac = -1;
%     momfac = 1;
% end
if ismom
    momfac = momfac*-sign(mean(mean(gmtry.bb(:,:,3))));
end
if ~reverse
    fluxup = fluxleft; % Poloidal flux through upstream surface for outer side
    fluxdown = fluxright; % Poloidal flux through downstream surface for outer side
else
    fluxup = fluxright; % Poloidal flux through upstream surface for inner side
    fluxdown = fluxleft; % Poloidal flux through downstream surface for inner side
end

%% CALCULATION OF THE AREAS

% Poloidal- or parallel-directed area at all the cell boundaries for each cell
area_divide = calc_area(gmtry,areatype);

% Total areas at the ends which fluxes and sources will be divided by
quantity = evalin('base', 'BAL_QUANT');
switch quantity
    case 'total_pressure'
        area_divide_rad = ones(1,size(fluxleft,1));
    otherwise
        switch areaend
            case 'left'
                area_divide_rad = calc_fluxend(area_divide,indbal,'left');
            case 'right'
                area_divide_rad = calc_fluxend(area_divide,indbal,'right',rightix,rightiy);
            case 'none'
                area_divide_rad = ones(1,size(fluxleft,1));
        end
end

%% PRODUCE THE PLOTS

% Radial coordinate
% x_rad = calc_radialcoordinate(gmtry,indbal,default_region,radbaldist);
% x_rad_interp = linspace(min(x_rad),max(x_rad),500);

% Total balance with residuals
cmap = gmtry.cmap;
fluxuptot = momfac*reversefac*sum(fluxup,2)'./area_divide_rad;
fluxdowntot = momfac*reversefac*sum(fluxdown,2)'./area_divide_rad;
sourcetot = momfac*sum(sourceint,2)'./area_divide_rad;
coderes = momfac*(resint./area_divide_rad)';

% Check the level of agreement between post-calculated and code-calculated residuals
postres = momfac*(reversefac*(sum(fluxup,2)-sum(fluxdown,2))+sum(sourceint,2))./area_divide_rad';

% Decompose upstream fluxes
for i=1:size(fluxup,2)
    if any(fluxup(:,i))
        fluxupcomp(:,i) = momfac*reversefac*fluxup(:,i)./area_divide_rad';
    end
end

% Decompose downstream fluxes
for i=1:size(fluxdown,2)
    if any(fluxdown(:,i))
        fluxdowncomp(:,i) = momfac*reversefac*fluxdown(:,i)./area_divide_rad';   
    end
end

% Decompose sources
for i=1:size(sourceint,2)
    if any(sourceint(:,i))
        sourcecomp(:,i) = momfac*sourceint(:,i)./area_divide_rad';
    end
end

%% CREATE A STRUCTURE IN WHICH THE PLOTTED VALUES ARE STORED

% Areas
%fluxes.area_divide_rad = area_divide_rad;

% Radial coordinate
%fluxes.Radial_coordinate_cell = x_rad;

% Upstream flux (total + components)
fluxes.fluxuptot = fluxuptot;
%rb.(matlab.lang.makeValidName(sprintf(totname{1}))) = fluxuptot;
for i=1:size(fluxup,2)
    if any(fluxup(:,i))
        fluxes.fluxupcomp(:,i) = fluxupcomp(:,i);
        %rb.(matlab.lang.makeValidName(sprintf('Flux_decomp_%s',fluxname{i}))) = fluxupcomp(:,i);
    end
end

% Downstream flux (total + components)
fluxes.fluxdowntot = fluxdowntot;
%rb.(matlab.lang.makeValidName(sprintf(totname{2}))) = fluxdowntot;
for i=1:size(fluxdown,2)
    if any(fluxdown(:,i))
        fluxes.fluxdowncomp(:,i) = fluxdowncomp(:,i);
        %rb.(matlab.lang.makeValidName(sprintf('Flux_decomp_%s',fluxname{i}))) = fluxdowncomp(:,i);
    end
end

% Poloidally-integrated source (total + components)
fluxes.sourcetot = sourcetot;
%rb.(matlab.lang.makeValidName(sprintf(totname{3}))) = sourcetot;
for i=1:size(sourceint,2)
    if any(sourceint(:,i))
        fluxes.sourcecomp(:,i) = sourcecomp(:,i);
        %rb.(matlab.lang.makeValidName(sprintf('Source_decomp_%s',sourcename{i}))) = sourcecomp(:,i);
    end
end

% Poloidally integrated residual
fluxes.Residual(:) = coderes;

% Names
fluxes.flux_up_tot_name = totname{1};
fluxes.flux_down_tot_name = totname{2};
fluxes.flux_component_names = fluxname;
fluxes.source_tot_name = totname{3};
fluxes.source_component_names = sourcename;

end