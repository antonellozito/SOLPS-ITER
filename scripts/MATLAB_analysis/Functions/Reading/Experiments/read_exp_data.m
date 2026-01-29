function exp_data = read_exp_data(simulation)
%
% read_exp_data reads the information needed to extract experimental data
% related to a given simulation, from a given device
% This is how the exp_data file should be:
%
% 'DEVICE'                                                         'AUG'
% 
% 'ELECTRON_DENSITY_PROFILE_MIDPLANE_SHOT'                         '39409'
% 'ELECTRON_DENSITY_PROFILE_MIDPLANE_EXPERIMENT'                   'augd'
% 'ELECTRON_DENSITY_PROFILE_MIDPLANE_SOURCE'                       'IDA'
% 'ELECTRON_DENSITY_PROFILE_MIDPLANE_SIGNAL'                       'ne'
% 'ELECTRON_DENSITY_PROFILE_MIDPLANE_SIGNAL_UNCERTAINTY'           'ne_unc'
% 'ELECTRON_DENSITY_PROFILE_MIDPLANE_SIGNAL_NAME_DISPLAY'          'IDA fit'
% 'ELECTRON_DENSITY_PROFILE_MIDPLANE_TIME_START'                   '2.5'
% 'ELECTRON_DENSITY_PROFILE_MIDPLANE_TIME_END'                     '4.5'
% 'ELECTRON_DENSITY_PROFILE_MIDPLANE_SEPARATRIX_SHIFT'             '+0.000'
% 'ELECTRON_TEMPERATURE_PROFILE_MIDPLANE_SHOT'                     '39409'
% 'ELECTRON_TEMPERATURE_PROFILE_MIDPLANE_EXPERIMENT'               'augd'
% 'ELECTRON_TEMPERATURE_PROFILE_MIDPLANE_SOURCE'                   'IDA'
% 'ELECTRON_TEMPERATURE_PROFILE_MIDPLANE_SIGNAL'                   'Te'
% 'ELECTRON_TEMPERATURE_PROFILE_MIDPLANE_SIGNAL_UNCERTAINTY'       'Te_unc'
% 'ELECTRON_TEMPERATURE_PROFILE_MIDPLANE_SIGNAL_NAME_DISPLAY'      'IDA fit'
% 'ELECTRON_TEMPERATURE_PROFILE_MIDPLANE_TIME_START'               '2.5'
% 'ELECTRON_TEMPERATURE_PROFILE_MIDPLANE_TIME_END'                 '4.5'
% 'ELECTRON_TEMPERATURE_PROFILE_MIDPLANE_SEPARATRIX_SHIFT'         '+0.000'
% 
% 'ELECTRON_DENSITY_DATA_MIDPLANE_SHOT'                            '39409'
% 'ELECTRON_DENSITY_DATA_MIDPLANE_EXPERIMENTS'                     {'augd','augd','augd'}
% 'ELECTRON_DENSITY_DATA_MIDPLANE_SOURCES'                         {'IDA','IDA','LIN'}
% 'ELECTRON_DENSITY_DATA_MIDPLANE_SIGNALS'                         {'tsdatcne','tsdatene','ne'}
% 'ELECTRON_DENSITY_DATA_MIDPLANE_NAMES_DISPLAY'                   {'Core TS','Edge TS','LiBES'}
% 'ELECTRON_DENSITY_DATA_MIDPLANE_TIME_START'                      '2.9'
% 'ELECTRON_DENSITY_DATA_MIDPLANE_TIME_END'                        '3.3'
% 'ELECTRON_DENSITY_DATA_MIDPLANE_REDUCED_SET'                     'true'
% 'ELECTRON_DENSITY_DATA_MIDPLANE_REDUCED_SET_TIME_DELTA'          '0.01'
% 'ELECTRON_DENSITY_DATA_MIDPLANE_SEPARATRIX_SHIFT'                '+0.000'
% 'ELECTRON_TEMPERATURE_DATA_MIDPLANE_SHOT'                        '39409'
% 'ELECTRON_TEMPERATURE_DATA_MIDPLANE_EXPERIMENTS'                 {'augd','augd'}
% 'ELECTRON_TEMPERATURE_DATA_MIDPLANE_SOURCES'                     {'IDA','IDA'}
% 'ELECTRON_TEMPERATURE_DATA_MIDPLANE_SIGNALS'                     {'tsdatcte','tsdatete'}
% 'ELECTRON_TEMPERATURE_DATA_MIDPLANE_NAMES_DISPLAY'               {'Core TS','Edge TS'}
% 'ELECTRON_TEMPERATURE_DATA_MIDPLANE_TIME_START'                  '2.9'
% 'ELECTRON_TEMPERATURE_DATA_MIDPLANE_TIME_END'                    '3.3'
% 'ELECTRON_TEMPERATURE_DATA_MIDPLANE_REDUCED_SET'                 'true'
% 'ELECTRON_TEMPERATURE_DATA_MIDPLANE_REDUCED_SET_TIME_DELTA'      '0.01'
% 'ELECTRON_TEMPERATURE_DATA_MIDPLANE_SEPARATRIX_SHIFT'            '+0.000'
% 'ION_TEMPERATURE_DATA_MIDPLANE_SHOT'                             '39409'
% 'ION_TEMPERATURE_DATA_MIDPLANE_EXPERIMENTS'                      {'augd','augd'}
% 'ION_TEMPERATURE_DATA_MIDPLANE_SOURCES'                          {'CEZ','CMZ'}
% 'ION_TEMPERATURE_DATA_MIDPLANE_SIGNALS'                          {'Ti_c','Ti_c'}
% 'ION_TEMPERATURE_DATA_MIDPLANE_NAMES_DISPLAY'                    {'Core CXRS','Edge CXRS'}
% 'ION_TEMPERATURE_DATA_MIDPLANE_TIME_START'                       '2.9'
% 'ION_TEMPERATURE_DATA_MIDPLANE_TIME_END'                         '3.3'
% 'ION_TEMPERATURE_DATA_MIDPLANE_REDUCED_SET'                      'true'
% 'ION_TEMPERATURE_DATA_MIDPLANE_REDUCED_SET_TIME_DELTA'           '0.1'
% 'ION_TEMPERATURE_DATA_MIDPLANE_SEPARATRIX_SHIFT'                 '+0.000'
% 
% 'ELECTRON_DENSITY_DATA_CHORDS_SHOT'                              '39409'
% 'ELECTRON_DENSITY_DATA_CHORDS_EXPERIMENTS'                       {'augd'}
% 'ELECTRON_DENSITY_DATA_CHORDS_SOURCES'                           {'DTN'}
% 'ELECTRON_DENSITY_DATA_CHORDS_SIGNALS'                           {'Ne_ld'}
% 'ELECTRON_DENSITY_DATA_CHORDS_NAMES_DISPLAY'                     {'Div. TS'}
% 'ELECTRON_DENSITY_DATA_CHORDS_TIME_START'                        '2.9'
% 'ELECTRON_DENSITY_DATA_CHORDS_TIME_END'                          '3.3'
% 'ELECTRON_DENSITY_DATA_CHORDS_REDUCED_SET'                       'true'
% 'ELECTRON_DENSITY_DATA_CHORDS_REDUCED_SET_TIME_DELTA'            '0.01'
% 'ELECTRON_TEMPERATURE_DATA_CHORDS_SHOT'                          '39409'
% 'ELECTRON_TEMPERATURE_DATA_CHORDS_EXPERIMENTS'                   {'augd'}
% 'ELECTRON_TEMPERATURE_DATA_CHORDS_SOURCES'                       {'DTN'}
% 'ELECTRON_TEMPERATURE_DATA_CHORDS_SIGNALS'                       {'Te_ld'}
% 'ELECTRON_TEMPERATURE_DATA_CHORDS_NAMES_DISPLAY'                 {'Div. TS'}
% 'ELECTRON_TEMPERATURE_DATA_CHORDS_TIME_START'                    '2.9'
% 'ELECTRON_TEMPERATURE_DATA_CHORDS_TIME_END'                      '3.3'
% 'ELECTRON_TEMPERATURE_DATA_CHORDS_REDUCED_SET'                   'true'
% 'ELECTRON_TEMPERATURE_DATA_CHORDS_REDUCED_SET_TIME_DELTA'        '0.01'
% 'ION_TEMPERATURE_DATA_CHORDS_SHOT'                               ''
% 'ION_TEMPERATURE_DATA_CHORDS_EXPERIMENTS'                        {}
% 'ION_TEMPERATURE_DATA_CHORDS_SOURCES'                            {}
% 'ION_TEMPERATURE_DATA_CHORDS_SIGNALS'                            {}
% 'ION_TEMPERATURE_DATA_CHORDS_NAMES_DISPLAY'                      {}
% 'ION_TEMPERATURE_DATA_CHORDS_TIME_START'                         ''
% 'ION_TEMPERATURE_DATA_CHORDS_TIME_END'                           ''
% 'ION_TEMPERATURE_DATA_CHORDS_REDUCED_SET'                        ''
% 'ION_TEMPERATURE_DATA_CHORDS_REDUCED_SET_TIME_DELTA'             ''
% 
% 'DATA_TARGETS_SHOT'                                              '39409'
% 'DATA_TARGETS_EXPERIMENT'                                        'augd'
% 'DATA_TARGETS_SOURCE'                                            'LSD'
% 'DATA_TARGETS_NAME_DISPLAY'                                      'LP'
% 'DATA_TARGETS_TIME_START'                                        '2.9'
% 'DATA_TARGETS_TIME_END'                                          '3.3'
% 'DATA_TARGETS_REDUCED_SET'                                       'true'
% 'DATA_TARGETS_REDUCED_SET_TIME_DELTA'                            '0.04'
% 'DATA_TARGETS_SEPARATRIX_SHIFT'                                  '+0.004'
% 
% 'DATA_SPECTROSCOPY_SHOT'                                         '39409'
% 'DATA_SPECTROSCOPY_EXPERIMENTS'                                  {'augd','augd','augd'}
% 'DATA_SPECTROSCOPY_SOURCES'                                      {'EVL','EVL','FVL'}
% 'DATA_SPECTROSCOPY_SIGNALS'                                      {'Ne','He0_3965','D_0_6561'}
% 'DATA_SPECTROSCOPY_NAMES_DISPLAY'                                {'Vis. spec.','Vis. spec.','Vis. spec.'}
% 'DATA_SPECTROSCOPY_TIME_START'                                   '2.9'
% 'DATA_SPECTROSCOPY_TIME_END'                                     '3.3'
% 'DATA_SPECTROSCOPY_REDUCED_SET'                                  'true'
% 'DATA_SPECTROSCOPY_REDUCED_SET_TIME_DELTA'                       '0.05'
%
% Output is a struct "exp_data" with all the data fields in the exp_data file
%
% input: main simulation structure
%
%% PRELIMINARY OPERATIONS

% Load the file

index = find(contains({simulation.run.name},'exp_data'));
if isempty(index)
    error('Error: exp_data not found');
end
file = simulation.run(index).file;
fid = fopen(file);

exp_data = struct();

%% READ THE ENTRIES

while ~feof(fid)
    line = fgetl(fid);
    if ischar(line) && ~isempty(strtrim(line))
        % Extract field and value using regular expression
        tokens = regexp(line, '''([^'']+)''\s+(.*)', 'tokens', 'once');
        if isempty(tokens)
            continue;
        end
        key = tokens{1};
        raw_value = strtrim(tokens{2});

        % Remove quotes if the value is quoted
        if startsWith(raw_value, '''') && endsWith(raw_value, '''')
            raw_value = raw_value(2:end-1);
        end

        % Parse value
        exp_data.(key) = parse_value(raw_value);
    end
end

frewind(fid);

fclose(fid);

end

%% AUXILIARY FUNCTION TO READ EACH TYPE OF ENTRY

function value = parse_value(str)
str = strtrim(str);

% Detect and evaluate MATLAB-style cell array
if startsWith(str, '{') && endsWith(str, '}')
    try
        value = eval(str);
        return;
    catch
        warning('Could not evaluate: %s', str);
    end
end

% Try numeric
num = str2double(str);
if ~isnan(num)
    value = num;
    return;
end

% Try logical
if strcmpi(str, 'true')
    value = true;
elseif strcmpi(str, 'false')
    value = false;
else
    % Return as plain string
    value = str;
end

end
