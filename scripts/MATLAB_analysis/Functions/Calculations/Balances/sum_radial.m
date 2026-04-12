function sum = sum_radial(transport_mode,field,indbal,gmtry)
%
% balance_sum_radial finds radially-summed values of cell-centred quantities along the poloidal length of the balance volume
%
%% CALCULATION

transport_mode = lower(char(transport_mode));

% Geometry variables
rightix = gmtry.rightix+1;
rightiy = gmtry.rightiy+1;
topix = gmtry.topix+1;
topiy = gmtry.topiy+1;

% Go to the bottom left of indbal
[ix,iy]=ind2sub(size(indbal),find(indbal,1));

% For poloidally consecutive points in indbal, sum radially
sum = [];
ixout = 1;
while true
    sum(ixout) = field(ix,iy);
    iyscan = iy;
    ixscan = ix;
    switch transport_mode
        case 'parallel'
            while indbal(topix(ixscan,iyscan),topiy(ixscan,iyscan)) && ...
                    topiy(ixscan,iyscan)~=iyscan
                ixscan = topix(ixscan,iyscan);
                iyscan = topiy(ixscan,iyscan);
                sum(ixout) = sum(ixout)+field(ixscan,iyscan);
            end
            ixout = ixout+1;
            if indbal(rightix(ix,iy),rightiy(ix,iy))
                ix = rightix(ix,iy);
                iy = rightiy(ix,iy);
            else
                break;
            end
        case 'radial'
            while indbal(topix(ixscan,iyscan),topiy(ixscan,iyscan))
                ixscan = topix(ixscan,iyscan);
                iyscan = topiy(ixscan,iyscan);
                sum(ixout) = sum(ixout)+field(ixscan,iyscan);
            end
            ixout = ixout+1;
            if indbal(rightix(ix,iy),rightiy(ix,iy)) && ...
                    topiy(ixscan,iyscan)~=iyscan
                ix = rightix(ix,iy);
                iy = rightiy(ix,iy);
            else
                break;
            end
        otherwise
            error('Error: Transport mode ''%s'' not supported.',transport_mode);
    end
end

end
