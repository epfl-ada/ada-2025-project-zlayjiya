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
        from gensim.models.phrases import Phrases, Phraser
        from gensim.corpora import Dictionary
        from gensim.models import LdaModel
        import re
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
    
    # YouTube-specific stopwords to filter common noise
    YOUTUBE_STOPWORDS = {
        'video', 'videos', 'watch', 'subscribe', 'channel', 'like', 'comment',
        'share', 'new', 'best', 'top', 'official', 'full', 'hd', 'hq', '4k',
        'episode', 'part', 'season', 'trailer', 'clip', 'scene', 'movie',
        'free', 'download', 'link', 'description', 'follow', 'instagram',
        'twitter', 'facebook', 'tiktok', 'snapchat', 'social', 'media',
        'http', 'https', 'www', 'com', 'bit', 'ly', 'youtu', 'youtube',
        'please', 'thank', 'thanks', 'hello', 'hey', 'today', 'day', 'week',
        'year', 'time', 'thing', 'stuff', 'lot', 'way', 'guy', 'people',
        'world', 'life', 'really', 'actually', 'literally', 'basically',
        'amazing', 'awesome', 'insane', 'crazy', 'epic', 'ultimate'
    }
    ALL_STOPWORDS = STOPWORDS | YOUTUBE_STOPWORDS
    
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
    
    # FIX: Handle NaN values properly (avoid "nan" tokens)
    for col in ['title', 'description', 'tags']:
        if col in videos_sample.columns:
            videos_sample[col] = videos_sample[col].fillna('').astype(str)
    
    # URL pattern for stripping links from descriptions
    URL_PATTERN = re.compile(r'https?://\S+|www\.\S+')
    
    # Get texts based on text_mode
    def combine_text_fields(row):
        """Combine title + tags + truncated description (TA recommended approach)"""
        parts = []
        
        # Add title
        title = row.get('title', '').strip()
        if title and title != 'nan':
            parts.append(title)
        
        # Add tags (comma-separated string)
        tags = row.get('tags', '').strip()
        if tags and tags != 'nan':
            tags_cleaned = tags.replace(',', ' ')
            parts.append(tags_cleaned)
        
        # Add truncated description (strip URLs)
        desc = row.get('description', '').strip()
        if desc and desc != 'nan':
            desc = URL_PATTERN.sub('', desc)  # Strip URLs
            desc_truncated = desc[:desc_max_chars]
            parts.append(desc_truncated)
        
        return ' '.join(parts)
    
    def combine_title_desc(row):
        """Combine title + truncated description only (no tags - less noise)"""
        parts = []
        title = row.get('title', '').strip()
        if title and title != 'nan':
            parts.append(title)
        desc = row.get('description', '').strip()
        if desc and desc != 'nan':
            desc = URL_PATTERN.sub('', desc)  # Strip URLs
            desc_truncated = desc[:desc_max_chars]
            parts.append(desc_truncated)
        return ' '.join(parts)
    
    if text_mode == 'combined':
        print(f"Using combined mode: title + tags + description (truncated to {desc_max_chars} chars)")
        texts = videos_sample.apply(combine_text_fields, axis=1).tolist()
    elif text_mode == 'title_desc':
        print(f"Using title_desc mode: title + description (truncated to {desc_max_chars} chars) - NO TAGS")
        texts = videos_sample.apply(combine_title_desc, axis=1).tolist()
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
        print(f"Unknown text_mode: {text_mode}. Use 'title', 'title_desc', 'description', 'tags', or 'combined'")
        return {'topics': [], 'n_videos': 0, 'sampled_channels': sampled_channels}
    
    texts = [t for t in texts if len(t.strip()) > 0]
    
    if len(texts) == 0:
        print("No valid texts")
        return {'topics': [], 'n_videos': 0, 'sampled_channels': sampled_channels}
    
    print(f"Processing {len(texts)} texts with spacy...")
    
    # POS tags to keep (content words only - much cleaner topics)
    KEEP_POS = {"NOUN", "PROPN", "ADJ"}
    
    # Preprocess with spacy
    processed_docs = []
    for doc in nlp.pipe(texts, n_process=1, batch_size=50):
        # Filter by POS, lemmatize, remove punctuation
        doc_tokens = [
            token.lemma_.lower() 
            for token in doc 
            if token.is_alpha and token.pos_ in KEEP_POS and not token.is_stop
        ]
        # Remove stopwords (including YouTube-specific) and keep only words of length 3+
        doc_tokens = [token for token in doc_tokens if token not in ALL_STOPWORDS and len(token) > 2]
        processed_docs.append(doc_tokens)
    
    # Drop empty docs after preprocessing (reduces noise)
    docs = [d for d in processed_docs if len(d) > 0]
    print(f"Preprocessed {len(docs)} documents (dropped {len(processed_docs) - len(docs)} empty docs)")
    
    if len(docs) == 0:
        print("All documents were empty after preprocessing")
        return {'topics': [], 'n_videos': len(texts), 'sampled_channels': sampled_channels}
    
    # Transform with bigrams (not append - avoids double counting)
    print("Adding bigrams...")
    bigram = Phrases(docs, min_count=5, threshold=10)
    bigram_mod = Phraser(bigram)
    docs = [bigram_mod[doc] for doc in docs]
    
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
    
    # Train LDA model (using LdaModel for alpha/eta='auto' support)
    print(f"Training LDA model with {n_topics} topics...")
    try:
        model = LdaModel(
            corpus=corpus,
            num_topics=n_topics,
            id2word=dictionary,
            passes=passes,
            random_state=seed,
            alpha='auto',  # Learn optimal alpha (improves topic separation)
            eta='auto'     # Learn optimal eta (improves word distribution)
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


#from src.models.model_analysis import plot_interactive_community_edges
import numpy as np
import pandas as pd
import plotly.graph_objects as go


def chord_diagram_html_slider(
    flows: pd.DataFrame,
    communities_sorted,
    community_sizes=None,
    top_k=150,
    title="",
    out_path=None,
    slider_steps=None,  # List of n_top values to include, e.g. [10, 20, 30, 40, 52]
):
    """
    Chord diagram with a NATIVE PLOTLY SLIDER that works in exported HTML.
    Uses trace visibility toggling for clean switching between views.
    
    Parameters:
    -----------
    slider_steps : list, optional
        List of community counts to include in slider. Default: [10, 15, 20, 30, 40, all]
    """
    import plotly.graph_objects as go
    
    # Theme - pure black background
    bg = "#000000"
    font = "'-apple-system','BlinkMacSystemFont','Segoe UI',Roboto,Helvetica,Arial,sans-serif"
    
    palette = [
        "#7C3AED", "#06B6D4", "#F97316", "#22C55E", "#E11D48",
        "#FACC15", "#A855F7", "#14B8A6", "#60A5FA", "#FB7185",
        "#34D399", "#F59E0B", "#818CF8", "#2DD4BF", "#F472B6",
    ]
    
    order = list(communities_sorted)
    idx_map = {c: i for i, c in enumerate(order)}
    n_total = len(order)
    
    # Calculate community sizes if not provided
    if community_sizes is None:
        community_sizes = {}
        for c in order:
            in_edges = len(flows[flows["c2"] == c]) if "c2" in flows.columns else 0
            out_edges = len(flows[flows["c1"] == c]) if "c1" in flows.columns else 0
            community_sizes[c] = float(in_edges + out_edges)
        if sum(community_sizes.values()) == 0:
            community_sizes = {c: 1.0 for c in order}
    
    # Sort communities by size
    sorted_communities = sorted(community_sizes.items(), key=lambda x: x[1], reverse=True)
    
    # Default slider steps
    if slider_steps is None:
        slider_steps = [10, 15, 20, 30, 40, n_total]
        slider_steps = [s for s in slider_steps if s <= n_total]
        if n_total not in slider_steps:
            slider_steps.append(n_total)
    slider_steps = sorted(set(slider_steps))
    
    # Prepare original flows
    original_flows = flows.copy()
    original_flows = original_flows[original_flows["c1"] != original_flows["c2"]].copy()
    
    def arc(theta0, theta1, r=1.05, k=60):
        tt = np.linspace(theta0, theta1, k)
        return (r*np.cos(tt), r*np.sin(tt))
    
    def build_traces_for_n(n_top, visible=True):
        traces = []
        edge_metadata = []  # Track which communities each edge connects
        arc_metadata = []   # Track which community each arc belongs to
        
        top_n_list = [c for c, _ in sorted_communities[:n_top]]
        top_n_set = set(top_n_list)
        filtered_flows = original_flows[original_flows["c1"].isin(top_n_set) & original_flows["c2"].isin(top_n_set)].copy()
        local_idx_map = {c: i for i, c in enumerate(top_n_list)}
        def local_canon_key(a, b):
            return (a, b) if local_idx_map[a] < local_idx_map[b] else (b, a)
        pairs = {}
        for _, row in filtered_flows.iterrows():
            key = local_canon_key(row["c1"], row["c2"])
            pairs[key] = pairs.get(key, 0) + float(row["weight"])
        df = pd.DataFrame([{"c1": k[0], "c2": k[1], "weight": v} for k, v in pairs.items()])
        df = df.sort_values("weight", ascending=False).head(top_k).reset_index(drop=True)
        if len(df) == 0:
            return traces, [], []
        w = df["weight"].values
        wmin, wmax = float(w.min()), float(w.max())
        
        # LOG SCALE normalization for edge weights
        log_wmin = np.log1p(wmin)
        log_wmax = np.log1p(wmax)
        def norm_log(x):
            return (np.log1p(x) - log_wmin) / (log_wmax - log_wmin + 1e-12)
        
        local_sizes = {}
        for c in top_n_list:
            in_e = len(filtered_flows[filtered_flows["c2"] == c])
            out_e = len(filtered_flows[filtered_flows["c1"] == c])
            local_sizes[c] = float(in_e + out_e)
        gap = 0.015
        total_gap = n_top * gap
        available_angle = 2 * np.pi - total_gap
        total_size = sum(local_sizes.values())
        comm = {}
        t = 0.0
        for c in top_n_list:
            size_ratio = local_sizes[c] / total_size if total_size > 0 else 1/n_top
            theta_span = available_angle * size_ratio
            comm[c] = {"start": t, "end": t + theta_span, "mid": t + theta_span / 2, "size": local_sizes[c]}
            t += theta_span + gap
        
        for _, row in df.iterrows():
            c1, c2, ww = row["c1"], row["c2"], float(row["weight"])
            # Use log-scaled normalization
            nw = norm_log(ww)
            nw_visual = nw ** 0.7
            thickness = 0.006 + 0.032 * nw_visual
            t1, t2 = comm[c1]["mid"], comm[c2]["mid"]
            p0 = (np.cos(t1), np.sin(t1))
            p1 = (np.cos(t2), np.sin(t2))
            tm = (t1 + t2) / 2.0
            pc = (0.20*np.cos(tm), 0.20*np.sin(tm))
            t_vals = np.linspace(0, 1, 100)
            x = (1-t_vals)**2*p0[0] + 2*(1-t_vals)*t_vals*pc[0] + t_vals**2*p1[0]
            y = (1-t_vals)**2*p0[1] + 2*(1-t_vals)*t_vals*pc[1] + t_vals**2*p1[1]
            dx = np.gradient(x)
            dy = np.gradient(y)
            norm_len = np.sqrt(dx*dx + dy*dy) + 1e-12
            nx_arr = -dy / norm_len
            ny_arr = dx / norm_len
            x1 = x + (thickness/2)*nx_arr
            y1 = y + (thickness/2)*ny_arr
            x2 = x - (thickness/2)*nx_arr
            y2 = y - (thickness/2)*ny_arr
            rx = np.concatenate([x1, x2[::-1]])
            ry = np.concatenate([y1, y2[::-1]])
            
            # Blend colors from both communities
            col1 = palette[idx_map[c1] % len(palette)]
            col2 = palette[idx_map[c2] % len(palette)]
            h1 = col1.lstrip("#")
            r1, g1, b1 = int(h1[0:2], 16), int(h1[2:4], 16), int(h1[4:6], 16)
            h2 = col2.lstrip("#")
            r2, g2, b2 = int(h2[0:2], 16), int(h2[2:4], 16), int(h2[4:6], 16)
            r_b, g_b, b_b = (r1+r2)//2, (g1+g2)//2, (b1+b2)//2
            alpha_base = 0.15 + 0.55 * nw_visual
            fill_color = f"rgba({r_b},{g_b},{b_b},{alpha_base*0.6})"
            line_color = f"rgba({r_b},{g_b},{b_b},{alpha_base*0.8})"
            
            traces.append(go.Scatter(
                x=rx.tolist(), y=ry.tolist(),
                mode="lines", fill="toself",
                fillcolor=fill_color,
                line=dict(width=0.8, color=line_color),
                hovertemplate=f"<b>C{idx_map[c1]} ↔ C{idx_map[c2]}</b><br>Weight: {ww:,.0f}<extra></extra>",
                showlegend=False,
                visible=visible,
                meta={"type": "edge", "c1": int(idx_map[c1]), "c2": int(idx_map[c2])},
            ))
            edge_metadata.append({"c1": idx_map[c1], "c2": idx_map[c2]})
        
        for c in top_n_list:
            xa, ya = arc(comm[c]["start"], comm[c]["end"], r=1.06, k=70)
            traces.append(go.Scatter(
                x=list(xa), y=list(ya), mode="lines",
                line=dict(color=palette[idx_map[c] % len(palette)], width=14),
                hovertemplate=f"<b>Community {idx_map[c]}</b><br>Connections: {int(comm[c]['size']):,}<extra></extra>",
                showlegend=False,
                visible=visible,
                meta={"type": "arc", "community": int(idx_map[c])},
            ))
            arc_metadata.append({"community": idx_map[c]})
        
        lx, ly, lt = [], [], []
        for c in top_n_list:
            tmid = comm[c]["mid"]
            lx.append(1.22*np.cos(tmid))
            ly.append(1.22*np.sin(tmid))
            lt.append(f"C{idx_map[c]}")
        traces.append(go.Scatter(
            x=lx, y=ly, mode="text", text=lt,
            textfont=dict(family=font, size=13, color="white", weight=600),
            hoverinfo="skip", showlegend=False,
            visible=visible,
            meta={"type": "label"},
        ))
        return traces, edge_metadata, arc_metadata
    
    # Build ALL traces for all slider values, tracking indices
    fig = go.Figure()
    trace_groups = {}  # Maps n_top -> list of trace indices
    all_edge_metadata = []  # Global edge metadata for all traces
    all_arc_metadata = []   # Global arc metadata for all traces
    
    for step_idx, n_top in enumerate(slider_steps):
        # Only the last step (all communities) is visible initially
        is_visible = (n_top == slider_steps[-1])
        traces, edge_meta, arc_meta = build_traces_for_n(n_top, visible=is_visible)
        
        start_idx = len(fig.data)
        for trace in traces:
            fig.add_trace(trace)
        end_idx = len(fig.data)
        
        trace_groups[n_top] = list(range(start_idx, end_idx))
        all_edge_metadata.extend(edge_meta)
        all_arc_metadata.extend(arc_meta)
    
    total_traces = len(fig.data)
    
    # Build slider steps with visibility toggling
    sliders_steps = []
    for step_idx, n_top in enumerate(slider_steps):
        # Create visibility array: True only for this step's traces
        visibility = [False] * total_traces
        for idx in trace_groups[n_top]:
            visibility[idx] = True
        
        label = f"All ({n_top})" if n_top == n_total else str(n_top)
        step = dict(
            method="update",
            args=[{"visible": visibility}],
            label=label
        )
        sliders_steps.append(step)
    
    # Find initial active index (last one = all communities)
    initial_active = len(slider_steps) - 1
    
    sliders = [dict(
        active=initial_active,
        currentvalue=dict(
            prefix="Communities: ", 
            font=dict(size=14, color="white"),
            visible=True,
            xanchor="center"
        ),
        pad=dict(t=60, b=10),
        len=0.65,
        x=0.175,
        xanchor="left",
        y=0,
        yanchor="top",
        steps=sliders_steps,
        bgcolor="#333",
        bordercolor="#555",
        font=dict(color="white", size=12),
        ticklen=5,
        tickcolor="white",
    )]

    # Layout
    fig.update_layout(
        title=dict(
            text=f"<span style='text-shadow:2px 2px 0 #000'>{title}</span>",
            x=0.5, y=0.96,
            font=dict(size=24, family=font, color="white")
        ),
        paper_bgcolor=bg,
        plot_bgcolor=bg,
        height=900,
        margin=dict(l=40, r=40, t=80, b=100),
        font=dict(family=font, color="white"),
        hoverlabel=dict(
            bgcolor="#0b1220",
            font_family=font,
            font_color="white",
            bordercolor="#06b6d4"
        ),
        sliders=sliders,
        )
    
    fig.update_xaxes(showgrid=False, zeroline=False, showticklabels=False, range=[-1.4, 1.4], scaleanchor="y")
    fig.update_yaxes(showgrid=False, zeroline=False, showticklabels=False, range=[-1.4, 1.4])
    
    if out_path:
        # Hide the modebar (toolbar)
        config = {
            'displayModeBar': False,
            'staticPlot': False,
        }
        
        # Custom JavaScript for hover effects with community/edge awareness
        hover_script = """
        var gd = document.getElementsByClassName('plotly-graph-div')[0];
        var isHovering = false;
        
        gd.on('plotly_hover', function(data) {
            if (isHovering) return;
            isHovering = true;
            
            var hoveredTrace = data.points[0].curveNumber;
            var traces = gd.data;
            var hoveredMeta = traces[hoveredTrace].meta;
            
            // Skip if no meta (like labels)
            if (!hoveredMeta) {
                isHovering = false;
                return;
            }
            
            var opacities = [];
            
            for (var i = 0; i < traces.length; i++) {
                var traceMeta = traces[i].meta;
                var shouldHighlight = false;
                
                if (!traceMeta) {
                    // Labels - always visible
                    opacities.push(1.0);
                    continue;
                }
                
                if (hoveredMeta.type === 'arc') {
                    // Hovering on a community arc - highlight all edges connected to this community
                    var hoveredComm = hoveredMeta.community;
                    if (traceMeta.type === 'arc') {
                        // Highlight only the hovered arc
                        shouldHighlight = (traceMeta.community === hoveredComm);
                    } else if (traceMeta.type === 'edge') {
                        // Highlight edges connected to this community
                        shouldHighlight = (traceMeta.c1 === hoveredComm || traceMeta.c2 === hoveredComm);
                    }
                } else if (hoveredMeta.type === 'edge') {
                    // Hovering on an edge - highlight all segments of this edge and both community arcs
                    var c1 = hoveredMeta.c1;
                    var c2 = hoveredMeta.c2;
                    if (traceMeta.type === 'edge') {
                        // Highlight all segments of this edge
                        shouldHighlight = (traceMeta.c1 === c1 && traceMeta.c2 === c2);
                    } else if (traceMeta.type === 'arc') {
                        // Highlight both connected community arcs
                        shouldHighlight = (traceMeta.community === c1 || traceMeta.community === c2);
                    }
                }
                
                opacities.push(shouldHighlight ? 1.0 : 0.08);
            }
            
            // Batch update for performance
            Plotly.restyle(gd, {opacity: opacities});
        });
        
        gd.on('plotly_unhover', function(data) {
            isHovering = false;
            var traces = gd.data;
            var opacities = [];
            for (var i = 0; i < traces.length; i++) {
                opacities.push(1.0);
            }
            Plotly.restyle(gd, {opacity: opacities});
        });
        """
        
        # Write HTML with hover script
        fig.write_html(
            out_path, 
            include_plotlyjs="cdn", 
            full_html=True,
            config=config,
            post_script=hover_script
        )
        print(f"✓ Saved interactive chord diagram with slider to {out_path}")
    
    return fig


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


def plot_echo_share(mobility_df, echo_candidates, q_ext, out_path="reports/figures/echo_chamber_external_share.html"):
    """
    Plot external share bar chart highlighting echo candidates.
    """
    import plotly.graph_objects as go
    
    # YouNiverse Theme
    bg_color = "#000000"
    font_stack = "'-apple-system', 'BlinkMacSystemFont', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
    
    # Prepare data
    communities = mobility_df["community"].astype(str).tolist()
    external_shares = mobility_df["external_share"].tolist()
    
    # Color: echo chambers in red/purple, others in cyan
    colors = ["#8b5cf6" if es <= q_ext else "#06b6d4" for es in external_shares]
    
    # Create figure
    fig = go.Figure()
    
    # Add bar chart
    fig.add_trace(go.Bar(
        x=communities,
        y=external_shares,
        marker=dict(
            color=colors,
            line=dict(color="#FFFFFF", width=0.5)
        ),
        hovertemplate="<b>Community %{x}</b><br>External Share: %{y:.3f}<extra></extra>",
        name="External Share"
    ))
    
    # Add threshold line
    fig.add_hline(
        y=q_ext,
        line_dash="dash",
        line_color="#FFFFFF",
        line_width=2,
        annotation_text=f"25th percentile: {q_ext:.3f}",
        annotation_position="top right",
        annotation_font=dict(size=12, color="#FFFFFF", family=font_stack)
    )
    
    # Layout with YouNiverse theme - no title for embedding
    fig.update_layout(
        paper_bgcolor=bg_color,
        plot_bgcolor=bg_color,
        height=450,
        margin=dict(l=60, r=40, t=40, b=60),
        font=dict(family=font_stack, size=14, color="#FFFFFF"),
        hoverlabel=dict(
            bgcolor="#111111",
            font_size=14,
            font_family=font_stack,
            font_color="#FFFFFF",
            bordercolor="#06b6d4"
        ),
        showlegend=False
    )
    
    # X-axis styling
    fig.update_xaxes(
        title="COMMUNITY ID",
        title_font=dict(family=font_stack, size=14, color="#FFFFFF"),
        showgrid=False,
        zeroline=False,
        tickfont=dict(family=font_stack, color="#888888"),
        linecolor="#444444"
    )
    
    # Y-axis styling
    fig.update_yaxes(
        title="<span style='color:#06b6d4'>EXTERNAL SHARE</span>",
        title_font=dict(family=font_stack, size=14),
        showgrid=True,
        gridcolor="rgba(255,255,255,0.05)",
        zeroline=False,
        linecolor="#06b6d4",
        tickfont=dict(family=font_stack, color="#888888")
    )
    
    # Save as HTML instead of PNG for consistency
    if out_path:
        html_path = out_path.replace('.png', '.html')
        config = {'displayModeBar': False}
        fig.write_html(html_path, include_plotlyjs='cdn', full_html=True, config=config)
    
    return fig


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



def plot_bridge_categories(agg, out_path="reports/figures/bridge_categories_top3.html", show_title=True):
    """
    Plot top 3 bridge categories per community.
    Uses YouNiverse theme for consistency.
    """
    import plotly.graph_objects as go
    
    # YouNiverse Theme - pure black background
    bg_color = "#000000"
    font_stack = "'-apple-system', 'BlinkMacSystemFont', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
    
    # Get top 3 categories per community
    cat_top3 = (
        agg.sort_values(["community", "cross_strength"], ascending=[True, False])
        .groupby("community").head(3)
    )
    
    # Color palette for categories
    category_colors = {
        "Entertainment": "#8b5cf6",
        "Music": "#06b6d4",
        "Gaming": "#F97316",
        "Howto & Style": "#22C55E",
        "Sports": "#E11D48",
        "News & Politics": "#FACC15",
        "People & Blogs": "#A855F7",
        "Comedy": "#14B8A6",
        "Film & Animation": "#E879F9",
        "Education": "#FB7185",
        "Autos & Vehicles": "#94A3B8",
    }
    
    fig = go.Figure()
    
    # Get unique categories
    categories = cat_top3["category_cc"].unique()
    
    # Add traces for each category
    for category in categories:
        cat_data = cat_top3[cat_top3["category_cc"] == category]
        color = category_colors.get(category, "#888888")
        
        fig.add_trace(go.Bar(
            x=cat_data["community"].astype(str),
            y=cat_data["cross_strength"],
            name=category,
            marker=dict(color=color, line=dict(color="#FFFFFF", width=0.5)),
            hovertemplate="<b>Community %{x}</b><br>" + 
                         f"{category}<br>" + 
                         "Cross Strength: %{y:,.0f}<extra></extra>",
        ))
    
    # Layout
    title_config = dict(
        #text="<span style='text-shadow: 2px 2px 0 #000;'>TOP BRIDGE CATEGORIES BY COMMUNITY</span>",
        x=0.5,
        y=0.95,
        font=dict(size=24, family=font_stack, color="#FFFFFF")
    ) if show_title else dict(text="")
    
    fig.update_layout(
        title=title_config,
        paper_bgcolor=bg_color,
        plot_bgcolor=bg_color,
        height=550,
        margin=dict(l=80, r=80, t=60 if not show_title else 120, b=80),
        font=dict(family=font_stack, size=14, color="#FFFFFF"),
        barmode='group',
        hoverlabel=dict(
            bgcolor="#111111",
            font_size=14,
            font_family=font_stack,
            font_color="#FFFFFF",
            bordercolor="#06b6d4"
        ),
        legend=dict(
            orientation="v",
            yanchor="top",
            y=0.98,
            xanchor="right",
            x=0.99,
            bgcolor="rgba(0,0,0,0.6)",
            font=dict(family=font_stack, size=11, color="#FFFFFF"),
            bordercolor="#444444",
            borderwidth=1
        )
    )
    
    # X-axis styling
    fig.update_xaxes(
        title="COMMUNITY ID",
        title_font=dict(family=font_stack, size=14, color="#FFFFFF"),
        showgrid=False,
        zeroline=False,
        tickfont=dict(family=font_stack, color="#888888"),
        linecolor="#444444"
    )
    
    # Y-axis styling
    fig.update_yaxes(
        title="<span style='color:#06b6d4'>CROSS STRENGTH (BRIDGES)</span>",
        title_font=dict(family=font_stack, size=14),
        showgrid=True,
        gridcolor="rgba(255,255,255,0.05)",
        zeroline=False,
        linecolor="#06b6d4",
        tickfont=dict(family=font_stack, color="#888888")
    )
    
    if out_path:
        html_path = out_path.replace('.png', '.html')
        config = {'displayModeBar': False}
        fig.write_html(html_path, include_plotlyjs='cdn', full_html=True, config=config)
        print(f"✓ Saved bridge categories plot to {html_path}")
    
    return fig


def plot_directional_flows(flow_norm, top_n=20, out_path="reports/figures/bridge_community_topflows.html", show_title=True):
    """
    Plot strongest directional flows between communities (normalized weights).
    Uses YouNiverse theme for consistency.
    """
    import plotly.graph_objects as go
    import pandas as pd
    
    # YouNiverse Theme - pure black background
    bg_color = "#000000"
    font_stack = "'-apple-system', 'BlinkMacSystemFont', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
    
    # Prepare data
    flow_long = flow_norm.stack().reset_index()
    flow_long.columns = ["community_src", "community_dst", "weight"]
    flow_long = flow_long[flow_long["community_src"] != flow_long["community_dst"]]
    flow_long = flow_long[flow_long["weight"] > 0]
    top_flows = flow_long.sort_values("weight", ascending=True).tail(top_n)  # Ascending for horizontal bar
    
    # Create flow labels
    flow_labels = [f"C{int(row['community_src'])} → C{int(row['community_dst'])}" 
                   for _, row in top_flows.iterrows()]
    
    # Color gradient based on weight
    weights = top_flows["weight"].values
    w_norm = (weights - weights.min()) / (weights.max() - weights.min() + 1e-12)
    
    # Create color gradient (purple to cyan based on weight)
    colors = []
    for norm_val in w_norm:
        # Blend from purple (#8b5cf6) to cyan (#06b6d4)
        r = int(139 + (6 - 139) * norm_val)
        g = int(92 + (182 - 92) * norm_val)
        b = int(246 + (212 - 246) * norm_val)
        colors.append(f"rgb({r},{g},{b})")
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=flow_labels,
        x=top_flows["weight"],
        orientation='h',
        marker=dict(
            color=colors,
            line=dict(color="#FFFFFF", width=0.5)
        ),
        hovertemplate="<b>%{y}</b><br>Normalized Flow: %{x:.4f}<extra></extra>",
        showlegend=False
    ))
    
    # Layout
    title_config = dict(
        #text="<span style='text-shadow: 2px 2px 0 #000;'>TOP CROSS-COMMUNITY FLOWS</span>",
        x=0.5,
        y=0.96,
        font=dict(size=24, family=font_stack, color="#FFFFFF")
    ) if show_title else dict(text="")
    
    fig.update_layout(
        title=title_config,
        paper_bgcolor=bg_color,
        plot_bgcolor=bg_color,
        height=max(550, top_n * 25 + 100),
        margin=dict(l=150, r=80, t=60 if not show_title else 120, b=80),
        font=dict(family=font_stack, size=13, color="#FFFFFF"),
        hoverlabel=dict(
            bgcolor="#111111",
            font_size=14,
            font_family=font_stack,
            font_color="#FFFFFF",
            bordercolor="#06b6d4"
        )
    )
    
    # X-axis styling
    fig.update_xaxes(
        title="<span style='color:#06b6d4'>NORMALIZED FLOW</span>",
        title_font=dict(family=font_stack, size=14),
        showgrid=True,
        gridcolor="rgba(255,255,255,0.05)",
        zeroline=False,
        tickfont=dict(family=font_stack, color="#888888"),
        linecolor="#06b6d4"
    )
    
    # Y-axis styling
    fig.update_yaxes(
        title="SOURCE → DESTINATION",
        title_font=dict(family=font_stack, size=14, color="#FFFFFF"),
        showgrid=False,
        zeroline=False,
        tickfont=dict(family=font_stack, color="#888888", size=11),
        linecolor="#444444"
    )
    
    if out_path:
        html_path = out_path.replace('.png', '.html')
        config = {'displayModeBar': False}
        fig.write_html(html_path, include_plotlyjs='cdn', full_html=True, config=config)
        print(f"✓ Saved directional flows plot to {html_path}")
    
    return fig



def bridge_channels_html_slider(
    top_channels,
    out_path="reports/figures/bridge_channels_interactive.html",
    topN=10,
    communities_per_group=3
):
    """
    Bridge Channels visualization with NATIVE PLOTLY slider that works in exported HTML.
    Shows top bridge channels for each community group.
    
    Parameters:
    -----------
    top_channels : DataFrame
        DataFrame with columns: community, name, cross_strength, cross_share
    out_path : str
        Output path for HTML file
    topN : int
        Number of top channels to show per community
    communities_per_group : int
        Number of communities to show per group (default 3)
    """
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    import numpy as np
    
    # YouNiverse Theme
    bg_color = "#000000"
    font_stack = "'-apple-system', 'BlinkMacSystemFont', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
    color_palette = ["#8b5cf6", "#06b6d4", "#F97316", "#22C55E", "#E11D48", "#FACC15", "#A855F7", "#14B8A6", "#60A5FA", "#FB7185"]
    
    # Get sorted communities
    communities_list = sorted(top_channels["community"].unique())
    
    # Group communities
    groups = []
    for i in range(0, len(communities_list), communities_per_group):
        group = communities_list[i:i+communities_per_group]
        group_label = f"Communities {group[0]}-{group[-1]}" if len(group) > 1 else f"Community {group[0]}"
        groups.append((group_label, group))
    
    # Create figure with max subplots needed
    max_comms = communities_per_group
    fig = make_subplots(
        rows=max_comms, cols=1,
        subplot_titles=[f"<b>Community</b>" for _ in range(max_comms)],
        vertical_spacing=0.12,
        specs=[[{"type": "bar"}] for _ in range(max_comms)]
    )
    
    # Build all traces for all groups
    trace_groups = {}  # Maps group_idx -> list of trace indices
    
    for group_idx, (group_label, selected_communities) in enumerate(groups):
        group_traces = []
        
        for idx, comm in enumerate(selected_communities):
            data = top_channels[top_channels["community"] == comm].sort_values(
                "cross_strength", ascending=True
            ).tail(topN)
            
            if data.empty:
                continue
            
            color = color_palette[int(comm) % len(color_palette)]
            
            trace = go.Bar(
                y=data["name"].tolist(),
                x=data["cross_strength"].tolist(),
                orientation='h',
                marker=dict(color=color, line=dict(color="#FFFFFF", width=0.5)),
                text=[f"{cs:.2f}" for cs in data["cross_share"]],
                textposition='outside',
                textfont=dict(size=9, color="#FFFFFF"),
                hovertemplate="<b>%{y}</b><br>Cross Strength: %{x:,.0f}<br>Cross Share: %{text}<extra></extra>",
                showlegend=False,
                visible=(group_idx == 0),  # Only first group visible initially
            )
            group_traces.append((trace, idx + 1, comm))
        
        trace_groups[group_idx] = group_traces
    
    # Add all traces to figure
    trace_index_map = {}  # Maps group_idx -> list of (trace_index, comm)
    current_trace_idx = 0
    
    for group_idx, group_traces in trace_groups.items():
        trace_index_map[group_idx] = []
        for trace, subplot_row, comm in group_traces:
            fig.add_trace(trace, row=subplot_row, col=1)
            trace_index_map[group_idx].append((current_trace_idx, comm))
            current_trace_idx += 1
    
    total_traces = len(fig.data)
    
    # Build slider steps
    slider_steps = []
    for group_idx, (group_label, selected_communities) in enumerate(groups):
        # Create visibility array
        visibility = [False] * total_traces
        for trace_idx, _ in trace_index_map.get(group_idx, []):
            visibility[trace_idx] = True
        
        # Build subplot title updates
        annotations = []
        for i, comm in enumerate(selected_communities):
            annotations.append(dict(
                text=f"<b>Community {comm}</b>",
                font=dict(size=12, color="#06b6d4", family=font_stack),
                showarrow=False,
                x=0.5,
                xref="paper",
                y=1 - (i * 0.33) - 0.01,
                yref="paper",
                xanchor="center",
                yanchor="bottom"
            ))
        
        step = dict(
            method="update",
            args=[
                {"visible": visibility},
                {"annotations": annotations}
            ],
            label=group_label.replace("Communities ", "").replace("Community ", "")
        )
        slider_steps.append(step)
    
    # Initial annotations for first group
    initial_annotations = []
    first_group_comms = groups[0][1] if groups else []
    for i, comm in enumerate(first_group_comms):
        initial_annotations.append(dict(
            text=f"<b>Community {comm}</b>",
            font=dict(size=12, color="#06b6d4", family=font_stack),
            showarrow=False,
            x=0.5,
            xref="paper",
            y=1 - (i * 0.33) - 0.01,
            yref="paper",
            xanchor="center",
            yanchor="bottom"
        ))
    
    sliders = [dict(
        active=0,
        currentvalue=dict(
            prefix="Group: ",
            font=dict(size=14, color="white"),
            visible=True,
            xanchor="center"
        ),
        pad=dict(t=50, b=10),
        len=0.9,
        x=0.05,
        xanchor="left",
        y=0,
        yanchor="top",
        steps=slider_steps,
        bgcolor="#333",
        bordercolor="#555",
        font=dict(color="white", size=10),
        ticklen=5,
        tickcolor="white",
    )]
    
    # Update layout
    height = max(700, max_comms * 280)
    
    fig.update_layout(
        paper_bgcolor=bg_color,
        plot_bgcolor=bg_color,
        height=height,
        margin=dict(l=280, r=100, t=60, b=100),
        font=dict(family=font_stack, size=11, color="#FFFFFF"),
        hoverlabel=dict(
            bgcolor="#111111",
            font_size=12,
            font_family=font_stack,
            font_color="#FFFFFF",
            bordercolor="#06b6d4"
        ),
        sliders=sliders,
        annotations=initial_annotations,
    )
    
    # Update axes
    for i in range(1, max_comms + 1):
        fig.update_xaxes(
            title_text="Cross Strength" if i == max_comms else "",
            showgrid=True,
            gridcolor="rgba(255,255,255,0.05)",
            zeroline=False,
            tickfont=dict(family=font_stack, color="#888888", size=10),
            title_font=dict(family=font_stack, color="#06b6d4", size=12),
            row=i, col=1
        )
        fig.update_yaxes(
            showgrid=False,
            tickfont=dict(family=font_stack, color="#888888", size=10),
            row=i, col=1
        )
    
    if out_path:
        config = {'displayModeBar': False}
        fig.write_html(out_path, include_plotlyjs='cdn', full_html=True, config=config)
        print(f"✓ Saved bridge channels interactive plot to {out_path}")
    
    return fig
