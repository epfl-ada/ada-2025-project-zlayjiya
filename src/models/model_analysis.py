import pandas as pd
import networkx as nx
from collections import Counter
import numpy as np
import matplotlib.pyplot as plt
import random

from src.utils.general_utils import gini

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


import networkx as nx
import igraph as ig
import leidenalg

def run_leiden_on_nx(G, weight='weight', resolution=1.0):
    """
    Runs the Leiden algorithm on a NetworkX graph using the leidenalg backend.
    """
    # 1. Convert NetworkX graph to igraph
    # This is necessary because leidenalg operates on igraph objects
    h = ig.Graph.from_networkx(G)
    
    # 2. Run the Leiden algorithm
    # We use ModularityVertexPartition to mirror Louvain's behavior
    partition = leidenalg.find_partition(
        h, 
        leidenalg.ModularityVertexPartition, 
        weights=h.es[weight] if weight in h.es.attributes() else None,
        resolution_parameter=resolution
    )
    
    # 3. Convert back to NetworkX-style communities (list of sets)
    communities = []
    for community in partition:
        communities.append(set(h.vs[community]['_nx_name']))
        
    return communities

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
    communities = nx.community.louvain_communities(LCC, weight="weight_normalized",seed=42)
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


def visualize_network(LCC, communities, node_df, viz_out_path, n_per_comm=10, min_comm_nodes=20, seed=42,random=False):
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
    if not random:

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
    else:
        selected = set()
        for nodes_c in communities:
            if len(nodes_c) > 5:
                # Random sample without replacement
                sample_size = min(n_per_comm, len(nodes_c))
                random_nodes = np.random.choice(list(nodes_c), size=sample_size, replace=False)
                selected.update(random_nodes)

        edges_to_keep = [(u, v) for u, v, d in LCC.edges(data=True) 
                        if u in selected and v in selected and d.get("weight_raw", 0) >= 2]
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


def categoryDetect(community, video_metadata_df, k_channels=10, n_videos_per_channel=50, 
                   n_topics=4, text_mode='combined', desc_max_chars=200, min_wordcount=5, 
                   max_freq=0.5, passes=10, seed=42, nlp=None):
    """
    Detects topics/categories for a given community using LDA (following Lab 9 methodology).
    Uses spacy for preprocessing and gensim for topic modeling.
    
    Parameters:
    -----------
    community : set or list
        Set of channel IDs forming a community
    video_metadata_df : pd.DataFrame
        DataFrame with columns: 'channel_id', 'title', 'description', 'tags' (optional)
    k_channels : int
        Number of channels to randomly sample from the community
    n_videos_per_channel : int
        Maximum number of videos to sample per channel
    n_topics : int
        Number of topics to extract with LDA
    text_mode : str
        Text source for topic detection:
        - 'title': use only video titles
        - 'description': use only descriptions
        - 'tags': use only tags
        - 'combined': use title + tags + truncated description (recommended by TA)
    desc_max_chars : int
        Maximum characters to keep from description when using 'combined' mode
    min_wordcount : int
        Minimum word count for dictionary filtering
    max_freq : float
        Maximum document frequency for dictionary filtering
    passes : int
        Number of passes for LDA training
    seed : int
        Random seed for reproducibility
    nlp : spacy model (optional)
        Spacy NLP model for text processing. If None, will try to load 'en_core_web_sm'
        
    Returns:
    --------
    dict with keys:
        - 'topics': list of topics (each topic is a list of (word, weight) tuples)
        - 'model': the trained LDA model
        - 'corpus': the corpus used
        - 'dictionary': the dictionary used
        - 'n_videos': number of videos analyzed
        - 'sampled_channels': list of channel IDs sampled
    """
    try:
        import spacy
        from gensim.models.phrases import Phrases
        from gensim.corpora import Dictionary
        from gensim.models import LdaMulticore
    except ImportError as e:
        print(f"Missing required library: {e}")
        print("Install with: pip install spacy gensim")
        return {'topics': [], 'n_videos': 0, 'sampled_channels': []}
    
    print(f"=== Topic Detection for Community ({len(community)} channels) ===")
    
    # Set random seed
    random.seed(seed)
    np.random.seed(seed)
    
    # Load spacy model
    if nlp is None:
        try:
            nlp = spacy.load('en_core_web_sm', disable=['parser', 'ner'])
        except:
            print("Spacy model 'en_core_web_sm' not found")
            print("Install with: python -m spacy download en_core_web_sm")
            return {'topics': [], 'n_videos': 0, 'sampled_channels': []}
    
    STOPWORDS = spacy.lang.en.stop_words.STOP_WORDS
    
    # Sample channels
    community_list = list(community)
    k_actual = min(k_channels, len(community_list))
    sampled_channels = random.sample(community_list, k_actual)
    print(f"Sampled {k_actual} channels from community")
    
    # Filter and sample videos
    if 'channel_id' not in video_metadata_df.columns:
        print("No 'channel_id' column found in video metadata")
        return {'topics': [], 'n_videos': 0, 'sampled_channels': sampled_channels}
    
    videos_from_community = video_metadata_df[
        video_metadata_df['channel_id'].isin(sampled_channels)
    ].copy()
    
    if len(videos_from_community) == 0:
        print("No videos found for sampled channels")
        return {'topics': [], 'n_videos': 0, 'sampled_channels': sampled_channels}
    
    # Sample videos per channel
    sampled_videos = []
    for channel in sampled_channels:
        channel_videos = videos_from_community[videos_from_community['channel_id'] == channel]
        n_sample = min(n_videos_per_channel, len(channel_videos))
        if n_sample > 0:
            sampled = channel_videos.sample(n=n_sample, random_state=seed)
            sampled_videos.append(sampled)
    
    if not sampled_videos:
        print("No videos sampled")
        return {'topics': [], 'n_videos': 0, 'sampled_channels': sampled_channels}
    
    videos_sample = pd.concat(sampled_videos, ignore_index=True)
    print(f"Sampled {len(videos_sample)} videos")
    
    # Get texts based on text_mode
    def combine_text_fields(row):
        """Combine title + tags + truncated description (TA recommended approach)"""
        parts = []
        
        # Add title
        title = str(row.get('title', '')).strip()
        if title:
            parts.append(title)
        
        # Add tags (comma-separated string)
        tags = str(row.get('tags', '')).strip()
        if tags:
            # Tags are usually comma-separated, convert to space-separated
            tags_cleaned = tags.replace(',', ' ')
            parts.append(tags_cleaned)
        
        # Add truncated description
        desc = str(row.get('description', '')).strip()
        if desc:
            # Truncate description to first N characters
            desc_truncated = desc[:desc_max_chars]
            parts.append(desc_truncated)
        
        return ' '.join(parts)
    
    if text_mode == 'combined':
        print(f"Using combined mode: title + tags + description (truncated to {desc_max_chars} chars)")
        texts = videos_sample.apply(combine_text_fields, axis=1).tolist()
    elif text_mode == 'title':
        if 'title' not in videos_sample.columns:
            print("Column 'title' not found")
            return {'topics': [], 'n_videos': 0, 'sampled_channels': sampled_channels}
        texts = videos_sample['title'].fillna('').astype(str).tolist()
    elif text_mode == 'description':
        if 'description' not in videos_sample.columns:
            print("Column 'description' not found")
            return {'topics': [], 'n_videos': 0, 'sampled_channels': sampled_channels}
        texts = videos_sample['description'].fillna('').astype(str).tolist()
    elif text_mode == 'tags':
        if 'tags' not in videos_sample.columns:
            print("Column 'tags' not found")
            return {'topics': [], 'n_videos': 0, 'sampled_channels': sampled_channels}
        texts = videos_sample['tags'].fillna('').astype(str).tolist()
    else:
        print(f"Unknown text_mode: {text_mode}. Use 'title', 'description', 'tags', or 'combined'")
        return {'topics': [], 'n_videos': 0, 'sampled_channels': sampled_channels}
    
    texts = [t for t in texts if len(t.strip()) > 0]
    
    if len(texts) == 0:
        print("No valid texts")
        return {'topics': [], 'n_videos': 0, 'sampled_channels': sampled_channels}
    
    print(f"Processing {len(texts)} texts with spacy...")
    
    # Preprocess with spacy
    processed_docs = []
    for doc in nlp.pipe(texts, n_process=1, batch_size=50):
        # Lemmatize, remove punctuation and stopwords
        doc_tokens = [token.lemma_ for token in doc if token.is_alpha and not token.is_stop]
        # Remove stopwords and keep only words of length 3+
        doc_tokens = [token for token in doc_tokens if token not in STOPWORDS and len(token) > 2]
        processed_docs.append(doc_tokens)
    
    docs = processed_docs
    print(f"Preprocessed {len(docs)} documents")
    
    # Add bigrams
    print("Adding bigrams...")
    bigram = Phrases(docs, min_count=5)
    for idx in range(len(docs)):
        for token in bigram[docs[idx]]:
            if '_' in token:
                docs[idx].append(token)
    
    # Create dictionary and corpus
    print("Creating dictionary and corpus...")
    dictionary = Dictionary(docs)
    dictionary.filter_extremes(no_below=min_wordcount, no_above=max_freq)
    corpus = [dictionary.doc2bow(doc) for doc in docs]
    
    print(f'Number of unique tokens: {len(dictionary)}')
    print(f'Number of documents: {len(corpus)}')
    
    if len(dictionary) == 0:
        print("Dictionary is empty after filtering")
        return {'topics': [], 'n_videos': len(texts), 'sampled_channels': sampled_channels}
    
    # Train LDA model
    print(f"Training LDA model with {n_topics} topics...")
    try:
        model = LdaMulticore(
            corpus=corpus,
            num_topics=n_topics,
            id2word=dictionary,
            workers=4,
            passes=passes,
            random_state=seed
        )
        
        # Extract topics
        print(f"\nDetected {n_topics} topics:\n")
        topics = []
        for topic_id in range(n_topics):
            topic_words = model.show_topic(topic_id, topn=10)
            topics.append(topic_words)
            words_str = ', '.join([f"{word}" for word, _ in topic_words[:5]])
            print(f"Topic {topic_id}: {words_str}")
        
        return {
            'topics': topics,
            'model': model,
            'corpus': corpus,
            'dictionary': dictionary,
            'n_videos': len(texts),
            'sampled_channels': sampled_channels,
            'docs': docs
        }
    
    except Exception as e:
        print(f"LDA training failed: {e}")
        return {'topics': [], 'n_videos': len(texts), 'sampled_channels': sampled_channels}



def visualize_core_network(
    LCC,
    communities,
    node_df,
    viz_out_path,
    n_per_comm=15,
    num_top_communities=5,
    weight_threshold=5,
    seed=42,
):
    """
    Zoom into the “galactic core” by plotting only the largest communities with thicker edges.
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
        if top_nodes:
            top_per_comm[cid] = name_of(top_nodes[0])

    edges_to_keep = [
        (u, v) for u, v, d in LCC.edges(data=True)
        if u in selected and v in selected and d.get("weight_raw", 0) >= weight_threshold
    ]

    H = LCC.edge_subgraph(edges_to_keep).copy()
    H.remove_nodes_from(list(nx.isolates(H)))
    print(f"Core visualization: {H.number_of_nodes()} nodes, {H.number_of_edges()} edges")

    pos = nx.spring_layout(H, weight="weight_raw", seed=seed, k=1.5, iterations=100)

    comm_colors = plt.cm.Set1(np.linspace(0, 1, num_top_communities))
    node_colors = [comm_colors[node2comm[n]] for n in H.nodes()]
    node_sizes = [50 * np.log10(strength.get(n, 1) + 10) for n in H.nodes()]

    plt.figure(figsize=(16, 12), facecolor='white')
    nx.draw_networkx_edges(H, pos, width=0.5, alpha=0.2, edge_color="black")
    nx.draw_networkx_nodes(
        H, pos, node_color=node_colors, node_size=node_sizes,
        edgecolors="black", linewidths=0.5, alpha=0.8
    )

    label_targets = {}
    for nodes_c in core_communities:
        top_3 = sorted(nodes_c, key=lambda u: strength.get(u, 0), reverse=True)[:3]
        for node in top_3:
            if node in H:
                label_targets[node] = name_of(node)

    nx.draw_networkx_labels(H, pos, labels=label_targets, font_size=8, font_weight='bold')

    plt.title(
        f"Voyage into the Core: Interaction between Top {num_top_communities} Galaxies",
        fontsize=15,
    )
    plt.axis("off")
    plt.savefig(viz_out_path, dpi=300, bbox_inches="tight")
    plt.show()


def visualize_core_interactive(
    LCC,
    communities,
    node_df,
    html_out_path,
    num_top_communities=5,
    n_per_comm=20,
    seed=42,
):
    """
    Interactive PyVis view of the core communities with a small legend overlay.
    """
    try:
        from pyvis.network import Network
        import matplotlib.colors as mcolors
    except ImportError as e:
        raise ImportError("pyvis is required for visualize_core_interactive. Install with `pip install pyvis`.") from e

    print(f"🔭 Zooming into the top {num_top_communities} galaxies...")

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

    edges_to_keep = [
        (u, v) for u, v, d in LCC.edges(data=True)
        if u in selected and v in selected and d.get("weight_raw", 0) >= 3
    ]
    H = LCC.edge_subgraph(edges_to_keep).copy()
    H.remove_nodes_from(list(nx.isolates(H)))

    pos = nx.spring_layout(H, weight="weight_raw", seed=seed, k=5.0, iterations=200)
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
    x_range = max(p[0] for p in pos.values()) - min(p[0] for p in pos.values())
    y_range = max(p[1] for p in pos.values()) - min(p[1] for p in pos.values())

    net = Network(height='850px', width='100%', bgcolor='#ffffff', font_color='black', cdn_resources='remote')
    net.toggle_physics(False)

    comm_colors = plt.cm.Set1(np.linspace(0, 1, num_top_communities))
    SPREAD = 4500

    for node in H.nodes():
        cid = node2comm[node]
        color = mcolors.to_hex(comm_colors[cid])
        x = ((pos[node][0] - min(p[0] for p in pos.values())) / x_range - 0.5) * SPREAD
        y = ((pos[node][1] - min(p[1] for p in pos.values())) / y_range - 0.5) * SPREAD
        size = 12 + (np.log10(strength.get(node, 1) + 1) * 15)
        net.add_node(
            node, x=x, y=y, label=name_of(node), color=color, size=size,
            title=f"Channel: {name_of(node)}<br>Galaxy Cluster: {cid}",
            borderWidth=1.5, font={'size': 20, 'strokeWidth': 3, 'strokeColor': '#ffffff'}
        )

    for u, v, d in H.edges(data=True):
        w = d.get("weight_raw", 1)
        width = 0.8 + (np.log10(w) * 2.0)
        net.add_edge(u, v, width=width, color='rgba(150,150,150,0.25)')

    legend_html = """
    <div style="position: absolute; top: 15px; left: 15px; width: 230px; background: rgba(255,255,255,0.9); 
                border: 2px solid #333; padding: 15px; font-family: 'Segoe UI', sans-serif; z-index: 1000; border-radius: 10px;">
        <b style="font-size: 14px; display: block; margin-bottom: 10px; border-bottom: 1px solid #333;">Dominant Galactic Hubs</b>
    """
    for cid, nodes_c in enumerate(core_communities):
        best = max(nodes_c, key=lambda u: strength.get(u, 0))
        color = mcolors.to_hex(comm_colors[cid])
        name = name_of(best)
        legend_html += f'<div style="margin-bottom: 6px;"><span style="color:{color}; font-size: 18px;">●</span> <b>Hub {cid}:</b> {name}</div>'
    legend_html += "</div>"

    net.save_graph(html_out_path)
    with open(html_out_path, 'r', encoding='utf-8') as f:
        content = f.read().replace('<body>', f'<body>{legend_html}')
    with open(html_out_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✅ Core-only interactive map saved: {html_out_path}")




def compute_comm_flows(edges_normalized, node_df, comm_summary):
    """
    Build community-to-community flow matrices and mobility metrics.
    Returns a dict with edges_comm, pair_strength, flow_norm, flow_share, communities_sorted, mobility_df.
    """
    # Map channel -> community
    channel_to_comm = node_df.set_index("channel_id")["community"]

    edges_comm = (
        edges_normalized[["src", "dst", "weight", "weight_raw"]]
        .assign(
            src_comm=lambda df: df["src"].map(channel_to_comm),
            dst_comm=lambda df: df["dst"].map(channel_to_comm),
        )
        .dropna(subset=["src_comm", "dst_comm"])
        .astype({"src_comm": int, "dst_comm": int})
    )
    edges_comm["is_cross"] = edges_comm["src_comm"] != edges_comm["dst_comm"]

    communities_sorted = sorted(node_df["community"].unique())
    pair_strength = (
        edges_comm.groupby(["src_comm", "dst_comm"])[["weight", "weight_raw"]]
        .sum()
        .reset_index()
    )

    flow_norm = pd.DataFrame(0.0, index=communities_sorted, columns=communities_sorted)
    flow_raw = pd.DataFrame(0.0, index=communities_sorted, columns=communities_sorted)
    for _, row in pair_strength.iterrows():
        a, b, w_norm, w_raw = int(row.src_comm), int(row.dst_comm), row.weight, row.weight_raw
        flow_norm.loc[a, b] += w_norm
        flow_raw.loc[a, b] += w_raw

    flow_norm_no_diag = flow_norm.copy()
    np.fill_diagonal(flow_norm_no_diag.values, 0)
    flow_share = flow_norm_no_diag.div(flow_norm_no_diag.sum(axis=1), axis=0).fillna(0)

    total_strength = (
        edges_comm.groupby("src_comm")["weight"].sum()
        .add(edges_comm.groupby("dst_comm")["weight"].sum(), fill_value=0)
    )
    cut_cross = edges_comm[edges_comm["is_cross"]].groupby(["src_comm", "dst_comm"])["weight"].sum()
    cut_per_comm = cut_cross.groupby(level=0).sum().add(cut_cross.groupby(level=1).sum(), fill_value=0)
    external_share = (cut_per_comm / total_strength).fillna(0)

    mobility_rows = []
    for cid in communities_sorted:
        row = flow_share.loc[cid]
        dests = row[row > 0]
        if dests.empty:
            entropy = 0.0
            top_share = 0.0
            gini_out = 0.0
        else:
            p = dests / dests.sum()
            entropy = -np.sum(p * np.log2(p))
            top_share = p.max()
            gini_out = gini(p)
        mobility_rows.append(
            {
                "community": cid,
                "external_share": float(external_share.get(cid, 0)),
                "entropy_out": float(entropy),
                "gini_out": float(gini_out),
                "top_dest_share": float(top_share),
            }
        )

    mode_category = node_df.groupby("community")["category_cc"].agg(
        lambda s: s.mode().iat[0] if not s.mode().empty else "Unknown"
    )

    mobility_df = (
        pd.DataFrame(mobility_rows)
        .merge(comm_summary[["community", "n_nodes", "avg_degree"]], on="community", how="left")
        .merge(mode_category.rename("top_category"), on="community", how="left")
        .sort_values(["external_share", "entropy_out"])
    )

    return {
        "edges_comm": edges_comm,
        "pair_strength": pair_strength,
        "flow_norm": flow_norm,
        "flow_share": flow_share,
        "communities_sorted": communities_sorted,
        "mobility_df": mobility_df,
    }


def top_destinations(flow_share, communities_sorted):
    """
    Rank top partner per community (by share of outgoing flow).
    """
    rows = []
    for cid in communities_sorted:
        row = flow_share.loc[cid]
        if row.sum() == 0:
            continue
        top_vals = row.sort_values(ascending=False).head(3)
        rows.append(
            {
                "community": cid,
                "top_partner": int(top_vals.index[0]),
                "share_to_top": float(top_vals.iloc[0]),
                "second_partner": int(top_vals.index[1]) if len(top_vals) > 1 else None,
                "share_to_second": float(top_vals.iloc[1]) if len(top_vals) > 1 else None,
            }
        )
    return pd.DataFrame(rows).sort_values("share_to_top", ascending=False)


def plot_chord_backbone(pair_strength, communities_sorted, top_n=100, out_path="reports/figures/community_chord_simple.png"):
    """
    Plot undirected backbone of community flows (chord-like arcs).
    """
    import matplotlib.pyplot as plt


    flows = pair_strength.copy()
    flows = flows[flows["src_comm"] != flows["dst_comm"]]
    flows["a"] = flows[["src_comm", "dst_comm"]].min(axis=1)
    flows["b"] = flows[["src_comm", "dst_comm"]].max(axis=1)
    flows = flows.groupby(["a", "b"], as_index=False)["weight"].sum()
    flows = flows.rename(columns={"a": "c1", "b": "c2"})
    flows = flows.sort_values("weight", ascending=False).head(top_n)

    order = sorted(communities_sorted)
    theta = np.linspace(0, 2 * np.pi, len(order), endpoint=False)
    coords = {c: (np.cos(t), np.sin(t)) for c, t in zip(order, theta)}

    w = flows["weight"]
    w_norm = (w - w.min()) / (w.max() - w.min() + 1e-9)
    widths = 1.0 + 6 * w_norm
    colors = plt.cm.viridis(0.2 + 0.8 * w_norm)
    alphas = 0.25 + 0.65 * w_norm
    sm = plt.cm.ScalarMappable(cmap=plt.cm.viridis, norm=plt.Normalize(vmin=w.min(), vmax=w.max()))
    sm.set_array([])

    fig, ax = plt.subplots(figsize=(11, 11))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    for (c1, c2, weight), lw, col, a in zip(flows[["c1", "c2", "weight"]].itertuples(index=False, name=None), widths, colors, alphas):
        x0, y0 = coords[c1]
        x1, y1 = coords[c2]
        ctrl = np.array([0, 0])
        t = np.linspace(0, 1, 150)
        curve = (1 - t)[:, None] ** 2 * np.array([x0, y0]) + 2 * (1 - t)[:, None] * t[:, None] * ctrl + t[:, None] ** 2 * np.array([x1, y1])
        ax.plot(curve[:, 0], curve[:, 1], color=col, alpha=a, linewidth=lw, solid_capstyle="round")

    for c in order:
        x, y = coords[c]
        ax.scatter(x, y, s=150, color="white", edgecolor="black", zorder=3)
        ax.text(x * 1.12, y * 1.12, f"C{c}", ha="center", va="center", fontsize=11, weight="bold")

    ax.set_aspect("equal")
    ax.axis("off")
    plt.title("Flux inter-community", fontsize=12)
    cbar = plt.colorbar(sm, ax=ax, fraction=0.035, pad=0.02)
    cbar.set_label("Undirected flow weight (yellow = strongest)", fontsize=9)
    plt.text(0, -1.18, "Edge width scales with flow strength", ha="center", va="center", fontsize=6)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.show()

    # Affiche un petit tableau affichant les 5 liens les plus forts juste après le plot
    flows.sort_values("weight", ascending=False).head(5)
    


def find_echo_candidates(mobility_df, ext_quantile=0.25, entropy_quantile=0.5):
    """
    Identify low-openness, low-diversity communities and return (candidates, q_ext, q_ent).
    """
    q_ext = mobility_df["external_share"].quantile(ext_quantile)
    q_ent = mobility_df["entropy_out"].quantile(entropy_quantile)
    echo_candidates = mobility_df[
        (mobility_df["external_share"] <= q_ext) & (mobility_df["entropy_out"] <= q_ent)
    ].copy()
    echo_candidates = echo_candidates.sort_values(["external_share", "entropy_out"])
    return echo_candidates, q_ext, q_ent


def plot_echo_share(mobility_df, echo_candidates, q_ext, out_path="reports/figures/echo_chamber_external_share.png"):
    """
    Plot external share bar chart highlighting echo candidates.
    """
    import matplotlib.pyplot as plt

    colors = ["#d62728" if es <= q_ext else "#1f77b4" for es in mobility_df["external_share"]]
    plt.figure(figsize=(12, 5))
    plt.bar(mobility_df["community"].astype(str), mobility_df["external_share"], color=colors)
    plt.axhline(q_ext, color="black", linestyle="--", label="25e percentile share")
    plt.ylabel("Part des flux sortants")
    plt.xlabel("ID communauté")
    plt.title("External share par communauté (plus bas = plus fermé)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.show()


def compute_bridge_channels(LCC, node_df, communities, betweenness_k=800, cross_share_min=0.5, cross_strength_min=1000):
    """
    Compute bridge channels and aggregated category info.
    """
    # Betweenness
    G_bt = LCC.copy()
    for u, v, d in G_bt.edges(data=True):
        w = d.get("weight", 1.0)
        d["length"] = 1 / (w + 1e-9)
    betweenness = nx.betweenness_centrality(G_bt, k=betweenness_k, weight="length", seed=42)
    node_df = node_df.copy()
    node_df["betweenness"] = node_df["channel_id"].map(betweenness).fillna(0)

    comm_map = node_df.set_index("channel_id")["community"].to_dict()
    bridge_rows = []
    for u in LCC.nodes():
        total_raw = 0.0
        cross_raw = 0.0
        for v, data in LCC[u].items():
            w = data.get("weight_raw", data.get("weight", 0))
            total_raw += w
            if comm_map.get(u) != comm_map.get(v):
                cross_raw += w
        cross_share = cross_raw / total_raw if total_raw > 0 else 0.0
        bridge_rows.append(
            {
                "channel_id": u,
                "name": LCC.nodes[u].get("name_cc", u),
                "community": comm_map.get(u),
                "total_strength": total_raw,
                "cross_strength": cross_raw,
                "cross_share": cross_share,
                "degree": LCC.degree(u),
                "betweenness": betweenness.get(u, 0.0),
            }
        )

    bridge_df = pd.DataFrame(bridge_rows).sort_values(
        ["cross_share", "betweenness", "cross_strength"], ascending=[False, False, False]
    )
    bridge_top = bridge_df[
        (bridge_df["cross_share"] >= cross_share_min) & (bridge_df["cross_strength"] > cross_strength_min)
    ]

    bridge_top_cat = bridge_top.merge(node_df[["channel_id", "category_cc"]], on="channel_id", how="left")

    top_channels = (
        bridge_df.merge(node_df[["channel_id", "category_cc"]], on="channel_id", how="left")
        .sort_values(
            ["community", "cross_share", "betweenness", "cross_strength"], ascending=[True, False, False, False]
        )
        .groupby("community")
        .head(10)
    )

    agg = (
        bridge_top_cat.groupby(["community", "category_cc"])
        .agg(
            n_channels=("channel_id", "count"),
            cross_strength=("cross_strength", "sum"),
            avg_cross_share=("cross_share", "mean"),
        )
        .reset_index()
    )
    agg["share_strength"] = agg.groupby("community")["cross_strength"].transform(lambda s: s / s.sum())

    return {
        "bridge_df": bridge_df,
        "bridge_top": bridge_top,
        "top_channels": top_channels,
        "bridge_top_cat": bridge_top_cat,
        "agg": agg,
    }


def plot_bridge_top_channels(top_channels, topN=10, out_path="reports/figures/bridge_channels_static_overview.png"):
    """
    Static multipanel barplot of top bridge channels per community.
    """
    import seaborn as sns
    

    communities = sorted(top_channels["community"].unique())
    palette = sns.color_palette("tab20", len(communities))
    comm_color = {c: palette[i % len(palette)] for i, c in enumerate(communities)}

    fig, axes = plt.subplots(
        nrows=len(communities), figsize=(10, max(4, 2 * len(communities))), constrained_layout=True, sharex=False
    )
    if len(communities) == 1:
        axes = [axes]

    for ax, comm in zip(axes, communities):
        data = top_channels[top_channels["community"] == comm].sort_values("cross_strength", ascending=False).head(topN)
        if data.empty:
            ax.set_axis_off()
            continue
        sns.barplot(data=data, y="name", x="cross_strength", color=comm_color.get(comm, "#1f77b4"), ax=ax)
        for i, row in data.reset_index().iterrows():
            ax.text(row["cross_strength"] * 1.01, i, f"{row['cross_share']:.2f}", va="center", fontsize=7)
        ax.set_ylabel("Channel")
        ax.set_xlabel("Cross strength")
        ax.set_title(f"Top {topN} bridge channels — comm {comm}")

    plt.suptitle("Bridge channels by community (static overview)", fontsize=14)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.show()


def plot_bridge_categories(agg, out_path="reports/figures/bridge_categories_top3.png"):
    """
    Plot top 3 bridge categories per community.
    """
    import seaborn as sns
    import matplotlib.pyplot as plt

    cat_top3 = (
        agg.sort_values(["community", "cross_strength"], ascending=[True, False]).groupby("community").head(3)
    )

    plt.figure(figsize=(10, 5))
    sns.barplot(data=cat_top3, x="community", y="cross_strength", hue="category_cc", palette="tab10")
    plt.ylabel("Cross strength (bridges)")
    plt.xlabel("Community")
    plt.title("Top bridge categories (cross strength)")
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.show()


def plot_directional_flows(flow_norm, top_n=20, out_path="reports/figures/bridge_community_topflows.png"):
    """
    Plot strongest directional flows between communities (normalized weights).
    """
    import seaborn as sns
    import matplotlib.pyplot as plt

    flow_long = flow_norm.stack().reset_index()
    flow_long.columns = ["community_src", "community_dst", "weight"]
    flow_long = flow_long[flow_long["community_src"] != flow_long["community_dst"]]
    flow_long = flow_long[flow_long["weight"] > 0]
    top_flows = flow_long.sort_values("weight", ascending=False).head(top_n)

    plt.figure(figsize=(10, 6))
    sns.barplot(
        data=top_flows,
        y=top_flows.apply(lambda r: f"C{int(r.community_src)} → C{int(r.community_dst)}", axis=1),
        x="weight",
        hue="weight",
        palette="crest",
    )
    plt.xlabel("Normalized flow")
    plt.ylabel("Source → destination")
    plt.title("Top cross-community flows (normalized)")
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.show()

