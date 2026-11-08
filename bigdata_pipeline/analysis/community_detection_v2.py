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
  5. Comparison with the v1 partition (--v1 communities.csv): NMI, ARI, homogeneity, completeness.

Every table is written as its own folder  <out>/<name>/<name>.csv + README.md
(how it was generated, what the columns mean), the convention of the project.
Charts (English) go to <out>/figures/.

Usage
  python3 community_detection_v2.py --selftest
  python3 community_detection_v2.py --gold telescope_pipeline_files/gold --out communities_v2 \
         --v1 communities/communities.csv
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


def load_v1(path):
    df = pd.read_csv(path)
    low = {c.lower(): c for c in df.columns}
    idc = next((low[c] for c in ("channel_id", "node", "id", "channel", "channelid") if c in low), df.columns[0])
    cc = next((low[c] for c in ("community", "comm", "louvain", "leiden", "cluster", "community_id") if c in low), df.columns[1])
    print(f"  v1 file: id column = '{idc}', community column = '{cc}', {len(df):,} rows")
    df = df[[idc, cc]].dropna().drop_duplicates(idc)
    return df[idc].astype("int64").to_numpy(), pd.factorize(df[cc])[0].astype(np.int64)


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
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color("#b8b7b1")
    ax.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.xaxis.label.set_color(MUTED)
    ax.yaxis.label.set_color(MUTED)


def make_charts(figdir, results, yearly, flows_info, v1_cont):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap
    figdir = Path(figdir)
    figdir.mkdir(parents=True, exist_ok=True)
    seq = LinearSegmentedColormap.from_list("blue_seq", ["#eef4fc", "#b5d0f2", "#2a78d6", "#0d3b78"])
    plt.rcParams.update({"font.size": 10, "axes.titlesize": 11, "axes.titleweight": "bold",
                         "axes.titlecolor": INK, "figure.dpi": 100})

    # 1. community size distribution
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    for (name, mem), col in zip(results.items(), (BLUE, ORANGE)):
        s = np.sort(np.bincount(mem))[::-1]
        ax.plot(np.arange(1, len(s) + 1), s, color=col, linewidth=2, label=f"{name} ({len(s):,} communities)")
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("Community rank (1 = largest)"); ax.set_ylabel("Channels in the community")
    ax.set_title("Community size distribution"); _style(ax)
    ax.legend(frameon=False, fontsize=9, labelcolor=INK)
    fig.tight_layout(); fig.savefig(figdir / "fig_community_sizes.png", dpi=200); plt.close(fig)

    # 2. yearly structure (three panels, one measure each)
    if yearly is not None and len(yearly) >= 2:
        fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.6), sharex=True)
        for ax, col, title in zip(axes, ("n_channels", "n_communities", "modularity"),
                                  ("Active channels", "Communities (Leiden)", "Modularity (Leiden)")):
            ax.plot(yearly["year"], yearly[col], color=BLUE, linewidth=2, marker="o", markersize=5,
                    markeredgecolor="white", markeredgewidth=1)
            ax.set_title(title); _style(ax)
            ax.set_xticks(yearly["year"]); ax.tick_params(axis="x", rotation=60)
        fig.tight_layout(); fig.savefig(figdir / "fig_yearly_structure.png", dpi=200); plt.close(fig)

        y2 = yearly.dropna(subset=["nmi_prev"])
        if len(y2):
            fig, ax = plt.subplots(figsize=(7.2, 3.8))
            ax.plot(y2["year"], y2["nmi_prev"], color=BLUE, linewidth=2, marker="o", markersize=6,
                    markeredgecolor="white", markeredgewidth=1)
            ax.set_ylim(0, 1); ax.set_xticks(y2["year"])
            ax.set_xlabel("Year"); ax.set_ylabel("NMI with the previous year")
            ax.set_title("Stability of the community structure from year to year"); _style(ax)
            fig.tight_layout(); fig.savefig(figdir / "fig_yearly_stability.png", dpi=200); plt.close(fig)

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
    fig.tight_layout(); fig.savefig(figdir / "fig_flows_between_communities.png", dpi=200); plt.close(fig)

    # 4. v1 vs v2
    if v1_cont is not None:
        cont, rl, cl = v1_cont
        fig, ax = plt.subplots(figsize=(7.4, 6.0))
        im = ax.imshow(cont, cmap=seq, vmin=0, vmax=1)
        ax.set_xticks(range(len(cl))); ax.set_xticklabels(cl, fontsize=8)
        ax.set_yticks(range(len(rl))); ax.set_yticklabels(rl, fontsize=8)
        ax.set_xlabel("v2 community (Leiden, message-level graph)")
        ax.set_ylabel("v1 community")
        ax.set_title("Where the channels of each v1 community end up in v2 (row share)")
        ax.title.set_fontsize(10)
        for i in range(cont.shape[0]):
            for j in range(cont.shape[1]):
                if cont[i, j] >= 0.15:
                    ax.text(j, i, f"{cont[i, j]*100:.0f}", ha="center", va="center", fontsize=7,
                            color="white" if cont[i, j] > 0.5 else INK)
        cb = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02); cb.ax.tick_params(labelsize=8)
        fig.tight_layout(); fig.savefig(figdir / "fig_v1_vs_v2.png", dpi=200); plt.close(fig)
    print(f"  charts written to {figdir}")


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
    leiden = relabel_by_size(run_leiden(net, args.resolution, args.seed))
    results["Leiden"] = leiden
    st = partition_stats(net, leiden); st.update(algorithm="leiden", codelength=np.nan, seconds=round(time.time() - t))
    summary.append(st)
    print(f"Leiden: {st['n_communities']:,} communities, modularity {st['modularity']}, "
          f"intra share {st['intra_share']} ({st['seconds']}s)")
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
    comp, v1_cont = [], None
    if "Infomap" in results:
        comp.append({"pair": "leiden_vs_infomap", **compare(net.nodes, leiden, net.nodes, results["Infomap"])})
    if args.v1:
        v1n, v1m = load_v1(args.v1)
        for name, mem in results.items():
            comp.append({"pair": f"{name.lower()}_vs_v1", **compare(net.nodes, mem, v1n, v1m)})
        s1 = pd.Series(v1m, index=v1n)
        s2 = pd.Series(leiden, index=net.nodes)
        common = s1.index.intersection(s2.index)
        top1 = s1.loc[common].value_counts().index[:12]
        top2 = s2.loc[common].value_counts().index[:12]
        ct = pd.crosstab(s1.loc[common], s2.loc[common]).loc[top1, top2]
        full = pd.crosstab(s1.loc[common], s2.loc[common]).loc[top1].sum(axis=1)
        v1_cont = ((ct.div(full, axis=0)).to_numpy(), [f"v1-{i}" for i in range(len(top1))],
                   [str(c) for c in top2])
    if comp:
        cc = {"pair": "partitions compared", "n_common": "channels present in both",
              "nmi": "normalized mutual information (0 = unrelated, 1 = identical)",
              "ari": "adjusted Rand index", "homogeneity": "each community of the 2nd partition holds channels of a single community of the 1st (1 = yes)",
              "completeness": "channels of a community of the 1st partition stay together in the 2nd"}
        W.table("community_comparison", pd.DataFrame(comp)[list(cc)],
                "Agreement between partitions, computed on the channels present in both.", cc)

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
        if len(yearly):
            W.table("yearly_communities", yearly[list(yc)],
                    "One Leiden partition per year (same parameters) and its similarity to the previous year.", yc)

    if not args.no_charts:
        make_charts(Path(out) / "figures", results, yearly, (m, labels), v1_cont)
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
        # a "v1" partition: truth with 15 % of the channels moved to a wrong community
        rng = np.random.default_rng(1)
        v1 = truth.copy()
        moved = rng.random(len(v1)) < 0.15
        v1[moved] = rng.integers(0, 6, moved.sum())
        pd.DataFrame({"channel_id": ids, "community": v1}).to_csv(tmp / "v1.csv", index=False)
        args.gold, args.out, args.v1 = str(tmp / "gold"), str(tmp / "out"), str(tmp / "v1.csv")
        args.min_year_edges = 100
        edges = load_edges(args.gold)
        results, net = analyse(edges, args, args.out)
        truth_s = pd.Series(truth, index=ids).loc[net.nodes].to_numpy()
        for name, mem in results.items():
            nmi = compare(net.nodes, mem, net.nodes, truth_s)["nmi"]
            print(f"  {name} vs planted truth: NMI = {nmi}")
            assert nmi > 0.85, f"{name} does not recover the planted communities (NMI {nmi})"
        for t in ("communities_leiden", "community_summary", "community_profiles_leiden",
                  "community_flows_leiden", "community_comparison", "yearly_communities"):
            assert (Path(args.out) / t / f"{t}.csv").exists() and (Path(args.out) / t / "README.md").exists(), t
        if not args.no_charts:
            for f in ("fig_community_sizes", "fig_yearly_structure", "fig_yearly_stability",
                      "fig_flows_between_communities", "fig_v1_vs_v2"):
                assert (Path(args.out) / "figures" / f"{f}.png").exists(), f
        print("\nSELFTEST PASSED")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--gold", default="telescope_pipeline_files/gold")
    ap.add_argument("--out", default="communities_v2")
    ap.add_argument("--v1", default=None, help="v1 communities CSV (channel id + community columns)")
    ap.add_argument("--resolution", type=float, default=1.0)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--min-weight", type=int, default=1, help="drop pairs with fewer total forwards")
    ap.add_argument("--infomap-trials", type=int, default=1)
    ap.add_argument("--skip-infomap", action="store_true")
    ap.add_argument("--skip-yearly", action="store_true")
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