r"""
Language-community analysis (project subject 2).

    "Analysis of the distribution between the different language communities
     and modification of the structure depending on the language."

This script answers two questions on the Channel-to-Channel graph:

  (a) DISTRIBUTION - how are channels spread across languages, and how far do
      the Leiden communities follow language?
  (b) STRUCTURE    - does the shape of the network (density, reciprocity,
      clustering, hubs, cross-language links) change from one language to
      another?

Steps (each result is a CSV in its own folder, with a README, like the other
scripts of the project):

  1. channel_language/                  channel -> language (+ where it comes from)
  2. language_distribution/             channels per language
     community_language_purity/         purity / entropy of every community
     language_community_contingency/    language x community counts
     language_community_agreement/      NMI, ARI, homogeneity, completeness
  3. language_mixing_matrix/            language -> language edge counts
     language_homophily/                per-language homophily + global assortativity
     language_graph_structure/          per-language sub-graph statistics

Input (all under BASE_DIR, see config.py):
  - channel_to_channel_graph.csv         columns msg_source_ch, msg_dest_ch
  - communities/communities.csv          (from community_detection.py)
  - Channel_Language.csv                 tab-separated, "File Names" + "detected_language"
  - Source_Channel_Metadata.csv          optional, only with --enrich-titles

Usage:
    python language_analysis.py --selftest          # synthetic data, no input needed
    python language_analysis.py                     # full run
    python language_analysis.py --enrich-titles     # also fill gaps with langdetect
    python language_analysis.py --min-nodes 200 --top-langs 25

Requires: pandas numpy scipy scikit-learn matplotlib
          igraph (recommended, fast clustering coefficient; falls back to
          networkx, which is slow on very large languages)
          langdetect (only for --enrich-titles)
"""

import argparse
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import sparse
from scipy.sparse.csgraph import connected_components
from sklearn.metrics import (
    adjusted_rand_score,
    homogeneity_completeness_v_measure,
    normalized_mutual_info_score,
)

PROGRAM_NAME = "language_analysis"
NULL_LANG_VALUES = {"", "nan", "none", "null", "unknown", "nat"}
OTHER = "other"

LANG_NAMES = {
    "ru": "Russian", "en": "English", "es": "Spanish", "fr": "French",
    "de": "German", "it": "Italian", "pt": "Portuguese", "tr": "Turkish",
    "ar": "Arabic", "fa": "Persian", "zh": "Chinese", "ja": "Japanese",
    "ko": "Korean", "hi": "Hindi", "id": "Indonesian", "uk": "Ukrainian",
    "pl": "Polish", "nl": "Dutch", "vi": "Vietnamese", "th": "Thai",
    "he": "Hebrew", "ha": "Hausa", "yo": "Yoruba", "ig": "Igbo",
    "am": "Amharic", "sw": "Swahili", "bg": "Bulgarian", "et": "Estonian",
    "ro": "Romanian", "el": "Greek", "sv": "Swedish", "da": "Danish",
    "fi": "Finnish", "no": "Norwegian", "cs": "Czech", "sk": "Slovak",
    "hu": "Hungarian", "sr": "Serbian", "hr": "Croatian", "lt": "Lithuanian",
    "lv": "Latvian", "ka": "Georgian", "az": "Azerbaijani", "kk": "Kazakh",
    "uz": "Uzbek", "ur": "Urdu", "bn": "Bengali", "ta": "Tamil",
    "ml": "Malayalam", "my": "Burmese", "km": "Khmer", "lo": "Lao",
    "mn": "Mongolian", "si": "Sinhala", "ps": "Pashto", "ku": "Kurdish",
}


def lang_name(code):
    return LANG_NAMES.get(code, str(code).upper())


# ============================================================
# EXPORT HELPER (same convention as the other scripts)
# ============================================================

def export_csv_with_readme(df, base_dir, name, title, description_lines):
    """Write base_dir/<name>/<name>.csv and base_dir/<name>/README.md."""
    folder = Path(base_dir) / name
    folder.mkdir(parents=True, exist_ok=True)
    csv_path = folder / f"{name}.csv"
    df.to_csv(csv_path, index=False)

    lines = [f"# {title}", ""] + list(description_lines) + [
        "",
        "## File",
        f"- `{csv_path.name}` — {len(df):,} rows, {len(df.columns)} columns.",
        "",
        "## Columns",
    ]
    for col in df.columns:
        example = df[col].iloc[0] if len(df) else ""
        lines.append(f"- `{col}` ({df[col].dtype}) — e.g. `{example}`")
    lines.append("")
    (folder / "README.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"   -> {csv_path}  ({len(df):,} rows)")
    return df


# ============================================================
# 1. LOAD DATA
# ============================================================

def load_edges(edgelist_path, chunk_size=500_000):
    """
    Read the edge list and return (edges, channel_ids):
      edges        DataFrame with int columns s, d (distinct, no self-loops)
      channel_ids  array of channel id strings; position = node index
    """
    print("[1/6] Loading edges...")
    src_parts, dst_parts, total = [], [], 0
    for chunk in pd.read_csv(
        edgelist_path,
        usecols=["msg_source_ch", "msg_dest_ch"],
        dtype={"msg_source_ch": str, "msg_dest_ch": str},
        chunksize=chunk_size,
    ):
        src_parts.append(chunk["msg_source_ch"].to_numpy())
        dst_parts.append(chunk["msg_dest_ch"].to_numpy())
        total += len(chunk)
        print(f"   -> rows read: {total:,}", end="\r")
    print()
    src = np.concatenate(src_parts)
    dst = np.concatenate(dst_parts)
    codes, uniques = pd.factorize(np.concatenate([src, dst]))
    n = len(src)
    edges = pd.DataFrame({"s": codes[:n], "d": codes[n:]})
    edges = edges[edges["s"] != edges["d"]].drop_duplicates().reset_index(drop=True)
    print(f"   -> nodes: {len(uniques):,}   distinct directed edges: {len(edges):,}")
    return edges, np.asarray(uniques)


def load_declared_languages(language_path):
    """Channel_Language.csv (tab-separated) -> {channel_id: language_code}."""
    df = pd.read_csv(language_path, sep="\t", dtype=str, index_col=0)
    df.columns = [c.strip() for c in df.columns]
    id_col, lang_col = "File Names", "detected_language"
    if id_col not in df.columns or lang_col not in df.columns:
        raise SystemExit(f"Expected columns {id_col!r} and {lang_col!r}, got {list(df.columns)}")
    out = {}
    for cid, lang in zip(df[id_col], df[lang_col]):
        if pd.isna(lang):
            continue
        lang = str(lang).strip()
        if lang.lower() in NULL_LANG_VALUES:
            continue
        out[str(cid).strip()] = lang
    return out


def build_channel_language(channel_ids, declared, titles_path=None, enrich=False):
    """
    One row per channel of the graph: channel_id, language, source.
      source = 'dataset'  language given by Channel_Language.csv
               'title'    detected from the channel title (langdetect)
               'unknown'  no language (language is empty)
    """
    print("[2/6] Building the channel -> language table...")
    lang_map = dict(declared)
    title_added = set()
    if enrich:
        try:
            # Reuse the exact enrichment of community_detection.py so that the
            # languages match the names already given to the communities.
            from community_detection import (
                enrich_language_map_from_titles,
                load_source_metadata_titles,
            )
        except ImportError as exc:
            print(f"   -> cannot import community_detection ({exc}); enrichment skipped")
        else:
            titles = load_source_metadata_titles(titles_path)
            before = set(lang_map)
            lang_map, _ = enrich_language_map_from_titles(lang_map, titles)
            title_added = set(lang_map) - before

    languages, sources = [], []
    for cid in channel_ids:
        if cid in declared:
            languages.append(declared[cid]); sources.append("dataset")
        elif cid in title_added:
            languages.append(lang_map[cid]); sources.append("title")
        else:
            languages.append(""); sources.append("unknown")
    df = pd.DataFrame({"channel_id": channel_ids, "language": languages, "source": sources})
    known = (df["source"] != "unknown").mean()
    print(f"   -> language known for {known:.1%} of the {len(df):,} graph channels "
          f"(dataset: {(df['source'] == 'dataset').sum():,}, "
          f"title: {(df['source'] == 'title').sum():,})")
    return df


# ============================================================
# 2. DISTRIBUTION
# ============================================================

def language_distribution(ch):
    """Channels per language, over the whole graph."""
    n_total = len(ch)
    known = ch[ch["language"] != ""]
    out = (known.groupby("language").size().rename("n_channels").reset_index()
           .sort_values("n_channels", ascending=False).reset_index(drop=True))
    out["language_name"] = out["language"].map(lang_name)
    out["share_of_known"] = out["n_channels"] / max(len(known), 1)
    out["share_of_all"] = out["n_channels"] / n_total
    out["rank"] = np.arange(1, len(out) + 1)
    return out[["rank", "language", "language_name", "n_channels",
                "share_of_known", "share_of_all"]]


def community_language_purity(ch, comm):
    """
    Per community: dominant language, purity (share of the dominant language
    among channels with a known language) and Shannon entropy in bits.
    effective_languages = 2**entropy = how many equally-sized languages the
    community is 'equivalent' to (1 = pure, higher = mixed).
    """
    df = ch.merge(comm, on="channel_id", how="inner")
    rows = []
    for cid, g in df.groupby("community_id"):
        known = g.loc[g["language"] != "", "language"]
        row = {"community_id": cid, "size": len(g), "n_known": len(known)}
        if len(known) == 0:
            row.update(dominant_language="", purity=np.nan, entropy_bits=np.nan,
                       effective_languages=np.nan)
        else:
            p = known.value_counts(normalize=True)
            ent = float(-(p * np.log2(p)).sum())
            row.update(dominant_language=p.index[0], purity=float(p.iloc[0]),
                       entropy_bits=ent, effective_languages=float(2 ** ent))
        rows.append(row)
    out = pd.DataFrame(rows).sort_values("size", ascending=False).reset_index(drop=True)
    out["dominant_language_name"] = out["dominant_language"].map(
        lambda c: lang_name(c) if c else "")
    out["known_share"] = out["n_known"] / out["size"]
    return out[["community_id", "size", "n_known", "known_share", "dominant_language",
                "dominant_language_name", "purity", "entropy_bits", "effective_languages"]]


def language_community_contingency(ch, comm, min_count=1):
    df = ch.merge(comm, on="channel_id", how="inner")
    df = df[df["language"] != ""]
    out = (df.groupby(["language", "community_id"]).size().rename("n_channels")
           .reset_index())
    out = out[out["n_channels"] >= min_count]
    out["language_name"] = out["language"].map(lang_name)
    return (out.sort_values("n_channels", ascending=False)
            [["language", "language_name", "community_id", "n_channels"]]
            .reset_index(drop=True))


def language_community_agreement(ch, comm):
    """
    Agreement between 'partition by language' and 'partition by community',
    computed on channels that have BOTH a language and a community.

      homogeneity   1 = every community contains a single language
      completeness  1 = every language sits entirely in one community
      NMI / ARI     symmetric agreement (0 = independent, 1 = identical)
    """
    df = ch.merge(comm, on="channel_id", how="inner")
    df = df[df["language"] != ""]
    if df.empty:
        return pd.DataFrame([{"n_channels": 0}])
    lang_codes = pd.factorize(df["language"])[0]
    comm_codes = pd.factorize(df["community_id"])[0]
    hom, comp, v = homogeneity_completeness_v_measure(lang_codes, comm_codes)
    return pd.DataFrame([{
        "n_channels": len(df),
        "n_languages": int(lang_codes.max() + 1),
        "n_communities": int(comm_codes.max() + 1),
        "nmi": normalized_mutual_info_score(lang_codes, comm_codes),
        "ari": adjusted_rand_score(lang_codes, comm_codes),
        "homogeneity": hom,
        "completeness": comp,
        "v_measure": v,
    }])


# ============================================================
# 3. STRUCTURE BY LANGUAGE
# ============================================================

def top_language_codes(ch, top_n):
    counts = ch.loc[ch["language"] != "", "language"].value_counts()
    return list(counts.index[:top_n])


def language_mixing(edges, node_lang, languages, top_n_langs):
    """
    node_lang: array of language code per node ('' = unknown).
    Returns (mixing, homophily, assortativity) for edges whose two ends both
    have a known language. Languages outside the top N are grouped as 'other'.

      mixing      source_language, dest_language, n_edges, share_of_source,
                  expected_share (dest language's share of all edge ends,
                  i.e. what random mixing would give), ratio = observed / expected
      homophily   per language: share of its outgoing edges that stay in the
                  language, expected share, ratio (>1 = more inward than chance)
      assortativity  Newman's attribute assortativity coefficient, one number:
                  0 = language plays no role in who links to whom, 1 = all
                  edges stay within a language
    """
    keep = set(languages[:top_n_langs])
    lab = np.array([l if l in keep else (OTHER if l else "") for l in node_lang], dtype=object)
    ls, ld = lab[edges["s"].to_numpy()], lab[edges["d"].to_numpy()]
    both = (ls != "") & (ld != "")
    e = pd.DataFrame({"source_language": ls[both], "dest_language": ld[both]})
    total = len(e)
    n_known_edges_share = total / max(len(edges), 1)

    mix = (e.groupby(["source_language", "dest_language"]).size()
           .rename("n_edges").reset_index())
    out_tot = mix.groupby("source_language")["n_edges"].transform("sum")
    in_share = e["dest_language"].value_counts(normalize=True)
    mix["share_of_source"] = mix["n_edges"] / out_tot
    mix["expected_share"] = mix["dest_language"].map(in_share)
    mix["ratio"] = mix["share_of_source"] / mix["expected_share"]
    mix["source_name"] = mix["source_language"].map(lambda c: c if c == OTHER else lang_name(c))
    mix["dest_name"] = mix["dest_language"].map(lambda c: c if c == OTHER else lang_name(c))
    mix = mix.sort_values("n_edges", ascending=False).reset_index(drop=True)

    intra = mix[mix["source_language"] == mix["dest_language"]].set_index("source_language")
    hom = pd.DataFrame({"language": sorted(set(mix["source_language"]))})
    hom["n_out_edges"] = hom["language"].map(mix.groupby("source_language")["n_edges"].sum())
    hom["intra_share"] = hom["language"].map(intra["share_of_source"]).fillna(0.0)
    hom["expected_intra_share"] = hom["language"].map(in_share).fillna(0.0)
    hom["homophily_ratio"] = hom["intra_share"] / hom["expected_intra_share"].replace(0, np.nan)
    hom["language_name"] = hom["language"].map(lambda c: c if c == OTHER else lang_name(c))
    hom = hom.sort_values("n_out_edges", ascending=False).reset_index(drop=True)

    # Newman assortativity on the directed mixing matrix
    labels = sorted(set(e["source_language"]) | set(e["dest_language"]))
    idx = {l: i for i, l in enumerate(labels)}
    M = np.zeros((len(labels), len(labels)))
    for a, b, n in zip(mix["source_language"], mix["dest_language"], mix["n_edges"]):
        M[idx[a], idx[b]] = n
    M /= M.sum() if M.sum() else 1
    ai, bi = M.sum(axis=1), M.sum(axis=0)
    denom = 1 - float((ai * bi).sum())
    assort = (float(np.trace(M)) - float((ai * bi).sum())) / denom if denom > 0 else np.nan
    glob = pd.DataFrame([{
        "n_edges_both_known": total,
        "share_of_edges_both_known": n_known_edges_share,
        "intra_language_edge_share": float(np.trace(M)),
        "assortativity_by_language": assort,
    }])
    return mix, hom, glob


def _transitivity(n, s, d):
    """Global clustering coefficient of the undirected simple graph."""
    try:
        import igraph as ig
        g = ig.Graph(n=n, edges=list(zip(s.tolist(), d.tolist())), directed=False)
        g = g.simplify()
        return float(g.transitivity_undirected(mode="zero"))
    except ImportError:
        import networkx as nx
        G = nx.Graph()
        G.add_nodes_from(range(n))
        G.add_edges_from(zip(s.tolist(), d.tolist()))
        return float(nx.transitivity(G))


def language_graph_structure(edges, node_lang, languages, min_nodes, skip_clustering=False):
    """
    One row per language with at least `min_nodes` channels: statistics of the
    sub-graph induced by the channels of that language (edges with both ends
    in the language).
    """
    rows = []
    s_all, d_all = edges["s"].to_numpy(), edges["d"].to_numpy()
    for lang in languages:
        nodes = np.flatnonzero(node_lang == lang)
        if len(nodes) < min_nodes:
            continue
        local = -np.ones(len(node_lang), dtype=np.int64)
        local[nodes] = np.arange(len(nodes))
        s, d = local[s_all], local[d_all]
        m = (s >= 0) & (d >= 0)
        s, d = s[m], d[m]
        n, ne = len(nodes), len(s)

        row = {"language": lang, "language_name": lang_name(lang),
               "n_channels": n, "n_edges": ne}
        if ne == 0:
            rows.append(row)
            continue
        A = sparse.coo_matrix((np.ones(ne), (s, d)), shape=(n, n)).tocsr()
        row["density"] = ne / (n * (n - 1)) if n > 1 else np.nan
        row["reciprocity"] = float(A.multiply(A.T).sum() / ne)
        und = ((A + A.T) > 0).astype(np.int8)
        deg = np.asarray(und.sum(axis=1)).ravel()
        row["mean_degree"] = float(deg.mean())
        row["median_degree"] = float(np.median(deg))
        row["max_degree"] = int(deg.max())
        row["isolated_share"] = float((deg == 0).mean())
        k = max(1, int(round(0.01 * n)))
        row["top1pct_degree_share"] = float(np.sort(deg)[::-1][:k].sum() / max(deg.sum(), 1))
        _, lab = connected_components(und, directed=False)
        row["giant_component_share"] = float(np.bincount(lab).max() / n)
        row["n_components"] = int(lab.max() + 1)
        row["clustering"] = np.nan if skip_clustering else _transitivity(n, s, d)

        # cross-language exposure: edges leaving / entering the language
        out_edges = (node_lang[s_all] == lang) & (node_lang[d_all] != lang) & (node_lang[d_all] != "")
        in_edges = (node_lang[d_all] == lang) & (node_lang[s_all] != lang) & (node_lang[s_all] != "")
        row["out_to_other_language"] = int(out_edges.sum())
        row["in_from_other_language"] = int(in_edges.sum())
        rows.append(row)
        print(f"   -> {lang}: {n:,} channels, {ne:,} internal edges")
    return pd.DataFrame(rows)


# ============================================================
# CHARTS
# ============================================================

COLORS = ["#2E5395", "#5B8DD9", "#85B09A", "#E8A33D", "#C0392B",
          "#8E44AD", "#16A085", "#D35400", "#2C3E50", "#7F8C8D"]


def make_charts(charts_dir, dist, purity, mix, hom, struct=None, agree=None, glob=None):
    """All chart text is in English, same look as the other project scripts."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    charts_dir = Path(charts_dir)
    charts_dir.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({
        "font.family": "serif", "font.size": 11, "axes.titlesize": 13,
        "axes.labelsize": 12, "figure.dpi": 150, "savefig.dpi": 150,
        "savefig.bbox": "tight",
    })

    def save(fig, name):
        fig.savefig(charts_dir / name)
        plt.close(fig)

    top = dist.head(15)
    fig, ax = plt.subplots(figsize=(8, 5.5))
    ax.barh(top["language_name"][::-1], top["n_channels"][::-1], color=COLORS[0])
    ax.set_xscale("log")
    ax.set_xlabel("Number of channels (log scale)")
    ax.set_title("Channels per language (top 15)")
    save(fig, "language_distribution.png")

    p = purity["purity"].dropna()
    if len(p):
        w = purity.loc[p.index, "size"]
        fig, ax = plt.subplots(figsize=(7, 4.5))
        ax.hist(p, bins=20, weights=w, color=COLORS[2], edgecolor="white")
        ax.set_yscale("log")
        ax.set_xlabel("Community purity (share of the dominant language)")
        ax.set_ylabel("Channels (log scale)")
        title = "Do communities follow language?"
        if agree is not None and len(agree) and "nmi" in agree.columns:
            title += f"  (NMI = {agree['nmi'].iloc[0]:.2f})"
        ax.set_title(title)
        save(fig, "community_purity_hist.png")

    if len(mix):
        labs = list(hom["language"].head(12))
        mat = (mix[mix["source_language"].isin(labs) & mix["dest_language"].isin(labs)]
               .pivot(index="source_language", columns="dest_language", values="share_of_source")
               .reindex(index=labs, columns=labs).fillna(0))
        names = [c if c == OTHER else lang_name(c) for c in labs]
        fig, ax = plt.subplots(figsize=(8, 6.5))
        im = ax.imshow(mat.to_numpy(), cmap="Blues", vmin=0, vmax=1)
        ax.set_xticks(range(len(labs))); ax.set_xticklabels(names, rotation=60, ha="right")
        ax.set_yticks(range(len(labs))); ax.set_yticklabels(names)
        ax.set_xlabel("Destination language"); ax.set_ylabel("Source language")
        ax.set_title("Where do the edges of each language go?\n(each row sums to 100%)")
        fig.colorbar(im, ax=ax, shrink=0.8, label="Share of outgoing edges")
        save(fig, "language_mixing_matrix.png")

    h = hom[hom["language"] != OTHER].head(15).dropna(subset=["homophily_ratio"])
    if len(h):
        fig, ax = plt.subplots(figsize=(8, 5.5))
        y = list(range(len(h)))[::-1]
        ax.hlines(y, 1, h["homophily_ratio"], color=COLORS[3], lw=3)
        ax.scatter(h["homophily_ratio"], y, color=COLORS[3], s=60, zorder=3)
        ax.set_yticks(y); ax.set_yticklabels(h["language_name"])
        ax.axvline(1, color="#555555", ls="--", lw=1)
        ax.set_xscale("log")
        ax.set_xlabel("Homophily ratio = observed / expected share of edges staying in the language")
        title = "Language homophily (right of the dashed line = more inward than chance)"
        ax.set_title(title, fontsize=11)
        save(fig, "language_homophily.png")

    if struct is not None and len(struct) and "reciprocity" in struct.columns:
        s = struct.sort_values("n_channels", ascending=False).head(12).reset_index(drop=True)
        panels = [("reciprocity", "Reciprocity"), ("clustering", "Clustering coefficient"),
                  ("giant_component_share", "Giant component share"),
                  ("top1pct_degree_share", "Degree share of the top 1% channels")]
        fig, axes = plt.subplots(2, 2, figsize=(11, 8))
        for ax, (col, label), color in zip(axes.ravel(), panels, COLORS):
            if col not in s.columns or s[col].isna().all():
                ax.axis("off"); continue
            ax.bar(s["language_name"], s[col], color=color)
            ax.set_title(label)
            ax.tick_params(axis="x", rotation=60)
            for t in ax.get_xticklabels():
                t.set_ha("right")
        fig.suptitle("Network structure by language (12 largest languages)", fontsize=14)
        fig.tight_layout()
        save(fig, "language_graph_structure.png")

    (charts_dir / "README.md").write_text(
        "# Charts - language analysis\n\n"
        "All outputs produced by `language_analysis.py` (matplotlib PNG, English labels).\n\n"
        "- `language_distribution.png` - channels per language (top 15, log scale).\n"
        "- `community_purity_hist.png` - purity of communities weighted by size, with the "
        "NMI between language and community partitions in the title.\n"
        "- `language_mixing_matrix.png` - share of each language's outgoing edges going to "
        "each language (each row sums to 1).\n"
        "- `language_homophily.png` - observed / expected share of edges that stay inside "
        "the language (above 1 = more inward than chance).\n"
        "- `language_graph_structure.png` - reciprocity, clustering, giant component and hub "
        "concentration of the sub-graph of each language.\n", encoding="utf-8")
    print(f"   -> charts in {charts_dir}")


# ============================================================
# PIPELINE
# ============================================================

def run(base_dir, edgelist, communities_path, language_path, titles_path,
        enrich=False, top_langs=20, min_nodes=100, skip_clustering=False, charts=True):
    base_dir = Path(base_dir)
    edges, channel_ids = load_edges(edgelist)
    declared = load_declared_languages(language_path)
    ch = build_channel_language(channel_ids, declared, titles_path, enrich)
    comm = pd.read_csv(communities_path, dtype={"channel_id": str})

    print("[3/6] Exporting the language table...")
    export_csv_with_readme(
        ch, base_dir, "channel_language", "Channel -> language",
        ["One row per channel of the Channel-to-Channel graph.", "",
         "- `language`: ISO-like language code; empty when unknown.",
         "- `source`: `dataset` (Channel_Language.csv), `title` (langdetect on the "
         "channel title, only with `--enrich-titles`) or `unknown`.", "",
         "Generated by `code/language_analysis.py`."])

    print("[4/6] Distribution...")
    dist = language_distribution(ch)
    export_csv_with_readme(
        dist, base_dir, "language_distribution", "Channels per language",
        ["Number of graph channels per language, over channels with a known language.", "",
         "`share_of_known` is relative to channels with a known language, "
         "`share_of_all` to every channel of the graph (unknown included).", "",
         "Generated by `code/language_analysis.py`."])
    purity = community_language_purity(ch, comm)
    export_csv_with_readme(
        purity, base_dir, "community_language_purity", "Language purity of each community",
        ["One row per community.", "",
         "- `purity`: share of the dominant language among channels with a known language.",
         "- `entropy_bits`: Shannon entropy of the language mix (0 = single language).",
         "- `effective_languages`: 2^entropy, the number of equally sized languages "
         "the community is equivalent to (1 = pure).",
         "- `known_share`: share of the community's channels with a known language; "
         "low values make purity unreliable.", "",
         "Generated by `code/language_analysis.py`."])
    export_csv_with_readme(
        language_community_contingency(ch, comm), base_dir,
        "language_community_contingency", "Language x community counts",
        ["Number of channels for every (language, community) pair with at least one "
         "channel. Sorted by count.", "",
         "Generated by `code/language_analysis.py`."])
    agree = language_community_agreement(ch, comm)
    export_csv_with_readme(
        agree, base_dir, "language_community_agreement",
        "Agreement between language and community partitions",
        ["Computed on channels that have both a language and a community.", "",
         "- `homogeneity`: 1 if every community holds a single language.",
         "- `completeness`: 1 if every language falls entirely in one community.",
         "- `nmi`, `ari`: symmetric agreement, 0 = independent, 1 = identical.", "",
         "Generated by `code/language_analysis.py`."])

    print("[5/6] Structure by language...")
    node_lang = ch["language"].to_numpy(dtype=object)
    order = top_language_codes(ch, top_langs)
    mix, hom, glob = language_mixing(edges, node_lang, order, top_langs)
    export_csv_with_readme(
        mix, base_dir, "language_mixing_matrix", "Language -> language edges",
        ["Directed edges (source channel -> destination channel) whose two ends have "
         f"a known language. Languages outside the top {top_langs} are grouped as `other`.", "",
         "- `share_of_source`: share of the source language's outgoing edges.",
         "- `expected_share`: share of the destination language among all edges "
         "(what random mixing would give).",
         "- `ratio`: observed / expected; above 1 the link is more frequent than chance.", "",
         "Generated by `code/language_analysis.py`."])
    export_csv_with_readme(
        hom, base_dir, "language_homophily", "Homophily by language",
        ["For each source language: share of outgoing edges staying in the same "
         "language (`intra_share`), the share expected by chance, and their ratio.", "",
         "Generated by `code/language_analysis.py`."])
    export_csv_with_readme(
        glob, base_dir, "language_assortativity", "Global language assortativity",
        ["One row. `assortativity_by_language` is Newman's attribute assortativity: "
         "0 = language plays no role in who links to whom, 1 = every edge stays "
         "inside a language.", "",
         "`share_of_edges_both_known` tells how much of the graph this is based on.", "",
         "Generated by `code/language_analysis.py`."])
    struct = language_graph_structure(edges, node_lang, order, min_nodes, skip_clustering)
    export_csv_with_readme(
        struct, base_dir, "language_graph_structure", "Sub-graph statistics per language",
        [f"Statistics of the sub-graph induced by the channels of each language with at "
         f"least {min_nodes} channels (edges with both ends in that language).", "",
         "- `density`, `reciprocity`, `clustering` (global transitivity, undirected).",
         "- `mean_degree` / `median_degree` / `max_degree`: undirected degree inside the language.",
         "- `top1pct_degree_share`: share of degree held by the 1% best connected channels "
         "(hub concentration).",
         "- `giant_component_share`: share of channels in the largest weakly connected component.",
         "- `out_to_other_language` / `in_from_other_language`: edges linking the language "
         "to a channel of another known language.", "",
         "Generated by `code/language_analysis.py`."])

    print("[6/6] Charts...")
    if charts:
        make_charts(base_dir / "charts" / PROGRAM_NAME, dist, purity, mix, hom,
                    struct, agree, glob)

    print("\nGlobal results")
    print(agree.round(3).to_string(index=False))
    print(glob.round(3).to_string(index=False))
    return {"dist": dist, "purity": purity, "agree": agree, "mix": mix,
            "hom": hom, "glob": glob, "struct": struct, "channel_language": ch}


# ============================================================
# SELF-TEST (synthetic data, no dataset needed)
# ============================================================

def make_synthetic(root, n_per_lang=300, seed=0):
    """
    Three languages (ru, en, ar) with strong inward linking, plus a few
    cross-language edges. Communities = languages, except one mixed community.
    """
    rng = np.random.default_rng(seed)
    langs = ["ru", "en", "ar"]
    ids, lang_of = [], {}
    for li, lg in enumerate(langs):
        for i in range(n_per_lang):
            cid = str(1000 * (li + 1) + i)
            ids.append(cid); lang_of[cid] = lg
    # 10 channels without a language
    unk = [str(9000 + i) for i in range(10)]
    ids += unk

    rows = []
    for li, lg in enumerate(langs):
        members = [c for c in ids if lang_of.get(c) == lg]
        for c in members:
            for t in rng.choice(members, size=6, replace=False):
                if t != c:
                    rows.append((c, t))
            if rng.random() < 0.04:                      # rare cross-language edge
                rows.append((c, str(rng.choice([x for x in ids if lang_of.get(x) not in (lg, None)]))))
    for u in unk:
        rows.append((u, ids[0]))
    root = Path(root)
    pd.DataFrame(rows, columns=["msg_source_ch", "msg_dest_ch"]).to_csv(
        root / "channel_to_channel_graph.csv", index=False)

    lang_df = pd.DataFrame({"File Names": list(lang_of), "detected_language": list(lang_of.values())})
    lang_df.to_csv(root / "Channel_Language.csv", sep="\t")

    comm = []
    for c in ids:
        lg = lang_of.get(c)
        comm.append((c, {"ru": 0, "en": 1, "ar": 2}.get(lg, 3)))
    (root / "communities").mkdir(exist_ok=True)
    pd.DataFrame(comm, columns=["channel_id", "community_id"]).to_csv(
        root / "communities" / "communities.csv", index=False)


def run_selftest():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        make_synthetic(tmp)
        res = run(tmp, tmp / "channel_to_channel_graph.csv",
                  tmp / "communities" / "communities.csv", tmp / "Channel_Language.csv",
                  None, enrich=False, top_langs=5, min_nodes=50, charts=True)
        agree, hom, glob = res["agree"].iloc[0], res["hom"], res["glob"].iloc[0]
        struct = res["struct"]

        assert abs(agree["nmi"] - 1.0) < 1e-9, agree["nmi"]       # communities == languages
        assert agree["homogeneity"] > 0.999 and agree["completeness"] > 0.999
        assert res["purity"].query("community_id != 3")["purity"].min() == 1.0
        assert glob["assortativity_by_language"] > 0.8, glob
        assert (hom["homophily_ratio"] > 2).all(), hom
        assert len(res["dist"]) == 3 and res["dist"]["n_channels"].tolist() == [300, 300, 300]
        assert len(struct) == 3 and (struct["giant_component_share"] > 0.9).all()
        assert (struct["reciprocity"].between(0, 1)).all()
        for name in ("channel_language", "language_distribution", "community_language_purity",
                     "language_community_contingency", "language_community_agreement",
                     "language_mixing_matrix", "language_homophily",
                     "language_assortativity", "language_graph_structure"):
            assert (tmp / name / f"{name}.csv").exists() and (tmp / name / "README.md").exists(), name
        for png in ("language_distribution", "community_purity_hist", "language_mixing_matrix",
                    "language_homophily", "language_graph_structure"):
            assert (tmp / "charts" / PROGRAM_NAME / f"{png}.png").exists(), png
    print("\nSELFTEST OK")


# ============================================================
# MAIN
# ============================================================

def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--selftest", action="store_true", help="run on synthetic data and exit")
    ap.add_argument("--enrich-titles", action="store_true",
                    help="fill missing languages with langdetect on channel titles (slow)")
    ap.add_argument("--top-langs", type=int, default=20,
                    help="languages kept individually in the mixing matrix (others -> 'other')")
    ap.add_argument("--min-nodes", type=int, default=100,
                    help="minimum channels for a language to get a sub-graph row")
    ap.add_argument("--skip-clustering", action="store_true",
                    help="skip the clustering coefficient (the slowest metric)")
    ap.add_argument("--no-charts", action="store_true")
    ap.add_argument("--basedir", type=Path, default=None)
    args = ap.parse_args()

    if args.selftest:
        run_selftest()
        return

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from config import BASE_DIR
    base = args.basedir or BASE_DIR
    comm_path = base / "communities" / "communities.csv"
    if not comm_path.exists():
        comm_path = base / "communities.csv"
    run(base, base / "channel_to_channel_graph.csv", comm_path,
        base / "Channel_Language.csv", base / "Source_Channel_Metadata.csv",
        enrich=args.enrich_titles, top_langs=args.top_langs, min_nodes=args.min_nodes,
        skip_clustering=args.skip_clustering, charts=not args.no_charts)


if __name__ == "__main__":
    main()