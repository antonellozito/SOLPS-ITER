function write_fort46(file,neutrals_triangles)
% write_fort46(file,neutrals_triangles)
%
% Write fort.46 file for use by EIRENE.
%
% Notes: 
%  - routine does not do any consistency checking on the data (size of
%    the fields in neutrals_triangles, etc.)
%  - routine will overwrite existing data if 'file' exists
% 

[fid,msg] = fopen(file,'wt');
if (fid == -1)
   error(msg);
end

%% WRITE NUMBER OF TRIANGLES

fprintf(fid,'%6d  20170930  3.x.x-xxx-xxxxxxxxx             \n',neutrals_triangles.ntri);

%% WRITE NUMBERS OF SPECIES AND SPECIES NAMES

fprintf(fid,'%4d  %4d  %4d\n',neutrals_triangles.natm,neutrals_triangles.nmol,neutrals_triangles.nion);

for i = 1:neutrals_triangles.natm
    fprintf(fid,' %s\n',neutrals_triangles.species_atm{i});
end

for i = 1:neutrals_triangles.nmol
    fprintf(fid,' %s\n',neutrals_triangles.species_mol{i});
end

for i = 1:neutrals_triangles.nion
    fprintf(fid,' %s\n',neutrals_triangles.species_ion{i});
end

%% WRITE FIELDS

write_ft_real_grid(fid,'pdena',neutrals_triangles.pdena);
write_ft_real_grid(fid,'pdenm',neutrals_triangles.pdenm);
write_ft_real_grid(fid,'pdeni',neutrals_triangles.pdeni);

write_ft_real_grid(fid,'edena',neutrals_triangles.edena);
write_ft_real_grid(fid,'edenm',neutrals_triangles.edenm);
write_ft_real_grid(fid,'edeni',neutrals_triangles.edeni);

write_ft_real_grid(fid,'vxdena',neutrals_triangles.vxdena);
write_ft_real_grid(fid,'vxdenm',neutrals_triangles.vxdenm);
write_ft_real_grid(fid,'vxdeni',neutrals_triangles.vxdeni);

write_ft_real_grid(fid,'vydena',neutrals_triangles.vydena);
write_ft_real_grid(fid,'vydenm',neutrals_triangles.vydenm);
write_ft_real_grid(fid,'vydeni',neutrals_triangles.vydeni);

write_ft_real_grid(fid,'vzdena',neutrals_triangles.vzdena);
write_ft_real_grid(fid,'vzdenm',neutrals_triangles.vzdenm);
write_ft_real_grid(fid,'vzdeni',neutrals_triangles.vzdeni);

write_ft_real_grid(fid,'volumes',neutrals_triangles.volumes);

write_ft_real_grid(fid,'pux',neutrals_triangles.pux);
write_ft_real_grid(fid,'puy',neutrals_triangles.puy);

write_ft_real_grid(fid,'pvx',neutrals_triangles.pvx);
write_ft_real_grid(fid,'pvy',neutrals_triangles.pvy);

%% CLOSE FILE

fclose(fid);

end