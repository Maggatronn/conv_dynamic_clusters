import json
import numpy as np
import hdbscan

# Load the UMAP data
with open('umapped_data.json', 'r') as f:
    data = json.load(f)

# Extract UMAP coordinates
umap_coords = np.array([[d['d0'], d['d1']] for d in data])

# Run HDBSCAN with parameters adjusted for ~7 clusters
clusterer = hdbscan.HDBSCAN(
    min_cluster_size=3,      # Smaller minimum cluster size
    min_samples=2,           # More lenient neighbor requirements
    cluster_selection_epsilon=0.25,  # More granular cluster separation
    cluster_selection_method='eom',  # 'eom' for more balanced clusters
    metric='euclidean',
    prediction_data=True
)

# Fit the clusterer
clusterer.fit(umap_coords)

# Add cluster assignments and probabilities to the data
for i, point in enumerate(data):
    point['cluster'] = int(clusterer.labels_[i])
    point['cluster_probability'] = float(clusterer.probabilities_[i])

# Save the results
with open('umapped_data.json', 'w') as f:
    json.dump(data, f, indent=2)

# Print clustering summary
unique_clusters = np.unique(clusterer.labels_)
print("\nClustering Summary:")
print(f"Number of clusters found: {len(unique_clusters[unique_clusters >= 0])}")
print(f"Number of noise points: {np.sum(clusterer.labels_ == -1)}")
print("\nPoints per cluster:")
for cluster in sorted(unique_clusters):
    if cluster == -1:
        print(f"Noise points: {np.sum(clusterer.labels_ == cluster)}")
    else:
        print(f"Cluster {cluster}: {np.sum(clusterer.labels_ == cluster)}") 