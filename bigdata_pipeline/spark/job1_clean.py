#!/usr/bin/env python3
"""
JOB 1 - CLEAN: raw Telegram messages (JSONL or ZIP of JSONL) -> Parquet.

Reads the raw disk (read-only) and writes ONE small typed Parquet dataset per
batch folder on the internal disk:

    <out>/clean/batch=<batch_folder>/part-*.parquet      (12 files per batch)
    <out>/clean_log.csv                                  (one line per batch)

--raw can be a folder of .jsonl, a folder of .zip, one .zip, or a mix. The
.jsonl files inside a zip are read straight from the archive, nothing is
extracted. Spark has no built-in zip reader, so the files are distributed to the
Spark tasks as a list and parsed with the same tested Python code
(clean_records.py); Spark then handles the typed DataFrame and the Parquet
writing. 345 GB of JSON become a few GB of Parquet.

Resume: a batch that is already complete (marker + same number of files) is
skipped, so you can interrupt and relaunch, or add batches later in any order.
A batch is re-done if its number of input files changed, or with --force.
--limit N processes only the first N files and writes to <out>/clean_trial
(never mixed with the real data).

Usage:
    python3 job1_clean.py --raw /media/<disk>/telescope_raw --out ~/telescope_v2 --limit 50
    python3 job1_clean.py --raw /media/<disk>/telescope_raw --out ~/telescope_v2
    python3 job1_clean.py --raw /path/to/folder_of_zips   --out ~/telescope_v2
"""
import argparse
import csv
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from clean_records import CLEAN_COLUMNS, clean_row  # noqa: E402
from inputs import list_inputs, open_text            # noqa: E402


def make_schema():
    from pyspark.sql.types import LongType, StringType, StructField, StructType
    return StructType([StructField(c, StringType() if c == "kind" else LongType(), True)
                       for c in CLEAN_COLUMNS])


def make_reader(acc_ok, acc_bad, acc_skip):
    """Function run by each Spark task: parse every file of its group."""
    def run(groups):
        for tasks in groups:
            for src, member, channel in tasks:
                n_ok = n_bad = n_skip = 0
                fin, closer = open_text(src, member)
                try:
                    for line in fin:
                        row, status = clean_row(line, channel)
                        if row is not None:
                            n_ok += 1
                            yield row
                        elif status == "bad_json":
                            n_bad += 1
                        else:
                            n_skip += 1
                finally:
                    closer.close()
                acc_ok.add(n_ok)
                acc_bad.add(n_bad)
                acc_skip.add(n_skip)
    return run


def balanced_groups(items, n_groups):
    """Biggest files first, each one given to the least loaded group (greedy balancing)."""
    import heapq
    ordered = sorted(items, key=lambda i: -i["size"])
    n = max(1, min(n_groups, len(ordered)))
    groups = [[] for _ in range(n)]
    heap = [(0, g) for g in range(n)]                  # (total size so far, group index)
    heapq.heapify(heap)
    for it in ordered:
        load, g = heapq.heappop(heap)
        groups[g].append((it["src"], it["member"], it["channel"]))
        heapq.heappush(heap, (load + it["size"], g))
    return groups


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--raw", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--limit", type=int, default=0, help="trial: first N files, writes to clean_trial/")
    ap.add_argument("--files-per-batch", type=int, default=12, help="Parquet files written per batch")
    ap.add_argument("--force", action="store_true", help="redo batches even if already done")
    args = ap.parse_args()

    items = list(list_inputs(args.raw))
    if args.limit:
        items = items[:args.limit]
    batches = {}
    for it in items:
        batches.setdefault(it["batch"], []).append(it)
    print(f"{len(items):,} files in {len(batches)} batch(es)")

    from spark_session import get_spark
    spark = get_spark("telescope-job1-clean")
    sc = spark.sparkContext
    for f in ("clean_records.py", "inputs.py"):        # make the modules importable in workers
        sc.addPyFile(str(HERE / f))
    schema = make_schema()

    clean_dir = args.out / ("clean_trial" if args.limit else "clean")
    clean_dir.mkdir(parents=True, exist_ok=True)
    log_path = args.out / ("clean_trial_log.csv" if args.limit else "clean_log.csv")
    new_log = not log_path.exists()

    with open(log_path, "a", newline="", encoding="utf-8") as logf:
        log = csv.writer(logf)
        if new_log:
            log.writerow(["batch", "files", "messages_ok", "bad_json", "skipped", "gb_read", "seconds"])
        for batch, its in sorted(batches.items()):
            dst = clean_dir / f"batch={batch}"
            info = dst / "_info.json"
            if not args.force and (dst / "_SUCCESS").exists() and info.exists():
                if json.loads(info.read_text())["files"] == len(its):
                    print(f"[{batch}] already done, skipped")
                    continue
            t0 = time.time()
            acc = [sc.accumulator(0) for _ in range(3)]
            groups = balanced_groups(its, args.files_per_batch)
            rdd = (sc.parallelize(groups, len(groups))
                   .mapPartitions(make_reader(*acc)))
            df = spark.createDataFrame(rdd, schema, verifySchema=False)
            print(f"[{batch}] {len(its):,} files -> {len(groups)} tasks ...", flush=True)
            df.write.mode("overwrite").parquet(str(dst))
            info.write_text(json.dumps({"files": len(its)}))
            gb = sum(i["size"] for i in its) / 1e9
            dt = time.time() - t0
            log.writerow([batch, len(its), acc[0].value, acc[1].value, acc[2].value,
                          round(gb, 2), round(dt)])
            logf.flush()
            print(f"[{batch}] done: {acc[0].value:,} messages, {gb:,.1f} GB in {dt:,.0f}s "
                  f"({gb * 1000 / max(dt, 1e-9):,.0f} MB/s)", flush=True)
    spark.stop()
    print("done")


if __name__ == "__main__":
    main()
