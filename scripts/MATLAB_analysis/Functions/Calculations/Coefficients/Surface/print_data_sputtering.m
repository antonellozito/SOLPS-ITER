clear;

folder=dir('/Users/antonello/Work/MATLAB/TRIM/New Folder');

for i=3:length(folder)
   filenames{i}=folder(i).name;
   if strcmp(filenames{i}(1),'Y') && strcmp(filenames{i}(end-2:end),'mat')
       temp = append('/Users/antonello/Work/MATLAB/TRIM/New Folder/',filenames{i});
       load(temp);
       temp = filenames{i}(3:end-4);
       temp = sprintf('%s_fit.y',temp);
       fid = fopen(temp,'w');
       fprintf(fid,'Sputtering yield\n');
       fprintf(fid,'Projectile: %s, m1 = %.2f, z1 = %d\n',projectile,m1,z1);
       fprintf(fid,'Target: %s, m2 = %.2f, z2 = %d, Es = %.2f\n',target,m2,z2,Es);
       fprintf(fid,'Energy range: %d eV - %d eV\n',energies(1),energies(end));
       fprintf(fid,'\n');
       fprintf(fid,'Angle   Q             Eth           \n');
       for j = 1:length(angles)
            if isnan(coeffs{j}(1))
                fprintf(fid,'%-7d NaN           NaN        \n',angles(j));
            else
                fprintf(fid,'%-7d %-+.5e  %-+.5e\n',angles(j),coeffs{j}(1),coeffs{j}(2));
            end
       end
       fclose(fid);
   end
end