import pickle
import networkx as nx
import os
import json

# --- 1. CONFIGURATION ---
# Path to your data folder
DATA_DIR = "../../data/resultats"
OUTPUT_HTML = "network_density.html"
YEARS = list(range(2010, 2020))

# --- 2. DATA EXTRACTION ---
print("--- Starting Network Density Analysis ---")

years_found = []
densities = []

for year in YEARS:
    pkl_path = os.path.join(DATA_DIR, str(year), f"viz_data_{year}.pkl")
    
    if not os.path.exists(pkl_path):
        print(f"⚠️  Year {year}: File not found. Skipping.")
        continue

    try:
        with open(pkl_path, "rb") as f:
            data = pickle.load(f)
            
            # Ensure the Largest Connected Component (LCC) exists
            if 'LCC' in data:
                # Calculate Density: ratio of actual edges to possible edges
                d = nx.density(data['LCC'])
                
                years_found.append(year)
                densities.append(float(d))
                print(f"✅ Year {year}: Density {d:.6f}")
            else:
                print(f"⚠️  Year {year}: 'LCC' graph missing in pickle.")

    except Exception as e:
        print(f"❌ Error processing year {year}: {e}")

# --- 3. CALCULATE DROP ---
# Calculate the total percentage drop for the annotation (kept for potential use, but not displayed)
drop_percent = 0.0
if len(densities) > 1:
    start_val = densities[0]
    end_val = densities[-1]
    if start_val > 0:
        drop_percent = ((start_val - end_val) / start_val) * 100

# Prepare JSON data for injection
json_years = json.dumps(years_found)
json_densities = json.dumps(densities)

print("--- Generating HTML Dashboard ---")

# --- 4. HTML TEMPLATE (DARK MODE) ---
html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>YouNiverse | Global Connectivity Decay</title>
    <script src="https://cdn.plot.ly/plotly-2.24.1.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap" rel="stylesheet">
    <style>
        /* DARK MODE CSS */
        body {{ 
            font-family: 'Inter', sans-serif; 
            margin: 0; 
            background-color: transparent; 
            color: #e0e0e0; 
            display: flex; 
            justify-content: center; 
            align-items: center; 
            height: 100vh; 
        }}
        
        #chart-container {{ 
            background: transparent; 
            border: none; 
            border-radius:none; 
            box-shadow: 0 15px 35px rgba(0,0,0,0.5); 
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
    const densities = {json_densities};
    // const dropPercent = {drop_percent:.1f}; // Not used in chart anymore

    // Trace Configuration
    const trace = {{
        x: years,
        y: densities,
        mode: 'lines+markers',
        name: 'Network Density',
        // Cyan/Blue color to pop against the dark background
        line: {{ color: '#00d2ff', width: 4, shape: 'spline' }}, 
        marker: {{ 
            size: 10, 
            color: '#00d2ff', 
            line: {{ color: '#ffffff', width: 2 }} 
        }},
        fill: 'tozeroy',
        fillcolor: 'rgba(0, 210, 255, 0.1)', // Subtle glowing effect
        type: 'scatter',
        hovertemplate: '<b>Year %{{x}}</b><br>Density: %{{y:.6f}}<extra></extra>'
    }};

    const layout = {{
        title: {{ 
            text: 'Decline of Global Connectivity (2010-2019)', 
            font: {{ family: 'Inter', size: 24, weight: 900, color: '#ffffff' }} 
        }},
        font: {{
            family: 'Inter',
            color: '#e0e0e0'
        }},
        xaxis: {{ 
            title: 'Year', 
            gridcolor: '#444444', 
            zeroline: false, 
            tickmode: 'linear',
            tickcolor: '#e0e0e0'
        }},
        yaxis: {{ 
            title: 'Structural Density', 
            gridcolor: '#444444', 
            zeroline: false, 
            tickformat: '.4f',
            tickcolor: '#e0e0e0'
        }},
        margin: {{ l: 80, r: 50, t: 100, b: 80 }},
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        
        // Annotations removed
        annotations: []
    }};

    Plotly.newPlot('chart-container', [trace], layout, {{responsive: true}});
</script>
</body>
</html>
"""

# --- 5. EXPORT FILE ---
with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"\n🎉 Success! Dashboard generated at: {os.path.abspath(OUTPUT_HTML)}")