function write_fort44(file,neutrals_grid,wall)
% write_fort44(file,neutrals_grid,wall)
%
% Write fort.44 file for use by EIRENE.
%
% Notes: 
%  - routine does not do any consistency checking on the data (size of
%    the fields in neutrals_triangles, etc.)
%  - routine will overwrite existing data if 'file' exists
%  - only the fields belonging to the B2 grid are written for now
%    wall is still to do
% 

[fid,msg] = fopen(file,'wt');
if (fid == -1)
   error(msg);
end

%% WRITE DIMENSION OF THE GRID

fprintf(fid,' %3d   %3d  20201006  3.x.x-xxx-xxxxxxxxx             \n',neutrals_grid.nx,neutrals_grid.ny);

%% WRITE NUMBER OF STRATA, NUMBERS OF SPECIES AND SPECIES NAMES

fprintf(fid,' %d\n',neutrals_grid.nstra);

fprintf(fid,'%4d  %4d  %4d\n',neutrals_grid.natm,neutrals_grid.nmol,neutrals_grid.nion);

for i = 1:neutrals_grid.natm
    fprintf(fid,' %s\n',neutrals_grid.species_atm{i});
end

for i = 1:neutrals_grid.nmol
    fprintf(fid,' %s\n',neutrals_grid.species_mol{i});
end

for i = 1:neutrals_grid.nion
    fprintf(fid,' %s\n',neutrals_grid.species_ion{i});
end

%% WRITE FIELDS

write_ft_real_grid(fid,'dab2',neutrals_grid.dab2);
write_ft_real_grid(fid,'tab2',neutrals_grid.tab2);
write_ft_real_grid(fid,'dmb2',neutrals_grid.dmb2);
write_ft_real_grid(fid,'tmb2',neutrals_grid.tmb2);
write_ft_real_grid(fid,'dib2',neutrals_grid.dib2);
write_ft_real_grid(fid,'tib2',neutrals_grid.tib2);

write_ft_real_grid(fid,'rfluxa',neutrals_grid.rfluxa);
write_ft_real_grid(fid,'rfluxm',neutrals_grid.rfluxm);
write_ft_real_grid(fid,'pfluxa',neutrals_grid.pfluxa);
write_ft_real_grid(fid,'pfluxm',neutrals_grid.pfluxm);
write_ft_real_grid(fid,'refluxa',neutrals_grid.refluxa);
write_ft_real_grid(fid,'refluxm',neutrals_grid.refluxm);
write_ft_real_grid(fid,'pefluxa',neutrals_grid.pefluxa);
write_ft_real_grid(fid,'pefluxm',neutrals_grid.pefluxm);

write_ft_real_grid(fid,'emiss',neutrals_grid.emiss);
write_ft_real_grid(fid,'emissmol',neutrals_grid.emissmol);
write_ft_real_grid(fid,'srcml',neutrals_grid.srcml);
write_ft_real_grid(fid,'edissml',neutrals_grid.edissml);
write_ft_real_grid(fid,'eneutrad',neutrals_grid.eneutrad);
write_ft_real_grid(fid,'emolrad',neutrals_grid.emolrad);
write_ft_real_grid(fid,'eionrad',neutrals_grid.eionrad);

write_ft_real_grid(fid,'pdena_int',neutrals_grid.pdena_int);
write_ft_real_grid(fid,'pdenm_int',neutrals_grid.pdenm_int);
write_ft_real_grid(fid,'pdeni_int',neutrals_grid.pdeni_int);
write_ft_real_grid(fid,'pdena_int_b2',neutrals_grid.pdena_int_b2);
write_ft_real_grid(fid,'pdenm_int_b2',neutrals_grid.pdenm_int_b2);
write_ft_real_grid(fid,'pdeni_int_b2',neutrals_grid.pdeni_int_b2);

write_ft_real_grid(fid,'edena_int',neutrals_grid.edena_int);
write_ft_real_grid(fid,'edenm_int',neutrals_grid.edenm_int);
write_ft_real_grid(fid,'edeni_int',neutrals_grid.edeni_int);
write_ft_real_grid(fid,'edena_int_b2',neutrals_grid.edena_int_b2);
write_ft_real_grid(fid,'edenm_int_b2',neutrals_grid.edenm_int_b2);
write_ft_real_grid(fid,'edeni_int_b2',neutrals_grid.edeni_int_b2);

%% CLOSE FILE

fclose(fid);

end