function [x_rad,x_radedge] = calc_radialcoordinate(gmtry,indbal,default_region,radbaldist)
%
% calc_radialcoordinate calculates the radial coordinate of the radial balance plots
%
%% CALCULATION

indbaledge = indbal;
rightix = gmtry.rightix+1;
rightiy = gmtry.rightiy+1;
topix = gmtry.topix+1;
topiy = gmtry.topiy+1;
for ix = 1:gmtry.nx
    iylast = find(indbal(ix,:),1,'last');
    if ~isempty(iylast)
        indbaledge(topix(ix,iylast),topiy(ix,iylast)) = true;
    end
end

switch default_region(2)
   
    case 'i'
        
        switch radbaldist
            
            case 'midplane' % y - y_sep at inner mid-plane (cm):
                yimp = [0,cumsum(sqrt(diff(gmtry.cr(gmtry.imp,:)).^2+diff(gmtry.cz(gmtry.imp,:)).^2))];
                yimp = yimp-yimp(gmtry.sep+2);
        
                x_radedge = [];
                for iy=1:gmtry.ny
                    ixfirst = find(indbaledge(:,iy),1,'first');
                    if indbaledge(ixfirst,iy)
                    x_radedge = [x_radedge,yimp(iy)];
                    end
                end
                x_radedge = 100*x_radedge; % coordinates of the bottom edges of the cells             
                
                dys1 = sqrt(diff(gmtry.cr_y(gmtry.imp,gmtry.sep+1:gmtry.sep+2))^2+diff(gmtry.cz_y(gmtry.imp,gmtry.sep+1:gmtry.sep+2))^2);                
                yimp = yimp+dys1/2;
                
                x_rad = [];
                for iy=1:gmtry.ny
                    ixfirst = find(indbal(:,iy),1,'first');
                    if indbal(ixfirst,iy)
                    x_rad = [x_rad,yimp(iy)];
                    end
                end
                x_rad = 100*x_rad; % coordinates of the centers of the cells
                
            case 'x-point' % y - y_sep at inner x-point surface (cm):
                xcut = find(diff(gmtry.leftix(:,1))<1);
                yix = [0,cumsum(sqrt(diff(gmtry.cr(xcut(1)-1,:)).^2+diff(gmtry.cz(xcut(1)-1,:)).^2))];
                yix = yix-yix(gmtry.sep+2);
               
                x_radedge = [];
                for iy=1:gmtry.ny
                    ixfirst = find(indbaledge(:,iy),1,'first');
                    if indbaledge(ixfirst,iy)
                    x_radedge = [x_radedge,yix(iy)]; 
                    end
                end
                x_radedge = 100*x_radedge; % coordinates of the bottom edges of the cells                
                
                dys1 = sqrt(diff(gmtry.cr_y(xcut(1)-1,gmtry.sep+1:gmtry.sep+2))^2+diff(gmtry.cz_y(xcut(1)-1,gmtry.sep+1:gmtry.sep+2))^2);                
                yix = yix+dys1/2;
                
                x_rad = [];
                for iy=1:gmtry.ny
                    ixfirst = find(indbal(:,iy),1,'first');
                    if indbal(ixfirst,iy)
                    x_rad = [x_rad,yix(iy)];
                    end
                end
                x_rad = 100*x_rad; % coordinates of the centers of the cells
                
            case 'target' % y - y_sep at inner target (cm):
                yit = [0,cumsum(sqrt(diff(gmtry.cr(1,:)).^2+diff(gmtry.cz(1,:)).^2))];
                yit = yit-yit(gmtry.sep+2);
        
                x_radedge = [];
                for iy=1:gmtry.ny
                    ixfirst = find(indbaledge(:,iy),1,'first');
                    if indbaledge(ixfirst,iy)
                    x_radedge = [x_radedge,yit(iy)];
                    end
                end
                x_radedge = 100*x_radedge; % coordinates of the bottom edges of the cells
                
                dys1 = sqrt(diff(gmtry.cr_y(1,gmtry.sep+1:gmtry.sep+2))^2+diff(gmtry.cz_y(1,gmtry.sep+1:gmtry.sep+2))^2);                
                yit = yit+dys1/2;
                
                x_rad = [];
                for iy=1:gmtry.ny
                    ixfirst = find(indbal(:,iy),1,'first');
                    if indbal(ixfirst,iy)
                    x_rad = [x_rad,yit(iy)];
                    end
                end
                x_rad = 100*x_rad; % coordinates of the centers of the cells 

            case 'rho'
                x_rad = calc_rho;

         end
                
    case 'o'
        
        switch radbaldist
            
            case 'midplane' % y - y_sep at outer mid-plane (cm):
                yomp = [0,cumsum(sqrt(diff(gmtry.cr(gmtry.omp,:)).^2+diff(gmtry.cz(gmtry.omp,:)).^2))];
                yomp = yomp-yomp(gmtry.sep+2);
                
                x_radedge = [];
                for iy=1:gmtry.ny
                    ixfirst = find(indbaledge(:,iy),1,'first');
                    if indbaledge(ixfirst,iy)
                    x_radedge = [x_radedge,yomp(iy)];
                    end
                end
                x_radedge = 100*x_radedge; % coordinates of the bottom edges of the cells
                
                dys1 = sqrt(diff(gmtry.cr_y(gmtry.omp,gmtry.sep+1:gmtry.sep+2))^2+diff(gmtry.cz_y(gmtry.omp,gmtry.sep+1:gmtry.sep+2))^2);
                yomp = yomp+dys1/2;

                x_rad = [];
                for iy=1:gmtry.ny
                    ixfirst = find(indbal(:,iy),1,'first');
                    if indbal(ixfirst,iy)
                    x_rad = [x_rad,yomp(iy)];
                    end
                end
                x_rad = 100*x_rad; % coordinates of the centers of the cells

            case 'x-point' % y - y_sep at outer x-point surface (cm):
                xcut = find(diff(gmtry.leftix(:,1))<1);
                yox = [0,cumsum(sqrt(diff(gmtry.cr(xcut(2)+1,:)).^2+diff(gmtry.cz(xcut(2)+1,:)).^2))];
                yox = yox-yox(gmtry.sep+2);

                x_radedge = [];
                for iy=1:gmtry.ny
                    ixfirst = find(indbaledge(:,iy),1,'first');
                    if indbaledge(ixfirst,iy)
                    x_radedge = [x_radedge,yox(iy)];
                    end
                end
                x_radedge = 100*x_radedge; % coordinates of the bottom edges of the cells
                
                dys1 = sqrt(diff(gmtry.cr_y(xcut(2)+1,gmtry.sep+1:gmtry.sep+2))^2+diff(gmtry.cz_y(xcut(2)+1,gmtry.sep+1:gmtry.sep+2))^2);
                yox = yox+dys1/2;
                
                x_rad = [];
                for iy=1:gmtry.ny
                    ixfirst = find(indbal(:,iy),1,'first');
                    if indbal(ixfirst,iy)
                    x_rad = [x_rad,yox(iy)];
                    end
                end
                x_rad = 100*x_rad; % coordinates of the centers of the cells
                
            case 'target' % y - y_sep at outer target (cm):
                yot = [0,cumsum(sqrt(diff(gmtry.cr(end,:)).^2+diff(gmtry.cz(end,:)).^2))];
                yot = yot-yot(gmtry.sep+2);

                x_radedge = [];
                for iy=1:gmtry.ny
                    ixfirst = find(indbaledge(:,iy),1,'first');
                    if indbaledge(ixfirst,iy)
                    x_radedge = [x_radedge,yot(iy)];
                    end
                end
                x_radedge = 100*x_radedge; % coordinates of the bottom edges of the cells                
                
                dys1 = sqrt(diff(gmtry.cr_y(end,gmtry.sep+1:gmtry.sep+2))^2+diff(gmtry.cz_y(end,gmtry.sep+1:gmtry.sep+2))^2);
                yot = yot+dys1/2;
                
                x_rad = [];
                for iy=1:gmtry.ny
                    ixfirst = find(indbal(:,iy),1,'first');
                    if indbal(ixfirst,iy)
                    x_rad = [x_rad,yot(iy)];
                    end
                end
                x_rad = 100*x_rad; % coordinates of the centers of the cells     

            case 'rho'
                x_rad = calc_rho;
                
        end
end
 
end