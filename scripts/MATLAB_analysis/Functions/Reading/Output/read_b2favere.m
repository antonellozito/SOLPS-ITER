function avere = read_b2favere(simulation,nx,ny,ns)
%
% read_b2favere reads the final averaged plasma state file created by B2.5
% Output is a struct "avere" with all the data fields in the b2favere file
%
% 1st input: main simulation structure
%
% Following inputs: x-dimension, y-dimension, number of species

%% PRELIMINARY OPERATIONS

% Load the file and read the version

index = find(contains({simulation.run.name},'b2favere'));
if isempty(index)
   error('Error: b2favere not found');
end
fid = simulation.run(index).fid;
if (fid == -1)
   error('Error: b2favere not found');
end

line    = fgetl(fid);
version = line(8:17);

% Read some integers

avere.naver  = scan_b2_int(fid,'naver' ,1);
avere.ntotdt = scan_b2_int(fid,'ntotdt',1);

%% READ THE DATA

% State variables

avere.na  = scan_b2_real(fid,'na_mean'    ,[nx+2,ny+2,ns]);
avere.te  = scan_b2_real(fid,'te_mean'    ,[nx+2,ny+2]);
avere.ti  = scan_b2_real(fid,'ti_mean'    ,[nx+2,ny+2]);
avere.po  = scan_b2_real(fid,'po_mean'    ,[nx+2,ny+2]);
avere.ua  = scan_b2_real(fid,'ua_mean'    ,[nx+2,ny+2,ns]);

% Sources

avere.sna     = scan_b2_real(fid,'sna_mean'    ,[nx+2,ny+2,2,ns]);
avere.sne     = scan_b2_real(fid,'sne_mean'    ,[nx+2,ny+2,2]);
avere.she     = scan_b2_real(fid,'she_mean'    ,[nx+2,ny+2,4]);
avere.shi     = scan_b2_real(fid,'shi_mean'    ,[nx+2,ny+2,4]);
avere.sch     = scan_b2_real(fid,'sch_mean'    ,[nx+2,ny+2,4]);
avere.smo     = scan_b2_real(fid,'smo_mean'    ,[nx+2,ny+2,4,ns]);

fprintf('Structure AVERE from b2favere read.\n');

frewind(fid);

end