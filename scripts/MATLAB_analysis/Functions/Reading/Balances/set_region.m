function [indbal,reverse] = set_region(transport_mode,region_name,gmtry)

%
% balance_set_region sets the logical grid for the region in which the balances are performed
%
%% DEFINE THE QUANTITIES

transport_mode = lower(char(transport_mode));

indbal = false(gmtry.nx,gmtry.ny);
reverse = false;
top = gmtry.nx/2;
xcut = find(diff(gmtry.leftix(:,1))<1);

%% REGIONS DEFINITION

switch transport_mode
    case 'parallel'
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
                            display('Region: Inner side (separatrix)');
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
                            display('Region: Outer side (separatrix)');
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
    case 'radial'
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
    otherwise
        error('Error: Transport mode ''%s'' not supported.',transport_mode);
end

end
