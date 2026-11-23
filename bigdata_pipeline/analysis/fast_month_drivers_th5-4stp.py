#!/usr/bin/env python3
"""
WHO PRODUCES THE FAST RELAYS OF A GIVEN MONTH?

For a month with a jump in instant relays (default 2024-09) compared with a reference month (default 2024-08):
  * how concentrated the fast relays (<= 10 s after the original post) are: share of the top 1, 10, 50, 100
    channels, and how many channels make half of them;
  * which channels explain the JUMP: excess = fast relays in the month - fast relays in the reference month;
  * which source channels receive those fast relays;
  * title / username of the public channels, and the kind assigned by fast_mirror_channels.py when available.

Reads gold/chains (columns dest_channel, origin_channel, delay_s, date) with a month filter.
Nothing here says why a channel relays fast: this only says who and how many.

Outputs in --out: month_drivers_channels (top --top by excess), month_drivers_sources, month_drivers_summary;
figure month_drivers_concentration.png in --figdir.
Usage: python3 fast_month_drivers.py [--month 2024-09] [--ref 2024-08]
"""
import argparse
import glob
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))


def next_month(m):
    y, mo = map(int, m.split("-"))
    return f"{y + (mo == 12)}-{(mo % 12) + 1:02d}"


def relays(path, month):
    """Relays dated in `month` (delay >= 0): dest_channel, origin_channel, delay_s."""
    cols = ["dest_channel", "origin_channel", "delay_s", "date"]
    lo, hi = month, next_month(month)
    p = Path(path)
    if glob.glob(str(p / "*.parquet")) or p.suffix == ".parquet":
        import pyarrow.dataset as ds
        t = ds.dataset(str(p), format="parquet").to_table(
            columns=cols, filter=(ds.field("date") >= lo) & (ds.field("date") < hi))
        d = t.to_pandas()
    else:
        parts = []
        for f in sorted(glob.glob(str(p / "*.csv"))) if p.is_dir() else [str(p)]:
            for c in pd.read_csv(f, usecols=cols, chunksize=1_000_000):
                parts.append(c[(c["date"].astype(str) >= lo) & (c["date"].astype(str) < hi)])
        d = pd.concat(parts, ignore_index=True)
    return d[d["delay_s"] >= 0].drop(columns="date")


def per_channel(d, fast_s):
    f = d[d["delay_s"] <= fast_s]
    out = d.groupby("dest_channel").size().rename("n_relays").to_frame()
    out["n_fast"] = f.groupby("dest_channel").size()
    out["n_fast"] = out["n_fast"].fillna(0).astype(int)
    top = (f.groupby(["dest_channel", "origin_channel"]).size().rename("k").reset_index()
           .sort_values(["dest_channel", "k"], ascending=[True, False]).drop_duplicates("dest_channel")
           .set_index("dest_channel"))
    out["top_source"] = top["origin_channel"]
    out["top_source_share_of_fast"] = (top["k"] / out["n_fast"].replace(0, np.nan)).round(3)
    out["fast_share"] = (out["n_fast"] / out["n_relays"]).round(3)
    return out


def concentration(counts, ks=(1, 10, 50, 100)):
    c = np.sort(np.asarray(counts, dtype=float))[::-1]
    c = c[c > 0]
    tot = c.sum()
    rows = [(f"share of the top {k} channels (%)", round(100 * c[:k].sum() / tot, 1)) for k in ks if tot > 0]
    rows.append(("channels that make half of the total", int(np.searchsorted(np.cumsum(c), tot / 2) + 1) if tot > 0 else 0))
    rows.append(("channels with at least one", len(c)))
    return rows, c


def run(a):
    m, r = relays(a.chains, a.month), relays(a.chains, a.ref)
    pm, pr = per_channel(m, a.fast), per_channel(r, a.fast)
    x = pm.join(pr[["n_relays", "n_fast"]].add_suffix("_ref"), how="outer").fillna(0)
    for c in ["n_relays", "n_fast", "n_relays_ref", "n_fast_ref"]:
        x[c] = x[c].astype(int)
    x["excess_fast"] = x["n_fast"] - x["n_fast_ref"]
    x = x.reset_index().rename(columns={"index": "channel_id", "dest_channel": "channel_id"})
    tot_m, tot_r = int(x["n_fast"].sum()), int(x["n_fast_ref"].sum())
    pos = x[x["excess_fast"] > 0]["excess_fast"]
    rows = [(f"relays in {a.month}", len(m)), (f"fast relays in {a.month}", tot_m),
            (f"fast relays in {a.ref}", tot_r), ("fast-relay increase", tot_m - tot_r),
            (f"fast share {a.month} (%)", round(100 * tot_m / max(len(m), 1), 2)),
            (f"fast share {a.ref} (%)", round(100 * tot_r / max(len(r), 1), 2))]
    conc, curve = concentration(x["n_fast"])
    rows += [(f"{k} in {a.month}", v) for k, v in conc]
    cexc, _ = concentration(pos)
    rows += [(f"excess: {k}", v) for k, v in cexc]
    summary = pd.DataFrame(rows, columns=["metric", "value"])

    top = x.sort_values("excess_fast", ascending=False).head(a.top).copy()
    ids = set(top["channel_id"].astype("int64")) | set(top["top_source"].dropna().astype("int64"))
    try:
        import importlib
        mod = importlib.import_module("fast_mirror_channels_th5-2stp")
        public_info = mod.public_info
        info = public_info(a.metadata, ids)
    except Exception as e:                           # metadata is optional context
        print("metadata not read:", e)
        info = pd.DataFrame(columns=["channel_id", "title", "username", "participants_count"])
    top = top.merge(info, on="channel_id", how="left")
    top = top.merge(info[["channel_id", "title"]].rename(columns={"channel_id": "top_source", "title": "source_title"}), on="top_source", how="left")
    if a.selected and Path(a.selected).exists():
        k = pd.read_csv(a.selected)[["channel_id", "kind"]]
        top = top.merge(k, on="channel_id", how="left")
    src = (m[m["delay_s"] <= a.fast].groupby("origin_channel").agg(n_fast=("dest_channel", "size"), n_followers=("dest_channel", "nunique"))
           .sort_values("n_fast", ascending=False).head(100).reset_index())
    src = src.merge(info.rename(columns={"channel_id": "origin_channel"}), on="origin_channel", how="left")
    a.out.mkdir(parents=True, exist_ok=True)
    for name, df in [("month_drivers_channels", top), ("month_drivers_sources", src), ("month_drivers_summary", summary)]:
        (a.out / name).mkdir(exist_ok=True)
        df.to_csv(a.out / name / f"{name}.csv", index=False, encoding="utf-8-sig")
    if not a.no_charts:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.plot(np.arange(1, len(curve) + 1), np.cumsum(curve) / curve.sum() * 100, color="#1F4E79")
        ax.set(xscale="log", xlabel="channels, ranked by fast relays", ylabel="cumulative share of fast relays (%)",
               title=f"Concentration of fast relays, {a.month}")
        fig.tight_layout()
        a.figdir.mkdir(parents=True, exist_ok=True)
        fig.savefig(a.figdir / "month_drivers_concentration.png", dpi=150)
        plt.close(fig)
    print(summary.to_string(index=False))
    cols = [c for c in ["channel_id", "title", "source_title", "kind", "n_fast", "n_fast_ref", "excess_fast", "fast_share", "top_source_share_of_fast"] if c in top]
    print("\nchannels that explain the jump:\n", top[cols].head(25).to_string(index=False))
    print("\nsources receiving most fast relays:\n", src.head(10).to_string(index=False))


def selftest():
    import tempfile
    rng = np.random.default_rng(0)
    rows = []
    for ch in range(1, 301):                        # ordinary channels: few fast relays, same in both months
        for mth in ("2024-08", "2024-09"):
            rows += [(ch, 7000 + ch % 20, int(rng.choice([4, 400], p=[0.03, 0.97])), f"{mth}-10T10:00:00") for _ in range(30)]
    rows += [(900, 8000, 2, "2024-09-12T10:00:00")] * 4000     # one driver in September only
    rows += [(901, 8001, 2, "2024-09-13T10:00:00")] * 1000
    with tempfile.TemporaryDirectory() as t:
        pd.DataFrame(rows, columns=["dest_channel", "origin_channel", "delay_s", "date"]).to_csv(Path(t) / "c.csv", index=False)
        m, r = relays(t, "2024-09"), relays(t, "2024-08")
    pm, pr = per_channel(m, 10), per_channel(r, 10)
    assert pm.loc[900, "n_fast"] == 4000 and pm.loc[900, "top_source"] == 8000 and 900 not in pr.index
    conc, _ = concentration(pm["n_fast"])
    d = dict(conc)
    assert d["share of the top 1 channels (%)"] > 50 and d["channels that make half of the total"] <= 2, d
    assert next_month("2024-12") == "2025-01" and next_month("2024-09") == "2024-10"
    print("selftest OK")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--chains", type=Path, default=Path("telescope_pipeline_files/gold/chains"))
    ap.add_argument("--month", default="2024-09")
    ap.add_argument("--ref", default="2024-08")
    ap.add_argument("--fast", type=int, default=10, help="seconds after the original post")
    ap.add_argument("--top", type=int, default=500)
    ap.add_argument("--metadata", type=Path, default=Path("telescope_files/Source_Channel_Metadata.csv"))
    ap.add_argument("--selected", type=Path, default=Path("bigdata_pipeline/analysis/suspicious/mirrors/fast_mirror_channels/fast_mirror_channels.csv"))
    ap.add_argument("--out", type=Path, default=Path("bigdata_pipeline/analysis/suspicious/mirrors"))
    ap.add_argument("--figdir", type=Path, default=Path("bigdata_pipeline/analysis/figures/suspicious"))
    ap.add_argument("--no-charts", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    selftest() if a.selftest else run(a)


if __name__ == "__main__":
    main()