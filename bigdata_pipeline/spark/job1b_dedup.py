#!/usr/bin/env python3
"""
JOB 1b - REMOVE DUPLICATED MESSAGES.

The raw files repeat some messages: the same (channel, message id) appears 2 to 7 times inside one file,
sometimes with different counters. A Telegram message id is unique inside a channel, so one copy is kept.

Input : <out>/clean            (Parquet from job1_clean.py, left untouched)
Output: <out>/clean_dedup      (Parquet, same columns, one row per (dest_channel, msg_id))
        <out>/dedup_log.csv    messages before / after
        <out>/dedup_report.csv which columns differ between copies of one message

Rule when copies differ: keep the copy that has forward information (origin_channel known), then the one with
the most views, then the most forwards, then the latest date. dedup_report.csv shows how often each column
differs, so the rule can be checked.

Jobs 2-4 read clean_dedup/ automatically when it exists.

Usage: python3 job1b_dedup.py --out ~/telescope_v2 [--clean DIR] [--no-report] [--no-verify]
"""
import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

KEY = ["dest_channel", "msg_id"]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--clean", type=Path, default=None)
    ap.add_argument("--no-report", action="store_true", help="skip the report on differing copies")
    ap.add_argument("--no-verify", action="store_true", help="skip the final uniqueness check")
    args = ap.parse_args()
    clean = args.clean or args.out / "clean"
    dst = args.out / "clean_dedup"

    from pyspark.sql import Window
    from pyspark.sql import functions as F
    from spark_session import get_spark
    spark = get_spark("telescope-job1b-dedup")

    c = spark.read.parquet(str(clean))
    n_in = c.count()
    print(f"messages in clean: {n_in:,}")

    rank = Window.partitionBy(*KEY).orderBy(
        F.col("origin_channel").isNotNull().desc(),
        F.col("views").desc_nulls_last(),
        F.col("forwards").desc_nulls_last(),
        F.col("ts").desc())
    (c.withColumn("_rank", F.row_number().over(rank)).where(F.col("_rank") == 1).drop("_rank")
      .write.mode("overwrite").parquet(str(dst)))
    d = spark.read.parquet(str(dst))
    n_out = d.count()
    print(f"messages in clean_dedup: {n_out:,} ({n_in - n_out:,} copies removed, {(n_in - n_out) / n_in:.2%})")
    with open(args.out / "dedup_log.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["messages_before", "messages_after", "copies_removed"])
        w.writerow([n_in, n_out, n_in - n_out])

    if not args.no_verify:
        n_keys = d.select(*KEY).distinct().count()
        print("uniqueness check:", "OK" if n_keys == n_out else f"ERROR {n_keys:,} distinct keys for {n_out:,} rows")

    if not args.no_report:
        cols = [x for x in c.columns if x not in KEY]
        flags = [F.when(F.size(F.collect_set(F.coalesce(F.col(x).cast("string"), F.lit("<null>")))) > 1, 1)
                  .otherwise(0).alias(x) for x in cols]
        g = c.groupBy(*KEY).agg(F.count(F.lit(1)).alias("_n"), *flags).where(F.col("_n") > 1)
        row = g.agg(F.count(F.lit(1)).alias("duplicated_keys"), F.sum(F.col("_n") - 1).alias("extra_copies"),
                    *[F.sum(F.col(x)).alias(x) for x in cols]).collect()[0].asDict()
        print("columns that differ between copies (number of duplicated messages):")
        with open(args.out / "dedup_report.csv", "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["measure", "value"])
            for k, v in row.items():
                w.writerow([k, v])
                print(f"  {k}: {v}")
    spark.stop()


if __name__ == "__main__":
    main()
