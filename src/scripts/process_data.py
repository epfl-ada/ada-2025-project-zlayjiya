# src/scripts/process_data.py
import pandas as pd
import fsspec
from collections import defaultdict, Counter
from itertools import combinations
from tqdm.auto import tqdm
import pickle
import os
import json
import csv
from src.data.data_loader import get_file_url # Import helper

def build_video_to_channel_map(video_df):
    """
    Creates the video_id -> channel_id dictionary.
   
    """
    print(f"Creating {len(video_df):,} v2c mappings...")
    return dict(zip(video_df.display_id.values, video_df.channel_id.values))

def get_channel_subset_map(channel_df, min_subscribers=200_000):
    """
    Creates a boolean map of channels to include based on subscriber count.
   
    """
    subset_map = dict(zip(channel_df.channel.values, channel_df.subscribers_cc.values > min_subscribers))
    print(f"Created channel subset map. {sum(subset_map.values()):,} channels selected.")
    return subset_map

# --- Helper functions for new logic ---
def save_state_and_dict(rows_seen, channelToCommNumbers, dict_path, state_path):
    """
    Saves the channel-to-commenter-count dict and the row state.
   
    """
    with open(dict_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["channel_id", "count"])
        w.writeheader()
        for ch, cnt in channelToCommNumbers.items():
            w.writerow({"channel_id": ch, "count": int(cnt)})
    with open(state_path, "w") as f:
        json.dump({"rows_seen": int(rows_seen)}, f)

def flush_authors(authors_dict, edges_counter, channelToCommNumbers, top_k, min_chans):
    """
    For each author: keep only top-K channels (by count), then add +1 to each pair.
    Also increments channelToCommNumbers for those top-K channels.
   
    """
    for author, cnt in authors_dict.items():
        if not cnt:
            continue
        topk = [ch for ch, _ in cnt.most_common(top_k)]
        if len(topk) >= min_chans:
            for a, b in combinations(sorted(topk), 2):
                edges_counter[(a, b)] += 1
        for ch in topk:
            channelToCommNumbers[ch] += 1
    authors_dict.clear()

def generate_edges(
    v2c_map, 
    out_csv_path,
    checkpoint_path,
    state_path,
    dict_path,
    max_rows=150_000_000,
    top_k_per_author=5,
    min_chans_for_pairs=2,
    author_flush_threshold=500_000,
    checkpoint_every=5,
    chunksize=1_000_000
):
    """
    Streams comments and generates the weighted edge list
    based on Top-K co-commenting logic.
   
    """
    
    if os.path.exists(out_csv_path):
        print(f"{out_csv_path} already exists. Skipping edge generation.")
        return load_edges(out_csv_path)

    print("Starting edge generation process (Top-K logic)...")
    
    if os.path.exists(checkpoint_path):
        print("Resuming from checkpoint...")
        with open(checkpoint_path, "rb") as f:
            edges_counter = pickle.load(f)
    else:
        edges_counter = Counter()

    if os.path.exists(dict_path):
        print(f"Resuming commenter counts from {dict_path}...")
        channelToCommNumbers = defaultdict(int)
        with open(dict_path, newline="", encoding="utf-8") as f:
            r = csv.DictReader(f)
            for row in r:
                try:
                    channelToCommNumbers[row["channel_id"]] = int(row["count"])
                except Exception:
                    continue
    else:
        channelToCommNumbers = defaultdict(int)

    if os.path.exists(state_path):
        with open(state_path) as f:
            rows_seen = json.load(f)["rows_seen"]
    else:
        rows_seen = 0
    
    print(f"Starting from {rows_seen:,} rows seen.")
    
    chunk_idx = 0
    user_counts = defaultdict(Counter)
    COMMENTS_URL_KEY = "youtube_comments.tsv.gz"
    
    comments_url = get_file_url(COMMENTS_URL_KEY)
    with fsspec.open(comments_url, "rb") as fh:
        reader = pd.read_csv(
            fh,
            sep="\\t",
            compression="gzip",
            usecols=["author", "video_id"],
            dtype=str,
            chunksize=chunksize
        )

        for chunk in tqdm(reader, desc="Streaming comments in chunks"):
            chunk_idx += 1

            if max_rows and rows_seen >= max_rows:
                print(f"Max rows ({max_rows:,}) reached. Stopping.")
                break

            if max_rows:
                remaining = max_rows - rows_seen
                if len(chunk) > remaining:
                    chunk = chunk.iloc[:remaining]
            
            chunk["channel_id"] = chunk["video_id"].map(v2c_map)
            chunk = chunk.dropna(subset=["author", "channel_id"])
            
            for author, series in chunk.groupby("author")["channel_id"]:
                vc = series.value_counts()
                user_counts[author].update(vc.to_dict())

            rows_seen += len(chunk)

            if len(user_counts) > author_flush_threshold:
                flush_authors(user_counts, edges_counter, channelToCommNumbers, top_k_per_author, min_chans_for_pairs)

            if chunk_idx % checkpoint_every == 0:
              with open(checkpoint_path, "wb") as f:
                  pickle.dump(edges_counter, f)
              
              save_state_and_dict(rows_seen, channelToCommNumbers, dict_path, state_path)

    print("Processing final flush...")
    flush_authors(user_counts, edges_counter, channelToCommNumbers, top_k_per_author, min_chans_for_pairs)
    save_state_and_dict(rows_seen, channelToCommNumbers, dict_path, state_path)
    
    print(f"Processed ~{rows_seen:,} comment rows; unique edges: {len(edges_counter):,}")

    edges_df = pd.DataFrame(((a, b, w) for (a, b), w in edges_counter.items()),
                            columns=["src", "dst", "weight"])
    edges_df.to_csv(out_csv_path, index=False)
    print(f"Wrote edges → {out_csv_path}")
    
    if os.path.exists(checkpoint_path): os.remove(checkpoint_path)
    if os.path.exists(state_path): os.remove(state_path)
    
    return edges_df

# Helper function
def load_edges(path):
    print(f"Loading existing edges from {path}...")
    return pd.read_csv(path)