#!/usr/bin/env python3
"""
TeleScope v2 - Theme 2: language communities.

Question: do the communities found without any language information (Leiden, theme 1)
line up with the language of the channels, and how much does language drive forwarding?

Inputs
  --communities  communities_leiden.csv written by community_detection_v2.py (channel_id, community)
  --languages    Channel_Language.csv (tab separated, 'File Names' + 'detected_language')
  --gold         gold folder of the pipeline (edges_monthly) - forwards between channels

Analyses (every table is a folder with its CSV and a README, images go to --figdir)
  1. community_language_purity  per community: dominant language, purity, entropy, known channels
  2. language_summary           global agreement: purity, NMI, ARI, homogeneity, completeness
  3. language_homophily         per language: share of its forwards that stay in the same language,
                                against the share expected if forwards ignored language
  4. language_flows             language -> language forwards (top pairs)
  5. language_spread            how many communities each language is split over
  6. inference_accuracy / channel_language_inferred
                                language of unlabelled channels guessed from their neighbours,
                                with accuracy measured by hiding known labels (holdout)
                                Inferred values are labelled 'inferred' and never replace the detected ones.

  7. language_yearly / language_yearly_by_language
                                evolution by year: language mix, diversity (entropy, effective number of languages),
                                share of forwards staying in a language, assortativity, cohesion of each main language
  8. language_bridges           channels whose forwards cross a language boundary most (as source / as forwarder)
  9. language_activity / language_top_channels
                                weight and influence of each language (channels vs forwards received, messages if
                                gold/channel_stats has a recognisable message-count column) and its most forwarded channels
 10. diversity                  entropy of the language mix (global, per year) and of each language's audience

The communities are detected WITHOUT the language (see theme 1), so comparing them with the
language is not circular.

Run (from the project root):
  python3 bigdata_pipeline/analysis/language_analysis_v2.py \
      --communities bigdata_pipeline/analysis/communities_v2/communities_leiden/communities_leiden.csv \
      --languages telescope_files/Channel_Language.csv \
      --gold telescope_pipeline_files/gold \
      --out bigdata_pipeline/analysis/language_v2 \
      --figdir bigdata_pipeline/analysis/figures/language_communities
  python3 bigdata_pipeline/analysis/language_analysis_v2.py --selftest

This file must stay in the same folder as community_detection_v2.py (it reuses its readers).
"""
import argparse
import sys
import tempfile
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from community_detection_v2 import LANG_NAMES, NULL_LANG, build_net, load_edges, load_language_map  # noqa: E402

# labels seen in Channel_Language.csv that the theme 1 script does not know: complete them here
NULL_LANG.add("cannot determine")                       # not a language: the detector gave up
LANG_NAMES.update({"mk": "Macedonian", "ca": "Catalan", "af": "Afrikaans", "tl": "Tagalog", "cy": "Welsh",
                   "so": "Somali", "sq": "Albanian", "sl": "Slovenian", "zh-cn": "Chinese", "pa": "Punjabi",
                   "te": "Telugu", "cs": "Czech", "sk": "Slovak"})


def lname(code):
    return LANG_NAMES.get(str(code).lower(), str(code))


# ---------------------------------------------------------------- output

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
            f"`language_analysis_v2.py`, run on {date.today().isoformat()}.\n\n{self.context}\n\n"
            f"## Content ({len(df):,} rows)\n\n| Column | Meaning |\n|---|---|\n{cols}\n", encoding="utf-8")
        self.tables.append(name)
        print(f"  wrote {name}/ ({len(df):,} rows)")


# ---------------------------------------------------------------- computations

def purity_table(comm, lang):
    """One row per community, computed on the channels whose language is known."""
    df = pd.DataFrame({"community": comm.values, "lang": lang.reindex(comm.index).values})
    size = df.groupby("community").size()
    known = df.dropna(subset=["lang"])
    cnt = known.groupby(["community", "lang"]).size().reset_index(name="n")
    nk = cnt.groupby("community")["n"].sum()
    top = cnt.sort_values(["community", "n"], ascending=[True, False]).drop_duplicates("community").set_index("community")
    p = cnt.n / cnt.community.map(nk)
    ent = (-(p * np.log2(p))).groupby(cnt.community).sum()
    nlang = cnt.groupby("community").size()
    rows = []
    for c in size.index:
        k = int(nk.get(c, 0))
        if k == 0:
            rows.append({"community": c, "size": int(size[c]), "known_language": 0, "known_share": 0.0,
                         "dominant_language": "", "dominant_name": "", "purity": np.nan,
                         "entropy_bits": np.nan, "n_languages": 0})
            continue
        code = str(top.loc[c, "lang"])
        rows.append({"community": c, "size": int(size[c]), "known_language": k,
                     "known_share": round(k / size[c], 4), "dominant_language": code, "dominant_name": lname(code),
                     "purity": round(float(top.loc[c, "n"]) / k, 4), "entropy_bits": round(float(ent[c]), 4),
                     "n_languages": int(nlang[c])})
    return pd.DataFrame(rows).sort_values("community").reset_index(drop=True)


def agreement(comm, lang, min_known=3, purity=None):
    """Global agreement between the partition and the language (known channels only)."""
    from sklearn.metrics import (adjusted_rand_score, completeness_score, homogeneity_score,
                                 normalized_mutual_info_score)
    d = pd.DataFrame({"c": comm.values, "l": lang.reindex(comm.index).values}).dropna()
    out = {"channels_in_graph": len(comm), "channels_with_language": len(d),
           "coverage": round(len(d) / len(comm), 4), "communities": int(comm.nunique()),
           "languages": int(d.l.nunique())}
    cl = d.groupby(["c", "l"]).size()
    out["weighted_purity"] = round(float(cl.groupby(level=0).max().sum() / len(d)), 4)
    out["language_entropy_bits"], out["effective_languages"] = entropy_stats(d.l.value_counts().values)
    out["majority_language_share"] = round(float(d.l.value_counts(normalize=True).iloc[0]), 4)
    out["NMI"] = round(float(normalized_mutual_info_score(d.l, d.c)), 4)
    out["ARI"] = round(float(adjusted_rand_score(d.l, d.c)), 4)
    out["homogeneity"] = round(float(homogeneity_score(d.l, d.c)), 4)       # a community holds one language
    out["completeness"] = round(float(completeness_score(d.l, d.c)), 4)     # a language sits in one community
    if purity is not None:
        big = purity[(purity.known_language >= min_known)]
        out[f"communities_with_{min_known}plus_known"] = len(big)
        out["median_purity"] = round(float(big.purity.median()), 4) if len(big) else np.nan
        out["share_communities_purity_ge_0.8"] = round(float((big.purity >= 0.8).mean()), 4) if len(big) else np.nan
    return out


def entropy_stats(counts):
    """Shannon entropy (bits) and effective number of categories (2**entropy)."""
    p = np.asarray(counts, float)
    p = p[p > 0]
    if len(p) == 0:
        return np.nan, np.nan
    p = p / p.sum()
    h = float(-(p * np.log2(p)).sum())
    return round(h, 4), round(2 ** h, 2)


def language_edges(net, lang_by_node):
    """Directed forwards between channels whose language is known on both sides."""
    ls = lang_by_node[net.src]
    ld = lang_by_node[net.dst]
    ok = pd.notna(ls) & pd.notna(ld)
    return pd.DataFrame({"src": ls[ok], "dst": ld[ok], "w": net.w[ok]})


def flows_and_homophily(le):
    """Language-to-language forwards, per-language homophily and the global assortativity."""
    flow = le.groupby(["src", "dst"], as_index=False)["w"].sum()
    tot = flow.w.sum()
    out_l = flow.groupby("src")["w"].sum()
    in_l = flow.groupby("dst")["w"].sum()
    same = flow[flow.src == flow.dst].set_index("src")["w"]
    a = (out_l / tot)
    b = (in_l / tot)
    langs = sorted(set(a.index) | set(b.index))
    e_same = float(same.sum() / tot)
    exp_same = float(sum(a.get(l, 0) * b.get(l, 0) for l in langs))
    r = (e_same - exp_same) / (1 - exp_same) if exp_same < 1 else np.nan
    by_src = {k: g["w"].to_numpy() for k, g in flow.groupby("src")}
    rows = []
    for l in langs:
        o = float(out_l.get(l, 0))
        s = float(same.get(l, 0))
        exp = float(b.get(l, 0))                       # chance a forward lands in l if language did not matter
        sh = s / o if o else np.nan
        rows.append({"language": l, "language_name": lname(l), "forwards_out": int(o),
                     "forwards_in": int(in_l.get(l, 0)), "same_language_share": round(sh, 4),
                     "expected_share": round(exp, 4), "lift": round(sh / exp, 2) if exp else np.nan,
                     "audience_entropy_bits": entropy_stats(by_src[l])[0] if l in by_src else np.nan,
                     "audience_effective_languages": entropy_stats(by_src[l])[1] if l in by_src else np.nan})
    hom = pd.DataFrame(rows).sort_values("forwards_out", ascending=False).reset_index(drop=True)
    flow = flow.assign(share_of_source_out=(flow.w / flow.src.map(out_l)).round(4))
    flow["src_name"] = flow.src.map(lname)
    flow["dst_name"] = flow.dst.map(lname)
    flow = flow.rename(columns={"w": "forwards"}).sort_values("forwards", ascending=False)
    glob = {"forwards_between_known": int(tot), "same_language_share": round(e_same, 4),
            "expected_same_language_share": round(exp_same, 4),
            "lift": round(e_same / exp_same, 2) if exp_same else np.nan, "assortativity": round(float(r), 4)}
    return hom, flow[["src", "src_name", "dst", "dst_name", "forwards", "share_of_source_out"]], glob


def spread_table(comm, lang, min_channels=50):
    d = pd.DataFrame({"c": comm.values, "l": lang.reindex(comm.index).values}).dropna()
    rows = []
    for l, g in d.groupby("l"):
        if len(g) < min_channels:
            continue
        v = g.c.value_counts()
        cum = v.cumsum() / len(g)
        rows.append({"language": l, "language_name": lname(l), "channels": len(g), "communities": len(v),
                     "largest_community": int(v.index[0]), "share_in_largest": round(float(v.iloc[0] / len(g)), 4),
                     "communities_for_80pct": int((cum < 0.8).sum() + 1)})
    return pd.DataFrame(rows).sort_values("channels", ascending=False).reset_index(drop=True)


def infer_languages(net, lang_by_node, min_class=50, holdout=0.1, min_vote=0.6, seed=42):
    """Neighbour vote on the forward graph (both directions, weighted). Accuracy measured by holdout."""
    from scipy import sparse
    n = len(net.nodes)
    s = pd.Series(lang_by_node)
    counts = s.dropna().value_counts()
    classes = counts[counts >= min_class].index.tolist()
    if len(classes) < 2:
        return None, None
    cidx = {c: i for i, c in enumerate(classes)}
    cls = np.array([cidx.get(x, -1) if isinstance(x, str) else -1 for x in lang_by_node])
    A = sparse.coo_matrix((np.r_[net.w, net.w], (np.r_[net.src, net.dst], np.r_[net.dst, net.src])), shape=(n, n)).tocsr()

    def votes(known_mask):
        rows = np.where(known_mask & (cls >= 0))[0]
        Y = sparse.csr_matrix((np.ones(len(rows)), (rows, cls[rows])), shape=(n, len(classes)))
        return (A @ Y).toarray()

    known = cls >= 0
    rng = np.random.default_rng(seed)
    idx = np.where(known)[0]
    hold = rng.choice(idx, size=max(1, int(len(idx) * holdout)), replace=False)
    mask = known.copy()
    mask[hold] = False
    V = votes(mask)[hold]
    tot = V.sum(axis=1)
    base_class = int(np.bincount(cls[mask & (cls >= 0)], minlength=len(classes)).argmax())
    baseline = float((cls[hold] == base_class).mean())
    has = tot > 0
    share = np.where(has, V.max(axis=1) / np.where(has, tot, 1), 0)
    pred = V.argmax(axis=1)
    ok = pred == cls[hold]
    bins = [0, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0001]
    rows = []
    for lo, hi in zip(bins[:-1], bins[1:]):
        m = has & (share >= lo) & (share < hi)
        rows.append({"vote_share_from": lo, "vote_share_to": min(hi, 1.0), "held_out_channels": int(m.sum()),
                     "accuracy": round(float(ok[m].mean()), 4) if m.any() else np.nan})
    sel = has & (share >= min_vote)
    rows.append({"vote_share_from": min_vote, "vote_share_to": 1.0, "held_out_channels": int(sel.sum()),
                 "accuracy": round(float(ok[sel].mean()), 4) if sel.any() else np.nan})
    acc = pd.DataFrame(rows)
    acc["row"] = [f"{a:.1f}-{b:.1f}" for a, b in zip(acc.vote_share_from, acc.vote_share_to)]
    acc.loc[acc.index[-1], "row"] = f">= {min_vote} (rule used)"
    acc["baseline_majority_language"] = round(baseline, 4)
    acc["held_out_total"] = len(hold)
    acc["with_known_neighbour"] = int(has.sum())
    # final: unknown channels
    V2 = votes(known)
    unk = np.where(~pd.notna(pd.Series(lang_by_node)).to_numpy())[0]
    t2 = V2[unk].sum(axis=1)
    h2 = t2 > 0
    sh2 = np.where(h2, V2[unk].max(axis=1) / np.where(h2, t2, 1), 0)
    keep = h2 & (sh2 >= min_vote)
    inf = pd.DataFrame({"channel_id": net.nodes[unk][keep], "inferred_language": [classes[i] for i in V2[unk][keep].argmax(axis=1)],
                        "vote_share": sh2[keep].round(4), "neighbour_forwards": t2[keep].astype(int), "source": "inferred"})
    return acc, inf



def yearly_tables(edges, lang, keep_ids, min_forwards=5000, top_n=8):
    """Year by year: language mix of active channels, diversity, and how much forwarding stays in a language."""
    e = edges[edges.origin_channel != edges.dest_channel]
    e = e[e.origin_channel.isin(keep_ids) & e.dest_channel.isin(keep_ids)]
    e = e.assign(ls=e.origin_channel.map(lang), ld=e.dest_channel.map(lang))
    rows, by_lang = [], []
    for y, g in e.groupby("year"):
        k = g.dropna(subset=["ls", "ld"])
        tot = int(k.n_forwards.sum())
        if tot < min_forwards:
            continue
        hom, _, glob = flows_and_homophily(pd.DataFrame({"src": k.ls, "dst": k.ld, "w": k.n_forwards}))
        active = pd.unique(pd.concat([g.origin_channel, g.dest_channel]))
        al = lang.reindex(active).dropna()
        cnt = al.value_counts()
        h, eff = entropy_stats(cnt.values)
        rows.append({"year": int(y), "active_channels": len(active), "active_with_language": len(al),
                     "languages": int(cnt.size), "top_language": cnt.index[0],
                     "top_language_share": round(float(cnt.iloc[0] / len(al)), 4),
                     "language_entropy_bits": h, "effective_languages": eff, "forwards_between_known": tot,
                     "same_language_share": glob["same_language_share"],
                     "expected_same_language_share": glob["expected_same_language_share"],
                     "assortativity": glob["assortativity"]})
        for _, r in hom.iterrows():
            n_act = int(cnt.get(r.language, 0))
            by_lang.append({"year": int(y), "language": r.language, "language_name": r.language_name,
                            "active_channels": n_act, "share_of_active": round(n_act / len(al), 4),
                            "forwards_out": int(r.forwards_out), "same_language_share": r.same_language_share,
                            "lift": r.lift})
    yr = pd.DataFrame(rows)
    byl = pd.DataFrame(by_lang)
    if len(byl):
        top = byl.groupby("language")["forwards_out"].sum().nlargest(top_n).index
        byl = byl[byl.language.isin(top)].sort_values(["language", "year"]).reset_index(drop=True)
    return yr, byl


def bridges_table(net, lang_by_node, comm_by_node, top=30, min_forwards=50):
    """Channels whose forwards most often cross a language boundary, as source (exports) or as forwarder (imports)."""
    ls, ld = lang_by_node[net.src], lang_by_node[net.dst]
    ok = pd.notna(ls) & pd.notna(ld)
    d = pd.DataFrame({"src": net.src[ok], "dst": net.dst[ok], "ls": ls[ok], "ld": ld[ok], "w": net.w[ok]})
    d["cross"] = d.ls != d.ld
    rows = []
    for direction, node_col, other in (("exports", "src", "ld"), ("imports", "dst", "ls")):
        tot = d.groupby(node_col)["w"].sum()
        c = d[d.cross]
        cr = c.groupby(node_col)["w"].sum()
        oth = (c.groupby([node_col, other])["w"].sum().reset_index()
               .sort_values([node_col, "w"], ascending=[True, False]).drop_duplicates(node_col).set_index(node_col)[other])
        t = pd.DataFrame({"total": tot, "cross": cr}).fillna(0)
        t = t[t.total >= min_forwards].sort_values("cross", ascending=False).head(top)
        for rank, (node, r) in enumerate(t.iterrows(), 1):
            code = lang_by_node[node]
            rows.append({"direction": direction, "rank": rank, "channel_id": int(net.nodes[node]), "language": code,
                         "language_name": lname(code), "community": int(comm_by_node[node]),
                         "forwards_with_known_language": int(r.total), "forwards_across_languages": int(r.cross),
                         "cross_share": round(float(r.cross / r.total), 4),
                         "main_other_language": lname(oth.get(node, "")) if node in oth.index else ""})
    return pd.DataFrame(rows, columns=["direction", "rank", "channel_id", "language", "language_name", "community",
                                       "forwards_with_known_language", "forwards_across_languages", "cross_share",
                                       "main_other_language"])


def load_channel_stats(gold, id_col=None, msg_col=None):
    """Optional: message counts per channel from gold/channel_stats (Parquet) or channel_stats_csv/*.csv."""
    gold = Path(gold)
    pq, csvdir = gold / "channel_stats", gold / "channel_stats_csv"
    df = None
    if pq.exists():
        try:
            df = pd.read_parquet(pq)
        except Exception:
            df = None
    if df is None and csvdir.exists():
        parts = sorted(csvdir.glob("*.csv"))
        if parts:
            df = pd.concat((pd.read_csv(p) for p in parts), ignore_index=True)
    if df is None:
        print("  channel_stats not found: activity table without message counts")
        return None
    idc = id_col or next((c for c in ("channel_id", "channel", "origin_channel") if c in df.columns), None)
    mc = msg_col or next((c for c in ("n_messages", "messages", "message_count", "n_msgs", "total_messages", "nb_messages")
                          if c in df.columns), None)
    if idc not in df.columns or mc not in df.columns:
        print(f"  channel_stats columns are {list(df.columns)}: no message count recognised "
              f"(pass --stats-id-col and --stats-msg-col)")
        return None
    out = pd.DataFrame({"channel_id": pd.to_numeric(df[idc], errors="coerce"),
                        "messages": pd.to_numeric(df[mc], errors="coerce")}).dropna()
    out["channel_id"] = out.channel_id.astype("int64")
    return out.groupby("channel_id", as_index=False)["messages"].sum()


def activity_tables(net, lang_by_node, comm_by_node, stats=None, top_langs=12, top_channels=10):
    n = len(net.nodes)
    df = pd.DataFrame({"channel_id": net.nodes, "language": lang_by_node, "community": comm_by_node,
                       "times_forwarded": np.bincount(net.src, net.w, n).astype(np.int64),
                       "forwards_made": np.bincount(net.dst, net.w, n).astype(np.int64)})
    if stats is not None:
        df = df.merge(stats, on="channel_id", how="left")
    k = df.dropna(subset=["language"])
    agg = {"channels": ("channel_id", "size"), "times_forwarded": ("times_forwarded", "sum"),
           "forwards_made": ("forwards_made", "sum")}
    if stats is not None:
        agg["messages"] = ("messages", "sum")
    g = k.groupby("language").agg(**agg).reset_index().sort_values("channels", ascending=False)
    g["language_name"] = g.language.map(lname)
    sc = g.channels / g.channels.sum()
    st = g.times_forwarded / g.times_forwarded.sum()
    g["share_of_channels"] = sc.round(6)
    g["share_of_times_forwarded"] = st.round(6)
    g["influence_ratio"] = (st / sc).round(2)                 # from unrounded shares
    g["forwarded_per_channel"] = (g.times_forwarded / g.channels).round(1)
    cols = ["language", "language_name", "channels", "share_of_channels", "times_forwarded",
            "share_of_times_forwarded", "influence_ratio", "forwarded_per_channel", "forwards_made"]
    if stats is not None:
        g["messages_per_channel"] = (g.messages / g.channels).round(1)
        cols += ["messages", "messages_per_channel"]
    g = g[cols].reset_index(drop=True)
    rows = []
    for code in g.language.head(top_langs):
        t = k[k.language == code].nlargest(top_channels, "times_forwarded")
        for rank, (_, r) in enumerate(t.iterrows(), 1):
            rows.append({"language": code, "language_name": lname(code), "rank": rank, "channel_id": int(r.channel_id),
                         "community": int(r.community), "times_forwarded": int(r.times_forwarded),
                         "forwards_made": int(r.forwards_made)})
    return g, pd.DataFrame(rows)


# ---------------------------------------------------------------- charts (same look as theme 1)

def _setup():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "serif", "font.size": 10, "axes.titlesize": 11, "axes.titleweight": "normal",
                         "axes.titlecolor": "black", "axes.labelcolor": "black", "figure.dpi": 100})
    return plt


def _grid(ax, axis="y"):
    ax.grid(True, axis=axis, linestyle="--", linewidth=0.8, color="#d9d9d9")
    ax.set_axisbelow(True)
    ax.tick_params(colors="#222222", labelsize=9)


def charts(figdir, lang, pur, hom, flow, acc, top=15):
    plt = _setup()
    fd = Path(figdir)
    fd.mkdir(parents=True, exist_ok=True)

    # 1. language distribution
    vc = lang.dropna().value_counts().head(top)
    fig, ax = plt.subplots(figsize=(10, 5.6))
    ax.bar(range(len(vc)), vc.values, color="#5B8DD9")
    for x, v in enumerate(vc.values):
        ax.text(x, v, f"{v:,}", ha="center", va="bottom", fontsize=7)
    ax.set_xticks(range(len(vc))); ax.set_xticklabels([lname(i) for i in vc.index], rotation=45, ha="right")
    ax.set_xlabel("Language"); ax.set_ylabel("Number of channels")
    ax.set_title(f"Top {len(vc)} languages among channels of the forward graph"); _grid(ax)
    fig.tight_layout(); fig.savefig(fd / "language_distribution.png", dpi=200); plt.close(fig)

    # 2. purity of the largest communities
    p = pur[pur.known_language >= 3].sort_values("size", ascending=False).head(20)
    if len(p):
        fig, ax = plt.subplots(figsize=(11, 6.4))
        ax.bar(range(len(p)), p.purity, color="#86B3A1")
        for x, (v, k) in enumerate(zip(p.purity, p.known_language)):
            ax.text(x, v, f"{v * 100:.0f}%", ha="center", va="bottom", fontsize=7)
        ax.set_xticks(range(len(p)))
        ax.set_xticklabels([f"C{c} {n} (n={k}/{s})" for c, n, k, s in
                            zip(p.community, p.dominant_name, p.known_language, p["size"])],
                           rotation=45, ha="right", fontsize=7.5)
        ax.set_ylim(0, 1.08); ax.set_ylabel("Share of the dominant language (known channels)")
        ax.set_xlabel("Community (largest first)")
        ax.set_title("Language purity of the 20 largest communities"); _grid(ax)
        fig.tight_layout(); fig.savefig(fd / "community_purity.png", dpi=200); plt.close(fig)

    # 3. same-language share vs expectation
    h = hom.head(12)
    if len(h):
        x = np.arange(len(h))
        fig, ax = plt.subplots(figsize=(10, 5.6))
        ax.bar(x - 0.2, h.same_language_share, 0.4, color="#2F5597", label="observed")
        ax.bar(x + 0.2, h.expected_share, 0.4, color="#E8A33D", label="expected if language did not matter")
        ax.set_xticks(x); ax.set_xticklabels(h.language_name, rotation=45, ha="right")
        ax.set_ylabel("Share of the language's forwards that stay in the language"); ax.set_xlabel("Language")
        ax.set_title("Forwards staying inside the same language"); ax.legend(frameon=False); _grid(ax)
        fig.tight_layout(); fig.savefig(fd / "language_homophily.png", dpi=200); plt.close(fig)

    # 4. flow matrix, row-normalised
    tops = hom.head(10).language.tolist()
    if len(tops) >= 2:
        f = flow.copy()
        f["s"] = f.src.where(f.src.isin(tops), "other")
        f["d"] = f.dst.where(f.dst.isin(tops), "other")
        m = f.groupby(["s", "d"])["forwards"].sum().unstack(fill_value=0)
        order = tops + (["other"] if "other" in m.index or "other" in m.columns else [])
        m = m.reindex(index=order, columns=order, fill_value=0)
        pm = m.div(m.sum(axis=1).replace(0, np.nan), axis=0)
        lab = [lname(i) if i != "other" else "Other" for i in order]
        fig, ax = plt.subplots(figsize=(9, 7.4))
        im = ax.imshow(pm.values, cmap="Blues", vmin=0, vmax=1)
        for i in range(len(order)):
            for j in range(len(order)):
                v = pm.values[i, j]
                if np.isfinite(v) and v >= 0.01:
                    ax.text(j, i, f"{v * 100:.0f}", ha="center", va="center", fontsize=7,
                            color="white" if v > 0.55 else "#222222")
        ax.set_xticks(range(len(order))); ax.set_xticklabels(lab, rotation=45, ha="right")
        ax.set_yticks(range(len(order))); ax.set_yticklabels(lab)
        ax.set_xlabel("Language of the channel that forwards (destination)")
        ax.set_ylabel("Language of the original channel (origin)")
        ax.set_title("Where forwards go, by language (% of each origin language's forwards)")
        fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02)
        fig.tight_layout(); fig.savefig(fd / "language_flows_heatmap.png", dpi=200); plt.close(fig)

    # 5. inference accuracy
    if acc is not None:
        a = acc.iloc[:-1]
        a = a[a.held_out_channels > 0]
        fig, ax = plt.subplots(figsize=(9, 5.6))
        ax.bar(range(len(a)), a.accuracy, color="#5B8DD9")
        for x, (v, n) in enumerate(zip(a.accuracy, a.held_out_channels)):
            ax.text(x, v, f"{v * 100:.0f}%\n(n={n:,})", ha="center", va="bottom", fontsize=7)
        ax.axhline(float(acc.baseline_majority_language.iloc[0]), color="#E8A33D", linestyle="--",
                   label="always predict the most frequent language")
        ax.set_xticks(range(len(a))); ax.set_xticklabels(a.row)
        ax.set_ylim(0, 1.15); ax.set_xlabel("Share of neighbour votes won by the winning language")
        ax.set_ylabel("Accuracy on hidden known channels")
        ax.set_title("Guessing a channel's language from its neighbours"); ax.legend(frameon=False, loc="lower right"); _grid(ax)
        fig.tight_layout(); fig.savefig(fd / "language_inference_accuracy.png", dpi=200); plt.close(fig)


PALETTE = ["#2F5597", "#E8A33D", "#86B3A1", "#C0504D", "#8064A2", "#4BACC6", "#F79646", "#7F7F7F"]


def extra_charts(figdir, yr, byl, br, act):
    plt = _setup()
    fd = Path(figdir)
    fd.mkdir(parents=True, exist_ok=True)

    if yr is not None and len(yr) >= 2:
        fig, ax = plt.subplots(figsize=(9, 5.4))
        ax.plot(yr.year, yr.same_language_share, "-o", color="#2F5597", label="observed share staying in the language")
        ax.plot(yr.year, yr.expected_same_language_share, "-s", color="#E8A33D", label="expected if language did not matter")
        ax.plot(yr.year, yr.assortativity, "-^", color="#86B3A1", label="assortativity (0 = language ignored)")
        ax.set_ylim(0, 1.03); ax.set_xticks(yr.year); ax.set_xlabel("Year"); ax.set_ylabel("Share / coefficient")
        ax.set_title("Do forwards stay inside a language? Evolution by year"); ax.legend(frameon=False, fontsize=8, loc="lower left")
        _grid(ax); fig.tight_layout(); fig.savefig(fd / "language_yearly_homophily.png", dpi=200); plt.close(fig)

        fig, ax = plt.subplots(figsize=(9, 5.4))
        ax.plot(yr.year, yr.effective_languages, "-o", color="#5B8DD9")
        for x, v, t in zip(yr.year, yr.effective_languages, yr.top_language_share):
            ax.text(x, v, f"{v:.2f}\n(top {t * 100:.0f}%)", ha="center", va="bottom", fontsize=7)
        ax.set_xticks(yr.year); ax.set_xlabel("Year"); ax.set_ylabel("Effective number of languages (2^entropy)")
        ax.set_title("Language diversity of the active channels, by year"); ax.set_ylim(bottom=1)
        _grid(ax); fig.tight_layout(); fig.savefig(fd / "language_yearly_diversity.png", dpi=200); plt.close(fig)

    if byl is not None and len(byl):
        order = byl.groupby("language")["forwards_out"].sum().sort_values(ascending=False).index.tolist()
        fig, ax = plt.subplots(figsize=(9.5, 5.6))
        for i, code in enumerate(order):
            g = byl[byl.language == code]
            ax.plot(g.year, g.share_of_active.replace(0, np.nan), "-o", ms=4, color=PALETTE[i % len(PALETTE)], label=lname(code))
        ax.set_yscale("log"); ax.set_xticks(sorted(byl.year.unique())); ax.set_xlabel("Year")
        ax.set_ylabel("Share of active channels with a known language (log scale)")
        ax.set_title("Weight of each language among active channels, by year"); ax.legend(frameon=False, fontsize=8, ncol=2)
        _grid(ax); fig.tight_layout(); fig.savefig(fd / "language_yearly_shares.png", dpi=200); plt.close(fig)

        fig, ax = plt.subplots(figsize=(9.5, 5.6))
        for i, code in enumerate(order[:6]):
            g = byl[byl.language == code].dropna(subset=["same_language_share"])
            ax.plot(g.year, g.same_language_share, "-o", ms=4, color=PALETTE[i % len(PALETTE)], label=lname(code))
        ax.set_ylim(0, 1.03); ax.set_xticks(sorted(byl.year.unique())); ax.set_xlabel("Year")
        ax.set_ylabel("Share of the language's forwards staying in the language")
        ax.set_title("Cohesion of each language, by year"); ax.legend(frameon=False, fontsize=8, ncol=2)
        _grid(ax); fig.tight_layout(); fig.savefig(fd / "language_yearly_cohesion.png", dpi=200); plt.close(fig)

    if br is not None and len(br):
        fig, axes = plt.subplots(1, 2, figsize=(13, 6.4))
        for ax, (direction, title, color) in zip(axes, (("exports", "Channels whose content is forwarded across languages", "#2F5597"),
                                                       ("imports", "Channels forwarding content from other languages", "#E8A33D"))):
            t = br[br.direction == direction].head(15).iloc[::-1]
            ax.barh(range(len(t)), t.forwards_across_languages, color=color)
            ax.set_yticks(range(len(t)))
            ax.set_yticklabels([f"{c} ({n})" for c, n in zip(t.channel_id, t.language_name)], fontsize=7.5)
            for y, (v, sh) in enumerate(zip(t.forwards_across_languages, t.cross_share)):
                ax.text(v, y, f" {v:,} ({sh * 100:.0f}%)", va="center", fontsize=7)
            ax.set_xlabel("Forwards across a language boundary"); ax.set_title(title, fontsize=10)
            ax.grid(True, axis="x", linestyle="--", linewidth=0.8, color="#d9d9d9"); ax.set_axisbelow(True)
            ax.set_xlim(0, t.forwards_across_languages.max() * 1.25 if len(t) else 1)
        fig.tight_layout(); fig.savefig(fd / "language_bridges.png", dpi=200); plt.close(fig)

    if act is not None and len(act):
        a = act.head(10)
        x = np.arange(len(a))
        fig, ax = plt.subplots(figsize=(10, 5.8))
        ax.bar(x - 0.2, a.share_of_channels, 0.4, color="#5B8DD9", label="share of channels")
        ax.bar(x + 0.2, a.share_of_times_forwarded, 0.4, color="#86B3A1", label="share of forwards received")
        for i, r in enumerate(a.influence_ratio):
            ax.text(i, max(a.share_of_channels.iloc[i], a.share_of_times_forwarded.iloc[i]), f"x{r:.1f}",
                    ha="center", va="bottom", fontsize=7)
        ax.set_yscale("log"); ax.set_xticks(x); ax.set_xticklabels(a.language_name, rotation=45, ha="right")
        ax.set_ylabel("Share (log scale)"); ax.set_xlabel("Language")
        ax.set_title("Weight and influence by language (xN = forwards received / channels)")
        ax.legend(frameon=False); _grid(ax); fig.tight_layout(); fig.savefig(fd / "language_activity.png", dpi=200); plt.close(fig)


def write_readme(figdir):
    Path(figdir).mkdir(parents=True, exist_ok=True)
    (Path(figdir) / "README.md").write_text(
        "# Figures - language communities (theme 2)\n\nImages only. Tables are in the language_v2 folder.\n\n"
        "| File | What it shows |\n|---|---|\n"
        "| language_distribution.png | channels per language (top 15) |\n"
        "| community_purity.png | share of the dominant language in the 20 largest communities |\n"
        "| language_homophily.png | share of each language's forwards that stay in the language, versus chance |\n"
        "| language_flows_heatmap.png | origin language (rows) to forwarding language (columns), % of each row |\n"
        "| language_inference_accuracy.png | accuracy of the neighbour-vote language guess on hidden known channels |\n"
        "| language_yearly_homophily.png | per year: share of forwards staying in a language, expectation, assortativity |\n"
        "| language_yearly_diversity.png | per year: effective number of languages among active channels |\n"
        "| language_yearly_shares.png | per year: weight of each main language among active channels |\n"
        "| language_yearly_cohesion.png | per year: share of each main language's forwards staying in the language |\n"
        "| language_bridges.png | channels whose forwards cross a language boundary most (as source / as forwarder) |\n"
        "| language_activity.png | share of channels versus share of forwards received, per language |\n",
        encoding="utf-8")


# ---------------------------------------------------------------- main

def analyse(args):
    out = Path(args.out)
    print("reading data")
    comm = pd.read_csv(args.communities, usecols=["channel_id", "community"]).drop_duplicates("channel_id")
    comm = comm.set_index("channel_id")["community"]
    lmap = {k: str(v).lower() for k, v in load_language_map(args.languages).items()}
    lang = pd.Series(lmap)
    lang = lang[~lang.index.duplicated()]
    print(f"  {len(comm):,} channels in the partition, {comm.nunique():,} communities")

    edges = load_edges(args.gold)
    net = build_net(edges, args.min_weight)
    keep = np.isin(net.nodes, comm.index.to_numpy())
    # keep only channels present in the partition
    from community_detection_v2 import Net
    remap = -np.ones(len(net.nodes), dtype=np.int64)
    remap[keep] = np.arange(keep.sum())
    m = keep[net.src] & keep[net.dst]
    net = Net(nodes=net.nodes[keep], src=remap[net.src[m]], dst=remap[net.dst[m]], w=net.w[m])
    lang_by_node = np.array([lang.get(c) for c in net.nodes], dtype=object)
    lang_by_node = np.where(pd.isna(pd.Series(lang_by_node)), None, lang_by_node)
    print(f"  graph: {len(net.nodes):,} channels, {len(net.src):,} links; "
          f"{pd.notna(pd.Series(lang_by_node)).sum():,} with a known language")

    ctx = (f"Partition: `{args.communities}` (Leiden, detected without language). Language: `{args.languages}`. "
           f"Forwards: `{args.gold}` (all months summed, self-loops removed, minimum weight {args.min_weight}).")
    W = Writer(out, ctx)

    pur = purity_table(comm, lang)
    W.table("community_language_purity", pur,
            "For each community: dominant language among its channels with a known language, and how pure it is.",
            {"community": "community number (0 = largest)", "size": "channels in the community",
             "known_language": "channels with a known language", "known_share": "known_language / size",
             "dominant_language": "most frequent language code", "dominant_name": "its name",
             "purity": "share of the dominant language among known channels",
             "entropy_bits": "Shannon entropy of the language mix (0 = single language)",
             "n_languages": "distinct languages present"})

    ag = agreement(comm, lang, purity=pur)
    le = language_edges(net, lang_by_node)
    hom, flow, glob = flows_and_homophily(le)
    ag.update({f"forwards_{k}" if not k.startswith("forwards") else k: v for k, v in glob.items()})
    summ = pd.DataFrame({"measure": list(ag.keys()), "value": list(ag.values())})
    W.table("language_summary", summ,
            "Global agreement between the communities and the languages, and how much forwarding stays inside a language. "
            "NMI/ARI close to 1 mean the partition recovers the languages; homogeneity = a community holds one language; "
            "completeness = a language is kept in one community. assortativity: 0 = language ignored, 1 = forwards never cross languages.",
            {"measure": "name of the measure", "value": "value"})

    W.table("language_homophily", hom,
            "For each origin language: share of its forwards received by channels of the same language, versus the share expected "
            "if forwards ignored language (= share of all forwards received by that language).",
            {"language": "code", "language_name": "name", "forwards_out": "forwards written about channels of this language",
             "forwards_in": "forwards received by channels of this language",
             "same_language_share": "share of forwards_out that land in the same language",
             "expected_share": "same share if language did not matter", "lift": "observed / expected",
             "audience_entropy_bits": "entropy of the languages that forward this language's content (0 = one language only)",
             "audience_effective_languages": "2^entropy: effective number of languages in its audience"})
    W.table("language_flows", flow.head(args.top_flows),
            f"The {args.top_flows} largest language-to-language flows (both channels with a known language).",
            {"src": "origin language", "src_name": "name", "dst": "forwarding language", "dst_name": "name",
             "forwards": "number of forwards", "share_of_source_out": "share of the origin language's forwards"})
    sp = spread_table(comm, lang)
    W.table("language_spread", sp,
            "For each language with at least 50 channels: how many communities it is spread over.",
            {"language": "code", "language_name": "name", "channels": "channels with this language",
             "communities": "communities containing at least one", "largest_community": "community with most of them",
             "share_in_largest": "share of its channels in that community",
             "communities_for_80pct": "communities needed to cover 80% of its channels"})

    acc = inf = None
    if not args.skip_inference:
        acc, inf = infer_languages(net, lang_by_node, args.min_class, 0.1, args.min_vote, args.seed)
        if acc is not None:
            W.table("inference_accuracy", acc[["row", "vote_share_from", "vote_share_to", "held_out_channels", "accuracy",
                                               "baseline_majority_language", "held_out_total", "with_known_neighbour"]],
                    "Accuracy of the neighbour-vote language guess, measured by hiding 10% of the known languages. "
                    "Compare with the baseline of always predicting the most frequent language.",
                    {"row": "bin of winning vote share", "vote_share_from": "bin lower bound", "vote_share_to": "bin upper bound",
                     "held_out_channels": "hidden channels in the bin", "accuracy": "share guessed right",
                     "baseline_majority_language": "accuracy of always guessing the most frequent language",
                     "held_out_total": "hidden channels in total",
                     "with_known_neighbour": "hidden channels having at least one neighbour with a known language"})
            W.table("channel_language_inferred", inf,
                    f"Channels without a detected language for which a language was inferred (winning vote share >= {args.min_vote}). "
                    "These values are guesses ('inferred'), not detections.",
                    {"channel_id": "Telegram channel id", "inferred_language": "guessed language code",
                     "vote_share": "share of neighbour forwards coming from that language",
                     "neighbour_forwards": "total forwards with neighbours of a known language", "source": "always 'inferred'"})

    yr = byl = None
    if not args.skip_yearly:
        yr, byl = yearly_tables(edges, lang, comm.index, args.min_year_forwards)
        if len(yr):
            W.table("language_yearly", yr,
                    "Year by year: language mix and diversity of the channels active that year, and how much of the forwarding "
                    "stays inside a language. Years with too few forwards between known-language channels are left out.",
                    {"year": "calendar year", "active_channels": "channels that forward or are forwarded that year",
                     "active_with_language": "of which with a known language", "languages": "distinct languages among them",
                     "top_language": "most frequent language", "top_language_share": "its share of the known active channels",
                     "language_entropy_bits": "Shannon entropy of the language mix",
                     "effective_languages": "2^entropy: how many equally frequent languages would give the same diversity",
                     "forwards_between_known": "forwards between channels with a known language",
                     "same_language_share": "share of those forwards that stay in the language",
                     "expected_same_language_share": "same share if language did not matter",
                     "assortativity": "0 = language ignored, 1 = forwards never cross languages"})
            W.table("language_yearly_by_language", byl,
                    "Year by year, for the eight languages that forward the most: their weight and cohesion.",
                    {"year": "calendar year", "language": "code", "language_name": "name",
                     "active_channels": "active channels with this language", "share_of_active": "share of the known active channels",
                     "forwards_out": "forwards of the language's content that year (both languages known)",
                     "same_language_share": "share of them received by the same language", "lift": "observed / expected"})
        else:
            print("  no year has enough forwards for the yearly tables (see --min-year-forwards)")
    br = act = None
    comm_by_node = comm.reindex(net.nodes).to_numpy()
    if not args.skip_bridges:
        br = bridges_table(net, lang_by_node, comm_by_node, args.bridges_top, args.bridges_min_forwards)
        W.table("language_bridges", br,
                "Channels with the most forwards across a language boundary: 'exports' = their content is forwarded by channels "
                "of another language; 'imports' = they forward content written by channels of another language. Only forwards "
                "where both channels have a known language are counted.",
                {"direction": "exports or imports", "rank": "rank inside the direction", "channel_id": "Telegram channel id",
                 "language": "its language code", "language_name": "name", "community": "its Leiden community",
                 "forwards_with_known_language": "its forwards in this direction with a known language on both sides",
                 "forwards_across_languages": "of which across a language boundary", "cross_share": "ratio of the two",
                 "main_other_language": "the foreign language involved most often"})
    if not args.skip_activity:
        stats = load_channel_stats(args.gold, args.stats_id_col, args.stats_msg_col)
        act, topch = activity_tables(net, lang_by_node, comm_by_node, stats)
        cols = {"language": "code", "language_name": "name", "channels": "channels with this language in the graph",
                "share_of_channels": "share of the channels with a known language",
                "times_forwarded": "times the content of these channels was forwarded", "share_of_times_forwarded": "its share of all",
                "influence_ratio": "share of forwards received / share of channels (above 1 = more influential than its size)",
                "forwarded_per_channel": "times_forwarded / channels", "forwards_made": "forwards these channels made",
                "messages": "messages written (from channel_stats)", "messages_per_channel": "messages / channels"}
        W.table("language_activity", act, "Activity and influence of each language: how much its channels are forwarded, "
                "compared with how many channels it has.", {k: v for k, v in cols.items() if k in act.columns})
        W.table("language_top_channels", topch, "The 10 most forwarded channels of each of the 12 largest languages.",
                {"language": "code", "language_name": "name", "rank": "rank inside the language", "channel_id": "Telegram channel id",
                 "community": "its Leiden community", "times_forwarded": "times its content was forwarded",
                 "forwards_made": "forwards it made"})

    if not args.no_charts:
        print("charts")
        charts(args.figdir, lang_by_node_series(net, lang_by_node), pur, hom, flow, acc)
        extra_charts(args.figdir, yr, byl, br, act)
        write_readme(args.figdir)
    print("done")
    return {"summary": ag, "purity": pur, "homophily": hom, "inferred": inf, "accuracy": acc, "tables": W.tables,
            "yearly": yr, "yearly_by_language": byl, "bridges": br, "activity": act}


def lang_by_node_series(net, lang_by_node):
    return pd.Series(lang_by_node, index=net.nodes)


# ---------------------------------------------------------------- selftest

def synthetic(seed=0, comms=6, size=500, p_known=0.6, purity=0.88):
    rng = np.random.default_rng(seed)
    langs = ["ru", "en", "ar"]
    n = comms * size
    ids = 1000 + np.arange(n)
    c = np.repeat(np.arange(comms), size)
    main = np.array([langs[i % 3] for i in c])
    lang = np.where(rng.random(n) < purity, main, rng.choice(langs, n))
    lang = np.where(rng.random(n) < p_known, lang, "")
    rows = []
    intra = {2020: 0.95, 2021: 0.85, 2022: 0.70}           # language cohesion decreases over time
    for _ in range(n * 8):
        a = rng.integers(n)
        year = int(rng.choice([2020, 2021, 2022]))
        if rng.random() < intra[year]:
            b = c[a] * size + rng.integers(size)
        else:
            b = rng.integers(n)
        if a != b:
            rows.append((ids[a], ids[b], f"{year}-03", 1 + int(rng.integers(3))))
    return ids, c, lang, pd.DataFrame(rows, columns=["origin_channel", "dest_channel", "month", "n_forwards"])


def selftest(_args):
    ids, c, lang, ed = synthetic()
    with tempfile.TemporaryDirectory() as t:
        t = Path(t)
        (t / "gold" / "edges_monthly_csv").mkdir(parents=True)
        (t / "gold" / "channel_stats_csv").mkdir(parents=True)
        ed.to_csv(t / "gold" / "edges_monthly_csv" / "p.csv", index=False)
        pd.DataFrame({"channel_id": ids, "n_messages": np.random.default_rng(1).integers(1, 500, len(ids))}).to_csv(
            t / "gold" / "channel_stats_csv" / "s.csv", index=False)
        pd.DataFrame({"channel_id": ids, "community": c}).to_csv(t / "c.csv", index=False)
        pd.DataFrame({"File Names": [f"{i}.jsonl" for i in ids], "detected_language": lang}).to_csv(t / "l.csv", sep="\t")
        a = argparse.Namespace(communities=str(t / "c.csv"), languages=str(t / "l.csv"), gold=str(t / "gold"),
                               out=str(t / "out"), figdir=str(t / "fig"), min_weight=1, top_flows=15, min_class=50,
                               min_vote=0.6, seed=42, skip_inference=False, no_charts=False,
                               skip_yearly=False, min_year_forwards=1000, skip_bridges=False, bridges_top=30, bridges_min_forwards=5,
                               skip_activity=False, stats_id_col=None, stats_msg_col=None)
        r = analyse(a)
        s = r["summary"]
        assert 0.8 < s["weighted_purity"] <= 1, s
        assert s["NMI"] > 0.3, s
        assert s["forwards_lift"] > 1.2 and s["forwards_assortativity"] > 0.2, s
        acc = r["accuracy"]
        assert acc.accuracy.iloc[-1] > acc.baseline_majority_language.iloc[0] + 0.2, acc
        assert (r["inferred"].source == "inferred").all() and len(r["inferred"]) > 0
        known = set(ids[lang != ""])
        assert not (set(r["inferred"].channel_id) & known), "inference must only cover unlabelled channels"
        for name in r["tables"]:
            assert (t / "out" / name / f"{name}.csv").exists() and (t / "out" / name / "README.md").exists()
        for f in ("language_distribution", "community_purity", "language_homophily",
                  "language_flows_heatmap", "language_inference_accuracy"):
            assert (t / "fig" / f"{f}.png").exists(), f
        yr = r["yearly"]
        assert list(yr.year) == [2020, 2021, 2022], yr
        assert yr.assortativity.iloc[0] > yr.assortativity.iloc[-1] + 0.05, yr[["year", "assortativity"]]
        assert (r["yearly_by_language"].language.nunique()) == 3
        br = r["bridges"]
        assert set(br.direction) == {"exports", "imports"} and (br.forwards_across_languages > 0).all()
        assert (br.cross_share <= 1).all()
        act = r["activity"]
        assert "messages" in act.columns and act.channels.sum() == (lang != "").sum()
        assert abs(act.share_of_channels.sum() - 1) < 0.01
        assert "audience_effective_languages" in r["homophily"].columns
        assert "effective_languages" in s
        for f in ("language_yearly_homophily", "language_yearly_diversity", "language_yearly_shares",
                  "language_yearly_cohesion", "language_bridges", "language_activity"):
            assert (t / "fig" / f"{f}.png").exists(), f
        assert (t / "fig" / "README.md").exists()
        print(s)
    print("selftest OK")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--communities", default="bigdata_pipeline/analysis/communities_v2/communities_leiden/communities_leiden.csv")
    ap.add_argument("--languages", default="telescope_files/Channel_Language.csv")
    ap.add_argument("--gold", default="telescope_pipeline_files/gold")
    ap.add_argument("--out", default="bigdata_pipeline/analysis/language_v2")
    ap.add_argument("--figdir", default="bigdata_pipeline/analysis/figures/language_communities")
    ap.add_argument("--min-weight", type=int, default=1, help="same value as the theme 1 run")
    ap.add_argument("--top-flows", type=int, default=30)
    ap.add_argument("--min-class", type=int, default=50, help="inference only votes for languages with this many channels")
    ap.add_argument("--min-vote", type=float, default=0.6, help="winning share of neighbour votes required to infer a language")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--skip-inference", action="store_true")
    ap.add_argument("--skip-yearly", action="store_true", help="skip the year-by-year tables and charts")
    ap.add_argument("--min-year-forwards", type=int, default=5000,
                    help="a year needs this many forwards between known-language channels to be reported")
    ap.add_argument("--skip-bridges", action="store_true")
    ap.add_argument("--bridges-top", type=int, default=30, help="channels listed per direction")
    ap.add_argument("--bridges-min-forwards", type=int, default=50,
                    help="a channel needs this many forwards with known-language channels to be ranked")
    ap.add_argument("--skip-activity", action="store_true")
    ap.add_argument("--stats-id-col", default=None, help="channel id column of gold/channel_stats if not recognised")
    ap.add_argument("--stats-msg-col", default=None, help="message count column of gold/channel_stats if not recognised")
    ap.add_argument("--no-charts", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest(args)
    analyse(args)


if __name__ == "__main__":
    main()