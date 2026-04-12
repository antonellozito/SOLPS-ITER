function sum = sum_poloidaledge(field,indbal,gmtry)

%
% sum_poloidaledge finds poloidally-summed values of edge-centred quantity "field" (fluxes) along the radial length of the balance volume
%
%% CALCULATION

% Geometry variables
indbaledge = indbal;
rightix = gmtry.rightix+1;
rightiy = gmtry.rightiy+1;
topix = gmtry.topix+1;
topiy = gmtry.topiy+1;
    
% Add an extra true cell to the top edge of indbal to get indbaledge
for ix = 1:gmtry.nx
    iylast = find(indbal(ix,:),1,'last');
    if ~isempty(iylast)
        indbaledge(topix(ix,iylast),topiy(ix,iylast)) = true;
    end
end
     
% Go to the bottom left of indbal:
[ix,iy]=ind2sub(size(indbal),find(indbal,1));

% For radially consecutive points in indbal, sum poloidally
sum = [];
iyout = 1;
while true
	sum(iyout) = field(ix,iy);
	ixscan = ix;
	iyscan = iy;
	while indbaledge(rightix(ixscan,iyscan),rightiy(ixscan,iyscan)) && ...
        rightix(ixscan,iyscan)~=ixscan
        iyscan = rightiy(ixscan,iyscan);
        ixscan = rightix(ixscan,iyscan);
        sum(iyout) = sum(iyout)+field(ixscan,iyscan);
    end
	iyout = iyout+1;
	if indbal(ix,iy)
        ix = topix(ix,iy);
        iy = topiy(ix,iy);
    else
        break;
	end
end

end
