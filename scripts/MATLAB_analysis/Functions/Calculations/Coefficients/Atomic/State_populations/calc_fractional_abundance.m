function fz = calc_fractional_abundance(varargin)

SIMULATION = varargin{1};
atom = varargin{2};
ne = varargin{3};
Te = varargin{4};
if length(varargin) > 4
    Ti = varargin{5};
    n0_by_ne = varargin{6};
end

temp = read_adas_adf11(SIMULATION,lower(atom),'scd');
Z = temp.Z;

for i = 1:Z

    [~,ion_coeff(:,i)] = read_atomic_reactions_coefficients(SIMULATION,ne,Te,lower(atom),i-1,'scd');
    ion_rate(:,i) = ion_coeff(:,i).*ne;
    [~,rec_coeff(:,i)] = read_atomic_reactions_coefficients(SIMULATION,ne,Te,lower(atom),i-1,'acd');
    rec_rate(:,i) = rec_coeff(:,i).*ne;
    if length(varargin) > 4
        [~,cx_coeff(:,i)] = read_atomic_reactions_coefficients(SIMULATION,ne,Ti,lower(atom),i-1,'ccd');
        cx_rate(:,i) = cx_coeff(:,i).*ne;
        rec_rate(:,i) = rec_rate(:,i) + n0_by_ne.*cx_rate(:,i);
    end

end

rate_ratio = [ones(size(Te)), ion_rate./rec_rate];
fz = cumprod(rate_ratio,2);
fz = fz ./ sum(fz, 2);

end

