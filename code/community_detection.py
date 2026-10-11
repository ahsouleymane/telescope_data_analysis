"""
Community detection analysis on the TeleScope dataset.
Based on the Channel-to-Channel graph (CID).

Generates CSV outputs and PNG charts with named communities.

Fixes applied vs. previous version (see progress report §4):
  - §4.3 Indexing bug in plot_top_communities / plot_community_graph:
    labels now use the real Louvain community_id instead of the rank
    in the size-sorted list.
  - §4.4 NaN handling: missing/"nan" language values are filtered out
    both when loading Channel_Language.csv and when aggregating, so
    they never get counted as a valid dominant language ("NAN (100%)").
  - §4.5 LANG_NAMES dictionary extended with languages observed in the
    data that were missing (bg, et, ro, el, sv, da, fi, no, cs, sk, hu,
    sr, hr, lt, lv, ka, az, kk, uz, ur, bn, ta, ml, my, km, lo, mn, si,
    ps, ku, az).
  - §4.6 Statistical reliability: a community is only named with a
    language if at least MIN_KNOWN_FOR_NAME channels with a known
    language are present in it; otherwise it is labelled
    "Unknown (low confidence)" and the known/total ratio is reported
    alongside the dominant share so small-sample names are visible as
    such rather than looking as reliable as large ones.

§4.2 (99.3% of channels in UNKNOWN communities) is a data-coverage
issue, not a code bug: Channel_Language.csv only covers ~71k of the
~261k channels in the graph. It is now addressed: load_source_metadata_titles
extracts each channel's title/username from Source_Channel_Metadata.csv
(534k rows, far more channels than Channel_Language.csv), and
enrich_language_map_from_titles runs language detection (langdetect)
on those titles to fill in ONLY the channels missing from
Channel_Language.csv — Channel_Language.csv stays authoritative and is
never overwritten, since a human/pipeline-verified language label is
more trustworthy than a guess from a short channel title.

Requires: pip install langdetect

§4.7 (graph converted to undirected before Louvain) is a deliberate,
documented methodological choice, not a bug: Louvain requires an
undirected graph. It is called out in the report since the project's
theme concerns propagation dynamics, where edge direction matters.

Readability changes (not bugs, requested separately):
  - plot_degree_distribution now draws the CCDF (complementary
    cumulative distribution) of the degree instead of a raw scatter
    of degree vs. frequency: same log-log power-law reading, but a
    smooth monotonic curve instead of a noisy point cloud.
  - plot_community_graph now draws a community-level "meta-graph"
    (one node per community, sized by channel count; edges weighted
    by the real number of inter-community connections in the full
    graph; force-directed layout) instead of a circular layout of
    thousands of sampled individual channels, which tangled into an
    unreadable mass of crossing edges regardless of sample size.
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

# §4.6: minimum number of channels with a KNOWN language required
# before a community is named after a dominant language rather than
# flagged as low-confidence.
MIN_KNOWN_FOR_NAME = 3

# Values that mean "no language known" and must never be treated as
# a real language (§4.4).
NULL_LANG_VALUES = {"", "nan", "none", "null", "unknown", "nat"}

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
    """
    Detect communities using the Louvain algorithm.

    Returns a list of (community_id, node_set) tuples. Keeping the id
    attached to the node set from this point on is what fixes §4.3:
    every downstream function (naming, plotting) can look up the
    right name for the right community instead of relying on
    position-in-a-re-sorted-list, which silently drifts out of sync
    with the original Louvain id as soon as anything gets sorted by
    size.
    """
    print("[3/7] Detecting communities (Louvain)...")

    G_undirected = G.to_undirected()

    raw_communities = nx.community.louvain_communities(
        G_undirected,
        weight=None,
        resolution=resolution,
        seed=seed
    )

    communities = list(enumerate(raw_communities))  # [(community_id, node_set), ...]

    print(f"   -> Communities detected: {len(communities)}")

    sizes = sorted([len(c) for _, c in communities], reverse=True)
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
        sep="\t",        # fixed: file is tab-separated, not comma (§4.1, already fixed)
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

    # Build the mapping, filtering out missing/placeholder language
    # values at the source (§4.4) so "nan" never becomes a pseudo-language.
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

    sample = list(language_map.items())[:5]
    print(f"   -> Sample: {sample}")

    return language_map


# ============================================================
# 4b. LOAD CHANNEL TITLES (Source_Channel_Metadata.csv)
# ============================================================

def load_source_metadata_titles(path):
    """
    Extract a usable text label (title, falling back to username) for
    each channel from Source_Channel_Metadata.csv.

    Format: id, updated_utc, data
        "2044316859", 1720798494, '{"_": "Channel", ..., "title": "INSIDER | News | Politics | USA", "username": "INSIDERR_POLITIC", ...}'

    This file covers far more channels (~534k rows) than
    Channel_Language.csv (~71k), which is why it is used to close the
    coverage gap behind the 99.3% UNKNOWN communities (§4.2).
    """
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
# 4c. ENRICH LANGUAGE MAP FROM TITLES (langdetect)
# ============================================================

def enrich_language_map_from_titles(language_map, titles,
                                    min_confidence=0.70, min_letters=4):
    """
    Fill gaps in language_map using language detection on each
    channel's title/username (from Source_Channel_Metadata.csv).

    Channel_Language.csv stays authoritative: any channel already in
    language_map is left untouched here — only channels with NO known
    language get a detected one. Detection on short titles is noisy,
    so a candidate is only added when:
      - the cleaned title has at least `min_letters` alphabetic
        characters (very short titles like "USA" or emoji-only titles
        are skipped rather than guessed at), and
      - langdetect's top language has probability >= min_confidence.

    Returns (updated language_map, number of channels added).
    """
    try:
        from langdetect import detect_langs, DetectorFactory
        from langdetect.lang_detect_exception import LangDetectException
        DetectorFactory.seed = 42  # deterministic results across runs
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
    print(f"   -> Added {added:,} channels via title-based language detection "
          f"(min_confidence={min_confidence}, min_letters={min_letters})")
    print(f"   -> language_map now covers {len(language_map):,} channels total")
    return language_map, added


# ============================================================
# 5. NAME COMMUNITIES
# ============================================================

def name_communities(communities, language_map):
    """
    Assign a name to each community based on its dominant language.

    communities: list of (community_id, node_set).

    Only channels with a KNOWN language (present and valid in
    language_map) are used to compute the dominant language and its
    share (§4.4 — "Unknown" is never a candidate dominant language).

    If fewer than MIN_KNOWN_FOR_NAME channels in a community have a
    known language, the community is named "Unknown (low confidence)"
    instead of a language with a misleadingly precise-looking
    percentage computed from 1-2 data points (§4.6).

    Returns a dict: community_id -> community_name
    """
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
        # §4.5: languages present in the data but previously missing
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
        known_languages = [
            language_map[n] for n in nodes if n in language_map
        ]

        n_known = len(known_languages)
        n_total = len(nodes)

        if n_known == 0:
            name = "Unknown (0 known)"
        elif n_known < MIN_KNOWN_FOR_NAME:
            lang_counts = Counter(known_languages)
            dominant_lang, cnt = lang_counts.most_common(1)[0]
            readable = LANG_NAMES.get(dominant_lang, dominant_lang.upper())
            name = f"Unknown (low confidence: {readable}? n={n_known}/{n_total})"
        else:
            lang_counts = Counter(known_languages)
            dominant_lang, cnt = lang_counts.most_common(1)[0]
            share = cnt / n_known
            readable = LANG_NAMES.get(dominant_lang, dominant_lang.upper())
            name = f"{readable} ({share:.0%}, n={n_known}/{n_total})"

        community_names[comm_id] = name

    # Print top 10 by size, with correct ids (§4.3)
    top_by_size = sorted(communities, key=lambda cn: len(cn[1]), reverse=True)[:10]
    print("   -> Top 10 community names (by size):")
    for rank, (comm_id, nodes) in enumerate(top_by_size, start=1):
        print(f"      #{rank} (id={comm_id}, size={len(nodes):,}): {community_names[comm_id]}")

    return community_names


# ============================================================
# 6. EXPORT CSV RESULTS
# ============================================================

def export_communities(communities, output_path):
    """Export community assignments to CSV."""
    rows = []
    for comm_id, nodes in communities:
        for node in nodes:
            rows.append({"channel_id": node, "community_id": comm_id})

    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)
    print(f"   -> Communities exported: {output_path} ({len(df):,} rows)")
    return df


def export_community_sizes(communities, output_path):
    """Export community sizes to CSV."""
    rows = [
        {"community_id": comm_id, "size": len(nodes)}
        for comm_id, nodes in communities
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


def plot_top_communities(df_sizes, community_names, top_n, output_path):
    """
    Bar chart of the top N largest communities with names as labels.

    Fixed (§4.3): takes df_sizes (which carries the real community_id
    next to each size) instead of a bare sizes list, so the label for
    each bar is looked up by the community's actual id, not by its
    rank in the sorted list.
    """
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
                bar.get_height(),
                f"{val:,}", ha="center", va="bottom", fontsize=7)

    fig.savefig(output_path)
    plt.close(fig)
    print(f"   -> Saved: {output_path}")


def plot_degree_distribution(G, output_path):
    """
    CCDF (complementary cumulative distribution function) of the
    degree distribution, log-log scale.

    Replaces the previous raw scatter plot of degree vs. frequency,
    which is standard in network science but hard to read without
    practice (sparse, noisy cloud of points at high degree). The
    CCDF — P(degree >= k) for each k — is monotonic and far smoother:
    a straight line in log-log still indicates a power law, but the
    curve itself is easy to follow even without specialist training.
    """
    print("[7/7] Generating degree distribution (CCDF) chart...")

    degrees = np.array(sorted(d for _, d in G.degree() if d > 0))
    n = len(degrees)
    unique_degrees = np.unique(degrees)
    # number of nodes with degree >= k, for each unique k, via binary search
    idx = np.searchsorted(degrees, unique_degrees, side="left")
    ccdf = (n - idx) / n

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.loglog(unique_degrees, ccdf, "-", color=COLORS[2], linewidth=2)
    ax.set_xlabel("Degree k (log scale)")
    ax.set_ylabel("P(Degree ≥ k)  (log scale)")
    ax.set_title("Degree distribution — complementary CDF (log-log)")
    ax.grid(True, which="both", linestyle="--", alpha=0.4)
    fig.savefig(output_path)
    plt.close(fig)
    print(f"   -> Saved: {output_path}")


def plot_community_graph(G, communities, community_names,
                         top_n, output_path, min_inter_edges=1):
    """
    Community-level ("meta-graph") visualization: one node per
    community instead of a sampled cloud of individual channels.

    Replaces the previous node-link plot of thousands of sampled
    channels on a circular layout, which for dense communities tends
    to render as an unreadable tangle of crossing edges regardless of
    sample size. Here:
      - each node = one of the top_n largest communities, sized by
        its total number of channels (not just the sampled subset),
      - each edge = at least one real connection exists between those
        two communities in the full graph, with edge width
        proportional to how many such connections there are,
      - layout is force-directed (spring_layout) rather than
        circular, so strongly-linked communities are pulled together.

    This shows the actual structure (which communities talk to which,
    and how much) instead of a dense, uninterpretable sample of
    individual edges.
    """
    print(f"[7/7] Generating community-level graph (top {top_n} communities)...")

    sorted_comms = sorted(communities, key=lambda cn: len(cn[1]), reverse=True)[:top_n]
    comm_id_order = [cid for cid, _ in sorted_comms]
    sizes = {cid: len(nodes) for cid, nodes in sorted_comms}

    node_to_comm = {}
    for comm_id, nodes in sorted_comms:
        for n in nodes:
            node_to_comm[n] = comm_id

    # Count real connections between the selected communities across
    # the FULL graph (not a sample), so edge weights are exact.
    edge_weights = Counter()
    for u, v in G.edges():
        cu, cv = node_to_comm.get(u), node_to_comm.get(v)
        if cu is not None and cv is not None and cu != cv:
            key = tuple(sorted((cu, cv)))
            edge_weights[key] += 1

    meta = nx.Graph()
    for cid in comm_id_order:
        meta.add_node(cid)
    for (cu, cv), w in edge_weights.items():
        if w >= min_inter_edges:
            meta.add_edge(cu, cv, weight=w)

    pos = nx.spring_layout(meta, seed=42, weight="weight", k=1.2)

    max_size = max(sizes.values())
    node_sizes = [max(300, 4000 * sizes[cid] / max_size) for cid in meta.nodes()]

    color_for_id = {cid: COLORS[i % len(COLORS)] for i, cid in enumerate(comm_id_order)}
    node_colors = [color_for_id[cid] for cid in meta.nodes()]

    max_weight = max(edge_weights.values()) if edge_weights else 1
    edge_widths = [0.5 + 5 * meta[u][v]["weight"] / max_weight for u, v in meta.edges()]

    fig, ax = plt.subplots(figsize=(12, 10))
    nx.draw_networkx_edges(meta, pos, width=edge_widths, alpha=0.5,
                           edge_color="#999999", ax=ax)
    nx.draw_networkx_nodes(meta, pos, node_size=node_sizes,
                           node_color=node_colors, alpha=0.9, ax=ax)

    # Wrap each label onto two short lines ("Language (share%)" / "n=known/total")
    # instead of one long string, and disable clipping (clip_on=False) so a
    # label near the edge of the plot is never cut off by the axes boundary —
    # with savefig.bbox="tight" (set in rcParams) the saved figure expands to
    # include the full text instead of truncating it.
    def _wrap_label(name):
        if ", n=" in name:
            head, tail = name.split(", n=", 1)
            return f"{head}\nn={tail}"
        return name

    labels = {cid: _wrap_label(community_names.get(cid, f"Community_{cid}"))
              for cid in meta.nodes()}
    nx.draw_networkx_labels(meta, pos, labels=labels, font_size=7.5, ax=ax,
                            clip_on=False)

    # Generous margins so node circles AND their wrapped text labels have
    # room on every side, instead of sitting flush against the plot edge.
    ax.margins(0.25, 0.25)

    ax.set_title(f"Community-level graph (top {top_n}) — "
                 "node size = channels, edge width = inter-community links")
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
    LANGUAGE_FILE = BASE_DIR / "Channel_Language.csv"
    SOURCE_METADATA_FILE = BASE_DIR / "Source_Channel_Metadata.csv"

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
    communities = detect_communities(G, resolution=1.0, seed=42)  # list of (id, node_set)

    # --- Load language metadata ---
    language_map = load_language_metadata(LANGUAGE_FILE)
    coverage_before = sum(1 for n in G.nodes() if n in language_map)
    print(f"   -> Coverage before title enrichment: {coverage_before:,} / "
          f"{G.number_of_nodes():,} graph channels "
          f"({100*coverage_before/G.number_of_nodes():.1f}%)")

    # --- Enrich language metadata from Source_Channel_Metadata.csv ---
    titles = load_source_metadata_titles(SOURCE_METADATA_FILE)
    language_map, n_added = enrich_language_map_from_titles(language_map, titles)
    coverage_after = sum(1 for n in G.nodes() if n in language_map)
    print(f"   -> Coverage after title enrichment: {coverage_after:,} / "
          f"{G.number_of_nodes():,} graph channels "
          f"({100*coverage_after/G.number_of_nodes():.1f}%)")

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
        df_sizes, community_names, top_n=20,
        output_path=CHARTS_DIR / "top_20_communities.png"
    )
    plot_degree_distribution(
        G, CHARTS_DIR / "degree_distribution.png"
    )
    plot_community_graph(
        G, communities, community_names,
        top_n=5,
        output_path=CHARTS_DIR / "community_graph.png"
    )
    plot_resolution_curve(
        G, resolutions=[0.5, 0.8, 1.0, 1.2, 1.5, 2.0],
        output_path=CHARTS_DIR / "resolution_curve.png"
    )

    print("\n✅ Analysis completed.")
    print(f"   CSVs and charts saved in: {BASE_DIR}")