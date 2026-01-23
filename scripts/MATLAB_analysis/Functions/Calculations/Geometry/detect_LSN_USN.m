function SN_type = detect_LSN_USN(simulation)

try
    experiment_directory = regexprep(simulation.RUN_DIRECTORY, '/[^/]*$', '');
    NREG = strtrim(fileread(sprintf('%s/NREG',experiment_directory)));
    NREG = str2double(NREG);
catch
    [NREG,~,~] = find_nreg_species(simulation);
end

if NREG(1) == 4

    index_run = find(contains({simulation.run.name},'b2fgmtry'));
    index_baserun = find(contains({simulation.geometry.name},'b2fgmtry'));
    if isempty(index_run) && isempty (index_baserun)
       error('Error: b2fgmtry not found');
    end
    
    if not(isempty(index_run)) && strcmp(simulation.run(index_run).status,'read')
        index = index_run;
        fid = simulation.run(index).fid;
    elseif not(isempty(index_baserun)) && strcmp(simulation.geometry(index_baserun).status,'read')
        index = index_baserun;
        fid = simulation.geometry(index).fid;
    end
    
    if (fid == -1)
       error('Error: b2fgmtry not found');
    end
    
    line    = fgetl(fid);
    version = line(8:17);
    
    line    = fgetl(fid);
    if contains(line, 'nx,ny')
        version = 'structured';
    elseif contains(line, 'nCi,nCg,nCv,nFc,nVx,nFs,nFt')
        version = 'unstructured';
    end
    frewind(fid);

    if strcmp(version,'structured')
    
        dim = scan_b2_int(fid,'nx,ny',2);
        nx  = dim(1);
        ny  = dim(2);

        crx = scan_b2_real(fid,'crx',[nx+2,ny+2,4]);
        cry = scan_b2_real(fid,'cry',[nx+2,ny+2,4]);
        nncut = scan_b2_int(fid,'nncut',1); 
        leftcut = scan_b2_int(fid,'leftcut',nncut);
        topcut = scan_b2_int(fid,'topcut',nncut);

        frewind(fid);

        if ( cry(leftcut(1)+2, topcut(1)+1, 1) < ...
             cry(leftcut(1)+2, 1, 1) || ...
            (cry(leftcut(1)+2, topcut(1)+1, 1) == ...
             cry(leftcut(1)+2, 1, 1) && ...
             crx(leftcut(1)+2, topcut(1)+1, 1) < ...
             crx(leftcut(1)+2, 1, 1)) )

            SN_type = 'LSN';
        
        else

            SN_type = 'USN';

        end

    elseif strcmp(version,'unstructured')
    
        % TODO, assume LSN

        SN_type = 'LSN';

    end

else

    SN_type = 'none';

end

end