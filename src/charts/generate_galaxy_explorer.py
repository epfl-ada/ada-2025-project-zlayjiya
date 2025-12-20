import pickle
import json
import os
import networkx as nx
from collections import defaultdict

# --- 1. CONFIGURATION ---
DATA_DIR = "../../data/resultats" 
OUTPUT_HTML = "galaxy_explorer.html"
YEARS = list(range(2010, 2020))

# --- 2. DATA PROCESSING FUNCTION ---
def process_year(year):
    """
    Reads the PKL file for a specific year and aggregates channels into galaxies.
    """
    pkl_path = os.path.join(DATA_DIR, str(year), f"viz_data_{year}.pkl")
    
    if not os.path.exists(pkl_path):
        print(f"⚠️  Year {year}: File not found. Skipping.")
        return None

    try:
        with open(pkl_path, "rb") as f:
            data = pickle.load(f)

        LCC = data['LCC']
        communities = data['communities']
        
        if 'node_df' in data:
            node_df = data['node_df'].set_index("channel_id").to_dict(orient="index")
        else:
            node_df = {}

        # --- A. PREPARE NODES (GALAXIES) ---
        nodes_json = []
        node2comm = {} 
        comm_sizes = {} 
        
        strength = {
            u: sum(d.get("weight", d.get("weight_raw", 1)) for _, d in LCC[u].items()) 
            for u in LCC.nodes()
        }

        for cid, nodes_c in enumerate(communities):
            if len(nodes_c) < 5: continue
            
            for node in nodes_c:
                node2comm[node] = cid
            
            sorted_nodes = sorted(nodes_c, key=lambda u: strength.get(u, 0), reverse=True)[:5]
            
            top_channels = []
            for n in sorted_nodes:
                info = node_df.get(n, {})
                name = info.get('name_cc') or str(n)
                top_channels.append(name)
            
            comm_id = f"comm_{cid}"
            comm_sizes[comm_id] = len(nodes_c)
            
            nodes_json.append({
                "id": comm_id,
                "name": top_channels[0] if top_channels else f"Galaxy {cid}",
                "size": len(nodes_c),
                "top_channels": top_channels
            })

        # --- B. PREPARE EDGES ---
        comm_edges = defaultdict(int)
        
        for u, v, d in LCC.edges(data=True):
            cu = node2comm.get(u)
            cv = node2comm.get(v)
            
            if cu is not None and cv is not None and cu != cv:
                edge_key = tuple(sorted([cu, cv]))
                weight = d.get("weight", d.get("weight_raw", 1))
                comm_edges[edge_key] += weight

        links_json = []
        for (c1, c2), w in comm_edges.items():
            id1 = f"comm_{c1}"
            id2 = f"comm_{c2}"
            
            if id1 in comm_sizes and id2 in comm_sizes:
                size_product = comm_sizes[id1] * comm_sizes[id2]
                density = (w / size_product) * 1000 if size_product > 0 else 0
                
                links_json.append({
                    "source": id1,
                    "target": id2,
                    "weight": float(density),
                    "raw_weight": int(w)
                })

        print(f"✅ Year {year}: {len(nodes_json)} galaxies, {len(links_json)} connections.")
        return {"nodes": nodes_json, "links": links_json}

    except Exception as e:
        print(f"❌ Error processing {year}: {e}")
        return None

# --- 3. EXECUTE PROCESSING ---
print("--- Starting Galaxy Extraction ---")
all_data = {}

for year in YEARS:
    result = process_year(year)
    if result:
        all_data[year] = result

json_payload = json.dumps(all_data)

print("--- Generating HTML Explorer ---")

# --- 4. HTML TEMPLATE ---
html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>YouNiverse | Galaxy Explorer</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
    <style>
        :root { 
            --primary: #00d2ff; 
            --bg: #000000; 
            --text: #e0e0e0; 
            --panel: rgba(20, 20, 20, 0.95); 
            --border: #333;
        }
        
        body { 
            font-family: 'Inter', sans-serif; 
            background-color: var(--bg); 
            color: var(--text); 
            overflow: hidden; 
            margin: 0; 
        }
        
        #viz-layout { display: flex; width: 100vw; height: 100vh; position: relative; }

        #controls { position: absolute; top: 20px; left: 20px; z-index: 1000; display: flex; flex-direction: column; gap: 10px; }
        
        .btn { 
            padding: 12px 20px; 
            background: #1a1a1a; 
            color: white;
            border: 1px solid var(--border); 
            border-radius: 30px; 
            cursor: pointer; 
            font-weight: 700; 
            font-family: 'Inter'; 
            transition: 0.3s; 
            box-shadow: 0 4px 6px rgba(0,0,0,0.5); 
        }
        .btn:hover { background: #333; border-color: var(--primary); }

        #info-panel {
            position: absolute; top: 20px; right: 20px; width: 340px; 
            background: var(--panel);
            border: 1px solid var(--border); 
            border-radius: 12px; padding: 24px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5); 
            z-index: 100; display: none;
            backdrop-filter: blur(10px);
        }
        #info-panel.active { display: block; }
        #info-panel h2 { margin-top: 0; color: #fff; }

        #timeline-container {
            position: absolute; bottom: 30px; left: 50%; transform: translateX(-50%);
            width: 450px; background: #1a1a1a; padding: 20px 30px; border-radius: 60px;
            border: 1px solid var(--border);
            box-shadow: 0 5px 20px rgba(0,0,0,0.5); display: flex; align-items: center; gap: 20px; z-index: 1000;
        }
        #year-slider { flex-grow: 1; accent-color: var(--primary); cursor: pointer; }
        #year-display { font-weight: 900; font-size: 22px; color: var(--primary); min-width: 60px; }

        /* --- UPDATED EDGE STYLES --- */
        /* pointer-events: none ensures edges are ignored by the mouse (no hover) */
        .link { 
            stroke: #555; 
            stroke-opacity: 0.2; 
            transition: stroke 0.3s, stroke-opacity 0.3s, filter 0.3s; 
            pointer-events: none; 
        }

        /* --- NEW: ILLUMINATED EDGE STYLE --- */
        .edge-highlight {
            stroke: var(--primary) !important;
            stroke-opacity: 0.8 !important;
            filter: drop-shadow(0 0 4px var(--primary)); /* Glowing effect */
            z-index: 500;
        }

        .node circle { stroke: #fff; stroke-width: 1.5px; cursor: pointer; transition: all 0.2s; }
        .node text { 
            font-size: 11px; font-weight: 700; fill: #bbb; 
            pointer-events: none; text-shadow: 0 2px 4px #000; 
        }
        
        /* Faded state for non-connected elements */
        .faded { opacity: 0.05 !important; }
        
        /* Highlight state for the selected node */
        .highlight { stroke: var(--primary) !important; stroke-width: 4px !important; filter: drop-shadow(0 0 8px var(--primary)); }
        
        #top-channels-list { list-style: none; padding: 0; }
        #top-channels-list li { 
            background: #222; margin-bottom: 8px; padding: 12px; 
            border-radius: 8px; font-size: 13px; font-weight: 600; color: #eee; 
            border: 1px solid #333;
        }
    </style>
</head>
<body>

<div id="viz-layout">
    <div id="controls">
        <button id="recenter-btn" class="btn">Recenter View</button>
    </div>
    
    <div id="timeline-container">
        <span id="year-display">2010</span>
        <input type="range" id="year-slider" min="2010" max="2019" step="1" value="2010">
    </div>

    <div id="info-panel">
        <h2 id="comm-name">Galaxy Name</h2>
        <p id="comm-size" style="color: #888;">0 Channels</p>
        <hr style="border-color: #333;">
        <p style="color: var(--primary); text-transform: uppercase; font-size: 12px; font-weight: 800; letter-spacing: 1px;">Top 5 Leaders</p>
        <ul id="top-channels-list"></ul>
    </div>
</div>

<script>
    // --- INJECTED DATA PLACEHOLDER ---
    const dataset = __JSON_DATA_PLACEHOLDER__;
    
    const width = window.innerWidth, height = window.innerHeight;
    
    const svg = d3.select("#viz-layout").append("svg")
        .attr("width", width)
        .attr("height", height)
        .style("background-color", "var(--bg)");
        
    const g = svg.append("g");

    const zoom = d3.zoom()
        .scaleExtent([0.1, 8])
        .on("zoom", (e) => g.attr("transform", e.transform));
    svg.call(zoom);

    let currentYear = 2010;
    let simulation;
    
    const colorScale = d3.scaleOrdinal(d3.schemeTableau10);

    function updateGraph(year) {
        currentYear = year;
        
        g.selectAll("*").remove();
        if (simulation) simulation.stop();
        d3.select("#info-panel").classed("active", false);

        const data = dataset[year];

        if (!data) {
            g.append("text")
                .attr("x", width/2).attr("y", height/2)
                .attr("fill", "white").attr("text-anchor", "middle")
                .style("font-size", "24px")
                .text("No data available for " + year);
            return;
        }

        const nodes = data.nodes.map(d => ({...d}));
        const links = data.links.map(d => ({...d}));

        const sizeScale = d3.scaleSqrt()
            .domain(d3.extent(nodes, d => d.size))
            .range([12, 70]);
        
        const weightExtent = d3.extent(links, d => d.weight);
        const distanceScale = d3.scaleLinear()
            .domain(weightExtent)
            .range([400, 100]); 

        simulation = d3.forceSimulation(nodes)
            .force("link", d3.forceLink(links).id(d => d.id).distance(d => distanceScale(d.weight)))
            .force("charge", d3.forceManyBody().strength(d => -1000 - (d.size * 5)))
            .force("center", d3.forceCenter(width / 2, height / 2))
            .force("collide", d3.forceCollide().radius(d => sizeScale(d.size) + 15).iterations(2));

        // --- DRAW EDGES ---
        // Removed mouseover/mouseout listeners
        const link = g.append("g")
            .selectAll("line")
            .data(links)
            .join("line")
            .attr("class", "link")
            .attr("stroke-width", d => Math.min(Math.log10(d.raw_weight + 1) * 3, 8));

        // --- DRAW NODES ---
        const node = g.append("g")
            .selectAll("g")
            .data(nodes)
            .join("g")
            .attr("class", "node")
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended));

        node.append("circle")
            .attr("r", d => sizeScale(d.size))
            .attr("fill", (d, i) => colorScale(i % 10))
            .attr("fill-opacity", 0.9);

        node.append("text")
            .attr("text-anchor", "middle")
            .attr("dy", d => sizeScale(d.size) + 20)
            .text(d => d.name);

        // --- INTERACTION ---
        node.on("click", (event, d) => {
            event.stopPropagation();
            
            d3.select("#info-panel").classed("active", true);
            d3.select("#comm-name").text(d.name + " Cluster");
            d3.select("#comm-size").text(`${d.size.toLocaleString()} Channels`);
            
            const list = d3.select("#top-channels-list").html("");
            d.top_channels.forEach(channelName => {
                list.append("li").text(channelName);
            });

            // --- VISUAL LOGIC ---
            // 1. Fade everything that is NOT the selected node
            node.classed("faded", n => n.id !== d.id);
            
            // 2. Default: fade all links (make them disappear essentially)
            link.classed("faded", true);
            link.classed("edge-highlight", false);

            // 3. Highlight ONLY connected links
            // We search for links where source OR target matches current ID
            link.classed("faded", l => l.source.id !== d.id && l.target.id !== d.id);
            link.classed("edge-highlight", l => l.source.id === d.id || l.target.id === d.id);
            
            // 4. Highlight Selected Circle
            d3.selectAll("circle").classed("highlight", false);
            d3.select(event.currentTarget).select("circle").classed("highlight", true);
        });

        simulation.on("tick", () => {
            link
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);

            node.attr("transform", d => `translate(${d.x},${d.y})`);
        });
    }

    document.getElementById("year-slider").oninput = function() {
        document.getElementById("year-display").innerText = this.value;
        updateGraph(this.value);
    };

    document.getElementById("recenter-btn").onclick = () => {
        svg.transition().duration(750).call(zoom.transform, d3.zoomIdentity);
    };

    // Reset when clicking background
    svg.on("click", () => {
        d3.select("#info-panel").classed("active", false);
        d3.selectAll(".faded").classed("faded", false);
        d3.selectAll(".highlight").classed("highlight", false);
        d3.selectAll(".edge-highlight").classed("edge-highlight", false);
    });

    function dragstarted(event, d) { if (!event.active) simulation.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; }
    function dragged(event, d) { d.fx = event.x; d.fy = event.y; }
    function dragended(event, d) { if (!event.active) simulation.alphaTarget(0); d.fx = null; d.fy = null; }

    updateGraph(2010);
</script>
</body>
</html>
"""

# --- 5. INJECTION & WRITE FILE ---
final_html = html_template.replace("__JSON_DATA_PLACEHOLDER__", json_payload)

with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
    f.write(final_html)

print(f"\n🎉 Success! Galaxy Explorer generated at: {os.path.abspath(OUTPUT_HTML)}")