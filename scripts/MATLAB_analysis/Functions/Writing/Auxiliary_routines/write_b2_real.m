function write_b2_real(fid,fieldname,field)
% write_rfield(fid,fieldname,field)
%
% Auxiliary routine to write real fields for B2.5 b2f* files
% 

% Print a label
fprintf(fid,'%s','*cf:    real');
fprintf(fid,'%16d',numel(field));
fprintf(fid,'%s\n',['    ',fieldname]);

% Only write field if number of elements is larger than 0
if numel(field) > 0
    % Print the data to string, increase digits for exponent to 3
    sfield = sprintf('%21.13E%21.13E%21.13E%21.13E%21.13E%21.13E\n',field);
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