import pickle
import os
import json

# --- 1. CONFIGURATION ---
# Path to your data folder
DATA_DIR = "../../data/resultats" 
OUTPUT_HTML = "fragmentation.html"
YEARS = list(range(2010, 2020))

# --- 2. DATA EXTRACTION ---
print("--- Starting Fragmentation Analysis ---")

years_found = []
counts = []

for year in YEARS:
    pkl_path = os.path.join(DATA_DIR, str(year), f"viz_data_{year}.pkl")
    
    if not os.path.exists(pkl_path):
        print(f"⚠️  Year {year}: File not found. Skipping.")
        continue

    try:
        with open(pkl_path, "rb") as f:
            data = pickle.load(f)
            
            # Check if 'communities' key exists
            if 'communities' in data:
                count = len(data['communities'])
                years_found.append(year)
                counts.append(count)
                print(f"✅ Year {year}: {count} communities detected.")
            else:
                print(f"⚠️  Year {year}: 'communities' data missing.")

    except Exception as e:
        print(f"❌ Error processing year {year}: {e}")

# --- 3. CALCULATE GROWTH ---
if len(counts) > 1:
    start_val = counts[0]
    end_val = counts[-1]
    # Avoid division by zero
    if start_val > 0:
        growth_percent = int(((end_val - start_val) / start_val) * 100)
    else:
        growth_percent = 0
else:
    growth_percent = 0

# Prepare JSON data for injection
json_years = json.dumps(years_found)
json_counts = json.dumps(counts)

print("--- Generating HTML Dashboard ---")

# --- 4. HTML TEMPLATE (DARK MODE) ---
html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube Network Fragmentation | 2010-2019</title>
    <script src="https://cdn.plot.ly/plotly-2.24.1.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap" rel="stylesheet">
    <style>
        /* DARK MODE CSS */
        body {{ 
            font-family: 'Inter', sans-serif; 
            margin: 0; 
            background-color: transparent; 
            display: flex; 
            justify-content: center; 
            align-items: center; 
            height: 100vh; 
            width: 100vw;
            color: #e0e0e0;
        }}
        
        #chart-container {{ 
            background: transparent;
            border: none; 
            border-radius: 20px; 
            box-shadow: none; 
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
    const communitiesCount = {json_counts};
    const growthPercent = {growth_percent};

    // Configure the Scatter Trace
    const trace = {{
        x: years,
        y: communitiesCount,
        mode: 'lines+markers+text',
        name: 'Communities Count',
        text: communitiesCount,
        textposition: 'top center',
        textfont: {{ family: 'Inter', weight: 700, size: 13, color: '#e0e0e0' }},
        line: {{ color: '#e41a1c', width: 4, shape: 'spline' }}, // Red line
        marker: {{ 
            size: 10, 
            color: '#e41a1c', 
            line: {{ color: '#ffffff', width: 2 }} 
        }},
        fill: 'tozeroy', 
        fillcolor: 'rgba(228, 26, 28, 0.1)', // Subtle red fill
        type: 'scatter'
    }};

    // Historical Annotations logic
    const annotations = [
        // Main Growth Box (Top Left)
        {{
            xref: 'paper', yref: 'paper',
            x: 0.04, y: 0.98,
            text: `+${{growthPercent}}% Fragmentation`,
            showarrow: false,
            font: {{ family: 'Inter', size: 18, color: '#e41a1c', weight: 900 }},
            bgcolor: '#000000', // Black background for box
            bordercolor: '#e41a1c',
            borderwidth: 2,
            borderpad: 8
        }}
    ];

    // Helper to add timeline events safely
    const addEvent = (year, label, ax, ay) => {{
        const idx = years.indexOf(year);
        if (idx !== -1) {{
            annotations.push({{
                x: year, 
                y: communitiesCount[idx], 
                text: label, 
                showarrow: true, arrowhead: 2, ax: ax, ay: ay, 
                arrowcolor: '#e0e0e0',
                font: {{ size: 11, color: '#cccccc' }} 
            }});
        }}
    }};

    // Add specific historical events
    addEvent(2012, 'PewDiePie era starts', 0, 40);
    addEvent(2016, 'Massive Indian expansion (Jio)', 0, 40);
    addEvent(2019, 'Peak Network Modularity', -40, 0);

    const layout = {{
        title: {{
            text: 'YouTube Network Fragmentation (2010-2019)',
            font: {{ family: 'Inter', size: 24, weight: 900, color: '#ffffff' }},
            pad: {{ t: 20 }}
        }},
        font: {{
            family: 'Inter',
            color: '#e0e0e0'
        }},
        xaxis: {{
            title: 'Analysis Year',
            tickmode: 'linear',
            gridcolor: '#444444',
            zeroline: false,
            tickcolor: '#e0e0e0',
            font: {{ family: 'Inter', weight: 700 }}
        }},
        yaxis: {{
            title: 'Detected Communities (Louvain/Leiden)',
            gridcolor: '#444444',
            zeroline: false,
            tickcolor: '#e0e0e0',
            range: [0, Math.max(...communitiesCount) * 1.3] // Add space for annotations
        }},
        margin: {{ l: 80, r: 50, t: 100, b: 80 }},
        hovermode: 'x unified',
        annotations: annotations,
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)'
    }};

    // Render Plotly Chart
    Plotly.newPlot('chart-container', [trace], layout, {{responsive: true}});

</script>

</body>
</html>
"""

# --- 5. EXPORT FILE ---
with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"\n🎉 Success! Dashboard generated at: {os.path.abspath(OUTPUT_HTML)}")