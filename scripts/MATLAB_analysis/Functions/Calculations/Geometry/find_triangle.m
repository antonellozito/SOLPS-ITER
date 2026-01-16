function triangle_index = find_triangle(tri,R,z)

% Calculate the centroids of each triangle
numTriangles = size(tri.cells, 1);
centroids = zeros(numTriangles, 2);

for i = 1:numTriangles
    % Get the node indices for the i-th triangle
    nodeIndices = tri.cells(i, :);
    
    % Get the coordinates of the nodes
    x_coords = tri.nodes(nodeIndices, 1);
    y_coords = tri.nodes(nodeIndices, 2);
    
    % Calculate the centroid (center of mass) of the triangle
    centroids(i, 1) = mean(x_coords);
    centroids(i, 2) = mean(y_coords);
end

% Calculate the distances from the given point to each centroid
distances = sqrt((centroids(:, 1) - R).^2 + (centroids(:, 2) - z).^2);

% Find the index of the closest centroid
[~, triangle_index] = min(distances);

end
