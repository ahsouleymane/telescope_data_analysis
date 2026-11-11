#!/usr/bin/env python3
"""
JOB 2 - MESSAGE CHAINS.

For every original message (origin_channel, origin_post) that was forwarded by
public channels, list all its relays ordered by time.

Input : <out>/clean            (Parquet from job1_clean.py)
Output: <out>/gold/chains      (Parquet), columns:

  origin_channel  origin_post  origin_date  rank  dest_channel  dest_msg
  date  delay_s  n_relays

  rank      1 = first relay in time, 2 = second...
  delay_s   seconds between the original post and this relay
  n_relays  number of relays of this original message in the data

Telegram keeps the ORIGINAL author in every forward header, so intermediate
hops are not stored: the order and delays come from the dates.
A forward from a channel without the original post id cannot be grouped and is
left out (it still counts as an edge in job 3).

Usage: python3 job2_chains.py --out ~/telescope_v2 [--clean DIR]
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


def iso(col):
    from pyspark.sql import functions as F
    return F.date_format(F.timestamp_seconds(col), "yyyy-MM-dd'T'HH:mm:ss")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--clean", type=Path, default=None)
    args = ap.parse_args()
    from spark_session import default_clean
    clean = args.clean or default_clean(args.out)       # clean_dedup/ when job1b_dedup.py has been run

    from pyspark.sql import Window
    from pyspark.sql import functions as F
    from spark_session import get_spark
    spark = get_spark("telescope-job2-chains")

    c = (spark.read.parquet(str(clean))
         .where((F.col("kind") == "channel") & F.col("origin_post").isNotNull()
                & F.col("origin_channel").isNotNull()))
    key = ["origin_channel", "origin_post"]
    ordered = Window.partitionBy(*key).orderBy("ts", "dest_channel", "msg_id")
    whole = Window.partitionBy(*key)

    res = (c.withColumn("rank", F.row_number().over(ordered))
            .withColumn("n_relays", F.count(F.lit(1)).over(whole))
            .withColumn("delay_s", F.col("ts") - F.col("origin_ts"))
            .select("origin_channel", "origin_post",
                    iso(F.col("origin_ts")).alias("origin_date"),
                    "rank",
                    F.col("dest_channel"), F.col("msg_id").alias("dest_msg"),
                    iso(F.col("ts")).alias("date"),
                    "delay_s", "n_relays"))

    dst = args.out / "gold" / "chains"
    res.write.mode("overwrite").parquet(str(dst))
    n = spark.read.parquet(str(dst)).count()
    print(f"chains: {n:,} relays written to {dst}")
    spark.stop()


if __name__ == "__main__":
    main()
