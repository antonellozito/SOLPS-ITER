function neutrals_triangles = read_fort46_full(fid)
% tdata = read_ft46(file)
%
% Read fort.46 file.
%
% For now, only fort.46 version 20160513 recognized 
%

%% Read dimensions

% ntri, version
ntri = fscanf(fid,'%d',1);
ver  = fscanf(fid,'%d',1);

neutrals_triangles.ntri = ntri;

if ver ~= 20160513 && ver ~= 20160829 && ver ~= 20170930
    error('Error: read_ft46: unknown format of fort.46 file');
end

% go to new line (skip reading a possible git-hash)
fgetl(fid);

% natm, nmol, nion
dims = fscanf(fid,'%d',3);
natm = dims(1);
nmol = dims(2);
nion = dims(3);
neutrals_triangles.natm = natm;
neutrals_triangles.nmol = nmol;
neutrals_triangles.nion = nion;

line = fgetl(fid);
for i = 1:natm
    line = fgetl(fid);
    neutrals_triangles.species_atm{i} = strtrim(line);
end
for i = 1:nmol
    line = fgetl(fid);
    neutrals_triangles.species_mol{i} = strtrim(line);
end
for i = 1:nion
    line = fgetl(fid);
    neutrals_triangles.species_ion{i} = strtrim(line);
end

%% Read data

neutrals_triangles.pdena  = scan_ft_real_grid(fid,ver,'pdena',[ntri,natm]);
neutrals_triangles.pdenm  = scan_ft_real_grid(fid,ver,'pdenm',[ntri,nmol]);
neutrals_triangles.pdeni  = scan_ft_real_grid(fid,ver,'pdeni',[ntri,nion]);

neutrals_triangles.edena  = scan_ft_real_grid(fid,ver,'edena',[ntri,natm]);
neutrals_triangles.edenm  = scan_ft_real_grid(fid,ver,'edenm',[ntri,nmol]);
neutrals_triangles.edeni  = scan_ft_real_grid(fid,ver,'edeni',[ntri,nion]);

neutrals_triangles.vxdena = scan_ft_real_grid(fid,ver,'vxdena',[ntri,natm]);
neutrals_triangles.vxdenm = scan_ft_real_grid(fid,ver,'vxdenm',[ntri,nmol]);
neutrals_triangles.vxdeni = scan_ft_real_grid(fid,ver,'vxdeni',[ntri,nion]);

neutrals_triangles.vydena = scan_ft_real_grid(fid,ver,'vydena',[ntri,natm]);
neutrals_triangles.vydenm = scan_ft_real_grid(fid,ver,'vydenm',[ntri,nmol]);
neutrals_triangles.vydeni = scan_ft_real_grid(fid,ver,'vydeni',[ntri,nion]);

neutrals_triangles.vzdena = scan_ft_real_grid(fid,ver,'vzdena',[ntri,natm]);
neutrals_triangles.vzdenm = scan_ft_real_grid(fid,ver,'vzdenm',[ntri,nmol]);
neutrals_triangles.vzdeni = scan_ft_real_grid(fid,ver,'vzdeni',[ntri,nion]);

neutrals_triangles.volumes = scan_ft_real_grid(fid,ver,'volumes',[ntri]);

neutrals_triangles.pux = scan_ft_real_grid(fid,ver,'pux',[ntri]);
neutrals_triangles.puy = scan_ft_real_grid(fid,ver,'puy',[ntri]);

neutrals_triangles.pvx = scan_ft_real_grid(fid,ver,'pvx',[ntri]);
neutrals_triangles.pvy = scan_ft_real_grid(fid,ver,'pvy',[ntri]);

frewind(fid);

%% Close file

fclose(fid);