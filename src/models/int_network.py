import networkx as nx
import numpy as np
import matplotlib.pyplot as plt
from pyvis.network import Network
import matplotlib.colors as mcolors

def visualize_core_network(LCC, communities, node_df, viz_out_path,
                           n_per_comm=15,
                           num_top_communities=5,
                           weight_threshold=5,
                           seed=42):
    """
    Zooms into the 'Galactic Core' by only graphing the largest communities.
    Filters out peripheral/satellite galaxies.
    """
    print(f"Focusing on the top {num_top_communities} largest galaxies...")

    sorted_communities = sorted(communities, key=len, reverse=True)
    core_communities = sorted_communities[:num_top_communities]
   
    node2comm = {node: cid for cid, comm in enumerate(core_communities) for node in comm}
    core_nodes_all = set(node2comm.keys())

    strength = {u: sum(d.get("weight_raw", 0) for _, d in LCC[u].items()) for u in core_nodes_all}

    meta = node_df.set_index("channel_id").to_dict(orient="index")
    def name_of(uid):
        nm = (meta.get(uid, {}) or {}).get("name_cc") or uid
        return nm if len(str(nm)) > 0 else uid

    selected = set()
    top_per_comm = {}
    for cid, nodes_c in enumerate(core_communities):
        top_nodes = sorted(nodes_c, key=lambda u: strength.get(u, 0), reverse=True)
        selected.update(top_nodes[:n_per_comm])
        top_per_comm[cid] = name_of(top_nodes[0])

    edges_to_keep = [
        (u, v) for u, v, d in LCC.edges(data=True)
        if u in selected and v in selected and d.get("weight_raw", 0) >= weight_threshold
    ]
   
    H = LCC.edge_subgraph(edges_to_keep).copy()
    H.remove_nodes_from(list(nx.isolates(H)))

    print(f"Core visualization: {H.number_of_nodes()} nodes, {H.number_of_edges()} edges")

    pos = nx.spring_layout(H, weight="weight_raw", seed=seed, k=1.5, iterations=100)
   
    plt.figure(figsize=(16, 12), facecolor='white')
   
    comm_colors = plt.cm.Set1(np.linspace(0, 1, num_top_communities))
    node_colors = [comm_colors[node2comm[n]] for n in H.nodes()]
    node_sizes = [50 * np.log10(strength.get(n, 1) + 10) for n in H.nodes()]

    nx.draw_networkx_edges(H, pos, width=0.5, alpha=0.2, edge_color="black")
    nx.draw_networkx_nodes(H, pos, node_color=node_colors, node_size=node_sizes,
                           edgecolors="black", linewidths=0.5, alpha=0.8)
    label_targets = {}
    for nodes_c in core_communities:
        top_3 = sorted(nodes_c, key=lambda u: strength.get(u, 0), reverse=True)[:3]
        for node in top_3:
            if node in H:
                label_targets[node] = name_of(node)
               
    nx.draw_networkx_labels(H, pos, labels=label_targets, font_size=8, font_weight='bold')

    plt.title(f"Voyage into the Core: Interaction between Top {num_top_communities} Galaxies", fontsize=15)
    plt.axis("off")
    plt.savefig(viz_out_path, dpi=300, bbox_inches="tight")
    plt.show()


def visualize_core_interactive(LCC, communities, node_df, html_out_path, 
                               num_top_communities=5, n_per_comm=20, seed=42):

    print(f"Finalizing Cosmic Core for {num_top_communities} galaxies...")
    
    sorted_communities = sorted(communities, key=len, reverse=True)
    core_communities = sorted_communities[:num_top_communities]
    
    node2comm = {node: cid for cid, comm in enumerate(core_communities) for node in comm}
    core_nodes_all = set(node2comm.keys())
    
    strength = {u: sum(d.get("weight_raw", 0) for _, d in LCC[u].items()) for u in core_nodes_all}
    meta = node_df.set_index("channel_id").to_dict(orient="index")

    def name_of(uid):
        nm = (meta.get(uid, {}) or {}).get("name_cc") or uid
        return str(nm) if len(str(nm)) > 0 else str(uid)

    selected = set()
    for nodes_c in core_communities:
        top_nodes = sorted(nodes_c, key=lambda u: strength.get(u, 0), reverse=True)
        selected.update(top_nodes[:n_per_comm])

    edges_to_keep = [(u, v) for u, v, d in LCC.edges(data=True) 
                     if u in selected and v in selected and d.get("weight_raw", 0) >= 3]
    H = LCC.edge_subgraph(edges_to_keep).copy()
    H.remove_nodes_from(list(nx.isolates(H)))

    pos = nx.spring_layout(H, weight="weight_raw", seed=seed, k=2.5, iterations=100)
    center_x = np.mean([p[0] for p in pos.values()])
    center_y = np.mean([p[1] for p in pos.values()])
    
    expanded_pos = {}
    distances = {node: np.sqrt((p[0]-center_x)**2 + (p[1]-center_y)**2) for node, p in pos.items()}
    max_dist = max(distances.values()) if distances else 1.0
    
    for node, (x, y) in pos.items():
        dist = distances[node]
        norm_dist = dist / max_dist
        expansion_factor = 1.0 + (3.5 * (1 - norm_dist)**2)
        expanded_pos[node] = (center_x + (x - center_x) * expansion_factor, 
                             center_y + (y - center_y) * expansion_factor)
    
    pos = expanded_pos
    SPREAD = 2000 

    net = Network(height='850px', width='100%', bgcolor='#050505', font_color='white', cdn_resources='remote')
    net.toggle_physics(False) 

    cosmic_palette = [
        # Core cosmic (5)
        "#7b2cbf", "#ff0054", "#3f37c9", "#4cc9f0", "#f9c74f",
        # Neon electric (5)
        "#ff006e", "#8338ec", "#06ffa5", "#fb5607", "#ffbe0b",
        # Ocean depths (5)
        "#e63946", "#a8dadc", "#457b9d", "#1d3557", "#f1faee",
        # Solar warmth (5)
        "#d62828", "#f77f00", "#fcbf49", "#eae2b7", "#003049",
        # Pastel nebula (5)
        "#9d4edd", "#c77dff", "#e0aaff", "#ff9770", "#ffc2d1",
        # Vibrant galaxy (5)
        "#06d6a0", "#118ab2", "#073b4c", "#ef476f", "#ffd166",
        # Aurora borealis (5)
        "#b5179e", "#7209b7", "#560bad", "#f72585", "#4361ee",
        # Stellar fusion (5)
        "#ff9e00", "#ff6d00", "#ff3d00", "#dd2c00", "#bf360c",
        # Deep space (5)
        "#00b4d8", "#0096c7", "#0077b6", "#023e8a", "#03045e",
        # Supernova burst (5)
        "#ff4d6d", "#ff758f", "#ff9ebb", "#c9184a", "#a4133c"
    ]

    for node in H.nodes():
        cid = node2comm[node]
        color = cosmic_palette[cid % len(cosmic_palette)]
        x_pos = float(pos[node][0] * SPREAD)
        y_pos = float(pos[node][1] * SPREAD)
        node_size = 3 + (np.log10(strength.get(node, 1) + 1) * 15)
        
        net.add_node(
            node, x=x_pos, y=y_pos, label=name_of(node), 
            color={'background': color, 'border': '#ffffff', 'highlight': color}, 
            size=node_size,
            shadow={'enabled': True, 'color': color, 'size': 10, 'x': 0, 'y': 0}, 
            title=f"Channel: {name_of(node)} \nGalaxy Cluster: {cid}",
            borderWidth=0,
            font={'size': 18, 'color': '#ffffff'}
        )

    for u, v, d in H.edges(data=True):
        w = d.get("weight_raw", 1)
        width = 0.5 + (np.log10(w) * 1.5)
        # Faint starlight thread edges
        net.add_edge(u, v, width=width, color='rgba(255, 255, 255, 0.08)')

    # 5. Legend and HTML Injection
    legend_html = f"""
    <div style="position: absolute; top: 15px; left: 15px; width: 230px; background: rgba(5, 5, 5, 0.9); 
                border: 1px solid #333; padding: 12px; font-family: sans-serif; z-index: 1000; border-radius: 8px; color: #eee;">
        <b style="font-size: 13px; display: block; margin-bottom: 8px; border-bottom: 1px solid #333; color: #888;">Galactic Hubs</b>
    """
    for cid, nodes_c in enumerate(core_communities[:20]):
        best = max(nodes_c, key=lambda u: strength.get(u, 0))
        color = cosmic_palette[cid % len(cosmic_palette)]
        legend_html += f'<div style="margin-bottom: 5px; font-size: 11px;"><span style="color:{color};">●</span> <b>C{cid}:</b> {name_of(best)}</div>'
    legend_html += "</div>"

    net.save_graph(html_out_path)

    with open(html_out_path, 'r', encoding='utf-8') as f:
        content = f.read()

    zoom_js = """
    <script type="text/javascript">
    setTimeout(function() {
        network.moveTo({
        scale: 0.07,
        position: {x: 0, y: 2500},
        animation: false
        });
    }, 100);
    </script>
    """

    content = content.replace(
        "</body>",
        f"{legend_html}\n{zoom_js}\n</body>"
    )

    content = content.replace(
        "<body>",
        '<body style="background-color:#050505; margin:0; overflow:hidden;">'
    )
    style_fix = """
    <style>
    html, body {
    margin: 0 !important;
    padding: 0 !important;
    width: 100%;
    height: 100%;
    border:0;
    background: #050505 !important;
    overflow: hidden;
    }
    .card {
        border: none !important;
        outline: none !important;
        border-radius: 0 !important;
        background-color: black;
    }

    #mynetwork {
    width: 100% !important;
    background: #050505 !important;
    border: #000000;
    }

    canvas {
    display: block !important;
    background: #050505 !important;
    }
    </style>
    """
    content = content.replace("</head>", style_fix + "\n</head>")

    with open(html_out_path, 'w', encoding='utf-8') as f:
        f.write(content)


    print(f"Cosmic Core saved to: {html_out_path}")

def visualize_single_galaxy(LCC, communities, node_df, community_id, html_out_path,
                           n_nodes=50,
                           weight_threshold=3,
                           seed=42):
    """
    Visualizes a single galaxy (community) from the YouNiverse using Pyvis.
    
    Parameters:
    -----------
    LCC : networkx.Graph
        The largest connected component of your network
    communities : list of sets
        List where each element is a set of nodes in that community
    node_df : pd.DataFrame
        DataFrame with channel metadata (must have 'channel_id' and 'name_cc' columns)
    community_id : int
        The ID of the community to visualize (0-indexed)
    html_out_path : str
        Path to save the HTML visualization
    n_nodes : int
        Maximum number of nodes to display (top by degree)
    weight_threshold : float
        Minimum edge weight to include
    seed : int
        Random seed for layout reproducibility
    """
    
    print(f"\nZooming into Galaxy #{community_id}...")
    print("=" * 60)
    
    if community_id >= len(communities):
        raise ValueError(f"Community {community_id} doesn't exist. Max ID is {len(communities)-1}")
    
    galaxy_nodes = communities[community_id]
    print(f"Total Channels in Galaxy: {len(galaxy_nodes)}")
    
    subgraph_full = LCC.subgraph(galaxy_nodes).copy()
    
    strength = {u: sum(d.get("weight_raw", 0) for _, d in subgraph_full[u].items()) 
                for u in galaxy_nodes}
    
    total_strength = sum(strength.values())
    avg_strength = np.mean(list(strength.values()))
    

    total_possible_edges = (len(galaxy_nodes) * (len(galaxy_nodes) - 1)) / 2
    internal_density = subgraph_full.number_of_edges() / total_possible_edges if total_possible_edges > 0 else 0
    
    clustering = nx.average_clustering(subgraph_full, weight='weight_raw')
    
    meta = node_df.set_index("channel_id").to_dict(orient="index")
    
    def name_of(uid):
        nm = (meta.get(uid, {}) or {}).get("name_cc") or uid
        return str(nm) if len(str(nm)) > 0 else str(uid)
    
    
    black_hole = max(galaxy_nodes, key=lambda u: strength.get(u, 0))
    black_hole_name = name_of(black_hole)
    black_hole_strength = strength[black_hole]
    
    top_5_channels = sorted(galaxy_nodes, key=lambda u: strength.get(u, 0), reverse=True)[:5]
    
    print(f"\nBLACK HOLE: {black_hole_name}")
    print(f"   Gravitational Strength: {black_hole_strength:,.0f}")
    print(f"\nTop 5 Channels:")
    for i, channel in enumerate(top_5_channels, 1):
        print(f"   {i}. {name_of(channel)} (strength: {strength[channel]:,.0f})")
    
    print(f"\nGalaxy Statistics:")
    print(f"   Total Internal Strength: {total_strength:,.0f}")
    print(f"   Average Node Strength: {avg_strength:,.2f}")
    print(f"   Internal Density: {internal_density:.4f}")
    print(f"   Clustering Coefficient: {clustering:.4f}")
    print(f"   Total Edges: {subgraph_full.number_of_edges():,}")
    
    top_nodes = sorted(galaxy_nodes, key=lambda u: strength.get(u, 0), reverse=True)[:n_nodes]
    
    edges_to_keep = [
        (u, v) for u, v, d in subgraph_full.edges(data=True)
        if u in top_nodes and v in top_nodes and d.get("weight_raw", 0) >= weight_threshold
    ]
    
    H = LCC.edge_subgraph(edges_to_keep).copy()
    H.remove_nodes_from(list(nx.isolates(H)))
    
    print(f"\n Visualization:")
    print(f"   Displaying {H.number_of_nodes()} nodes, {H.number_of_edges()} edges")
    print(f"   (Filtered: min {weight_threshold} edge weight)")
    
    pos = nx.spring_layout(H, weight="weight_raw", seed=seed, k=2.0, iterations=100)
    
    center_x = np.mean([p[0] for p in pos.values()])
    center_y = np.mean([p[1] for p in pos.values()])
    
    expanded_pos = {}
    distances = {node: np.sqrt((p[0]-center_x)**2 + (p[1]-center_y)**2) for node, p in pos.items()}
    max_dist = max(distances.values()) if distances else 1.0
    
    for node, (x, y) in pos.items():
        dist = distances[node]
        norm_dist = dist / max_dist
        expansion_factor = 1.0 + (3.0 * (1 - norm_dist)**2)
        expanded_pos[node] = (
            center_x + (x - center_x) * expansion_factor,
            center_y + (y - center_y) * expansion_factor
        )
    
    pos = expanded_pos
    SPREAD = 2000
    
    net = Network(height='600px', width='100%', bgcolor='#050505', 
                  font_color='white', cdn_resources='remote')
    net.toggle_physics(False)
    
    galaxy_colors = {
        'main': '#7b2cbf',
        'highlight': '#9d4edd',
        'accent': '#c77dff'
    }
    
    for node in H.nodes():
        x_pos = float(pos[node][0] * SPREAD)
        y_pos = float(pos[node][1] * SPREAD)
        node_strength = strength.get(node, 1)
        node_size = 5 + (np.log10(node_strength + 1) * 20)
        
        # Color based on importance
        if node_strength > np.percentile(list(strength.values()), 90):
            color = galaxy_colors['highlight']
        elif node_strength > np.percentile(list(strength.values()), 70):
            color = galaxy_colors['accent']
        else:
            color = galaxy_colors['main']
        
        net.add_node(
            node,
            x=x_pos,
            y=y_pos,
            label=name_of(node),
            color={'background': color, 'border': '#ffffff', 'highlight': '#ff0054'},
            size=node_size,
            shadow={'enabled': True, 'color': color, 'size': 5, 'x': 0, 'y': 0},
            title=f"Channel: {name_of(node)}\nStrength: {node_strength:.0f}",
            borderWidth=1,
            font={'size': 16, 'color': '#ffffff'}
        )
    
    # 14. Add edges
    for u, v, d in H.edges(data=True):
        w = d.get("weight_raw", 1)
        width = 0.5 + (np.log10(w) * 1.5)
        net.add_edge(u, v, width=width, color='rgba(255, 255, 255, 0.1)')
  
    net.save_graph(html_out_path)
    
    with open(html_out_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    zoom_js = """
    <script type="text/javascript">
    setTimeout(function() {
        network.moveTo({
            scale: 0.05,
            position: {x: 0, y: 2700},
            animation: false
        });
    }, 100);
    </script>
    """
    
    style_fix = """
    <style>
    html, body {
        margin: 0 !important;
        padding: 0 !important;
        width: 100%;
        height: 100%;
        border: 0;
        background: #050505 !important;
        overflow: hidden;
    }
    .card {
        border: none !important;
        outline: none !important;
        border-radius: 0 !important;
        background-color: black;
    }
    #mynetwork {
        width: 100% !important;
        background: #050505 !important;
        border: #000000;
    }
    canvas {
        display: block !important;
        background: #050505 !important;
    }
    </style>
    """
    
    content = content.replace("</head>", style_fix + "\n</head>")
    content = content.replace("<body>", '<body style="background-color:#050505; margin:0; overflow:hidden;">')
    content = content.replace("</body>", f"{zoom_js}\n</body>")
    
    with open(html_out_path, 'w', encoding='utf-8') as f:
        f.write(content)
        f.flush()
    
    print(f"\n✅ Galaxy #{community_id} visualization saved to: {html_out_path}")
    print("=" * 60)
    
    return {
        'community_id': community_id,
        'total_channels': len(galaxy_nodes),
        'total_strength': total_strength,
        'avg_strength': avg_strength,
        'internal_density': internal_density,
        'clustering_coefficient': clustering,
        'total_edges': subgraph_full.number_of_edges(),
        'displayed_nodes': H.number_of_nodes(),
        'displayed_edges': H.number_of_edges(),
        'black_hole': black_hole_name,
        'black_hole_strength': black_hole_strength,
        'top_5_channels': [name_of(ch) for ch in top_5_channels]
    }