# src/data/load.py
import pandas as pd
import fsspec
import os
import requests
import sys
import csv
from collections import defaultdict

ZENODO_RECORD_ID = "4650046"

def get_file_url(key):
    """Constructs a direct download URL for a Zenodo file."""
    return f"https://zenodo.org/records/{ZENODO_RECORD_ID}/files/{key}?download=1"


def load_video_metadata(columns=None, local_path="yt_metadata_helper.feather"):
    """
    Downloads (if needed) and loads the video metadata feather file.
   
    """
    print("Loading Video Metadata...")
    if not os.path.exists(local_path):
        print(f"Downloading yt_metadata_helper.feather to {local_path}...")
        URL = get_file_url("yt_metadata_helper.feather")
        with requests.get(URL, stream=True) as r:
            r.raise_for_status()
            total = int(r.headers.get("content-length", 0))
            done = 0
            with open(local_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024*1024):
                    if chunk:
                        f.write(chunk); done += len(chunk)
                        if total: print(f"\\r{done/total:.1%}", end=""); sys.stdout.flush()
        print("\nDownload complete.")
        
    df = pd.read_feather(local_path, columns=columns, dtype_backend="pyarrow")
    print(f"Loaded {len(df):,} video records.")
    return df

def load_edges(path="data/processed/channel_edges.csv"):
    """
    Loads the processed edge list.
    """
    print(f"Loading edges from {path}...")
    return pd.read_csv(path)

def load_commenter_counts(dict_path):
    """
    Loads the dictionary mapping channel_id to its unique commenter count.
   
    """
    print(f"Loading commenter counts from {dict_path}...")
    channelToCommNumbers = defaultdict(int)
    if not os.path.exists(dict_path):
        print("Warning: Commenter count file not found. Returning empty dict.")
        return channelToCommNumbers
        
    with open(dict_path, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            try:
                channelToCommNumbers[row["channel_id"]] = int(row["count"])
            except Exception:
                continue
    print(f"Loaded {len(channelToCommNumbers):,} channel commenter counts.")
    return channelToCommNumbers