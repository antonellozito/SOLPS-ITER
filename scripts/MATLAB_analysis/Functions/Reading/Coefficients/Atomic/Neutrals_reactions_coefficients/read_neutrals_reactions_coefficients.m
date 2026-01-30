function [info,coeff] = read_neutrals_reactions_coefficients(SIMULATION,database,reaction,n,T,E)
%
% read_neutrals_reactions_coefficients reads the neutrals reaction rates from the
% AMJUEL and HYDHEL databases.
% Output is a struct "info" containing informations about the reaction,
% and a "coeff" vector corresponding to the input [n;T;E] array
%
% Input arguments:
%
% - simulation : main simulation structure
% - database : database to be read ('AMJUEL', 'HYDHEL' or 'AMMONX')
% - reaction : code identifier of the desired reaction, in the form 'x_y.z.w'
% - n       : array of densities in m^-3
% - T       : array of temperatures in eV
% - E       : neutral energy in eV (optional, only for CX reactions)
%

% Find the EIRENE database folder
EIRENE_database = SIMULATION.EIRENE_DATABASE;

% Load the AMJUEL, HYDHEL and AMMONX datafiles
amjuel_datafile = sprintf('%s/AMdata/amjuel.tex',EIRENE_database);
if ~isfile(amjuel_datafile)
    error('Error: The amjuel.tex datafile does not exist');
end

hydhel_datafile = sprintf('%s/AMdata/hydhel.tex',EIRENE_database);
if ~isfile(hydhel_datafile)
    error('Error: The hydhel.tex datafile does not exist');
end

ammonx_datafile = sprintf('%s/AMdata/AMMONX_Arrh-elast.tex',EIRENE_database);
if ~isfile(ammonx_datafile)
    error('Error: The AMMONX_Arrh-elast.tex datafile does not exist');
end

% Load the desired database and compute coefficients
switch database

    case 'AMJUEL'
        % Parse database
        db = read_amjuel(amjuel_datafile);
        fprintf('amjuel.tex datafile read\n');
        
        % Compute coefficients
        if ~exist('E','var') || isempty(E)
            coeff = calc_coeff(db, reaction, n, T, [], database);
        else
            coeff = calc_coeff(db, reaction, n, T, E, database);
        end

    case 'HYDHEL'
        % Parse database
        db = read_hydhel(hydhel_datafile);
        fprintf('hydhel.tex datafile read\n');
        
        % Compute coefficients
        if ~exist('E','var') || isempty(E)
            coeff = calc_coeff(db, reaction, n, T, [], database);
        else
            coeff = calc_coeff(db, reaction, n, T, E, database);
        end

    case 'AMMONX'
        % Parse database
        db = read_ammonx(ammonx_datafile);
        fprintf('AMMONX_Arrh-elast.tex datafile read\n');
        
        % Compute coefficients
        coeff = calc_coeff(db, reaction, n, T, [], database);

    otherwise
        error('Error: Unknown database: %s', database);
end

% Extract info about the reaction
rhn = sprintf('H_%s', strrep(strrep(reaction, '.', '_'), '-', '_'));
if ~isfield(db, rhn)
    error('Error: Reaction %s not found in database', rhn);
end

temp = db.(rhn);
info.name = sprintf('%s, H.%d_%s', temp.report, temp.header, temp.name);

switch temp.unit
    case 'm$^2$'
        info.type = 'cross section';
        info.unit = 'm^2';
    case 'm$^3$ s$^{-1}$'
        info.type = 'rate coefficient';
        info.unit = 'm^3 s^-1';
    case 'eV'
        info.type = 'energy source/sink coefficient';
        info.unit = 'eV';
    case 'm$^3$ eV s$^{-1}$'
        info.type = 'energy source/sink rate coefficient';
        info.unit = 'm^3 eV s^-1';
    case ''
        info.type = 'ratio';
        info.unit = '';
    otherwise
        info.type = 'unknown';
        info.unit = temp.unit;
end

info.reaction = strrep(temp.latex, '\rightarrow', '→');
info.parameters = temp.parameters;

end


function coeff = calc_coeff(database, reaction, n, T, E, report)
    % Evaluate reaction coefficients
    
    if strcmp(report,'AMJUEL') || strcmp(report,'HYDHEL')

        % Select reaction
        rhn = sprintf('H_%s', strrep(reaction, '.', '_'));
        
        if ~isfield(database, rhn)
            error('Error: Reaction %s not found in database', rhn);
        end
        
        jreaction = database.(rhn);
        c = jreaction.coefficients;
        params = jreaction.parameters;
        
        % Check required parameters
        if contains(params, 'n') && isempty(n)
            error('Error: You need to specify a density.');
        end
        if contains(params, 'T') && isempty(T)
            error('Error: You need to specify a temperature.');
        end
        if contains(params, 'E') && isempty(E)
            error('Error: You need to specify an energy.');
        end
        
        % Validity checks
        if contains(params, 'E')
            E = double(E);
            if isfield(jreaction, 'Emin') && ~isempty(jreaction.Emin)
                E(E < jreaction.Emin) = NaN;
            end
            if isfield(jreaction, 'Emax') && ~isempty(jreaction.Emax)
                E(E > jreaction.Emax) = NaN;
            end
        end
        
        if contains(params, 'T')
            T = double(T);
            if isfield(jreaction, 'Tmin') && ~isempty(jreaction.Tmin)
                T(T < jreaction.Tmin) = NaN;
            end
            if isfield(jreaction, 'Tmax') && ~isempty(jreaction.Tmax)
                T(T > jreaction.Tmax) = NaN;
            end
        end
        
        if contains(params, 'n')
            n = double(n);
            if isfield(jreaction, 'nmin') && ~isempty(jreaction.nmin)
                n(n < jreaction.nmin) = NaN;
            end
            if isfield(jreaction, 'nmax') && ~isempty(jreaction.nmax)
                n(n > jreaction.nmax) = NaN;
            end
        end
        
        % Single-polynomial fits
        if length(strfind(params, ',')) == 0
            if strcmp(params, 'E')
                logx = log(E);
            elseif strcmp(params, 'T')
                logx = log(T);
            else
                error('Error: Parameter dependence not implemented.');
            end
            
            f = logx * 0.0;
            for i = 0:8
                f = f + c(i+1) * logx.^i;
            end
            
            if isfield(jreaction, 'Arrhenius_coefficient') && ~isempty(jreaction.Arrhenius_coefficient)
                f = f - jreaction.Arrhenius_coefficient ./ T;
            end
            
            coeff = exp(f) * jreaction.factor;
            
        % Double-polynomial fits
        elseif length(strfind(params, ',')) == 1
            if strcmp(params, 'E,T')
                logx = log(E);
                logy = log(T);
            elseif strcmp(params, 'n,T')
                logx = log(n * jreaction.factor_n);
                logy = log(T);
            else
                error('Error: Parameter combination not implemented.');
            end
            
            f = logx * 0.0;
            for ix = 0:8
                fy = logy * 0.0;
                for iy = 0:8
                    fy = fy + c(iy+1, ix+1) * logy.^iy;
                end
                f = f + fy .* logx.^ix;
            end
            
            coeff = exp(f) * jreaction.factor;
        else
            error('Error: Only single- or double-polynomial fits are implemented.');
        end

    elseif strcmp(report,'AMMONX')

        % Select reaction
        rhn = sprintf('H_%s', strrep(strrep(reaction, '.', '_'), '-', '_'));
        
        if ~isfield(database, rhn)
            error('Error: Reaction %s not found in database', rhn);
        end
        
        jreaction = database.(rhn);
        c = jreaction.coefficients;
        params = jreaction.parameters;
        
        % Check required parameters
        if contains(params, 'T') && isempty(T)
            error('Error: You need to specify a temperature.');
        end
        
        % Validity checks
        if contains(params, 'T')
            T = double(T);
            if isfield(jreaction, 'Tmin') && ~isempty(jreaction.Tmin)
                T(T < jreaction.Tmin) = NaN;
            end
            if isfield(jreaction, 'Tmax') && ~isempty(jreaction.Tmax)
                T(T > jreaction.Tmax) = NaN;
            end
        end
        
        % Single-polynomial fit (AMMONX only has T-dependent reactions)
        if strcmp(params, 'T')
            logx = log(T);
            
            f = logx * 0.0;
            for i = 0:8
                f = f + c(i+1) * logx.^i;
            end
            
            if isfield(jreaction, 'Arrhenius_coefficient') && ~isempty(jreaction.Arrhenius_coefficient)
                f = f - jreaction.Arrhenius_coefficient ./ T;
            end
            
            coeff = exp(f) * jreaction.factor;
        else
            error('Error: Parameter dependence not implemented for AMMONX.');
        end

    end

end
