#!/usr/bin/env python3
"""
JOB 3 - WEIGHTED, MONTHLY EDGES.

An edge A -> B in month M means: channel B forwarded messages whose original
author is channel A. Weight = number of such forwards.

Input : <out>/clean
Output: <out>/gold/edges_monthly   (Parquet): origin_channel, dest_channel, month, n_forwards
        <out>/gold/edges_monthly_csv/   with --csv (one CSV file with a header,
                                        for the v1 scripts that read CSV)

Usage: python3 job3_edges.py --out ~/telescope_v2 [--clean DIR] [--csv]
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--clean", type=Path, default=None)
    ap.add_argument("--csv", action="store_true", help="also write a single CSV file")
    args = ap.parse_args()
    clean = args.clean or args.out / "clean"

    from pyspark.sql import functions as F
    from spark_session import get_spark
    spark = get_spark("telescope-job3-edges")

    c = (spark.read.parquet(str(clean))
         .where((F.col("kind") == "channel") & F.col("origin_channel").isNotNull()
                & F.col("dest_channel").isNotNull() & F.col("ts").isNotNull()))
    edges = (c.withColumn("month", F.date_format(F.timestamp_seconds("ts"), "yyyy-MM"))
              .groupBy("origin_channel", "dest_channel", "month")
              .agg(F.count(F.lit(1)).alias("n_forwards")))

    dst = args.out / "gold" / "edges_monthly"
    edges.write.mode("overwrite").parquet(str(dst))
    res = spark.read.parquet(str(dst))
    total = res.agg(F.sum("n_forwards")).first()[0] or 0
    print(f"edges: {res.count():,} (origin, destination, month) triples; "
          f"{total:,} forwards in total -> {dst}")
    if args.csv:
        csv_dir = args.out / "gold" / "edges_monthly_csv"
        res.coalesce(1).write.mode("overwrite").option("header", True).csv(str(csv_dir))
        print(f"csv written to {csv_dir}")
    spark.stop()


if __name__ == "__main__":
    main()
