clear;

folder=dir('/Users/antonello/Desktop/Reflection');

for i=3:length(folder)
   filenames{i}=folder(i).name;
   if strcmp(filenames{i}(1:2),'RE') && strcmp(filenames{i}(end-2:end),'mat')
       temp = append('/Users/antonello/Desktop/Reflection/',filenames{i});
       load(temp);
       temp = filenames{i}(4:end-4);
       temp = sprintf('%s_fit.re',temp);
       fid = fopen(temp,'w');
       fprintf(fid,'Energy reflection coefficient\n');
       fprintf(fid,'Projectile: %s, m1 = %.2f, z1 = %d\n',projectile,m1,z1);
       fprintf(fid,'Target: %s, m2 = %.2f, z2 = %d, Es = %.2f\n',target,m2,z2,Es);
       fprintf(fid,'Energy range: %d eV - %d eV\n',energies(1),energies(end));
       fprintf(fid,'\n');
       fprintf(fid,'Angle   b1            b2            b3            b4           \n');
       for j = 1:length(angles)
            if isnan(coeffs{j}(1))
                fprintf(fid,'%-7d NaN           NaN           NaN           NaN        \n',angles(j));
            else
                fprintf(fid,'%-7d %-+.5e  %-+.5e  %-+.5e  %-+.5e\n',angles(j),coeffs{j}(1),coeffs{j}(2),coeffs{j}(3),coeffs{j}(4));
            end
       end
       fclose(fid);
   end
end