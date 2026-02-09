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

index = find(contains({simulation.run.name},'b2time.nc'));
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
    if any(strcmp(varargin,'TIME_TRACES'))
        READ_TIME_TRACES = true;
    end
    if any(strcmp(varargin,'PROFILES'))
        READ_PROFILES = true;  
    end
end

output = [];

output.timesa.value = ncread(file,'timesa');
info = ncinfo(file,'timesa');
output.timesa.description = ncreadatt(file,'timesa','long_name');
output.timesa.unit = ncreadatt(file,'timesa','units');
output.timesa.dimensions = {info.Dimensions.Name};

%% READ THE TIME TRACES

if READ_TIME_TRACES

    try

    output.nasepm.value = ncread(file,'nasepm');
    info = ncinfo(file,'nasepm');
    output.nasepm.description = ncreadatt(file,'nasepm','long_name');
    output.nasepm.unit = ncreadatt(file,'nasepm','units');
    output.nasepm.dimensions = {info.Dimensions.Name};

    catch
    end

    output.nesepm.value = ncread(file,'nesepm');
    info = ncinfo(file,'nesepm');
    output.nesepm.description = ncreadatt(file,'nesepm','long_name');
    output.nesepm.unit = ncreadatt(file,'nesepm','units');
    output.nesepm.dimensions = {info.Dimensions.Name};

    output.tesepm.value = ncread(file,'tesepm');
    info = ncinfo(file,'tesepm');
    output.tesepm.description = ncreadatt(file,'tesepm','long_name');
    output.tesepm.unit = ncreadatt(file,'tesepm','units');
    output.tesepm.dimensions = {info.Dimensions.Name};

    output.tisepm.value = ncread(file,'tisepm');
    info = ncinfo(file,'tisepm');
    output.tisepm.description = ncreadatt(file,'tisepm','long_name');
    output.tisepm.unit = ncreadatt(file,'tisepm','units');
    output.tisepm.dimensions = {info.Dimensions.Name};

    output.posepm.value = ncread(file,'posepm');
    info = ncinfo(file,'posepm');
    output.posepm.description = ncreadatt(file,'posepm','long_name');
    output.posepm.unit = ncreadatt(file,'posepm','units');
    output.posepm.dimensions = {info.Dimensions.Name};

    try

    output.dabsepm.value = ncread(file,'dabsepm');
    info = ncinfo(file,'dabsepm');
    output.dabsepm.description = ncreadatt(file,'dabsepm','long_name');
    output.dabsepm.unit = ncreadatt(file,'dabsepm','units');
    output.dabsepm.dimensions = {info.Dimensions.Name};

    output.dmbsepm.value = ncread(file,'dmbsepm');
    info = ncinfo(file,'dmbsepm');
    output.dmbsepm.description = ncreadatt(file,'dmbsepm','long_name');
    output.dmbsepm.unit = ncreadatt(file,'dmbsepm','units');
    output.dmbsepm.dimensions = {info.Dimensions.Name};

    output.tabsepm.value = ncread(file,'tabsepm');
    info = ncinfo(file,'tabsepm');
    output.tabsepm.description = ncreadatt(file,'tabsepm','long_name');
    output.tabsepm.unit = ncreadatt(file,'tabsepm','units');
    output.tabsepm.dimensions = {info.Dimensions.Name};

    output.tmbsepm.value = ncread(file,'tmbsepm');
    info = ncinfo(file,'tmbsepm');
    output.tmbsepm.description = ncreadatt(file,'tmbsepm','long_name');
    output.tmbsepm.unit = ncreadatt(file,'tmbsepm','units');
    output.tmbsepm.dimensions = {info.Dimensions.Name};

    catch
    end

    try

    output.nasepi.value = ncread(file,'nasepi');
    info = ncinfo(file,'nasepi');
    output.nasepi.description = ncreadatt(file,'nasepi','long_name');
    output.nasepi.unit = ncreadatt(file,'nasepi','units');
    output.nasepi.dimensions = {info.Dimensions.Name};

    output.namxip.value = ncread(file,'namxip');
    info = ncinfo(file,'namxip');
    output.namxip.description = ncreadatt(file,'namxip','long_name');
    output.namxip.unit = ncreadatt(file,'namxip','units');
    output.namxip.dimensions = {info.Dimensions.Name};

    output.nasepa.value = ncread(file,'nasepa');
    info = ncinfo(file,'nasepa');
    output.nasepa.description = ncreadatt(file,'nasepa','long_name');
    output.nasepa.unit = ncreadatt(file,'nasepa','units');
    output.nasepa.dimensions = {info.Dimensions.Name};

    output.namxap.value = ncread(file,'namxap');
    info = ncinfo(file,'namxap');
    output.namxap.description = ncreadatt(file,'namxap','long_name');
    output.namxap.unit = ncreadatt(file,'namxap','units');
    output.namxap.dimensions = {info.Dimensions.Name};

    catch
    end

    output.nesepi.value = ncread(file,'nesepi');
    info = ncinfo(file,'nesepi');
    output.nesepi.description = ncreadatt(file,'nesepi','long_name');
    output.nesepi.unit = ncreadatt(file,'nesepi','units');
    output.nesepi.dimensions = {info.Dimensions.Name};

    output.nemxip.value = ncread(file,'nemxip');
    info = ncinfo(file,'nemxip');
    output.nemxip.description = ncreadatt(file,'nemxip','long_name');
    output.nemxip.unit = ncreadatt(file,'nemxip','units');
    output.nemxip.dimensions = {info.Dimensions.Name};

    output.nesepa.value = ncread(file,'nesepa');
    info = ncinfo(file,'nesepa');
    output.nesepa.description = ncreadatt(file,'nesepa','long_name');
    output.nesepa.unit = ncreadatt(file,'nesepa','units');
    output.nesepa.dimensions = {info.Dimensions.Name};

    output.nemxap.value = ncread(file,'nemxap');
    info = ncinfo(file,'nemxap');
    output.nemxap.description = ncreadatt(file,'nemxap','long_name');
    output.nemxap.unit = ncreadatt(file,'nemxap','units');
    output.nemxap.dimensions = {info.Dimensions.Name};

    output.tesepi.value = ncread(file,'tesepi');
    info = ncinfo(file,'tesepi');
    output.tesepi.description = ncreadatt(file,'tesepi','long_name');
    output.tesepi.unit = ncreadatt(file,'tesepi','units');
    output.tesepi.dimensions = {info.Dimensions.Name};

    output.temxip.value = ncread(file,'temxip');
    info = ncinfo(file,'temxip');
    output.temxip.description = ncreadatt(file,'temxip','long_name');
    output.temxip.unit = ncreadatt(file,'temxip','units');
    output.temxip.dimensions = {info.Dimensions.Name};

    output.tesepa.value = ncread(file,'tesepa');
    info = ncinfo(file,'tesepa');
    output.tesepa.description = ncreadatt(file,'tesepa','long_name');
    output.tesepa.unit = ncreadatt(file,'tesepa','units');
    output.tesepa.dimensions = {info.Dimensions.Name};

    output.temxap.value = ncread(file,'temxap');
    info = ncinfo(file,'temxap');
    output.temxap.description = ncreadatt(file,'temxap','long_name');
    output.temxap.unit = ncreadatt(file,'temxap','units');
    output.temxap.dimensions = {info.Dimensions.Name};

    output.tisepi.value = ncread(file,'tisepi');
    info = ncinfo(file,'tisepi');
    output.tisepi.description = ncreadatt(file,'tisepi','long_name');
    output.tisepi.unit = ncreadatt(file,'tisepi','units');
    output.tisepi.dimensions = {info.Dimensions.Name};

    output.timxip.value = ncread(file,'timxip');
    info = ncinfo(file,'timxip');
    output.timxip.description = ncreadatt(file,'timxip','long_name');
    output.timxip.unit = ncreadatt(file,'timxip','units');
    output.timxip.dimensions = {info.Dimensions.Name};

    output.tisepa.value = ncread(file,'tisepa');
    info = ncinfo(file,'tisepa');
    output.tisepa.description = ncreadatt(file,'tisepa','long_name');
    output.tisepa.unit = ncreadatt(file,'tisepa','units');
    output.tisepa.dimensions = {info.Dimensions.Name};

    output.timxap.value = ncread(file,'timxap');
    info = ncinfo(file,'timxap');
    output.timxap.description = ncreadatt(file,'timxap','long_name');
    output.timxap.unit = ncreadatt(file,'timxap','units');
    output.timxap.dimensions = {info.Dimensions.Name};

    output.posepi.value = ncread(file,'posepi');
    info = ncinfo(file,'posepi');
    output.posepi.description = ncreadatt(file,'posepi','long_name');
    output.posepi.unit = ncreadatt(file,'posepi','units');
    output.posepi.dimensions = {info.Dimensions.Name};

    output.pomxip.value = ncread(file,'pomxip');
    info = ncinfo(file,'pomxip');
    output.pomxip.description = ncreadatt(file,'pomxip','long_name');
    output.pomxip.unit = ncreadatt(file,'pomxip','units');
    output.pomxip.dimensions = {info.Dimensions.Name};

    output.posepa.value = ncread(file,'posepa');
    info = ncinfo(file,'posepa');
    output.posepa.description = ncreadatt(file,'posepa','long_name');
    output.posepa.unit = ncreadatt(file,'posepa','units');
    output.posepa.dimensions = {info.Dimensions.Name};

    output.pomxap.value = ncread(file,'pomxap');
    info = ncinfo(file,'pomxap');
    output.pomxap.description = ncreadatt(file,'pomxap','long_name');
    output.pomxap.unit = ncreadatt(file,'pomxap','units');
    output.pomxap.dimensions = {info.Dimensions.Name};

    try

    output.dabsepi.value = ncread(file,'dabsepi');
    info = ncinfo(file,'dabsepi');
    output.dabsepi.description = ncreadatt(file,'dabsepi','long_name');
    output.dabsepi.unit = ncreadatt(file,'dabsepi','units');
    output.dabsepi.dimensions = {info.Dimensions.Name};

    output.dmbsepi.value = ncread(file,'dmbsepi');
    info = ncinfo(file,'dmbsepi');
    output.dmbsepi.description = ncreadatt(file,'dmbsepi','long_name');
    output.dmbsepi.unit = ncreadatt(file,'dmbsepi','units');
    output.dmbsepi.dimensions = {info.Dimensions.Name};

    output.tabsepi.value = ncread(file,'tabsepi');
    info = ncinfo(file,'tabsepi');
    output.tabsepi.description = ncreadatt(file,'tabsepi','long_name');
    output.tabsepi.unit = ncreadatt(file,'tabsepi','units');
    output.tabsepi.dimensions = {info.Dimensions.Name};

    output.tmbsepi.value = ncread(file,'tmbsepi');
    info = ncinfo(file,'tmbsepi');
    output.tmbsepi.description = ncreadatt(file,'tmbsepi','long_name');
    output.tmbsepi.unit = ncreadatt(file,'tmbsepi','units');
    output.tmbsepi.dimensions = {info.Dimensions.Name};

    output.dabsepa.value = ncread(file,'dabsepa');
    info = ncinfo(file,'dabsepa');
    output.dabsepa.description = ncreadatt(file,'dabsepa','long_name');
    output.dabsepa.unit = ncreadatt(file,'dabsepa','units');
    output.dabsepa.dimensions = {info.Dimensions.Name};

    output.dmbsepa.value = ncread(file,'dmbsepa');
    info = ncinfo(file,'dmbsepa');
    output.dmbsepa.description = ncreadatt(file,'dmbsepa','long_name');
    output.dmbsepa.unit = ncreadatt(file,'dmbsepa','units');
    output.dmbsepa.dimensions = {info.Dimensions.Name};

    output.tabsepa.value = ncread(file,'tabsepa');
    info = ncinfo(file,'tabsepa');
    output.tabsepa.description = ncreadatt(file,'tabsepa','long_name');
    output.tabsepa.unit = ncreadatt(file,'tabsepa','units');
    output.tabsepa.dimensions = {info.Dimensions.Name};

    output.tmbsepa.value = ncread(file,'tmbsepa');
    info = ncinfo(file,'tmbsepa');
    output.tmbsepa.description = ncreadatt(file,'tmbsepa','long_name');
    output.tmbsepa.unit = ncreadatt(file,'tmbsepa','units');
    output.tmbsepa.dimensions = {info.Dimensions.Name};

    catch
    end

    output.fnixip.value = ncread(file,'fnixip');
    info = ncinfo(file,'fnixip');
    output.fnixip.description = ncreadatt(file,'fnixip','long_name');
    output.fnixip.unit = ncreadatt(file,'fnixip','units');
    output.fnixip.dimensions = {info.Dimensions.Name};

    output.fnixap.value = ncread(file,'fnixap');
    info = ncinfo(file,'fnixap');
    output.fnixap.description = ncreadatt(file,'fnixap','long_name');
    output.fnixap.unit = ncreadatt(file,'fnixap','units');
    output.fnixap.dimensions = {info.Dimensions.Name};

    output.feexip.value = ncread(file,'feexip');
    info = ncinfo(file,'feexip');
    output.feexip.description = ncreadatt(file,'feexip','long_name');
    output.feexip.unit = ncreadatt(file,'feexip','units');
    output.feexip.dimensions = {info.Dimensions.Name};

    output.feexap.value = ncread(file,'feexap');
    info = ncinfo(file,'feexap');
    output.feexap.description = ncreadatt(file,'feexap','long_name');
    output.feexap.unit = ncreadatt(file,'feexap','units');
    output.feexap.dimensions = {info.Dimensions.Name};

    output.feixip.value = ncread(file,'feixip');
    info = ncinfo(file,'feixip');
    output.feixip.description = ncreadatt(file,'feixip','long_name');
    output.feixip.unit = ncreadatt(file,'feixip','units');
    output.feixip.dimensions = {info.Dimensions.Name};

    output.feixap.value = ncread(file,'feixap');
    info = ncinfo(file,'feixap');
    output.feixap.description = ncreadatt(file,'feixap','long_name');
    output.feixap.unit = ncreadatt(file,'feixap','units');
    output.feixap.dimensions = {info.Dimensions.Name};

    output.fetxip.value = ncread(file,'fetxip');
    info = ncinfo(file,'fetxip');
    output.fetxip.description = ncreadatt(file,'fetxip','long_name');
    output.fetxip.unit = ncreadatt(file,'fetxip','units');
    output.fetxip.dimensions = {info.Dimensions.Name};

    output.fetxap.value = ncread(file,'fetxap');
    info = ncinfo(file,'fetxap');
    output.fetxap.description = ncreadatt(file,'fetxap','long_name');
    output.fetxap.unit = ncreadatt(file,'fetxap','units');
    output.fetxap.dimensions = {info.Dimensions.Name};

    output.fniyip.value = ncread(file,'fniyip');
    info = ncinfo(file,'fniyip');
    output.fniyip.description = ncreadatt(file,'fniyip','long_name');
    output.fniyip.unit = ncreadatt(file,'fniyip','units');
    output.fniyip.dimensions = {info.Dimensions.Name};

    output.fniyap.value = ncread(file,'fniyap');
    info = ncinfo(file,'fniyap');
    output.fniyap.description = ncreadatt(file,'fniyap','long_name');
    output.fniyap.unit = ncreadatt(file,'fniyap','units');
    output.fniyap.dimensions = {info.Dimensions.Name};

    output.feeyip.value = ncread(file,'feeyip');
    info = ncinfo(file,'feeyip');
    output.feeyip.description = ncreadatt(file,'feeyip','long_name');
    output.feeyip.unit = ncreadatt(file,'feeyip','units');
    output.feeyip.dimensions = {info.Dimensions.Name};

    output.feeyap.value = ncread(file,'feeyap');
    info = ncinfo(file,'feeyap');
    output.feeyap.description = ncreadatt(file,'feeyap','long_name');
    output.feeyap.unit = ncreadatt(file,'feeyap','units');
    output.feeyap.dimensions = {info.Dimensions.Name};

    output.feiyip.value = ncread(file,'feiyip');
    info = ncinfo(file,'feiyip');
    output.feiyip.description = ncreadatt(file,'feiyip','long_name');
    output.feiyip.unit = ncreadatt(file,'feiyip','units');
    output.feiyip.dimensions = {info.Dimensions.Name};

    output.feiyap.value = ncread(file,'feiyap');
    info = ncinfo(file,'feiyap');
    output.feiyap.description = ncreadatt(file,'feiyap','long_name');
    output.feiyap.unit = ncreadatt(file,'feiyap','units');
    output.feiyap.dimensions = {info.Dimensions.Name};

    output.fetyip.value = ncread(file,'fetyip');
    info = ncinfo(file,'fetyip');
    output.fetyip.description = ncreadatt(file,'fetyip','long_name');
    output.fetyip.unit = ncreadatt(file,'fetyip','units');
    output.fetyip.dimensions = {info.Dimensions.Name};

    output.fetyap.value = ncread(file,'fetyap');
    info = ncinfo(file,'fetyap');
    output.fetyap.description = ncreadatt(file,'fetyap','long_name');
    output.fetyap.unit = ncreadatt(file,'fetyap','units');
    output.fetyap.dimensions = {info.Dimensions.Name};

    output.pwmxip.value = ncread(file,'pwmxip');
    info = ncinfo(file,'pwmxip');
    output.pwmxip.description = ncreadatt(file,'pwmxip','long_name');
    output.pwmxip.unit = ncreadatt(file,'pwmxip','units');
    output.pwmxip.dimensions = {info.Dimensions.Name};

    output.pwmxap.value = ncread(file,'pwmxap');
    info = ncinfo(file,'pwmxap');
    output.pwmxap.description = ncreadatt(file,'pwmxap','long_name');
    output.pwmxap.unit = ncreadatt(file,'pwmxap','units');
    output.pwmxap.dimensions = {info.Dimensions.Name};

    output.tmne.value = ncread(file,'tmne')';
    info = ncinfo(file,'tmne');
    output.tmne.description = ncreadatt(file,'tmne','long_name');
    output.tmne.unit = ncreadatt(file,'tmne','units');
    output.tmne.dimensions = {info.Dimensions.Name};

    output.tmte.value = ncread(file,'tmte')';
    info = ncinfo(file,'tmte');
    output.tmte.description = ncreadatt(file,'tmte','long_name');
    output.tmte.unit = ncreadatt(file,'tmte','units');
    output.tmte.dimensions = {info.Dimensions.Name};

    output.tmti.value = ncread(file,'tmti')';
    info = ncinfo(file,'tmti');
    output.tmti.description = ncreadatt(file,'tmti','long_name');
    output.tmti.unit = ncreadatt(file,'tmti','units');
    output.tmti.dimensions = {info.Dimensions.Name};

    fprintf('Time traces from b2time.nc read\n');

end

%% READ THE PROFILES

if READ_PROFILES

    try

    output.na3dl.value = ncread(file,'na3dl');
    info = ncinfo(file,'na3dl');
    output.na3dl.description = ncreadatt(file,'na3dl','long_name');
    output.na3dl.unit = ncreadatt(file,'na3dl','units');
    output.na3dl.dimensions = {info.Dimensions.Name};

    output.na3di.value = ncread(file,'na3di');
    info = ncinfo(file,'na3di');
    output.na3di.description = ncreadatt(file,'na3di','long_name');
    output.na3di.unit = ncreadatt(file,'na3di','units');
    output.na3di.dimensions = {info.Dimensions.Name};

    output.na3da.value = ncread(file,'na3da');
    info = ncinfo(file,'na3da');
    output.na3da.description = ncreadatt(file,'na3da','long_name');
    output.na3da.unit = ncreadatt(file,'na3da','units');
    output.na3da.dimensions = {info.Dimensions.Name};

    output.na3dr.value = ncread(file,'na3dr');
    info = ncinfo(file,'na3dr');
    output.na3dr.description = ncreadatt(file,'na3dr','long_name');
    output.na3dr.unit = ncreadatt(file,'na3dr','units');
    output.na3dr.dimensions = {info.Dimensions.Name};

    if contains(simulation.geometry_type,'double null') || contains(simulation.geometry_type,'snowflake')
        output.na3dtl.value = ncread(file,'na3dtl');
        info = ncinfo(file,'na3dtl');
        output.na3dtl.description = ncreadatt(file,'na3dtl','long_name');
        output.na3dtl.unit = ncreadatt(file,'na3dtl','units');
        output.na3dtl.dimensions = {info.Dimensions.Name};

        output.na3dtr.value = ncread(file,'na3dtr');
        info = ncinfo(file,'na3dtr');
        output.na3dtr.description = ncreadatt(file,'na3dtr','long_name');
        output.na3dtr.unit = ncreadatt(file,'na3dtr','units');
        output.na3dtr.dimensions = {info.Dimensions.Name};
    end

    catch
    end

    output.ne3dl.value = ncread(file,'ne3dl');
    info = ncinfo(file,'ne3dl');
    output.ne3dl.description = ncreadatt(file,'ne3dl','long_name');
    output.ne3dl.unit = ncreadatt(file,'ne3dl','units');
    output.ne3dl.dimensions = {info.Dimensions.Name};

    output.ne3di.value = ncread(file,'ne3di');
    info = ncinfo(file,'ne3di');
    output.ne3di.description = ncreadatt(file,'ne3di','long_name');
    output.ne3di.unit = ncreadatt(file,'ne3di','units');
    output.ne3di.dimensions = {info.Dimensions.Name};

    output.ne3da.value = ncread(file,'ne3da');
    info = ncinfo(file,'ne3da');
    output.ne3da.description = ncreadatt(file,'ne3da','long_name');
    output.ne3da.unit = ncreadatt(file,'ne3da','units');
    output.ne3da.dimensions = {info.Dimensions.Name};

    output.ne3dr.value = ncread(file,'ne3dr');
    info = ncinfo(file,'ne3dr');
    output.ne3dr.description = ncreadatt(file,'ne3dr','long_name');
    output.ne3dr.unit = ncreadatt(file,'ne3dr','units');
    output.ne3dr.dimensions = {info.Dimensions.Name};

    if contains(simulation.geometry_type,'double null') || contains(simulation.geometry_type,'snowflake')
        output.ne3dtl.value = ncread(file,'ne3dtl');
        info = ncinfo(file,'ne3dtl');
        output.ne3dtl.description = ncreadatt(file,'ne3dtl','long_name');
        output.ne3dtl.unit = ncreadatt(file,'ne3dtl','units');
        output.ne3dtl.dimensions = {info.Dimensions.Name};

        output.ne3dtr.value = ncread(file,'ne3dtr');
        info = ncinfo(file,'ne3dtr');
        output.ne3dtr.description = ncreadatt(file,'ne3dtr','long_name');
        output.ne3dtr.unit = ncreadatt(file,'ne3dtr','units');
        output.ne3dtr.dimensions = {info.Dimensions.Name};
    end

    output.te3dl.value = ncread(file,'te3dl').*6.2415e+18;
    info = ncinfo(file,'te3dl');
    output.te3dl.description = ncreadatt(file,'te3dl','long_name');
    output.te3dl.unit = ncreadatt(file,'te3dl','units');
    output.te3dl.dimensions = {info.Dimensions.Name};

    output.te3di.value = ncread(file,'te3di').*6.2415e+18;
    info = ncinfo(file,'te3di');
    output.te3di.description = ncreadatt(file,'te3di','long_name');
    output.te3di.unit = ncreadatt(file,'te3di','units');
    output.te3di.dimensions = {info.Dimensions.Name};

    output.te3da.value = ncread(file,'te3da').*6.2415e+18;
    info = ncinfo(file,'te3da');
    output.te3da.description = ncreadatt(file,'te3da','long_name');
    output.te3da.unit = ncreadatt(file,'te3da','units');
    output.te3da.dimensions = {info.Dimensions.Name};

    output.te3dr.value = ncread(file,'te3dr').*6.2415e+18;
    info = ncinfo(file,'te3dr');
    output.te3dr.description = ncreadatt(file,'te3dr','long_name');
    output.te3dr.unit = ncreadatt(file,'te3dr','units');
    output.te3dr.dimensions = {info.Dimensions.Name};

    if contains(simulation.geometry_type,'double null') || contains(simulation.geometry_type,'snowflake')
        output.te3dtl.value = ncread(file,'te3dtl');
        info = ncinfo(file,'te3dtl');
        output.te3dtl.description = ncreadatt(file,'te3dtl','long_name');
        output.te3dtl.unit = ncreadatt(file,'te3dtl','units');
        output.te3dtl.dimensions = {info.Dimensions.Name};

        output.te3dtr.value = ncread(file,'te3dtr');
        info = ncinfo(file,'te3dtr');
        output.te3dtr.description = ncreadatt(file,'te3dtr','long_name');
        output.te3dtr.unit = ncreadatt(file,'te3dtr','units');
        output.te3dtr.dimensions = {info.Dimensions.Name};
    end

    output.ti3dl.value = ncread(file,'ti3dl').*6.2415e+18;
    info = ncinfo(file,'ti3dl');
    output.ti3dl.description = ncreadatt(file,'ti3dl','long_name');
    output.ti3dl.unit = ncreadatt(file,'ti3dl','units');
    output.ti3dl.dimensions = {info.Dimensions.Name};

    output.ti3di.value = ncread(file,'ti3di').*6.2415e+18;
    info = ncinfo(file,'ti3di');
    output.ti3di.description = ncreadatt(file,'ti3di','long_name');
    output.ti3di.unit = ncreadatt(file,'ti3di','units');
    output.ti3di.dimensions = {info.Dimensions.Name};

    output.ti3da.value = ncread(file,'ti3da').*6.2415e+18;
    info = ncinfo(file,'ti3da');
    output.ti3da.description = ncreadatt(file,'ti3da','long_name');
    output.ti3da.unit = ncreadatt(file,'ti3da','units');
    output.ti3da.dimensions = {info.Dimensions.Name};

    output.ti3dr.value = ncread(file,'ti3dr').*6.2415e+18;
    info = ncinfo(file,'ti3dr');
    output.ti3dr.description = ncreadatt(file,'ti3dr','long_name');
    output.ti3dr.unit = ncreadatt(file,'ti3dr','units');
    output.ti3dr.dimensions = {info.Dimensions.Name};

    if contains(simulation.geometry_type,'double null') || contains(simulation.geometry_type,'snowflake')
        output.ti3dtl.value = ncread(file,'ti3dtl');
        info = ncinfo(file,'ti3dtl');
        output.ti3dtl.description = ncreadatt(file,'ti3dtl','long_name');
        output.ti3dtl.unit = ncreadatt(file,'ti3dtl','units');
        output.ti3dtl.dimensions = {info.Dimensions.Name};

        output.ti3dtr.value = ncread(file,'ti3dtr');
        info = ncinfo(file,'ti3dtr');
        output.ti3dtr.description = ncreadatt(file,'ti3dtr','long_name');
        output.ti3dtr.unit = ncreadatt(file,'ti3dtr','units');
        output.ti3dtr.dimensions = {info.Dimensions.Name};
    end

    output.fl3dl.value = ncread(file,'fl3dl');
    info = ncinfo(file,'fl3dl');
    output.fl3dl.description = ncreadatt(file,'fl3dl','long_name');
    output.fl3dl.unit = ncreadatt(file,'fl3dl','units');
    output.fl3dl.dimensions = {info.Dimensions.Name};

    output.fl3dr.value = ncread(file,'fl3dr');
    info = ncinfo(file,'fl3dr');
    output.fl3dr.description = ncreadatt(file,'fl3dr','long_name');
    output.fl3dr.unit = ncreadatt(file,'fl3dr','units');
    output.fl3dr.dimensions = {info.Dimensions.Name};

    if contains(simulation.geometry_type,'double null') || contains(simulation.geometry_type,'snowflake')
        output.fl3dtl.value = ncread(file,'fl3dtl');
        info = ncinfo(file,'fl3dtl');
        output.fl3dtl.description = ncreadatt(file,'fl3dtl','long_name');
        output.fl3dtl.unit = ncreadatt(file,'fl3dtl','units');
        output.fl3dtl.dimensions = {info.Dimensions.Name};

        output.fl3dtr.value = ncread(file,'fl3dtr');
        info = ncinfo(file,'fl3dtr');
        output.fl3dtr.description = ncreadatt(file,'fl3dtr','long_name');
        output.fl3dtr.unit = ncreadatt(file,'fl3dtr','units');
        output.fl3dtr.dimensions = {info.Dimensions.Name};
    end

    output.fo3dl.value = ncread(file,'fo3dl');
    info = ncinfo(file,'fo3dl');
    output.fo3dl.description = ncreadatt(file,'fo3dl','long_name');
    output.fo3dl.unit = ncreadatt(file,'fo3dl','units');
    output.fo3dl.dimensions = {info.Dimensions.Name};

    output.fo3dr.value = ncread(file,'fo3dr');
    info = ncinfo(file,'fo3dr');
    output.fo3dr.description = ncreadatt(file,'fo3dr','long_name');
    output.fo3dr.unit = ncreadatt(file,'fo3dr','units');
    output.fo3dr.dimensions = {info.Dimensions.Name};

    if contains(simulation.geometry_type,'double null') || contains(simulation.geometry_type,'snowflake')
        output.fo3dtl.value = ncread(file,'fo3dtl');
        info = ncinfo(file,'fo3dtl');
        output.fo3dtl.description = ncreadatt(file,'fo3dtl','long_name');
        output.fo3dtl.unit = ncreadatt(file,'fo3dtl','units');
        output.fo3dtl.dimensions = {info.Dimensions.Name};

        output.fo3dtr.value = ncread(file,'fo3dtr');
        info = ncinfo(file,'fo3dtr');
        output.fo3dtr.description = ncreadatt(file,'fo3dtr','long_name');
        output.fo3dtr.unit = ncreadatt(file,'fo3dtr','units');
        output.fo3dtr.dimensions = {info.Dimensions.Name};
    end

    output.fn3dl.value = ncread(file,'fn3dl');
    info = ncinfo(file,'fn3dl');
    output.fn3dl.description = ncreadatt(file,'fn3dl','long_name');
    output.fn3dl.unit = ncreadatt(file,'fn3dl','units');
    output.fn3dl.dimensions = {info.Dimensions.Name};

    output.fn3dr.value = ncread(file,'fn3dr');
    info = ncinfo(file,'fn3dr');
    output.fn3dr.description = ncreadatt(file,'fn3dr','long_name');
    output.fn3dr.unit = ncreadatt(file,'fn3dr','units');
    output.fn3dr.dimensions = {info.Dimensions.Name};

    if contains(simulation.geometry_type,'double null') || contains(simulation.geometry_type,'snowflake')
        output.fn3dtl.value = ncread(file,'fn3dtl');
        info = ncinfo(file,'fn3dtl');
        output.fn3dtl.description = ncreadatt(file,'fn3dtl','long_name');
        output.fn3dtl.unit = ncreadatt(file,'fn3dtl','units');
        output.fn3dtl.dimensions = {info.Dimensions.Name};

        output.fn3dtr.value = ncread(file,'fn3dtr');
        info = ncinfo(file,'fn3dtr');
        output.fn3dtr.description = ncreadatt(file,'fn3dtr','long_name');
        output.fn3dtr.unit = ncreadatt(file,'fn3dtr','units');
        output.fn3dtr.dimensions = {info.Dimensions.Name};
    end

    output.fe3dl.value = ncread(file,'fe3dl');
    info = ncinfo(file,'fe3dl');
    output.fe3dl.description = ncreadatt(file,'fe3dl','long_name');
    output.fe3dl.unit = ncreadatt(file,'fe3dl','units');
    output.fe3dl.dimensions = {info.Dimensions.Name};

    output.fe3dr.value = ncread(file,'fe3dr');
    info = ncinfo(file,'fe3dr');
    output.fe3dr.description = ncreadatt(file,'fe3dr','long_name');
    output.fe3dr.unit = ncreadatt(file,'fe3dr','units');
    output.fe3dr.dimensions = {info.Dimensions.Name};

    if contains(simulation.geometry_type,'double null') || contains(simulation.geometry_type,'snowflake')
        output.fe3dtl.value = ncread(file,'fe3dtl');
        info = ncinfo(file,'fe3dtl');
        output.fe3dtl.description = ncreadatt(file,'fe3dtl','long_name');
        output.fe3dtl.unit = ncreadatt(file,'fe3dtl','units');
        output.fe3dtl.dimensions = {info.Dimensions.Name};

        output.fe3dtr.value = ncread(file,'fe3dtr');
        info = ncinfo(file,'fe3dtr');
        output.fe3dtr.description = ncreadatt(file,'fe3dtr','long_name');
        output.fe3dtr.unit = ncreadatt(file,'fe3dtr','units');
        output.fe3dtr.dimensions = {info.Dimensions.Name};
    end

    output.fi3dl.value = ncread(file,'fi3dl');
    info = ncinfo(file,'fi3dl');
    output.fi3dl.description = ncreadatt(file,'fi3dl','long_name');
    output.fi3dl.unit = ncreadatt(file,'fi3dl','units');
    output.fi3dl.dimensions = {info.Dimensions.Name};

    output.fi3dr.value = ncread(file,'fi3dr');
    info = ncinfo(file,'fi3dr');
    output.fi3dr.description = ncreadatt(file,'fi3dr','long_name');
    output.fi3dr.unit = ncreadatt(file,'fi3dr','units');
    output.fi3dr.dimensions = {info.Dimensions.Name};

    if contains(simulation.geometry_type,'double null') || contains(simulation.geometry_type,'snowflake')
        output.fi3dtl.value = ncread(file,'fi3dtl');
        info = ncinfo(file,'fi3dtl');
        output.fi3dtl.description = ncreadatt(file,'fi3dtl','long_name');
        output.fi3dtl.unit = ncreadatt(file,'fi3dtl','units');
        output.fi3dtl.dimensions = {info.Dimensions.Name};

        output.fi3dtr.value = ncread(file,'fi3dtr');
        info = ncinfo(file,'fi3dtr');
        output.fi3dtr.description = ncreadatt(file,'fi3dtr','long_name');
        output.fi3dtr.unit = ncreadatt(file,'fi3dtr','units');
        output.fi3dtr.dimensions = {info.Dimensions.Name};
    end

    output.ft3dl.value = ncread(file,'ft3dl');
    info = ncinfo(file,'ft3dl');
    output.ft3dl.description = ncreadatt(file,'ft3dl','long_name');
    output.ft3dl.unit = ncreadatt(file,'ft3dl','units');
    output.ft3dl.dimensions = {info.Dimensions.Name};

    output.ft3dr.value = ncread(file,'ft3dr');
    info = ncinfo(file,'ft3dr');
    output.ft3dr.description = ncreadatt(file,'ft3dr','long_name');
    output.ft3dr.unit = ncreadatt(file,'ft3dr','units');
    output.ft3dr.dimensions = {info.Dimensions.Name};

    if contains(simulation.geometry_type,'double null') || contains(simulation.geometry_type,'snowflake')
        output.ft3dtl.value = ncread(file,'ft3dtl');
        info = ncinfo(file,'ft3dtl');
        output.ft3dtl.description = ncreadatt(file,'ft3dtl','long_name');
        output.ft3dtl.unit = ncreadatt(file,'ft3dtl','units');
        output.ft3dtl.dimensions = {info.Dimensions.Name};

        output.ft3dtr.value = ncread(file,'ft3dtr');
        info = ncinfo(file,'ft3dtr');
        output.ft3dtr.description = ncreadatt(file,'ft3dtr','long_name');
        output.ft3dtr.unit = ncreadatt(file,'ft3dtr','units');
        output.ft3dtr.dimensions = {info.Dimensions.Name};
    end

    try

    output.dab3dl.value = ncread(file,'dab3dl');
    info = ncinfo(file,'dab3dl');
    output.dab3dl.description = ncreadatt(file,'dab3dl','long_name');
    output.dab3dl.unit = ncreadatt(file,'dab3dl','units');
    output.dab3dl.dimensions = {info.Dimensions.Name};

    output.dab3di.value = ncread(file,'dab3di');
    info = ncinfo(file,'dab3di');
    output.dab3di.description = ncreadatt(file,'dab3di','long_name');
    output.dab3di.unit = ncreadatt(file,'dab3di','units');
    output.dab3di.dimensions = {info.Dimensions.Name};

    output.dab3da.value = ncread(file,'dab3da');
    info = ncinfo(file,'dab3da');
    output.dab3da.description = ncreadatt(file,'dab3da','long_name');
    output.dab3da.unit = ncreadatt(file,'dab3da','units');
    output.dab3da.dimensions = {info.Dimensions.Name};

    output.dab3dr.value = ncread(file,'dab3dr');
    info = ncinfo(file,'dab3dr');
    output.dab3dr.description = ncreadatt(file,'dab3dr','long_name');
    output.dab3dr.unit = ncreadatt(file,'dab3dr','units');
    output.dab3dr.dimensions = {info.Dimensions.Name};

    if contains(simulation.geometry_type,'double null') || contains(simulation.geometry_type,'snowflake')
        output.dab3dtl.value = ncread(file,'dab3dtl');
        info = ncinfo(file,'dab3dtl');
        output.dab3dtl.description = ncreadatt(file,'dab3dtl','long_name');
        output.dab3dtl.unit = ncreadatt(file,'dab3dtl','units');
        output.dab3dtl.dimensions = {info.Dimensions.Name};

        output.dab3dtr.value = ncread(file,'dab3dtr');
        info = ncinfo(file,'dab3dtr');
        output.dab3dtr.description = ncreadatt(file,'dab3dtr','long_name');
        output.dab3dtr.unit = ncreadatt(file,'dab3dtr','units');
        output.dab3dtr.dimensions = {info.Dimensions.Name};
    end

    output.dmb3dl.value = ncread(file,'dmb3dl');
    info = ncinfo(file,'dmb3dl');
    output.dmb3dl.description = ncreadatt(file,'dmb3dl','long_name');
    output.dmb3dl.unit = ncreadatt(file,'dmb3dl','units');
    output.dmb3dl.dimensions = {info.Dimensions.Name};

    output.dmb3di.value = ncread(file,'dmb3di');
    info = ncinfo(file,'dmb3di');
    output.dmb3di.description = ncreadatt(file,'dmb3di','long_name');
    output.dmb3di.unit = ncreadatt(file,'dmb3di','units');
    output.dmb3di.dimensions = {info.Dimensions.Name};

    output.dmb3da.value = ncread(file,'dmb3da');
    info = ncinfo(file,'dmb3da');
    output.dmb3da.description = ncreadatt(file,'dmb3da','long_name');
    output.dmb3da.unit = ncreadatt(file,'dmb3da','units');
    output.dmb3da.dimensions = {info.Dimensions.Name};

    output.dmb3dr.value = ncread(file,'dmb3dr');
    info = ncinfo(file,'dmb3dr');
    output.dmb3dr.description = ncreadatt(file,'dmb3dr','long_name');
    output.dmb3dr.unit = ncreadatt(file,'dmb3dr','units');
    output.dmb3dr.dimensions = {info.Dimensions.Name};

    if contains(simulation.geometry_type,'double null') || contains(simulation.geometry_type,'snowflake')
        output.dmb3dtl.value = ncread(file,'dmb3dtl');
        info = ncinfo(file,'dmb3dtl');
        output.dmb3dtl.description = ncreadatt(file,'dmb3dtl','long_name');
        output.dmb3dtl.unit = ncreadatt(file,'dmb3dtl','units');
        output.dmb3dtl.dimensions = {info.Dimensions.Name};

        output.dmb3dtr.value = ncread(file,'dmb3dtr');
        info = ncinfo(file,'dmb3dtr');
        output.dmb3dtr.description = ncreadatt(file,'dmb3dtr','long_name');
        output.dmb3dtr.unit = ncreadatt(file,'dmb3dtr','units');
        output.dmb3dtr.dimensions = {info.Dimensions.Name};
    end

    output.tab3dl.value = ncread(file,'tab3dl').*6.2415e+18;
    info = ncinfo(file,'tab3dl');
    output.tab3dl.description = ncreadatt(file,'tab3dl','long_name');
    output.tab3dl.unit = ncreadatt(file,'tab3dl','units');
    output.tab3dl.dimensions = {info.Dimensions.Name};

    output.tab3di.value = ncread(file,'tab3di').*6.2415e+18;
    info = ncinfo(file,'tab3di');
    output.tab3di.description = ncreadatt(file,'tab3di','long_name');
    output.tab3di.unit = ncreadatt(file,'tab3di','units');
    output.tab3di.dimensions = {info.Dimensions.Name};

    output.tab3da.value = ncread(file,'tab3da').*6.2415e+18;
    info = ncinfo(file,'tab3da');
    output.tab3da.description = ncreadatt(file,'tab3da','long_name');
    output.tab3da.unit = ncreadatt(file,'tab3da','units');
    output.tab3da.dimensions = {info.Dimensions.Name};

    output.tab3dr.value = ncread(file,'tab3dr').*6.2415e+18;
    info = ncinfo(file,'tab3dr');
    output.tab3dr.description = ncreadatt(file,'tab3dr','long_name');
    output.tab3dr.unit = ncreadatt(file,'tab3dr','units');
    output.tab3dr.dimensions = {info.Dimensions.Name};

    if contains(simulation.geometry_type,'double null') || contains(simulation.geometry_type,'snowflake')
        output.tab3dtl.value = ncread(file,'tab3dtl');
        info = ncinfo(file,'tab3dtl');
        output.tab3dtl.description = ncreadatt(file,'tab3dtl','long_name');
        output.tab3dtl.unit = ncreadatt(file,'tab3dtl','units');
        output.tab3dtl.dimensions = {info.Dimensions.Name};

        output.tab3dtr.value = ncread(file,'tab3dtr');
        info = ncinfo(file,'tab3dtr');
        output.tab3dtr.description = ncreadatt(file,'tab3dtr','long_name');
        output.tab3dtr.unit = ncreadatt(file,'tab3dtr','units');
        output.tab3dtr.dimensions = {info.Dimensions.Name};
    end

    output.tmb3dl.value = ncread(file,'tmb3dl').*6.2415e+18;
    info = ncinfo(file,'tmb3dl');
    output.tmb3dl.description = ncreadatt(file,'tmb3dl','long_name');
    output.tmb3dl.unit = ncreadatt(file,'tmb3dl','units');
    output.tmb3dl.dimensions = {info.Dimensions.Name};

    output.tmb3di.value = ncread(file,'tmb3di').*6.2415e+18;
    info = ncinfo(file,'tmb3di');
    output.tmb3di.description = ncreadatt(file,'tmb3di','long_name');
    output.tmb3di.unit = ncreadatt(file,'tmb3di','units');
    output.tmb3di.dimensions = {info.Dimensions.Name};

    output.tmb3da.value = ncread(file,'tmb3da').*6.2415e+18;
    info = ncinfo(file,'tmb3da');
    output.tmb3da.description = ncreadatt(file,'tmb3da','long_name');
    output.tmb3da.unit = ncreadatt(file,'tmb3da','units');
    output.tmb3da.dimensions = {info.Dimensions.Name};

    output.tmb3dr.value = ncread(file,'tmb3dr').*6.2415e+18;
    info = ncinfo(file,'tmb3dr');
    output.tmb3dr.description = ncreadatt(file,'tmb3dr','long_name');
    output.tmb3dr.unit = ncreadatt(file,'tmb3dr','units');
    output.tmb3dr.dimensions = {info.Dimensions.Name};

    if contains(simulation.geometry_type,'double null') || contains(simulation.geometry_type,'snowflake')
        output.tmb3dtl.value = ncread(file,'tmb3dtl');
        info = ncinfo(file,'tmb3dtl');
        output.tmb3dtl.description = ncreadatt(file,'tmb3dtl','long_name');
        output.tmb3dtl.unit = ncreadatt(file,'tmb3dtl','units');
        output.tmb3dtl.dimensions = {info.Dimensions.Name};

        output.tmb3dtr.value = ncread(file,'tmb3dtr');
        info = ncinfo(file,'tmb3dtr');
        output.tmb3dtr.description = ncreadatt(file,'tmb3dtr','long_name');
        output.tmb3dtr.unit = ncreadatt(file,'tmb3dtr','units');
        output.tmb3dtr.dimensions = {info.Dimensions.Name};
    end

    catch
    end

    output.dn3di.value = ncread(file,'dn3di');
    info = ncinfo(file,'dn3di');
    output.dn3di.description = ncreadatt(file,'dn3di','long_name');
    output.dn3di.unit = ncreadatt(file,'dn3di','units');
    output.dn3di.dimensions = {info.Dimensions.Name};

    output.dn3da.value = ncread(file,'dn3da');
    info = ncinfo(file,'dn3da');
    output.dn3da.description = ncreadatt(file,'dn3da','long_name');
    output.dn3da.unit = ncreadatt(file,'dn3da','units');
    output.dn3da.dimensions = {info.Dimensions.Name};

    output.dp3di.value = ncread(file,'dp3di');
    info = ncinfo(file,'dp3di');
    output.dp3di.description = ncreadatt(file,'dp3di','long_name');
    output.dp3di.unit = ncreadatt(file,'dp3di','units');
    output.dp3di.dimensions = {info.Dimensions.Name};

    output.dp3da.value = ncread(file,'dp3da');
    info = ncinfo(file,'dp3da');
    output.dp3da.description = ncreadatt(file,'dp3da','long_name');
    output.dp3da.unit = ncreadatt(file,'dp3da','units');
    output.dp3da.dimensions = {info.Dimensions.Name};

    output.ke3di.value = ncread(file,'ke3di');
    info = ncinfo(file,'ke3di');
    output.ke3di.description = ncreadatt(file,'ke3di','long_name');
    output.ke3di.unit = ncreadatt(file,'ke3di','units');
    output.ke3di.dimensions = {info.Dimensions.Name};

    output.ke3da.value = ncread(file,'ke3da');
    info = ncinfo(file,'ke3da');
    output.ke3da.description = ncreadatt(file,'ke3da','long_name');
    output.ke3da.unit = ncreadatt(file,'ke3da','units');
    output.ke3da.dimensions = {info.Dimensions.Name};

    output.ki3di.value = ncread(file,'ki3di');
    info = ncinfo(file,'ki3di');
    output.ki3di.description = ncreadatt(file,'ki3di','long_name');
    output.ki3di.unit = ncreadatt(file,'ki3di','units');
    output.ki3di.dimensions = {info.Dimensions.Name};

    output.ki3da.value = ncread(file,'ki3da');
    info = ncinfo(file,'ki3da');
    output.ki3da.description = ncreadatt(file,'ki3da','long_name');
    output.ki3da.unit = ncreadatt(file,'ki3da','units');
    output.ki3da.dimensions = {info.Dimensions.Name};

    output.vx3di.value = ncread(file,'vx3di');
    info = ncinfo(file,'vx3di');
    output.vx3di.description = ncreadatt(file,'vx3di','long_name');
    output.vx3di.unit = ncreadatt(file,'vx3di','units');
    output.vx3di.dimensions = {info.Dimensions.Name};

    output.vx3da.value = ncread(file,'vx3da');
    info = ncinfo(file,'vx3da');
    output.vx3da.description = ncreadatt(file,'vx3da','long_name');
    output.vx3da.unit = ncreadatt(file,'vx3da','units');
    output.vx3da.dimensions = {info.Dimensions.Name};

    output.vy3di.value = ncread(file,'vy3di');
    info = ncinfo(file,'vy3di');
    output.vy3di.description = ncreadatt(file,'vy3di','long_name');
    output.vy3di.unit = ncreadatt(file,'vy3di','units');
    output.vy3di.dimensions = {info.Dimensions.Name};

    output.vy3da.value = ncread(file,'vy3da');
    info = ncinfo(file,'vy3da');
    output.vy3da.description = ncreadatt(file,'vy3da','long_name');
    output.vy3da.unit = ncreadatt(file,'vy3da','units');
    output.vy3da.dimensions = {info.Dimensions.Name};

    output.vs3di.value = ncread(file,'vs3di');
    info = ncinfo(file,'vs3di');
    output.vs3di.description = ncreadatt(file,'vs3di','long_name');
    output.vs3di.unit = ncreadatt(file,'vs3di','units');
    output.vs3di.dimensions = {info.Dimensions.Name};

    output.vs3da.value = ncread(file,'vs3da');
    info = ncinfo(file,'vs3da');
    output.vs3da.description = ncreadatt(file,'vs3da','long_name');
    output.vs3da.unit = ncreadatt(file,'vs3da','units');
    output.vs3da.dimensions = {info.Dimensions.Name};

    fprintf('Profiles from b2time.nc read\n');

end

fclose(fid);

end
