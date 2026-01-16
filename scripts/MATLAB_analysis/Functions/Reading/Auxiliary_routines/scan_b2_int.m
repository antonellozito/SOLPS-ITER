function field = scan_b2_int(fid,fieldname,dims)
%
% Auxiliary routine to read integer fields from B2.5 b2f* files
% 
%% PRELIMINARY OPERATIONS

% Search the file until identifier 'fieldname' is found

line = fgetl(fid);
while isempty(strfind(line,fieldname))
    line = fgetl(fid);
    if line == -1
        error(['EOF reached without finding ',fieldname,'.']);
    end
end

% Consistency check: number of elements specified in the file should equal to prod(dims)

numin = strread(line,'%*s %*s %d');
if numin ~= prod(dims)
    error('Error: read_ifield: inconsistent number of input elements.');
end

%% READ THE DATA

field = fscanf(fid,'%d',prod(dims));
if (length(dims) > 1)
    field = reshape(field,dims);
end

end