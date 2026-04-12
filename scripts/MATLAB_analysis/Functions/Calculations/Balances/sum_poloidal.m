function sum = sum_poloidal(field,indbal,gmtry)

%
% sum_poloidal finds poloidally-summed values of cell-centred quantity "field" (sources and residuals) along the radial length of the balance volume
%
%% CALCULATION

% Geometry variables
rightix = gmtry.rightix+1;
rightiy = gmtry.rightiy+1;
topix = gmtry.topix+1;
topiy = gmtry.topiy+1;
    
% Go to the bottom left of indbal:
[ix,iy]=ind2sub(size(indbal),find(indbal,1));
    
% For radially consecutive points in indrad, sum poloidally:
sum = [];
iyout = 1;   
while true
    sum(iyout) = field(ix,iy);
	iyscan = iy;
	ixscan = ix;
	while indbal(rightix(ixscan,iyscan),rightiy(ixscan,iyscan))
        ixscan = rightix(ixscan,iyscan);
        iyscan = rightiy(ixscan,iyscan);
        sum(iyout) = sum(iyout)+field(ixscan,iyscan);
    end
	iyout = iyout+1;
	if indbal(topix(ix,iy),topiy(ix,iy)) && ...
        topiy(ixscan,iyscan)~=iyscan
        ix = topix(ix,iy);
        iy = topiy(ix,iy);
    else
        break;
	end
end

end
