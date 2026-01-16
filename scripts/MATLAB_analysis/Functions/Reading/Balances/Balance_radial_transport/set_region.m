function indbal = set_region(region_name,gmtry)
%
% set_region sets the indbal logical grid for the region in which the balances are performed 
%
%% DEFINE THE QUANTITIES

indbal = false(gmtry.nx,gmtry.ny);
top = gmtry.nx/2;
xcut = find(diff(gmtry.leftix(:,1))<1);

%% REGIONS DEFINITION

if length(xcut)==2
    display('Assuming single-null case');
    switch region_name(1)
        case 'i'
            switch region_name(2)
                case 's'
                    indbal(xcut(1):top-1,gmtry.sep+2:end-1) = true;
                    display('Region: Inner side (SOL)');
                case 'd'
                    indbal(2:top-1,gmtry.sep+2:end-1) = true;
                    display('Region: Inner side (SOL+divertor)');                   
                case 'm'
                    indbal(gmtry.imp,gmtry.sep+2:end-1) = true;
                    display('Region: Inner midplane');
            end
        case 'o'
            switch region_name(2)
                case 's'
                    indbal(top:xcut(2),gmtry.sep+2:end-1) = true;
                    display('Region: Outer side (SOL)');
                case 'd'
                    indbal(top:end-1,gmtry.sep+2:end-1) = true;
                    display('Region: Outer side (SOL+divertor)');                    
                case 'm'
                    indbal(gmtry.omp+1,gmtry.sep+2:end-1) = true;
                    display('Region: Outer midplane');
            end
        otherwise
            error('Error: Region name ''%s'' not supported',region_name);
    end
elseif length(xcut)==5
    error('Error: Connected double-null still not tested');
elseif isempty(xcut)
    error('Error: Continuous slab-like still not tested');
end

end