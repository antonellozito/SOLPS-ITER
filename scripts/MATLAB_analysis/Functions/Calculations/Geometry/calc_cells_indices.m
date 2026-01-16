function [index_vol,index_face] = calc_cells_indices(geometry,coordinate_type,special_region,region,cell_index)

if not(isunstructuredgrid(geometry))

    % Structured grid

    switch coordinate_type

        case 'radial'

            if special_region
                switch region
                    case 'inner_target'
                        index_vol = 1;
                    case 'inner_X_point'
                        index_vol = geometry.leftcut+2;
                    case 'inner_midplane'
                        index_vol = geometry.imp+2;
                    case 'top'
                        index_vol = geometry.leftcut+2+((geometry.rightcut+2)-(geometry.leftcut+2))/2;
                    case 'outer_midplane'
                        index_vol = geometry.omp+2;
                    case 'outer_X_point'
                        index_vol = geometry.rightcut+1;
                    case 'outer_target'
                        index_vol = geometry.nx;
                    otherwise
                        error(['Error: allowed special poloidal/parallel locations in calc_cells_indices are:\n' ...
                            '''inner_target'',''inner_X_point'',''inner_midplane'',''top'',' ...
                            '''outer_midplane'',''outer_X_point'',''outer_target'''])
                end
            else
                index_vol = cell_index;
            end

        case 'poloidal'

            if special_region
                switch region
                    case 'core_boundary'
                        error('Error: core boundary still to do in calc_cell_indices')
                    case 'separatrix'
                        index_vol = geometry.sep+2;
                    case 'wall_boundary'
                        error('Error: core boundary still to do in calc_cell_indices')
                    otherwise
                        error('Error: allowed special radial locations in calc_cells_indices are:\n''core_boundary '',''separatrix'',''wall_boundary''')
                end
            else
                index_vol = cell_index;
            end

        case 'parallel'

            if special_region
                switch region
                    case 'core_boundary'
                        error('Error: core boundary still to do in calc_cell_indices')
                    case 'separatrix'
                        index_vol = geometry.sep+2;
                    case 'wall_boundary'
                        error('Error: core boundary still to do in calc_cell_indices')
                    otherwise
                        error('Error: allowed special radial locations in calc_cells_indices are:\n''core_boundary '',''separatrix'',''wall_boundary''')
                end
            else
                index_vol = cell_index;
            end

    end

    index_face = index_vol;

else

    % Unstructured grid

    switch coordinate_type

        case 'radial'

            if special_region
                switch region
                    case 'inner_target'
                        index_vol = geometry.cvlistl;
                        index_face = geometry.fclistl;
                    case 'inner_X_point'
                        error('Error: Still to convert in calc_cells_indices')
                    case 'inner_midplane'
                        index_vol = geometry.cvlisti;
                        index_face = geometry.cvlisti;
                    case 'top'
                        error('Error: Still to convert in calc_cells_indices')
                    case 'outer_midplane'
                        index_vol = geometry.cvlista;
                        index_face = geometry.cvlista;
                    case 'outer_X_point'
                        error('Error: Still to convert in calc_cells_indices')
                    case 'outer_target'
                        index_vol = geometry.cvlistr;
                        index_face = geometry.fclistr;
                    otherwise
                        error(['Error: allowed special poloidal locations in calc_cells_indices are:\n' ...
                            '''inner_target'',''inner_X_point'',''inner_midplane'',''top'',' ...
                            '''outer_midplane'',''outer_X_point'',''outer_target'''])
                end
            else
                index_vol = cell_index;
                index_face = cell_index;
            end

        case 'poloidal'

            error('Error: Search of radial cells indices still to convert in calc_cells_indices for unstructured grids')

        case 'parallel'

            error('Error: Search of radial cells indices still to convert in calc_cells_indices for unstructured grids')

    end

end

end
