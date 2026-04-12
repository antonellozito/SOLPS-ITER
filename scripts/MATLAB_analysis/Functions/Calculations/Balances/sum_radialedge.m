function sum = sum_radialedge(field,indbal,gmtry)

%
% sum_radialedge finds radially-summed values of edge-centred quantity "field" (fluxes) along the poloidal length of the balance volume
%
%% CALCULATION

% Geometry variables
indbaledge = indbal;
rightix = gmtry.rightix+1;
rightiy = gmtry.rightiy+1;
topix = gmtry.topix+1;
topiy = gmtry.topiy+1;
    
% Add an extra true cell to the right-most edge of indbal to get indbaledge
for iy = 1:gmtry.ny
	ixlast = find(indbal(:,iy),1,'last');
	if ~isempty(ixlast)
        indbaledge(rightix(ixlast,iy),rightiy(ixlast,iy)) = true;
	end
end

% Go to the bottom left of indbal:
[ix,iy]=ind2sub(size(indbal),find(indbal,1));
   
% For poloidally consecutive points in indbal, sum radially
sum = [];
ixout = 1;
while true
    sum(ixout) = field(ix,iy);
	iyscan = iy;
	ixscan = ix;
	while indbaledge(topix(ixscan,iyscan),topiy(ixscan,iyscan)) && ...
        topiy(ixscan,iyscan)~=iyscan
        ixscan = topix(ixscan,iyscan);
        iyscan = topiy(ixscan,iyscan);
        sum(ixout) = sum(ixout)+field(ixscan,iyscan);
    end
	ixout = ixout+1;
	if indbal(ix,iy)
        ix = rightix(ix,iy);
        iy = rightiy(ix,iy);
    else
        break;
	end
end

end
