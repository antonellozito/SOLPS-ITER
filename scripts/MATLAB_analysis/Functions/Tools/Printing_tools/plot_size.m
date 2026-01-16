function [xlim,ylim,orientation,length,height] = plot_size(device,region)

% device: 'aug', 'cmod', 'd3d', 'east', 'iter', 'jet', 'mastu', 'sparc', 'tcv'

if strcmp(device,'aug')

    switch region

        case 'full'
            xlim = [0.8 2.65];
            ylim = [-1.4 1.4];
            orientation = 'portrait';
            length = 600;
            height = 800;

        case 'midplane'
            xlim = [1.45 2.4];
            ylim = [-0.3 0.4];
            orientation = 'landscape';
            length = 800;
            height = 600;

        case 'lower_divertor'
            xlim = [1.15 1.8];
            ylim = [-1.2 -0.7];
            orientation = 'landscape';
            length = 800;
            height = 600;

        case 'lower_subdivertor'
            xlim = [0.95 2.3];
            ylim = [-1.35 -0.5];
            orientation = 'landscape';
            length = 800;
            height = 600;

        case 'upper_divertor'
            xlim = [1.1 1.75];
            ylim = [0.7 1.2];
            orientation = 'landscape';
            length = 800;
            height = 600;

        case 'upper_subdivertor'
            xlim = [0.95 2.3];
            ylim = [0.5 1.35];
            orientation = 'landscape';
            length = 800;
            height = 600;

        otherwise
            xlim = [0.8 2.65];
            ylim = [-1.4 1.4];
            orientation = 'portrait';
            length = 600;
            height = 800;

    end

elseif strcmp(device,'cmod')

    switch region

        case 'full'
            xlim = [0.4 0.95];
            ylim = [-0.6 0.6];
            orientation = 'portrait';
            length = 600;
            height = 800;

        case 'midplane'
            xlim = [0.65 0.95];
            ylim = [-0.15 0.15];
            orientation = 'landscape';
            length = 800;
            height = 600;

        case 'lower_divertor'
            xlim = [0.4 0.75];
            ylim = [-0.6 -0.3];
            orientation = 'landscape';
            length = 800;
            height = 600;

        case 'lower_subdivertor'
            xlim = [0.4 0.9];
            ylim = [-0.6 -0.25];
            orientation = 'landscape';
            length = 800;
            height = 600;

        case 'upper_divertor'
            xlim = [0.4 0.75];
            ylim = [0.3 0.6];
            orientation = 'landscape';
            length = 800;
            height = 600;

        case 'upper_subdivertor'
            xlim = [0.4 0.9];
            ylim = [0.25 0.6];
            orientation = 'landscape';
            length = 800;
            height = 600;

        otherwise
            xlim = [0.4 0.95];
            ylim = [-0.6 0.6];
            orientation = 'portrait';
            length = 600;
            height = 800;

    end

elseif strcmp(device,'d3d')

    switch region

        case 'full'
            xlim = [0.9 2.5];
            ylim = [-1.4 1.4];
            orientation = 'portrait';
            length = 600;
            height = 800;

        case 'midplane'
            xlim = [2.0 2.4];
            ylim = [-0.3 0.3];
            orientation = 'landscape';
            length = 800;
            height = 600;

        case 'lower_divertor'
            xlim = [1.0 1.6];
            ylim = [-1.4 -1.0];
            orientation = 'landscape';
            length = 800;
            height = 600;

        case 'lower_subdivertor'
            xlim = [1.0 2.2];
            ylim = [-1.4 -0.8];
            orientation = 'landscape';
            length = 800;
            height = 600;

        case 'upper_divertor'
            xlim = [1.0 1.4];
            ylim = [0.9 1.4];
            orientation = 'landscape';
            length = 800;
            height = 600;

        case 'upper_subdivertor'
            xlim = [1.0 2.0];
            ylim = [0.7 1.4];
            orientation = 'landscape';
            length = 800;
            height = 600;

        otherwise
            xlim = [0.9 2.5];
            ylim = [-1.4 1.4];
            orientation = 'portrait';
            length = 600;
            height = 800;

    end

elseif strcmp(device,'east')

    switch region

        case 'full'
            xlim = [1.1 2.8];
            ylim = [-1.3 1.3];
            orientation = 'portrait';
            length = 600;
            height = 800;

        case 'midplane'
            xlim = [1.9 2.5];
            ylim = [-0.3 0.3];
            orientation = 'landscape';
            length = 800;
            height = 600;

        case 'lower_divertor'
            xlim = [1.3 1.9];
            ylim = [-1.2 -0.6];
            orientation = 'landscape';
            length = 800;
            height = 600;

        case 'lower_subdivertor'
            xlim = [1.1 2.7];
            ylim = [-1.3 -0.4];
            orientation = 'landscape';
            length = 800;
            height = 600;

        case 'upper_divertor'
            xlim = [1.3 1.9];
            ylim = [0.6 1.2];
            orientation = 'landscape';
            length = 800;
            height = 600;

        case 'upper_subdivertor'
            xlim = [1.1 2.7];
            ylim = [0.4 1.3];
            orientation = 'landscape';
            length = 800;
            height = 600;

        otherwise
            xlim = [1.1 2.8];
            ylim = [-1.3 1.3];
            orientation = 'portrait';
            length = 600;
            height = 800;

    end

elseif strcmp(device,'iter')

    switch region

        case 'full'
            xlim = [3.5,10.0];
            ylim = [-5.3,5.3];
            orientation = 'portrait';
            length = 600;
            height = 800;

        case 'midplane'
            xlim = [6.0,9.0];
            ylim = [-0.5 1.5];
            orientation = 'landscape';
            length = 800;
            height = 600;

        case 'lower_divertor'
            xlim = [4.0,6.2];
            ylim = [-4.6,-2.8];
            orientation = 'landscape';
            length = 800;
            height = 600;

        case 'lower_subdivertor'
            xlim = [3.5,8.0];
            ylim = [-5.3,-2.2];
            orientation = 'landscape';
            length = 800;
            height = 600;

        case 'upper_divertor'
            xlim = [4.0,6.2];
            ylim = [2.8,4.6];
            orientation = 'landscape';
            length = 800;
            height = 600;

        case 'upper_subdivertor'
            xlim = [3.5,8.0];
            ylim = [2.2,5.3];
            orientation = 'landscape';
            length = 800;
            height = 600;

        otherwise
            xlim = [3.5,10.0];
            ylim = [-5.3,5.3];
            orientation = 'portrait';
            length = 600;
            height = 800;

    end

elseif strcmp(device,'jet')

    switch region

        case 'full'
            xlim = [1.6 4.0];
            ylim = [-2.7 2.7];
            orientation = 'portrait';
            length = 600;
            height = 800;

        case 'midplane'
            xlim = [3.4 4.0];
            ylim = [-0.1 0.7];
            orientation = 'landscape';
            length = 800;
            height = 600;

        case 'lower_divertor'
            xlim = [2.3 3.0];
            ylim = [-1.7 -1.1];
            orientation = 'landscape';
            length = 800;
            height = 600;

        case 'lower_subdivertor'
            xlim = [2.0 3.7];
            ylim = [-2.7 -0.7];
            orientation = 'landscape';
            length = 800;
            height = 600;

        case 'upper_divertor'
            xlim = [2.3 3.0];
            ylim = [1.4 2.0];
            orientation = 'landscape';
            length = 800;
            height = 600;

        case 'upper_subdivertor'
            xlim = [2.0 3.7];
            ylim = [0.7 2.7];
            orientation = 'landscape';
            length = 800;
            height = 600;

        otherwise
            xlim = [1.6 4.0];
            ylim = [-2.7 2.7];
            orientation = 'portrait';
            length = 600;
            height = 800;

    end

elseif strcmp(device,'mastu')

    switch region

        case 'full'
            xlim = [0.2 2.0];
            ylim = [-2.2 2.2];
            orientation = 'portrait';
            length = 600;
            height = 800;

        case 'midplane'
            xlim = [1.1 1.5];
            ylim = [-0.3 0.3];
            orientation = 'landscape';
            length = 800;
            height = 600;

        case 'lower_divertor'
            xlim = [0.3 1.1];
            ylim = [-1.8 -1.1];
            orientation = 'landscape';
            length = 800;
            height = 600;

        case 'lower_subdivertor'
            xlim = [0.3 1.9];
            ylim = [-2.1 -0.9];
            orientation = 'landscape';
            length = 800;
            height = 600;

        case 'upper_divertor'
            xlim = [0.3 1.1];
            ylim = [1.1 1.8];
            orientation = 'landscape';
            length = 800;
            height = 600;

        case 'upper_subdivertor'
            xlim = [0.3 1.9];
            ylim = [0.9 2.1];
            orientation = 'landscape';
            length = 800;
            height = 600;

        otherwise
            xlim = [0.2 2.0];
            ylim = [-2.2 2.2];
            orientation = 'portrait';
            length = 600;
            height = 800;

    end

elseif strcmp(device,'sparc')

    switch region

        case 'full'
            xlim = [1.3 2.5];
            ylim = [-1.7 1.7];
            orientation = 'portrait';
            length = 600;
            height = 800;

        case 'midplane'
            xlim = [2.2 2.5];
            ylim = [-0.4 0.4];
            orientation = 'landscape';
            length = 800;
            height = 600;

        case 'lower_divertor'
            xlim = [1.3 1.8];
            ylim = [-1.6 -0.9];
            orientation = 'landscape';
            length = 800;
            height = 600;

        case 'lower_subdivertor'
            xlim = [1.3 2.3];
            ylim = [-1.7 -0.8];
            orientation = 'landscape';
            length = 800;
            height = 600;

        case 'upper_divertor'
            xlim = [1.3 1.8];
            ylim = [0.9 1.6];
            orientation = 'landscape';
            length = 800;
            height = 600;

        case 'upper_subdivertor'
            xlim = [1.3 2.3];
            ylim = [0.8 1.7];
            orientation = 'landscape';
            length = 800;
            height = 600;

        otherwise
            xlim = [1.3 2.5];
            ylim = [-1.7 1.7];
            orientation = 'portrait';
            length = 600;
            height = 800;

    end

elseif strcmp(device,'tcv')

    switch region

        case 'full'
            xlim = [0.6 1.2];
            ylim = [-0.8 0.8];
            orientation = 'portrait';
            length = 600;
            height = 800;

        case 'midplane'
            xlim = [0.9 1.2];
            ylim = [-0.2 0.1];
            orientation = 'landscape';
            length = 800;
            height = 600;

        case 'lower_divertor'
            xlim = [0.6 1.2];
            ylim = [-0.8 -0.2];
            orientation = 'landscape';
            length = 800;
            height = 600;

        case 'lower_subdivertor'
            xlim = [0.6 1.2];
            ylim = [-0.8 -0.2];
            orientation = 'landscape';
            length = 800;
            height = 600;

        case 'upper_divertor'
            xlim = [0.6 1.2];
            ylim = [0.2 0.8];
            orientation = 'landscape';
            length = 800;
            height = 600;

        case 'upper_subdivertor'
            xlim = [0.6 1.2];
            ylim = [0.2 0.8];
            orientation = 'landscape';
            length = 800;
            height = 600;

        otherwise
            xlim = [0.6 1.2];
            ylim = [-0.8 0.8];
            orientation = 'portrait';
            length = 600;
            height = 800;

    end

else

    xlim = 'auto';
    ylim = 'auto';
    orientation = 'portrait';
    length = 600;
    height = 800;

end

end
