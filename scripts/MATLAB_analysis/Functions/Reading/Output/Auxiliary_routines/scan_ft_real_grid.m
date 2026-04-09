function field = scan_ft_real_grid(fid,ver,fieldname,dims)
%
% Auxiliary routine to read real fields on the computational grid from EIRENE fort.* files
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
    
    % Consistency check: number of elements specified in the file should equal to prod(dims)
    
    numin = strread(line,'%*s %*s %*s %*s %*s %*s %d');
    if numin ~= prod(dims)
        error('Error: read_ft44_rfield: inconsistent number of input elements.');
    end
end

%% READ THE DATA

field = fscanf(fid,'%e',prod(dims));
if (length(dims) > 1)
    field = reshape(field,dims);
end

%frewind(fid);

end
