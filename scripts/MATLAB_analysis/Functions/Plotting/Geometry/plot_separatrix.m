function h = plot_separatrix(gmtry,varargin)
%
% Routine to plot separatrix.
% 
% Input arguments:
%
% - gmtry   : struct read from b2fgmtry-file
% - options : list of plot options compatible with Matlab plot command
%
% Output arguments:
%
% - h       : handle to the separatrix line
%

% Init empty output
h = [];

if not(isunstructuredgrid(gmtry))

    switch gmtry.nncut
        
        case 0
            
            % No sep in this case...
            disp('plotsep: no separatrix in case gmtry.nncut = 0.');
        
        case 1
            
            % Collect separatrix coordinates
            sep.r = [gmtry.crx(:,gmtry.topcut(1)+2,1);gmtry.crx(end,gmtry.topcut(1)+2,2)];
            sep.z = [gmtry.cry(:,gmtry.topcut(1)+2,1);gmtry.cry(end,gmtry.topcut(1)+2,2)];
            
            % Plot
            h = plot(sep.r,sep.z,varargin{:});
            
        otherwise
            
            disp(['plotsep: not implemented for gmtry.nncut = ',gmtry.nncut,'.']);
            
    end

else

    % identify separatrix flux tube
    [sep1] = find_flux_surfaces_us(gmtry,gmtry.cvlista(gmtry.icsepomp));
    [sep2] = find_flux_surfaces_us(gmtry,gmtry.cvlista(gmtry.icsepomp-1));
    sep = intersect(sep1,sep2);
    for jj=1:gmtry.fsFcP(sep,2)     
            ifc = gmtry.fsFc(gmtry.fsFcP(sep,1)+jj-1);
            vx1 = gmtry.fcVx(ifc,1); vx2 = gmtry.fcVx(ifc,2);
            plot([gmtry.vxX(vx1) gmtry.vxX(vx2)],[gmtry.vxY(vx1) gmtry.vxY(vx2)],varargin{:}) 
    end

end

