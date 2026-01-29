function rates = read_b2frates(simulation)
%
% read_b2frates reads the atomic reaction rates file created by B2.5
% Output is a struct "rates" with all the data fields in the b2frates file
%
%% PRELIMINARY OPERATIONS

% Load the file

index = find(contains({simulation.atomic_rates.name},'b2frates'));
if isempty(index)
   error('Error: b2frates not found');
end
file = simulation.atomic_rates(index).file;
fid = fopen(file);
if (fid == -1)
   error('Error: b2frates not found');
end

% Read the dimensions

dim = scan_b2_int(fid,'rtnt,rtnn,rtns',3);
rates.rtnt = dim(1);
rates.rtnn = dim(2);
rates.rtns = dim(3);

ratdims = [rates.rtnt+1,rates.rtnn+1,rates.rtns];

%% READ THE DATA

% Charges and boundaries

rates.zamin   = scan_b2_real(fid,'rtzmin',rates.rtns);       % Minimum atomic charge for each species
rates.zamax   = scan_b2_real(fid,'rtzmax',rates.rtns);       % Maximum atomic charge for each species
rates.zn      = scan_b2_real(fid,'rtzn   ',rates.rtns);      % Nuclear charge for each species
rates.rtt     = scan_b2_real(fid,'rtt   ',rates.rtnt+1);   % Sequence of temperature values for which the rate coefficients are evaluated, eV
rates.rtn     = scan_b2_real(fid,'rtn   ',rates.rtnn+1);   % Sequence of density values for which the rate coefficients are evaluated, m^-3
rates.rtlt    = scan_b2_real(fid,'rtlt   ',rates.rtnt+1);  % Sequence of the logatithms of the temperature values for which the rate coefficients are evaluated
rates.rtln    = scan_b2_real(fid,'rtln   ',rates.rtnn+1);  % Sequence of the logatithms of the density values for which the rate coefficients are evaluated

% State variables

rates.rtlsa     = scan_b2_real(fid,'rtlsa'    ,ratdims);   % Logarithm of the ionization rate coefficient (m^3/s) for the process is -> is+1
rates.rtlra     = scan_b2_real(fid,'rtlra'    ,ratdims);   % Logarithm of the recombination rate coefficient (m^3/s) for the process is -> is-1
rates.rtlqa     = scan_b2_real(fid,'rtlqa'    ,ratdims);   % Logarithm of the electron heat loss rate coefficient (eV*m^3/s) for each species
rates.rtlcx     = scan_b2_real(fid,'rtlcx'    ,ratdims);   % Logarithm of the charge-exchange rate coefficient (m^3/s) for each species
rates.rtlrd     = scan_b2_real(fid,'rtlrd'    ,ratdims);   % 
rates.rtlbr     = scan_b2_real(fid,'rtlbr'    ,ratdims);   % 
rates.rtlza     = scan_b2_real(fid,'rtlza'    ,ratdims);   % Effective charge state for the superstage k, e
rates.rtlz2     = scan_b2_real(fid,'rtlz2'    ,ratdims);   % Effective squared charge for the superstage k, e^2
rates.rtlpt     = scan_b2_real(fid,'rtlpt'    ,ratdims);   % Cumulative ionization energy to reach superstage k, eV
rates.rtlpi     = scan_b2_real(fid,'rtlpi'    ,ratdims);   % Effective ionization energy to reach superstage k from k-1, eV

% Species

atomic_data = read_atomic_data(sprintf('%s/incatm',simulation.B25_DATABASE));

for i = 1:rates.rtns

    atomic_number(i) = rates.zn(i);
    charge_state(i) = rates.zamax(i);

    if atomic_number(i) == 1
        name{i} = 'D';
    else
        index(i) = find(arrayfun(@(x) x.atomic_number == atomic_number(i), atomic_data));
        name{i} = atomic_data(index(i)).species;
    end

    rates.species{i} = sprintf('%s%d',name{i},charge_state(i));

end

frewind(fid);

fclose(fid);

fprintf('Structure RATES from b2frates read.\n');

end
