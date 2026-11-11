#!/usr/bin/env python3
"""
TeleScope v2 - Theme 3: traceability of forwarded messages up to the original source.

What the data allows
  Telegram keeps ONLY the original author in the header of a forward (channel id, post id, date of the
  original post). A relay therefore points straight to its source; the intermediate hops of a chain
  (A -> B -> C) are not stored. The "chain" of an original post is the list of its relays ordered by time.

The tracing protocol implemented here (written with the measured numbers to tracing_protocol.md)
  1. Read the forward header of every message: origin channel, origin post, origin date.
  2. Classify its traceability level:
       A  forwarded from a channel, post id known       -> traceable to the exact post
       B  forwarded from a channel, post id missing     -> traceable to the channel only
       C  forwarded from a user                         -> source is a person, not traced
       D  origin hidden by Telegram privacy             -> source unknown
  3. For level A, verify the source against the corpus: is the origin channel in the data? is the original
     post in the data? does its date match the date written in the forward header?
  4. Order the relays of each original post by time (rank) and measure the delay to the original.
  5. Report who the sources are (concentration), how far content travels (relays per post) and how fast.

Inputs (from the pipeline)
  --chains  gold/chains   (Parquet written by job2_chains.py)
  --clean   clean         (Parquet written by job1_clean.py; needed for steps 2 and 3, optional)
Outputs: tables (one folder per CSV with its README) in --out, charts in --figdir (images only),
         tracing_protocol.md in --out.

Duplicated relays (same destination channel and message id more than once in chains) are removed before any
count, and their number is reported.

Run (project root):
  python3 bigdata_pipeline/analysis/source_tracing_v2.py \
      --chains telescope_pipeline_files/gold/chains --clean telescope_pipeline_files/clean \
      --languages telescope_files/Channel_Language.csv \
      --out bigdata_pipeline/analysis/tracing_v2 --figdir bigdata_pipeline/analysis/figures/traceability
  python3 bigdata_pipeline/analysis/source_tracing_v2.py --selftest
Needs pandas, numpy, pyarrow, matplotlib. Keep it in the same folder as community_detection_v2.py.
"""
import argparse
import sys
import tempfile
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    import pyarrow  # noqa: F401
    HAS_ARROW = True
except ImportError:
    HAS_ARROW = False

SHIFT = 32
MASK = (1 << SHIFT) - 1
SH, MASK_U = np.uint64(SHIFT), np.uint64(MASK)


def pack(channel, post):
    """(channel id, post id) -> one unsigned 64-bit key. Channel ids can exceed 2**31, hence unsigned."""
    return (channel.astype(np.uint64) << SH) | post.astype(np.uint64)


def hi(key):
    return (key >> SH).astype(np.int64)


def lo(key):
    return (key & MASK_U).astype(np.int64)
DELAY_EDGES = [0, 60, 600, 3600, 86400, 7 * 86400, 30 * 86400]
DELAY_LABELS = ["before the original (negative)", "under 1 min", "1 to 10 min", "10 to 60 min", "1 to 24 h",
                "1 to 7 days", "7 to 30 days", "over 30 days"]
SIZE_EDGES = [2, 3, 6, 11, 51, 101, 1001]
SIZE_LABELS = ["1 relay", "2 relays", "3 to 5", "6 to 10", "11 to 50", "51 to 100", "101 to 1000", "over 1000"]
LEVELS = {"channel_with_post": "A", "channel_without_post": "B", "user": "C", "hidden": "D"}
LEVEL_TEXT = {"A": "forwarded from a channel, original post known (traceable to the post)",
              "B": "forwarded from a channel, original post id missing (traceable to the channel)",
              "C": "forwarded from a user (source is a person)",
              "D": "origin hidden by Telegram privacy (source unknown)"}


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
            f"`source_tracing_v2.py`, run on {date.today().isoformat()}.\n\n{self.context}\n\n"
            f"## Content ({len(df):,} rows)\n\n| Column | Meaning |\n|---|---|\n{cols}\n", encoding="utf-8")
        self.tables.append(name)
        print(f"  wrote {name}/ ({len(df):,} rows)")


# ---------------------------------------------------------------- loading
# Two readers behind the same functions: Parquet (pyarrow, what the pipeline writes) and CSV (fallback, also used
# by the self-test where pyarrow may be missing).

def _is_parquet(path):
    p = Path(path)
    return p.is_file() and p.suffix == ".parquet" or (p.is_dir() and any(p.rglob("*.parquet")))


def _csv_parts(path):
    p = Path(path)
    parts = [p] if p.is_file() else sorted(p.rglob("*.csv"))
    if not parts:
        raise SystemExit(f"nothing to read in {path}: expected Parquet or CSV files")
    return parts


def _arrow():
    try:
        import pyarrow.compute as pc
        import pyarrow.dataset as ds
        return ds, pc
    except ImportError:
        raise SystemExit("pyarrow is required to read Parquet (pip install pyarrow)")


def _np(col, dtype=None):
    a = col.combine_chunks() if hasattr(col, "combine_chunks") else col
    a = a.to_numpy(zero_copy_only=False)
    return a.astype(dtype) if dtype is not None else a


def _epoch(series):
    return (pd.to_datetime(series, format="%Y-%m-%dT%H:%M:%S", utc=True).astype("datetime64[s, UTC]")
            .astype("int64")).to_numpy()


def read_chains_raw(path):
    """Columns of gold/chains as numpy arrays: origin_channel, origin_post, dest_channel, dest_msg, delay, origin_ts, year."""
    if _is_parquet(path):
        ds, pc = _arrow()
        import pyarrow as pa
        d = ds.dataset(str(path), format="parquet")
        t = d.to_table(columns=["origin_channel", "origin_post", "dest_channel", "dest_msg", "delay_s"])
        out = {"oc": _np(t["origin_channel"], np.int64), "op": _np(t["origin_post"], np.int64),
               "dc": _np(t["dest_channel"], np.int64), "dm": _np(t["dest_msg"], np.int64),
               "delay": _np(t["delay_s"], np.int64)}
        del t
        t = d.to_table(columns=["origin_date"])
        out["ots"] = _np(pc.cast(pc.strptime(t["origin_date"], format="%Y-%m-%dT%H:%M:%S", unit="s"), pa.int64()), np.int64)
        del t
        t = d.to_table(columns=["date"])
        out["year"] = _np(pc.cast(pc.utf8_slice_codeunits(t["date"], 0, 4), pa.int16()), np.int16)
        return out
    parts = []
    for f in _csv_parts(path):
        df = pd.read_csv(f, usecols=["origin_channel", "origin_post", "origin_date", "dest_channel", "dest_msg", "date", "delay_s"])
        parts.append(pd.DataFrame({"oc": df.origin_channel.astype("int64"), "op": df.origin_post.astype("int64"),
                                   "dc": df.dest_channel.astype("int64"), "dm": df.dest_msg.astype("int64"),
                                   "delay": df.delay_s.astype("int64"), "ots": _epoch(df.origin_date),
                                   "year": df["date"].str[:4].astype("int16")}))
    df = pd.concat(parts, ignore_index=True)
    return {k: df[k].to_numpy() for k in df.columns}


def load_chains(path):
    """Compact numpy columns of the relays; removes duplicated relays. Returns (dict, raw_rows, duplicates)."""
    r = read_chains_raw(path)
    n_raw = len(r["oc"])
    if max(r["oc"].max(), r["dc"].max()) > MASK or max(r["op"].max(), r["dm"].max()) > MASK or min(r["oc"].min(), r["dc"].min()) < 0:
        raise SystemExit("channel or message ids outside the range 0 to 2**32 - 1: the 64-bit keys used here would collide")
    _, first = np.unique(pack(r["dc"], r["dm"]), return_index=True)
    first.sort()
    dups = n_raw - len(first)
    if dups:
        r = {k: v[first] for k, v in r.items()}
    return {"origin_channel": r["oc"], "origin_post": r["op"], "dest_channel": r["dc"], "delay": r["delay"],
            "origin_ts": r["ots"], "year": r["year"]}, n_raw, dups


def iter_clean(path):
    """Yield batches of the cleaned messages: dest_channel, msg_id, ts, and one boolean mask per traceability level."""
    if _is_parquet(path):
        ds, pc = _arrow()
        d = ds.dataset(str(path), format="parquet", partitioning="hive")

        def mask(b, value):
            return pc.fill_null(pc.equal(b.column("kind"), value), False).to_numpy(zero_copy_only=False).astype(bool)
        for b in d.to_batches(columns=["dest_channel", "msg_id", "ts", "kind", "origin_post"], batch_size=1_000_000):
            ch = mask(b, "channel")
            no_post = b.column("origin_post").is_null().to_numpy(zero_copy_only=False).astype(bool)
            yield (_np(b.column("dest_channel"), np.int64), _np(b.column("msg_id"), np.int64),
                   _np(pc.fill_null(b.column("ts"), 0), np.int64),
                   {"channel_with_post": ch & ~no_post, "channel_without_post": ch & no_post,
                    "user": mask(b, "user"), "hidden": mask(b, "hidden")})
        return
    for f in _csv_parts(path):
        for df in pd.read_csv(f, usecols=["dest_channel", "msg_id", "ts", "kind", "origin_post"], chunksize=1_000_000):
            kind = df.kind.fillna("").astype(str).to_numpy()
            ch = kind == "channel"
            no_post = df.origin_post.isna().to_numpy()
            yield (df.dest_channel.to_numpy(np.int64), df.msg_id.to_numpy(np.int64), df.ts.fillna(0).to_numpy(np.int64),
                   {"channel_with_post": ch & ~no_post, "channel_without_post": ch & no_post,
                    "user": kind == "user", "hidden": kind == "hidden"})


def scan_clean(path, needed):
    """One pass over the cleaned messages: levels by year, channels present, and the original posts found (needed = sorted keys)."""
    found_ts = np.full(len(needed), -1, np.int64)
    levels, chans, total, forwards = {}, [], 0, 0
    for dc, mid, ts, parts in iter_clean(path):
        year = ts.astype("datetime64[s]").astype("datetime64[Y]").astype(np.int64) + 1970
        for name, m in parts.items():
            if m.any():
                ys, cs = np.unique(year[m], return_counts=True)
                for y, c in zip(ys, cs):
                    levels[(int(y), name)] = levels.get((int(y), name), 0) + int(c)
        total += len(dc)
        forwards += int(sum(m.sum() for m in parts.values()))
        chans.append(np.unique(dc))
        if len(needed):
            mk = pack(dc, mid)
            idx = np.minimum(np.searchsorted(needed, mk), len(needed) - 1)
            hit = needed[idx] == mk
            found_ts[idx[hit]] = ts[hit]
    return levels, np.unique(np.concatenate(chans)), found_ts, total, forwards


# ---------------------------------------------------------------- computations

def chain_tables(c, languages=None):
    oc, op, dc, delay = c["origin_channel"], c["origin_post"], c["dest_channel"], c["delay"]
    okey = pack(oc, op)
    uo, first_idx, inv, cnt = np.unique(okey, return_index=True, return_inverse=True, return_counts=True)
    g = pd.DataFrame({"inv": inv, "delay": delay}).groupby("inv")["delay"].agg(["min", "max"])
    first_delay, last_delay = g["min"].to_numpy(), g["max"].to_numpy()
    u_oc, u_op = hi(uo), lo(uo)
    n = len(oc)

    # relays per original post
    sb = np.digitize(cnt, SIZE_EDGES)
    size = pd.DataFrame({"size_class": [SIZE_LABELS[i] for i in range(len(SIZE_LABELS))],
                         "original_posts": np.bincount(sb, minlength=len(SIZE_LABELS)),
                         "relays": np.bincount(sb, weights=cnt, minlength=len(SIZE_LABELS)).astype(np.int64)})
    size["share_of_posts"] = (size.original_posts / len(uo)).round(4)
    size["share_of_relays"] = (size.relays / n).round(4)

    # delays: all relays and first relay of each post
    def dist(x):
        return np.bincount(np.digitize(x, DELAY_EDGES), minlength=len(DELAY_LABELS))
    da, df_ = dist(delay), dist(first_delay)
    dd = pd.DataFrame({"delay_class": DELAY_LABELS, "relays": da, "share_of_relays": (da / n).round(4),
                       "first_relays": df_, "share_of_first_relays": (df_ / len(uo)).round(4)})

    # delays by year of the relay
    yd = pd.DataFrame({"year": c["year"], "delay": delay})
    yd["h1"] = (yd.delay >= 0) & (yd.delay < 3600)
    yd["d1"] = (yd.delay >= 0) & (yd.delay < 86400)
    by_year = yd.groupby("year").agg(relays=("delay", "size"), median_delay_s=("delay", "median"),
                                      share_within_1h=("h1", "mean"), share_within_1day=("d1", "mean")).reset_index()
    by_year["share_within_1h"] = by_year.share_within_1h.round(4)
    by_year["share_within_1day"] = by_year.share_within_1day.round(4)

    # sources
    src = pd.DataFrame({"origin_channel": u_oc, "cnt": cnt}).groupby("origin_channel").agg(
        original_posts=("cnt", "size"), relays=("cnt", "sum")).reset_index()
    up = np.unique(pack(oc, dc))
    uc, n_dest = np.unique(hi(up), return_counts=True)
    src = src.merge(pd.DataFrame({"origin_channel": uc, "relaying_channels": n_dest}), on="origin_channel", how="left")
    src["relays_per_post"] = (src.relays / src.original_posts).round(2)
    src = src.sort_values("relays", ascending=False).reset_index(drop=True)
    src["share_of_relays"] = (src.relays / n).round(5)
    if languages is not None:
        src["language"] = src.origin_channel.map(languages)
    # concentration
    cum = src.relays.cumsum().to_numpy() / n
    conc = []
    for f in (0.001, 0.01, 0.05, 0.10, 0.25, 0.50):
        k = max(1, int(round(f * len(src))))
        conc.append({"top_share_of_sources": f, "sources": k, "share_of_relays": round(float(cum[k - 1]), 4)})
    conc = pd.DataFrame(conc)

    # most relayed original posts
    top = np.argsort(-cnt)[:100]
    posts = pd.DataFrame({"origin_channel": u_oc[top], "origin_post": u_op[top], "relays": cnt[top],
                          "first_relay_delay_s": first_delay[top], "last_relay_delay_s": last_delay[top]})
    summ = {"relays_after_deduplication": n, "original_posts": len(uo), "origin_channels": len(src),
            "relaying_channels": int(np.unique(dc).size), "mean_relays_per_post": round(n / len(uo), 3),
            "median_relays_per_post": float(np.median(cnt)), "max_relays_per_post": int(cnt.max()),
            "posts_with_one_relay_share": round(float((cnt == 1).mean()), 4),
            "median_first_relay_delay_s": float(np.median(first_delay)),
            "relays_within_1h_share": round(float(((delay >= 0) & (delay < 3600)).mean()), 4),
            "relays_before_original": int((delay < 0).sum())}
    return {"size": size, "delays": dd, "by_year": by_year, "sources": src, "concentration": conc, "posts": posts,
            "summary": summ, "uo": uo, "first_idx": first_idx, "cnt": cnt, "u_oc": u_oc}


def availability(c, t, found_ts, channels):
    """Source verification against the corpus, per original post and weighted by relays."""
    uo, cnt, fi, u_oc = t["uo"], t["cnt"], t["first_idx"], t["u_oc"]
    in_corpus = np.isin(u_oc, channels)
    found = found_ts >= 0
    o_ts = c["origin_ts"][fi]
    same = found & (found_ts == o_ts)
    near = found & (np.abs(found_ts - o_ts) <= 60)
    rows = []

    def add(name, m, what):
        rows.append({"measure": name, "original_posts": int(m.sum()), "share_of_posts": round(float(m.mean()), 4),
                     "relays": int(cnt[m].sum()), "share_of_relays": round(float(cnt[m].sum() / cnt.sum()), 4),
                     "meaning": what})
    add("origin_channel_in_corpus", in_corpus, "the source channel has messages in the dataset")
    add("origin_post_found", found, "the original post itself is in the dataset")
    add("origin_post_missing_channel_present", in_corpus & ~found,
        "channel in the dataset but this post is not (deleted, outside the collected period, or never collected)")
    add("origin_channel_not_in_corpus", ~in_corpus, "the source channel was never collected: traceable to its id only")
    add("date_identical", same, "the header date equals the date of the post found")
    add("date_within_60s", near, "the header date is within one minute of the post found")
    add("date_differs", found & ~near, "header date and post date differ by more than one minute (to inspect)")
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- charts (same look as the other themes)

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


def charts(figdir, t, by_level=None, avail=None):
    plt = _setup()
    fd = Path(figdir)
    fd.mkdir(parents=True, exist_ok=True)

    s = t["size"]
    fig, ax = plt.subplots(figsize=(9.5, 5.6))
    ax.bar(range(len(s)), s.original_posts, color="#5B8DD9")
    for x, (v, sh) in enumerate(zip(s.original_posts, s.share_of_posts)):
        ax.text(x, max(v, 1), f"{v:,}\n({sh * 100:.1f}%)", ha="center", va="bottom", fontsize=7)
    ax.set_yscale("log"); ax.set_ylim(0.8, max(s.original_posts.max(), 1) * 6)
    ax.set_xticks(range(len(s))); ax.set_xticklabels(s.size_class, rotation=30, ha="right")
    ax.set_xlabel("Relays of the same original post"); ax.set_ylabel("Original posts (log scale)")
    ax.set_title("How far does a post travel? Relays per original post"); _grid(ax)
    fig.tight_layout(); fig.savefig(fd / "chain_size_distribution.png", dpi=200); plt.close(fig)

    d = t["delays"]
    x = np.arange(len(d))
    fig, ax = plt.subplots(figsize=(10, 5.6))
    ax.bar(x - 0.2, d.share_of_relays, 0.4, color="#2F5597", label="all relays")
    ax.bar(x + 0.2, d.share_of_first_relays, 0.4, color="#E8A33D", label="first relay of each post")
    ax.set_xticks(x); ax.set_xticklabels(d.delay_class, rotation=30, ha="right")
    ax.set_xlabel("Delay between the original post and the relay"); ax.set_ylabel("Share")
    ax.set_title("How fast is a post relayed?"); ax.legend(frameon=False); _grid(ax)
    fig.tight_layout(); fig.savefig(fd / "delay_distribution.png", dpi=200); plt.close(fig)

    y = t["by_year"]
    if len(y) >= 2:
        fig, ax = plt.subplots(figsize=(9, 5.4))
        ax.plot(y.year, y.share_within_1h, "-o", color="#2F5597", label="relayed within 1 hour")
        ax.plot(y.year, y.share_within_1day, "-s", color="#E8A33D", label="relayed within 1 day")
        ax.set_ylim(0, 1.03); ax.set_xticks(y.year); ax.set_xlabel("Year of the relay"); ax.set_ylabel("Share of relays")
        ax.set_title("Speed of relaying, by year"); ax.legend(frameon=False); _grid(ax)
        fig.tight_layout(); fig.savefig(fd / "delay_by_year.png", dpi=200); plt.close(fig)

    src = t["sources"]
    cum = src.relays.cumsum().to_numpy() / src.relays.sum()
    fig, ax = plt.subplots(figsize=(7.6, 6))
    ax.plot(np.arange(1, len(cum) + 1) / len(cum), cum, color="#2F5597")
    ax.plot([0, 1], [0, 1], "--", color="#7F7F7F", label="equal shares")
    ax.set_xlabel("Share of source channels (largest first)"); ax.set_ylabel("Share of all relays")
    ax.set_title("Concentration of sources"); ax.legend(frameon=False); _grid(ax, "both")
    fig.tight_layout(); fig.savefig(fd / "source_concentration.png", dpi=200); plt.close(fig)

    top = src.head(20).iloc[::-1]
    fig, ax = plt.subplots(figsize=(9.5, 6.4))
    ax.barh(range(len(top)), top.relays, color="#86B3A1")
    labels = [f"{c}" + (f" ({l})" if "language" in top and isinstance(l, str) else "")
              for c, l in zip(top.origin_channel, top.get("language", [None] * len(top)))]
    ax.set_yticks(range(len(top))); ax.set_yticklabels(labels, fontsize=7.5)
    for i, v in enumerate(top.relays):
        ax.text(v, i, f" {v:,}", va="center", fontsize=7)
    ax.set_xlabel("Relays"); ax.set_title("The 20 most relayed source channels"); _grid(ax, "x")
    ax.set_xlim(0, top.relays.max() * 1.15)
    fig.tight_layout(); fig.savefig(fd / "top_sources.png", dpi=200); plt.close(fig)

    if by_level is not None and len(by_level):
        p = by_level.pivot(index="year", columns="level", values="messages").fillna(0)
        p = p[[c for c in "ABCD" if c in p.columns]]
        share = p.div(p.sum(axis=1), axis=0)
        fig, ax = plt.subplots(figsize=(9.5, 5.6))
        bottom = np.zeros(len(share))
        for col, color in zip(share.columns, ["#2F5597", "#E8A33D", "#86B3A1", "#C0504D"]):
            ax.bar(share.index.astype(str), share[col], bottom=bottom, color=color, label=f"{col}: {LEVEL_TEXT[col]}")
            bottom += share[col].to_numpy()
        ax.set_ylabel("Share of forwarded messages"); ax.set_xlabel("Year of the forward")
        ax.set_title("Traceability level of forwarded messages, by year")
        ax.legend(frameon=False, fontsize=7, loc="lower left", bbox_to_anchor=(0, -0.42)); _grid(ax)
        fig.tight_layout(); fig.savefig(fd / "traceability_levels.png", dpi=200, bbox_inches="tight"); plt.close(fig)

    if avail is not None and len(avail):
        a = avail[avail.measure.isin(["origin_channel_in_corpus", "origin_post_found", "date_identical", "date_within_60s"])]
        fig, ax = plt.subplots(figsize=(8.5, 5.2))
        ax.bar(range(len(a)), a.share_of_relays, color="#5B8DD9")
        for x_, v in enumerate(a.share_of_relays):
            ax.text(x_, v, f"{v * 100:.1f}%", ha="center", va="bottom", fontsize=8)
        ax.set_xticks(range(len(a))); ax.set_xticklabels([m.replace("_", " ") for m in a.measure], rotation=20, ha="right")
        ax.set_ylim(0, 1.1); ax.set_ylabel("Share of relays")
        ax.set_title("Can the source be checked in the dataset?"); _grid(ax)
        fig.tight_layout(); fig.savefig(fd / "source_verification.png", dpi=200); plt.close(fig)

    (fd / "README.md").write_text(
        "# Figures - traceability (theme 3)\n\nImages only. Tables and the protocol are in the tracing_v2 folder.\n\n"
        "| File | What it shows |\n|---|---|\n"
        "| chain_size_distribution.png | original posts by number of relays |\n"
        "| delay_distribution.png | delay between the original post and its relays |\n"
        "| delay_by_year.png | share of relays within 1 hour / 1 day, by year |\n"
        "| source_concentration.png | share of relays held by the largest source channels |\n"
        "| top_sources.png | the 20 most relayed source channels |\n"
        "| traceability_levels.png | levels A to D of the forwarded messages, by year (needs --clean) |\n"
        "| source_verification.png | origin channel / post found in the dataset, date agreement (needs --clean) |\n",
        encoding="utf-8")


# ---------------------------------------------------------------- protocol text

def protocol_text(summ, dups, n_raw, levels_df, avail):
    L = ["# Tracing protocol - theme 3", "",
         f"Generated by `source_tracing_v2.py` on {date.today().isoformat()}.", "",
         "## What the data allows", "",
         "Telegram stores only the **original author** in the header of a forward. Each relay therefore points directly "
         "to its source (channel, post id, date of the original post). Intermediate hops of a chain are not recorded: the "
         "chain of an original post is its list of relays ordered by time.", "",
         "## Steps", "",
         "1. Read the forward header: origin channel, origin post id, origin date.",
         "2. Classify the traceability level:"]
    for k, v in LEVEL_TEXT.items():
        L.append(f"   - **{k}** - {v}")
    L += ["3. For level A, verify the source against the dataset: origin channel present, original post present, header date "
          "equal to the date of the post found.",
          "4. Order the relays of each original post by time (rank) and compute the delay to the original post.",
          "5. Report the sources (concentration, most relayed), the reach (relays per post) and the speed (delays).", "",
          "## Measured on the dataset", ""]
    L.append(f"- Relays read from chains: {n_raw:,}; duplicated relays removed: {dups:,}; relays kept: "
             f"{summ['relays_after_deduplication']:,}.")
    L.append(f"- Original posts: {summ['original_posts']:,} from {summ['origin_channels']:,} source channels, relayed by "
             f"{summ['relaying_channels']:,} channels.")
    L.append(f"- Relays per post: mean {summ['mean_relays_per_post']}, median {summ['median_relays_per_post']:g}, maximum "
             f"{summ['max_relays_per_post']:,}; {summ['posts_with_one_relay_share'] * 100:.1f}% of posts have a single relay.")
    L.append(f"- Median delay of the first relay: {summ['median_first_relay_delay_s']:g} s; "
             f"{summ['relays_within_1h_share'] * 100:.1f}% of relays occur within one hour; "
             f"{summ['relays_before_original']:,} relays carry a date earlier than the original post (to inspect).")
    if levels_df is not None and len(levels_df):
        tot = levels_df.groupby("level")["messages"].sum()
        allf = tot.sum()
        L += ["", "### Traceability levels (all forwarded messages)", "",
              "| Level | Meaning | Messages | Share |", "|---|---|---|---|"]
        for k in "ABCD":
            if k in tot.index:
                L.append(f"| {k} | {LEVEL_TEXT[k]} | {int(tot[k]):,} | {tot[k] / allf * 100:.2f}% |")
    if avail is not None and len(avail):
        L += ["", "### Source verification (level A)", "", "| Check | Original posts | Relays | Share of relays |", "|---|---|---|---|"]
        for _, r in avail.iterrows():
            L.append(f"| {r.measure} | {r.original_posts:,} | {r.relays:,} | {r.share_of_relays * 100:.1f}% |")
    L += ["", "## Limits", "",
          "- Hop-by-hop depth cannot be measured: only the original author is kept in a forward.",
          "- A post missing from the dataset is not proof that it never existed (deleted, outside the collected period).",
          "- Delays are measured in seconds between the date in the forward header and the date of the relay."]
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------- main

def run(args):
    out = Path(args.out)
    print("reading chains")
    c, n_raw, dups = load_chains(args.chains)
    print(f"  {n_raw:,} relays, {dups:,} duplicates removed")
    languages = None
    if args.languages:
        from community_detection_v2 import load_language_map
        languages = {k: v for k, v in load_language_map(args.languages).items()}
    t = chain_tables(c, languages)
    ctx = f"Relays: `{args.chains}` (job 2). " + (f"Messages: `{args.clean}` (job 1)." if args.clean else "")
    W = Writer(out, ctx)

    summ = dict(t["summary"], raw_relays=n_raw, duplicated_relays_removed=dups)
    W.table("tracing_summary", pd.DataFrame({"measure": list(summ), "value": list(summ.values())}),
            "Headline numbers of the chains after removing duplicated relays (same destination channel and message id).",
            {"measure": "name of the measure", "value": "value"})
    W.table("chain_size_distribution", t["size"], "Original posts grouped by their number of relays.",
            {"size_class": "relays of the post", "original_posts": "posts in the class", "relays": "relays they hold",
             "share_of_posts": "share of all posts", "share_of_relays": "share of all relays"})
    W.table("delay_distribution", t["delays"],
            "Delay between the original post and its relays, for all relays and for the first relay of each post.",
            {"delay_class": "delay range", "relays": "relays", "share_of_relays": "share of relays",
             "first_relays": "first relays of posts", "share_of_first_relays": "share of posts"})
    W.table("delay_by_year", t["by_year"], "Speed of relaying by year of the relay.",
            {"year": "year of the relay", "relays": "relays", "median_delay_s": "median delay in seconds",
             "share_within_1h": "relays within one hour of the original", "share_within_1day": "within one day"})
    src_cols = {"origin_channel": "source channel id", "original_posts": "its posts that were relayed",
                "relays": "relays of its posts", "relaying_channels": "distinct channels that relayed it",
                "relays_per_post": "relays / posts", "share_of_relays": "share of all relays",
                "language": "language from Channel_Language.csv"}
    W.table("top_sources", t["sources"].head(args.top), f"The {args.top} most relayed source channels.",
            {k: v for k, v in src_cols.items() if k in t["sources"].columns})
    W.table("source_concentration", t["concentration"], "Share of relays held by the largest source channels.",
            {"top_share_of_sources": "fraction of source channels (largest first)", "sources": "number of channels",
             "share_of_relays": "share of all relays they hold"})
    W.table("top_origin_posts", t["posts"], "The 100 most relayed original posts.",
            {"origin_channel": "source channel", "origin_post": "post id", "relays": "number of relays",
             "first_relay_delay_s": "delay of the first relay (s)", "last_relay_delay_s": "delay of the last relay (s)"})

    by_level = avail = None
    if args.clean:
        print("scanning cleaned messages (one pass)")
        levels, channels, found_ts, total, forwards = scan_clean(args.clean, t["uo"])
        by_level = pd.DataFrame([{"year": y, "level": LEVELS[k], "messages": v} for (y, k), v in sorted(levels.items())])
        lv = by_level.groupby("level")["messages"].sum().reindex(list("ABCD")).fillna(0).astype(np.int64)
        W.table("traceability_levels", pd.DataFrame({"level": lv.index, "meaning": [LEVEL_TEXT[k] for k in lv.index],
                                                     "messages": lv.values,
                                                     "share_of_forwards": (lv.values / max(lv.sum(), 1)).round(5)}),
                f"All {total:,} cleaned messages, of which {forwards:,} are forwards, by traceability level.",
                {"level": "A to D", "meaning": "definition", "messages": "forwarded messages", "share_of_forwards": "share"})
        W.table("traceability_by_year", by_level, "Traceability levels by year of the forwarding message.",
                {"year": "year", "level": "A to D", "messages": "forwarded messages"})
        avail = availability(c, t, found_ts, channels)
        W.table("source_verification", avail,
                "Is the source of a relay present in the dataset, and does the header date agree with the post found?",
                {"measure": "check", "original_posts": "distinct original posts", "share_of_posts": "share of posts",
                 "relays": "relays of those posts", "share_of_relays": "share of relays", "meaning": "reading"})

    (out / "tracing_protocol.md").write_text(protocol_text(t["summary"], dups, n_raw, by_level, avail),
                                             encoding="utf-8")
    print("  wrote tracing_protocol.md")
    if not args.no_charts:
        print("charts")
        charts(args.figdir, t, by_level, avail)
    print("done")
    return {"tables": W.tables, "chains": t, "levels": by_level, "availability": avail, "duplicates": dups}


# ---------------------------------------------------------------- selftest

OFF_SRC, OFF_DST = 2_500_000_000, 3_100_000_000      # above 2**31 on purpose: real channel ids reach that range


def synthetic(root, seed=0):
    rng = np.random.default_rng(seed)
    base = 1_600_000_000
    rows = []
    for ch in range(OFF_SRC, OFF_SRC + 50):                                    # 50 source channels with 100 original posts
        for p in range(1, 101):
            rows.append((ch, p, base + p * 30 * 86400, "", None, None))
    fwd = []
    mid = {}
    n_ok = 0
    for _ in range(4000):
        r = rng.random()
        dest = int(rng.integers(OFF_DST, OFF_DST + 200))
        mid[dest] = mid.get(dest, 0) + 1
        ts = base + int(rng.integers(0, 400)) * 3600 + int(rng.integers(0, 3600))
        if r < 0.80:                                                # level A
            oc = int(rng.choice(list(range(OFF_SRC, OFF_SRC + 50)) + [OFF_SRC + 2000, OFF_SRC + 2001]))
            op = int(rng.integers(1, 120))
            ots = base + op * 30 * 86400
            ts = ots + int(rng.lognormal(7, 2))
            rows.append((dest, mid[dest], ts, "channel", op, oc))
            fwd.append((oc, op, ots, dest, mid[dest], ts))
            n_ok += 1
        elif r < 0.88:
            rows.append((dest, mid[dest], ts, "channel", None, OFF_SRC))
        elif r < 0.94:
            rows.append((dest, mid[dest], ts, "user", None, None))
        else:
            rows.append((dest, mid[dest], ts, "hidden", None, None))
    clean = pd.DataFrame([(a, b, c, k, op, oc) for (a, b, c, k, op, oc) in
                          [(r[0], r[1], r[2], r[3], r[4], r[5] if len(r) > 5 else None) for r in rows]],
                         columns=["dest_channel", "msg_id", "ts", "kind", "origin_post", "origin_channel"])
    # originals are stored as (channel, post, ts, '', None, None)
    clean["origin_post"] = clean["origin_post"].astype("Int64")
    clean["origin_channel"] = clean["origin_channel"].astype("Int64")
    (root / "clean_csv").mkdir(parents=True)
    clean.to_csv(root / "clean_csv" / "part.csv", index=False)
    if HAS_ARROW:
        (root / "clean" / "batch=a").mkdir(parents=True)
        clean.to_parquet(root / "clean" / "batch=a" / "part.parquet", index=False)
    f = pd.DataFrame(fwd, columns=["origin_channel", "origin_post", "origin_ts", "dest_channel", "dest_msg", "ts"])
    f = f.sort_values(["origin_channel", "origin_post", "ts", "dest_channel", "dest_msg"])
    f["rank"] = f.groupby(["origin_channel", "origin_post"]).cumcount() + 1
    f["n_relays"] = f.groupby(["origin_channel", "origin_post"])["ts"].transform("size")
    f["delay_s"] = f.ts - f.origin_ts
    fmt = lambda s: pd.to_datetime(s, unit="s").dt.strftime("%Y-%m-%dT%H:%M:%S")
    f["origin_date"] = fmt(f.origin_ts)
    f["date"] = fmt(f.ts)
    f = f[["origin_channel", "origin_post", "origin_date", "rank", "dest_channel", "dest_msg", "date", "delay_s", "n_relays"]]
    f = pd.concat([f, f.head(40)], ignore_index=True)               # 40 duplicated relays
    (root / "chains_csv").mkdir(parents=True)
    f.to_csv(root / "chains_csv" / "part.csv", index=False)
    if HAS_ARROW:
        (root / "gold" / "chains").mkdir(parents=True)
        f.to_parquet(root / "gold" / "chains" / "part.parquet", index=False)
    return n_ok


def _check(r, t, n_ok, tag):
    assert r["duplicates"] == 40, r["duplicates"]
    s = r["chains"]["summary"]
    assert s["relays_after_deduplication"] == n_ok, (s, n_ok)
    assert s["origin_channels"] <= 52
    sz = r["chains"]["size"]
    assert sz.relays.sum() == n_ok and sz.original_posts.sum() == s["original_posts"]
    assert abs(r["chains"]["delays"].share_of_relays.sum() - 1) < 1e-3
    av = r["availability"].set_index("measure")
    assert 0 < av.loc["origin_channel_not_in_corpus", "share_of_relays"] < 0.1
    assert av.loc["origin_post_found", "share_of_relays"] > 0.7
    assert av.loc["date_identical", "relays"] == av.loc["origin_post_found", "relays"]
    lv = r["levels"].groupby("level")["messages"].sum()
    assert lv["A"] == n_ok and {"B", "C", "D"} <= set(lv.index), lv
    for name in r["tables"]:
        assert (t / f"out_{tag}" / name / f"{name}.csv").exists() and (t / f"out_{tag}" / name / "README.md").exists()
    assert (t / f"out_{tag}" / "tracing_protocol.md").exists()
    for f in ("chain_size_distribution", "delay_distribution", "delay_by_year", "source_concentration", "top_sources",
              "traceability_levels", "source_verification"):
        assert (t / f"fig_{tag}" / f"{f}.png").exists(), f


def selftest(_args):
    with tempfile.TemporaryDirectory() as t:
        t = Path(t)
        n_ok = synthetic(t)
        results = {}
        for tag, chains, clean in [("csv", t / "chains_csv", t / "clean_csv")] + (
                [("parquet", t / "gold" / "chains", t / "clean")] if HAS_ARROW else []):
            a = argparse.Namespace(chains=str(chains), clean=str(clean), languages=None, out=str(t / f"out_{tag}"),
                                   figdir=str(t / f"fig_{tag}"), top=20, no_charts=False)
            results[tag] = run(a)
            _check(results[tag], t, n_ok, tag)
            print(f"  [{tag}] OK")
        if "parquet" in results:
            assert results["csv"]["chains"]["summary"] == results["parquet"]["chains"]["summary"]
        else:
            print("  pyarrow not installed: the Parquet reader was not exercised in this self-test")
        print((t / "out_csv" / "tracing_protocol.md").read_text())
    print("selftest OK")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--chains", default="telescope_pipeline_files/gold/chains")
    ap.add_argument("--clean", default=None, help="cleaned messages (enables levels A-D and source verification)")
    ap.add_argument("--languages", default=None, help="Channel_Language.csv: adds the language of the top sources")
    ap.add_argument("--out", default="bigdata_pipeline/analysis/tracing_v2")
    ap.add_argument("--figdir", default="bigdata_pipeline/analysis/figures/traceability")
    ap.add_argument("--top", type=int, default=50, help="source channels listed in top_sources")
    ap.add_argument("--no-charts", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest(args)
    run(args)


if __name__ == "__main__":
    main()