function [indbal,reverse] = set_region(region_name,gmtry)
%
% set_region sets the indbal logical grid for the region in which the balances are performed
%
%% DEFINE THE QUANTITIES

indbal = false(gmtry.nx,gmtry.ny);
top = gmtry.nx/2;
xcut = find(diff(gmtry.leftix(:,1))<1);

%% REGIONS DEFINITION

if length(xcut)==2
    display('Assuming single null case');
    switch region_name(1:2)
        case {'li','ui'}
            switch region_name(3)
                case 'x'
                    indbal(2:xcut(1)-1,gmtry.sep+2:end-1) = true;
                    reverse = true;
                    display('Region: Inner side (X-point to target)');
                case 'm'
                    indbal(2:gmtry.imp+1,gmtry.sep+2:end-1) = true;
                    reverse = true;
                    display('Region: Inner side (midplane to target)');
                case 's'
                    indbal(2:top-1,gmtry.sep+2) = true;
                    reverse = true;
                    display('Region: Inner side (separatrix)')
            end
        case {'uo','lo'}
            switch region_name(3)
                case 'x'
                    indbal(xcut(2)+1:end-1,gmtry.sep+2:end-1) = true;
                    reverse = false;
                    display('Region: Outer side (X-point to target)');                   
                case 'm'
                    indbal(gmtry.omp+1:end-1,gmtry.sep+2:end-1) = true;
                    reverse = false;
                    display('Region: Outer side (midplane to target)');
                case 's'
                    indbal(top:end-1,gmtry.sep+2) = true;
                    reverse = false;
                    display('Region: Outer side (separatrix)')   
            end
        otherwise
            error('Error: Region name ''%s'' not supported.',region_name);
    end
elseif length(xcut)==5
    display('Assuming connected double-null case');
    switch region_name(1:2)
        case 'li'
            indbal(2:xcut(1)-1,gmtry.sep+2:end-1) = true;
            reverse = true;
            display('Region: Lower inner side (X-point to target)');
        case 'ui'
            indbal(xcut(2):xcut(3)-1,gmtry.sep+2:end-1) = true;
            reverse = false;
            display('Region: Upper inner side (X-point to target)');
        case 'uo'
            indbal(xcut(3)+2:xcut(4),gmtry.sep+2:end-1) = true;
            reverse = true;
            display('Region: Upper outer side (X-point to target)');
        case 'lo'
            indbal(xcut(5)+1:end-1,gmtry.sep+2:end-1) = true;
            reverse = false;
            display('Region: Lower outer side (X-point to target)');
        otherwise
            error('Error: Region name ''%s'' not supported.',region_name);
    end
elseif isempty(xcut)
    display('Assuming continuous slab-like case');
    switch region_name(1:2)
        case {'li','ui','uo','lo'}
            indbal(2:end-1,2:end-1) = true;
            reverse = false;
        otherwise
            error('Error: Region name ''%s'' not supported.',region_name);
    end
    
end
