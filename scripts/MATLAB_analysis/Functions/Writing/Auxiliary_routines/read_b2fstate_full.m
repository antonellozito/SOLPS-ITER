function state = read_b2fstate_full(fid)
% state = read_b2fstate(file)
%
% Read b2fstati/b2fstate file created by B2.5.
%
% Output is a struct "state" with all the data fields in the b2fstate/i
% file (except for the dimensions nx,ny,ns, which are implicit in the array
% sizes).
%

%% Read dimensions nx, ny, ns

line    = fgetl(fid);
version = line(8:17);

state.version = version;

if str2num(strrep(version,'.','')) >= str2num(strrep('03.002.000','.',''))

    dim = scan_b2_int(fid,'nCv,nFc,ns',3);
    nCv  = dim(1);
    nFc  = dim(2);
    ns   = dim(3);
    
    statedim  = [nCv,1];
    statedims = [nCv,ns];
    
    fluxdim   = [nFc,2];
    fluxdimp  = [nFc,2];
    fluxdims  = [nFc,2,ns];

else

    dim = scan_b2_int(fid,'nx,ny,ns',3);
    nx  = dim(1);
    ny  = dim(2);
    ns  = dim(3);
   
    statedim  = [nx+2,ny+2];
    statedims = [nx+2,ny+2,ns];
    fluxdim  = [nx+2,ny+2,2];
    fluxdimp = [nx+2,ny+2];
    fluxdims = [nx+2,ny+2,2,ns];
    if version >= '03.001.000'
        fluxdim  = [nx+2,ny+2,2,2];
        fluxdimp = fluxdim;
        fluxdims = [nx+2,ny+2,2,2,ns];
    end

end

%% Read charges etc.

state.zamin = scan_b2_real(fid,'zamin',ns);
state.zamax = scan_b2_real(fid,'zamax',ns);
state.zn    = scan_b2_real(fid,'zn   ',ns);
state.am    = scan_b2_real(fid,'am   ',ns);


%% Read state variables

state.na     = scan_b2_real(fid,'na'    ,statedims);
state.ne     = scan_b2_real(fid,'ne'    ,statedim);
state.ua     = scan_b2_real(fid,'ua'    ,statedims);
state.uadia  = scan_b2_real(fid,'uadia' ,fluxdims);
state.te     = scan_b2_real(fid,'te'    ,statedim);
state.ti     = scan_b2_real(fid,'ti'    ,statedim);
state.po     = scan_b2_real(fid,'po'    ,statedim);


%% Read fluxes

state.fna    = scan_b2_real(fid,'fna'   ,fluxdims);
state.fhe    = scan_b2_real(fid,'fhe'   ,fluxdim);
state.fhi    = scan_b2_real(fid,'fhi'   ,fluxdim);
state.fch    = scan_b2_real(fid,'fch'   ,fluxdim);
state.fch_32 = scan_b2_real(fid,'fch_32',fluxdim);
state.fch_52 = scan_b2_real(fid,'fch_52',fluxdim);
state.kinrgy = scan_b2_real(fid,'kinrgy',statedims);
state.time   = scan_b2_real(fid,'time'  ,1);
state.fch_p  = scan_b2_real(fid,'fch_p' ,fluxdimp);

if str2num(strrep(version,'.','')) >= str2num(strrep('03.000.005','.',''))
    % Starting at version 03.000.005, a large number of additional fields
    % was added to remove restart effect for 5.2 model equations (BCs)
    state.fna_mdf     = scan_b2_real(fid,'fna_mdf'    ,fluxdims);
    state.fhe_mdf     = scan_b2_real(fid,'fhe_mdf'    ,fluxdim);
    state.fhi_mdf     = scan_b2_real(fid,'fhi_mdf'    ,fluxdim);
    state.fna_fcor    = scan_b2_real(fid,'fna_fcor'   ,fluxdims);
    state.fna_nodrift = scan_b2_real(fid,'fna_nodrift',fluxdims);
    state.fna_he      = scan_b2_real(fid,'fna_he'     ,fluxdims);
    state.fnaPSch     = scan_b2_real(fid,'fnaPSch'    ,fluxdims);
    state.fhePSch     = scan_b2_real(fid,'fhePSch'    ,fluxdim);
    state.fhiPSch     = scan_b2_real(fid,'fhiPSch'    ,fluxdim);
    state.fna_eir     = scan_b2_real(fid,'fna_eir'    ,fluxdims);
    state.fne_eir     = scan_b2_real(fid,'fne_eir'    ,fluxdim);
    state.fhe_eir     = scan_b2_real(fid,'fhe_eir'    ,fluxdim);
    state.fhi_eir     = scan_b2_real(fid,'fhi_eir'    ,fluxdim);
    state.fna_32      = scan_b2_real(fid,'fna_32'     ,fluxdims);
    state.fna_52      = scan_b2_real(fid,'fna_52'     ,fluxdims);
    state.fni_32      = scan_b2_real(fid,'fni_32'     ,fluxdim);
    state.fni_52      = scan_b2_real(fid,'fni_52'     ,fluxdim);
    state.fne_32      = scan_b2_real(fid,'fne_32'     ,fluxdim);
    state.fne_52      = scan_b2_real(fid,'fne_52'     ,fluxdim);
    state.fchdia      = scan_b2_real(fid,'fchdia'     ,fluxdim);
    state.fchin       = scan_b2_real(fid,'fchin'      ,fluxdim);
    state.fchvispar   = scan_b2_real(fid,'fchvispar'  ,fluxdim);
    state.fchvisper   = scan_b2_real(fid,'fchvisper'  ,fluxdim);
    state.fchvisq     = scan_b2_real(fid,'fchvisq'    ,fluxdim);
    state.fchinert    = scan_b2_real(fid,'fchinert'   ,fluxdim);
    
    state.vaecrb = scan_b2_real(fid,'vaecrb' ,fluxdims);
    state.vadia  = scan_b2_real(fid,'vadia'  ,fluxdims);
    state.wadia  = scan_b2_real(fid,'wadia'  ,fluxdims);
    state.veecrb = scan_b2_real(fid,'veecrb' ,fluxdim);
    state.vedia  = scan_b2_real(fid,'vedia'  ,fluxdim);
    
    state.floe_noc  = scan_b2_real(fid,'floe_noc' ,fluxdim);
    state.floi_noc  = scan_b2_real(fid,'floi_noc' ,fluxdim);
end

fprintf('Full plasma solution from b2fstate read\n');

%% Close file

fclose(fid);
