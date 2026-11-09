#!/usr/bin/env python3
"""
TeleScope v2 - COMMUNITY DETECTION on the weighted, monthly forwarding graph.

Input : <gold>/edges_monthly   (Parquet, written by job3_edges.py)
        or <gold>/edges_monthly_csv/part-*.csv   (job3 --csv)
        columns: origin_channel, dest_channel, month (yyyy-MM), n_forwards
        An edge A -> B means "B forwarded messages written by A"; weight = n_forwards.

What it does
  1. Static graph (all months summed): Leiden (modularity, undirected weights, A<->B summed)
     and Infomap (directed, flow-based), the two being independent views of the same graph.
  2. Quality: modularity, share of forwards that stay inside a community, size distribution.
  3. Diffusion between communities: who forwards whom, as a community x community table.
  4. Time: one Leiden per year, stability of the partitions between consecutive years (NMI, ARI).
  5. Optional: Leiden vs Infomap agreement, noise floor (--seed-baseline), number of communities vs
     resolution (--resolution-curve), communities named by dominant language (--languages).

Every table is written as its own folder  <out>/<name>/<name>.csv + README.md
(how it was generated, what the columns mean), the convention of the project.
Charts (English, same types and look as the v1 charts) go to --figdir (images only).

Usage
  python3 community_detection_v2.py --selftest
  python3 community_detection_v2.py --gold telescope_pipeline_files/gold --out communities_v2 --figdir figures/community_detection \
         --languages telescope_files/Channel_Language.csv
  add --skip-infomap to go faster, --resolution 0.5 for fewer/larger communities
"""
import argparse
import json
import random
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------- data

@dataclass
class Net:
    """Directed weighted graph on integer codes 0..n-1; nodes[code] = channel id."""
    nodes: np.ndarray
    src: np.ndarray
    dst: np.ndarray
    w: np.ndarray


def load_edges(gold):
    gold = Path(gold)
    pq, csvdir = gold / "edges_monthly", gold / "edges_monthly_csv"
    df = None
    if pq.exists():
        try:
            df = pd.read_parquet(pq)
        except ImportError:
            df = None
    if df is None:
        parts = sorted(csvdir.glob("*.csv")) if csvdir.exists() else []
        if not parts:
            raise SystemExit(f"No edges found: expected {pq} (Parquet, needs pyarrow) or {csvdir}/*.csv")
        df = pd.concat((pd.read_csv(p) for p in parts), ignore_index=True)
    df = df[["origin_channel", "dest_channel", "month", "n_forwards"]].copy()
    df["origin_channel"] = df["origin_channel"].astype("int64")
    df["dest_channel"] = df["dest_channel"].astype("int64")
    df["n_forwards"] = df["n_forwards"].astype("int64")
    df["year"] = df["month"].astype(str).str[:4].astype(int)
    return df


def build_net(df, min_weight=1):
    """Sum the weights of each (origin, destination) pair, drop self-loops and light edges."""
    d = df.groupby(["origin_channel", "dest_channel"], as_index=False)["n_forwards"].sum()
    d = d[(d.origin_channel != d.dest_channel) & (d.n_forwards >= min_weight)]
    codes, uniq = pd.factorize(pd.concat([d.origin_channel, d.dest_channel], ignore_index=True))
    n = len(d)
    return Net(nodes=np.asarray(uniq), src=codes[:n].astype(np.int64),
               dst=codes[n:].astype(np.int64), w=d.n_forwards.to_numpy(float))


def undirected(net):
    """A<->B summed: returns (a, b, w) with a < b."""
    u = (pd.DataFrame({"a": np.minimum(net.src, net.dst), "b": np.maximum(net.src, net.dst), "w": net.w})
         .groupby(["a", "b"], as_index=False)["w"].sum())
    return u["a"].to_numpy(), u["b"].to_numpy(), u["w"].to_numpy()


# ---------------------------------------------------------------- algorithms (igraph)

def run_leiden(net, resolution=1.0, seed=42):
    import igraph as ig
    a, b, w = undirected(net)
    g = ig.Graph(n=len(net.nodes), edges=list(zip(a.tolist(), b.tolist())), directed=False)
    g.es["weight"] = w.tolist()
    random.seed(seed)
    ig.set_random_number_generator(random)
    cl = g.community_leiden(objective_function="modularity", weights="weight",
                            resolution=resolution, n_iterations=-1)
    return np.asarray(cl.membership, dtype=np.int64)


def run_infomap(net, trials=1):
    import igraph as ig
    g = ig.Graph(n=len(net.nodes), edges=list(zip(net.src.tolist(), net.dst.tolist())), directed=True)
    g.es["weight"] = net.w.tolist()
    cl = g.community_infomap(edge_weights="weight", trials=trials)
    return np.asarray(cl.membership, dtype=np.int64), float(cl.codelength)


# ---------------------------------------------------------------- metrics (numpy only)

def relabel_by_size(mem):
    """Community 0 = the largest one."""
    sizes = pd.Series(mem).value_counts()
    mapping = {c: i for i, c in enumerate(sizes.index)}
    return np.array([mapping[c] for c in mem], dtype=np.int64)


def modularity_undirected(net, mem):
    a, b, w = undirected(net)
    m = w.sum()
    n = len(net.nodes)
    strength = np.bincount(a, w, n) + np.bincount(b, w, n)
    k = mem.max() + 1
    intra = np.bincount(mem[a][mem[a] == mem[b]], w[mem[a] == mem[b]], k).sum()
    comm_strength = np.bincount(mem, strength, k)
    return float(intra / m - ((comm_strength / (2 * m)) ** 2).sum())


def partition_stats(net, mem):
    sizes = np.bincount(mem)
    order = np.sort(sizes)[::-1]
    intra = net.w[mem[net.src] == mem[net.dst]].sum()
    return {
        "n_nodes": int(len(net.nodes)), "n_edges_directed": int(len(net.src)),
        "total_forwards": int(net.w.sum()), "n_communities": int(len(sizes)),
        "modularity": round(modularity_undirected(net, mem), 4),
        "intra_share": round(float(intra / net.w.sum()), 4),
        "largest_community": int(order[0]),
        "largest_share": round(float(order[0] / len(mem)), 4),
        "top10_share": round(float(order[:10].sum() / len(mem)), 4),
        "singletons": int((sizes == 1).sum()),
    }


def compare(nodes_a, mem_a, nodes_b, mem_b):
    """NMI, ARI, homogeneity, completeness on the channels present in both partitions."""
    from sklearn.metrics import (adjusted_rand_score, completeness_score, homogeneity_score,
                                 normalized_mutual_info_score)
    a = pd.Series(mem_a, index=nodes_a)
    b = pd.Series(mem_b, index=nodes_b)
    a = a[~a.index.duplicated()]
    b = b[~b.index.duplicated()]
    common = a.index.intersection(b.index)
    if len(common) < 2:
        return {"n_common": int(len(common)), "nmi": np.nan, "ari": np.nan,
                "homogeneity": np.nan, "completeness": np.nan}
    x, y = a.loc[common].to_numpy(), b.loc[common].to_numpy()
    return {"n_common": int(len(common)),
            "nmi": round(float(normalized_mutual_info_score(x, y)), 4),
            "ari": round(float(adjusted_rand_score(x, y)), 4),
            "homogeneity": round(float(homogeneity_score(x, y)), 4),
            "completeness": round(float(completeness_score(x, y)), 4)}


def flows_table(net, mem, top=15):
    """Community x community forwards (top communities by size, the rest = 'other')."""
    k = mem.max() + 1
    big = min(top, k)
    cmap = np.where(np.arange(k) < big, np.arange(k), big)         # big -> itself, rest -> 'other'
    co, cd = cmap[mem[net.src]], cmap[mem[net.dst]]
    f = pd.DataFrame({"o": co, "d": cd, "w": net.w}).groupby(["o", "d"], as_index=False)["w"].sum()
    out_tot = f.groupby("o")["w"].transform("sum")
    f["share_of_origin_out"] = (f["w"] / out_tot).round(4)
    lab = lambda c: "other" if c == big and k > big else str(c)
    f["origin_community"] = f["o"].map(lab)
    f["dest_community"] = f["d"].map(lab)
    f = f.rename(columns={"w": "forwards"})
    return f[["origin_community", "dest_community", "forwards", "share_of_origin_out"]], big, k > big


def profiles_table(net, mem):
    k = mem.max() + 1
    n = len(net.nodes)
    strength = np.bincount(net.src, net.w, n) + np.bincount(net.dst, net.w, n)
    same = mem[net.src] == mem[net.dst]
    out_f = np.bincount(mem[net.src], net.w, k)
    in_f = np.bincount(mem[net.dst], net.w, k)
    intra = np.bincount(mem[net.src][same], net.w[same], k)
    rows = []
    for c in range(k):
        idx = np.where(mem == c)[0]
        top = idx[np.argsort(-strength[idx])[:5]]
        rows.append({"community": c, "size": len(idx), "forwards_out": int(out_f[c]),
                     "forwards_in": int(in_f[c]), "forwards_inside": int(intra[c]),
                     "inside_share_of_out": round(float(intra[c] / out_f[c]), 4) if out_f[c] else np.nan,
                     "top_channels": ";".join(str(net.nodes[i]) for i in top)})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- output (folder per CSV + README)

class Writer:
    def __init__(self, out, context):
        self.out, self.context = Path(out), context
        self.tables = []

    def table(self, name, df, what, columns):
        d = self.out / name
        d.mkdir(parents=True, exist_ok=True)
        df.to_csv(d / f"{name}.csv", index=False)
        cols = "\n".join(f"| `{c}` | {t} |" for c, t in columns.items())
        (d / "README.md").write_text(
            f"# {name}\n\n{what}\n\n## How it was generated\n\n"
            f"`community_detection_v2.py`, run on {date.today().isoformat()}.\n\n{self.context}\n\n"
            f"## Content ({len(df):,} rows)\n\n| Column | Meaning |\n|---|---|\n{cols}\n", encoding="utf-8")
        self.tables.append(name)
        print(f"  wrote {name}/ ({len(df):,} rows)")


# ---------------------------------------------------------------- charts

INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e5e4e0"
BLUE, ORANGE = "#2a78d6", "#eb6834"


def _style(ax):
    """Same look as the v1 charts: serif font, boxed axes, dashed light grid."""
    ax.grid(True, which="major", linestyle="--", linewidth=0.8, color="#d9d9d9")
    ax.set_axisbelow(True)
    ax.tick_params(colors="#222222", labelsize=9)


def _rc(plt):
    plt.rcParams.update({"font.family": "serif", "font.size": 10, "axes.titlesize": 11,
                         "axes.titleweight": "normal", "axes.titlecolor": "black",
                         "axes.labelcolor": "black", "figure.dpi": 100})


def make_charts(figdir, results, yearly, flows_info):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap
    figdir = Path(figdir)
    figdir.mkdir(parents=True, exist_ok=True)
    seq = LinearSegmentedColormap.from_list("blue_seq", ["#eef4fc", "#b5d0f2", "#2a78d6", "#0d3b78"])
    _rc(plt)

    # 1. community size distribution
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    for (name, mem), col in zip(results.items(), (BLUE, ORANGE)):
        s = np.sort(np.bincount(mem))[::-1]
        ax.plot(np.arange(1, len(s) + 1), s, color=col, linewidth=2, label=f"{name} ({len(s):,} communities)")
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("Community rank (1 = largest)"); ax.set_ylabel("Channels in the community")
    ax.set_title("Community size distribution"); _style(ax)
    ax.legend(frameon=False, fontsize=9, labelcolor=INK)
    fig.tight_layout(); fig.savefig(figdir / "community_size_rank.png", dpi=200); plt.close(fig)

    # 2. yearly structure (three panels, one measure each)
    if yearly is not None and len(yearly) >= 2:
        fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.6), sharex=True)
        for ax, col, title in zip(axes, ("n_channels", "n_communities", "modularity"),
                                  ("Active channels", "Communities (Leiden)", "Modularity (Leiden)")):
            ax.plot(yearly["year"], yearly[col], color=BLUE, linewidth=2, marker="o", markersize=5,
                    markeredgecolor="white", markeredgewidth=1)
            ax.set_title(title); _style(ax)
            ax.set_xticks(yearly["year"]); ax.tick_params(axis="x", rotation=60)
        fig.tight_layout(); fig.savefig(figdir / "yearly_structure.png", dpi=200); plt.close(fig)

        y2 = yearly.dropna(subset=["nmi_prev"])
        if len(y2):
            fig, ax = plt.subplots(figsize=(7.2, 3.8))
            ax.plot(y2["year"], y2["nmi_prev"], color=BLUE, linewidth=2, marker="o", markersize=6,
                    markeredgecolor="white", markeredgewidth=1, label="Consecutive years")
            if "nmi_other_seed" in yearly and yearly["nmi_other_seed"].notna().any():
                ax.plot(yearly["year"], yearly["nmi_other_seed"], color=ORANGE, linewidth=2, marker="o",
                        markersize=6, markeredgecolor="white", markeredgewidth=1,
                        label="Same year, different random seed")
                ax.legend(frameon=False, fontsize=9, labelcolor=INK, loc="lower right")
            ax.set_ylim(0, 1); ax.set_xticks(yearly["year"])
            ax.set_xlabel("Year"); ax.set_ylabel("NMI")
            ax.set_title("Stability of the community structure from year to year"); _style(ax)
            fig.tight_layout(); fig.savefig(figdir / "yearly_stability.png", dpi=200); plt.close(fig)

    # 3. forwards between communities (row-normalised)
    mat, labels = flows_info
    fig, ax = plt.subplots(figsize=(7.4, 6.4))
    im = ax.imshow(mat, cmap=seq, vmin=0, vmax=1)
    ax.set_xticks(range(len(labels))); ax.set_xticklabels(labels, rotation=60, fontsize=8)
    ax.set_yticks(range(len(labels))); ax.set_yticklabels(labels, fontsize=8)
    ax.set_xlabel("Destination community (forwarded the message)")
    ax.set_ylabel("Origin community (wrote the message)")
    ax.set_title("Where each community's messages are forwarded (share of its outgoing forwards)")
    ax.title.set_fontsize(10)
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            if mat[i, j] >= 0.10:
                ax.text(j, i, f"{mat[i, j]*100:.0f}", ha="center", va="center", fontsize=7,
                        color="white" if mat[i, j] > 0.5 else INK)
    cb = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02); cb.ax.tick_params(labelsize=8)
    cb.set_label("Share of outgoing forwards", fontsize=9, color=MUTED)
    fig.tight_layout(); fig.savefig(figdir / "flows_between_communities.png", dpi=200); plt.close(fig)

    print(f"  charts written to {figdir}")



# ---------------------------------------------------------------- v1-style charts, Gephi meta-graph

def resolution_curve(net, resolutions, seed, base_res, base_stats):
    """Leiden at several resolutions (the base one is reused): communities and modularity."""
    rows = []
    for r in resolutions:
        t = time.time()
        if abs(r - base_res) < 1e-9:
            st, secs = base_stats, np.nan
        else:
            st = partition_stats(net, relabel_by_size(run_leiden(net, r, seed)))
            secs = round(time.time() - t)
        rows.append({"resolution": r, "n_communities": st["n_communities"], "modularity": st["modularity"],
                     "intra_share": st["intra_share"], "largest_share": st["largest_share"], "seconds": secs})
        print(f"  resolution {r}: {st['n_communities']:,} communities, Q={st['modularity']}")
    return pd.DataFrame(rows)


def meta_graph(net, mem, top):
    """Community-level graph of the `top` largest communities (undirected, as in v1).
    Edge weight = forwards between the two communities (both directions), `links` = distinct channel pairs."""
    top = min(top, int(mem.max()) + 1)
    sizes = np.bincount(mem)
    co, cd = mem[net.src], mem[net.dst]
    keep = (co < top) & (cd < top)
    df = (pd.DataFrame({"o": co[keep], "d": cd[keep], "w": net.w[keep]})
          .groupby(["o", "d"], as_index=False).agg(forwards=("w", "sum"), links=("w", "size")))
    inside = df[df.o == df.d].set_index("o")["forwards"]
    nodes = pd.DataFrame({"community": np.arange(top), "size": sizes[:top],
                          "forwards_inside": [int(inside.get(c, 0)) for c in range(top)]})
    between = df[df.o != df.d].copy()
    between["a"] = np.minimum(between.o, between.d)
    between["b"] = np.maximum(between.o, between.d)
    edges = between.groupby(["a", "b"], as_index=False)[["forwards", "links"]].sum()
    return nodes, edges


def write_gexf(path, meta):
    try:
        import networkx as nx
    except ImportError:
        print("  networkx not installed: meta_graph.gexf skipped")
        return
    nodes, edges = meta
    g = nx.Graph()
    for r in nodes.itertuples():
        g.add_node(int(r.community), label=f"Community {r.community} ({r.size:,} channels)",
                   size=int(r.size), forwards_inside=int(r.forwards_inside))
    for r in edges.itertuples():
        g.add_edge(int(r.a), int(r.b), weight=int(r.forwards), links=int(r.links))
    nx.write_gexf(g, str(path))


def extra_charts(figdir, net, mem, curve):
    """The v1 chart types: size histogram, degree CCDF, number of communities vs resolution."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    figdir = Path(figdir)
    _rc(plt)

    # histogram of community sizes (log y)
    sizes = np.bincount(mem)
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    ax.hist(sizes, bins=40, color="#2F5597", edgecolor="white", rwidth=0.9)
    ax.set_yscale("log")
    ax.set_xlabel("Community size (number of channels)")
    ax.set_ylabel("Number of communities (log scale)")
    ax.set_title("Distribution of community sizes"); _style(ax)
    fig.tight_layout(); fig.savefig(figdir / "community_size_distribution.png", dpi=200); plt.close(fig)

    # degree distribution: complementary CDF, log-log
    a, b, _ = undirected(net)
    n = len(net.nodes)
    deg = np.bincount(a, minlength=n) + np.bincount(b, minlength=n)
    v, c = np.unique(deg[deg > 0], return_counts=True)
    ccdf = c[::-1].cumsum()[::-1] / c.sum()
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    ax.plot(v, ccdf, color="#86B3A1", linewidth=2)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("Degree k (log scale)"); ax.set_ylabel("P(Degree >= k)  (log scale)")
    ax.set_title("Degree distribution - complementary CDF (log-log)"); _style(ax)
    ax.grid(True, which="minor", linestyle="--", linewidth=0.5, color="#e6e6e6")
    fig.tight_layout(); fig.savefig(figdir / "degree_distribution.png", dpi=200); plt.close(fig)

    # number of communities vs. Leiden resolution
    if curve is not None and len(curve) >= 2:
        fig, ax = plt.subplots(figsize=(7.2, 4.6))
        ax.plot(curve["resolution"], curve["n_communities"], color="#E8A33D", linewidth=2, marker="o")
        ax.set_xlabel("Resolution parameter"); ax.set_ylabel("Number of communities")
        ax.set_title("Number of communities vs. resolution (Leiden)"); _style(ax)
        fig.tight_layout(); fig.savefig(figdir / "resolution_curve.png", dpi=200); plt.close(fig)


FIG_DOC = {
    "community_size_distribution.png": "histogram of community sizes (log y).",
    "degree_distribution.png": "CCDF of node degree (log-log).",
    "resolution_curve.png": "number of communities vs. Leiden resolution (needs --resolution-curve).",
    "top_20_communities.png": "the largest communities, named by dominant language when --languages is given.",
    "community_size_rank.png": "community size against rank, log-log, one line per algorithm.",
    "flows_between_communities.png": "share of each community's outgoing forwards that go to each community (15 largest + other).",
    "yearly_structure.png": "active channels, communities and modularity per year.",
    "yearly_stability.png": "NMI between consecutive years, with the same-year/other-seed noise floor when --seed-baseline is used.",
    "meta_graph.gexf": "community-level meta-graph to open in Gephi. Node size = channel count, "
                       "edge weight = forwards between the two communities (attribute `links` = distinct channel pairs).",
}


def write_fig_readme(figdir):
    figdir = Path(figdir)
    png = [f for f in FIG_DOC if f.endswith(".png") and (figdir / f).exists()]
    lines = ["# Charts - Community detection (igraph + Leiden), v2", "",
             "All outputs produced by `community_detection_v2.py`.", "", "## Matplotlib PNG"]
    lines += [f"- `{f}` - {FIG_DOC[f]}" for f in png]
    if (figdir / "meta_graph.gexf").exists():
        lines += ["", "## Gephi", f"- `meta_graph.gexf` - {FIG_DOC['meta_graph.gexf']}"]
    (figdir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")



# ---------------------------------------------------------------- naming by dominant language (as in v1)

LANG_NAMES = {
    "ru": "Russian", "en": "English", "es": "Spanish", "fr": "French", "de": "German", "it": "Italian",
    "pt": "Portuguese", "tr": "Turkish", "ar": "Arabic", "fa": "Persian", "zh": "Chinese", "ja": "Japanese",
    "ko": "Korean", "hi": "Hindi", "id": "Indonesian", "uk": "Ukrainian", "pl": "Polish", "nl": "Dutch",
    "vi": "Vietnamese", "th": "Thai", "he": "Hebrew", "ha": "Hausa", "yo": "Yoruba", "ig": "Igbo",
    "am": "Amharic", "sw": "Swahili", "bg": "Bulgarian", "et": "Estonian", "ro": "Romanian", "el": "Greek",
    "sv": "Swedish", "da": "Danish", "fi": "Finnish", "no": "Norwegian", "cs": "Czech", "sk": "Slovak",
    "hu": "Hungarian", "sr": "Serbian", "hr": "Croatian", "lt": "Lithuanian", "lv": "Latvian",
    "ka": "Georgian", "az": "Azerbaijani", "kk": "Kazakh", "uz": "Uzbek", "ur": "Urdu", "bn": "Bengali",
    "ta": "Tamil", "ml": "Malayalam", "my": "Burmese", "km": "Khmer", "lo": "Lao", "mn": "Mongolian",
    "si": "Sinhala", "ps": "Pashto", "ku": "Kurdish",
}
NULL_LANG = {"", "nan", "none", "null", "unknown", "und", "n/a", "na", "-", "?"}


def load_language_map(path):
    """channel id -> language code, from Channel_Language.csv (tab-separated)."""
    df = pd.read_csv(path, sep="\t", dtype=str, index_col=0)
    df.columns = [c.strip() for c in df.columns]
    if "File Names" not in df.columns:
        df = pd.read_csv(path, sep="\t", dtype=str)
        df.columns = [c.strip() for c in df.columns]
    if "File Names" not in df.columns or "detected_language" not in df.columns:
        raise SystemExit(f"{path}: expected columns 'File Names' and 'detected_language', got {list(df.columns)}")
    ids = df["File Names"].astype(str).str.strip().str.replace(r"\.jsonl?$", "", regex=True)
    langs = df["detected_language"].fillna("").astype(str).str.strip()
    ok = ids.str.isdigit() & ~langs.str.lower().isin(NULL_LANG)
    out = dict(zip(pd.to_numeric(ids[ok]).astype("int64"), langs[ok]))
    print(f"  languages: {len(out):,} channels with a language ({len(df) - ok.sum():,} rows without)")
    return out


def name_communities(nodes, mem, lang_map):
    """Same rules as v1: '<Language> (<share>%, n=<known>/<size>)'; fewer than 3 known -> low confidence."""
    size = np.bincount(mem)
    lang = pd.Series(nodes).map(lang_map)
    known = pd.DataFrame({"c": mem, "lang": lang}).dropna(subset=["lang"])
    counts = known.groupby(["c", "lang"]).size().reset_index(name="n")
    n_known = counts.groupby("c")["n"].sum()
    top = counts.sort_values(["c", "n"], ascending=[True, False]).drop_duplicates("c").set_index("c")
    rows = []
    for c in range(len(size)):
        nk = int(n_known.get(c, 0))
        if nk == 0:
            name, dom, share = "Unknown (0 known)", "", np.nan
        else:
            code = str(top.loc[c, "lang"])
            dom = LANG_NAMES.get(code.lower(), code)
            share = float(top.loc[c, "n"]) / nk
            name = (f"Unknown (low confidence: {dom}? n={nk}/{size[c]})" if nk < 3
                    else f"{dom} ({share * 100:.0f}%, n={nk}/{size[c]})")
        rows.append({"community": c, "community_name": name, "dominant_language": dom,
                     "dominant_share": round(share, 4) if share == share else np.nan,
                     "n_known": nk, "size": int(size[c])})
    return pd.DataFrame(rows)


def top_communities_chart(figdir, mem, names, top=20):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    _rc(plt)
    sizes = np.bincount(mem)
    k = min(top, len(sizes))
    if names is not None:
        labels = names["community_name"].iloc[:k].tolist()
        title = f"Top {k} largest communities (named by dominant language)"
    else:
        labels = [f"Community {c}" for c in range(k)]
        title = f"Top {k} largest communities"
    fig, ax = plt.subplots(figsize=(11, 6.4))
    bars = ax.bar(range(k), sizes[:k], color="#5B8DD9")
    for x, v in enumerate(sizes[:k]):
        ax.text(x, v, f"{v:,}", ha="center", va="bottom", fontsize=7)
    ax.set_xticks(range(k)); ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=7.5)
    ax.set_xlabel("Community"); ax.set_ylabel("Number of channels"); ax.set_title(title)
    ax.grid(True, axis="y", linestyle="--", linewidth=0.8, color="#d9d9d9"); ax.set_axisbelow(True)
    ax.tick_params(axis="y", labelsize=9)
    fig.tight_layout(); fig.savefig(Path(figdir) / "top_20_communities.png", dpi=200); plt.close(fig)


# ---------------------------------------------------------------- main analysis

def analyse(edges, args, out):
    t0 = time.time()
    ctx = (f"- Input: monthly edges `{args.gold}` ({len(edges):,} (origin, destination, month) rows).\n"
           f"- Graph: forwards summed over all months, self-loops removed, pairs with fewer than "
           f"{args.min_weight} forward(s) dropped.\n"
           f"- Leiden: modularity objective, resolution {args.resolution}, seed {args.seed}, weights = number of "
           f"forwards, A->B and B->A summed (undirected).\n"
           f"- Infomap: directed, weights = number of forwards, {args.infomap_trials} trial(s).")
    W = Writer(out, ctx)

    net = build_net(edges, args.min_weight)
    print(f"graph: {len(net.nodes):,} channels, {len(net.src):,} directed pairs, {int(net.w.sum()):,} forwards "
          f"({time.time()-t0:.0f}s)")

    results, summary = {}, []
    t = time.time()
    leiden, reused = None, False
    prev_csv = Path(out) / "communities_leiden" / "communities_leiden.csv"
    if args.reuse_leiden and prev_csv.exists():
        s_prev = pd.read_csv(prev_csv).drop_duplicates("channel_id").set_index("channel_id")["community"]
        cand = s_prev.reindex(net.nodes)
        if cand.notna().all():
            leiden, reused = cand.to_numpy().astype(np.int64), True
            print(f"Leiden: reused from {prev_csv}")
        else:
            print("Leiden: previous file does not match this graph, recomputing")
    if leiden is None:
        leiden = relabel_by_size(run_leiden(net, args.resolution, args.seed))
    results["Leiden"] = leiden
    st = partition_stats(net, leiden)
    st.update(algorithm="leiden", codelength=np.nan, seconds=np.nan if reused else round(time.time() - t))
    summary.append(st)
    print(f"Leiden: {st['n_communities']:,} communities, modularity {st['modularity']}, "
          f"intra share {st['intra_share']}")
    if not args.skip_infomap:
        t = time.time()
        mem, cl = run_infomap(net, args.infomap_trials)
        info = relabel_by_size(mem)
        results["Infomap"] = info
        st = partition_stats(net, info); st.update(algorithm="infomap", codelength=round(cl, 4), seconds=round(time.time() - t))
        summary.append(st)
        print(f"Infomap: {st['n_communities']:,} communities, modularity {st['modularity']}, "
              f"intra share {st['intra_share']} ({st['seconds']}s)")

    strength = np.bincount(net.src, net.w, len(net.nodes)) + np.bincount(net.dst, net.w, len(net.nodes))
    for name, mem in results.items():
        sizes = np.bincount(mem)
        df = pd.DataFrame({"channel_id": net.nodes, "community": mem,
                           "community_size": sizes[mem], "forwards_total": strength.astype(np.int64)})
        df = df.sort_values(["community", "forwards_total"], ascending=[True, False])
        W.table(f"communities_{name.lower()}", df,
                f"Community of every channel that has at least one forward link, from {name}. "
                "Community 0 is the largest.",
                {"channel_id": "Telegram channel id", "community": "community number (0 = largest)",
                 "community_size": "number of channels in that community",
                 "forwards_total": "forwards in + out of the channel in the graph"})
    cols = {"algorithm": "leiden or infomap", "n_nodes": "channels in the graph",
            "n_edges_directed": "distinct (origin, destination) pairs", "total_forwards": "sum of the weights",
            "n_communities": "number of communities", "modularity": "weighted modularity (undirected, A<->B summed)",
            "intra_share": "share of forwards whose origin and destination are in the same community",
            "largest_community": "channels in the largest community", "largest_share": "that size / all channels",
            "top10_share": "share of channels in the 10 largest communities",
            "singletons": "communities with a single channel", "codelength": "Infomap map equation (bits), empty for Leiden",
            "seconds": "run time"}
    W.table("community_summary", pd.DataFrame(summary)[list(cols)],
            "Quality and size indicators of each partition of the full graph.", cols)

    W.table("community_profiles_leiden", profiles_table(net, leiden),
            "One row per Leiden community: size, forwards leaving, entering and staying inside, and the five most "
            "connected channels.",
            {"community": "community number", "size": "channels", "forwards_out": "forwards written by its channels",
             "forwards_in": "forwards made by its channels", "forwards_inside": "forwards from and to the same community",
             "inside_share_of_out": "forwards_inside / forwards_out", "top_channels": "five channels with the most forwards (in+out)"})

    ftab, big, has_other = flows_table(net, leiden, args.top_flows)
    W.table("community_flows_leiden", ftab,
            f"Forwards between the {big} largest Leiden communities (the others grouped as 'other').",
            {"origin_community": "community of the channel that wrote the message",
             "dest_community": "community of the channel that forwarded it", "forwards": "number of forwards",
             "share_of_origin_out": "forwards / all forwards of messages written in origin_community"})
    labels = [str(i) for i in range(big)] + (["other"] if has_other else [])
    m = np.zeros((len(labels), len(labels)))
    pos = {l: i for i, l in enumerate(labels)}
    for r in ftab.itertuples():
        m[pos[r.origin_community], pos[r.dest_community]] = r.share_of_origin_out

    # comparisons
    comp = []
    if "Infomap" in results:
        comp.append({"pair": "leiden_vs_infomap", **compare(net.nodes, leiden, net.nodes, results["Infomap"])})
    if args.seed_baseline:
        t = time.time()
        other = relabel_by_size(run_leiden(net, args.resolution, args.seed + 1))
        comp.append({"pair": "leiden_seed_vs_leiden_seed+1", **compare(net.nodes, leiden, net.nodes, other)})
        print(f"seed baseline (full graph): NMI {comp[-1]['nmi']} ({time.time()-t:.0f}s)")
    if comp:
        cc = {"pair": "partitions compared", "n_common": "channels present in both",
              "nmi": "normalized mutual information (0 = unrelated, 1 = identical)",
              "ari": "adjusted Rand index", "homogeneity": "each community of the 2nd partition holds channels of a single community of the 1st (1 = yes)",
              "completeness": "channels of a community of the 1st partition stay together in the 2nd"}
        W.table("community_comparison", pd.DataFrame(comp)[list(cc)],
                "Agreement between partitions, computed on the channels present in both. "
                "leiden_seed_vs_leiden_seed+1 is the same algorithm run twice with different random seeds: "
                "it measures how much of the disagreement between two partitions is just algorithm noise.", cc)

    # yearly
    yearly = None
    if not args.skip_yearly:
        rows, prev = [], None
        for y, sub in edges.groupby("year"):
            n_y = build_net(sub, 1)
            if len(n_y.src) < args.min_year_edges:
                print(f"  {y}: only {len(n_y.src):,} pairs, skipped")
                continue
            mem = relabel_by_size(run_leiden(n_y, args.resolution, args.seed))
            r = {"year": int(y), "n_channels": len(n_y.nodes), "n_edges": len(n_y.src),
                 "n_forwards": int(n_y.w.sum()), "n_communities": int(mem.max() + 1),
                 "modularity": round(modularity_undirected(n_y, mem), 4),
                 "largest_share": round(float(np.bincount(mem).max() / len(mem)), 4)}
            if args.seed_baseline:
                alt = relabel_by_size(run_leiden(n_y, args.resolution, args.seed + 1))
                r["nmi_other_seed"] = compare(n_y.nodes, mem, n_y.nodes, alt)["nmi"]
            if prev is not None:
                c = compare(n_y.nodes, mem, prev[0], prev[1])
                r.update(n_common_prev=c["n_common"], nmi_prev=c["nmi"], ari_prev=c["ari"])
            else:
                r.update(n_common_prev=np.nan, nmi_prev=np.nan, ari_prev=np.nan)
            rows.append(r); prev = (n_y.nodes, mem)
            print(f"  {y}: {r['n_channels']:,} channels, {r['n_communities']:,} communities, Q={r['modularity']}")
        yearly = pd.DataFrame(rows)
        yc = {"year": "calendar year", "n_channels": "channels with a link that year", "n_edges": "distinct pairs that year",
              "n_forwards": "forwards that year", "n_communities": "Leiden communities that year",
              "modularity": "modularity of that year's partition", "largest_share": "share of channels in the largest community",
              "n_common_prev": "channels present this year and the previous one", "nmi_prev": "NMI with the previous year",
              "ari_prev": "ARI with the previous year"}
        if "nmi_other_seed" in yearly:
            yc["nmi_other_seed"] = "NMI between two Leiden runs of the SAME year with different random seeds (noise floor)"
        if len(yearly):
            W.table("yearly_communities", yearly[list(yc)],
                    "One Leiden partition per year (same parameters) and its similarity to the previous year.", yc)

    curve = None
    if args.resolution_curve:
        print("resolution curve ...")
        curve = resolution_curve(net, [float(x) for x in args.curve_resolutions.split(",")], args.seed,
                                 args.resolution, partition_stats(net, leiden))
        cc = {"resolution": "Leiden resolution parameter", "n_communities": "number of communities",
              "modularity": "modularity of the partition (standard definition, resolution 1)",
              "intra_share": "share of forwards inside communities", "largest_share": "share of channels in the largest community",
              "seconds": "run time (empty for the resolution already computed)"}
        W.table("resolution_curve", curve[list(cc)],
                "Leiden run at several resolutions on the same graph: how the partition coarsens or splits.", cc)
    names = None
    lang_path = args.languages
    if lang_path is None:
        for cand in ("Channel_Language.csv", "telescope_files/Channel_Language.csv"):
            if Path(cand).exists():
                lang_path = cand
                break
    if lang_path:
        names = name_communities(net.nodes, leiden, load_language_map(lang_path))
        nc = {"community": "community number (0 = largest)", "community_name": "label built from the dominant language",
              "dominant_language": "language with most channels among those with a known language",
              "dominant_share": "its share among the channels with a known language",
              "n_known": "channels of the community with a known language", "size": "channels in the community"}
        W.table("community_names", names[list(nc)],
                "Name of each Leiden community: '<Language> (<share>%, n=<known>/<size>)', with fewer than 3 "
                "known channels the name is flagged low confidence; no known channel gives 'Unknown (0 known)'. "
                f"Languages from `{lang_path}`.", nc)
    else:
        print("  no Channel_Language.csv found: communities are numbered, not named (use --languages)")
    if not args.no_charts:
        figdir = Path(args.figdir)
        figdir.mkdir(parents=True, exist_ok=True)
        make_charts(figdir, results, yearly, (m, labels))
        extra_charts(figdir, net, leiden, curve)
        top_communities_chart(figdir, leiden, names, args.top)
        write_gexf(figdir / "meta_graph.gexf", meta_graph(net, leiden, args.meta_top))
        write_fig_readme(figdir)
    (Path(out) / "run_info.json").write_text(json.dumps(
        {"date": date.today().isoformat(), "tables": W.tables, "seconds": round(time.time() - t0),
         "args": {k: str(v) for k, v in vars(args).items()}}, indent=2), encoding="utf-8")
    print(f"done in {time.time()-t0:.0f}s -> {out}")
    return results, net


# ---------------------------------------------------------------- selftest

def synthetic(seed=0, groups=6, size=50, years=(2020, 2021, 2022)):
    """Planted partition: `groups` communities, dense inside, sparse between."""
    rng = np.random.default_rng(seed)
    ids = 1000 + np.arange(groups * size)
    truth = np.repeat(np.arange(groups), size)
    rows = []
    for y in years:
        for mth in range(1, 13):
            for _ in range(900):
                o = rng.integers(len(ids))
                same = rng.random() < 0.92
                cands = np.where(truth == truth[o])[0] if same else np.where(truth != truth[o])[0]
                d = rng.choice(cands)
                if d != o:
                    rows.append((ids[o], ids[d], f"{y}-{mth:02d}", int(rng.integers(1, 6))))
    df = pd.DataFrame(rows, columns=["origin_channel", "dest_channel", "month", "n_forwards"])
    df = df.groupby(["origin_channel", "dest_channel", "month"], as_index=False)["n_forwards"].sum()
    return df, ids, truth


def selftest(args):
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        df, ids, truth = synthetic()
        (tmp / "gold" / "edges_monthly_csv").mkdir(parents=True)
        df.to_csv(tmp / "gold" / "edges_monthly_csv" / "part-0.csv", index=False)
        args.gold, args.out = str(tmp / "gold"), str(tmp / "out")
        args.figdir = str(tmp / "figs")
        lang_codes = np.array(["ru", "en", "fa"])[truth % 3]
        known = np.random.default_rng(3).random(len(ids)) < 0.7
        pd.DataFrame({"File Names": [f"{i}.jsonl" for i in ids],
                      "detected_language": np.where(known, lang_codes, "")}).to_csv(tmp / "lang.csv", sep="\t")
        args.languages = str(tmp / "lang.csv")
        args.min_year_edges = 100
        edges = load_edges(args.gold)
        args.seed_baseline = True
        args.resolution_curve, args.curve_resolutions, args.meta_top = True, "0.5,1.0,2.0", 10
        results, net = analyse(edges, args, args.out)
        first = pd.read_csv(Path(args.out) / "communities_leiden" / "communities_leiden.csv")
        args.reuse_leiden, args.skip_yearly = True, True          # second pass must reuse, not recompute
        results2, _ = analyse(edges, args, args.out)
        again = pd.read_csv(Path(args.out) / "communities_leiden" / "communities_leiden.csv")
        assert first.sort_values("channel_id")["community"].tolist() == again.sort_values("channel_id")["community"].tolist(), \
            "reused Leiden partition differs from the saved one"
        print("  reuse of the saved Leiden partition: OK")
        args.reuse_leiden, args.skip_yearly = False, False
        truth_s = pd.Series(truth, index=ids).loc[net.nodes].to_numpy()
        for name, mem in results.items():
            nmi = compare(net.nodes, mem, net.nodes, truth_s)["nmi"]
            print(f"  {name} vs planted truth: NMI = {nmi}")
            assert nmi > 0.85, f"{name} does not recover the planted communities (NMI {nmi})"
        for t in ("communities_leiden", "community_summary", "community_profiles_leiden",
                  "community_flows_leiden", "community_comparison", "yearly_communities"):
            assert (Path(args.out) / t / f"{t}.csv").exists() and (Path(args.out) / t / "README.md").exists(), t
        if not args.no_charts:
            for f in ("community_size_rank", "community_size_distribution", "degree_distribution",
                      "resolution_curve", "yearly_structure", "yearly_stability",
                      "flows_between_communities"):
                assert (Path(args.figdir) / f"{f}.png").exists(), f
            assert (Path(args.figdir) / "meta_graph.gexf").exists(), "meta_graph.gexf"
            assert (Path(args.figdir) / "top_20_communities.png").exists(), "top_20_communities.png"
            nm = pd.read_csv(Path(args.out) / "community_names" / "community_names.csv")
            print("  names:", nm["community_name"].tolist()[:3])
            assert nm["community_name"].str.contains(r"Russian|English|Persian").all(), "community naming"
            assert (Path(args.figdir) / "README.md").exists(), "figures/README.md"
        print("\nSELFTEST PASSED")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--gold", default="telescope_pipeline_files/gold")
    ap.add_argument("--out", default="communities_v2", help="tables: one folder per CSV, each with its README")
    ap.add_argument("--figdir", default="figures/community_detection", help="charts only (PNG + meta_graph.gexf)")
    ap.add_argument("--resolution", type=float, default=1.0)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--min-weight", type=int, default=1, help="drop pairs with fewer total forwards")
    ap.add_argument("--infomap-trials", type=int, default=1)
    ap.add_argument("--skip-infomap", action="store_true")
    ap.add_argument("--reuse-leiden", action="store_true",
                    help="load the Leiden partition from <out>/communities_leiden instead of recomputing it")
    ap.add_argument("--seed-baseline", action="store_true",
                    help="also run Leiden with a second seed (full graph and each year): the noise floor")
    ap.add_argument("--skip-yearly", action="store_true")
    ap.add_argument("--resolution-curve", action="store_true",
                    help="run Leiden at several resolutions (about 3-4 min each on the full graph)")
    ap.add_argument("--curve-resolutions", default="0.5,0.8,1.0,1.2,1.5,2.0")
    ap.add_argument("--languages", default=None,
                    help="Channel_Language.csv (tab-separated, 'File Names' + 'detected_language'): "
                         "names the communities by dominant language, as in v1")
    ap.add_argument("--top", type=int, default=20, help="communities shown in top_20_communities.png")
    ap.add_argument("--meta-top", type=int, default=50, help="communities kept in meta_graph.gexf")
    ap.add_argument("--min-year-edges", type=int, default=5000)
    ap.add_argument("--top-flows", type=int, default=15)
    ap.add_argument("--no-charts", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest(args)
    edges = load_edges(args.gold)
    print(f"loaded {len(edges):,} monthly edge rows, years {edges.year.min()}-{edges.year.max()}")
    analyse(edges, args, args.out)


if __name__ == "__main__":
    main()