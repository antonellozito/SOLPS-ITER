function sources = sources_distribution(BAL_QUANT,BALFILE,indbal,SPECIES_INDEX,gmtry,reverse,DEFAULT_REGION,AREAEND,AREATYPE,...
    structure,geometry,equilibrium,PLOT_TYPE,REGION,COLORBAR,PLOT_STRUCTURE,PLOT_EQUILIBRIUM,PLOT_SEPARATRIX,PLOT_BOUNDARY,PLOT_GRID,...
    LINESTYLE_STRUCTURE,LINEWIDTH_STRUCTURE,COLOR_STRUCTURE,FLUX_SURFACES,LINESTYLE_EQUILIBRIUM,LINEWIDTH_EQUILIBRIUM,COLOR_EQUILIBRIUM,...
    LINESTYLE_SEPARATRIX,LINEWIDTH_SEPARATRIX,COLOR_SEPARATRIX,LINESTYLE_BOUNDARY,LINEWIDTH_BOUNDARY,COLOR_BOUNDARY,LINESTYLE_GRID,LINEWIDTH_GRID,COLOR_GRID,...
    LIMITS,FMIN,FMAX)

%% REGIONS DEFINITION

top = gmtry.nx/2;
xcut = find(diff(gmtry.leftix(:,1))<1);

if length(xcut)==2
    switch DEFAULT_REGION(1:2)
        case {'li','ui'}
            switch DEFAULT_REGION(3)
                case 'x'
                    x_start = 2;
                    x_end = xcut(1)-1;
                    x_start_plot = 1;
                    x_end_plot = xcut(1)-1;
                case 'm'
                    x_start = 2;
                    x_end = gmtry.imp+1;
                    x_start_plot = 1;
                    x_end_plot = gmtry.imp+1;
            end
        case {'uo','lo'}
            switch DEFAULT_REGION(3)
                case 'x'
                    x_start = xcut(2)+1;
                    x_end = size(indbal,1)-1;
                    x_start_plot = xcut(2)+1;
                    x_end_plot = size(indbal,1);
                case 'm'
                    x_start = gmtry.omp+1;
                    x_end = size(indbal,1)-1;
                    x_start_plot = gmtry.omp+1;
                    x_end_plot = size(indbal,1);
            end
    end
% elseif length(xcut)==5
%     switch DEFAULT_REGION(1:2)
%         case 'li'
%             x_start = 2;
%             x_end = xcut(1)-1;
%         case 'ui'
%             x_start = xcut(2);
%             x_end = xcut(3)-1;
%         case 'uo'
%             x_start = xcut(3)+2;
%             x_end = xcut(4);
%         case 'lo'
%             x_start = xcut(5)+1;
%             x_end = size(indbal,1)-1;
%     end
% elseif isempty(xcut)
%     switch DEFAULT_REGION(1:2)
%         case {'li','ui','uo','lo'}
%             x_start = 2;
%             x_end = size(indbal,1)-1;
%     end
    
end

y_start_plot = gmtry.sep+1;
y_end_plot = gmtry.ny-1;

%% CALCULATE THE FLUXES

switch BAL_QUANT
    case 'particles'
        sources = distribution_sources_part(BALFILE,indbal,SPECIES_INDEX,gmtry,reverse,DEFAULT_REGION,AREAEND,AREATYPE,'rho',x_start,x_end);
    case 'force'
        sources = distribution_sources_force(BALFILE,indbal,SPECIES_INDEX,gmtry,reverse,DEFAULT_REGION,AREAEND,AREATYPE,'rho',x_start,x_end);
    case 'momentum'
        sources = distribution_sources_mom(BALFILE,indbal,SPECIES_INDEX,gmtry,reverse,DEFAULT_REGION,AREAEND,AREATYPE,'rho',x_start,x_end);
    case 'total_pressure'
        sources = distribution_sources_totpress(BALFILE,indbal,gmtry,reverse,DEFAULT_REGION,AREATYPE,'rho',x_start,x_end);
    case 'electron_energy'
        sources = distribution_sources_elen(BALFILE,indbal,gmtry,reverse,DEFAULT_REGION,AREAEND,AREATYPE,'rho',x_start,x_end);
    case 'ion_energy'
        sources = distribution_sources_ionen(BALFILE,indbal,gmtry,reverse,DEFAULT_REGION,AREAEND,AREATYPE,'rho',x_start,x_end);
    case 'total_energy'
        sources = distribution_sources_toten(BALFILE,indbal,gmtry,reverse,DEFAULT_REGION,AREAEND,AREATYPE,'rho',x_start,x_end);
    otherwise
        error('Error: Balance quantity ''%s'' not supported.',BAL_QUANT);
end

for i = 1:size(sources,2)
    data(i,:) = sources{i}.sourcetot;
end
data((size(sources,2)+1),:) = sources{(size(sources,2))}.sourcetot;
data(:,end+1) = data(:,end);
 
%% CREATE THE FIGURE

figure;
hold on;
axis tight;
axis equal;

%% PLOT THE FLUX

% Computational grid

    switch PLOT_TYPE
        case 'patchplot'
            patchplot(geometry,data,x_start_plot:x_end_plot,y_start_plot:y_end_plot,[],[],[],true);
        case 'contourfplot'
            contourfplot(geometry,data,x_start_plot:x_end_plot,y_start_plot:y_end_plot,[],[],[],[],true);
        case 'contourplot'
            contourplot(geometry,data,x_start_plot:x_end_plot,y_start_plot:y_end_plot,[],[],[],[],true);
    end

%% PLOT ADDITIONAL FIELDS

if PLOT_GRID
    plot_b2_grid(geometry,COLOR_GRID,'Linewidth',LINEWIDTH_GRID,'Linestyle',LINESTYLE_GRID);
end

if PLOT_BOUNDARY
    plot_boundary(geometry,COLOR_BOUNDARY,'Linewidth',LINEWIDTH_BOUNDARY,'Linestyle',LINESTYLE_BOUNDARY);
end

if PLOT_SEPARATRIX
    plot_separatrix(geometry,COLOR_SEPARATRIX,'Linewidth',LINEWIDTH_SEPARATRIX,'Linestyle',LINESTYLE_SEPARATRIX);
end

if PLOT_EQUILIBRIUM
    plot_equilibrium(equilibrium,FLUX_SURFACES,LINESTYLE_EQUILIBRIUM,LINEWIDTH_EQUILIBRIUM,COLOR_EQUILIBRIUM);
end

if PLOT_STRUCTURE
    plot_structure(structure,COLOR_STRUCTURE,'Linewidth',LINEWIDTH_STRUCTURE,'Linestyle',LINESTYLE_STRUCTURE);
end

%% PLOT PROPERTIES

set(gca,'Box','on');

set(0,'DefaultAxesTitleFontWeight','normal');

if LIMITS
    colorbarpwn(FMIN,FMAX,'colorP',[1 0 0],'colorN',[0 0 1]);
    caxis([FMIN FMAX]);
end

if COLORBAR

    colorbar;

    switch AREATYPE
        case 'parallel'
            direction = 'Parallel';
        case 'contact'
            direction = 'Poloidal';
        case 'none'
            direction = 'Poloidal';
    end

    switch BAL_QUANT
    case 'particles'
        name = sprintf('%s particle source',direction);
    case 'force'
        name = sprintf('%s force',direction);
    case 'momentum'
        name = sprintf('%s momentum source',direction);
    case 'total_pressure'
        name = sprintf('Total pressure source');
    case 'electron_energy'
        name = sprintf('%s electron energy source',direction);
    case 'ion_energy'
        name = sprintf('%s ion energy source',direction);
    case 'total_energy'
        name = sprintf('%s total energy source',direction);
    end
    set(get(colorbar,'title'),'string',name,'fontsize',16,'interpreter','latex');

end
        
[xlimits,ylimits,orientation,length,height] = plot_size('',REGION);
        
xlim(xlimits);
ylim(ylimits);
xlabel('$R$ [m]','fontsize',16,'interpreter','latex');
ylabel('$z$ [m]','fontsize',16,'interpreter','latex');

%% PRINT THE PLOT

set(gcf,'PaperOrientation',orientation);
set(gcf,'Position', [400 400 length height]);

end
