function value = trim_last_rows(value, rows_number)
if nargin < 2
    rows_number = 1;
end

if rows_number <= 0
    return
end

value(end-rows_number+1:end, :) = [];
end
