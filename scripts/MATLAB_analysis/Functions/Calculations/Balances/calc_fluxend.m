function fluxend = calc_fluxend(transport_mode,field,indbal,direction,varargin)

transport_mode = lower(char(transport_mode));

if nargin >= 6
    nextix = varargin{1};
    nextiy = varargin{2};
else
    nextix = [];
    nextiy = [];
end
%
% balance_calc_fluxend finds values of edge-centred quantities at the ends of the balance volume
%
%% CALCULATION

fluxend = [];

switch transport_mode
    case 'parallel'
        for iy = 1:size(field,2)
            inds = find(indbal(:,iy));
            if ~isempty(inds)
                if strcmp(lower(direction),'left')
                    fluxend = [fluxend,field(inds(1),iy)]; % Left edge
                elseif strcmp(lower(direction),'right')
                    fluxend = [fluxend,field(nextix(inds(end),iy),nextiy(inds(end),iy))]; % Right edge
                else
                    error('Error: direction must be ''left'' or ''right''');
                end
            end
        end
    case 'radial'
        for ix = 1:size(field,1)
            inds = find(indbal(ix,:));
            if ~isempty(inds)
                if strcmp(lower(direction),'bottom')
                    fluxend = [fluxend,field(ix,inds(1))]; % Bottom edge
                elseif strcmp(lower(direction),'top')
                    fluxend = [fluxend,field(nextix(ix,inds(end)),nextiy(ix,inds(end)))]; % Top edge
                else
                    error('Error: direction must be ''bottom'' or ''top''');
                end
            end
        end
    otherwise
        error('Error: Transport mode ''%s'' not supported.',transport_mode);
end
    
end
