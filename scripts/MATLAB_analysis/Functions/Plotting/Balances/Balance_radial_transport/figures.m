function [axgrid,axbal,axstrat] = figures(quantity,isplot,gmtry,strata_plot)
%
% figures creates axis handles for plotting grid and balance plots
%
%% GRID

% Create the figure
figure('windowstyle','docked');
axgrid = subplot('position',[0.3 0.1 0.4 0.85]); box on; hold on;

% Set the title
switch quantity
    case 'particles'
        if length(isplot)>1
            strtmp = sprintf('Particle balance: (%s',sprintf('%s,',gmtry.species{isplot}));
            strtmp(end) = ')';
        else
            strtmp = ['Particle balance: ',gmtry.species{isplot}];
        end
        title(axgrid,strtmp,'fontweight','normal','fontsize',10);
    case 'momentum'
        if length(isplot)>1
            strtmp = sprintf('Momentum balance: (%s',sprintf('%s,',gmtry.species{isplot}));
            strtmp(end) = ')';
        else
            strtmp = ['Momentum balance: ',gmtry.species{isplot}];
        end
        title(axgrid,strtmp,'fontweight','normal','fontsize',10);
    case 'total_pressure'
        title(axgrid,'Total pressure balance','fontweight','normal','fontsize',10);
    case 'electron_energy'
        title(axgrid,'Electron energy balance','fontweight','normal','fontsize',10);
    case 'ion_energy'
        title(axgrid,'Ion energy balance','fontweight','normal','fontsize',10);
    case 'total_energy'
        title(axgrid,'Total energy balance','fontweight','normal','fontsize',10);
    otherwise
        error('Error: Figure type unknown.');
end

%% RADIAL BALANCE

% Create the figure
figure('windowstyle','docked');
height = 0.4;
width = 0.2;
margin = (1-3*width)/4;

% Total balance
axbal(1) = subplot('position',[margin 1.15*height width height]); box on; hold on;
position = get(axbal(1),'Position'); lgd = legend(axbal(1),'show','location','southoutside');
set(axbal(1), 'Position', position);

% Decomposition of poloidally-integrated fluxes
axbal(2) = subplot('position',[width+2*margin 1.15*height width height]); box on; hold on;
position = get(axbal(2),'Position'); lgd = legend(axbal(2),'show','location','southoutside');
set(axbal(2), 'Position', position);      

% Decomposition of poloidally-integrated sources
axbal(3) = subplot('position',[2*width+3*margin 1.15*height width height]); box on; hold on;
position = get(axbal(3),'Position'); lgd = legend(axbal(3),'show','location','southoutside');
set(axbal(3), 'Position', position);  
 
%% POLOIDAL BALANCE

% Create the figure
figure('windowstyle','docked');
height = 0.4;
width = 0.2;
margin = (1-4*width)/5;

% Total balance
axbal(4) = subplot('position',[margin 1.15*height width height]); box on; hold on;
position = get(axbal(4),'Position'); lgd = legend(axbal(4),'show','location','southoutside');
set(axbal(4), 'Position', position);

% Decomposition of fluxes at the separatrix
axbal(5) = subplot('position',[width+2*margin 1.15*height width height]); box on; hold on;
position = get(axbal(5),'Position'); lgd = legend(axbal(5),'show','location','southoutside');
set(axbal(5), 'Position', position);

% Decomposition of fluxes at the wall
axbal(6) = subplot('position',[2*width+3*margin 1.15*height width height]); box on; hold on;
position = get(axbal(6),'Position'); lgd = legend(axbal(6),'show','location','southoutside');
set(axbal(6), 'Position', position);

% Decomposition of radially-integrated sources
axbal(7) = subplot('position',[3*width+4*margin 1.15*height width height]); box on; hold on;
position = get(axbal(7),'Position'); lgd = legend(axbal(7),'show','location','southoutside');
set(axbal(7), 'Position', position);

%% STRATA DECOMPOSITION

% Ceate the figure
if strata_plot
	figure('windowstyle','docked');
	margin = 0.04;
 	width = (1-5*margin)/4;
	height = (1-6*margin)/2;
           
% Strata decomposition of poloidally-integrated EIRENE sources            
	axstrat(1) = subplot('position',[margin height+9/2*margin width height]); box on; hold on;
	title(axstrat(1),'Due to atom-plasma collisions','fontweight','normal');
	axstrat(2) = subplot('position',[width+2*margin height+9/2*margin width height]); box on; hold on;
	title(axstrat(2),'Due to molecule-plasma collisions','fontweight','normal');
	axstrat(3) = subplot('position',[2*width+3*margin height+9/2*margin width height]); box on; hold on;
	title(axstrat(3),'Due to test ion-plasma collisions','fontweight','normal');
	axstrat(4) = subplot('position',[3*width+4*margin height+9/2*margin width height]); box on; hold on;
	title(axstrat(4),'Due to recombination','fontweight','normal');
 
% Strata decomposition of radially-integrated EIRENE sources    
    axstrat(5) = subplot('position',[margin 3/2*margin width height]); box on; hold on;
	title(axstrat(5),'Due to atom-plasma collisions','fontweight','normal');
	axstrat(6) = subplot('position',[width+2*margin 3/2*margin width height]); box on; hold on;
	title(axstrat(6),'Due to molecule-plasma collisions','fontweight','normal');
	axstrat(7) = subplot('position',[2*width+3*margin 3/2*margin width height]); box on; hold on;
	title(axstrat(7),'Due to test ion-plasma collisions','fontweight','normal');
	axstrat(8) = subplot('position',[3*width+4*margin 3/2*margin width height]); box on; hold on; 
	title(axstrat(8),'Due to recombination','fontweight','normal');

% Titles    
    axstrat(9) = subplot('position',[0.5 2*height+11/2*margin 0.001 0.001],'visible','off');
	axstrat(10) = subplot('position',[0.5 height+5/2*margin 0.001 0.001],'visible','off');

else
	axstrat = 0;
end

end