function strata_plots(eirene_atom,eirene_mol,eirene_tion,eirene_rc,titlestr,namestr,gmtry,indbal,nstra,axstrat,axbal,radial_coordinate,poloidal_coordinate,area_divide_rad,area_divide_pol,reverse,ismom)
%
% strata_plots decomposes the EIRENE source components in the different strata for both radial balance plots and poloidal balance plots          
% 
% eirene_atom:     An (nx*ny*nstra) sided matrix for the source component due to atom-plasma collisions
%                  where nstra is the number of different strata
% eirene_mol:      An (nx*ny*nstra) sided matrix for the source component due to molecule-plasma collisions
%                  where nstra is the number of different strata
% eirene_tion:     An (nx*ny*nstra) sided matrix for the source component due to test ion-plasma collisions
%                  where nstra is the number of different strata
% eirene_rc:       An (nx*ny*nstra) sided matrix for the source component due to recombinations
%                  where nstra is the number of different strata
% titlestr:        Strings for the titles of the strata decomposition plots
% gmtry:           Structure containing commonly-used variables                                                                      
% indbal:          Logical matrix of size nx*ny that is true for cells where balance should be performed                             
% nstra:           Number of strata
% axstrat:         Array of axes into which strata decomposition plots will be placed                                                             
% axbal:           Array of axes into which balance plots will be placed   
% area_divide_rad: Areas which fluxes and sources in the radial balance plots are divided by
% area_divide_pol: Areas which fluxes and sources in the poloidal balance plots are divided by
% reverse:         True if the right-most end of the balance volume is upstream of the left-most end, otherwise false
% ismom:           True if we are performing momentum balance                                                                        
%
%% PRELIMINARY OPERATIONS

cmap = gmtry.cmap;

if ~reverse
    momfac = 1;
elseif ismom
    momfac = -1;
else
    momfac = 1;
end

% Titles
axes(axstrat(9));
text(0.5,0.5,titlestr{1},'horizontalalignment','center','fontsize',10);
axes(axstrat(10));
text(0.5,0.5,titlestr{2},'horizontalalignment','center','fontsize',10);

% Read the name of the strata

SIMULATION = evalin('base', 'SIMULATION');
temp = find(contains({SIMULATION.run.name},'b2.neutrals.parameters'));
file = SIMULATION.run(temp).file;
fid = fopen(file);
line = fgetl(fid);
while ~contains(line,'crcstra')
    line = fgetl(fid);
end
temp = extractAfter(line,'crcstra=');
temp = textscan(temp,'%s ',nstra);
for istra = 1:nstra
    stratum_type{istra} = temp{1}{istra}(2);
end

while ~contains(line,'species_start')
    line = fgetl(fid);
end
temp = extractAfter(line,'species_start=');
temp = textscan(temp,'%d, ',istra);
for istra = 1:nstra
    stratum_species_start{istra} = temp{1}(istra);
end

while ~contains(line,'species_end')
    line = fgetl(fid);
end
temp = extractAfter(line,'species_end=');
temp = textscan(temp,'%d, ',istra);
for istra = 1:nstra
    stratum_species_end{istra} = temp{1}(istra);
end

for istra = 1:nstra
    switch stratum_type{istra}
        case 'W'
            stratum_name{istra} = 'Recycling, inner target';
        case 'E'
            stratum_name{istra} = 'Recycling, outer target';
        case 'N'
            stratum_name{istra} = 'Recycling, wall';
        case 'S'
            stratum_name{istra} = 'Recycling, PFR';
        case 'C'
            stratum_name{istra} = 'Gas puff source';
        case 'V'
            stratum_name{istra} = 'Recombination';
        case 'T'
            stratum_name{istra} = 'Time-dependent source';
    end
end
for istra = 1:nstra
    if stratum_species_end{istra}-stratum_species_start{istra}==1
        stratum_name{istra} = append(stratum_name{istra},' (D)');
    elseif  stratum_species_end{istra}-stratum_species_start{istra}==7
        stratum_name{istra} = append(stratum_name{istra},' (N)');
    elseif  stratum_species_end{istra}-stratum_species_start{istra}==2
        stratum_name{istra} = append(stratum_name{istra},' (He)');
    end
end

fclose(fid);

%% POLOIDALLY-INTEGRATED SOURCES ALONG THE RADIAL DIRECTION 

x_rad = radial_coordinate;
tmp = get(axbal(2),'children');
x_rad_interp = get(tmp(1),'xdata');
cmap = repmat(gmtry.cmap,[nstra,1]);
tot_atom = repmat({zeros(size(x_rad_interp))},1,length(eirene_atom));
tot_mol = repmat({zeros(size(x_rad_interp))},1,length(eirene_mol));
tot_tion = repmat({zeros(size(x_rad_interp))},1,length(eirene_tion));
tot_rc = repmat({zeros(size(x_rad_interp))},1,length(eirene_rc));

% Individual strata plots
for istra = 1:nstra
    linestyle = repmat({'-','--',':','-.'},1,length(eirene_atom));
    % Source component due to atom-plasma collisions
    for ie = 1:length(eirene_atom)
        tmp = momfac*sum_poloidal(eirene_atom{ie}(:,:,istra),indbal,gmtry)./area_divide_rad;
        tmp_interp = interp1(x_rad, tmp, x_rad_interp, 'makima', 'extrap');
        if any(tmp)
            plot(x_rad_interp,tmp_interp,'parent',axstrat(1),'linewidth',1,'color',cmap(istra,:),'linestyle',linestyle{ie},'displayname',[sprintf('%s',stratum_name{istra}),namestr{ie}]);
            tot_atom{ie} = tot_atom{ie}+tmp_interp;
        end
    end
    linestyle = repmat({'-','--',':','-.'},1,length(eirene_mol));
    % Source component due to molecule-plasma collisions
    for ie = 1:length(eirene_mol)
        tmp = momfac*sum_poloidal(eirene_mol{ie}(:,:,istra),indbal,gmtry)./area_divide_rad;
        tmp_interp = interp1(x_rad, tmp, x_rad_interp, 'makima', 'extrap');
        if any(tmp)
            plot(x_rad_interp,tmp_interp,'parent',axstrat(2),'linewidth',1,'color',cmap(istra,:),'linestyle',linestyle{ie},'displayname',[sprintf('%s',stratum_name{istra}),namestr{ie}]);
            tot_mol{ie} = tot_mol{ie}+tmp_interp;
        end
    end
    linestyle = repmat({'-','--',':','-.'},1,length(eirene_tion));
    % Source component due to test ion-plasma collisions
    for ie = 1:length(eirene_tion)
        tmp = momfac*sum_poloidal(eirene_tion{ie}(:,:,istra),indbal,gmtry)./area_divide_rad;
        tmp_interp = interp1(x_rad, tmp, x_rad_interp, 'makima', 'extrap');
        if any(tmp)
            plot(x_rad_interp,tmp_interp,'parent',axstrat(3),'linewidth',1,'color',cmap(istra,:),'linestyle',linestyle{ie},'displayname',[sprintf('%s',stratum_name{istra}),namestr{ie}]);
            tot_tion{ie} = tot_tion{ie}+tmp_interp;
        end
    end
    linestyle = repmat({'-','--',':','-.'},1,length(eirene_rc));
    % Source component due to recombinations
    for ie = 1:length(eirene_rc)
        tmp = momfac*sum_poloidal(eirene_rc{ie}(:,:,istra),indbal,gmtry)./area_divide_rad;
        tmp_interp = interp1(x_rad, tmp, x_rad_interp, 'makima', 'extrap');
        if any(tmp)
            plot(x_rad_interp,tmp_interp,'parent',axstrat(4),'linewidth',1,'color',cmap(istra,:),'linestyle',linestyle{ie},'displayname',[sprintf('%s',stratum_name{istra}),namestr{ie}]);
            tot_rc{ie} = tot_rc{ie}+tmp_interp;
        end
    end
end

% Sum over strata plots
for ie = 1:length(eirene_atom)
    plot(x_rad_interp,tot_atom{ie},'linewidth',1,'color','k','linestyle',linestyle{ie},'parent',axstrat(1),'displayname',['Sum over strata ',namestr{ie}]);
    plot(x_rad_interp,tot_mol{ie},'linewidth',1,'color','k','linestyle',linestyle{ie},'parent',axstrat(2),'displayname',['Sum over strata ',namestr{ie}]);
    plot(x_rad_interp,tot_tion{ie},'linewidth',1,'color','k','linestyle',linestyle{ie},'parent',axstrat(3),'displayname',['Sum over strata ',namestr{ie}]);
    plot(x_rad_interp,tot_rc{ie},'linewidth',1,'color','k','linestyle',linestyle{ie},'parent',axstrat(4),'displayname',['Sum over strata ',namestr{ie}]);
end

% Plot properties
lgd = legend(axstrat(1),'show','location','best');
lgd = legend(axstrat(2),'show','location','best');
lgd = legend(axstrat(3),'show','location','best');
lgd = legend(axstrat(4),'show','location','best');
ylabel(axstrat(1),get(get(axbal(3),'ylabel'),'string'));
ylabel(axstrat(2),get(get(axbal(3),'ylabel'),'string'));
ylabel(axstrat(3),get(get(axbal(3),'ylabel'),'string'));
ylabel(axstrat(4),get(get(axbal(3),'ylabel'),'string'));
xlabel(axstrat(1),get(get(axbal(3),'xlabel'),'string'));
xlabel(axstrat(2),get(get(axbal(3),'xlabel'),'string'));
xlabel(axstrat(3),get(get(axbal(3),'xlabel'),'string'));
xlabel(axstrat(4),get(get(axbal(3),'xlabel'),'string'));
set(axstrat(1:4),'xlim',get(axbal(3),'xlim'));

% Set the same axes limits for all radial source plots:
ymin = 1E40;
ymax = -1E40;
for iax=1:4
    a = findobj(get(axstrat(iax),'children'),'type','line');
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
    set(axstrat(1:4),'ylim',[ymin ymax]);
end

%% RADIALLY-INTEGRATED SOURCES ALONG THE POLOIDAL DIRECTION 

x_pol = poloidal_coordinate;
tmp = get(axbal(end),'children');
x_pol_interp = get(tmp(1),'xdata');
tot_atom = repmat({zeros(size(x_pol_interp))},1,length(eirene_atom));
tot_mol = repmat({zeros(size(x_pol_interp))},1,length(eirene_mol));
tot_tion = repmat({zeros(size(x_pol_interp))},1,length(eirene_tion));
tot_rc = repmat({zeros(size(x_pol_interp))},1,length(eirene_rc));

% Individual strata plots
for istra = 1:nstra
    linestyle = repmat({'-','--',':','-.'},1,length(eirene_atom));
    % Source component due to atom-plasma collisions
    for ie = 1:length(eirene_atom)
        tmp = momfac*sum_radial(eirene_atom{ie}(:,:,istra),indbal,gmtry)/area_divide_pol;
        tmp_interp = interp1(x_pol, tmp, x_pol_interp, 'makima', 'extrap');
        if any(tmp)
            plot(x_pol_interp,tmp_interp,'parent',axstrat(5),'linewidth',1,'color',cmap(istra,:),'linestyle',linestyle{ie},'displayname',[sprintf('%s',stratum_name{istra}),namestr{ie}]);
            tot_atom{ie} = tot_atom{ie}+tmp_interp;
        end
    end
    linestyle = repmat({'-','--',':','-.'},1,length(eirene_mol));
    % Source component due to molecule-plasma collisions
    for ie = 1:length(eirene_mol)
        tmp = momfac*sum_radial(eirene_mol{ie}(:,:,istra),indbal,gmtry)/area_divide_pol;
        tmp_interp = interp1(x_pol, tmp, x_pol_interp, 'makima', 'extrap');
        if any(tmp)
            plot(x_pol_interp,tmp_interp,'parent',axstrat(6),'linewidth',1,'color',cmap(istra,:),'linestyle',linestyle{ie},'displayname',[sprintf('%s',stratum_name{istra}),namestr{ie}]);
            tot_mol{ie} = tot_mol{ie}+tmp_interp;
        end
    end
    linestyle = repmat({'-','--',':','-.'},1,length(eirene_tion));
    % Source component due to test ion-plasma collisions
    for ie = 1:length(eirene_tion)
        tmp = momfac*sum_radial(eirene_tion{ie}(:,:,istra),indbal,gmtry)/area_divide_pol;
        tmp_interp = interp1(x_pol, tmp, x_pol_interp, 'makima', 'extrap');
        if any(tmp)
            plot(x_pol_interp,tmp_interp,'parent',axstrat(7),'linewidth',1,'color',cmap(istra,:),'linestyle',linestyle{ie},'displayname',[sprintf('%s',stratum_name{istra}),namestr{ie}]);
            tot_tion{ie} = tot_tion{ie}+tmp_interp;
        end
    end
    linestyle = repmat({'-','--',':','-.'},1,length(eirene_rc));
    % Source component due to recombinations
    for ie = 1:length(eirene_rc)
        tmp = momfac*sum_radial(eirene_rc{ie}(:,:,istra),indbal,gmtry)/area_divide_pol;
        tmp_interp = interp1(x_pol, tmp, x_pol_interp, 'makima', 'extrap');
        if any(tmp)
            plot(x_pol_interp,tmp_interp,'parent',axstrat(8),'linewidth',1,'color',cmap(istra,:),'linestyle',linestyle{ie},'displayname',[sprintf('%s',stratum_name{istra}),namestr{ie}]);
            tot_rc{ie} = tot_rc{ie}+tmp_interp;
        end
    end
end

% Sum over strata plots
for ie = 1:length(eirene_atom)
    plot(x_pol_interp,tot_atom{ie},'linewidth',1,'color','k','linestyle',linestyle{ie},'parent',axstrat(5),'displayname',['Sum over strata ',namestr{ie}]);
    plot(x_pol_interp,tot_mol{ie},'linewidth',1,'color','k','linestyle',linestyle{ie},'parent',axstrat(6),'displayname',['Sum over strata ',namestr{ie}]);
    plot(x_pol_interp,tot_tion{ie},'linewidth',1,'color','k','linestyle',linestyle{ie},'parent',axstrat(7),'displayname',['Sum over strata ',namestr{ie}]);
    plot(x_pol_interp,tot_rc{ie},'linewidth',1,'color','k','linestyle',linestyle{ie},'parent',axstrat(8),'displayname',['Sum over strata ',namestr{ie}]);
end

% Plot properties
lgd = legend(axstrat(5),'show','location','best');
lgd = legend(axstrat(6),'show','location','best');
lgd = legend(axstrat(7),'show','location','best');
lgd = legend(axstrat(8),'show','location','best');
ylabel(axstrat(5),get(get(axbal(end),'ylabel'),'string'));
ylabel(axstrat(6),get(get(axbal(end),'ylabel'),'string'));
ylabel(axstrat(7),get(get(axbal(end),'ylabel'),'string'));
ylabel(axstrat(8),get(get(axbal(end),'ylabel'),'string'));
xlabel(axstrat(5),get(get(axbal(end),'xlabel'),'string'));
xlabel(axstrat(6),get(get(axbal(end),'xlabel'),'string'));
xlabel(axstrat(7),get(get(axbal(end),'xlabel'),'string'));
xlabel(axstrat(8),get(get(axbal(end),'xlabel'),'string'));
set(axstrat(5:8),'xlim',get(axbal(end),'xlim'));

% Set the same axes limits for all radial source plots:
ymin = 1E40;
ymax = -1E40;
for iax=5:8
    a = findobj(get(axstrat(iax),'children'),'type','line');
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
    set(axstrat(5:8),'ylim',[ymin ymax]);
end

end