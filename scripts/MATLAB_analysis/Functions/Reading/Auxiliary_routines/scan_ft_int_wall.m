function field = scan_ft_int_wall(fid,ver,fieldname,dims)
%
% Auxiliary routine to read integer fields on the wall from EIRENE fort.* files
% 
%% PRELIMINARY OPERATIONS

if ver >= 20160829
    
    % Search the file until identifier 'fieldname' is found
    
    line = fgetl(fid);
    while isempty(strfind(line,fieldname))
        line = fgetl(fid);
        if line == -1
            error(['EOF reached without finding ',fieldname,'.']);
        end
    end
end

%% READ THE DATA

field = fscanf(fid,'%d');
% if (length(dims) > 1)
%     field = reshape(field,dims);

end
