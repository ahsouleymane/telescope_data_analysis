"""
Builds the "map" of inter-community diffusion asked for by the
project's subject (modelisation et cartographie de la dynamique de la
diffusion ... entre les differentes communautes cibles):
  - ONE global map: the community-level diffusion network aggregated
    over the whole period (2015-2024), for the overall picture.
  - ONE map PER YEAR (2015-2024): the same network restricted to that
    year's cascades, as its own full-size figure, so each year's
    internal structure (who was central, who linked to whom that
    year) can be read on its own.

Input (all under BASE_DIR, produced by the earlier stages):
  - cascade_community_timeline/cascade_community_timeline.csv
    (built by cascading_community_timelines.py) — one row per cascade,
    with columns connected_component_id, date, n_channels,
    n_communities, communities (';'-joined community ids), views,
    forwards.
  - community_sizes/community_sizes.csv  (from community_detection.py)
  - community_names/community_names.csv  (from community_detection.py)

For each of the TOP_N largest communities (by total channel count,
from community_sizes.csv):
  - node size = number of dated cascades touching that community in
    the period the map covers (diffusion activity), not its static
    total channel count — this is what makes the map "dynamic" rather
    than a repeat of the earlier community_graph.png.
  - edge width = number of dated cascades touching BOTH communities in
    that same period (cross-community co-propagation).

Node positions are computed ONCE from the all-years-combined edge
weights (spring_layout) and reused identically on the global map and
on every yearly map, so all of them are visually comparable — only
sizes/edges change, never the layout itself.

Each community is also given a short rank (#1 = largest by total
channel count, from community_sizes.csv) shown before its name in the
legend, since most of the top communities share the same dominant
language ("Russian") and would otherwise be hard to tell apart.

Sizing: the global overview grid is sized against each year's own
maximum (not a shared/global scale), so a year with few cascades
(e.g. 2015) still shows clear internal structure instead of a cluster
of nearly-invisible dots — the trade-off is that node/edge sizes are
NOT comparable in absolute terms from one yearly map to another; the
total cascade count in each map's title is what carries that
comparison instead.

Output layout (same convention as community_detection.py):
  - CSVs go into their own folder (named after the CSV file, without
    extension) together with a README.md describing their content:
      community_activity_by_year/community_activity_by_year.csv + README.md
      cross_community_edges_by_year/cross_community_edges_by_year.csv + README.md
  - All PNG maps of this program go into charts/<PROGRAM_NAME>/:
      charts/community_diffusion_maps/fig_community_map_global.png
      charts/community_diffusion_maps/fig_community_map_2015.png ... 2024.png

Coverage caveat to keep in mind for the report: only ~68% of cascades
have a known date (see cascading_community_timelines.py docstring),
and 2015/2024 are partial years in the source data (first date
2015-09-29, last date 2024-09-28) — both are noted again on every map.
"""

from collections import Counter
from itertools import combinations
from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd

from config import BASE_DIR  # see code/config.py (env var TELESCOPE_DIR)

# --- Inputs (each produced by an earlier stage, in its own folder) ---
TIMELINE_FILE = (BASE_DIR / "cascade_community_timeline"
                 / "cascade_community_timeline.csv")
SIZES_FILE = BASE_DIR / "community_sizes" / "community_sizes.csv"
NAMES_FILE = BASE_DIR / "community_names" / "community_names.csv"

# --- Outputs ---
PROGRAM_NAME = "community_diffusion_maps"

# CSVs go into their own folders (via export_csv_with_readme), charts
# go into charts/<PROGRAM_NAME>/ (isolated from other programs).
OUT_ACTIVITY = BASE_DIR / "community_activity_by_year.csv"
OUT_EDGES = BASE_DIR / "cross_community_edges_by_year.csv"

CHARTS_DIR = BASE_DIR / "charts" / PROGRAM_NAME

TOP_N = 12
YEARS = list(range(2015, 2025))  # 2015-2024 inclusive

COLORS = ["#2E5395", "#5B8DD9", "#85B09A", "#E8A33D", "#C0392B",
          "#8E44AD", "#16A085", "#D35400", "#2C3E50", "#7F8C8D",
          "#1F618D", "#A93226"]

COVERAGE_NOTE = ("2015 and 2024 are partial years in the data (2015-09-29 to 2024-09-28); "
                 "only ~68% of cascades have a known date.")

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 10,
    "figure.dpi": 150,
    "savefig.dpi": 150,
    "savefig.bbox": "tight",
})


# ============================================================
# EXPORT CSV WITH README (same convention as community_detection.py)
# ============================================================

def export_csv_with_readme(df, output_path, title, description_lines):
    """
    Export a DataFrame to CSV inside a dedicated folder named after the
    CSV file (without extension), and write a README.md describing the
    CSV's content next to it.

    Example:
        output_path = BASE_DIR / "community_activity_by_year.csv"
        -> BASE_DIR / "community_activity_by_year" /
                       "community_activity_by_year.csv" + README.md
    """
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
        f"- `{output_path.name}` — {len(df):,} rows, "
        f"{len(df.columns)} columns.",
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


# ============================================================
# LOAD INPUTS
# ============================================================

def load_top_communities(sizes_path, names_path, top_n):
    sizes = pd.read_csv(sizes_path, dtype={"community_id": str})
    top_ids_ordered = (
        sizes.sort_values("size", ascending=False)
        .head(top_n)["community_id"].tolist()
    )

    names_df = pd.read_csv(names_path, dtype={"community_id": str})
    names = dict(zip(names_df["community_id"], names_df["community_name"]))

    # #1 = largest community by total channel count, in that order —
    # used as a short, unambiguous prefix in the legend, since most of
    # the top communities share the same dominant-language name.
    ranks = {cid: i + 1 for i, cid in enumerate(top_ids_ordered)}

    return set(top_ids_ordered), names, ranks


# ============================================================
# ACCUMULATE ACTIVITY AND EDGES (chunked)
# ============================================================

def accumulate_activity_and_edges(timeline_path, top_ids):
    """
    Streams cascade_community_timeline.csv in chunks and accumulates,
    per year:
      - activity[(year, community_id)] = number of dated cascades
        touching that community (restricted to top_ids)
      - edges[(year, frozenset({a, b}))] = number of dated cascades
        touching both a and b (restricted to top_ids)
    """
    print("[1/3] Accumulating yearly activity and cross-community edges "
          "(chunked, this takes a while over ~20M rows)...")

    activity = Counter()
    edges = Counter()
    total = 0
    dated = 0

    for chunk in pd.read_csv(timeline_path, dtype=str, chunksize=500_000):
        total += len(chunk)
        for date, communities_str in zip(chunk["date"], chunk["communities"]):
            if not isinstance(date, str) or len(date) < 4:
                continue
            year = int(date[:4])
            if year not in YEARS:
                continue
            dated += 1

            comms = (
                [c for c in communities_str.split(";") if c in top_ids]
                if isinstance(communities_str, str) else []
            )
            if not comms:
                continue

            for c in set(comms):
                activity[(year, c)] += 1

            if len(comms) >= 2:
                for a, b in combinations(sorted(set(comms)), 2):
                    edges[(year, frozenset((a, b)))] += 1

        print(f"   -> Processed: {total:,} rows (dated & relevant: {dated:,})...",
              end="\r")

    print()
    print(f"   -> Done. {len(activity):,} (year, community) activity entries, "
          f"{len(edges):,} (year, pair) edge entries")
    return activity, edges


# ============================================================
# SAVE TABLES (each in its own folder + README)
# ============================================================

def save_tables(activity, edges, out_activity_path, out_edges_path):
    df_activity = pd.DataFrame(
        [{"year": y, "community_id": c, "n_cascades": n}
         for (y, c), n in activity.items()]
    ).sort_values(["year", "n_cascades"], ascending=[True, False])

    export_csv_with_readme(
        df_activity, out_activity_path,
        title="Community activity by year (dated cascades)",
        description_lines=[
            "One row per (year, community) pair, giving the number of",
            "dated cascades that touch that community during that year.",
            "",
            "Only the TOP_N largest communities (by total channel count,",
            "from `community_sizes.csv`) are included — the map figures",
            "track exactly these communities.",
            "",
            "- `year` — calendar year (2015-2024). 2015 and 2024 are",
            "  partial years in the source data.",
            "- `community_id` — Leiden community ID.",
            "- `n_cascades` — number of dated cascades (from",
            "  `cascade_community_timeline.csv`) touching this community",
            "  during that year.",
            "",
            "Note: ~68% of cascades have a known date; counts here are",
            "over the dated subset only.",
        ],
    )

    df_edges = pd.DataFrame(
        [{"year": y,
          "community_a": sorted(pair)[0],
          "community_b": sorted(pair)[1],
          "n_cascades": n}
         for (y, pair), n in edges.items()]
    ).sort_values(["year", "n_cascades"], ascending=[True, False])

    export_csv_with_readme(
        df_edges, out_edges_path,
        title="Cross-community edges by year (dated cascades)",
        description_lines=[
            "One row per (year, unordered community pair) with at least",
            "one dated cascade touching BOTH communities during that",
            "year — this is the edge list of the yearly diffusion maps.",
            "",
            "Only pairs whose two communities are both in the TOP_N",
            "largest communities (by total channel count) are included.",
            "",
            "- `year` — calendar year (2015-2024).",
            "- `community_a`, `community_b` — the two community IDs,",
            "  always ordered so that `community_a < community_b`",
            "  (each unordered pair appears once per year).",
            "- `n_cascades` — number of dated cascades touching both",
            "  communities during that year.",
            "",
            "Note: ~68% of cascades have a known date; counts here are",
            "over the dated subset only.",
        ],
    )

    print(f"   -> Saved: {out_activity_path}")
    print(f"   -> Saved: {out_edges_path}")


# ============================================================
# LAYOUT AND DRAWING
# ============================================================

def aggregate_all_years(activity, edges):
    """Collapses the per-year counters into all-years totals, used
    both for the global map and to compute the one shared layout."""
    combined_activity = Counter()
    for (_, cid), n in activity.items():
        combined_activity[cid] += n

    combined_edges = Counter()
    for (_, pair), n in edges.items():
        combined_edges[pair] += n

    return combined_activity, combined_edges


def compute_stable_layout(top_ids, combined_edges):
    """
    One layout from the ALL-YEARS-COMBINED edge weights, reused
    identically on the global map and every yearly map, so every map
    places each community at the same spot — only size/edges change.
    """
    g_all = nx.Graph()
    g_all.add_nodes_from(top_ids)
    for pair, n in combined_edges.items():
        a, b = tuple(pair)
        g_all.add_edge(a, b, weight=n)
    return nx.spring_layout(g_all, seed=42, weight="weight", k=1.3)


def _legend_handles(top_ids, names, ranks, color_for_id):
    return [
        plt.Line2D([0], [0], marker="o", linestyle="",
                   color=color_for_id[cid], markersize=9,
                   label=f"#{ranks[cid]} {names.get(cid, f'Community_{cid}')}")
        for cid in sorted(top_ids, key=lambda c: ranks[c])
    ]


def _draw_map(ax, top_ids, pos, color_for_id, node_activity,
              edge_weights, max_activity, max_edge):
    g = nx.Graph()
    g.add_nodes_from(top_ids)
    for a, b in edge_weights:
        g.add_edge(a, b, weight=edge_weights[(a, b)])

    node_sizes = [
        80 + 1400 * (node_activity.get(cid, 0) / max_activity)
        for cid in g.nodes()
    ]
    node_colors = [color_for_id[cid] for cid in g.nodes()]
    edge_widths = [
        0.3 + 5 * (g[u][v]["weight"] / max_edge) for u, v in g.edges()
    ]

    nx.draw_networkx_edges(g, pos, width=edge_widths, alpha=0.5,
                           edge_color="#999999", ax=ax)
    nodes = nx.draw_networkx_nodes(g, pos, node_size=node_sizes,
                                   node_color=node_colors, alpha=0.9, ax=ax)
    # Without this, a node sitting near the plot's edge (e.g. the
    # isolated Persian community) gets visually sliced in half by the
    # axes boundary, especially in the small grid panels — margins
    # give every node room, clip_on=False stops it being cut off
    # outright even if a margin still isn't quite enough.
    nodes.set_clip_on(False)
    ax.margins(0.15, 0.15)
    ax.axis("off")


# ============================================================
# PLOT: GLOBAL OVERVIEW GRID (one panel per year)
# ============================================================

def plot_global_map(top_ids, names, ranks, activity, edges, pos, out_path):
    """
    The "global" map is a single overview image: a 2x5 grid with one
    small panel per year (2015-2024), all sharing the same fixed
    layout — so the whole evolution can be scanned at a glance, with
    each year's own full-size version available separately (see
    plot_year_maps). Each panel is normalized to THAT year's own
    maximum (not a shared/global scale), exactly like the standalone
    per-year maps, so early years still show internal structure
    instead of being flattened by later years' much larger volumes.
    """
    print("[2/3] Rendering global overview grid (one panel per year)...")

    color_for_id = {
        cid: COLORS[i % len(COLORS)]
        for i, cid in enumerate(sorted(top_ids))
    }

    fig, axes = plt.subplots(2, 5, figsize=(22, 10))

    for year, ax in zip(YEARS, axes.flat):
        year_activity = {cid: activity.get((year, cid), 0) for cid in top_ids}
        year_edges = {tuple(pair): n for (y, pair), n in edges.items() if y == year}

        max_activity = max(year_activity.values(), default=0) or 1
        max_edge = max(year_edges.values(), default=0) or 1

        _draw_map(ax, top_ids, pos, color_for_id, year_activity,
                  year_edges, max_activity, max_edge)
        total_cascades = sum(year_activity.values())
        ax.set_title(f"{year} (n={total_cascades:,} cascades)", fontsize=11)

    fig.suptitle(
        f"Yearly evolution of the diffusion network between the {TOP_N} largest "
        f"communities — node size = that year's activity, edge width = that year's "
        f"cross-community cascades",
        fontsize=14, y=1.02,
    )

    fig.legend(handles=_legend_handles(top_ids, names, ranks, color_for_id),
               loc="lower center", ncol=4, fontsize=8,
               bbox_to_anchor=(0.5, -0.08))
    fig.text(0.5, -0.13, COVERAGE_NOTE, ha="center",
             fontsize=8, style="italic", color="#595959")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    print(f"   -> Saved: {out_path}")


# ============================================================
# PLOT: ONE FULL-SIZE MAP PER YEAR
# ============================================================

def plot_year_maps(top_ids, names, ranks, activity, edges, pos, out_dir):
    print("[3/3] Rendering one map per year...")

    color_for_id = {
        cid: COLORS[i % len(COLORS)]
        for i, cid in enumerate(sorted(top_ids))
    }

    for year in YEARS:
        year_activity = {cid: activity.get((year, cid), 0) for cid in top_ids}
        year_edges = {tuple(pair): n for (y, pair), n in edges.items() if y == year}

        max_activity = max(year_activity.values(), default=0) or 1
        max_edge = max(year_edges.values(), default=0) or 1

        fig, ax = plt.subplots(figsize=(10, 9))
        _draw_map(ax, top_ids, pos, color_for_id, year_activity,
                  year_edges, max_activity, max_edge)

        total_cascades = sum(year_activity.values())
        ax.set_title(
            f"Diffusion network between the {TOP_N} largest communities — "
            f"{year} (n={total_cascades:,} cascades)",
            fontsize=13,
        )

        fig.legend(handles=_legend_handles(top_ids, names, ranks, color_for_id),
                   loc="lower center", ncol=4, fontsize=8,
                   bbox_to_anchor=(0.5, -0.05))
        fig.text(0.5, -0.1,
                 COVERAGE_NOTE + " Sizes/widths here are scaled to THIS year's own "
                 "maximum, not comparable in absolute terms to other years.",
                 ha="center", fontsize=8, style="italic", color="#595959")

        out_path = out_dir / f"fig_community_map_{year}.png"
        out_dir.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_path, bbox_inches="tight")
        plt.close(fig)
        print(f"   -> Saved: {out_path}")


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    # Make sure the chart folder exists, and document what it holds.
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    (CHARTS_DIR / "README.md").write_text(
        "# Charts — Community diffusion maps\n\n"
        "All PNG maps produced by `community_diffusion_maps.py`.\n\n"
        "- `fig_community_map_global.png` — 2x5 grid, one panel per year "
        "(2015-2024), all on the same fixed layout.\n"
        "- `fig_community_map_2015.png` … `fig_community_map_2024.png` — "
        "one full-size map per year, same fixed layout as the grid.\n\n"
        "Legend: `#rank Language (share%, n=known/total)` "
        "(rank = position in `community_sizes.csv`, #1 = largest).\n"
        "Node size = that period's diffusion activity; edge width = that "
        "period's cross-community cascades. Each panel is normalized to "
        "its own period's maximum (sizes are NOT comparable across years).\n\n"
        f"Coverage note: {COVERAGE_NOTE}\n",
        encoding="utf-8",
    )

    print("[0/3] Loading top communities...")
    top_ids, names, ranks = load_top_communities(SIZES_FILE, NAMES_FILE, TOP_N)
    print(f"   -> Tracking {len(top_ids)} communities: "
          f"{[f'#{ranks[c]} {names.get(c, c)}' for c in sorted(top_ids, key=lambda c: ranks[c])]}")

    activity, edges = accumulate_activity_and_edges(TIMELINE_FILE, top_ids)
    save_tables(activity, edges, OUT_ACTIVITY, OUT_EDGES)

    combined_activity, combined_edges = aggregate_all_years(activity, edges)
    pos = compute_stable_layout(top_ids, combined_edges)

    plot_global_map(top_ids, names, ranks, activity, edges, pos,
                    CHARTS_DIR / "fig_community_map_global.png")
    plot_year_maps(top_ids, names, ranks, activity, edges, pos, CHARTS_DIR)

    print("\n✅ Global map + one map per year done.")