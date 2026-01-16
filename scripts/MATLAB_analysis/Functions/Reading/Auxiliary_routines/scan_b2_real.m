function field = scan_b2_real(fid,fieldname,dims)
%
% Auxiliary routine to read real fields from B2.5 b2f* files
% 
%% PRELIMINARY OPERATIONS

% Search the file until identifier 'fieldname' is found

temp = '                                ';
for i = 1:length(fieldname)
    temp(i) = fieldname(i);
end
fieldname = temp;

line = fgetl(fid);
while ~contains(line,fieldname)
    line = fgetl(fid);
    if line == -1
        error(['EOF reached without finding ',fieldname,'.']);
    end
end

% Consistency check: number of elements specified in the file should equal to prod(dims)

numin = strread(line,'%*s %*s %d');
if numin ~= prod(dims)
    error('Error: read_rfield: inconsistent number of input elements.');
end

%% READ THE DATA

field = fscanf(fid,'%e',prod(dims));
if (length(dims) > 1)
    field = reshape(field,dims);
end

end