function plot_grid(gmtry,structure,indbal,axgrid,reverse)
%
% plot_grid plots the whole grid for a particular simulation, as well as the volume where the balance is performed
%
%% GRID

% Create the axis
axis(axgrid,'image');
xlabel(axgrid,'R [m]', 'fontsize', 12);
ylabel(axgrid,'Z [m]', 'fontsize', 12);

% Cell coordinates
rbl = gmtry.r(:,:,1);
rbr = gmtry.r(:,:,2);
rtl = gmtry.r(:,:,3);
rtr = gmtry.r(:,:,4);
zbl = gmtry.z(:,:,1);
zbr = gmtry.z(:,:,2);
ztl = gmtry.z(:,:,3);
ztr = gmtry.z(:,:,4);

% Plot the grid
patch([reshape(rbl,1,[]);...
       reshape(rbr,1,[]);...
       reshape(rtr,1,[]);...
       reshape(rtl,1,[])],...
      [reshape(zbl,1,[]);...
       reshape(zbr,1,[]);...
       reshape(ztr,1,[]);...
       reshape(ztl,1,[])],'w','parent',axgrid,'handlevisibility','off');

% Plot the structure
h = zeros(length(structure),1);
for i = 1:length(structure)
    h(i) = plot(structure(i).r,structure(i).z,'k','linewidth',0.4,'parent',axgrid,'handlevisibility','off'); hold on;
    if min(structure(i).z) < -1.3
        %fillout(structure(i).r,structure(i).z,[0.75 3 -1.504 1.504],[1 1 1]); hold on;
    else
        fill(structure(i).r,structure(i).z,[0.88 0.88 0.88],'parent',axgrid,'handlevisibility','off'); hold on;
    end
end

%% BALANCE VOLUME     
   
% Plot the balance volume
patch([reshape(rbl(indbal),1,[]);...
       reshape(rbr(indbal),1,[]);...
       reshape(rtr(indbal),1,[]);...
       reshape(rtl(indbal),1,[])],...
      [reshape(zbl(indbal),1,[]);...
       reshape(zbr(indbal),1,[]);...
       reshape(ztr(indbal),1,[]);...
       reshape(ztl(indbal),1,[])],...
      'y','parent',axgrid);
   
% Plot the left- and right-most surfaces of the volume of interest
rleft = [];
zleft = [];
rright = [];
zright = [];
for iy = 1:gmtry.ny
    first = find(indbal(:,iy),1,'first');
    last = find(indbal(:,iy),1,'last');
    if ~isempty(first)
        rleft = [rleft,rbl(first,iy),rtl(first,iy)];
        zleft = [zleft,zbl(first,iy),ztl(first,iy)];
        rright = [rright,rbr(last,iy),rtr(last,iy)];
        zright = [zright,zbr(last,iy),ztr(last,iy)];
    end
end
cmap = gmtry.cmap;
if ~reverse
    plot(rleft,zleft,'linewidth',2.2,'color',cmap(1,:),'parent',axgrid);
    plot(rright,zright,'linewidth',2.2,'color',cmap(2,:),'parent',axgrid);
else
    plot(rright,zright,'linewidth',2.2,'color',cmap(2,:),'parent',axgrid);
    plot(rleft,zleft,'linewidth',2.2,'color',cmap(1,:),'parent',axgrid);
end

% Legend
lgd = legend(axgrid,'Balance volume','Upstream surface','Downstream surface','fontsize',9);

end