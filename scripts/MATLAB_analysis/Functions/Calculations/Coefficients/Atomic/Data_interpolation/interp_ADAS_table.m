function interp_vals = interp_ADAS_table(ADAS_table, xprof, yprof, log_val, x_multiply)

    if nargin < 4
        log_val = false;
    end
    if nargin < 5
        x_multiply = true;
    end

    x = ADAS_table.logNe;
    y = ADAS_table.logT;
    table = ADAS_table.logdata;

    if x_multiply
        table = table + x;
    end

    if all(abs(table - table(:, 1)) < 0.05, 'all') || isempty(xprof)
        % 1D interpolation if independent of the last dimension
        interp_vals = interp1(y, table * log(10), yprof, 'linear');
    else
        % 2D interpolation
        [nt, nr] = size(xprof);
        interp_vals = zeros(nt, nr);

        for t = 1:nt
            % Perform 2D interpolation for each time slice
            interp_vals(t, :) = interp2(x, y, table' * log(10), xprof(t, :), yprof(t, :), 'linear');
        end
    end

    if ~log_val
        interp_vals = exp(interp_vals);
    end
end