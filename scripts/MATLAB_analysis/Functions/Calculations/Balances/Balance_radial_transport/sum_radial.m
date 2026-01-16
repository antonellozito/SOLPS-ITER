function sum = sum_radial(field,indbal,gmtry)
%
% sum_radial finds radially-summed values of cell-centred quantity "field" (sources and residuals) along the poloidal length of the balance volume
%
%% CALCULATION

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
end

end