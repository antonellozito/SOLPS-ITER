function output = read_b2time(varargin)
%
% read_b2time reads the b2time.nc file created by B2.5
% Output is the structs "time_traces" and "profiles" with the main time traces
% and radial plasma profiles at all simulated times
%
% 1st input: main simulation structure
%
% Following inputs: strings which specify which subsets of fields
%                   should be read:
%                   - 'TIME_TRACES'
%                   - 'PROFILES'

%% PRELIMINARY OPERATIONS

% Load the file

simulation = varargin{1};

index = find(contains({simulation.run.name}, 'b2time.nc'));
if isempty(index)
   error('Error: b2time.nc not found');
end
file = simulation.run(index).file;
fid = fopen(file);
if (fid == -1)
   error('Error: b2time.nc not found');
end

% Select which group of fields to read

READ_TIME_TRACES = false;
READ_PROFILES = false;

if numel(varargin) == 1
    READ_TIME_TRACES = true;
    READ_PROFILES = true;
else
    if any(strcmp(varargin, 'TIME_TRACES'))
        READ_TIME_TRACES = true;
    end
    if any(strcmp(varargin, 'PROFILES'))
        READ_PROFILES = true;
    end
end

output = [];
output = set_netcdf_field(output, file, 'timesa', 'timesa');

%% READ THE TIME TRACES

if READ_TIME_TRACES

    try
        output = set_netcdf_fields(output, file, {
            'nasepm', 'nasepm';
        });
    catch
    end

    output = set_netcdf_fields(output, file, {
        'nesepm', 'nesepm';
        'tesepm', 'tesepm';
        'tisepm', 'tisepm';
        'posepm', 'posepm';
    });

    try
        output = set_netcdf_fields(output, file, {
            'dabsepm', 'dabsepm';
            'dmbsepm', 'dmbsepm';
            'tabsepm', 'tabsepm';
            'tmbsepm', 'tmbsepm';
        });
    catch
    end

    try
        output = set_netcdf_fields(output, file, {
            'nasepi', 'nasepi';
            'namxip', 'namxip';
            'nasepa', 'nasepa';
            'namxap', 'namxap';
        });
    catch
    end

    output = set_netcdf_fields(output, file, {
        'nesepi', 'nesepi';
        'nemxip', 'nemxip';
        'nesepa', 'nesepa';
        'nemxap', 'nemxap';
        'tesepi', 'tesepi';
        'temxip', 'temxip';
        'tesepa', 'tesepa';
        'temxap', 'temxap';
        'tisepi', 'tisepi';
        'timxip', 'timxip';
        'tisepa', 'tisepa';
        'timxap', 'timxap';
        'posepi', 'posepi';
        'pomxip', 'pomxip';
        'posepa', 'posepa';
        'pomxap', 'pomxap';
    });

    try
        output = set_netcdf_fields(output, file, {
            'dabsepi', 'dabsepi';
            'dmbsepi', 'dmbsepi';
            'tabsepi', 'tabsepi';
            'tmbsepi', 'tmbsepi';
            'dabsepa', 'dabsepa';
            'dmbsepa', 'dmbsepa';
            'tabsepa', 'tabsepa';
            'tmbsepa', 'tmbsepa';
        });
    catch
    end

    output = set_netcdf_fields(output, file, {
        'fnixip', 'fnixip', [];
        'fnixap', 'fnixap', [];
        'feexip', 'feexip', [];
        'feexap', 'feexap', [];
        'feixip', 'feixip', [];
        'feixap', 'feixap', [];
        'fetxip', 'fetxip', [];
        'fetxap', 'fetxap', [];
        'fniyip', 'fniyip', [];
        'fniyap', 'fniyap', [];
        'feeyip', 'feeyip', [];
        'feeyap', 'feeyap', [];
        'feiyip', 'feiyip', [];
        'feiyap', 'feiyap', [];
        'fetyip', 'fetyip', [];
        'fetyap', 'fetyap', [];
        'pwmxip', 'pwmxip', [];
        'pwmxap', 'pwmxap', [];
        'tmne', 'tmne', @(value) value';
        'tmte', 'tmte', @(value) value';
        'tmti', 'tmti', @(value) value';
    });

    fprintf('Time traces from b2time.nc read\n');

end

%% READ THE PROFILES

if READ_PROFILES

    has_split_targets = contains(simulation.geometry_type, 'double null') || contains(simulation.geometry_type, 'snowflake');

    try
        output = set_netcdf_fields(output, file, {
            'na3dl', 'na3dl';
            'na3di', 'na3di';
            'na3da', 'na3da';
            'na3dr', 'na3dr';
        });
        if has_split_targets
            output = set_netcdf_fields(output, file, {
                'na3dtl', 'na3dtl';
                'na3dtr', 'na3dtr';
            });
        end
    catch
    end

    output = set_netcdf_fields(output, file, {
        'ne3dl', 'ne3dl';
        'ne3di', 'ne3di';
        'ne3da', 'ne3da';
        'ne3dr', 'ne3dr';
    });
    if has_split_targets
        output = set_netcdf_fields(output, file, {
            'ne3dtl', 'ne3dtl';
            'ne3dtr', 'ne3dtr';
        });
    end

    output = set_netcdf_fields(output, file, {
        'te3dl', 'te3dl', @(value) value .* 6.2415e+18;
        'te3di', 'te3di', @(value) value .* 6.2415e+18;
        'te3da', 'te3da', @(value) value .* 6.2415e+18;
        'te3dr', 'te3dr', @(value) value .* 6.2415e+18;
    });
    if has_split_targets
        output = set_netcdf_fields(output, file, {
            'te3dtl', 'te3dtl';
            'te3dtr', 'te3dtr';
        });
    end

    output = set_netcdf_fields(output, file, {
        'ti3dl', 'ti3dl', @(value) value .* 6.2415e+18;
        'ti3di', 'ti3di', @(value) value .* 6.2415e+18;
        'ti3da', 'ti3da', @(value) value .* 6.2415e+18;
        'ti3dr', 'ti3dr', @(value) value .* 6.2415e+18;
    });
    if has_split_targets
        output = set_netcdf_fields(output, file, {
            'ti3dtl', 'ti3dtl';
            'ti3dtr', 'ti3dtr';
        });
    end

    output = set_netcdf_fields(output, file, {
        'fl3dl', 'fl3dl';
        'fl3dr', 'fl3dr';
    });
    if has_split_targets
        output = set_netcdf_fields(output, file, {
            'fl3dtl', 'fl3dtl';
            'fl3dtr', 'fl3dtr';
        });
    end

    output = set_netcdf_fields(output, file, {
        'fo3dl', 'fo3dl';
        'fo3dr', 'fo3dr';
    });
    if has_split_targets
        output = set_netcdf_fields(output, file, {
            'fo3dtl', 'fo3dtl';
            'fo3dtr', 'fo3dtr';
        });
    end

    output = set_netcdf_fields(output, file, {
        'fn3dl', 'fn3dl';
        'fn3dr', 'fn3dr';
    });
    if has_split_targets
        output = set_netcdf_fields(output, file, {
            'fn3dtl', 'fn3dtl';
            'fn3dtr', 'fn3dtr';
        });
    end

    output = set_netcdf_fields(output, file, {
        'fe3dl', 'fe3dl';
        'fe3dr', 'fe3dr';
    });
    if has_split_targets
        output = set_netcdf_fields(output, file, {
            'fe3dtl', 'fe3dtl';
            'fe3dtr', 'fe3dtr';
        });
    end

    output = set_netcdf_fields(output, file, {
        'fi3dl', 'fi3dl';
        'fi3dr', 'fi3dr';
    });
    if has_split_targets
        output = set_netcdf_fields(output, file, {
            'fi3dtl', 'fi3dtl';
            'fi3dtr', 'fi3dtr';
        });
    end

    output = set_netcdf_fields(output, file, {
        'ft3dl', 'ft3dl';
        'ft3dr', 'ft3dr';
    });
    if has_split_targets
        output = set_netcdf_fields(output, file, {
            'ft3dtl', 'ft3dtl';
            'ft3dtr', 'ft3dtr';
        });
    end

    try
        output = set_netcdf_fields(output, file, {
            'dab3dl', 'dab3dl';
            'dab3di', 'dab3di';
            'dab3da', 'dab3da';
            'dab3dr', 'dab3dr';
        });
        if has_split_targets
            output = set_netcdf_fields(output, file, {
                'dab3dtl', 'dab3dtl';
                'dab3dtr', 'dab3dtr';
            });
        end

        output = set_netcdf_fields(output, file, {
            'dmb3dl', 'dmb3dl';
            'dmb3di', 'dmb3di';
            'dmb3da', 'dmb3da';
            'dmb3dr', 'dmb3dr';
        });
        if has_split_targets
            output = set_netcdf_fields(output, file, {
                'dmb3dtl', 'dmb3dtl';
                'dmb3dtr', 'dmb3dtr';
            });
        end

        output = set_netcdf_fields(output, file, {
            'tab3dl', 'tab3dl', @(value) value .* 6.2415e+18;
            'tab3di', 'tab3di', @(value) value .* 6.2415e+18;
            'tab3da', 'tab3da', @(value) value .* 6.2415e+18;
            'tab3dr', 'tab3dr', @(value) value .* 6.2415e+18;
        });
        if has_split_targets
            output = set_netcdf_fields(output, file, {
                'tab3dtl', 'tab3dtl';
                'tab3dtr', 'tab3dtr';
            });
        end

        output = set_netcdf_fields(output, file, {
            'tmb3dl', 'tmb3dl', @(value) value .* 6.2415e+18;
            'tmb3di', 'tmb3di', @(value) value .* 6.2415e+18;
            'tmb3da', 'tmb3da', @(value) value .* 6.2415e+18;
            'tmb3dr', 'tmb3dr', @(value) value .* 6.2415e+18;
        });
        if has_split_targets
            output = set_netcdf_fields(output, file, {
                'tmb3dtl', 'tmb3dtl';
                'tmb3dtr', 'tmb3dtr';
            });
        end
    catch
    end

    output = set_netcdf_fields(output, file, {
        'dn3di', 'dn3di';
        'dn3da', 'dn3da';
        'dp3di', 'dp3di';
        'dp3da', 'dp3da';
        'ke3di', 'ke3di';
        'ke3da', 'ke3da';
        'ki3di', 'ki3di';
        'ki3da', 'ki3da';
        'vx3di', 'vx3di';
        'vx3da', 'vx3da';
        'vy3di', 'vy3di';
        'vy3da', 'vy3da';
        'vs3di', 'vs3di';
        'vs3da', 'vs3da';
    });

    fprintf('Profiles from b2time.nc read\n');

end

fclose(fid);

end
