function write_b2frates(file,rates)

[fid,msg] = fopen(file,'wt');
if (fid == -1)
   error(msg);
end

%% WRITE FIELDS

% Charges and masses

write_b2_real(fid,'rtzmin                          ',rates.zamin);
write_b2_real(fid,'rtzmax                          ',rates.zamax);
write_b2_real(fid,'rtzn                            ',rates.zn);
write_b2_real(fid,'rtt                             ',rates.rtt);
write_b2_real(fid,'rtn                             ',rates.rtn);
write_b2_real(fid,'rtlt                            ',rates.rtlt);
write_b2_real(fid,'rtln                            ',rates.rtln);
write_b2_real(fid,'rtlsa                           ',rates.rtlsa);
write_b2_real(fid,'rtlra                           ',rates.rtlra);
write_b2_real(fid,'rtlqa                           ',rates.rtlqa);
write_b2_real(fid,'rtlcx                           ',rates.rtlcx);
write_b2_real(fid,'rtlrd                           ',rates.rtlrd);
write_b2_real(fid,'rtlbr                           ',rates.rtlbr);
write_b2_real(fid,'rtlza                           ',rates.rtlza);
write_b2_real(fid,'rtlz2                           ',rates.rtlz2);
write_b2_real(fid,'rtlpt                           ',rates.rtlpt);
write_b2_real(fid,'rtlpi                           ',rates.rtlpi);

%% CLOSE FILE

fclose(fid);

end
