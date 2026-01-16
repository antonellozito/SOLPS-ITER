function fluxend = calc_fluxend(field,indbal,direction,topix,topiy)
%
% calc_fluxend finds values of edge-centred quantity "field" (fluxes and areas) at the bottom or top ends of the balance volume
%
%% CALCULATION

fluxend = [];
    for ix=1:size(field,1)
        inds = find(indbal(ix,:));
        if ~isempty(inds)
            if strcmp(lower(direction),'bottom')
                fluxend = [fluxend,field(ix,inds(1))]; % select values at the bottom of the balance volume (separatrix)
            elseif strcmp(lower(direction),'top')
                fluxend = [fluxend,field(topix(ix,inds(end)),topiy(ix,inds(end)))]; % select values at the top of the balance volume (main wall boundary)
            else
                error('Error: direction must be ''bottom'' or ''top''');
            end
        end
    end
    
end