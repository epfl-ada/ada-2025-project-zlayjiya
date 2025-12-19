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
    Note: The helper file does NOT contain 'title', 'description', or 'tags'.
    Use load_video_metadata_with_text() if you need these fields.
   
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
    
    # Check if requesting columns that don't exist in helper file
    if columns:
        missing_cols = []
        # Try to read just to check what columns exist
        try:
            df_temp = pd.read_feather(local_path, columns=None, dtype_backend="pyarrow")
            available_cols = set(df_temp.columns)
            requested_cols = set(columns)
            missing_cols = requested_cols - available_cols
            if missing_cols:
                print(f"Warning: Columns {missing_cols} not in helper file.")
                print("Helper file excludes: 'title', 'description', 'tags'")
                print("Use load_video_metadata_with_text() if you need these fields.")
        except:
            pass
        
    df = pd.read_feather(local_path, columns=columns, dtype_backend="pyarrow")
    print(f"Loaded {len(df):,} video records.")
    return df


def load_video_metadata_with_text(jsonl_path=None, sample_size=None, channel_filter=None):
    """
    Loads video metadata from the original JSONL file (includes title, description).
    This is slower but includes all fields.
    
    Parameters:
    -----------
    jsonl_path : str, optional
        Path to yt_metadata_en.jsonl.gz. If None, will try to download.
    sample_size : int, optional
        If provided, only load this many rows (for testing)
    channel_filter : set/list, optional
        If provided, only load videos from these channel IDs (much faster!)
    
    Returns:
    --------
    DataFrame with all fields including 'channel_id', 'title', 'description'
    """
    import gzip
    import json
    
    if jsonl_path is None:
        jsonl_path = "yt_metadata_en.jsonl.gz"
        if not os.path.exists(jsonl_path):
            print("JSONL file not found. You need to download yt_metadata_en.jsonl.gz")
            print("This file is large (~10GB). Consider using load_video_metadata() instead.")
            return pd.DataFrame()
    
    print(f"Loading video metadata from {jsonl_path}...")
    if channel_filter:
        channel_filter = set(channel_filter)
        print(f"Filtering for {len(channel_filter)} channels...")
    else:
        print("This may take a while (file is large)...")
    
    records = []
    total_processed = 0
    with gzip.open(jsonl_path, 'rt', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if sample_size and len(records) >= sample_size:
                break
            
            total_processed += 1
            
            try:
                record = json.loads(line)
                channel_id = record.get('channel_id')
                
                # Skip if not in filter
                if channel_filter and channel_id not in channel_filter:
                    continue
                
                # Keep only needed fields to save memory
                records.append({
                    'channel_id': channel_id,
                    'title': record.get('title', ''),
                    'description': record.get('description', ''),
                    'display_id': record.get('display_id')
                })
            except:
                continue
            
            if total_processed % 1000000 == 0:
                print(f"  Processed {total_processed:,} records, kept {len(records):,}...")
    
    df = pd.DataFrame(records)
    print(f"Loaded {len(df):,} video records with text fields from {total_processed:,} total.")
    return df


def stream_video_metadata_from_zip(zip_path, channel_filter, max_videos_per_channel=None):
    """
    Streams video metadata directly from the YouNiverse dataset zip file.
    Much more efficient than extracting the entire file first.
    
    Parameters:
    -----------
    zip_path : str
        Path to youniverse-dataset.zip
    channel_filter : set/list
        Only load videos from these channel IDs
    max_videos_per_channel : int, optional
        Maximum videos to load per channel
    
    Returns:
    --------
    DataFrame with 'channel_id', 'title', 'description' columns
    """
    import zipfile
    import gzip
    import json
    from io import BytesIO
    
    print(f"Streaming video metadata from {zip_path}...")
    print(f"Filtering for {len(channel_filter)} channels...")
    
    channel_filter = set(channel_filter)
    records = []
    channel_counts = {ch: 0 for ch in channel_filter}
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            # Find the metadata file in the zip
            metadata_file = None
            for name in zf.namelist():
                if 'yt_metadata_en.jsonl.gz' in name:
                    metadata_file = name
                    break
            
            if not metadata_file:
                print("Error: yt_metadata_en.jsonl.gz not found in zip")
                return pd.DataFrame()
            
            print(f"Reading {metadata_file} from zip...")
            
            # Read the gzipped file from within the zip
            with zf.open(metadata_file) as gz_data:
                with gzip.open(BytesIO(gz_data.read()), 'rt', encoding='utf-8') as f:
                    total_processed = 0
                    for line in f:
                        total_processed += 1
                        
                        try:
                            record = json.loads(line)
                            channel_id = record.get('channel_id')
                            
                            # Skip if not in filter
                            if channel_id not in channel_filter:
                                continue
                            
                            # Skip if we have enough for this channel
                            if max_videos_per_channel and channel_counts[channel_id] >= max_videos_per_channel:
                                continue
                            
                            records.append({
                                'channel_id': channel_id,
                                'title': record.get('title', ''),
                                'description': record.get('description', ''),
                                'tags': record.get('tags', '')
                            })
                            
                            channel_counts[channel_id] += 1
                            
                            # Check if we're done
                            if max_videos_per_channel:
                                if all(cnt >= max_videos_per_channel for cnt in channel_counts.values()):
                                    print(f"  Reached max_videos_per_channel limit")
                                    break
                            
                        except:
                            continue
                        
                        if total_processed % 1000000 == 0:
                            print(f"  Processed {total_processed:,} records, kept {len(records):,}...")
        
        df = pd.DataFrame(records)
        print(f"\nLoaded {len(df):,} videos from {len([c for c in channel_counts.values() if c > 0])} channels")
        print(f"Processed {total_processed:,} total records")
        
        return df
        
    except Exception as e:
        print(f"Error streaming from zip: {e}")
        print("Trying to extract file first...")
        return pd.DataFrame()

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