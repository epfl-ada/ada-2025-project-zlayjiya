import pandas as pd
import numpy as np
import sys
import os
import matplotlib.pyplot as plt
from io import StringIO
import pickle

if len(sys.argv) < 2:
    print("Usage: python results.py <YEAR>")
    print("Ex: python results.py 2010")
    sys.exit(1)

YEAR = sys.argv[1]

module_path = os.path.abspath(os.path.join('..'))
if module_path not in sys.path:
    sys.path.append(module_path)

from src.data import data_loader 
from src.scripts import process_data as data_processor
from src.models import model_analysis as model_analyzer

print(f"Successfully imported src modules. Processing year {YEAR}.")

MIN_SUBSCRIBERS = 200_000
MIN_EDGE_WEIGHT = 25
MAX_COMMENT_ROWS = 150_000_000 

TOP_K_PER_AUTHOR = 5
MIN_CHANS_FOR_PAIRS = 2
AUTHOR_FLUSH_THRESHOLD = 500_000

NORM_ALPHA = 0.5
NORM_BETA = 1.0
USE_ENGAGEMENT_METRIC = True

CHANNEL_METADATA_PATH = "../data/raw/df_channels_en.tsv" 
VIDEO_METADATA_PATH = "../data/raw/yt_metadata_helper.feather"

EDGES_OUT_PATH = f"../data/temporal_graphs/{YEAR}/channel_edges_{YEAR}_100M.csv"
DICT_PATH = f"../data/temporal_graphs/{YEAR}/channel_counts_{YEAR}.csv"

OUTPUT_DIR = f"../data/resultats/{YEAR}"
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs("../reports/figures", exist_ok=True)

NODES_OUT_PATH = f"{OUTPUT_DIR}/chan_graph_node_metrics_{YEAR}.csv"
COMMUNITIES_OUT_PATH = f"{OUTPUT_DIR}/chan_graph_community_summary_{YEAR}.csv"
VIZ_OUT_PATH = f"../reports/figures/network_viz_{YEAR}.png"
RESULTS_TXT_PATH = f"{OUTPUT_DIR}/results_{YEAR}.txt"

print("Configuration and paths set.")

#dfChannels = pd.read_csv(CHANNEL_METADATA_PATH,sep='\t')
#videoDf = data_loader.load_video_metadata(local_path=VIDEO_METADATA_PATH, columns=["display_id", "channel_id"])

#v2c_map = data_processor.build_video_to_channel_map(videoDf)
#channel_subset_map = data_processor.get_channel_subset_map(dfChannels, MIN_SUBSCRIBERS)

#del videoDf
dfChannels = pd.read_csv(CHANNEL_METADATA_PATH, sep='\t')
edges_df = data_loader.load_edges(EDGES_OUT_PATH)
print(f"\nSuccessfully loaded {len(edges_df):,} edges.")
print(edges_df.head())

edges_filtered, channels_indexed = model_analyzer.filter_edges(
    edges_df, dfChannels, MIN_SUBSCRIBERS, MIN_EDGE_WEIGHT
)

commenter_counts = data_loader.load_commenter_counts(DICT_PATH)

edges_normalized = model_analyzer.normalize_edges(
    edges_filtered, 
    channels_indexed, 
    commenter_counts, 
    alpha=NORM_ALPHA, 
    beta=NORM_BETA, 
    use_engagement=USE_ENGAGEMENT_METRIC
)

G = model_analyzer.build_graph(edges_normalized, channels_indexed)

LCC, communities, node_df, comm_summary = model_analyzer.find_communities(
    G, nodes_out_path=NODES_OUT_PATH, comm_out_path=COMMUNITIES_OUT_PATH
)

with open(RESULTS_TXT_PATH, "w") as f:
    f.write(f"=== RESULTS FOR YEAR {YEAR} ===\n\n")
    
    f.write("Top 10 Largest Communities:\n")
    f.write(comm_summary.head(10).to_string(index=False))
    f.write("\n\n")
    
    f.write("Top 10 Channels by PageRank:\n")
    f.write(node_df.nlargest(10, "pagerank")[
        ["name_cc", "category_cc", "subscribers_cc", "community", "degree", "pagerank"]
    ].to_string(index=False))
    f.write("\n\n")

print("Top 10 Largest Communities:")
print(comm_summary.head(10).to_string(index=False))

print("Top 10 Channels by PageRank:")
print(node_df.nlargest(10, "pagerank")[
    ["name_cc", "category_cc", "subscribers_cc", "community", "degree", "pagerank"]
].to_string(index=False))

old_stdout = sys.stdout
sys.stdout = StringIO()

model_analyzer.analyze_communities(LCC, node_df, communities, max_show=20)

community_analysis = sys.stdout.getvalue()
sys.stdout = old_stdout

print(community_analysis)

with open(f"{OUTPUT_DIR}/community_analysis_{YEAR}.txt", "w") as f:
    f.write(community_analysis)

viz_data = {
    'LCC': LCC,
    'communities': communities,
    'node_df': node_df,
    'comm_summary': comm_summary
}

with open(f"{OUTPUT_DIR}/viz_data_{YEAR}.pkl", "wb") as f:
    pickle.dump(viz_data, f)

print(f"Saved viz data to {OUTPUT_DIR}/viz_data_{YEAR}.pkl")
#model_analyzer.visualize_network(
#    LCC, 
#    communities, 
#    node_df, 
#    viz_out_path=VIZ_OUT_PATH
#)
os.remove(NODES_OUT_PATH)
print(f"\n=== DONE FOR YEAR {YEAR} ===")
print(f"Results saved to {RESULTS_TXT_PATH}")