function output = compute_quantity(operation,structure)

fields = fieldnames(structure);
for i = 1:length(fields)
    temp = sprintf('%s=structure.%s;',fields{i},fields{i});
    eval(temp);   
end

output = eval(operation);

end
