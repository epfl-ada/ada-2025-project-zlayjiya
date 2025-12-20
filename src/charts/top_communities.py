import pickle
import pandas as pd
import os
import json

# --- 1. CONFIGURATION ---
# Path to your data folder
DATA_DIR = "../../data/resultats" 
OUTPUT_HTML = "top_communities.html"
YEARS = list(range(2010, 2020))

# --- 2. DATA EXTRACTION ---
print("--- Starting Top 5 Communities Analysis ---")

# Structure to hold data for Rank 1 to Rank 5 across all years
final_data = {
    "years": YEARS,
    "ranks": {f"rank{i}": {"sizes": [], "labels": []} for i in range(1, 6)}
}

for year in YEARS:
    pkl_path = os.path.join(DATA_DIR, str(year), f"viz_data_{year}.pkl")
    
    # Handle missing years
    if not os.path.exists(pkl_path):
        print(f"⚠️  Year {year}: File not found. Filling with zeros.")
        for i in range(1, 6):
            final_data["ranks"][f"rank{i}"]["sizes"].append(0)
            final_data["ranks"][f"rank{i}"]["labels"].append("No Data")
        continue

    try:
        with open(pkl_path, "rb") as f:
            data = pickle.load(f)
            
            # Check if necessary keys exist
            if 'comm_summary' not in data or 'node_df' not in data:
                print(f"⚠️  Year {year}: Missing 'comm_summary' or 'node_df'.")
                continue

            comm_summary = data['comm_summary']
            node_df = data['node_df']

            # Get the top 5 largest communities by node count
            top5_comm = comm_summary.nlargest(5, 'n_nodes')

            # Loop through Rank 1 to 5
            for i in range(5):
                rank_key = f"rank{i+1}"
                
                # If a community exists for this rank
                if i < len(top5_comm):
                    row = top5_comm.iloc[i]
                    comm_id = row['community']
                    size = int(row['n_nodes'])
                    
                    # --- Determine Identity ---
                    # Filter nodes belonging to this community
                    members = node_df[node_df['community'] == comm_id]
                    
                    if not members.empty:
                        # 1. Dominant Category (Mode)
                        main_cat = members['category_cc'].mode()
                        main_cat = main_cat.iloc[0] if not main_cat.empty else "Unknown"
                        
                        # 2. Top Creator (Max PageRank)
                        # Ensure pagerank column exists, otherwise fallback
                        if 'pagerank' in members.columns:
                            top_creator = members.nlargest(1, 'pagerank')['name_cc'].iloc[0]
                        else:
                            top_creator = "Unknown"
                    else:
                        main_cat = "Unknown"
                        top_creator = "Unknown"

                    # Create the label for the tooltip
                    label = f"{main_cat} ({top_creator})"
                    
                    final_data["ranks"][rank_key]["sizes"].append(size)
                    final_data["ranks"][rank_key]["labels"].append(label)
                
                # If fewer than 5 communities exist in that year
                else:
                    final_data["ranks"][rank_key]["sizes"].append(0)
                    final_data["ranks"][rank_key]["labels"].append("N/A")

        print(f"✅ Year {year}: Processed successfully.")

    except Exception as e:
        print(f"❌ Error processing year {year}: {e}")

# Prepare JSON data for injection
json_years = json.dumps(final_data["years"])
json_ranks = json.dumps(final_data["ranks"])

print("--- Generating HTML Dashboard ---")

# --- 3. HTML TEMPLATE (DARK MODE) ---
html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Dynamic Top 5 Communities | YouNiverse</title>
    <script src="https://cdn.plot.ly/plotly-2.24.1.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap" rel="stylesheet">
    <style>
        /* DARK MODE CSS */
        body {{ 
            font-family: 'Inter', sans-serif; 
            margin: 0; 
            background-color: transparent; /* Pure Black Background */
            color: #e0e0e0; 
            display: flex; 
            justify-content: center; 
            align-items: center; 
            height: 100vh; 
        }}
        
        #chart-container {{ 
            background: transparent; /* Very dark grey card */
            border: none; 
            border-radius: 20px; 
            box-shadow: 0 10px 30px rgba(0,0,0,0.5); 
            width: 100%; 
            height: 100%; 
            padding: 20px; 
            box-sizing: border-box;
        }}
    </style>
</head>
<body>
    <div id="chart-container"></div>

<script>
    // --- DATA INJECTED FROM PYTHON ---
    const years = {json_years};
    const ranks = {json_ranks};

    // Colors for Rank 1 to Rank 5
    const colors = ['#e41a1c', '#377eb8', '#4daf4a', '#984ea3', '#ff7f00'];
    const rankLabels = ['#1 Largest', '#2 Largest', '#3 Largest', '#4 Largest', '#5 Largest'];

    // Construct Traces
    const traces = Object.keys(ranks).map((key, index) => {{
        return {{
            x: years,
            y: ranks[key].sizes,
            name: rankLabels[index],
            text: ranks[key].labels, // This contains "Category (Creator)"
            hovertemplate: '<b>Rank ' + (index+1) + '</b><br>%{{text}}<br>Size: %{{y}} channels<extra></extra>',
            type: 'bar',
            marker: {{ color: colors[index], opacity: 0.9 }}
        }};
    }});

    const layout = {{
        title: {{ 
            text: 'Evolution of Top 5 Community Identities', 
            font: {{ family: 'Inter', size: 22, weight: 900, color: '#ffffff' }} 
        }},
        font: {{
            family: 'Inter',
            color: '#e0e0e0'
        }},
        barmode: 'group', // Bars side by side
        xaxis: {{ 
            title: 'Year', 
            gridcolor: '#444444', 
            zeroline: false,
            tickcolor: '#e0e0e0'
        }},
        yaxis: {{ 
            title: 'Community Size (# of channels)', 
            gridcolor: '#444444', 
            zeroline: false,
            tickcolor: '#e0e0e0'
        }},
        legend: {{ 
            x: 0.01, 
            y: 0.99, 
            bgcolor: 'rgba(0, 0, 0, 0.5)', 
            font: {{ color: '#e0e0e0' }}
        }},
        margin: {{ l: 80, r: 50, t: 100, b: 80 }},
        hovermode: 'x unified',
        paper_bgcolor: 'rgba(0,0,0,0)', 
        plot_bgcolor: 'rgba(0,0,0,0)'
    }};

    Plotly.newPlot('chart-container', traces, layout, {{responsive: true}});
</script>
</body>
</html>
"""

# --- 4. EXPORT FILE ---
with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"\n🎉 Success! Dashboard generated at: {os.path.abspath(OUTPUT_HTML)}")