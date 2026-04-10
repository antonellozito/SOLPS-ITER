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

rates = set_raw_b2_values(rates, fid, {
    'zamin', 'rtzmin', rates.rtns;
    'zamax', 'rtzmax', rates.rtns;
    'zn', 'rtzn   ', rates.rtns;
    'rtt', 'rtt   ', rates.rtnt+1;
    'rtn', 'rtn   ', rates.rtnn+1;
    'rtlt', 'rtlt   ', rates.rtnt+1;
    'rtln', 'rtln   ', rates.rtnn+1;
});

% State variables

rates = set_raw_b2_values(rates, fid, {
    'rtlsa', 'rtlsa', ratdims;
    'rtlra', 'rtlra', ratdims;
    'rtlqa', 'rtlqa', ratdims;
    'rtlcx', 'rtlcx', ratdims;
    'rtlrd', 'rtlrd', ratdims;
    'rtlbr', 'rtlbr', ratdims;
    'rtlza', 'rtlza', ratdims;
    'rtlz2', 'rtlz2', ratdims;
    'rtlpt', 'rtlpt', ratdims;
    'rtlpi', 'rtlpi', ratdims;
});

% Species

atomic_data = read_atomic_data(sprintf('%s/incatm',simulation.B25_DATABASE));

rates.species = cell(1, rates.rtns);
for i = 1:rates.rtns

    atomic_number = rates.zn(i);
    charge_state = rates.zamax(i);

    if atomic_number == 1
        species_name = 'D';
    else
        data_index = find(arrayfun(@(x) x.atomic_number == atomic_number, atomic_data), 1);
        species_name = atomic_data(data_index).species;
    end

    rates.species{i} = sprintf('%s%d', species_name, charge_state);

end

fclose(fid);

fprintf('Atomic rates from b2frates read\n');

end
