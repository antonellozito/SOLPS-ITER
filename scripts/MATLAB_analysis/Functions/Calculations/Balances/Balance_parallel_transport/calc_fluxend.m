function fluxend = calc_fluxend(field,indbal,direction,rightix,rightiy)
%
% calc_fluxend finds values of edge-centred quantity "field" (fluxes and areas) at the left-most or right-most ends of the balance volume
%
%% CALCULATION

fluxend = [];
    for iy=1:size(field,2)
        inds = find(indbal(:,iy));
        if ~isempty(inds)
            if strcmp(lower(direction),'left')
                fluxend = [fluxend,field(inds(1),iy)]; % select values at the left of the balance volume
            elseif strcmp(lower(direction),'right')
                fluxend = [fluxend,field(rightix(inds(end),iy),rightiy(inds(end),iy))]; % select values at the right of the balance volume
            else
                error('Error: direction must be ''left'' or ''right''');
            end
        end
    end
    
end