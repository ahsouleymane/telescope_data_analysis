"""
Builds the base dataset for the propagation-dynamics stage of the
project (after community detection + naming, see
community_detection_fixed.py).

Joins three files:
  - Message_Forwarding_Flows.csv (20,538,309 rows): each row is one
    connected component ("cascade") of the message-forwarding graph —
    a set of (channel_id, message_id) pairs that are all instances of
    the same propagated content across channels.
  - Aggregated_User_Interactions.csv (13,972,042 rows): indexed by the
    same connected_component_id, holds a JSON-ish blob with the
    cascade's date and engagement (views, forwards, reactions). This
    is the ONLY source of real calendar timestamps found in the
    dataset — channel_to_channel_graph.csv, Channel_Language.csv,
    Source_Channel_Metadata.csv and Temporal_Channel_Metadata.csv all
    lack one (see progress report §Methodology / next steps).
  - communities.csv (261,172 rows, produced by
    community_detection_fixed.py): channel_id -> community_id.

Output: cascade_community_timeline.csv, one row per cascade, with:
  connected_component_id, date, n_channels, n_communities,
  communities (';'-joined community ids), views, forwards

Coverage note: only ~68% of cascades (13,972,042 / 20,538,309) have a
known date, since Aggregated_User_Interactions.csv is a strict subset
of Message_Forwarding_Flows.csv (verified: every component_id in the
former also appears in the latter, and connected_component_id is
unique in both files). Cascades with n_communities >= 2 are the ones
of interest for cross-community propagation analysis.

Expect this to take a while given the scale (20M+ rows) — let it run
to completion rather than interrupting it; it writes the output file
incrementally (chunk by chunk), so a partial run still leaves usable
partial output.
"""

import ast
import re
from pathlib import Path

import pandas as pd

BASE_DIR = Path.home() / "Documents" / "telescope_data_analysis" / "telescope_files"
FLOWS_FILE = BASE_DIR / "Message_Forwarding_Flows.csv"
INTERACTIONS_FILE = BASE_DIR / "Aggregated_User_Interactions.csv"
COMMUNITIES_FILE = BASE_DIR / "communities.csv"
OUTPUT_FILE = BASE_DIR / "cascade_community_timeline.csv"

# Extracts just the channel_id from each ('channel_id', 'message_id') pair
# in connected_component_nodes, e.g. "[('1145313737', '38274'), ...]".
# Using a regex instead of ast.literal_eval (which would build the full
# list of tuples) is much faster at 20M+ rows, since we only need the
# channel ids here, not the message ids.
NODE_CHANNEL_RE = re.compile(r"\('(\d+)',")


def _safe_literal_eval(s):
    try:
        return ast.literal_eval(s)
    except (ValueError, SyntaxError):
        return None


def load_channel_to_community(path):
    print("[1/3] Loading channel -> community mapping (communities.csv)...")
    df = pd.read_csv(path, dtype=str)
    mapping = dict(zip(df["channel_id"], df["community_id"]))
    print(f"   -> {len(mapping):,} channels mapped to communities")
    return mapping


def load_interactions(path):
    """
    Returns a DataFrame indexed by connected_component_id with columns
    date (datetime, UTC), views, forwards — one row per cascade that
    has a known date.
    """
    print("[2/3] Loading cascade dates/engagement (Aggregated_User_Interactions.csv)...")
    frames = []
    total = 0

    for chunk in pd.read_csv(path, dtype=str, chunksize=500_000):
        total += len(chunk)
        parsed = chunk["filtered_message_info"].map(_safe_literal_eval)
        dates = parsed.map(lambda d: d.get("date") if isinstance(d, dict) else None)
        views = parsed.map(lambda d: d.get("views", 0) if isinstance(d, dict) else 0)
        forwards = parsed.map(lambda d: d.get("forwards", 0) if isinstance(d, dict) else 0)
        frames.append(pd.DataFrame({
            "connected_component_id": chunk["connected_component_id"],
            "date": dates,
            "views": views,
            "forwards": forwards,
        }))
        print(f"   -> Processed: {total:,} rows...", end="\r")

    print()
    df = pd.concat(frames, ignore_index=True)
    df["date"] = pd.to_datetime(df["date"], errors="coerce", utc=True)
    df = df.dropna(subset=["date"]).drop_duplicates(subset=["connected_component_id"])
    df = df.set_index("connected_component_id")
    print(f"   -> {len(df):,} cascades with a usable date")
    return df


def extract_channel_ids(nodes_str):
    return NODE_CHANNEL_RE.findall(nodes_str)


def build_cascade_timeline(flows_path, interactions_df, channel_to_community, output_path):
    """
    Streams Message_Forwarding_Flows.csv in chunks, resolves each
    cascade's channels to communities, attaches date/engagement where
    known, and writes the result incrementally to output_path (so
    memory stays bounded regardless of the 20M+ row count, and a
    partial run still leaves usable output).
    """
    print("[3/3] Building cascade -> communities timeline (chunked, this takes a while)...")

    total = 0
    dated = 0
    cross_community = 0
    first_chunk = True

    for chunk in pd.read_csv(flows_path, dtype=str, chunksize=200_000):
        total += len(chunk)

        channel_lists = chunk["connected_component_nodes"].map(extract_channel_ids)
        community_sets = channel_lists.map(
            lambda chans: {channel_to_community[c] for c in chans if c in channel_to_community}
        )

        chunk_out = pd.DataFrame({
            "connected_component_id": chunk["connected_component_id"],
            "n_channels": channel_lists.map(len),
            "n_communities": community_sets.map(len),
            "communities": community_sets.map(lambda s: ";".join(sorted(s))),
        })

        chunk_out = chunk_out.set_index("connected_component_id").join(
            interactions_df[["date", "views", "forwards"]], how="left"
        ).reset_index()

        dated += chunk_out["date"].notna().sum()
        cross_community += (chunk_out["n_communities"] >= 2).sum()

        chunk_out.to_csv(output_path, mode="w" if first_chunk else "a",
                         header=first_chunk, index=False)
        first_chunk = False

        print(f"   -> Processed: {total:,} cascades "
              f"(dated: {dated:,}, cross-community: {cross_community:,})...", end="\r")

    print()
    print(f"   -> Saved: {output_path}")
    print(f"   -> Total cascades: {total:,}")
    print(f"   -> Cascades with a known date: {dated:,} ({100*dated/total:.1f}%)")
    print(f"   -> Cross-community cascades (>=2 communities): {cross_community:,} "
          f"({100*cross_community/total:.1f}%)")


if __name__ == "__main__":
    channel_to_community = load_channel_to_community(COMMUNITIES_FILE)
    interactions_df = load_interactions(INTERACTIONS_FILE)
    build_cascade_timeline(FLOWS_FILE, interactions_df, channel_to_community, OUTPUT_FILE)