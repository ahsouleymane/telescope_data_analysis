"""
Community detection analysis on the TeleScope dataset.
Based on the Channel-to-Channel graph (CID).

Minimal migration to igraph + Leiden, with GEXF export for Gephi.

What changed vs. the NetworkX/Louvain version:
  - The graph is loaded with igraph (faster, less memory on 261k nodes).
  - Communities are detected with Leiden (leidenalg), which guarantees
    connected communities — unlike Louvain.
  - The community-level graph is no longer drawn with Matplotlib:
    it is exported as a GEXF file to be opened in Gephi (ForceAtlas 2,
    node size = channel count, edge width = inter-community links).
  - All other outputs (CSV + README, Matplotlib charts) are unchanged.

What is kept from the previous version:
  - §4.4 NaN handling in language metadata.
  - §4.5 extended LANG_NAMES.
  - §4.6 low-confidence naming with MIN_KNOWN_FOR_NAME.
  - Title-based language enrichment via langdetect (§4.2).
  - Each CSV in its own folder + README.
  - Charts in charts/community_detection/.

Requires: pip install python-igraph leidenalg langdetect
"""

import igraph as ig
import leidenalg as la
import networkx as nx          # only for stats helper + GEXF export
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

MIN_KNOWN_FOR_NAME = 3
NULL_LANG_VALUES = {"", "nan", "none", "null", "unknown", "nat"}

PROGRAM_NAME = "community_detection"

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
# 1. LOAD THE GRAPH WITH IGRAPH
# ============================================================

def load_channel_graph(edgelist_path):
    """
    Load the Channel-to-Channel graph with igraph.

    igraph uses integer vertex indices internally, so we keep an
    explicit mapping channel_id (str) <-> vertex index (int).
    Returns (G, channel_ids) where channel_ids[i] is the original
    channel ID of vertex i.
    """
    print("[1/7] Loading the graph with igraph (chunked)...")

    edges = []
    seen = set()
    total_rows = 0

    for chunk in pd.read_csv(
        edgelist_path,
        sep=",",
        header=0,
        usecols=["msg_source_ch", "msg_dest_ch"],
        dtype={"msg_source_ch": str, "msg_dest_ch": str},
        chunksize=200_000,
        engine="c"
    ):
        for u, v in zip(chunk["msg_source_ch"], chunk["msg_dest_ch"]):
            edges.append((u, v))
            seen.add(u)
            seen.add(v)
        total_rows += len(chunk)
        print(f"   -> Processed: {total_rows:,} rows...", end="\r")

    print()
    channel_ids = sorted(seen)
    id_to_idx = {cid: i for i, cid in enumerate(channel_ids)}

    G = ig.Graph(directed=True)
    G.add_vertices(len(channel_ids))
    G.add_edges([(id_to_idx[u], id_to_idx[v]) for u, v in edges])

    print(f"   -> Total rows: {total_rows:,}")
    print(f"   -> Nodes: {G.vcount():,}")
    print(f"   -> Edges: {G.ecount():,}")
    return G, channel_ids


# ============================================================
# 2. BASIC STATISTICS
# ============================================================

def compute_basic_stats(G):
    """Compute basic statistics of the igraph graph."""
    print("[2/7] Computing statistics...")

    # Weakly connected components (directed graph)
    components = G.connected_components(mode="weak")
    sizes = components.sizes()

    degrees = G.degree()
    stats = {
        "n_nodes": G.vcount(),
        "n_edges": G.ecount(),
        "n_components": len(sizes),
        "largest_component_size": max(sizes) if sizes else 0,
        "avg_degree": sum(degrees) / G.vcount(),
        "density": G.density(),
    }

    for k, v in stats.items():
        print(f"   -> {k}: {v:.4f}" if isinstance(v, float) else f"   -> {k}: {v:,}")

    return stats


# ============================================================
# 3. COMMUNITY DETECTION (LEIDEN)
# ============================================================

def detect_communities(G, resolution=1.0, seed=42):
    """
    Detect communities with Leiden (leidenalg).

    Leiden guarantees connected communities, unlike Louvain.
    It works on an undirected graph for the standard modularity
    partition (same methodological choice as before for Louvain:
    documented in the report, since the project's theme concerns
    propagation dynamics where edge direction matters).

    Returns a list of (community_id, set_of_channel_ids), using the
    ORIGINAL channel IDs (not igraph indices) so the rest of the
    pipeline is unchanged.
    """
    print("[3/7] Detecting communities (Leiden)...")

    G_und = G.as_undirected()
    partition = la.find_partition(
        G_und,
        la.RBConfigurationVertexPartition,  # <-- Changement ici
        resolution_parameter=resolution,
        seed=seed,
    )

    # Group igraph vertex indices by community
    comm_to_indices = {}
    for idx, comm_id in enumerate(partition.membership):
        comm_to_indices.setdefault(comm_id, []).append(idx)

    # Convert to channel IDs
    communities = [
        (comm_id, set(channel_ids[i] for i in indices))
        for comm_id, indices in comm_to_indices.items()
    ]

    print(f"   -> Communities detected: {len(communities)}")
    sizes_sorted = sorted([len(c) for _, c in communities], reverse=True)
    print(f"   -> Largest community: {sizes_sorted[0]:,} nodes")
    print(f"   -> Smallest community: {sizes_sorted[-1]:,} nodes")
    print(f"   -> Median size: {sizes_sorted[len(sizes_sorted)//2]:,} nodes")

    return communities


# ============================================================
# 4. LOAD LANGUAGE METADATA (unchanged)
# ============================================================

def load_language_metadata(language_path):
    """Load channel language metadata from TeleScope CSV."""
    print("[4/7] Loading language metadata...")

    df = pd.read_csv(language_path, sep="\t", dtype=str, index_col=0)
    print(f"   -> Columns: {list(df.columns)}")

    df.columns = [c.strip() for c in df.columns]

    id_col = "File Names"
    lang_col = "detected_language"

    if id_col not in df.columns or lang_col not in df.columns:
        print(f"   -> ERROR: expected columns not found. Got: {list(df.columns)}")
        return {}

    language_map = {}
    skipped = 0
    for _, row in df.iterrows():
        cid = str(row[id_col]).strip()
        lang_raw = row[lang_col]
        lang = "" if pd.isna(lang_raw) else str(lang_raw).strip()
        if lang.lower() in NULL_LANG_VALUES:
            skipped += 1
            continue
        language_map[cid] = lang

    print(f"   -> Channels with language info: {len(language_map):,}")
    if skipped:
        print(f"   -> Skipped {skipped:,} rows with missing/invalid language value")
    return language_map


# ============================================================
# 4b. LOAD CHANNEL TITLES (unchanged)
# ============================================================

def load_source_metadata_titles(path):
    """Extract title/username per channel from Source_Channel_Metadata.csv."""
    print("[4b/8] Loading channel titles from Source_Channel_Metadata.csv...")

    titles = {}
    total = 0
    parsed = 0

    for chunk in pd.read_csv(path, dtype=str, chunksize=50_000):
        for _, row in chunk.iterrows():
            total += 1
            cid = str(row["id"]).strip()
            raw = row.get("data")
            if pd.isna(raw):
                continue
            try:
                data = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                continue
            title = (data.get("title") or "").strip()
            username = (data.get("username") or "").strip()
            text = title if title else username
            if text:
                titles[cid] = text
                parsed += 1
        print(f"   -> Processed: {total:,} rows...", end="\r")

    print()
    print(f"   -> Titles/usernames extracted: {parsed:,} / {total:,} rows")
    return titles


# ============================================================
# 4c. ENRICH LANGUAGE MAP FROM TITLES (unchanged)
# ============================================================

def enrich_language_map_from_titles(language_map, titles,
                                    min_confidence=0.70, min_letters=4):
    """Fill gaps in language_map using langdetect on channel titles."""
    try:
        from langdetect import detect_langs, DetectorFactory
        from langdetect.lang_detect_exception import LangDetectException
        DetectorFactory.seed = 42
    except ImportError:
        print("   -> langdetect is not installed (pip install langdetect).")
        print("   -> Skipping title-based language enrichment.")
        return language_map, 0

    print("[4c/8] Enriching language_map from channel titles (langdetect)...")

    to_detect = {cid: text for cid, text in titles.items() if cid not in language_map}
    print(f"   -> Candidates (no known language yet): {len(to_detect):,}")

    added = 0
    checked = 0
    for cid, text in to_detect.items():
        checked += 1
        cleaned = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE).strip()
        letters = re.sub(r"[\d\s_]", "", cleaned)
        if len(letters) < min_letters:
            continue
        try:
            candidates = detect_langs(cleaned)
        except LangDetectException:
            continue
        if not candidates:
            continue
        best = candidates[0]
        if best.prob >= min_confidence:
            language_map[cid] = best.lang
            added += 1
        if checked % 20_000 == 0:
            print(f"   -> Checked: {checked:,} / {len(to_detect):,} "
                  f"(added so far: {added:,})", end="\r")

    print()
    print(f"   -> Added {added:,} channels via title-based language detection")
    print(f"   -> language_map now covers {len(language_map):,} channels total")
    return language_map, added


# ============================================================
# 5. NAME COMMUNITIES (unchanged)
# ============================================================

def name_communities(communities, language_map):
    """Assign a name to each community based on its dominant language."""
    print("[5/7] Naming communities by dominant language...")

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
        "bg": "Bulgarian", "et": "Estonian", "ro": "Romanian",
        "el": "Greek", "sv": "Swedish", "da": "Danish",
        "fi": "Finnish", "no": "Norwegian", "cs": "Czech",
        "sk": "Slovak", "hu": "Hungarian", "sr": "Serbian",
        "hr": "Croatian", "lt": "Lithuanian", "lv": "Latvian",
        "ka": "Georgian", "az": "Azerbaijani", "kk": "Kazakh",
        "uz": "Uzbek", "ur": "Urdu", "bn": "Bengali",
        "ta": "Tamil", "ml": "Malayalam", "my": "Burmese",
        "km": "Khmer", "lo": "Lao", "mn": "Mongolian",
        "si": "Sinhala", "ps": "Pashto", "ku": "Kurdish",
    }

    community_names = {}

    for comm_id, nodes in communities:
        known_languages = [language_map[n] for n in nodes if n in language_map]
        n_known = len(known_languages)
        n_total = len(nodes)

        if n_known == 0:
            name = "Unknown (0 known)"
        elif n_known < MIN_KNOWN_FOR_NAME:
            lang_counts = Counter(known_languages)
            dominant_lang, _ = lang_counts.most_common(1)[0]
            readable = LANG_NAMES.get(dominant_lang, dominant_lang.upper())
            name = f"Unknown (low confidence: {readable}? n={n_known}/{n_total})"
        else:
            lang_counts = Counter(known_languages)
            dominant_lang, cnt = lang_counts.most_common(1)[0]
            share = cnt / n_known
            readable = LANG_NAMES.get(dominant_lang, dominant_lang.upper())
            name = f"{readable} ({share:.0%}, n={n_known}/{n_total})"

        community_names[comm_id] = name

    top_by_size = sorted(communities, key=lambda cn: len(cn[1]), reverse=True)[:10]
    print("   -> Top 10 community names (by size):")
    for rank, (comm_id, nodes) in enumerate(top_by_size, start=1):
        print(f"      #{rank} (id={comm_id}, size={len(nodes):,}): {community_names[comm_id]}")

    return community_names


# ============================================================
# 6. EXPORT CSV (unchanged: each CSV in its own folder + README)
# ============================================================

def export_csv_with_readme(df, output_path, title, description_lines):
    """Export a DataFrame to CSV in its own folder, with a README.md."""
    output_path = Path(output_path)
    folder = output_path.parent / output_path.stem
    folder.mkdir(parents=True, exist_ok=True)

    csv_path = folder / output_path.name
    df.to_csv(csv_path, index=False)

    readme_path = folder / "README.md"
    lines = [f"# {title}", ""]
    lines += description_lines
    lines += [
        "",
        "## File",
        f"- `{output_path.name}` — {len(df):,} rows, {len(df.columns)} columns.",
        "",
        "## Columns",
    ]
    for col in df.columns:
        dtype = str(df[col].dtype)
        example = df[col].iloc[0] if len(df) else ""
        lines.append(f"- `{col}` ({dtype}) — e.g. `{example}`")
    lines.append("")

    readme_path.write_text("\n".join(lines), encoding="utf-8")

    print(f"   -> Exported: {csv_path} ({len(df):,} rows)")
    print(f"   -> README:   {readme_path}")
    return df


def export_communities(communities, output_path):
    """Export community assignments to CSV (with README)."""
    rows = []
    for comm_id, nodes in communities:
        for node in nodes:
            rows.append({"channel_id": node, "community_id": comm_id})

    df = pd.DataFrame(rows)
    return export_csv_with_readme(
        df, output_path,
        title="Community assignments (channel -> community)",
        description_lines=[
            "One row per channel in the Channel-to-Channel graph.",
            "",
            "Each channel is assigned to exactly one Leiden community",
            "(resolution=1.0, seed=42, on the undirected version of the graph).",
            "",
            "- `channel_id`: the channel's numeric ID (as a string).",
            "- `community_id`: the Leiden community ID (integer).",
        ],
    )


def export_community_sizes(communities, output_path):
    """Export community sizes to CSV (with README)."""
    rows = [
        {"community_id": comm_id, "size": len(nodes)}
        for comm_id, nodes in communities
    ]
    df = pd.DataFrame(rows).sort_values("size", ascending=False)
    return export_csv_with_readme(
        df, output_path,
        title="Community sizes",
        description_lines=[
            "One row per detected community, sorted by decreasing size.",
            "",
            "- `community_id`: the Leiden community ID.",
            "- `size`: number of channels in that community.",
        ],
    )


def export_community_names(community_names, output_path):
    """Export community names to CSV (with README)."""
    rows = [
        {"community_id": k, "community_name": v}
        for k, v in community_names.items()
    ]
    df = pd.DataFrame(rows)
    return export_csv_with_readme(
        df, output_path,
        title="Community names (dominant language)",
        description_lines=[
            "One row per community, giving its human-readable name.",
            "",
            "- `community_id`: the Leiden community ID.",
            "- `community_name`: a label built from the dominant language",
            "  among channels with a known language.",
            "",
            "Naming rules:",
            f"- Fewer than {MIN_KNOWN_FOR_NAME} known-language channels:",
            "  `Unknown (low confidence: <Lang>? n=known/total)`.",
            "- Zero known-language channels: `Unknown (0 known)`.",
            "- Otherwise: `<Language> (<share>%, n=known/total)`.",
        ],
    )


# ============================================================
# 7. CHARTS (Matplotlib, unchanged except community graph)
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


def plot_top_communities(df_sizes, community_names, top_n, output_path):
    """Bar chart of the top N largest communities with names as labels."""
    print(f"[7/7] Generating top {top_n} communities chart...")

    top = df_sizes.head(top_n)
    top_sizes = top["size"].tolist()
    top_ids = top["community_id"].tolist()
    indices = np.arange(len(top_sizes))
    labels = [community_names.get(cid, f"Community_{cid}") for cid in top_ids]

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
                bar.get_height(), f"{val:,}",
                ha="center", va="bottom", fontsize=7)

    fig.savefig(output_path)
    plt.close(fig)
    print(f"   -> Saved: {output_path}")


def plot_degree_distribution(G_ig, output_path):
    """CCDF of the degree distribution, log-log scale."""
    print("[7/7] Generating degree distribution (CCDF) chart...")

    degrees = np.array(sorted(d for d in G_ig.degree() if d > 0))
    n = len(degrees)
    unique_degrees = np.unique(degrees)
    idx = np.searchsorted(degrees, unique_degrees, side="left")
    ccdf = (n - idx) / n

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.loglog(unique_degrees, ccdf, "-", color=COLORS[2], linewidth=2)
    ax.set_xlabel("Degree k (log scale)")
    ax.set_ylabel("P(Degree >= k)  (log scale)")
    ax.set_title("Degree distribution - complementary CDF (log-log)")
    ax.grid(True, which="both", linestyle="--", alpha=0.4)
    fig.savefig(output_path)
    plt.close(fig)
    print(f"   -> Saved: {output_path}")


def plot_resolution_curve(G, resolutions, output_path):
    """Plot number of communities vs. resolution (Leiden)."""
    print("[7/7] Generating resolution curve chart...")

    G_und = G.as_undirected()
    n_comms = []
    for r in resolutions:
        p = la.find_partition(
            G_und, la.RBConfigurationVertexPartition,
            resolution_parameter=r, seed=42,
        )
        n_comms.append(len(set(p.membership)))
        print(f"   -> Resolution {r}: {n_comms[-1]} communities")

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(resolutions, n_comms, "o-", color=COLORS[3], linewidth=2)
    ax.set_xlabel("Resolution parameter")
    ax.set_ylabel("Number of communities")
    ax.set_title("Number of communities vs. resolution (Leiden)")
    ax.grid(True, linestyle="--", alpha=0.4)
    fig.savefig(output_path)
    plt.close(fig)
    print(f"   -> Saved: {output_path}")


# ============================================================
# 7b. EXPORT META-GRAPH FOR GEPHI (replaces plot_community_graph)
# ============================================================

def export_meta_graph_for_gephi(G, communities, community_names,
                                output_path, top_n=None):
    """
    Export a community-level meta-graph as GEXF for Gephi.

    - One node per community (optionally only the top_n largest).
    - Node attribute `size` = number of channels in that community.
    - Node attribute `label` = community name (dominant language).
    - Edge attribute `weight` = number of real inter-community
      connections in the FULL graph (not a sample).

    In Gephi:
      1. File -> Open -> select the .gexf file.
      2. Layout -> ForceAtlas 2 -> Run.
      3. Appearance -> Nodes -> Size -> based on `size`.
      4. Appearance -> Edges -> Width -> based on `weight`.
      5. Preview -> Export -> PNG / PDF.
    """
    print(f"[7/7] Exporting meta-graph for Gephi (top_n={top_n})...")

    if top_n is not None:
        selected = sorted(communities, key=lambda cn: len(cn[1]), reverse=True)[:top_n]
    else:
        selected = communities

    node_to_comm = {}
    for comm_id, nodes in selected:
        for n in nodes:
            node_to_comm[n] = comm_id

    # Count real inter-community edges across the FULL graph.
    # igraph gives us vertex indices; map back to channel IDs.
    edge_weights = Counter()
    for e in G.es:
        u = channel_ids[e.source]
        v = channel_ids[e.target]
        cu = node_to_comm.get(u)
        cv = node_to_comm.get(v)
        if cu is not None and cv is not None and cu != cv:
            key = tuple(sorted((cu, cv)))
            edge_weights[key] += 1

    # Build NetworkX graph (GEXF export is native in NetworkX)
    meta = nx.Graph()
    for comm_id, nodes in selected:
        meta.add_node(
            int(comm_id),
            size=len(nodes),
            label=community_names.get(comm_id, f"Community_{comm_id}"),
        )
    for (cu, cv), w in edge_weights.items():
        meta.add_edge(int(cu), int(cv), weight=int(w))

    nx.write_gexf(meta, output_path)
    print(f"   -> Saved: {output_path} ({meta.number_of_nodes()} nodes, "
          f"{meta.number_of_edges()} edges)")


# ============================================================
# 8. MAIN PROGRAM
# ============================================================

if __name__ == "__main__":
    from config import BASE_DIR

    EDGELIST = BASE_DIR / "channel_to_channel_graph.csv"
    LANGUAGE_FILE = BASE_DIR / "Channel_Language.csv"
    SOURCE_METADATA_FILE = BASE_DIR / "Source_Channel_Metadata.csv"

    OUTPUT_COMMS = BASE_DIR / "communities.csv"
    OUTPUT_SIZES = BASE_DIR / "community_sizes.csv"
    OUTPUT_NAMES = BASE_DIR / "community_names.csv"

    CHARTS_DIR = BASE_DIR / "charts" / PROGRAM_NAME
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)

    (CHARTS_DIR / "README.md").write_text(
        "# Charts — Community detection (igraph + Leiden)\n\n"
        "All outputs produced by `community_detection.py`.\n\n"
        "## Matplotlib PNG\n"
        "- `community_size_distribution.png` — histogram of community sizes (log y).\n"
        "- `top_20_communities.png` — 20 largest communities, named by dominant language.\n"
        "- `degree_distribution.png` — CCDF of node degree (log-log).\n"
        "- `resolution_curve.png` — number of communities vs. Leiden resolution.\n\n"
        "## Gephi\n"
        "- `meta_graph.gexf` — community-level meta-graph to open in Gephi.\n"
        "  Node size = channel count, edge width = inter-community links.\n",
        encoding="utf-8",
    )

    # --- Load graph ---
    G, channel_ids = load_channel_graph(EDGELIST)

    # --- Basic stats ---
    stats = compute_basic_stats(G)

    # --- Detect communities (Leiden) ---
    communities = detect_communities(G, resolution=1.0, seed=42)

    # --- Load language metadata ---
    language_map = load_language_metadata(LANGUAGE_FILE)
    coverage_before = sum(1 for n in channel_ids if n in language_map)
    print(f"   -> Coverage before title enrichment: {coverage_before:,} / "
          f"{len(channel_ids):,} graph channels "
          f"({100*coverage_before/len(channel_ids):.1f}%)")

    # --- Enrich language metadata from Source_Channel_Metadata.csv ---
    titles = load_source_metadata_titles(SOURCE_METADATA_FILE)
    language_map, n_added = enrich_language_map_from_titles(language_map, titles)
    coverage_after = sum(1 for n in channel_ids if n in language_map)
    print(f"   -> Coverage after title enrichment: {coverage_after:,} / "
          f"{len(channel_ids):,} graph channels "
          f"({100*coverage_after/len(channel_ids):.1f}%)")

    # --- Name communities ---
    community_names = name_communities(communities, language_map)

    # --- Export CSVs (each in its own folder, with a README) ---
    export_communities(communities, OUTPUT_COMMS)
    df_sizes = export_community_sizes(communities, OUTPUT_SIZES)
    export_community_names(community_names, OUTPUT_NAMES)

    sizes = df_sizes["size"].tolist()

    # --- Matplotlib charts ---
    plot_community_size_distribution(
        sizes, CHARTS_DIR / "community_size_distribution.png"
    )
    plot_top_communities(
        df_sizes, community_names, top_n=20,
        output_path=CHARTS_DIR / "top_20_communities.png"
    )
    plot_degree_distribution(
        G, CHARTS_DIR / "degree_distribution.png"
    )
    plot_resolution_curve(
        G, resolutions=[0.5, 0.8, 1.0, 1.2, 1.5, 2.0],
        output_path=CHARTS_DIR / "resolution_curve.png"
    )

    # --- GEXF export for Gephi (replaces the Matplotlib community graph) ---
    export_meta_graph_for_gephi(
        G, communities, community_names,
        top_n=5,
        output_path=CHARTS_DIR / "meta_graph.gexf"
    )

    print("\n✅ Analysis completed.")
    print(f"   CSVs and charts saved in: {BASE_DIR}")
    print(f"   Open {CHARTS_DIR / 'meta_graph.gexf'} in Gephi for the meta-graph.")