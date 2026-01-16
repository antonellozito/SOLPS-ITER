function field = write_b2_int(fid,fieldname,field)
% write_ifield(fid,fieldname,field)
%
% Auxiliary routine to write integer fields for B2.5 b2f* files
% 

% Print a label
fprintf(fid,'%s','*cf:    int ');
fprintf(fid,'%16d',numel(field));
fprintf(fid,'%s\n',['    ',fieldname]);

% Only write field if number of elements is larger than 0
if numel(field) > 0
    % Print the data to string
    sfield = sprintf('%11d%11d%11d%11d%11d%11d%11d%11d%11d%11d%11d%11d\n',field);
    
    % Print to file, making sure there is only a single newline character 
    % to avoid a blank line in the output
    if strcmp(sfield(end),sprintf('\n'))
        sfield = sfield(1:end-1);
    end
    fprintf(fid,'%s\n',sfield);
end

end