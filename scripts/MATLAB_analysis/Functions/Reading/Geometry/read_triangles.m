function triangles = read_triangles(simulation)
%
% read triangles is a wrapper routine to read all triangle data at once
% Output is a struct "triangles" containing nodes, cells, nghbr, side and cont as fiels of the triangular cells.
%
%% CREATE THE FIELDS

links = read_fort35(simulation);

try
    triangles.ixiy  = links.ixiy;
    triangles.nghbr = links.nghbr;
    triangles.side  = links.side;
    triangles.cont  = links.cont;
    triangles.nodes = read_fort33(simulation,0);
    triangles.cells = read_fort34(simulation);
catch
end
try
    triangles.plasma_cell = links.plasma_cell;
    triangles.nghbr = links.nghbr;
    triangles.side  = links.side;
    triangles.cont  = links.cont;
    triangles.nodes = read_fort33(simulation,1);
    triangles.cells = read_fort34(simulation);
catch
end

fprintf('Eirene triangles from fort.33, fort.34 and fort.35 read\n');

end