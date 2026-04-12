function pb = poloidal_balance(transport_mode,varargin)

transport_mode = lower(char(transport_mode));

switch transport_mode
    case 'parallel'
        [flux,source,res,totname,fluxname,sourcename,gmtry,indbal,ismom,axbal,units,default_region,reverse,areaend,areatype,polbaldist,residuals] = deal(varargin{:});
%
% poloidal_balance makes balance plots with poloidal resolution (integrating in the radial direction) in a given region          
%                                                                                                                                
% flux:        An (nx*ny*nd) sized matrix, where nd is the number of different fluxes into which the total flux is decomposed    
%              Comprising the flux from each component in the entire grid                                                        
% source:      An (nx*ny*nd) sized matrix, where nd is the number of different sources into which the total source is decomposed 
%              Comprising the source from each component in the entire grid                                                      
% res:         The code residual                                                                                                 
% totname:     A cell of length 3 with strings stating the names of                                                              
%              (1) flux, (2) source, (3) residual                                              
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
% polbaldist:  Distance used on the x-axis of plots (mapped to the first SOL ring)                                               
% residuals:   If true then residual are also plotted in the poloidal balance plots                                              
%
%% RADIAL INTEGRATION OF FLUXES AND SOURCES

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

quantity = evalin('base', 'BAL_QUANT');

% Radially-integrated poloidal fluxes through the cell edges along the poloidal length of the balance volume
% for each flux component

fluxedge = [];
if strcmp(quantity,'force')

    balfile = evalin('base', 'BALFILE');
    isplot = evalin('base', 'SPECIES_INDEX');
    tmp = ncread(balfile,'na');
    na = sum(tmp(:,:,isplot),3);

    for i=1:size(flux,3)
        fluxedge(:,i) = sum_radialedge(flux(:,:,i)./na,indbal,gmtry);
    end

    poldiv_flux = zeros(nx,ny,size(flux,3));
    for k=1:size(flux,3)
        for ix=1:nx
            for iy=1:ny
                if rightix(ix,iy)>nx
                    continue;
                end
                poldiv_flux(ix,iy,k) = flux(ix,iy,k)-flux(rightix(ix,iy),rightiy(ix,iy),k);
            end
        end
    end

    poldiv_fluxedge = [];
    for i=1:size(poldiv_flux,3)
        poldiv_fluxedge(:,i) = sum_radial(transport_mode,poldiv_flux(:,:,i)./na,indbal,gmtry);
    end

else

    for i=1:size(flux,3)
        fluxedge(:,i) = sum_radialedge(flux(:,:,i),indbal,gmtry);
    end

end

% Radially-integrated sources along the poloidal length of the balance volume
% for each source component

sourceint = [];
if strcmp(quantity,'force')

    for i=1:size(source,3)
        sourceint(:,i) = sum_radial(transport_mode,source(:,:,i)./na,indbal,gmtry);
    end

else

    for i=1:size(source,3)
        sourceint(:,i) = sum_radial(transport_mode,source(:,:,i),indbal,gmtry);
    end

end

% Poloidally-integrated residual

if strcmp(quantity,'force')

    resint = sum_radial(transport_mode,res./na,indbal,gmtry);

else

    resint = sum_radial(transport_mode,res,indbal,gmtry);

end

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

%% CALCULATION OF THE AREAS

% Poloidal- or parallel-directed area at all the cell boundaries for each cell
area_divide = calc_area(transport_mode,gmtry,areatype);

% Total areas at the ends which fluxes and sources will be divided by
switch quantity
    case {'force','total_pressure'}
        area_divide_pol = 1;
    otherwise
        switch areaend
            case 'left'
                area_divide_pol = sum(calc_fluxend(transport_mode,area_divide,indbal,'left',rightix,rightiy));
            case 'right'
                area_divide_pol = sum(calc_fluxend(transport_mode,area_divide,indbal,'right',rightix,rightiy));
            case 'none'
                area_divide_pol = 1;           
        end
end

%% PRODUCE THE PLOTS

% Poloidal/parallel coordinates for cell-center quantities and edge-centered quantities
[x_pol,x_poledge] = calc_poloidalcoordinate(transport_mode,gmtry,indbal,default_region,polbaldist);
x_pol_interp = linspace(min(x_pol),max(x_pol),500);
x_poledge_interp = linspace(min(x_poledge),max(x_poledge),500);

% Total balance with residuals
cmap = gmtry.cmap;
title(axbal(1),'Poloidal balance','fontweight','normal','fontsize',9);
axis(axbal(1),'tight');
fluxtot = momfac*reversefac*sum(fluxedge,2)/area_divide_pol;
fluxtot_interp = interp1(x_poledge, fluxtot, x_poledge_interp, 'makima', 'extrap');
plot(x_poledge_interp,fluxtot_interp,'parent',axbal(1),'displayname',totname{1},'linewidth',1,'color',cmap(1,:)); cmap=circshift(cmap,-1);
sourcetot = momfac*sum(sourceint,2)/area_divide_pol;
sourcetot_interp = interp1(x_pol, sourcetot, x_pol_interp, 'makima', 'extrap');
plot(x_pol_interp,sourcetot_interp,'parent',axbal(1),'displayname',totname{2},'linewidth',1,'color',cmap(1,:));
coderes = momfac*(resint/area_divide_pol)';
coderes_interp = interp1(x_pol, coderes, x_pol_interp, 'makima', 'extrap');
if residuals
    plot(x_pol_interp,coderes_interp,'-m','parent',axbal(1),'displayname',[totname{3},' (code)'],'linewidth',1);
end

% Check the level of agreement between post-calculated and code-calculated residuals
if strcmp(quantity,'force')
    postres = momfac*(sum(sourceint,2)+ sum(poldiv_fluxedge,2)  )/area_divide_pol;
else
    postres = momfac*(sum(sourceint,2)-diff(sum(fluxedge,2)))/area_divide_pol;
end
postres_interp = interp1(x_pol, postres, x_pol_interp, 'makima', 'extrap');
if residuals
    plot(x_pol_interp,postres_interp,'-g','parent',axbal(1),'displayname',[totname{3},' (post-cal.)'],'linewidth',1);
end
fprintf('Poloidal balance: the maximum difference between code- and post-calculated residuals is %e%%\n',max(abs((coderes-postres)./coderes)*100));

% Decompose fluxes
cmap = gmtry.cmap;
txt = sprintf('Decomposition of\n%s',totname{1});
title(axbal(2),txt,'fontweight','normal','fontsize',9);
axis(axbal(2),'tight');
for i=1:size(fluxedge,2)
    if any(fluxedge(:,i))
        fluxcomp(:,i) = momfac*reversefac*fluxedge(:,i)./area_divide_pol';
        fluxcomp_interp(:,i) = interp1(x_poledge, fluxcomp(:,i), x_poledge_interp, 'makima', 'extrap');
        plot(x_poledge_interp,fluxcomp_interp(:,i),'parent',axbal(2),'displayname',fluxname{i},'linewidth',1,'color',cmap(1,:)); cmap=circshift(cmap,-1);
    end
end

% Decompose sources
cmap = gmtry.cmap;
txt = sprintf('Decomposition of\n%s',totname{2});
title(axbal(3),txt,'fontweight','normal','fontsize',9);
axis(axbal(3),'tight');
for i=1:size(sourceint,2)
    if any(sourceint(:,i))
        sourcecomp(:,i) = momfac*sourceint(:,i)./area_divide_pol';
        sourcecomp_interp(:,i) = interp1(x_pol, sourcecomp(:,i), x_pol_interp, 'makima', 'extrap');
        plot(x_pol_interp,sourcecomp_interp(:,i),'parent',axbal(3),'displayname',sourcename{i},'linewidth',1,'color',cmap(1,:)); cmap=circshift(cmap,-1);
    end
end

% Set x- and y-label
for j=1:3
    switch polbaldist
        case 'parallel'
            switch default_region(2)
                case 'i'
                    txt = 'inner target';
                case 'o'
                    txt = 'outer target';
            end
        case 'poloidal'
             switch default_region(2)
                case 'i'
                    txt = 'inner target';
                case 'o'
                    txt = 'outer target';
            end  
    end
    xlabel(axbal(j),sprintf('%s distance from %s [m]',polbaldist,txt));
    ylabel(axbal(j),['[',units,']']);
end

% Set the same x-axis limits for all poloidal balance plots:

set(axbal(3),'xlim',[min(x_pol) max(x_pol)]);
set(axbal(1),'xlim',get(axbal(3),'xlim'));
set(axbal(2),'xlim',get(axbal(3),'xlim'));

% Set the same y-axis limits for all poloidal balance plots:
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
pb.area_divide_pol = area_divide_pol;

% Poloidal/parallel coordinates
pb.Poloidal_coordinate_cell = x_pol;
pb.Poloidal_coordinate_edge = x_poledge;

% Radially-integrated flux (total + components)
%pb.(matlab.lang.makeValidName(sprintf(totname{1}))) = fluxtot;
pb.fluxtot = fluxtot;
for i=1:size(fluxedge,2)
    if any(fluxedge(:,i))
        %pb.(matlab.lang.makeValidName(sprintf('Flux_decomp_%s',fluxname{i}))) = fluxcomp(:,i);
        pb.fluxcomp(:,i) = fluxcomp(:,i);
    end
end

% Radially-integrated source (total + components)
%pb.(matlab.lang.makeValidName(sprintf(totname{2}))) = sourcetot;
pb.sourcetot = sourcetot;
for i=1:size(sourceint,2)
    if any(sourceint(:,i))
        %pb.(matlab.lang.makeValidName(sprintf('Source_decomp_%s',sourcename{i}))) = sourcecomp(:,i);
        pb.sourcecomp(:,i) = sourcecomp(:,i);
    end
end

% Radially-integrated residual
pb.Residual(:) = coderes;

% Names
pb.flux_tot_name = totname{1};
pb.flux_component_names = fluxname;
pb.source_tot_name = totname{2};
pb.source_component_names = sourcename;

    case 'radial'
        [flux,source,res,totname,fluxname,sourcename,gmtry,indbal,ismom,axbal,units,default_region,areaend,areatype,polbaldist,residuals] = deal(varargin{:});
%
% poloidal_balance makes balance plots with poloidal resolution (integrating in the radial direction) in a given region          
%                                                                                                                                
% flux:        An (nx*ny*nd) sized matrix, where nd is the number of different fluxes into which the total flux is decomposed    
%              Comprising the flux from each component in the entire grid                                                        
% source:      An (nx*ny*nd) sized matrix, where nd is the number of different sources into which the total source is decomposed 
%              Comprising the source from each component in the entire grid                                                      
% res:         The code residual                                                                                                 
% totname:     A cell of length 4 with strings stating the names of                                                              
%              (1) separatrix flux, (2) wall boundary flux, (3) source, (4) residual                                              
% fluxname:    A cell of length nd with strings stating the names of each flux component                                         
% sourcename:  A cell of length nd with strings stating the names of each source component                                       
% gmtry:       Structure containing commonly-used variables                                                                      
% indbal:      Logical matrix of size nx*ny that is true for cells where balance should be performed                             
% ismom:       True if we are performing momentum balance                                                                        
% axbal:       Array of axes into which balance plots will be placed                                                             
% units:       String for units given on y axes                                                                                  
% region:      SOL region of the computational grid on which perform the balance                                                
% areaend:     Defines the radial end of the balance region at which areas will be calculated                                    
% areatype:    Type of area that radial fluxes are divided by                                                                     
% polbaldist:  Distance used on the x-axis of plots (mapped to the first SOL ring)                                               
% residuals:   If true then residual are also plotted in the poloidal balance plots                                              
%
%% RADIAL INTEGRATION OF FLUXES AND SOURCES

% Geometry variables
topix = gmtry.topix+1;
topiy = gmtry.topiy+1;
bottomix = gmtry.bottomix+1;
bottomiy = gmtry.bottomiy+1;
leftix = gmtry.leftix+1;
leftiy = gmtry.leftiy+1;
rightix = gmtry.rightix+1;
rightiy = gmtry.rightiy+1;

% Radial fluxes through separatrix and wall boundary along the poloidal length of the balance volume
% for each flux component
fluxsep = [];
fluxwall = [];
for i=1:size(flux,3)
    fluxsep(:,i) = calc_fluxend(transport_mode,flux(:,:,i),indbal,'bottom');
    fluxwall(:,i) = calc_fluxend(transport_mode,flux(:,:,i),indbal,'top',topix,topiy);
end

% Radially-integrated sources along the poloidal length of the balance volume
% for each source component
sourceint = [];
for i=1:size(source,3)
    sourceint(:,i) = sum_radial(transport_mode,source(:,:,i),indbal,gmtry);
end

% Radially-integrated residual:
resint = sum_radial(transport_mode,res,indbal,gmtry);

% Account for flux reversal (only for pressure balance):
reversefac = 1;
momfac = 1;
if ismom
    reversefac = 1;
    momfac = -1;
    momfac = momfac*-sign(mean(mean(gmtry.bb(:,:,3))));
end

%% CALCULATION OF THE AREAS

% Radial-directed area at all the cell boundaries for each cell
area_divide = calc_area(transport_mode,gmtry,areatype);

% Total areas at the ends which fluxes and sources will be divided by::
switch areaend
    case 'bottom'
        area_divide_pol = calc_fluxend(transport_mode,area_divide,indbal,'bottom');
    case 'top'
        area_divide_pol = calc_fluxend(transport_mode,area_divide,indbal,'top',topix,topiy);
    case 'none'
        area_divide_pol = 1;
end

%% PRODUCE THE PLOTS

% Poloidal/parallel coordinate
x_pol = calc_poloidalcoordinate(transport_mode,gmtry,indbal,default_region,polbaldist);
x_pol_interp = linspace(min(x_pol),max(x_pol),500);

% Total balance with residuals
cmap = gmtry.cmap;
title(axbal(1),'Poloidal balance','fontweight','normal','fontsize',9);
axis(axbal(1),'tight');
fluxseptot = momfac*reversefac*sum(fluxsep,2)'./area_divide_pol;
if default_region(2) == 'm'
    plot(x_pol,fluxseptot,'marker','.','parent',axbal(1),'displayname',totname{1},'linewidth',1,'color',cmap(1,:)); cmap=circshift(cmap,-1);
else
    fluxseptot_interp = interp1(x_pol, fluxseptot, x_pol_interp, 'makima', 'extrap');
    plot(x_pol_interp,fluxseptot_interp,'parent',axbal(1),'displayname',totname{1},'linewidth',1,'color',cmap(1,:)); cmap=circshift(cmap,-1);
end
fluxwalltot = momfac*reversefac*sum(fluxwall,2)'./area_divide_pol;
if default_region(2) == 'm'
    plot(x_pol,fluxwalltot,'marker','.','parent',axbal(1),'displayname',totname{2},'linewidth',1,'color',cmap(1,:)); cmap=circshift(cmap,-1);
else
    fluxwalltot_interp = interp1(x_pol, fluxwalltot, x_pol_interp, 'makima', 'extrap');
    plot(x_pol_interp,fluxwalltot_interp,'parent',axbal(1),'displayname',totname{2},'linewidth',1,'color',cmap(1,:)); cmap=circshift(cmap,-1);
end
sourcetot = momfac*sum(sourceint,2)'./area_divide_pol;
if default_region(2) == 'm'
    plot(x_pol,sourcetot,'marker','.','parent',axbal(1),'displayname',totname{3},'linewidth',1,'color',cmap(1,:));
else
    sourcetot_interp = interp1(x_pol, sourcetot, x_pol_interp, 'makima', 'extrap');
    plot(x_pol_interp,sourcetot_interp,'parent',axbal(1),'displayname',totname{3},'linewidth',1,'color',cmap(1,:));
end
coderes = momfac*(resint./area_divide_pol);
if default_region(2) == 'm'
    if residuals
        plot(x_pol,coderes,'-m','parent',axbal(1),'displayname',[totname{4},' (code)'],'linewidth',1);
    end
else
    coderes_interp = interp1(x_pol, coderes, x_pol_interp, 'makima', 'extrap');
    if residuals
        plot(x_pol_interp,coderes_interp,'-m','parent',axbal(1),'displayname',[totname{4},' (code)'],'linewidth',1);
    end
end

% Check the level of agreement between post-calculated and code-calculated residuals
postres = momfac*(reversefac*(sum(fluxsep,2)-sum(fluxwall,2))+sum(sourceint,2))'./area_divide_pol;
if default_region(2) == 'm'
    if residuals
        plot(x_pol,postres,'-g','parent',axbal(1),'displayname',[totname{4},' (post-cal.)'],'linewidth',1);
    end
else
    postres_interp = interp1(x_pol, postres, x_pol_interp, 'makima', 'extrap');
    if residuals
        plot(x_pol_interp,postres_interp,'-g','parent',axbal(1),'displayname',[totname{4},' (post-cal.)'],'linewidth',1);
    end
end
fprintf('Poloidal balance: the maximum difference between code- and post-calculated residuals is %e%%\n',max(abs((coderes-postres)./coderes)*100));

% Decompose fluxes at the separatrix
cmap = gmtry.cmap;
txt = sprintf('Decomposition of\n%s',totname{1});
title(axbal(2),txt,'fontweight','normal','fontsize',9);
axis(axbal(2),'tight');
for i=1:size(fluxsep,2)
    if any(fluxsep(:,i))
        fluxsepcomp(:,i) = momfac*reversefac*fluxsep(:,i)'./area_divide_pol;
        if default_region(2) == 'm'
            plot(x_pol,fluxsepcomp(:,i),'marker','.','parent',axbal(2),'displayname',fluxname{i},'linewidth',1,'color',cmap(1,:)); cmap=circshift(cmap,-1);
        else
            fluxsepcomp_interp(:,i) = interp1(x_pol, fluxsepcomp(:,i), x_pol_interp, 'makima', 'extrap');
            plot(x_pol_interp,fluxsepcomp_interp(:,i),'parent',axbal(2),'displayname',fluxname{i},'linewidth',1,'color',cmap(1,:)); cmap=circshift(cmap,-1);
        end
    end
end

% Decompose fluxes at the wall
cmap = gmtry.cmap;
txt = sprintf('Decomposition of\n%s',totname{2});
title(axbal(3),txt,'fontweight','normal','fontsize',9);
axis(axbal(3),'tight');
for i=1:size(fluxwall,2)
    if any(fluxwall(:,i))
        fluxwallcomp(:,i) = momfac*reversefac*fluxwall(:,i)'./area_divide_pol;
        if default_region(2) == 'm'
            plot(x_pol,fluxwallcomp(:,i),'marker','.','parent',axbal(3),'displayname',fluxname{i},'linewidth',1,'color',cmap(1,:)); cmap=circshift(cmap,-1);
        else
            fluxwallcomp_interp(:,i) = interp1(x_pol, fluxwallcomp(:,i), x_pol_interp, 'makima', 'extrap');
            plot(x_pol_interp,fluxwallcomp_interp(:,i),'parent',axbal(3),'displayname',fluxname{i},'linewidth',1,'color',cmap(1,:)); cmap=circshift(cmap,-1);
        end        
    end
end

% Decompose sources
cmap = gmtry.cmap;
txt = sprintf('Decomposition of\n%s',totname{3});
title(axbal(4),txt,'fontweight','normal','fontsize',9);
axis(axbal(4),'tight');
for i=1:size(sourceint,2)
    if any(sourceint(:,i))
        sourcecomp(:,i) = momfac*sourceint(:,i)'./area_divide_pol;
        if default_region(2) == 'm'
            plot(x_pol,sourcecomp(:,i),'marker','.','parent',axbal(4),'displayname',sourcename{i},'linewidth',1,'color',cmap(1,:)); cmap=circshift(cmap,-1);
        else
            sourcecomp_interp(:,i) = interp1(x_pol, sourcecomp(:,i), x_pol_interp, 'makima', 'extrap');
            plot(x_pol_interp,sourcecomp_interp(:,i),'parent',axbal(4),'displayname',sourcename{i},'linewidth',1,'color',cmap(1,:)); cmap=circshift(cmap,-1);
        end        
    end
end

% Set x- and y-label
for j=1:4
    switch polbaldist
        case 'parallel'
            switch default_region(1)
                case 'i'
                    txt = 'inner target';
                case 'o'
                    txt = 'outer target';
            end
        case 'poloidal'
             switch default_region(1)
                case 'i'
                    txt = 'inner target';
                case 'o'
                    txt = 'outer target';
            end  
    end
    xlabel(axbal(j),sprintf('%s distance from %s [m]',polbaldist,txt));
    ylabel(axbal(j),['[',units,']']);
end

% Set the same x-axis limits for all poloidal balance plots:

% set(axbal(3),'xlim',[min(x_pol) max(x_pol)]);
% set(axbal(1),'xlim',get(axbal(3),'xlim'));
% set(axbal(2),'xlim',get(axbal(3),'xlim'));

% Set the same y-axis limits for all poloidal balance plots:
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
pb.area_divide_pol = area_divide_pol;

% Poloidal/parallel coordinate
pb.Poloidal_coordinate = x_pol;

% Flux at the separatrix (total + components)
%pb.(matlab.lang.makeValidName(sprintf(totname{1}))) = fluxseptot;
pb.fluxseptot = fluxseptot;
for i=1:size(fluxsep,2)
    if any(fluxsep(:,i))
        %pb.(matlab.lang.makeValidName(sprintf('Flux_decomp_%s',fluxname{i}))) = fluxsepcomp(:,i);
        pb.fluxsepcomp(:,i) = fluxsepcomp(:,i);
    end
end

% Flux at the wall (total + components)
%pb.(matlab.lang.makeValidName(sprintf(totname{2}))) = fluxwalltot;
pb.fluxwalltot = fluxwalltot;
for i=1:size(fluxwall,2)
    if any(fluxwall(:,i))
        %pb.(matlab.lang.makeValidName(sprintf('Flux_decomp_%s',fluxname{i}))) = fluxwallcomp(:,i);
        pb.fluxwallcomp(:,i) = fluxwallcomp(:,i);
    end
end

% Radially-integrated source (total + components)
%pb.(matlab.lang.makeValidName(sprintf(totname{3}))) = sourcetot;
pb.sourcetot = sourcetot;
for i=1:size(sourceint,2)
    if any(sourceint(:,i))
        %pb.(matlab.lang.makeValidName(sprintf('Source_decomp_%s',sourcename{i}))) = sourcecomp(:,i);
        pb.sourcecomp(:,i) = sourcecomp(:,i);
    end
end

% Radially integrated residual
pb.Residual(:) = coderes;

% Names
pb.flux_sep_tot_name = totname{1};
pb.flux_wall_tot_name = totname{2};
pb.flux_component_names = fluxname;
pb.source_tot_name = totname{3};
pb.source_component_names = sourcename;
    otherwise
        error('Error: Transport mode ''%s'' not supported.',transport_mode);
end
