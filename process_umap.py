import json
import numpy as np
from sklearn.preprocessing import StandardScaler
import umap
import hdbscan
import json
import pandas as pd

# Read the input JSON file
with open('conv_chains_features.json', 'r') as f:
    data = json.load(f)

# Define numeric features to use (excluding turn_count_variance)
numeric_features = [
    'num_turns_in_conversation',
    'num_turns_facilitator',
    'num_observed_speakers',
    'avg_subst_responded_rate',
    'avg_mech_responded_rate',
    'avg_subst_responded_rate_nonself',
    'avg_subst_responded_rate_nonself_nonfac',
    'avg_subst_responded_rate_nonself_exclfac',
    'avg_subst_responded_rate_nonself_nonfac_exclfac',
    'gini_subst_responded_rate_nonself',
    'gini_subst_responded_rate_nonself_nonfac',
    'gini_subst_responded_rate_nonself_exclfac',
    'gini_subst_responded_rate_nonself_nonfac_exclfac',
    'total_turns_in_conversation',
    'total_speaking_time_seconds',
    'facilitator_speaking_percentage',
    'facilitator_turns_percentage',
    'speaking_time_gini_coefficient',
    'turn_distribution_gini_coefficient',
    'non_facilitator_speaking_gini_coefficient',
    'non_facilitator_turn_gini_coefficient',
    'turn_sequence_entropy',
    'substantive_responsivity_entropy'
]

# Extract features
X = np.array([[conv[feature] for feature in numeric_features] for conv in data])

# Scale the features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# UMAP parameters
RANDOM_STATE = 100  # Change this value to get different embeddings
N_NEIGHBORS = 15   # Number of neighbors to consider (default is 15)
MIN_DIST = 0.1    # Minimum distance between points in the embedding (default is 0.1)

# Apply UMAP with explicit parameters
reducer = umap.UMAP(
    random_state=RANDOM_STATE,
    n_neighbors=N_NEIGHBORS,
    min_dist=MIN_DIST,
    metric='euclidean'
)

print(f"Running UMAP with random_state={RANDOM_STATE}, n_neighbors={N_NEIGHBORS}, min_dist={MIN_DIST}")
embedding = reducer.fit_transform(X_scaled)

# Apply HDBSCAN clustering
clusterer = hdbscan.HDBSCAN(
    min_cluster_size=5,  # Minimum size of clusters
    min_samples=3,       # Number of samples in neighborhood for core points
    metric='euclidean'
)
cluster_labels = clusterer.fit_predict(embedding)

# Add UMAP coordinates and cluster labels to the data
for i, conv in enumerate(data):
    conv['umap_x'] = float(embedding[i, 0])
    conv['umap_y'] = float(embedding[i, 1])
    conv['cluster'] = int(cluster_labels[i])  # -1 represents noise points

# Calculate cluster probabilities
probabilities = clusterer.probabilities_

# Add cluster probabilities to data
for i, conv in enumerate(data):
    if conv['cluster'] != -1:  # Only add probability for points assigned to a cluster
        conv['cluster_probability'] = float(probabilities[i])
    else:
        conv['cluster_probability'] = 0.0

# Add metadata about the UMAP and HDBSCAN parameters
metadata = {
    "umap_parameters": {
        "random_state": RANDOM_STATE,
        "n_neighbors": N_NEIGHBORS,
        "min_dist": MIN_DIST
    },
    "hdbscan_parameters": {
        "min_cluster_size": 5,
        "min_samples": 3,
        "metric": "euclidean"
    },
    "num_clusters": int(max(cluster_labels) + 1),
    "noise_points": int(np.sum(cluster_labels == -1))
}

print(f"Found {metadata['num_clusters']} clusters and {metadata['noise_points']} noise points")

# Save the processed data
with open('umapped_data.json', 'w') as f:
    json.dump(data, f)

# Create JavaScript file with the data
js_code = f"""// Load and process the data
const data = {json.dumps(data, indent=2)};
const umap_params = {json.dumps(metadata, indent=2)};

// Set up the dimensions
const width = 1000;
const height = 600;
const margin = {{ top: 40, right: 40, bottom: 40, left: 40 }};

// Create the SVG container
const svg = d3.select("#visualization")
    .append("svg")
    .attr("width", width)
    .attr("height", height);

// Create tooltip
const tooltip = d3.select("body")
    .append("div")
    .attr("class", "tooltip");

// Add UMAP parameters text
d3.select("#visualization")
    .append("div")
    .attr("class", "umap-params")
    .html(`<strong>UMAP Parameters:</strong> Random State: ${{umap_params.umap_parameters.random_state}}, 
           N Neighbors: ${{umap_params.umap_parameters.n_neighbors}}, 
           Min Dist: ${{umap_params.umap_parameters.min_dist}}`);

// Function to update the visualization
function updateVisualization(selectedFeature) {{
    // Clear previous visualization
    svg.selectAll("*").remove();

    // Create scales for x and y axes based on UMAP coordinates
    const xScale = d3.scaleLinear()
        .domain([d3.min(data, d => d.umap_x), d3.max(data, d => d.umap_x)])
        .range([margin.left, width - margin.right]);

    const yScale = d3.scaleLinear()
        .domain([d3.min(data, d => d.umap_y), d3.max(data, d => d.umap_y)])
        .range([height - margin.bottom, margin.top]);

    // Create color scale for the selected feature
    const colorScale = d3.scaleSequential()
        .domain([
            d3.min(data, d => d[selectedFeature]),
            d3.max(data, d => d[selectedFeature])
        ])
        .interpolator(d3.interpolateViridis);

    // Add axes
    const xAxis = d3.axisBottom(xScale);
    const yAxis = d3.axisLeft(yScale);

    svg.append("g")
        .attr("transform", `translate(0,${{height - margin.bottom}})`)
        .call(xAxis);

    svg.append("g")
        .attr("transform", `translate(${{margin.left}},0)`)
        .call(yAxis);

    // Add axis labels
    svg.append("text")
        .attr("x", width / 2)
        .attr("y", height - 5)
        .attr("text-anchor", "middle")
        .text("UMAP Dimension 1");

    svg.append("text")
        .attr("transform", "rotate(-90)")
        .attr("x", -height / 2)
        .attr("y", 15)
        .attr("text-anchor", "middle")
        .text("UMAP Dimension 2");

    // Add dots
    svg.selectAll("circle")
        .data(data)
        .enter()
        .append("circle")
        .attr("cx", d => xScale(d.umap_x))
        .attr("cy", d => yScale(d.umap_y))
        .attr("r", 6)
        .attr("fill", d => colorScale(d[selectedFeature]))
        .attr("stroke", "#fff")
        .attr("stroke-width", 1)
        .on("mouseover", function(event, d) {{
            d3.select(this)
                .attr("r", 8)
                .attr("stroke-width", 2);
            
            tooltip.style("opacity", 1)
                .html(`
                    <strong>Conversation ID:</strong> ${{d.conv_id}}<br>
                    <strong>Facilitator:</strong> ${{d.facilitator_name}}<br>
                    <strong>Number of Speakers:</strong> ${{d.num_observed_speakers}}<br>
                    <strong>Selected Feature:</strong> ${{d[selectedFeature].toFixed(3)}}<br>
                    <strong>Turn Sequence Entropy:</strong> ${{d.turn_sequence_entropy.toFixed(3)}}<br>
                    <strong>Substantive Responsivity:</strong> ${{d.substantive_responsivity_entropy.toFixed(3)}}
                `)
                .style("left", (event.pageX + 10) + "px")
                .style("top", (event.pageY - 10) + "px");
        }})
        .on("mouseout", function() {{
            d3.select(this)
                .attr("r", 6)
                .attr("stroke-width", 1);
            
            tooltip.style("opacity", 0);
        }});
}}

// Event listener for dropdown changes
d3.select("#feature-select").on("change", function() {{
    updateVisualization(this.value);
}});

// Initial visualization
updateVisualization("speaking_time_gini_coefficient");"""

# Write the JavaScript file
with open('script.js', 'w') as f:
    f.write(js_code)

# Load the UMAP data
with open('umapped_data.json', 'r') as f:
    data = json.load(f)

# Extract UMAP coordinates
umap_coords = np.array([[d['umap_x'], d['umap_y']] for d in data])

# Run HDBSCAN
clusterer = hdbscan.HDBSCAN(
    min_cluster_size=5,  # Minimum cluster size
    min_samples=3,       # Minimum number of samples in neighborhood
    cluster_selection_epsilon=0.5,  # Allows for more noise points
)

# Fit the clusterer
clusterer.fit(umap_coords)

# Add cluster assignments and probabilities to the data
for i, point in enumerate(data):
    point['cluster'] = int(clusterer.labels_[i])
    point['cluster_probability'] = float(clusterer.probabilities_[i])

# Save the results
with open('umapped_data_clustered.json', 'w') as f:
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