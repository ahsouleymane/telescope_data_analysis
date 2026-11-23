#!/usr/bin/env python3
"""
CANDIDATES TO REVIEW BY HAND (theme 5).

Builds one table of the channels worth reading one by one, from the output of suspicious_trends.py:
  A. channels with at least --min-behaviour behaviour indicators (default 3);
  B. channels in a tight coordinated group that also have at least one behaviour indicator.
Each row gets context to judge it quickly: title / username / audience, top source and its title,
delay quartiles to that source, active months, community, language, the kind given by fast_mirror_channels.py
when available (linked_discussion ...), the tight group (rank, size, density), and two EMPTY columns
(manual_label, note) to fill in while reading.

Indicators overlap (a near-instant relay gives a small delay spread), so the score only sorts the list;
it does not measure how suspicious a channel is. Nothing here says why a channel behaves like this.

Outputs in --out: review_candidates (CSV), review_summary (CSV, counts by kind and indicator); both printed.
Usage: python3 review_candidates.py [--min-behaviour 3]
"""
import argparse
import importlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))


def select(sus, min_behaviour):
    """Rows of group A (many behaviour indicators) and B (tight group + at least one behaviour indicator)."""
    a = sus["score_behaviour"] >= min_behaviour
    b = (sus["score_coordination"] >= 1) & (sus["score_behaviour"] >= 1)
    out = sus[a | b].copy()
    out["selection"] = np.select([a[a | b] & b[a | b], a[a | b]], ["behaviour+group", "behaviour"], default="group+behaviour")
    return out


def add_groups(d, members, groups):
    """Attach the best (tightest) group of each channel: rank, size, density."""
    if members is None or groups is None or not len(members):
        return d
    g = groups[["group_rank", "n_channels", "density", "median_dt_s"]].rename(
        columns={"n_channels": "group_size", "density": "group_density", "median_dt_s": "group_median_dt_s"})
    m = members[["channel_id", "group_rank"]].merge(g, on="group_rank")
    m = m.sort_values("group_density", ascending=False).drop_duplicates("channel_id")
    return d.merge(m, on="channel_id", how="left")


def run(a):
    fm = importlib.import_module(a.module)
    sus = fm.read_table(a.suspicious)
    if sus is None:
        raise SystemExit(f"nothing found in {a.suspicious}: run suspicious_trends.py first")
    d = select(sus, a.min_behaviour)
    ids = set(d["channel_id"].astype("int64"))
    print(f"{len(d):,} channels to review "
          f"({int((d['selection'] != 'group+behaviour').sum())} with {a.min_behaviour}+ behaviour indicators, "
          f"{int((d['selection'] != 'behaviour').sum())} in a tight group with 1+ behaviour indicator)")

    d = add_groups(d, fm.read_table(a.members), fm.read_table(a.groups))
    prof = fm.follow_profile(fm.read_chains(a.chains, ids), ids)
    d = d.merge(prof.drop(columns=["n_relays"], errors="ignore"), on="channel_id", how="left", suffixes=("", "_src"))
    info_ids = ids | set(prof["top_source"].dropna().astype("int64"))
    info = fm.public_info(a.metadata, info_ids)
    d = d.merge(info, on="channel_id", how="left")
    d = d.merge(info[["channel_id", "title"]].rename(columns={"channel_id": "top_source", "title": "source_title"}),
                on="top_source", how="left")
    d = fm.attach_context(d, a.communities, a.languages, a.geo)
    if a.selected and Path(a.selected).exists():
        k = pd.read_csv(a.selected)[["channel_id", "kind"]].drop_duplicates("channel_id")
        d = d.merge(k, on="channel_id", how="left")
    d["kind"] = d["kind"].fillna("not_selected") if "kind" in d else "not_selected"
    d["manual_label"] = ""
    d["note"] = ""

    d = d.sort_values(["score_behaviour", "score", "n_posts"], ascending=False).reset_index(drop=True)
    cols = ["channel_id", "title", "username", "participants_count", "selection", "kind", "score_behaviour", "score_coordination",
            "reasons", "n_posts", "n_forwarded", "n_origins", "top_source", "source_title", "top_source_share",
            "delay_p25_s", "delay_median_s", "delay_p75_s", "first_month", "last_month", "n_active_months",
            "group_rank", "group_size", "group_density", "group_median_dt_s", "community", "language", "city_key",
            "manual_label", "note"]
    d = d[[c for c in cols if c in d]]
    a.out.mkdir(parents=True, exist_ok=True)
    for name, df in [("review_candidates", d)]:
        (a.out / name).mkdir(exist_ok=True)
        df.to_csv(a.out / name / f"{name}.csv", index=False, encoding="utf-8-sig")

    rows = [("channels to review", len(d))]
    rows += [(f"selection: {k}", int(v)) for k, v in d["selection"].value_counts().items()]
    rows += [(f"kind: {k}", int(v)) for k, v in d["kind"].value_counts().items()]
    ind = d["reasons"].str.split(", ").explode().value_counts()
    rows += [(f"indicator: {k}", int(v)) for k, v in ind.items()]
    summ = pd.DataFrame(rows, columns=["metric", "value"])
    (a.out / "review_summary").mkdir(exist_ok=True)
    summ.to_csv(a.out / "review_summary" / "review_summary.csv", index=False)
    print(summ.to_string(index=False))
    show = [c for c in ["channel_id", "title", "kind", "score_behaviour", "score_coordination", "n_posts", "top_source_share",
                        "delay_median_s", "group_rank"] if c in d]
    print("\nfirst 25:\n", d[show].head(25).to_string(index=False))
    print(f"\nfile to fill in by hand: {a.out / 'review_candidates' / 'review_candidates.csv'}")


def selftest():
    sus = pd.DataFrame({"channel_id": [1, 2, 3, 4], "score_behaviour": [4, 2, 1, 3], "score_coordination": [0, 1, 1, 1],
                        "score": [4, 3, 2, 4], "reasons": ["a, b", "a", "a", "a, b, c"], "n_posts": [10] * 4})
    s = select(sus, 3).set_index("channel_id")
    assert set(s.index) == {1, 2, 3, 4}, s
    assert s.loc[1, "selection"] == "behaviour" and s.loc[2, "selection"] == "group+behaviour"
    assert s.loc[4, "selection"] == "behaviour+group"
    assert select(sus, 4).set_index("channel_id").loc[4, "selection"] == "group+behaviour"
    grp = pd.DataFrame({"group_rank": [1, 2], "n_channels": [10, 5], "density": [0.9, 0.6], "median_dt_s": [1, 2]})
    mem = pd.DataFrame({"channel_id": [2, 2, 3], "group_rank": [1, 2, 2]})
    r = add_groups(s.reset_index(), mem, grp).set_index("channel_id")
    assert r.loc[2, "group_rank"] == 1 and r.loc[3, "group_size"] == 5 and np.isnan(r.loc[1, "group_rank"])
    print("selftest OK")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    base = Path("bigdata_pipeline/analysis/suspicious")
    ap.add_argument("--suspicious", type=Path, default=base / "suspicious_channels")
    ap.add_argument("--members", type=Path, default=base / "coordinated_members")
    ap.add_argument("--groups", type=Path, default=base / "coordinated_groups")
    ap.add_argument("--chains", type=Path, default=Path("telescope_pipeline_files/gold/chains"))
    ap.add_argument("--metadata", type=Path, default=Path("telescope_files/Source_Channel_Metadata.csv"))
    ap.add_argument("--communities", type=Path, default=Path("bigdata_pipeline/analysis/communities_v2/communities_leiden/communities_leiden.csv"))
    ap.add_argument("--languages", type=Path, default=Path("telescope_files/Channel_Language.csv"))
    ap.add_argument("--geo", type=Path, default=Path("bigdata_pipeline/analysis/geo/channel_geo/channel_geo.csv"))
    ap.add_argument("--selected", type=Path, default=base / "mirrors/fast_mirror_channels/fast_mirror_channels.csv")
    ap.add_argument("--module", default="fast_mirror_channels", help="module holding read_table, follow_profile, public_info ...")
    ap.add_argument("--min-behaviour", type=int, default=3, help="min behaviour indicators for group A")
    ap.add_argument("--out", type=Path, default=base / "review")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    selftest() if a.selftest else run(a)


if __name__ == "__main__":
    main()