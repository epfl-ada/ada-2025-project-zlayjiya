import pandas as pd
import networkx as nx
from collections import Counter
import numpy as np
import matplotlib.pyplot as plt

def filter_edges(edges_df, channel_df, min_subscribers=200_000, min_weight=3):
    """
    Filters the edge list based on subscriber count and edge weight.
   
    """
    print(f"Filtering edges: >{min_subscribers} subs, >{min_weight} weight.")
    channels_df = channel_df.set_index("channel")
    channels_df['big'] = channels_df['subscribers_cc'] > min_subscribers
    channels_filter = channels_df['big'].to_dict()
    
    edges = edges_df[edges_df['src'].map(channels_filter).fillna(False)]
    edges = edges[edges['dst'].map(channels_filter).fillna(False)]
    edges = edges[edges['weight'] > min_weight]
    
    print(f"Filtered down to {len(edges):,} edges.")
    return edges, channels_df

def normalize_edges(edges_df, channels_df, commenter_counts, alpha=0.5, beta=1.0, use_engagement=True):
    """
    Normalizes edge weights based on channel size (subscribers or commenters).
   
    """
    print("Normalizing edge weights...")
    edges_norm = edges_df.copy()
    
    channels_df['commenters_count'] = channels_df.index.map(commenter_counts).fillna(0)
    
    if use_engagement and 'commenters_count' in channels_df.columns and channels_df['commenters_count'].sum() > 0:
        metric = channels_df['commenters_count'].replace(0, 1)
        metric_name = 'commenters (Top-K)'
    else:
        metric = channels_df['subscribers_cc'].replace(0, 1)
        metric_name = 'subscribers'
    
    median_metric = metric.median()
    print(f"Using {metric_name} (median={median_metric:.0f}) for normalization.")
    
    size_factors = (metric / median_metric) ** beta
    size_map = size_factors.to_dict()
    
    normalized_weights = []
    for _, row in edges_df.iterrows():
        source_factor = size_map.get(row['src'], 1.0)
        target_factor = size_map.get(row['dst'], 1.0)
        combined_penalty = (source_factor * target_factor) ** alpha
        norm_weight = row['weight'] / combined_penalty
        normalized_weights.append(norm_weight)
    
    edges_norm['weight_normalized'] = normalized_weights
    edges_norm['weight_raw'] = edges_norm['weight'] 
    edges_norm['weight'] = edges_norm['weight_normalized'] 
    
    return edges_norm

def build_graph(edges_df, channels_df):
    """
    Creates the NetworkX graph and sets node attributes.
   
    """
    print("Building graph from normalized edges...")
    Graphtype = nx.Graph()
    G = nx.from_pandas_edgelist(
        edges_df,
        source='src',
        target="dst",
        edge_attr=["weight", "weight_normalized", "weight_raw"],
        create_using=Graphtype
    )
    nx.set_node_attributes(G, channels_df.to_dict(orient='index'))
    print(f"Graph built: {G.number_of_nodes():,} nodes, {G.number_of_edges():,} edges")
    return G

def find_communities(G, nodes_out_path, comm_out_path):
    """
    Finds the LCC, runs Louvain, calculates metrics, and saves results.
    """
    print("Finding Largest Connected Component (LCC)...")
    comps = sorted(nx.connected_components(G), key=len, reverse=True)
    if not comps:
        raise ValueError("Graph is empty or has no components. Check filters.")
        
    LCC = G.subgraph(comps[0]).copy()
    n, m = G.number_of_nodes(), G.number_of_edges()
    n_lcc, m_lcc = LCC.number_of_nodes(), LCC.number_of_edges()
    print(f"LCC:   {n_lcc:,} nodes, {m_lcc:,} edges  ({(n_lcc/n if n else 0):.1%} of nodes)")

    print("Detecting communities using Louvain...")
    communities = nx.community.louvain_communities(LCC, weight="weight_normalized", seed=42)
    modularity = nx.community.modularity(LCC, communities, weight="weight_normalized")
    print(f"Found {len(communities)} communities (modularity: {modularity:.3f})")
    
    node2comm = {node: cid for cid, comm in enumerate(communities) for node in comm}

    print("Calculating node metrics (PageRank, Strength)...")
    pagerank = nx.pagerank(LCC, weight="weight_raw")
    strength = {u: sum(d["weight_raw"] for _, d in LCC[u].items()) for u in LCC.nodes()}

    node_df = pd.DataFrame({
        "channel_id": list(LCC.nodes()),
        "name_cc": [LCC.nodes[u].get("name_cc", "") for u in LCC.nodes()],
        "category_cc": [LCC.nodes[u].get("category_cc", "") for u in LCC.nodes()],
        "subscribers_cc": [LCC.nodes[u].get("subscribers_cc","") for u in LCC.nodes()],
        "community": [node2comm[u] for u in LCC.nodes()],
        "degree": [LCC.degree(u) for u in LCC.nodes()],
        "strength": [strength[u] for u in LCC.nodes()],
        "pagerank": [pagerank[u] for u in LCC.nodes()],
    })

    comm_summary = node_df.groupby("community").agg(
        n_nodes=("channel_id", "count"),
        total_strength=("strength", "sum"),
        avg_degree=("degree", "mean"),
        avg_strength=("strength", "mean")
    ).sort_values("n_nodes", ascending=False).reset_index()

    node_df.to_csv(nodes_out_path, index=False)
    comm_summary.to_csv(comm_out_path, index=False)
    print(f"\n✓ Saved node metrics and community summary.")
    
    return LCC, communities, node_df, comm_summary

def analyze_communities(LCC, node_df, communities, max_show=5):
    """
    Prints a summary of the top communities.
    """
    print("--- Deep Dive into Top 5 Communities ---")
    node2comm = {node: i for i, comm in enumerate(communities) for node in comm}
    
    ndf = node_df[node_df["channel_id"].isin(LCC.nodes())].copy()
    ndf["community"] = ndf["channel_id"].map(node2comm)
    ndf["category_cc"] = ndf["category_cc"].fillna("Unknown")
    
    ndf["strength"] = ndf["channel_id"].map(
        lambda u: sum(d["weight_raw"] for _, d in LCC[u].items())
    )
    
    for cid, c_nodes in enumerate(communities[:max_show]):
        sub = LCC.subgraph(c_nodes)
        comm_df = ndf[ndf["community"] == cid]
        
        n_nodes = len(c_nodes)
        n_edges = sub.number_of_edges()
        
        cat_counts = Counter(comm_df["category_cc"])
        if not cat_counts: continue
        top_cat, top_cnt = cat_counts.most_common(1)[0]
        
        print("=" * 80)
        print(f"COMMUNITY {cid}")
        print(f"Size: {n_nodes} nodes, {n_edges} edges")
        print(f"Top category: {top_cat} ({top_cnt}/{n_nodes}) ")
        print("-" * 80)
        
        print("Categories:")
        for cat, cnt in cat_counts.most_common(5):
            print(f"  {cat:20s} {cnt:4d} ({cnt/n_nodes:.1%})")
        
        print("-" * 80)
        
        print("Top 5 Channels (by Subscribers):")
        top5 = comm_df.nlargest(5, "strength")
        print(top5[["name_cc", "category_cc", "strength","subscribers_cc"]].to_string(index=False))
        print("=" * 80)
        print()


def visualize_network(LCC, communities, node_df, viz_out_path, n_per_comm=10, min_comm_nodes=20, seed=42):
    """
    Generates and saves the network visualization.
   
    """
    print("Generating network visualization...")
    
    node2comm = {node: cid for cid, comm in enumerate(communities) for node in comm}
    
    strength = {u: sum(d["weight_raw"] for _, d in LCC[u].items()) for u in LCC.nodes()}
    
    meta = node_df.set_index("channel_id").to_dict(orient="index")
    def name_of(uid):
        nm = (meta.get(uid, {}) or {}).get("name_cc") or uid
        return nm if len(str(nm)) > 0 else uid

    top_per_comm = {}
    for cid, nodes_c in enumerate(communities):
        if(len(nodes_c)> min_comm_nodes):
            if not nodes_c: continue
            best = max(nodes_c, key=lambda u: strength.get(u, 0))
            top_per_comm[cid] = name_of(best)

    selected = set()
    for nodes_c in communities:
        if(len(nodes_c) > 5):
            top_nodes = sorted(nodes_c, key=lambda u: strength.get(u, 0), reverse=True)
            selected.update(top_nodes[:n_per_comm])

    edges_to_keep = [
        (u, v) for u, v, d in LCC.edges(data=True)
        if u in selected and v in selected and d.get("weight_raw", 0) >= 2
    ]
    H = LCC.edge_subgraph(edges_to_keep).copy()
    H.remove_nodes_from(list(nx.isolates(H)))
    print(f"Visualization subgraph: {H.number_of_nodes()} nodes, {H.number_of_edges()} edges")

    pos = nx.spring_layout(H, weight="weight_raw", seed=seed, k=2, iterations=50)
    comm_colors = plt.cm.tab20(np.linspace(0, 1, len(communities)))
    node_colors = [comm_colors[node2comm[n]] for n in H.nodes()]
    node_sizes = [30 * np.log10(strength.get(n, 1) + 1) for n in H.nodes()]
    edge_weights = [d.get("weight_raw", 1) for _, _, d in H.edges(data=True)]
    edge_widths = [0.1 + 0.5 * np.log10(w) for w in edge_weights]

    plt.figure(figsize=(14, 10), dpi=150)
    nx.draw_networkx_edges(H, pos, width=edge_widths, alpha=0.15, edge_color="gray")
    nx.draw_networkx_nodes(H, pos, node_color=node_colors, node_size=node_sizes,
                           edgecolors="black", linewidths=0.3, alpha=0.9)

    for cid, color in enumerate(comm_colors):
        if cid in top_per_comm:
            top_name = top_per_comm[cid]
            if len(top_name) > 25: top_name = top_name[:24] + "…"
            plt.scatter([], [], c=[color], s=80, label=f"{top_name}  (C{cid})")

    plt.legend(loc="lower left", ncol=3, fontsize=7, frameon=False,
               title="Communities labeled by top YouTuber")
    plt.title(f"Top {n_per_comm} channels per community (edges ≥ 2)", fontsize=12)
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(viz_out_path, dpi=150, bbox_inches="tight")
    print(f"✓ Saved {viz_out_path}")
    plt.show()