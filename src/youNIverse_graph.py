import pandas as pd
import os
import sys
import csv
import gzip
import json
import pickle
from collections import defaultdict, Counter
from itertools import combinations
from datetime import datetime
from tqdm.auto import tqdm # Progress bar for streaming visualization

# --- CLUSTER CONFIGURATION (Command Line Input) ---
if len(sys.argv) < 3:
    print("Usage: python youniverse_graph.py <START_YEAR> <END_YEAR>")
    print("Ex: python youniverse_graph.py 2010 2012")
    print("Ex: python youniverse_graph.py 2015 2015  (pour une seule année)")
    sys.exit(1)
    
START_YEAR = int(sys.argv[1])
END_YEAR = int(sys.argv[2])

if START_YEAR > END_YEAR:
    print("ERROR: START_YEAR doit être <= END_YEAR")
    sys.exit(1)

START_DATE = f"{START_YEAR}-01-01"
END_DATE = f"{END_YEAR}-12-31"

if START_YEAR == END_YEAR:
    YEAR_TAG = str(START_YEAR)
else:
    YEAR_TAG = f"{START_YEAR}-{END_YEAR}"

# Variables du Prototype
CHUNKSIZE = 10_000_000
MAX_ROWS = 100_000_000 
TOP_K_PER_AUTHOR = 5
MIN_CHANS_FOR_PAIRS = 2
AUTHOR_FLUSH_THRESHOLD = 2_000_000
CHECKPOINT_EVERY = 20

# Display tag for file names
ROWS_TAG = f"{MAX_ROWS//1_000_000}M" if MAX_ROWS else "ALL"

# File Paths (Assumes running from YouNiverse_Project/src)
PATH_COMMENTS = "../data/raw/youtube_comments.tsv.gz"
PATH_METADATA = "../data/raw/yt_metadata_helper.feather" 

# Dynamic Output Paths
OUTPUT_DIR = f"../data_new/temporal_graphs/{YEAR_TAG}"
os.makedirs(OUTPUT_DIR, exist_ok=True)
EDGES_OUT = os.path.join(OUTPUT_DIR, f"channel_edges_{YEAR_TAG}_{ROWS_TAG}.csv")
DICT_PATH = os.path.join(OUTPUT_DIR, f"channel_counts_{YEAR_TAG}.csv")
CHECKPOINT_PATH = os.path.join(OUTPUT_DIR, f"edges_checkpoint_{YEAR_TAG}.pkl")
STATE_PATH = os.path.join(OUTPUT_DIR, f"state_{YEAR_TAG}.json")

print(f"--- PROCESSING YEAR {YEAR_TAG} ({ROWS_TAG}) ---")

# --- GLOBAL STATE (Checkpoint Loading Logic) ---

if os.path.exists(CHECKPOINT_PATH):
    print("Resuming from checkpoint...")
    with open(CHECKPOINT_PATH, "rb") as f:
        edges_counter = pickle.load(f)
else:
    edges_counter = Counter()

if os.path.exists(DICT_PATH):
    channelToCommNumbers = defaultdict(int)
    with open(DICT_PATH, newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            try:
                channelToCommNumbers[row["channel_id"]] = int(row["count"])
            except Exception:
                continue
else:
    channelToCommNumbers = defaultdict(int)

if os.path.exists(STATE_PATH):
    with open(STATE_PATH) as f:
        rows_seen = json.load(f)["rows_seen"]
else:
    rows_seen = 0

chunk_idx = 0
user_counts = defaultdict(Counter)
currentAuthor = None

# --- AUXILIARY FUNCTIONS (from the Prototype) ---

def load_video_mapping_and_filter(path):
    # This function loads the Feather file and filters the map by date.
    print("Loading video metadata (v2c)...")
    
    # Use Cache for v2c if available (speeds up next runs)
    cache_path = "../data/processed/v2c.pkl"
    if os.path.exists(cache_path):
        with open(cache_path, "rb") as f:
            v2c_all = pickle.load(f)
    else:
        try:
            videoDf = pd.read_feather(path, columns=["display_id", "channel_id", "upload_date"], dtype_backend="pyarrow")
        except Exception:
            print(f"FATAL: Could not read Feather metadata file at {path}. Check path and file integrity.")
            sys.exit(1)
        
        videoDf["upload_date"] = pd.to_datetime(videoDf["upload_date"], errors='coerce')
        v2c_all = dict(zip(videoDf.display_id.values, videoDf.channel_id.values))
        
        os.makedirs("../data/processed", exist_ok=True)
        with open(cache_path, "wb") as f:
            pickle.dump(v2c_all, f)
            
    # Date Filtering (Reloading the DataFrame to apply the date filter)
    try:
        videoDf = pd.read_feather(path, columns=["display_id", "channel_id", "upload_date"], dtype_backend="pyarrow")
    except Exception:
        print("FATAL: Could not read Feather metadata file for filtering.")
        sys.exit(1)
        
    videoDf["upload_date"] = pd.to_datetime(videoDf["upload_date"], errors='coerce')
    ts_start = pd.to_datetime(START_DATE)
    ts_end = pd.to_datetime(END_DATE)
        
    videoDf_filtered = videoDf[
        (videoDf["upload_date"] >= ts_start) & 
        (videoDf["upload_date"] <= ts_end)
    ]
    
    # Final Filtered Mapping
    v2c_filtered = dict(zip(videoDf_filtered.display_id.values, videoDf_filtered.channel_id.values))
    
    print(f"Loaded total videos: {len(v2c_all):,}. Filtered for {YEAR_TAG}: {len(v2c_filtered):,} videos.")
    return v2c_filtered

def save_state_and_dict(rows_seen, channelToCommNumbers, dict_path=DICT_PATH, state_path=STATE_PATH):
    # Saves the channel-to-commenter-count dict and the row state.
    with open(dict_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["channel_id", "count"])
        w.writeheader()
        for ch, cnt in channelToCommNumbers.items():
            w.writerow({"channel_id": ch, "count": int(cnt)})
    # Writes the streaming state
    with open(state_path, "w") as f:
        json.dump({"rows_seen": int(rows_seen)}, f)


def flush_authors(authors_dict):
    # Implements the core business logic: Top K + Combinations
    global edges_counter, channelToCommNumbers
    for author, cnt in authors_dict.items():
        if not cnt:
            continue
        # top-K channels this author commented on the most
        topk = [ch for ch, _ in cnt.most_common(TOP_K_PER_AUTHOR)]
        if len(topk) >= MIN_CHANS_FOR_PAIRS:
            # +1 per unordered pair for this author
            for a, b in combinations(sorted(topk), 2):
                edges_counter[(a, b)] += 1
        # Increment unique commenter count for the involved channels
        for ch in topk:
            channelToCommNumbers[ch] += 1
    authors_dict.clear()

# --- MAIN EXECUTION ---
def run_analysis():
    global rows_seen, chunk_idx, user_counts, currentAuthor, edges_counter
    
    # 1. Prepare filtered video-to-channel map
    v2c = load_video_mapping_and_filter(PATH_METADATA)

    print("Starting comments analysis (Local Read)...")
    
    # --- SOLUTION POUR L'ERREUR D'EN-TÊTE ---
    # Nous lisons seulement les colonnes indispensables qui existent
    AUTH_COL_TSV = "author" 
    VID_COL_TSV = "video_id"
    
    try:
        reader = pd.read_csv(
            PATH_COMMENTS,
            sep="\t",
            compression="gzip",
            # We explicitly read ONLY the essential columns
            usecols=[AUTH_COL_TSV, VID_COL_TSV], 
            dtype=str,
            chunksize=CHUNKSIZE,
            on_bad_lines='skip'
        )
    except Exception as e:
        print(f"FATAL: Error reading comments file: {e}")
        return

    # Loop through the comment chunks with progress bar
    # We estimate the number of chunks based on the total number of comments in the dataset (~77M)
    estimated_chunks = 77000000 // CHUNKSIZE
    
    for chunk in tqdm(reader, desc="Streaming comments in chunks", total=estimated_chunks):
        chunk_idx += 1
        
        # Resume Logic: Skip chunks already processed
        if rows_seen > 0 and chunk_idx * CHUNKSIZE <= rows_seen:
             continue 
        
        if MAX_ROWS and rows_seen >= MAX_ROWS:
            break

        # Limit Logic: Adjust the last chunk if needed
        if MAX_ROWS:
            remaining = MAX_ROWS - rows_seen
            if len(chunk) > remaining:
                chunk = chunk.iloc[:remaining]

        # 1. Mapping & Filtering (Vectorized)
        
        # Rename column 'author' to 'author_id' to match internal logic
        chunk = chunk.rename(columns={AUTH_COL_TSV: 'author_id'})
        
        # Drop rows where essential data is missing
        chunk = chunk.dropna(subset=["author_id", "video_id"])
        
        # 2. Mapping Video -> Chaîne (Method: .map() vectorisée)
        # Drop rows missing map or author
        chunk["channel_id"] = chunk["video_id"].map(v2c)
        chunk = chunk.dropna(subset=["author_id", "channel_id"])
        
        if chunk.empty:
             rows_seen += len(chunk)
             continue

        # 3. Aggregate per Author (Efficient Pandas method)
        # update per-author channel counts (counts, not just unique)
        for author, series in chunk.groupby("author_id")["channel_id"]:
            vc = series.value_counts()
            user_counts[author].update(vc.to_dict())
            currentAuthor = author

        rows_seen += len(chunk)

        # 4. Flush Periodically (Saves memory)
        if len(user_counts) > AUTHOR_FLUSH_THRESHOLD:
            flush_authors(user_counts)

        # 5. Checkpoint
        if chunk_idx % CHECKPOINT_EVERY == 0:
            with open(CHECKPOINT_PATH, "wb") as f:
                pickle.dump(edges_counter, f)

            save_state_and_dict(rows_seen, channelToCommNumbers)
            # Colab Prototype Print
            print(f"current Author = {currentAuthor}")
            print(f"[checkpoint] rows_seen={rows_seen:,}, authors_tracked={len(user_counts):,}, unique_edges={len(edges_counter):,}")
            
    # --- FINALIZATION ---
    flush_authors(user_counts) # Final flush

    save_state_and_dict(rows_seen, channelToCommNumbers) # Final state save

    # Colab Prototype Print
    print(f"Processed ~{rows_seen:,} comment rows; unique edges: {len(edges_counter):,}")

    edges_df = pd.DataFrame(((a, b, w) for (a, b), w in edges_counter.items()),
                            columns=["src", "dst", "weight"])
    edges_df.to_csv(EDGES_OUT, index=False)
    # Colab Prototype Print
    print(f"Wrote edges → {EDGES_OUT}")
    print(f"Last author seen = {currentAuthor}")
    
    # Cleanup
    if os.path.exists(CHECKPOINT_PATH):
        os.remove(CHECKPOINT_PATH)
        print("Checkpoint removed.")


if __name__ == "__main__":
    run_analysis()