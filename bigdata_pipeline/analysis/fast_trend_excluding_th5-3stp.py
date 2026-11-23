#!/usr/bin/env python3
"""
IS THE RISE OF INSTANT RELAYS REAL, OR DUE TO A FEW CHANNELS?

Recomputes the monthly share of relays made within 10 s (and 60 s) of the original post, twice:
  all     : every relay in gold/chains
  without : the same, leaving out the relays made BY the channels listed in fast_mirror_channels.csv
            (default: all selected channels; --kinds limits it, e.g. --kinds linked_discussion,discussion_possible)
and reports how much of the fast relays of each month those channels explain.

Reads gold/chains in batches (columns dest_channel, delay_s, date), so memory stays small.
Both series use the same table (relays with a known original post), so they are comparable with each other;
the absolute level differs a little from forward_speed_monthly, which also counts relays without post id.

Outputs in --out: fast_trend_excluding (CSV), figure fast_trend_excluding.png; the last months are printed.
Usage: python3 fast_trend_excluding.py [--kinds linked_discussion,discussion_possible,instant_relay,other]
"""
import argparse
import glob
from pathlib import Path

import numpy as np
import pandas as pd


def batches(path):
    p = Path(path)
    cols = ["dest_channel", "delay_s", "date"]
    if glob.glob(str(p / "*.parquet")) or p.suffix == ".parquet":
        import pyarrow.dataset as ds
        for b in ds.dataset(str(p), format="parquet").scanner(columns=cols, batch_size=1_000_000).to_batches():
            yield b.to_pandas()
    else:
        for f in sorted(glob.glob(str(p / "*.csv"))) if p.is_dir() else [str(p)]:
            for d in pd.read_csv(f, usecols=cols, chunksize=1_000_000):
                yield d


def monthly(path, excluded):
    acc = {}
    for d in batches(path):
        d = d[d["delay_s"] >= 0]
        month = d["date"].astype(str).str[:7]
        out = d["dest_channel"].isin(excluded)
        f10, f60 = d["delay_s"] <= 10, d["delay_s"] <= 60
        t = pd.DataFrame({"month": month, "n": 1, "f10": f10.astype(int), "f60": f60.astype(int),
                          "n_out": out.astype(int), "f10_out": (f10 & out).astype(int), "f60_out": (f60 & out).astype(int)})
        for m, row in t.groupby("month").sum(numeric_only=True).iterrows():
            acc[m] = acc.get(m, 0) + row
    r = pd.DataFrame(acc).T.rename_axis("month").reset_index()
    r = r.rename(columns={"n": "n_all", "f10": "fast10_all", "f60": "fast60_all", "n_out": "n_selected", "f10_out": "fast10_selected", "f60_out": "fast60_selected"})
    r["n_without"] = r["n_all"] - r["n_selected"]
    r["fast10_without"] = r["fast10_all"] - r["fast10_selected"]
    r["fast60_without"] = r["fast60_all"] - r["fast60_selected"]
    r["fast10_pct_all"] = (100 * r["fast10_all"] / r["n_all"]).round(2)
    r["fast10_pct_without"] = (100 * r["fast10_without"] / r["n_without"].replace(0, np.nan)).round(2)
    r["fast60_pct_all"] = (100 * r["fast60_all"] / r["n_all"]).round(2)
    r["fast60_pct_without"] = (100 * r["fast60_without"] / r["n_without"].replace(0, np.nan)).round(2)
    r["share_of_fast10_from_selected_pct"] = (100 * r["fast10_selected"] / r["fast10_all"].replace(0, np.nan)).round(1)
    return r.sort_values("month").reset_index(drop=True)


def chart(r, figdir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(10, 4))
    x = pd.to_datetime(r["month"] + "-01")
    ax.plot(x, r["fast10_pct_all"], color="#C0392B", label="all channels")
    ax.plot(x, r["fast10_pct_without"], color="#1F4E79", label="without the selected channels")
    ax.set(ylabel="% of relays within 10 s", title="Instant relays per month: with and without the selected channels")
    ax.legend()
    fig.tight_layout()
    Path(figdir).mkdir(parents=True, exist_ok=True)
    fig.savefig(Path(figdir) / "fast_trend_excluding.png", dpi=150)
    plt.close(fig)


def selftest():
    import tempfile
    rng = np.random.default_rng(0)
    rows = []
    for m in ["2024-06", "2024-07"]:
        for ch in range(1, 200):                      # ordinary channels: 2 % instant
            rows += [(ch, int(rng.choice([5, 500], p=[0.02, 0.98])), f"{m}-10T10:00:00") for _ in range(20)]
    for ch in (900, 901):                             # selected channels: instant relays only in July
        rows += [(ch, 3, "2024-07-11T10:00:00")] * 2000
        rows += [(ch, 900, "2024-06-11T10:00:00")] * 20
    with tempfile.TemporaryDirectory() as t:
        pd.DataFrame(rows, columns=["dest_channel", "delay_s", "date"]).to_csv(Path(t) / "c.csv", index=False)
        r = monthly(t, {900, 901}).set_index("month")
    assert r.loc["2024-07", "fast10_pct_all"] > 40 and abs(r.loc["2024-07", "fast10_pct_without"] - 2) < 1.5, r.T
    assert r.loc["2024-07", "share_of_fast10_from_selected_pct"] > 95 and r.loc["2024-06", "fast10_pct_all"] < 5
    print("selftest OK")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--chains", type=Path, default=Path("telescope_pipeline_files/gold/chains"))
    ap.add_argument("--selected", type=Path, default=Path("bigdata_pipeline/analysis/suspicious/mirrors/fast_mirror_channels/fast_mirror_channels.csv"))
    ap.add_argument("--kinds", default=None, help="comma-separated kinds to leave out (default: all selected channels)")
    ap.add_argument("--out", type=Path, default=Path("bigdata_pipeline/analysis/suspicious/mirrors"))
    ap.add_argument("--figdir", type=Path, default=Path("bigdata_pipeline/analysis/figures/suspicious"))
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    s = pd.read_csv(a.selected)
    if a.kinds:
        s = s[s["kind"].isin(a.kinds.split(","))]
    excluded = set(s["channel_id"].astype("int64"))
    print(f"leaving out the relays of {len(excluded):,} channels" + (f" (kinds: {a.kinds})" if a.kinds else ""))
    r = monthly(a.chains, excluded)
    (a.out / "fast_trend_excluding").mkdir(parents=True, exist_ok=True)
    r.to_csv(a.out / "fast_trend_excluding" / "fast_trend_excluding.csv", index=False)
    chart(r, a.figdir)
    cols = ["month", "n_all", "fast10_pct_all", "fast10_pct_without", "share_of_fast10_from_selected_pct", "fast60_pct_all", "fast60_pct_without"]
    print(r[cols].tail(15).to_string(index=False))


if __name__ == "__main__":
    main()