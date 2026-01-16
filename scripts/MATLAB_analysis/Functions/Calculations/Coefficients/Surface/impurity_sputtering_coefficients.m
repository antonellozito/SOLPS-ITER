clear;

fid = fopen('/Users/antonello/Desktop/trim_data/implanted_sputter_data/N_He_W.y');
fid_fit = fopen('/Users/antonello/Desktop/trim_data/implanted_sputter_data/N_He_W_fit.y');
projectile = 'N';
implanted_impurity = 'He';
bulk_target = 'W';
m1 = 14.01;
z1 = 7;
m2 = 4.00;
z2 = 2;

angles = [0 20 40 55 65 70 75 80];
energies = [10 20 50 70 100 150 200 250 500 800];
C_imps = [0 0.002 0.004 0.006 0.008 0.010 0.012 0.014 0.015];

line = fgetl(fid);
line = fgetl(fid);
% temp = textscan(line,'Projectile: %s, m1 = %f, z1 = %d')
% projectile = temp{1}; m1 = temp{2}; z1 = temp{3};
line = fgetl(fid);
% temp = textscan(line,'Implanted impurity: %s, m2 = %f, z2 = %d, Es = %f')
% implanted_impurity = temp{1}; m2 = temp{2}; z2 = temp{3};
line = fgetl(fid);
% temp = textscan(line,'Bulk target: %s, m2 = %f, z2 = %d, Es = %f')
% implanted_impurity = temp{1};
line = fgetl(fid);
line = fgetl(fid);
line = fgetl(fid);
line = fgetl(fid);
line = fgetl(fid);
while line ~=-1
    temp = textscan(line,'%s %f %f %f %f %f %f %f');
    angle = temp{2}; energy = temp{3}; C_imp = temp{4}; Y_imp = temp{6};
    [d,angle_index] = min(abs(angle-angles));
    [d,energy_index] = min(abs(energy-energies));
    [d,C_imp_index] = min(abs(C_imp-C_imps));
    data(angle_index,energy_index,C_imp_index) = Y_imp;
    line = fgetl(fid);
end

line = fgetl(fid_fit);
line = fgetl(fid_fit);
line = fgetl(fid_fit);
line = fgetl(fid_fit);
line = fgetl(fid_fit);
line = fgetl(fid_fit);
line = fgetl(fid_fit);
line = fgetl(fid_fit);
for i = 1:length(angles)
    line = fgetl(fid_fit);   
    temp = textscan(line,'%f %f %f');
    Q0(i) = temp{2}; Eth(i) = temp{3};
end

Etf = 30.74 * ((m1 + m2)/m2) * z1 * z2 * sqrt((z1^(2/3)) + (z2^(2/3)));
energy_values = linspace(energies(1),energies(end),10000);

for i = 1:length(angles)
    for j = 1:length(energy_values)
        RedE(j) = energy_values(j) / Etf;
        Sn(j) = (0.5 * log(1 + 1.2288 * RedE(j))) / (RedE(j) + 0.1728 * sqrt(RedE(j)) + 0.008 * (RedE(j)^0.1504));
        EthOverE0(j) = Eth(i) / energy_values(j);
        Y_divided_C_imp(i,j) = Q0(i) * Sn(j) * (1.0 - (EthOverE0(j))^(2/3)) * ((1.0-EthOverE0(j))^2);
    end

    figure;
    hold on; box on;
    plot(energy_values,max(Y_divided_C_imp(i,:),0),'linewidth',1.5,'displayname','Bohdansky fit (Schmid 2022)');
    for k = [3,5,7,9]
        scatter(energies,data(i,:,k)./C_imps(k),50,'filled','DisplayName',sprintf('TRIM data, f imp = %.3f (Schmid 2022)',C_imps(k)));
    end
    xlim([energies(1) 800]);
    lgd = legend('fontsize',8,'Location','southeast');
    xlabel('$E_0$ [eV]','interpreter','latex','fontsize',10);
    ylabel('$Y_{imp}/f_{imp}$','interpreter','latex','fontsize',10);
    set(gcf,'Position', [400 400 400 300]);
    [t,s] = title(sprintf('implanted impurity sputtering yield, %s-->(%s in %s),\nangle = %d°, implantation depth = xx nm',...
        projectile,implanted_impurity,bulk_target,angles(i)),...
        sprintf('fit: Q0 = %.3f, Eth = %.3f',Q0(i),Eth(i)),'fontsize',8);

    print(sprintf('%s_%s_%s_y_%d°.pdf',projectile,implanted_impurity,bulk_target,angles(i)), '-vector', '-dpdf');

end
