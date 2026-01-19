function write_b2fstate(file,state)
% write_b2fstate(file,label,state)
%
% Write b2fstati/b2fstate file for use by B2.5.
%
% Input argument verions is optional. If not specified, will use default
% version = 03.000.000.
% 
% Notes: 
%  - routine does not do any consistency checking on the data (size of
%    the fields in state, etc.)
%  - routine will overwrite existing data if 'file' exists
% 

[fid,msg] = fopen(file,'wt');
if (fid == -1)
   error(msg);
end

%% WRITE VERSION HEADER

% Set default value for version, if not supplied
if isfield(state,'version')
    version = state.version;
else
    version = '03.000.000';
end

VERSION = strcat('VERSION',version);
fprintf(fid,'%s 3.0.0-000-xxxxxxxxx             \n',VERSION);


%% WRITE DIMENSIONS

nx = size(state.na,1)-2;
ny = size(state.na,2)-2;
ns = size(state.na,3);

write_b2_int(fid,'nx,ny,ns                        ',[nx,ny,ns]);


%% WRITE LABEL

write_b2_string(fid,'label                           ','b2mn     B2.5 xxxxx/x SOLPS-ITER  yyyy-mm-dd  hh:mm user    converted with MATLAB                                       ');


%% WRITE FIELDS

% Charges and masses

write_b2_real(fid,'zamin                           ',state.zamin);
write_b2_real(fid,'zamax                           ',state.zamax);
write_b2_real(fid,'zn                              ',state.zn);
write_b2_real(fid,'am                              ',state.am);

% State variables

write_b2_real(fid,'na                              '    , state.na);
write_b2_real(fid,'ne                              '    , state.ne);
write_b2_real(fid,'ua                              '    , state.ua);
write_b2_real(fid,'uadia                           ' , state.uadia);
write_b2_real(fid,'te                              '    , state.te);
write_b2_real(fid,'ti                              '    , state.ti);
write_b2_real(fid,'po                              '    , state.po);

% Fluxes

write_b2_real(fid,'fna                             '   ,state.fna);
write_b2_real(fid,'fhe                             '   ,state.fhe);
write_b2_real(fid,'fhi                             '   ,state.fhi);
write_b2_real(fid,'fch                             '   ,state.fch);
write_b2_real(fid,'fch_32                          ',state.fch_32);
write_b2_real(fid,'fch_52                          ',state.fch_52);
write_b2_real(fid,'kinrgy                          ',state.kinrgy);
write_b2_real(fid,'time                            '  ,state.time);
write_b2_real(fid,'fch_p                           ' ,state.fch_p);

if str2num(strrep(version,'.','')) >= str2num(strrep('03.000.005','.',''))
    % Starting at version 03.000.005, a large number of additional fields
    % was added to remove restart effect for 5.2 model equations (BCs)
    write_b2_real(fid,'fna_mdf                         '    ,state.fna_mdf);
    write_b2_real(fid,'fhe_mdf                         '    ,state.fhe_mdf);
    write_b2_real(fid,'fhi_mdf                         '    ,state.fhi_mdf);
    write_b2_real(fid,'fna_fcor                        '   ,state.fna_fcor);
    write_b2_real(fid,'fna_nodrift                     ',state.fna_nodrift);
    write_b2_real(fid,'fna_he                          '     ,state.fna_he);
    write_b2_real(fid,'fnaPSch                         '    ,state.fnaPSch);
    write_b2_real(fid,'fhePSch                         '    ,state.fhePSch);
    write_b2_real(fid,'fhiPSch                         '    ,state.fhiPSch);
    write_b2_real(fid,'fna_eir                         '    ,state.fna_eir);
    write_b2_real(fid,'fne_eir                         '    ,state.fne_eir);
    write_b2_real(fid,'fhe_eir                         '    ,state.fhe_eir);
    write_b2_real(fid,'fhi_eir                         '    ,state.fhi_eir);
    write_b2_real(fid,'fna_32                          '     ,state.fna_32);
    write_b2_real(fid,'fna_52                          '     ,state.fna_52);
    write_b2_real(fid,'fni_32                          '     ,state.fni_32);
    write_b2_real(fid,'fni_52                          '     ,state.fni_52);
    write_b2_real(fid,'fne_32                          '     ,state.fne_32);
    write_b2_real(fid,'fne_52                          '     ,state.fne_52);
    write_b2_real(fid,'fchdia                          '     ,state.fchdia);
    write_b2_real(fid,'fchin                           '      ,state.fchin);
    write_b2_real(fid,'fchvispar                       '  ,state.fchvispar);
    write_b2_real(fid,'fchvisper                       '  ,state.fchvisper);
    write_b2_real(fid,'fchvisq                         '    ,state.fchvisq);
    write_b2_real(fid,'fchinert                        '   ,state.fchinert);
    
    write_b2_real(fid,'vaecrb                          ' ,state.vaecrb);
    write_b2_real(fid,'vadia                           '  ,state.vadia);
    write_b2_real(fid,'wadia                           '  ,state.wadia);
    write_b2_real(fid,'veecrb                          ' ,state.veecrb);
    write_b2_real(fid,'vedia                           '  ,state.vedia);
    
    write_b2_real(fid,'floe_noc                        ' ,state.floe_noc);
    write_b2_real(fid,'floi_noc                        ' ,state.floi_noc);
end

%% CLOSE FILE

fclose(fid);

end
