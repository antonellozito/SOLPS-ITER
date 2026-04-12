function [x_pol,x_poledge] = calc_poloidalcoordinate(transport_mode,gmtry,indbal,default_region,polbaldist)
%
% balance_calc_poloidalcoordinate calculates the poloidal coordinate of the poloidal balance plots
%
%% CALCULATION

transport_mode = lower(char(transport_mode));

% Geometry variables
topix = gmtry.topix+1;
topiy = gmtry.topiy+1;
bottomix = gmtry.bottomix+1;
bottomiy = gmtry.bottomiy+1;
leftix = gmtry.leftix+1;
leftiy = gmtry.leftiy+1;
rightix = gmtry.rightix+1;
rightiy = gmtry.rightiy+1;

% Go to the bottom left of indbal
[ix,iy]=ind2sub(size(indbal),find(indbal,1));
ixsep = ix;
iysep = iy;

% Step to the first SOL ring
if ~isempty(find(diff(gmtry.leftix(:,1))<1,1))
    if iysep<gmtry.sep+2 % Step up
        while iysep~=gmtry.sep+2
            ixsep = topix(ixsep,iysep);
            iysep = topiy(ixsep,iysep);
        end
    elseif iysep>gmtry.sep+2 % Step down
        while iysep~=gmtry.sep+2
            ixsep = bottomix(ixsep,iysep);
            iysep = bottomiy(ixsep,iysep);
        end
    end
end

% Select parallel or poloidal distance
switch polbaldist
    case 'parallel'
        dist = gmtry.dspar;
        distedge = gmtry.dsparedge;
    case 'poloidal'
        dist = gmtry.dspol;
        distedge = gmtry.dspoledge;
    otherwise
        error('Error: Poloidal balance distance ''%s'' not supported.',polbaldist);
end

% Calculate the distance from the inner target along the first SOL ring

x_pol = dist(ixsep,iysep);
x_poledge = distedge(ixsep,iysep);
while indbal(rightix(ix,iy),rightiy(ix,iy))
    ixsep = rightix(ixsep,iysep);
    iysep = rightiy(ixsep,iysep);
    ix = rightix(ix,iy);
    iy = rightiy(ix,iy);
    x_pol = [x_pol,dist(ixsep,iysep)];
    x_poledge = [x_poledge,distedge(ixsep,iysep)];
end
x_poledge = [x_poledge,distedge(rightix(ixsep,iysep),iysep)];

% Revert to distance from outer target in case of region in the outer side

switch transport_mode
    case 'parallel'
        reverse_index = 2;
    case 'radial'
        reverse_index = 1;
    otherwise
        error('Error: Transport mode ''%s'' not supported.',transport_mode);
end

if ismember(default_region(reverse_index),'o')
    x_pol = dist(gmtry.nx,gmtry.sep+2)-x_pol;
    x_poledge = distedge(gmtry.nx,gmtry.sep+2)-x_poledge;
end

end
