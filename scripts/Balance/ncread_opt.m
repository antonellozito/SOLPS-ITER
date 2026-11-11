%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% ncread_opt reads a field of balance.nc that older versions of B2.5 do not    %
% write. If the file does not contain it, a warning is given and zeros of     %
% size sz are returned: the balance is then incomplete in the cases that the  %
% field covers.                                                                %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
function v = ncread_opt(balfile,name,sz)

info = ncinfo(balfile);
if any(strcmp({info.Variables.Name},name))
    v = ncread(balfile,name);
else
    warning(['%s not found in %s (written by an older B2.5): taken as ',...
        'zero.'],name,balfile);
    v = zeros(sz);
end

end
