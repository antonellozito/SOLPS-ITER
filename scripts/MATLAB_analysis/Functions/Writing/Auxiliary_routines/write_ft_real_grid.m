function write_ft_real_grid(fid,fieldname,field)
%
% Auxiliary routine to write real fields on the computational grid from EIRENE fort.* files
% 

% Print a label

fprintf(fid,'%s','*eirene data field ');
fprintf(fid,'%s',fieldname);
fprintf(fid,'%s',' with size ');
fprintf(fid,'%6d\n',numel(field));

% Only write field if number of elements is larger than 0
if numel(field) > 0
    % Print the data to string, increase digits for exponent to 2
    sfield = sprintf('%14.7E%14.7E%14.7E%14.7E%14.7E%14.7E\n',field);
    sfield = strrep(sfield,'E+','E+0');
    sfield = strrep(sfield,'E-','E-0');
    
    % Print to file, making sure there is only a single newline character 
    % to avoid a blank line in the output
    if strcmp(sfield(end),sprintf('\n'))
        sfield = sfield(1:end-1);
    end
    fprintf(fid,'%s\n',sfield);
end

end
