"""
Community detection analysis on the TeleScope dataset.
Based on the Channel-to-Channel graph (CID).

Generates CSV outputs and PNG charts with named communities.
"""

import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from collections import Counter
import json
import re

# ============================================================
# CONFIGURATION
# ============================================================

COLORS = ["#2E5395", "#5B8DD9", "#85B09A", "#E8A33D", "#C0392B",
          "#8E44AD", "#16A085", "#D35400", "#2C3E50", "#7F8C8D"]

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 11,
    "axes.titlesize": 13,
    "axes.labelsize": 12,
    "figure.dpi": 150,
    "savefig.dpi": 150,
    "savefig.bbox": "tight"
})


# ============================================================
# 1. LOAD THE GRAPH
# ============================================================

def load_channel_graph(edgelist_path):
    """
    Load the Channel-to-Channel graph using chunked reading (low memory).

    Format:
        msg_source_ch, msg_dest_ch, list_of_msg_source_ids
        1375981076, 1000015666, "[5209, 5208, ...]"
    """
    print("[1/7] Loading the graph (chunked)...")

    G = nx.DiGraph()
    chunk_size = 100_000
    total_rows = 0

    for chunk in pd.read_csv(
        edgelist_path,
        sep=",",
        header=0,
        usecols=["msg_source_ch", "msg_dest_ch"],
        dtype={"msg_source_ch": str, "msg_dest_ch": str},
        chunksize=chunk_size,
        engine="c"
    ):
        G.add_edges_from(zip(chunk["msg_source_ch"], chunk["msg_dest_ch"]))
        total_rows += len(chunk)
        print(f"   -> Processed: {total_rows:,} rows...", end="\r")

    print()
    print(f"   -> Total rows: {total_rows:,}")
    print(f"   -> Nodes: {G.number_of_nodes():,}")
    print(f"   -> Edges: {G.number_of_edges():,}")
    return G


# ============================================================
# 2. BASIC STATISTICS
# ============================================================

def compute_basic_stats(G):
    """Compute basic statistics of the graph."""
    print("[2/7] Computing statistics...")

    if G.is_directed():
        components = list(nx.weakly_connected_components(G))
    else:
        components = list(nx.connected_components(G))

    stats = {
        "n_nodes": G.number_of_nodes(),
        "n_edges": G.number_of_edges(),
        "n_components": len(components),
        "largest_component_size": max(len(c) for c in components) if components else 0,
        "avg_degree": sum(dict(G.degree()).values()) / G.number_of_nodes(),
        "density": nx.density(G)
    }

    for k, v in stats.items():
        print(f"   -> {k}: {v:.4f}" if isinstance(v, float) else f"   -> {k}: {v:,}")

    return stats


# ============================================================
# 3. COMMUNITY DETECTION (LOUVAIN)
# ============================================================

def detect_communities(G, resolution=1.0, seed=42):
    """Detect communities using the Louvain algorithm."""
    print("[3/7] Detecting communities (Louvain)...")

    G_undirected = G.to_undirected()

    communities = nx.community.louvain_communities(
        G_undirected,
        weight=None,
        resolution=resolution,
        seed=seed
    )

    print(f"   -> Communities detected: {len(communities)}")

    sizes = sorted([len(c) for c in communities], reverse=True)
    print(f"   -> Largest community: {sizes[0]:,} nodes")
    print(f"   -> Smallest community: {sizes[-1]:,} nodes")
    print(f"   -> Median size: {sizes[len(sizes)//2]:,} nodes")

    return communities


# ============================================================
# 4. LOAD LANGUAGE METADATA
# ============================================================

def load_language_metadata(language_path):
    """Load channel language metadata from TeleScope CSV."""
    print("[4/7] Loading language metadata...")

    df = pd.read_csv(
        language_path,
        sep="\t",        # au lieu de ","
        dtype=str,
        index_col=0
    )

    print(f"   -> Columns: {list(df.columns)}")

    # Rename columns to standard names (remove extra spaces)
    df.columns = [c.strip() for c in df.columns]

    # Identify ID and language columns
    id_col = "File Names"
    lang_col = "detected_language"

    if id_col not in df.columns or lang_col not in df.columns:
        print(f"   -> ERROR: expected columns not found. Got: {list(df.columns)}")
        return {}

    # Build the mapping
    language_map = {}
    for _, row in df.iterrows():
        cid = str(row[id_col]).strip()
        lang = str(row[lang_col]).strip()
        language_map[cid] = lang

    print(f"   -> Channels with language info: {len(language_map):,}")

    # Debug: show samples
    sample = list(language_map.items())[:5]
    print(f"   -> Sample: {sample}")

    return language_map

# ============================================================
# 5. NAME COMMUNITIES
# ============================================================

def name_communities(communities, language_map):
    """
    Assign a name to each community based on its dominant language.

    Returns a dict: community_id -> community_name
    """
    print("[5/7] Naming communities by dominant language...")

    # Language code to human-readable name
    LANG_NAMES = {
        "ru": "Russian", "en": "English", "es": "Spanish",
        "fr": "French", "de": "German", "it": "Italian",
        "pt": "Portuguese", "tr": "Turkish", "ar": "Arabic",
        "fa": "Persian", "zh": "Chinese", "ja": "Japanese",
        "ko": "Korean", "hi": "Hindi", "id": "Indonesian",
        "uk": "Ukrainian", "pl": "Polish", "nl": "Dutch",
        "vi": "Vietnamese", "th": "Thai", "he": "Hebrew",
        "ha": "Hausa", "yo": "Yoruba", "ig": "Igbo",
        "am": "Amharic", "sw": "Swahili",
    }

    community_names = {}

    for comm_id, nodes in enumerate(communities):
        languages = [language_map.get(n, "Unknown") for n in nodes]
        lang_counts = pd.Series(languages).value_counts()

        if len(lang_counts) == 0:
            name = f"Community_{comm_id}"
        else:
            dominant_lang = lang_counts.index[0]
            share = lang_counts.iloc[0] / len(languages)
            readable = LANG_NAMES.get(dominant_lang, dominant_lang.upper())
            name = f"{readable} ({share:.0%})"

        community_names[comm_id] = name

    # Print top 10 names
    print("   -> Top 10 community names:")
    for i in range(min(10, len(community_names))):
        print(f"      #{i+1}: {community_names[i]}")

    return community_names


# ============================================================
# 6. EXPORT CSV RESULTS
# ============================================================

def export_communities(communities, output_path):
    """Export community assignments to CSV."""
    rows = []
    for comm_id, nodes in enumerate(communities):
        for node in nodes:
            rows.append({"channel_id": node, "community_id": comm_id})

    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)
    print(f"   -> Communities exported: {output_path} ({len(df):,} rows)")
    return df


def export_community_sizes(communities, output_path):
    """Export community sizes to CSV."""
    rows = [
        {"community_id": i, "size": len(c)}
        for i, c in enumerate(communities)
    ]
    df = pd.DataFrame(rows).sort_values("size", ascending=False)
    df.to_csv(output_path, index=False)
    print(f"   -> Sizes exported: {output_path}")
    return df


def export_community_names(community_names, output_path):
    """Export community names to CSV."""
    rows = [
        {"community_id": k, "community_name": v}
        for k, v in community_names.items()
    ]
    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)
    print(f"   -> Names exported: {output_path}")
    return df


# ============================================================
# 7. GENERATE CHARTS (PNG)
# ============================================================

def plot_community_size_distribution(sizes, output_path):
    """Histogram of community sizes (log scale on y-axis)."""
    print("[7/7] Generating community size distribution chart...")

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(sizes, bins=50, color=COLORS[0], edgecolor="white")
    ax.set_yscale("log")
    ax.set_xlabel("Community size (number of channels)")
    ax.set_ylabel("Number of communities (log scale)")
    ax.set_title("Distribution of community sizes")
    ax.grid(True, linestyle="--", alpha=0.4)
    fig.savefig(output_path)
    plt.close(fig)
    print(f"   -> Saved: {output_path}")


def plot_top_communities(sizes, community_names, top_n, output_path):
    """Bar chart of the top N largest communities with names as labels."""
    print(f"[7/7] Generating top {top_n} communities chart...")

    top_sizes = sizes[:top_n]
    indices = np.arange(len(top_sizes))
    labels = [community_names.get(i, f"Community_{i}") for i in range(top_n)]

    fig, ax = plt.subplots(figsize=(13, 6))
    bars = ax.bar(indices, top_sizes, color=COLORS[1], edgecolor="white")
    ax.set_xlabel("Community")
    ax.set_ylabel("Number of channels")
    ax.set_title(f"Top {top_n} largest communities (named by dominant language)")
    ax.set_xticks(indices)
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
    ax.grid(True, axis="y", linestyle="--", alpha=0.4)

    for bar, val in zip(bars, top_sizes):
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height(),
                f"{val:,}", ha="center", va="bottom", fontsize=7)

    fig.savefig(output_path)
    plt.close(fig)
    print(f"   -> Saved: {output_path}")


def plot_degree_distribution(G, output_path):
    """Log-log plot of the degree distribution."""
    print("[7/7] Generating degree distribution chart...")

    degrees = [d for _, d in G.degree() if d > 0]
    values, counts = np.unique(degrees, return_counts=True)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.loglog(values, counts, "o", color=COLORS[2], markersize=4)
    ax.set_xlabel("Degree (log scale)")
    ax.set_ylabel("Frequency (log scale)")
    ax.set_title("Degree distribution (log-log)")
    ax.grid(True, which="both", linestyle="--", alpha=0.4)
    fig.savefig(output_path)
    plt.close(fig)
    print(f"   -> Saved: {output_path}")


def plot_community_graph(G, communities, community_names,
                         top_n, max_nodes, output_path):
    """Visualize a subgraph of the top N communities (sampled)."""
    print(f"[7/7] Generating graph visualization (top {top_n} communities)...")

    sorted_comms = sorted(communities, key=len, reverse=True)[:top_n]

    sampled_nodes = []
    for comm in sorted_comms:
        comm_list = list(comm)
        n_sample = min(len(comm_list), max_nodes // top_n)
        sampled_nodes.extend(np.random.choice(comm_list, n_sample, replace=False))

    subgraph = G.subgraph(sampled_nodes).to_undirected()
    pos = nx.circular_layout(subgraph)

    # Map node -> community index
    node_to_comm = {}
    for i, comm in enumerate(sorted_comms):
        for n in comm:
            node_to_comm[n] = i

    # Build node colors and labels
    node_colors = [COLORS[node_to_comm.get(n, 0) % len(COLORS)]
                   for n in subgraph.nodes()]

    fig, ax = plt.subplots(figsize=(12, 10))
    nx.draw_networkx_nodes(subgraph, pos, node_size=20,
                           node_color=node_colors, alpha=0.85, ax=ax)
    nx.draw_networkx_edges(subgraph, pos, alpha=0.15,
                           width=0.4, ax=ax)

    # Legend with community names
    for i, comm in enumerate(sorted_comms):
        ax.scatter([], [], c=COLORS[i % len(COLORS)],
                   label=community_names.get(i, f"Community_{i}"),
                   s=50)
    ax.legend(loc="upper right", fontsize=9, framealpha=0.9)

    ax.set_title(f"Top {top_n} largest communities (sampled)")
    ax.axis("off")
    fig.savefig(output_path)
    plt.close(fig)
    print(f"   -> Saved: {output_path}")


def plot_resolution_curve(G, resolutions, output_path):
    """Plot number of communities vs. resolution parameter."""
    print("[7/7] Generating resolution curve chart...")

    n_comms = []
    for r in resolutions:
        comms = nx.community.louvain_communities(
            G.to_undirected(), weight=None, resolution=r, seed=42
        )
        n_comms.append(len(comms))
        print(f"   -> Resolution {r}: {len(comms)} communities")

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(resolutions, n_comms, "o-", color=COLORS[3], linewidth=2)
    ax.set_xlabel("Resolution parameter")
    ax.set_ylabel("Number of communities")
    ax.set_title("Number of communities vs. resolution (Louvain)")
    ax.grid(True, linestyle="--", alpha=0.4)
    fig.savefig(output_path)
    plt.close(fig)
    print(f"   -> Saved: {output_path}")


# ============================================================
# 8. MAIN PROGRAM
# ============================================================

if __name__ == "__main__":
    # --- Paths ---
    BASE_DIR = Path.home() / "Documents" / "telescope_data_analysis" / "telescope_files"
    EDGELIST = BASE_DIR / "channel_to_channel_graph.csv"
    LANGUAGE_FILE = BASE_DIR / "Channel_Language.csv"  # ← adapt if JSONL

    OUTPUT_COMMS = BASE_DIR / "communities.csv"
    OUTPUT_SIZES = BASE_DIR / "community_sizes.csv"
    OUTPUT_NAMES = BASE_DIR / "community_names.csv"

    CHARTS_DIR = BASE_DIR / "charts"
    CHARTS_DIR.mkdir(exist_ok=True)

    # --- Load graph ---
    G = load_channel_graph(EDGELIST)

    # --- Basic stats ---
    stats = compute_basic_stats(G)

    # --- Detect communities ---
    communities = detect_communities(G, resolution=1.0, seed=42)

    # --- Load language metadata ---
    language_map = load_language_metadata(LANGUAGE_FILE)

    # --- Name communities ---
    community_names = name_communities(communities, language_map)

    # --- Export CSVs ---
    export_communities(communities, OUTPUT_COMMS)
    df_sizes = export_community_sizes(communities, OUTPUT_SIZES)
    export_community_names(community_names, OUTPUT_NAMES)

    sizes = df_sizes["size"].tolist()

    # --- Generate charts ---
    plot_community_size_distribution(
        sizes, CHARTS_DIR / "community_size_distribution.png"
    )
    plot_top_communities(
        sizes, community_names, top_n=20,
        output_path=CHARTS_DIR / "top_20_communities.png"
    )
    plot_degree_distribution(
        G, CHARTS_DIR / "degree_distribution.png"
    )
    plot_community_graph(
        G, communities, community_names,
        top_n=5, max_nodes=5000,
        output_path=CHARTS_DIR / "community_graph.png"
    )
    plot_resolution_curve(
        G, resolutions=[0.5, 0.8, 1.0, 1.2, 1.5, 2.0],
        output_path=CHARTS_DIR / "resolution_curve.png"
    )

    print("\n✅ Analysis completed.")
    print(f"   CSVs and charts saved in: {BASE_DIR}")