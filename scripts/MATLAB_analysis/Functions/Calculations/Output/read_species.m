function [species_label,atomic_number,charge_state] = read_species(simulation)

RATES = read_b2frates(simulation);
atomic_data = read_atomic_data(sprintf('%s/incatm',simulation.B25_DATABASE));

for i = 1:RATES.rtns

    atomic_number(i) = RATES.zn(i);
    charge_state(i) = RATES.zamax(i);

    if atomic_number(i) == 1
        name{i} = 'D';
    else
        index(i) = find(arrayfun(@(x) x.atomic_number == atomic_number(i), atomic_data));
        name{i} = atomic_data(index(i)).species;
    end

    species_label{i} = sprintf('%s%d',name{i},charge_state(i));

end

end
