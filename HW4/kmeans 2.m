% COSI101A code example (by Pengyu Hong)
% Clustering analysis
%% load data
data = csvread( 'hw4.csv' );

num_points = size( data, 1 );
plot( data(:,1), data(:,2), '.' );

colors = {'.r', '.g', '.b', '.m', '.y', '.k' };
cmap = colormap( 'lines' );
numColor = size(cmap,1);

%% k-means
num_classes = 3;
disFunctions = {'sqEuclidean' };
disID = 1;
ind = kmeans( data, num_classes, 'distance', disFunctions{disID}) ;
subsets = [];

for m = 1 : num_classes
    subsets{m}.data = [];
end

for k = 1 : num_points
    for m = 1 : num_classes
        if ind(k) == m
            subsets{m}.data = [subsets{m}.data; data(k,:)];
        end
    end
end

figure;
for k = 1 : length( subsets )
    ind = mod( k, numColor );
    if ind == 0, ind = numColor; end
    plot( subsets{k}.data(:,1), subsets{k}.data(:,2), '.', 'Color', cmap(ind, :) ); 
    if k == 1
        hold;
    end
end

title( ['k-means: ', num2str(num_classes), ' clusters'] )


[idx,C] = kmeans( data, num_classes );
writematrix(C, 'hw4_results.csv' )