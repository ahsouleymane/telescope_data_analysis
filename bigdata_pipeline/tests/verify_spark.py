#!/usr/bin/env python3
"""
End-to-end check of the Spark pipeline on ONE channel file. Needs PySpark + Java.

    pip install pyspark pandas pyarrow
    python3 bigdata/tests/verify_spark.py /path/to/1961746451.jsonl

What it does (in a temporary folder, your data is not touched):
  1. runs jobs 1-4 on the file as a plain .jsonl
  2. runs job 1 again on a .zip made from it, and checks both give the same rows
  3. recomputes the expected numbers with plain json + Counter (no Spark) and
     compares them with the Parquet outputs: message counts, forward kinds,
     monthly edge weights, chain sizes / order / delays, channel statistics.

Prints OK for every check; any mismatch stops with the numbers.
Expected for the 1961746451 sample: 30,488 messages, 12,378 forwards,
12,286 from public channels, 12,276 chain relays, 176,057 total_forwards.
"""
import json
import subprocess
import sys
import tempfile
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
SPARK = HERE.parent / "spark"
sys.path.insert(0, str(SPARK))
from clean_records import to_epoch  # noqa: E402


def run(script, *args):
    cmd = [sys.executable, str(SPARK / script), *map(str, args)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout[-2000:], r.stderr[-3000:])
        raise SystemExit(f"FAILED: {script}")
    return r.stdout


def check(name, got, expected):
    if got != expected:
        raise SystemExit(f"MISMATCH {name}:\n  spark    = {got}\n  expected = {expected}")
    print(f"OK  {name}: {got}")


def expected_numbers(path):
    e = Counter()
    edges, chains = Counter(), defaultdict(list)
    for line in path.read_text(encoding="utf-8").splitlines():
        d = json.loads(line)
        if d.get("_") != "Message":
            continue
        e["messages"] += 1
        e["views"] += d.get("views") or 0
        e["total_forwards"] += d.get("forwards") or 0
        f = d.get("fwd_from")
        if not f:
            continue
        e["forwards"] += 1
        fid = f.get("from_id") or {}
        if fid.get("_") == "PeerChannel":
            e["channel_forwards"] += 1
            o = fid["channel_id"]
            ts = to_epoch(d["date"])
            edges[(o, d["peer_id"]["channel_id"], pd.Timestamp(ts, unit="s").strftime("%Y-%m"))] += 1
            if f.get("channel_post") is not None:
                chains[(o, f["channel_post"])].append((ts, d["peer_id"]["channel_id"], d["id"],
                                                       to_epoch(f.get("date"))))
                e["chain_relays"] += 1
    return e, edges, chains


def main():
    if len(sys.argv) != 2 or not Path(sys.argv[1]).exists():
        raise SystemExit(__doc__)
    sample = Path(sys.argv[1]).resolve()
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        raw = tmp / "raw" / "batch_1"
        raw.mkdir(parents=True)
        (raw / sample.name).write_bytes(sample.read_bytes())
        out, out_zip = tmp / "out", tmp / "out_zip"

        print("running jobs 1-4 on the plain file ...")
        run("job1_clean.py", "--raw", tmp / "raw", "--out", out)
        run("job2_chains.py", "--out", out)
        run("job3_edges.py", "--out", out)
        run("job4_stats.py", "--out", out)

        print("running job 1 on a zip of the same file ...")
        zpath = tmp / "lot.zip"
        with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
            z.write(sample, f"batch_1/{sample.name}")
        run("job1_clean.py", "--raw", zpath, "--out", out_zip)

        clean = pd.read_parquet(out / "clean")
        clean_zip = pd.read_parquet(out_zip / "clean")
        cols = ["dest_channel", "msg_id", "ts", "views", "forwards", "kind",
                "origin_channel", "origin_post", "origin_ts"]
        key = ["dest_channel", "msg_id"]
        same = (clean[cols].sort_values(key).reset_index(drop=True)
                .equals(clean_zip[cols].sort_values(key).reset_index(drop=True)))
        check("zip and plain file give identical rows", same, True)

        e, edges, chains = expected_numbers(sample)
        check("messages", len(clean), e["messages"])
        check("forwards", int((clean["kind"] != "").sum()), e["forwards"])
        check("forwards from public channels", int((clean["kind"] == "channel").sum()), e["channel_forwards"])
        check("views total", int(clean["views"].fillna(0).sum()), e["views"])

        ed = pd.read_parquet(out / "gold" / "edges_monthly")
        got_edges = {(int(r.origin_channel), int(r.dest_channel), r.month): int(r.n_forwards)
                     for r in ed.itertuples()}
        check("monthly edges", got_edges, dict(edges))

        ch = pd.read_parquet(out / "gold" / "chains")
        check("chain relays", len(ch), e["chain_relays"])
        sizes = ch.groupby(["origin_channel", "origin_post"]).size().to_dict()
        check("chain sizes", {k: int(v) for k, v in sizes.items()},
              {k: len(v) for k, v in chains.items()})
        check("n_relays column consistent",
              bool((ch.groupby(["origin_channel", "origin_post"])["n_relays"].transform("first")
                    == ch.groupby(["origin_channel", "origin_post"])["rank"].transform("max")).all()), True)
        sample_keys = list(chains)[:300]
        ok = True
        for k in sample_keys:
            g = ch[(ch.origin_channel == k[0]) & (ch.origin_post == k[1])].sort_values("rank")
            exp = sorted(chains[k])
            ok &= list(g["delay_s"]) == [t - o if o is not None else None for t, _, _, o in exp]
            ok &= list(g["rank"]) == list(range(1, len(exp) + 1))
        check("chain order and delays (300 chains)", ok, True)

        st = pd.read_parquet(out / "gold" / "channel_stats")
        row = st.iloc[0]
        check("stats: one channel", len(st), 1)
        check("stats: n_messages", int(row.n_messages), e["messages"])
        check("stats: n_forwarded_in", int(row.n_forwarded_in), e["forwards"])
        check("stats: from channels", int(row.n_forwarded_in_from_channels), e["channel_forwards"])
        check("stats: total_views", int(row.total_views), e["views"])
        check("stats: total_forwards", int(row.total_forwards), e["total_forwards"])
    print("\nALL CHECKS PASSED")


if __name__ == "__main__":
    main()
