function data = read_exp_data_json(simulation)

%% PRELIMINARY OPERATIONS

% Load the file

index = find(contains({simulation.run.name},'exp_data.json'));
if isempty(index)
    error('Error: exp_data.json not found');
end
file = simulation.run(index).file;

%% READ THE ENTRIES

% Read JSON file
raw_data = jsondecode(fileread(file));

% Check mandatory DEVICE field
if ~isfield(raw_data, 'DEVICE')
    error('JSON file must contain DEVICE field');
end

% Initialize output structure
data.DEVICE = raw_data.DEVICE;

% Define all possible categories and their subcategories
category_structure = struct();
category_structure.MIDPLANE.DATA = {'ELECTRON_DENSITY_MIDPLANE', 'ELECTRON_TEMPERATURE_MIDPLANE', ...
                                    'ION_TEMPERATURE_MIDPLANE', 'ION_SPECIES_DENSITY_MIDPLANE'};
category_structure.MIDPLANE.PROFILES = {'ELECTRON_DENSITY_MIDPLANE', 'ELECTRON_TEMPERATURE_MIDPLANE', ...
                                        'ION_TEMPERATURE_MIDPLANE', 'ION_SPECIES_DENSITY_MIDPLANE'};
category_structure.CHORDS.DATA = {'ELECTRON_DENSITY_CHORDS', 'ELECTRON_TEMPERATURE_CHORDS', ...
                                 'ION_TEMPERATURE_CHORDS', 'ION_SPECIES_DENSITY_CHORDS', ...
                                 'PHOTON_EMISSION_CHORDS', 'RADIATED_POWER_CHORDS'};
category_structure.INNER_TARGET.DATA = {'ELECTRON_DENSITY_INNER_TARGET', 'ELECTRON_TEMPERATURE_INNER_TARGET', ...
                                       'PARTICLE_FLUX_DENSITY_INNER_TARGET', 'ENERGY_FLUX_DENSITY_INNER_TARGET'};
category_structure.INNER_TARGET.PROFILES = {'ELECTRON_DENSITY_INNER_TARGET', 'ELECTRON_TEMPERATURE_INNER_TARGET', ...
                                           'PARTICLE_FLUX_DENSITY_INNER_TARGET', 'ENERGY_FLUX_DENSITY_INNER_TARGET'};
category_structure.OUTER_TARGET.DATA = {'ELECTRON_DENSITY_OUTER_TARGET', 'ELECTRON_TEMPERATURE_OUTER_TARGET', ...
                                       'PARTICLE_FLUX_DENSITY_OUTER_TARGET', 'ENERGY_FLUX_DENSITY_OUTER_TARGET'};
category_structure.OUTER_TARGET.PROFILES = {'ELECTRON_DENSITY_OUTER_TARGET', 'ELECTRON_TEMPERATURE_OUTER_TARGET', ...
                                           'PARTICLE_FLUX_DENSITY_OUTER_TARGET', 'ENERGY_FLUX_DENSITY_OUTER_TARGET'};

% Define all possible attributes
all_attributes = {'SHOT', 'SOURCE', 'EXPERIMENT', 'VERSION', 'SIGNAL', ...
                 'SIGNAL_UNCERTAINTY', 'SPECIES', 'EMISSION_LINE', ...
                 'SHIFT_R', 'SHIFT_DSSEP', 'SHIFT_RHOP', ...
                 'CHORDS', 'TIME_START', 'TIME_END', 'REDUCED_SET_TIME_DELTA', ...
                 'NAME_DISPLAY'};

% Process each category
categories = fieldnames(category_structure);
for c = 1:length(categories)
    cat_name = categories{c};
    subcategories = fieldnames(category_structure.(cat_name));
    
    for s = 1:length(subcategories)
        subcat_name = subcategories{s};
        subsubcats = category_structure.(cat_name).(subcat_name);
        
        for ss = 1:length(subsubcats)
            subsub_name = subsubcats{ss};
            
            % Initialize with empty values
            data.(cat_name).(subcat_name).(subsub_name) = initialize_subsubcategory(all_attributes);
            
            % Check if this subsubcategory exists in JSON
            if isfield(raw_data, cat_name) && ...
               isfield(raw_data.(cat_name), subcat_name) && ...
               isfield(raw_data.(cat_name).(subcat_name), subsub_name)
                
                json_subsub = raw_data.(cat_name).(subcat_name).(subsub_name);
                
                % Validate mandatory fields
                validate_mandatory_fields(json_subsub, subsub_name, cat_name);
                
                % Get the number of elements from mandatory fields
                n_elements = get_num_elements(json_subsub.SHOT);
                
                % Process each attribute
                for a = 1:length(all_attributes)
                    attr_name = all_attributes{a};
                    
                    if isfield(json_subsub, attr_name)
                        attr_value = json_subsub.(attr_name);
                        attr_n_elements = get_num_elements(attr_value);
                        
                        % Truncate if more elements than expected
                        if attr_n_elements > n_elements
                            attr_value = truncate_to_n_elements(attr_value, n_elements);
                        end
                        
                        % Convert to cell array if single entry and not already a cell
                        attr_value = ensure_cell_format(attr_value);
                        
                        data.(cat_name).(subcat_name).(subsub_name).(attr_name) = attr_value;
                    end
                end
            end
        end
    end
end

end

%% AUXILIARY FUNCTIONS

function subsub = initialize_subsubcategory(attributes)
    % Initialize all attributes with empty values
    subsub = struct();
    for i = 1:length(attributes)
        attr = attributes{i};
        % Numeric attributes get []
        if ismember(attr, {'EMISSION_LINE', 'SHIFT_R', 'SHIFT_DSSEP', 'SHIFT_RHOP', 'CHORDS', ...
                          'TIME_START', 'TIME_END', 'REDUCED_SET_TIME_DELTA'})
            subsub.(attr) = [];
        else
            % String/mixed attributes get ''
            subsub.(attr) = '';
        end
    end
end

function validate_mandatory_fields(subsub_data, subsub_name, cat_name)
    % Check basic mandatory fields
    mandatory = {'SHOT', 'SOURCE', 'EXPERIMENT', 'SIGNAL', 'TIME_START', 'TIME_END'};
    
    for i = 1:length(mandatory)
        if ~isfield(subsub_data, mandatory{i})
            error('Subsubcategory %s is missing mandatory field: %s', subsub_name, mandatory{i});
        end
    end
    
    % Check SPECIES for ion species density and photon emission
    if contains(subsub_name, 'ION_SPECIES_DENSITY') || contains(subsub_name, 'PHOTON_EMISSION')
        if ~isfield(subsub_data, 'SPECIES')
            error('Subsubcategory %s requires SPECIES field', subsub_name);
        end
    end
    
    % Check EMISSION_LINE for photon emission
    if contains(subsub_name, 'PHOTON_EMISSION')
        if ~isfield(subsub_data, 'EMISSION_LINE')
            error('Subsubcategory %s requires EMISSION_LINE field', subsub_name);
        end
    end
    
    % Check CHORDS for CHORDS category
    % Note: CHORDS can be an array where each element corresponds to a SIGNAL
    if strcmp(cat_name, 'CHORDS')
        if ~isfield(subsub_data, 'CHORDS')
            error('Subsubcategory %s in CHORDS category requires CHORDS field', subsub_name);
        end
    end
end

function n = get_num_elements(value)
    % Get number of elements in a value (array or scalar)
    if ischar(value) || isstring(value)
        if isstring(value)
            n = length(value);
        else
            n = 1;
        end
    elseif iscell(value)
        n = length(value);  % Works for both regular and nested cell arrays
    else
        n = length(value);
    end
end

function truncated = truncate_to_n_elements(value, n)
    % Truncate value to n elements
    if ischar(value)
        truncated = value;
    elseif isstring(value)
        truncated = value(1:min(n, length(value)));
    elseif iscell(value)
        truncated = value(1:min(n, length(value)));  % Works for both regular and nested cell arrays
    else
        truncated = value(1:min(n, length(value)));
    end
end

function result = ensure_cell_format(value)
    % Ensure all attributes are in cell array format, even for single entries
    % Both string and numeric attributes are converted to cells
    if iscell(value)
        % Already a cell array
        result = value;
    elseif ischar(value)
        % Single character array - convert to {1} cell
        result = {value};
    elseif isstring(value)
        % String - convert to cell
        result = cellstr(value);
    elseif isnumeric(value) || islogical(value)
        % Numeric or logical - convert to cell array
        if isscalar(value)
            % Single value - convert to {1} cell
            result = {value};
        else
            % Multiple values - convert to cell array where each element is a scalar
            result = num2cell(value);
        end
    else
        % Unknown type - wrap in cell
        result = {value};
    end
end
