#!/usr/bin/env python3
"""
FAST MIRROR CHANNELS - who relays almost instantly, and from which single source?

Selects the channels that (1) relay a large share of their forwards within seconds of the original post and
(2) take almost everything from one source channel, then identifies:
  * the source each channel follows (top source), how regular its delay is, since when it does it;
  * families: all selected channels that follow the same source;
  * context: title / username / audience (public channel metadata), community, language, city.

Delay regularity: delay_iqr_s = p75 - p25 of the delays to the top source. A very small value (a few seconds)
means the lag is almost constant, which is how a script behaves; a large value looks human or batch-driven.
Nothing here proves automation: news mirrors and official relays behave the same way.

Inputs (all from earlier steps):
  --behavior  gold/channel_behavior         (job6)    --chains gold/chains (job2)
  optional    --metadata Source_Channel_Metadata.csv, --communities, --languages, --geo

Selection (parameters, not constants): share_fast10 >= --fast-min, top_origin_share >= --src-min,
n_forwarded >= --min-forwarded.

Outputs in --out: fast_mirror_channels, fast_mirror_families, fast_mirror_summary; charts in --figdir.
Usage: python3 fast_mirror_channels.py [--fast-min 0.44] [--src-min 0.9]
"""
import argparse
import csv
import re
import glob
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


def read_table(path):
    p = Path(path)
    if not p.exists():
        return None
    if p.is_file():
        return pd.read_parquet(p) if p.suffix == ".parquet" else pd.read_csv(p)
    fs = sorted(glob.glob(str(p / "*.parquet")))
    if fs:
        return pd.concat((pd.read_parquet(f) for f in fs), ignore_index=True)
    fs = sorted(glob.glob(str(p / "*.csv")))
    return pd.concat((pd.read_csv(f) for f in fs), ignore_index=True) if fs else None


def read_chains(path, ids):
    """Chains of the selected destination channels only (columns origin_channel, dest_channel, delay_s, date)."""
    cols = ["origin_channel", "dest_channel", "delay_s", "date"]
    p = Path(path)
    if glob.glob(str(p / "*.parquet")) or p.suffix == ".parquet":
        import pyarrow.dataset as ds
        d = ds.dataset(str(p), format="parquet")
        return d.to_table(columns=cols, filter=ds.field("dest_channel").isin(sorted(int(i) for i in ids))).to_pandas()
    d = read_table(p)
    return d[d["dest_channel"].isin(ids)][cols]


def follow_profile(chains, ids):
    """Per channel: top source and the regularity of the delay to it."""
    c = chains[chains["dest_channel"].isin(ids) & (chains["delay_s"] >= 0)].copy()
    c["month"] = pd.to_datetime(c["date"], utc=True, errors="coerce", format="ISO8601").dt.strftime("%Y-%m")
    n = c.groupby("dest_channel").size().rename("n_relays")
    per = c.groupby(["dest_channel", "origin_channel"])
    cnt = per.size().rename("n_from_source").reset_index()
    top = cnt.sort_values(["dest_channel", "n_from_source"], ascending=[True, False]).drop_duplicates("dest_channel")
    c = c.merge(top[["dest_channel", "origin_channel"]], on=["dest_channel", "origin_channel"])
    q = c.groupby("dest_channel")["delay_s"].quantile([0.25, 0.5, 0.75]).unstack()
    q.columns = ["delay_p25_s", "delay_median_s", "delay_p75_s"]
    q["delay_iqr_s"] = q["delay_p75_s"] - q["delay_p25_s"]
    q["share_from_source_within10s"] = c.assign(f=c["delay_s"] <= 10).groupby("dest_channel")["f"].mean()
    q["first_month"] = c.groupby("dest_channel")["month"].min()
    q["last_month"] = c.groupby("dest_channel")["month"].max()
    q["n_active_months"] = c.groupby("dest_channel")["month"].nunique()
    out = top.rename(columns={"origin_channel": "top_source"}).set_index("dest_channel").join(q).join(n)
    out["top_source_share"] = out["n_from_source"] / out["n_relays"]
    return out.reset_index().rename(columns={"dest_channel": "channel_id"})


def public_info(path, ids):
    """Title, username and audience size of public channels, read only for the requested ids."""
    if not path or not Path(path).exists():
        return pd.DataFrame(columns=["channel_id", "title", "username", "participants_count"])
    size = sys.maxsize
    while True:
        try:
            csv.field_size_limit(size)
            break
        except OverflowError:
            size //= 10
    ids, rows = {int(i) for i in ids}, []
    with open(path, encoding="utf-8-sig", newline="", errors="replace") as f:
        for r in csv.DictReader(f):
            try:
                cid = int(float(r.get("id", r.get("channel_id", ""))))
            except ValueError:
                continue
            if cid not in ids:
                continue
            try:
                o = json.loads(r["data"])
            except (KeyError, ValueError):
                continue
            full = o.get("full_chat") if isinstance(o.get("full_chat"), dict) else {}
            main = o
            for x in o.get("chats", []) if isinstance(o.get("chats"), list) else []:
                if isinstance(x, dict) and x.get("id") == cid:
                    main = x
            rows.append({"channel_id": cid, "title": main.get("title") or o.get("title") or "",
                         "username": main.get("username") or o.get("username") or "",
                         "participants_count": full.get("participants_count", main.get("participants_count"))})
    return pd.DataFrame(rows, columns=["channel_id", "title", "username", "participants_count"]).drop_duplicates("channel_id")


def attach_context(d, communities, languages, geo):
    if communities is not None and Path(communities).exists():
        c = pd.read_csv(communities, usecols=["channel_id", "community"]).drop_duplicates("channel_id")
        d = d.merge(c, on="channel_id", how="left")
        d = d.merge(c.rename(columns={"channel_id": "top_source", "community": "source_community"}), on="top_source", how="left")
        d["same_community_as_source"] = d["community"].eq(d["source_community"]) & d["community"].notna()
    if languages is not None and Path(languages).exists():
        L = pd.read_csv(languages, dtype=str)
        idc = next((c for c in ["channel_id", "file_names", "id"] if c in L), L.columns[0])
        lc = next((c for c in ["detected_language", "language", "lang"] if c in L), None)
        if lc:
            L = pd.DataFrame({"channel_id": pd.to_numeric(L[idc].str.extract(r"(\d+)")[0], errors="coerce"), "language": L[lc]})
            L = L.dropna().astype({"channel_id": "int64"}).drop_duplicates("channel_id")
            d = d.merge(L, on="channel_id", how="left")
    if geo is not None and Path(geo).exists():
        g = pd.read_csv(geo)
        g = g[g["n_cities"].eq(1)] if "n_cities" in g else g
        g = g.drop_duplicates("channel_id").assign(city_key=lambda x: x["city"].astype(str) + " (" + x["country"].astype(str) + ")")
        d = d.merge(g[["channel_id", "city_key"]], on="channel_id", how="left")
    return d


DISCUSSION_WORDS = r"chat|чат|comment|комментар|discussion|обсужд|коммент"


def _tokens(x):
    return {t for t in re.findall(r"\w+", str(x).lower()) if not t.isdigit()}


def title_similarity(title, source_title):
    """Share of the shorter title's words found in the other title (1 = one title contains the other)."""
    a, b = _tokens(title), _tokens(source_title)
    if not a or not b or not any(len(t) >= 4 for t in a & b):
        return 0.0
    return len(a & b) / min(len(a), len(b))


def classify(d, words, max_delay, max_iqr, instant_delay, min_sim=0.5):
    """Descriptive kind of each selected channel (rules are shown in the report, nothing is deleted):
      linked_discussion    near-constant short lag AND (a chat/comments word in the title OR a title similar to the
                           source title): Telegram forwards every post of a channel to its linked discussion group
      discussion_possible  same lag signature (<= max_delay s, IQR <= max_iqr s) without word or similar title
      instant_relay        median delay <= instant_delay s (same second): alert/news relays and cross-posting tools
      other                everything else: the cases to review by hand
    Returns the kind and the reason of the discussion rule.
    """
    title = d["title"].fillna("").astype(str)
    has_word = title.str.contains(words, case=False, regex=True)
    src = d["source_title"] if "source_title" in d else pd.Series("", index=d.index)
    sim = pd.Series([title_similarity(t, s) for t, s in zip(title, src.fillna(""))], index=d.index)
    similar = sim >= min_sim
    steady = (d["delay_median_s"] <= max_delay) & (d["delay_iqr_s"] <= max_iqr)
    kind = np.select([(has_word | similar) & steady & (d["delay_median_s"] > instant_delay),
                      steady & (d["delay_median_s"] > instant_delay), d["delay_median_s"] <= instant_delay],
                     ["linked_discussion", "discussion_possible", "instant_relay"], default="other")
    reason = np.where(kind != "linked_discussion", "", np.where(has_word, "title word", "similar title"))
    return pd.Series(kind, index=d.index), pd.Series(reason, index=d.index), sim.round(2)


def families(d, min_members):
    f = (d.groupby("top_source")
         .agg(n_followers=("channel_id", "size"), relays_total=("n_relays", "sum"),
              delay_median_s=("delay_median_s", "median"), delay_iqr_median_s=("delay_iqr_s", "median"),
              first_month=("first_month", "min"), last_month=("last_month", "max"))
         .reset_index())
    f = f[f["n_followers"] >= min_members].sort_values(["n_followers", "relays_total"], ascending=False).reset_index(drop=True)
    f["family_rank"] = np.arange(1, len(f) + 1)
    return f


def charts(d, f, figdir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    figdir = Path(figdir)
    figdir.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(d["delay_median_s"].clip(upper=120), bins=40, color="#1F4E79")
    ax.set(xlabel="median delay to the top source, s (capped at 120)", ylabel="channels",
           title="How fast do the selected channels relay?")
    fig.tight_layout()
    fig.savefig(figdir / "mirror_delay.png", dpi=150)
    plt.close(fig)
    if len(f):
        g = f.head(15)
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.barh([f"source {s}" for s in g["top_source"]][::-1], g["n_followers"][::-1], color="#1F4E79")
        for i, (n, m) in enumerate(zip(g["n_followers"][::-1], g["delay_median_s"][::-1])):
            ax.text(n, i, f" {n} channels, median {m:.0f}s", va="center", fontsize=8)
        ax.set_xlabel("channels that follow this source almost instantly")
        ax.set_title("Sources followed by the most fast mirrors")
        fig.tight_layout()
        fig.savefig(figdir / "mirror_families.png", dpi=150)
        plt.close(fig)


def run(a):
    beh = read_table(a.behavior)
    if beh is None:
        sys.exit(f"channel_behavior not found at {a.behavior}")
    sel = beh[(beh["share_fast10"] >= a.fast_min) & (beh["top_origin_share"] >= a.src_min) & (beh["n_forwarded"] >= a.min_forwarded)]
    print(f"selected channels: {len(sel):,} of {len(beh):,} (fast >= {a.fast_min}, one source >= {a.src_min}, >= {a.min_forwarded} forwards)")
    ids = set(sel["channel_id"].astype("int64"))
    prof = follow_profile(read_chains(a.chains, ids), ids)
    d = sel[["channel_id", "n_posts", "n_forwarded", "share_fast10", "top_origin_share", "sec_mode_share"]].merge(prof, on="channel_id", how="left")
    info = public_info(a.metadata, ids | set(d["top_source"].dropna().astype("int64")))
    d = d.merge(info, on="channel_id", how="left")
    d = d.merge(info.rename(columns={"channel_id": "top_source", "title": "source_title", "username": "source_username",
                                     "participants_count": "source_participants"}), on="top_source", how="left")
    d = attach_context(d, a.communities, a.languages, a.geo)
    d["source_is_selected"] = d["top_source"].isin(ids)
    d["lag_type"] = np.where(d["delay_iqr_s"] <= a.regular_iqr, "near-constant lag", "variable lag")
    d["kind"], d["discussion_reason"], d["title_similarity"] = classify(d, a.discussion_words, a.disc_max_delay, a.regular_iqr, a.instant_delay, a.title_sim)
    fam = families(d, a.min_members)

    a.out.mkdir(parents=True, exist_ok=True)
    review = d[d["kind"].isin(["instant_relay", "other", "discussion_possible"])].sort_values(["kind", "n_relays"], ascending=[True, False])
    for name, df in [("fast_mirror_channels", d.sort_values(["share_fast10", "n_forwarded"], ascending=False)),
                     ("fast_mirror_families", fam), ("fast_mirror_review", review)]:
        (a.out / name).mkdir(exist_ok=True)
        df.to_csv(a.out / name / f"{name}.csv", index=False, encoding="utf-8-sig")
    summary = pd.DataFrame([
        ("selected channels", len(d)), ("channels with a known top source", int(d["top_source"].notna().sum())),
        ("distinct sources followed", int(d["top_source"].nunique())),
        (f"families with >= {a.min_members} followers", len(fam)),
        ("channels in those families", int(d["top_source"].isin(fam["top_source"]).sum())),
        ("median delay to source (s)", float(d["delay_median_s"].median())),
        (f"near-constant lag (IQR <= {a.regular_iqr:g} s)", int((d["lag_type"] == "near-constant lag").sum())),
        ("source is itself a selected channel", int(d["source_is_selected"].sum())),
        ("with public title in metadata", int(d["title"].fillna("").ne("").sum()))]
        + [(f"kind: {k}", int((d["kind"] == k).sum())) for k in ["linked_discussion", "discussion_possible", "instant_relay", "other"]]
        + [("channels left to review (not linked_discussion)", len(review))], columns=["metric", "value"])
    (a.out / "fast_mirror_summary").mkdir(exist_ok=True)
    summary.to_csv(a.out / "fast_mirror_summary" / "fast_mirror_summary.csv", index=False)
    if not a.no_charts:
        charts(d, fam, a.figdir)
    print(summary.to_string(index=False))
    show = ["family_rank", "top_source", "n_followers", "relays_total", "delay_median_s", "delay_iqr_median_s", "first_month", "last_month"]
    print("\nlargest families:\n", fam[show].head(15).to_string(index=False))
    cols = [c for c in ["channel_id", "title", "source_title", "kind", "delay_median_s", "delay_iqr_s", "n_relays", "first_month", "last_month"] if c in review]
    print("\nto review (%d), by kind:\n" % len(review), review[cols].head(30).to_string(index=False))
    return d, fam


def selftest():
    rng = np.random.default_rng(3)
    rows = []
    for ch in range(1, 9):                           # 8 mirrors of source 900, constant ~3 s lag
        for _ in range(60):
            rows.append((900, ch, 3 + rng.integers(0, 2), "2024-03-01T10:00:00"))
    for ch in (20, 21):                              # 2 channels, variable lag, source 901
        for _ in range(60):
            rows.append((901, ch, int(rng.integers(1, 9)), "2023-01-01T10:00:00"))
    for ch in (30, 31):                              # slow channels (not selected)
        for _ in range(60):
            rows.append((902, ch, int(rng.integers(500, 5000)), "2023-01-01T10:00:00"))
    ch = pd.DataFrame(rows, columns=["origin_channel", "dest_channel", "delay_s", "date"])
    beh = pd.DataFrame({"channel_id": sorted(ch.dest_channel.unique())})
    beh["n_posts"], beh["n_forwarded"], beh["sec_mode_share"] = 100, 60, 0.02
    beh["share_fast10"] = np.where(beh.channel_id < 30, 0.95, 0.0)
    beh["top_origin_share"] = 1.0
    a = argparse.Namespace(fast_min=0.44, src_min=0.9, min_forwarded=30)
    sel = beh[(beh.share_fast10 >= a.fast_min) & (beh.top_origin_share >= a.src_min)]
    ids = set(sel.channel_id)
    prof = follow_profile(ch, ids)
    assert set(prof.channel_id) == ids and set(prof[prof.channel_id <= 8].top_source) == {900}
    assert (prof[prof.channel_id <= 8].delay_iqr_s <= 1).all() and prof[prof.channel_id <= 8].delay_median_s.between(3, 4).all()
    d = sel.merge(prof, on="channel_id")
    d["delay_iqr_s"] = d["delay_iqr_s"]
    f = families(d, 3)
    assert len(f) == 1 and f.loc[0, "top_source"] == 900 and f.loc[0, "n_followers"] == 8, f
    assert prof.first_month.eq("2024-03").sum() == 8 and prof.loc[prof.channel_id == 20, "first_month"].iloc[0] == "2023-01"
    t = pd.DataFrame({"title": ["ФНС России Chat", "Дом Комментарии", "Alerts relay", "Plain", None, "Slow chat", "Республика Коми", "Моя Россия"],
                      "source_title": ["ФНС России", "Дом", "Alerts", "Other", "x", "Slow", "Республика Коми Z", "Партизаны"],
                      "delay_median_s": [3, 3, 0, 3, 8, 3, 3, 0], "delay_iqr_s": [0, 0, 1, 0, 1, 40, 1, 1]})
    k, why, sim = classify(t, DISCUSSION_WORDS, 5.0, 5.0, 1.0)
    assert list(k) == ["linked_discussion", "linked_discussion", "instant_relay", "discussion_possible", "other", "other",
                       "linked_discussion", "instant_relay"], list(k)
    assert why.iloc[6] == "similar title" and why.iloc[0] == "title word" and sim.iloc[6] == 1.0
    print("selftest OK")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--behavior", type=Path, default=Path("telescope_pipeline_files/gold/channel_behavior"))
    ap.add_argument("--chains", type=Path, default=Path("telescope_pipeline_files/gold/chains"))
    ap.add_argument("--metadata", type=Path, default=Path("telescope_files/Source_Channel_Metadata.csv"))
    ap.add_argument("--communities", type=Path, default=Path("bigdata_pipeline/analysis/communities_v2/communities_leiden/communities_leiden.csv"))
    ap.add_argument("--languages", type=Path, default=Path("telescope_files/Channel_Language.csv"))
    ap.add_argument("--geo", type=Path, default=Path("bigdata_pipeline/analysis/geo/channel_geo/channel_geo.csv"))
    ap.add_argument("--out", type=Path, default=Path("bigdata_pipeline/analysis/suspicious/mirrors"))
    ap.add_argument("--figdir", type=Path, default=Path("bigdata_pipeline/analysis/figures/suspicious"))
    ap.add_argument("--fast-min", type=float, default=0.44, help="min share of forwards relayed within 10 s")
    ap.add_argument("--src-min", type=float, default=0.9, help="min share of forwards from the single top source")
    ap.add_argument("--min-forwarded", type=int, default=30)
    ap.add_argument("--min-members", type=int, default=3, help="min followers to call a source a family")
    ap.add_argument("--regular-iqr", type=float, default=5.0, help="delay IQR (s) under which the lag is called near-constant")
    ap.add_argument("--discussion-words", default=DISCUSSION_WORDS, help="regex of title words of a linked discussion group")
    ap.add_argument("--disc-max-delay", type=float, default=5.0, help="max median delay (s) of a linked discussion group")
    ap.add_argument("--title-sim", type=float, default=0.5, help="min word overlap between title and source title to call a channel a discussion group")
    ap.add_argument("--instant-delay", type=float, default=1.0, help="median delay (s) at or under which a relay is called instant (same second)")
    ap.add_argument("--no-charts", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    selftest() if a.selftest else run(a)


if __name__ == "__main__":
    main()