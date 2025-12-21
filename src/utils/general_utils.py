import numpy as np
import pandas as pd
from IPython.display import display


def gini(arr):
    arr = np.asarray(arr, dtype=float)
    if arr.size == 0 or np.allclose(arr.sum(), 0):
        return 0.0
    arr = np.sort(arr)
    n = arr.size
    cumx = np.cumsum(arr)
    return (n + 1 - 2 * (cumx / cumx[-1]).sum()) / n


def identify_black_holes(node_df, q, min_size=10):
    out = []
    for comm, df_c in node_df.groupby("community"):
        df_c = df_c.copy()
        if len(df_c) < min_size:
            continue

        s_thr = df_c["strength"].quantile(q)
        d_thr = df_c["degree"].quantile(q)

        top_strength = df_c[df_c["strength"] >= s_thr][["channel_id", "community", "strength"]]
        top_degree = df_c[df_c["degree"] >= d_thr][["channel_id", "degree"]]
        black = top_strength.merge(top_degree, on="channel_id", how="inner")
        out.append(black)

    if len(out) == 0:
        return pd.DataFrame(columns=["channel_id", "community", "strength", "degree"])

    return pd.concat(out, ignore_index=True)

    

def compute_concentration(node_df, bh_df, comm_summary):
    totals = comm_summary[["community", "total_strength"]].copy()

    total_degree = (
        node_df.groupby("community")["degree"]
        .sum()
        .reset_index(name="total_degree")
    )

    totals = totals.merge(total_degree, on="community", how="left")

    bh_totals = (
        bh_df.groupby("community")
        .agg(
            bh_strength=("strength", "sum"),
            bh_degree=("degree", "sum"),
            n_blackholes=("channel_id", "nunique"),
        )
        .reset_index()
    )

    out = totals.merge(bh_totals, on="community", how="inner")

    out["strength_concentration_ratio"] = (
        out["bh_strength"] / out["total_strength"]
    )
    out["degree_concentration_ratio"] = (
        out["bh_degree"] / out["total_degree"]
    )

    return out[[
        "community",
        "n_blackholes",
        "strength_concentration_ratio",
        "degree_concentration_ratio",
    ]].sort_values("strength_concentration_ratio", ascending=False)


def analyze_black_holes(bh_df, comm_summary, node_df, communities=None, top_k=20):
    bh = bh_df.copy()
    if communities is not None:
        bh = bh[bh["community"].isin(communities)].copy()

    totals_strength = comm_summary[["community", "total_strength"]].copy()

    totals_degree = (
        node_df.groupby("community", as_index=False)
        .agg(total_degree=("degree", "sum"))
    )

    totals = totals_strength.merge(totals_degree, on="community", how="inner")

    bh = bh.merge(totals, on="community", how="left")

    bh["strength_share"] = bh["strength"] / bh["total_strength"]
    bh["degree_share"]   = bh["degree"]   / bh["total_degree"]

    for comm in sorted(bh["community"].dropna().unique()):
        print(f"\n=== Community {comm} – Top dominant black holes ===")
        display(
            bh[bh["community"] == comm]
            .sort_values("strength", ascending=False)
            .head(top_k)[
                ["channel_id", "strength", "strength_share", "degree", "degree_share"]
            ]
        )

    return bh


def top_galaxies_strength_share_df(comm_summary, top_pct):
    df = comm_summary.copy()

    total_attention = df["total_strength"].sum()

    df = df.sort_values("total_strength", ascending=False)

    k = max(1, int(round(len(df) * top_pct / 100.0)))

    out = df.head(k)[["community", "n_nodes", "total_strength"]].copy()
    out["strength_share_total"] = out["total_strength"] / total_attention
