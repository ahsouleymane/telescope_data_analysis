#!/usr/bin/env python3
"""
THEME 5 - SUSPICIOUS TRENDS IN DISSEMINATION AND INTERACTION.

Reads the gold tables of job6_suspicious.py (and channel_stats from job 4 when present) and answers:
  1. Which channels behave unlike the rest (bot-like or amplification-like behaviour)?
  2. Which groups of channels relay the same messages within seconds of each other?
  3. How do relay speed and burst cascades evolve over the months?

Channel indicators (a flag is raised when the value passes the threshold; thresholds come from the
population quantile --q, with a floor so that a quantile of a quiet population cannot flag normal values):
  fast_relay     share_fast10 high              relays almost instantly after the original post
  single_source  top_origin_share >= --src-max  almost everything forwarded comes from one source
  round_clock    hour entropy close to uniform  posts evenly over 24 h, no night pause
  fixed_second   sec_mode_share high            posts on the same second of the minute
  daily_burst    max_posts_day / median day     huge one-day burst compared with its usual day
  views_gap      robust z of views vs reach     views far from what the channel's forwarding reach predicts

Behaviour indicators 7-11 use fixed parameters (round numbers, not quantiles; not validated):
  pure_relay       >= 99 % of the messages are forwards, >= 1000 messages
  broad_instant    fast_relay AND >= 100 distinct sources (multi-source instant aggregator)
  steady_delay     IQR of the delay <= 10 s over >= 200 relays (needs delay_p25_s / delay_p75_s from job6)
  high_throughput  median >= 1000 messages per active day
  abrupt_volume    >= 10000 messages within <= 30 observed active days (observation window, not channel age)
Coordination indicator:
  in_tight_group   member of a coordinated group with density >= 0.5 and >= 5 channels
score_behaviour (0-11) and score_coordination (0-1) are kept apart; score is their sum; ties are broken by the
mean percentile of the flagged quantile-based indicators.
A flag means "statistically unusual behaviour", never proof of bot or coordination.

Outputs (one folder per table, CSV): suspicious_channels, indicator_summary, coordinated_groups,
coordinated_members, monthly_trend, suspicious_summary; figures in --figdir.

Usage: python3 suspicious_trends.py --gold telescope_pipeline_files/gold --out bigdata_pipeline/analysis/suspicious \
         --figdir bigdata_pipeline/analysis/figures/suspicious
       python3 suspicious_trends.py --selftest
"""
import argparse
import glob
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

BEHAVIOUR = ["fast_relay", "single_source", "round_clock", "fixed_second", "daily_burst", "views_gap",
             "pure_relay", "broad_instant", "steady_delay", "high_throughput", "abrupt_volume"]
COORDINATION = ["in_tight_group"]
INDICATORS = BEHAVIOUR + COORDINATION
CATEGORY = {**{k: "behaviour" for k in BEHAVIOUR}, **{k: "coordination" for k in COORDINATION}}


# ------------------------------------------------------------------ IO
def read_table(path):
    """Read a Spark output folder (Parquet or CSV parts) or a single file; None when missing."""
    p = Path(path)
    if not p.exists():
        return None
    if p.is_file():
        return pd.read_parquet(p) if p.suffix == ".parquet" else pd.read_csv(p)
    parquet = sorted(glob.glob(str(p / "*.parquet")))
    if parquet:
        return pd.concat((pd.read_parquet(f) for f in parquet), ignore_index=True)
    csv = sorted(glob.glob(str(p / "*.csv")))
    return pd.concat((pd.read_csv(f) for f in csv), ignore_index=True) if csv else None


def write_table(df, out, name):
    d = Path(out) / name
    d.mkdir(parents=True, exist_ok=True)
    df.to_csv(d / f"{name}.csv", index=False)


# ------------------------------------------------------------------ channel indicators
def hour_entropy(hours):
    """Normalised Shannon entropy (0-1) of the 24-hour posting profile of each channel."""
    m = hours.pivot_table(index="channel_id", columns="hour", values="n_posts", aggfunc="sum", fill_value=0)
    p = m.div(m.sum(axis=1), axis=0).to_numpy()
    with np.errstate(divide="ignore", invalid="ignore"):
        h = -np.nansum(np.where(p > 0, p * np.log(p), 0.0), axis=1) / math.log(24)
    return pd.Series(h, index=m.index, name="hour_entropy")


def robust_z(x):
    x = np.asarray(x, dtype=float)
    med = np.nanmedian(x)
    mad = np.nanmedian(np.abs(x - med))
    return (x - med) / (1.4826 * mad if mad > 0 else np.nan)


def views_residual_z(df, stats):
    """Robust z of log views against the channel's forwarding reach (forwarded-in count) and size."""
    if stats is None or "n_forwarded_in" not in stats.columns:
        return pd.Series(np.nan, index=df.index)
    d = df.merge(stats[["channel_id", "n_forwarded_in"]], on="channel_id", how="left")
    y = np.log1p(d["views_mean"].fillna(0).to_numpy())
    X = np.column_stack([np.ones(len(d)), np.log1p(d["n_forwarded_in"].fillna(0).to_numpy()),
                         np.log1p(d["n_posts"].to_numpy())])
    ok = np.isfinite(y)
    beta, *_ = np.linalg.lstsq(X[ok], y[ok], rcond=None)
    return pd.Series(robust_z(y - X @ beta), index=df.index)


def flag_channels(beh, hours, stats, q=0.99, min_forwarded=30, min_posts_round=500, min_posts_sec=200,
                  min_day_burst=100, src_max=0.9, fast_floor=0.3, entropy_floor=0.97, sec_floor=0.1,
                  burst_floor=20.0, z_views=4.0, pure_share=0.99, pure_min_posts=1000, broad_origins=100,
                  steady_iqr=10.0, steady_min_relays=200, throughput=1000, abrupt_posts=10000, abrupt_days=30,
                  tight_ids=None):
    """Return the behaviour table with one boolean column per indicator, the score and the reasons."""
    d = beh.copy()
    d["hour_entropy"] = d["channel_id"].map(hour_entropy(hours)) if hours is not None else np.nan
    d["burst_ratio"] = d["max_posts_day"] / d["median_posts_day"].clip(lower=1)
    d["views_z"] = views_residual_z(d, stats).to_numpy()
    thr = {}

    def cut(col, mask, floor):
        """Boolean flag: above the population quantile (strictly, so that ties never flag everyone)
        and at least `floor`; a quantile below the floor falls back to the floor itself."""
        v = d.loc[mask, col].dropna()
        qv = float(v.quantile(q)) if len(v) else floor
        thr[col] = max(qv, floor)
        return mask & ((d[col] > qv) & (d[col] >= floor) if qv >= floor else (d[col] >= floor))

    el_f = d["n_forwarded"].fillna(0) >= min_forwarded
    d["fast_relay"] = cut("share_fast10", el_f, fast_floor)
    d["single_source"] = el_f & (d["top_origin_share"] >= src_max)
    thr["top_origin_share"] = src_max
    el_r = d["n_posts"] >= min_posts_round
    d["round_clock"] = cut("hour_entropy", el_r, entropy_floor)
    el_s = d["n_posts"] >= min_posts_sec
    d["fixed_second"] = cut("sec_mode_share", el_s, sec_floor)
    el_b = d["max_posts_day"] >= min_day_burst
    d["daily_burst"] = cut("burst_ratio", el_b, burst_floor)
    d["views_gap"] = d["views_z"].abs() >= z_views
    thr["views_z"] = z_views

    def col(name):                                   # missing columns (older job6 output) give all-False indicators
        return d[name] if name in d else pd.Series(np.nan, index=d.index)

    d["share_forwarded"] = col("n_forwarded") / col("n_posts")
    d["delay_iqr_s"] = col("delay_p75_s") - col("delay_p25_s")
    d["pure_relay"] = (d["n_posts"] >= pure_min_posts) & (d["share_forwarded"] >= pure_share)
    d["broad_instant"] = d["fast_relay"] & (col("n_origins") >= broad_origins)
    d["steady_delay"] = (d["n_forwarded"].fillna(0) >= steady_min_relays) & (d["delay_iqr_s"] <= steady_iqr)
    d["high_throughput"] = (col("median_posts_day") >= throughput) & (col("n_active_days") >= 3)
    d["abrupt_volume"] = (d["n_posts"] >= abrupt_posts) & (col("n_active_days") <= abrupt_days)
    d["in_tight_group"] = d["channel_id"].isin(tight_ids) if tight_ids else False
    thr.update({"share_forwarded": pure_share, "n_origins": broad_origins, "delay_iqr_s": steady_iqr,
                "median_posts_day": throughput, "n_posts_abrupt": abrupt_posts})

    cols_for = {"fast_relay": "share_fast10", "single_source": "top_origin_share", "round_clock": "hour_entropy",
                "fixed_second": "sec_mode_share", "daily_burst": "burst_ratio", "views_gap": "views_z"}
    pct = pd.DataFrame({k: d[c].abs().rank(pct=True) if k == "views_gap" else d[c].rank(pct=True)
                        for k, c in cols_for.items()})
    flags = d[INDICATORS].fillna(False).astype(bool)
    d["score_behaviour"] = flags[BEHAVIOUR].sum(axis=1)
    d["score_coordination"] = flags[COORDINATION].sum(axis=1)
    d["score"] = d["score_behaviour"] + d["score_coordination"]
    d["mean_pct"] = (pct.where(flags[list(cols_for)]).mean(axis=1)).fillna(0.0)
    d["reasons"] = flags.apply(lambda r: ", ".join(k for k in INDICATORS if r[k]), axis=1)
    return d.sort_values(["score", "mean_pct"], ascending=False).reset_index(drop=True), thr


def indicator_summary(d, thr):
    n = len(d)
    rows = [{"category": CATEGORY[k], "indicator": k, "n_flagged": int(d[k].sum()),
             "share_of_channels_pct": round(100 * d[k].mean(), 3)} for k in INDICATORS]
    out = pd.DataFrame(rows)
    key = {"fast_relay": "share_fast10", "single_source": "top_origin_share", "round_clock": "hour_entropy",
           "fixed_second": "sec_mode_share", "daily_burst": "burst_ratio", "views_gap": "views_z",
           "pure_relay": "share_forwarded", "broad_instant": "n_origins", "steady_delay": "delay_iqr_s",
           "high_throughput": "median_posts_day", "abrupt_volume": "n_posts_abrupt"}
    out["threshold"] = [thr.get(key.get(k, ""), np.nan) for k in INDICATORS]
    out.attrs["n"] = n
    return out


# ------------------------------------------------------------------ coordinated groups
def _components(p):
    """Connected components of the edge list p (channel_a, channel_b): list of edge sub-tables."""
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    ids = pd.Index(pd.unique(np.concatenate([p["channel_a"], p["channel_b"]])))
    a, b = ids.get_indexer(p["channel_a"]), ids.get_indexer(p["channel_b"])
    _, lab = connected_components(coo_matrix((np.ones(len(p)), (a, b)), shape=(len(ids), len(ids))), directed=False)
    el = lab[a]
    return [g for _, g in p.groupby(el)]


def split_groups(p, min_shared, min_size, max_size, factor=1.5):
    """Groups of channels linked by pairs with n_shared >= threshold. A component larger than max_size is
    chained together by a few very popular channels, not a real group: its threshold is raised (x factor)
    until it falls apart into components of at most max_size channels. Returns [(edges, threshold)]."""
    out, todo = [], [(p[p["n_shared"] >= min_shared], float(min_shared))]
    while todo:
        edges, thr = todo.pop()
        if edges.empty:
            continue
        for g in _components(edges):
            n = len(set(g["channel_a"]) | set(g["channel_b"]))
            if n < min_size:
                continue
            if n <= max_size:
                out.append((g, thr))
            else:
                nxt = max(thr * factor, thr + 1)
                todo.append((g[g["n_shared"] >= nxt], nxt))
    return out


def coordinated_groups(pairs, min_shared=5, max_median_dt=60, min_size=3, max_size=300):
    """Groups of channels that relay the same messages within seconds (see split_groups)."""
    p = pairs[(pairs["n_shared"] >= min_shared) & (pairs["median_dt_s"] <= max_median_dt)]
    if p.empty:
        return pd.DataFrame(), pd.DataFrame()
    parts = split_groups(p, min_shared, min_size, max_size)
    if not parts:
        return pd.DataFrame(), pd.DataFrame()
    rows, mem = [], []
    for g, thr in parts:
        chans = sorted(set(g["channel_a"]) | set(g["channel_b"]))
        n = len(chans)
        rows.append({"n_channels": n, "n_pairs": len(g), "shared_total": int(g["n_shared"].sum()),
                     "shared_max": int(g["n_shared"].max()), "median_dt_s": float(g["median_dt_s"].median()),
                     "n_origins_max": int(g["n_origins"].max()), "density": round(2 * len(g) / (n * (n - 1)), 3),
                     "min_shared_used": thr})
        deg = pd.concat([g[["channel_a", "n_shared"]].rename(columns={"channel_a": "channel_id"}),
                         g[["channel_b", "n_shared"]].rename(columns={"channel_b": "channel_id"})]) \
            .groupby("channel_id")["n_shared"].sum()
        mem.append(pd.DataFrame({"channel_id": chans, "shared_total": [int(deg[c]) for c in chans]}))
    grp = pd.DataFrame(rows)
    order = grp.sort_values(["n_channels", "shared_total"], ascending=False).index
    grp = grp.loc[order].reset_index(drop=True)
    grp["group_rank"] = np.arange(1, len(grp) + 1)
    rank_of = {old: new for new, old in enumerate(order, start=1)}
    members = pd.concat([m.assign(group_rank=rank_of[i]) for i, m in enumerate(mem)], ignore_index=True) \
        .sort_values(["group_rank", "shared_total"], ascending=[True, False]).reset_index(drop=True)
    return grp, members


# ------------------------------------------------------------------ monthly trends
def monthly_trend(speed, casc, min_forwards=100):
    s = speed.copy()
    s = s[s["n_forwards"] >= min_forwards]
    s["fast10_pct"] = (100 * s["n_fast10"] / s["n_forwards"]).round(2)
    s["fast60_pct"] = (100 * s["n_fast60"] / s["n_forwards"]).round(2)
    if casc is not None and len(casc):
        c = casc.assign(tight=(casc["n_first10min"] / casc["n_relays"]) >= 0.8).groupby("month") \
            .agg(n_cascades=("n_relays", "size"), n_tight=("tight", "sum")).reset_index()
        s = s.merge(c, on="month", how="outer")
    return s.sort_values("month").reset_index(drop=True)


# ------------------------------------------------------------------ charts
def charts(d, summ, grp, trend, figdir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    figdir = Path(figdir)
    figdir.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(8, 5.5))
    ax.barh((summ["indicator"] + " (" + summ["category"].str[:5] + ")")[::-1], summ["n_flagged"][::-1], color="#1F4E79")
    for i, v in enumerate(summ["n_flagged"][::-1]):
        ax.text(v, i, f" {v:,}", va="center", fontsize=9)
    ax.set_xlabel("flagged channels")
    ax.set_title("Channels flagged per indicator")
    fig.tight_layout()
    fig.savefig(figdir / "indicator_counts.png", dpi=150)
    plt.close(fig)

    vc = d["score"].value_counts().reindex(range(0, int(d["score"].max()) + 1), fill_value=0)
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(vc.index.astype(str), vc.values, color="#1F4E79")
    ax.set_yscale("log")
    ax.set_xlabel("number of flags")
    ax.set_ylabel("channels (log)")
    ax.set_title("Channels by number of indicators flagged")
    fig.tight_layout()
    fig.savefig(figdir / "score_distribution.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 5))
    x, y = d["share_fast10"], d["top_origin_share"]
    ok = x.notna() & y.notna()
    ax.scatter(x[ok], y[ok], s=4, alpha=0.25, color="#888888", label="all")
    hi = ok & (d["score"] >= 2)
    ax.scatter(x[hi], y[hi], s=14, color="#C0392B", label="2+ flags")
    ax.set_xlabel("share relayed within 10 s of the original")
    ax.set_ylabel("share from the single top source")
    ax.set_title("Relay speed vs dependence on one source")
    ax.legend()
    fig.tight_layout()
    fig.savefig(figdir / "fast_vs_source.png", dpi=150)
    plt.close(fig)

    if trend is not None and len(trend):
        fig, ax = plt.subplots(figsize=(10, 4))
        t = trend.dropna(subset=["fast10_pct"])
        ax.plot(pd.to_datetime(t["month"] + "-01"), t["fast10_pct"], color="#C0392B", label="within 10 s")
        ax.plot(pd.to_datetime(t["month"] + "-01"), t["fast60_pct"], color="#1F4E79", label="within 60 s")
        ax.set_ylabel("% of forwards")
        ax.set_title("Share of instant relays per month")
        ax.legend()
        fig.tight_layout()
        fig.savefig(figdir / "fast_share_monthly.png", dpi=150)
        plt.close(fig)
        if "n_tight" in trend.columns:
            fig, ax = plt.subplots(figsize=(10, 4))
            t = trend.dropna(subset=["n_cascades"])
            ax.bar(pd.to_datetime(t["month"] + "-01"), t["n_cascades"], width=25, color="#BBBBBB", label="cascades >= 10 relays")
            ax.bar(pd.to_datetime(t["month"] + "-01"), t["n_tight"], width=25, color="#C0392B", label="80%+ of relays in first 10 min")
            ax.set_title("Cascades per month of the original post")
            ax.legend()
            fig.tight_layout()
            fig.savefig(figdir / "cascades_monthly.png", dpi=150)
            plt.close(fig)

    if grp is not None and len(grp):
        g = grp.head(15)
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.barh([f"group {r}" for r in g["group_rank"]][::-1], g["n_channels"][::-1], color="#1F4E79")
        for i, (n, s) in enumerate(zip(g["n_channels"][::-1], g["shared_total"][::-1])):
            ax.text(n, i, f" {n} ch., {s:,} shared", va="center", fontsize=8)
        ax.set_xlabel("channels in the group")
        ax.set_title("Largest groups relaying the same messages within seconds")
        fig.tight_layout()
        fig.savefig(figdir / "coordinated_groups.png", dpi=150)
        plt.close(fig)


# ------------------------------------------------------------------ run
def run(a):
    gold = Path(a.gold)
    beh, hours, pairs = read_table(gold / "channel_behavior"), read_table(gold / "channel_hours"), read_table(gold / "coordinated_pairs")
    speed, casc, stats = read_table(gold / "forward_speed_monthly"), read_table(gold / "cascades"), read_table(gold / "channel_stats")
    if beh is None:
        sys.exit(f"channel_behavior not found in {gold}: run job6_suspicious.py first")
    grp, members = (coordinated_groups(pairs, a.min_shared, a.max_median_dt, a.min_group, a.max_group)
                    if pairs is not None else (pd.DataFrame(), pd.DataFrame()))
    tight = set()
    if len(grp):
        ranks = grp[(grp["density"] >= a.tight_density) & (grp["n_channels"] >= a.tight_size)]["group_rank"]
        tight = set(members[members["group_rank"].isin(ranks)]["channel_id"])
    d, thr = flag_channels(beh, hours, stats, q=a.q, min_forwarded=a.min_forwarded, src_max=a.src_max,
                           z_views=a.z_views, min_day_burst=a.min_day_burst, pure_share=a.pure_share,
                           pure_min_posts=a.pure_min_posts, broad_origins=a.broad_origins, steady_iqr=a.steady_iqr,
                           steady_min_relays=a.steady_min_relays, throughput=a.throughput, abrupt_posts=a.abrupt_posts,
                           abrupt_days=a.abrupt_days, tight_ids=tight)
    summ = indicator_summary(d, thr)
    trend = monthly_trend(speed, casc) if speed is not None else None

    cols = [c for c in ["channel_id", "score", "score_behaviour", "score_coordination", "reasons", "n_posts", "n_forwarded",
                        "share_forwarded", "n_origins", "share_fast10", "top_origin_share", "delay_iqr_s", "hour_entropy",
                        "sec_mode_share", "max_posts_day", "median_posts_day", "n_active_days", "burst_ratio", "views_z"] if c in d]
    write_table(d[d["score"] >= 1][cols].head(a.top).round(4), a.out, "suspicious_channels")
    write_table(summ, a.out, "indicator_summary")
    if len(grp):
        in_group = set(members["channel_id"])
        members["also_flagged"] = members["channel_id"].map(d.set_index("channel_id")["score"]).fillna(0).astype(int)
        write_table(grp, a.out, "coordinated_groups")
        write_table(members, a.out, "coordinated_members")
    if trend is not None:
        write_table(trend, a.out, "monthly_trend")

    n = len(d)
    rows = [("channels evaluated", n), ("channels with 1+ flag", int((d["score"] >= 1).sum())),
            ("channels with 2+ flags", int((d["score"] >= 2).sum())), ("channels with 3+ flags", int((d["score"] >= 3).sum())),
            ("coordinated pairs kept", 0 if pairs is None else int(((pairs["n_shared"] >= a.min_shared) & (pairs["median_dt_s"] <= a.max_median_dt)).sum())),
            ("channels with 2+ behaviour flags", int((d["score_behaviour"] >= 2).sum())),
            ("channels with 3+ behaviour flags", int((d["score_behaviour"] >= 3).sum())),
            ("channels in tight groups (coordination flag)", int(d["in_tight_group"].sum())),
            ("... of which with 1+ behaviour flag", int((d["in_tight_group"] & (d["score_behaviour"] >= 1)).sum())),
            ("coordinated groups", len(grp)), ("channels in groups", len(members)),
            ("largest group (channels)", int(grp["n_channels"].max()) if len(grp) else 0)]
    if trend is not None and trend["fast10_pct"].notna().any():
        t = trend.dropna(subset=["fast10_pct"])
        rows += [("fast10 % first month", float(t["fast10_pct"].iloc[0])), ("fast10 % last month", float(t["fast10_pct"].iloc[-1])),
                 ("fast10 % max month", f'{t.loc[t["fast10_pct"].idxmax(), "month"]} ({t["fast10_pct"].max():.1f})')]
    summary = pd.DataFrame(rows, columns=["metric", "value"])
    write_table(summary, a.out, "suspicious_summary")
    if not a.no_charts:
        charts(d, summ, grp, trend, a.figdir)
    print(summary.to_string(index=False))
    print("\nindicators:\n", summ.to_string(index=False))
    if len(grp):
        print("\nlargest groups:\n", grp.head(10).to_string(index=False))
    top = d[d["score"] >= 1].head(10)
    print("\ntop channels:\n", top[["channel_id", "score", "reasons", "n_posts", "n_forwarded"]].to_string(index=False))
    return d, grp, members, trend


# ------------------------------------------------------------------ selftest
def selftest():
    rng = np.random.default_rng(1)
    n = 3000
    beh = pd.DataFrame({"channel_id": np.arange(n), "n_posts": rng.integers(60, 3000, n),
                        "views_mean": rng.lognormal(6, 1, n), "max_posts_day": rng.integers(5, 40, n),
                        "median_posts_day": rng.integers(2, 10, n), "n_forwarded": rng.integers(0, 400, n),
                        "share_fast10": rng.beta(1, 30, n), "top_origin_share": rng.beta(2, 5, n),
                        "sec_mode_share": rng.uniform(0.015, 0.03, n)})
    beh["n_origins"] = rng.integers(1, 30, n)
    beh["n_active_days"] = rng.integers(30, 400, n)
    beh["delay_p25_s"] = rng.uniform(100, 2000, n)
    beh["delay_p75_s"] = beh["delay_p25_s"] + rng.uniform(500, 5000, n)
    bot, agg = 99999, 88888
    extra = [dict(channel_id=bot, n_posts=2000, views_mean=500.0, max_posts_day=600, median_posts_day=5, n_forwarded=300,
                  share_fast10=0.95, top_origin_share=0.98, sec_mode_share=0.6, n_origins=2, n_active_days=100,
                  delay_p25_s=1.0, delay_p75_s=3000.0),
             dict(channel_id=agg, n_posts=60849, views_mean=7.7, max_posts_day=4339, median_posts_day=3042, n_forwarded=60739,
                  share_fast10=0.72, top_origin_share=0.03, sec_mode_share=0.043, n_origins=492, n_active_days=22,
                  delay_p25_s=5.0, delay_p75_s=13.0)]
    beh = pd.concat([beh, pd.DataFrame(extra)], ignore_index=True)
    hours = pd.DataFrame([(c, h, int(max(1, rng.normal(40, 8)) if 8 <= h <= 22 else rng.integers(0, 4)))
                          for c in beh["channel_id"] for h in range(24)], columns=["channel_id", "hour", "n_posts"])
    hours.loc[hours["channel_id"] == bot, "n_posts"] = 80
    stats = pd.DataFrame({"channel_id": beh["channel_id"], "n_forwarded_in": rng.integers(0, 500, len(beh))})
    d, thr = flag_channels(beh, hours, stats, tight_ids={agg})
    r = d.set_index("channel_id")
    assert r.loc[bot, "score_behaviour"] >= 4, r.loc[bot, "reasons"]
    a_ = r.loc[agg]
    for k in ["fast_relay", "pure_relay", "broad_instant", "steady_delay", "high_throughput", "abrupt_volume", "in_tight_group"]:
        assert a_[k], (k, a_["reasons"])
    assert not a_["single_source"] and not a_["fixed_second"] and a_["score_behaviour"] == 6 and a_["score_coordination"] == 1
    assert d.iloc[0]["channel_id"] in (agg, bot)
    assert (d["score"] >= 1).mean() < 0.1, (d["score"] >= 1).mean()
    smy = indicator_summary(d, thr)
    assert set(smy["category"]) == {"behaviour", "coordination"} and len(smy) == len(INDICATORS)
    # group: 5 channels fully connected, plus a noisy 2-channel pair that must not form a group
    ch = [1, 2, 3, 4, 5]
    rows = [(a, b, 20, 3, 4.0) for i, a in enumerate(ch) for b in ch[i + 1:]]
    rows += [(10, 11, 30, 2, 5.0), (20, 21, 50, 5, 500.0), (22, 23, 2, 1, 3.0)]
    pairs = pd.DataFrame(rows, columns=["channel_a", "channel_b", "n_shared", "n_origins", "median_dt_s"])
    grp, mem = coordinated_groups(pairs)
    assert len(grp) == 1 and grp.loc[0, "n_channels"] == 5 and grp.loc[0, "density"] == 1.0, grp
    assert set(mem["channel_id"]) == set(ch)
    # two tight groups (strong pairs) bridged by a weak link through a hub must come out as two groups
    t1, t2 = list(range(100, 106)), list(range(200, 206))
    rows = [(a, b, 40, 4, 2.0) for i, a in enumerate(t1) for b in t1[i + 1:]]
    rows += [(a, b, 40, 4, 2.0) for i, a in enumerate(t2) for b in t2[i + 1:]]
    rows += [(100, 200, 5, 2, 9.0)]
    g2, m2 = coordinated_groups(pd.DataFrame(rows, columns=pairs.columns), max_size=8)
    assert len(g2) == 2 and sorted(g2["n_channels"]) == [6, 6] and (g2["min_shared_used"] > 5).all(), g2
    speed = pd.DataFrame({"month": ["2020-01", "2020-02", "2020-03"], "n_forwards": [1000, 50, 2000],
                          "n_fast10": [10, 5, 400], "n_fast60": [30, 6, 600], "median_delay_s": [900, 600, 20]})
    casc = pd.DataFrame({"month": ["2020-01", "2020-01", "2020-03"], "n_relays": [10, 20, 50], "n_first10min": [9, 2, 49]})
    t = monthly_trend(speed, casc)
    assert list(t["month"]) == ["2020-01", "2020-03"], t      # 2020-02 has too few forwards
    assert t.loc[0, "n_tight"] == 1 and t.loc[1, "fast10_pct"] == 20.0
    print("selftest OK")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--gold", type=Path, default=Path("telescope_pipeline_files/gold"))
    ap.add_argument("--out", type=Path, default=Path("bigdata_pipeline/analysis/suspicious"))
    ap.add_argument("--figdir", type=Path, default=Path("bigdata_pipeline/analysis/figures/suspicious"))
    ap.add_argument("--q", type=float, default=0.99, help="population quantile used as threshold")
    ap.add_argument("--min-forwarded", type=int, default=30)
    ap.add_argument("--src-max", type=float, default=0.9, help="top_origin_share threshold")
    ap.add_argument("--z-views", type=float, default=4.0)
    ap.add_argument("--min-day-burst", type=int, default=100)
    ap.add_argument("--min-shared", type=int, default=5)
    ap.add_argument("--max-median-dt", type=float, default=60)
    ap.add_argument("--min-group", type=int, default=3)
    ap.add_argument("--max-group", type=int, default=300, help="a larger component is split by raising the pair threshold")
    ap.add_argument("--tight-density", type=float, default=0.5, help="density of a 'tight' coordinated group")
    ap.add_argument("--tight-size", type=int, default=5, help="min channels of a 'tight' group")
    ap.add_argument("--pure-share", type=float, default=0.99, help="share of forwards of a pure relay")
    ap.add_argument("--pure-min-posts", type=int, default=1000)
    ap.add_argument("--broad-origins", type=int, default=100, help="distinct sources of a broad aggregator")
    ap.add_argument("--steady-iqr", type=float, default=10.0, help="max IQR (s) of the delay for a scripted relay")
    ap.add_argument("--steady-min-relays", type=int, default=200)
    ap.add_argument("--throughput", type=int, default=1000, help="median posts per active day")
    ap.add_argument("--abrupt-posts", type=int, default=10000)
    ap.add_argument("--abrupt-days", type=int, default=30, help="active days observed in the dataset")
    ap.add_argument("--top", type=int, default=500, help="rows kept in suspicious_channels")
    ap.add_argument("--no-charts", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
        return
    run(a)


if __name__ == "__main__":
    main()