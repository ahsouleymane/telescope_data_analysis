#!/usr/bin/env python3
"""
JOB 4 - CHANNEL STATISTICS.

Input : <out>/clean
Output: <out>/gold/channel_stats   (Parquet), one row per channel:

  channel_id, n_messages, n_forwarded_in, n_forwarded_in_from_channels,
  total_views, total_forwards, first_date, last_date

  n_forwarded_in                messages of the channel that are forwards (any origin)
  n_forwarded_in_from_channels  of those, forwards from a public channel
  total_forwards                how many times the channel's own messages were forwarded
  first_date / last_date        activity period seen in the data

Usage: python3 job4_stats.py --out ~/telescope_v2 [--clean DIR] [--csv]
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
    spark = get_spark("telescope-job4-stats")

    def iso(col):
        return F.date_format(F.timestamp_seconds(col), "yyyy-MM-dd'T'HH:mm:ss")

    c = spark.read.parquet(str(clean)).where(F.col("dest_channel").isNotNull())
    stats = (c.groupBy("dest_channel").agg(
                F.count(F.lit(1)).alias("n_messages"),
                F.sum(F.when(F.col("kind") != "", 1).otherwise(0)).alias("n_forwarded_in"),
                F.sum(F.when(F.col("kind") == "channel", 1).otherwise(0))
                 .alias("n_forwarded_in_from_channels"),
                F.coalesce(F.sum("views"), F.lit(0)).alias("total_views"),
                F.coalesce(F.sum("forwards"), F.lit(0)).alias("total_forwards"),
                F.min("ts").alias("first_ts"), F.max("ts").alias("last_ts"))
             .select(F.col("dest_channel").alias("channel_id"), "n_messages", "n_forwarded_in",
                     "n_forwarded_in_from_channels", "total_views", "total_forwards",
                     iso(F.col("first_ts")).alias("first_date"),
                     iso(F.col("last_ts")).alias("last_date")))

    dst = args.out / "gold" / "channel_stats"
    stats.write.mode("overwrite").parquet(str(dst))
    res = spark.read.parquet(str(dst))
    print(f"stats: {res.count():,} channels -> {dst}")
    if args.csv:
        csv_dir = args.out / "gold" / "channel_stats_csv"
        res.coalesce(1).write.mode("overwrite").option("header", True).csv(str(csv_dir))
        print(f"csv written to {csv_dir}")
    spark.stop()


if __name__ == "__main__":
    main()
