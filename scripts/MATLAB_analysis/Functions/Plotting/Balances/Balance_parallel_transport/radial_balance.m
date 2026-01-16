function rb = radial_balance(flux,source,res,totname,fluxname,sourcename,gmtry,indbal,ismom,axbal,units,default_region,reverse,areaend,areatype,radbaldist,residuals)
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
% axbal:       Array of axes into which balance plots will be placed                                                             
% units:       String for units given on y axes                                                                                  
% region:      SOL region of the computational grid on which perform the balance
% reverse:     True if the right-most end of the balance volume is upstream of the left-most end, otherwise false
% areaend:     Defines the radial end of the balance region at which areas will be calculated                                    
% areatype:    Type of area that radial fluxes are divided by                                                                     
% radbaldist:  Radial coordinate to which the plotted quantities are to be mapped                                                
% residuals:   If true then residual are also plotted in the poloidal balance plots                                              
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
    case 'force'
        balfile = evalin('base', 'BALFILE');
        isplot = evalin('base', 'SPECIES_INDEX');
        tmp = ncread(balfile,'na');
        na = sum(tmp(:,:,isplot),3);
        area_divide_rad = calc_fluxend(na,indbal,'left');
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
x_rad = calc_radialcoordinate(gmtry,indbal,default_region,radbaldist);
x_rad_interp = linspace(min(x_rad),max(x_rad),500);

% Total balance with residuals
cmap = gmtry.cmap;
title(axbal(1),'Radial balance','fontweight','normal','fontsize',9);
axis(axbal(1),'tight');
fluxuptot = momfac*reversefac*sum(fluxup,2)'./area_divide_rad;
fluxuptot_interp = interp1(x_rad, fluxuptot, x_rad_interp, 'makima', 'extrap');
plot(x_rad_interp,fluxuptot_interp,'parent',axbal(1),'displayname',totname{1},'linewidth',1,'color',cmap(1,:)); cmap=circshift(cmap,-1);
fluxdowntot = momfac*reversefac*sum(fluxdown,2)'./area_divide_rad;
fluxdowntot_interp = interp1(x_rad, fluxdowntot, x_rad_interp, 'makima', 'extrap');
plot(x_rad_interp,fluxdowntot_interp,'parent',axbal(1),'displayname',totname{2},'linewidth',1,'color',cmap(1,:)); cmap=circshift(cmap,-1);
sourcetot = momfac*sum(sourceint,2)'./area_divide_rad;
sourcetot_interp = interp1(x_rad, sourcetot, x_rad_interp, 'makima', 'extrap');
plot(x_rad_interp,sourcetot_interp,'parent',axbal(1),'displayname',totname{3},'linewidth',1,'color',cmap(1,:));
coderes = momfac*(resint./area_divide_rad)';
coderes_interp = interp1(x_rad, coderes, x_rad_interp, 'makima', 'extrap');
if residuals
	plot(x_rad_interp,coderes_interp,'-m','parent',axbal(1),'displayname',[totname{4},' (code)'],'linewidth',1);
end

% Check the level of agreement between post-calculated and code-calculated residuals
postres = momfac*(reversefac*(sum(fluxup,2)-sum(fluxdown,2))+sum(sourceint,2))./area_divide_rad';
postres_interp = interp1(x_rad, postres, x_rad_interp, 'makima', 'extrap');
if residuals
    plot(x_rad_interp,postres_interp,'-g','parent',axbal(1),'displayname',[totname{4},' (post-cal.)'],'linewidth',1);
end  
fprintf('Radial balance: the maximum difference between code- and post-calculated residuals is %e%%\n',max(abs((coderes-postres)./coderes)*100));

% Decompose upstream fluxes
cmap = gmtry.cmap;
txt = sprintf('Decomposition of\n%s',totname{1});
title(axbal(2),txt,'fontweight','normal','fontsize',9);
axis(axbal(2),'tight');
for i=1:size(fluxup,2)
    if any(fluxup(:,i))
        fluxupcomp(:,i) = momfac*reversefac*fluxup(:,i)./area_divide_rad';
        fluxupcomp_interp(:,i) = interp1(x_rad, fluxupcomp(:,i), x_rad_interp, 'makima', 'extrap');
        plot(x_rad_interp,fluxupcomp_interp(:,i),'parent',axbal(2),'displayname',fluxname{i},'linewidth',1,'color',cmap(1,:)); cmap=circshift(cmap,-1);
    end
end

% Decompose downstream fluxes
cmap = gmtry.cmap;
txt = sprintf('Decomposition of\n%s',totname{2});
title(axbal(3),txt,'fontweight','normal','fontsize',9);
axis(axbal(3),'tight');
for i=1:size(fluxdown,2)
    if any(fluxdown(:,i))
        fluxdowncomp(:,i) = momfac*reversefac*fluxdown(:,i)./area_divide_rad';   
        fluxdowncomp_interp(:,i) = interp1(x_rad, fluxdowncomp(:,i), x_rad_interp, 'makima', 'extrap');
        plot(x_rad_interp,fluxdowncomp_interp(:,i),'parent',axbal(3),'displayname',fluxname{i},'linewidth',1,'color',cmap(1,:)); cmap=circshift(cmap,-1);
    end
end

% Decompose sources
cmap = gmtry.cmap;    
txt = sprintf('Decomposition of\n%s',totname{3});
title(axbal(4),txt,'fontweight','normal','fontsize',9);
axis(axbal(4),'tight');    
for i=1:size(sourceint,2)
    if any(sourceint(:,i))
        sourcecomp(:,i) = momfac*sourceint(:,i)./area_divide_rad';
        sourcecomp_interp(:,i) = interp1(x_rad, sourcecomp(:,i), x_rad_interp, 'makima', 'extrap');
        plot(x_rad_interp,sourcecomp_interp(:,i),'parent',axbal(4),'displayname',sourcename{i},'linewidth',1,'color',cmap(1,:)); cmap=circshift(cmap,-1);
    end
end

% Set x- and y-label
for j=1:4
    switch radbaldist
        case 'midplane'
            switch default_region(2)
                case 'i'
                    txt = 'inner midplane';
                case 'o'
                    txt = 'outer midplane';
            end
            xlabel(axbal(j),sprintf('r-r_{sep} (%s) [cm]',txt));
        case 'x-point'
            txt = 'x-point';
            xlabel(axbal(j),sprintf('r-r_{sep} (%s) [cm]',txt));
        case 'target'
            switch default_region(2)
                case 'i'
                    txt = 'inner target';
                case 'o'
                    txt = 'outer target';
                    xlabel(axbal(j),sprintf('r-r_{sep} (%s) [cm]',txt));
            end
        case 'rho'
            xlabel(axbal(j),sprintf('\\rho_p'));
    end
    ylabel(axbal(j),['[',units,']']);
end

% Set the same x-axis limits for all the plots
% set(axbal(1),'xlim',[min(x_rad) max(x_rad)]);
% set(axbal(2),'xlim',get(axbal(1),'xlim'));
% set(axbal(3),'xlim',get(axbal(1),'xlim'));

% Set the same y-axis limits for all the plots
ymin = 1E40;
ymax = -1E40;
for iax=1:length(axbal)
	a = findobj(get(axbal(iax),'children'),'type','line');
	for il=1:length(a)
        if min(get(a(il),'ydata'))<ymin
            ymin = min(min(get(a(il),'ydata')));
        end
        if max(get(a(il),'ydata'))>ymax
            ymax = max(get(a(il),'ydata'));
        end
    end
end
if (ymin~=ymax)
	set(axbal,'ylim',[ymin ymax]);
end

%% CREATE A STRUCTURE IN WHICH THE PLOTTED VALUES ARE STORED

% Areas
rb.area_divide_rad = area_divide_rad;

% Radial coordinate
rb.Radial_coordinate_cell = x_rad;

% Upstream flux (total + components)
rb.fluxuptot = fluxuptot;
%rb.(matlab.lang.makeValidName(sprintf(totname{1}))) = fluxuptot;
for i=1:size(fluxup,2)
    if any(fluxup(:,i))
        rb.fluxupcomp(:,i) = fluxupcomp(:,i);
        %rb.(matlab.lang.makeValidName(sprintf('Flux_decomp_%s',fluxname{i}))) = fluxupcomp(:,i);
    end
end

% Downstream flux (total + components)
rb.fluxdowntot = fluxdowntot;
%rb.(matlab.lang.makeValidName(sprintf(totname{2}))) = fluxdowntot;
for i=1:size(fluxdown,2)
    if any(fluxdown(:,i))
        rb.fluxdowncomp(:,i) = fluxdowncomp(:,i);
        %rb.(matlab.lang.makeValidName(sprintf('Flux_decomp_%s',fluxname{i}))) = fluxdowncomp(:,i);
    end
end

% Poloidally-integrated source (total + components)
rb.sourcetot = sourcetot;
%rb.(matlab.lang.makeValidName(sprintf(totname{3}))) = sourcetot;
for i=1:size(sourceint,2)
    if any(sourceint(:,i))
        rb.sourcecomp(:,i) = sourcecomp(:,i);
        %rb.(matlab.lang.makeValidName(sprintf('Source_decomp_%s',sourcename{i}))) = sourcecomp(:,i);
    end
end

% Poloidally integrated residual
rb.Residual(:) = coderes;

% Names
rb.flux_up_tot_name = totname{1};
rb.flux_down_tot_name = totname{2};
rb.flux_component_names = fluxname;
rb.source_tot_name = totname{3};
rb.source_component_names = sourcename;

end