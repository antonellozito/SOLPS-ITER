clear;

fid = fopen('/Users/antonello/Desktop/refl.data/hew.rn');
projectile = 'He'; target = 'W';

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

e2 = 14.399651;

a_b = 0.529177;

a_L = ((9*pi^2)/(128))^(1/3)*a_b*(z1^(2/3)+z2^(2/3))^(-1/2);

epsilon_L = ((m1+m2)/(m2))*((z1*z2*e2)/(a_L));

for i = na:-1:1

    data_fit = data(:,i)';

    if all(data_fit)==0

        coeffs{i} = [nan nan nan nan];

        energy_values = linspace(energies(1),energies(end),10000);
        for j = 1:length(energy_values)
            data_values(j) = 0;
        end

    else

        epsilon = energies./epsilon_L;

        fun = @(a,epsilon)(exp(a(1)*(epsilon.^(a(2)))))./(1+exp(a(3)*(epsilon.^(a(4)))));
        %fun = @(a,epsilon)((a(1)*(epsilon.^(a(2)))))./(1+(a(3)*(epsilon.^(a(4)))));
%         if i == na
            a0 = [0 0 0 0];
           %a0 = [-0.186e-1 -0.127e1 0.654e1 0.137e0];
%         else
%             if isnan(coeffs{i+1})
%                 a0 = [0 0 0 0];
%             else
%                 a0 = coeffs{i+1};
%             end
%         end
        options = optimoptions('lsqcurvefit','Algorithm','levenberg-marquardt',....
            'MaxFunctionEvaluations',100000,'MaxIterations',100000,'FunctionTolerance',1e-40,'StepTolerance',1e-40);
        lb = [-inf,-inf,-inf,-inf];
        ub = [inf,inf,inf,inf];
        a = lsqcurvefit(fun,a0,epsilon,data_fit,lb,ub,options);
        coeffs{i} = a;

        energy_values = linspace(energies(1),energies(end),10000);
        for j = 1:length(energy_values)
            data_values(j) = (exp(coeffs{i}(1)*((energy_values(j)/epsilon_L).^(coeffs{i}(2)))))./(1+exp(coeffs{i}(3)*((energy_values(j)/epsilon_L).^(coeffs{i}(4)))));
        end

    end


    figure;
    hold on; box on;
    plot(energy_values,data_values,'linewidth',1.5,'displayname','Eckstein fit (Zito 2022)');
    scatter(energies,data_fit,50,'filled','DisplayName','TRIM data (Eckstein 1998)');
    xlim([energies(1) 1000]);
    lgd = legend('Interpreter','latex','fontsize',9);
    xlabel('$E_0$ [eV]','interpreter','latex','fontsize',10);
    ylabel('$R_{E}$','interpreter','latex','fontsize',10);
    set(gcf,'Position', [400 400 400 300]);
    [t,s] = title(sprintf('energy reflection coefficient, %s-->%s, angle = %d°',projectile,target,angles(i)),...
        sprintf('fit: a1 = %.3f, a2 = %.3f, a3 = %.3f, a4 = %.3f',coeffs{i}(1),coeffs{i}(2),coeffs{i}(3),coeffs{i}(4)),'fontsize',8);

    %print(sprintf('RN_%s_%s_%d°.pdf',projectile,target,angles(i)), '-vector', '-dpdf');

end

%save(sprintf('RN_%s_%s.mat',projectile,target),"projectile","target","z1","m1","z2","m2","Es","angles","energies","data","coeffs",'-mat')
