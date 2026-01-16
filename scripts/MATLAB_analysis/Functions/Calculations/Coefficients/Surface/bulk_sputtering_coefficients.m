clear;

fid = fopen('/Users/antonello/Work/Python/aurora/aurora/trim_data/bulk_sputter/Ar_W.y');
projectile = 'Ar';
target = 'W';

line = fgetl(fid);
line = fgetl(fid);
temp = textscan(line,'c z1= %f , m1=  %f , z2= %f , m2= %f , Es=%f , rho=%f g/cm**3');
z1 = temp{1}; m1 = temp{2}; z2 = temp{3}; m2 = temp{4}; Es = temp{5};
line = fgetl(fid);
temp = textscan(line,'c ne=%d, na=%d');
ne = temp{1}; na = temp{2};
line = fgetl(fid);
line = fgetl(fid);
temp = '';
for i = 1:na
    temp = append(temp,'%f');
end
temp = textscan(line,temp);
for i = 1:na
    angles(i) = temp{i};
end
line = fgetl(fid);

j = 1;
while j < ne+1
    line = fgetl(fid);
    temp = '%f';
    for i = 1:na
        temp = append(temp,'%.5f');
    end
    temp = textscan(line,temp);
    energies(j) = temp{1};
    for i = 1:na
        data(j,i) = temp{i+1};
    end
    j = j+1;
end

Etf = 30.74 * ((m1 + m2)/m2) * z1 * z2 * sqrt((z1^(2/3)) + (z2^(2/3)));
 
for i = 1:na

    data_fit = data(:,i)';

    if all(data_fit)==0

        coeffs{i} = [nan nan];

        energy_values = linspace(energies(1),energies(end),10000);
        for j = 1:length(energy_values)
            data_values(j) = 0;
        end

    else

        epsilon = energies./Etf;
        Sn = (0.5*log(1+1.2288*epsilon))./(epsilon+0.1728*sqrt(epsilon)+0.008*epsilon.^0.1504);

        fun = @(a,energies)a(1)*Sn.*(1-(a(2)./energies).^(2/3)).*((1-(a(2)./energies)).^2);
        
        if i == 1
            a0 = [1 10];
        else
            if isnan(coeffs{i-1})
                a0 = [1 10];
            else
                a0 = coeffs{i-1};
            end
        end
        options = optimoptions('lsqcurvefit','Algorithm','levenberg-marquardt',....
            'MaxFunctionEvaluations',100000,'MaxIterations',100000,'FunctionTolerance',1e-40,'StepTolerance',1e-40);
        lb = [0,0];
        ub = [inf,inf];
        a = lsqcurvefit(fun,a0,energies,data_fit,lb,ub,options);
        coeffs{i} = a;

        energy_values = linspace(energies(1),10000,10000);
        epsilon_values = energy_values./Etf;
        Sn_values = (0.5*log(1+1.2288*epsilon_values))./(epsilon_values+0.1728*sqrt(epsilon_values)+0.008*epsilon_values.^0.1504);
        for j = 1:length(energy_values)
            data_values(j) = coeffs{i}(1).*Sn_values(j).*(1-(coeffs{i}(2)./energy_values(j)).^(2/3)).*(1-(coeffs{i}(2)./energy_values(j))).^2;
        end

    end


    figure;
    hold on; box on;
    plot(energy_values,data_values,'linewidth',1.5,'displayname','Bohdansky fit (Zito 2022)');
    scatter(energies,data_fit,50,'filled','DisplayName','TRIM data (Eckstein 1998)');
    xlim([energies(1) 10000]);
    ylim([1e-4 10]);
    lgd = legend('interpreter','latex','fontsize',9,'Location','southeast');
    xlabel('$E_0$ [eV]','interpreter','latex','fontsize',10);
    ylabel('$Y$','interpreter','latex','fontsize',10);
    set(gcf,'Position', [400 400 400 300]);
    set(gca, 'YScale', 'log');
    set(gca, 'XScale', 'log');
    [t,s] = title(sprintf('sputtering yield, %s-->%s, angle = %d°',projectile,target,angles(i)),...
        sprintf('fit: Q = %.3f, Eth = %.3f',coeffs{i}(1),coeffs{i}(2)),'fontsize',8);

    print(sprintf('Y_%s_%s_%d°.pdf',projectile,target,angles(i)), '-vector', '-dpdf');

end

save(sprintf('Y_%s_%s.mat',projectile,target),"projectile","target","z1","m1","z2","m2","Es","angles","energies","data","coeffs",'-mat')
