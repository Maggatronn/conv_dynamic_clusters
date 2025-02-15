import json

# Read the input JSON file
with open('conv_chains_features.json', 'r') as f:
    data = json.load(f)

# Create JavaScript file with the data
js_code = f"""// Load and process the data
const data = {json.dumps(data, indent=2)};

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

// Function to update the visualization
function updateVisualization(selectedFeature) {{
    // Clear previous visualization
    svg.selectAll("*").remove();

    // Create scales for x and y axes based on selected features
    const xScale = d3.scaleLinear()
        .domain([0, d3.max(data, d => d.turn_sequence_entropy)])
        .range([margin.left, width - margin.right]);

    const yScale = d3.scaleLinear()
        .domain([0, d3.max(data, d => d.substantive_responsivity_entropy)])
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
        .text("Turn Sequence Entropy");

    svg.append("text")
        .attr("transform", "rotate(-90)")
        .attr("x", -height / 2)
        .attr("y", 15)
        .attr("text-anchor", "middle")
        .text("Substantive Responsivity Entropy");

    // Add dots
    svg.selectAll("circle")
        .data(data)
        .enter()
        .append("circle")
        .attr("cx", d => xScale(d.turn_sequence_entropy))
        .attr("cy", d => yScale(d.substantive_responsivity_entropy))
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