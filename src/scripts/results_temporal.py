import pandas as pd
import sys
import os
import pickle

if len(sys.argv) < 2:
    print("Usage: python results.py <YEAR>")
    print("Ex: python results.py 2010")
    sys.exit(1)

YEAR = sys.argv[1]

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from src.data import data_loader 
from src.models import model_analysis as model_analyzer

print(f"Successfully imported src modules. Processing year {YEAR}.")

MIN_SUBSCRIBERS = 200_000
MIN_EDGE_WEIGHT = 25
NORM_ALPHA = 0.5
NORM_BETA = 1.0
USE_ENGAGEMENT_METRIC = True

CHANNEL_METADATA_PATH = "../../data/raw/df_channels_en.tsv" 
EDGES_OUT_PATH = f"../../data/temporal_graphs/{YEAR}/channel_edges_{YEAR}_100M.csv"
DICT_PATH = f"../../data/temporal_graphs/{YEAR}/channel_counts_{YEAR}.csv"
OUTPUT_DIR = f"../../data/results/{YEAR}"
os.makedirs(OUTPUT_DIR, exist_ok=True)
NODES_OUT_PATH = f"{OUTPUT_DIR}/chan_graph_node_metrics_{YEAR}.csv"
COMMUNITIES_OUT_PATH = f"{OUTPUT_DIR}/chan_graph_community_summary_{YEAR}.csv"
print("Configuration and paths set.")

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

viz_data = {
    'LCC': LCC,
    'communities': communities,
    'node_df': node_df,
    'comm_summary': comm_summary
}

with open(f"{OUTPUT_DIR}/viz_data_{YEAR}.pkl", "wb") as f:
    pickle.dump(viz_data, f)

print(f"Saved viz data to {OUTPUT_DIR}/viz_data_{YEAR}.pkl")
os.remove(NODES_OUT_PATH)
