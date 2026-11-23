#!/usr/bin/env python3
"""
JOB 6 - BEHAVIOUR FEATURES FOR SUSPICIOUS-TREND ANALYSIS (theme 5).

Input : <out>/clean_dedup (or clean)
Output: <out>/gold/ (Parquet)

  channel_behavior      one row per channel with at least --min-posts messages:
                        n_posts, views_mean, views_median, zero_view_share, forwards_mean,
                        n_active_days, max_posts_day, median_posts_day,
                        n_forwarded, n_origins, top_origin_share,
                        share_fast10, share_fast60, median_delay_s, delay_p25_s, delay_p75_s, sec_mode_share
  channel_hours         channel, hour (UTC, 0-23), n_posts
  coordinated_pairs     channel_a, channel_b, n_shared, n_origins, median_dt_s
                        = pairs of channels that relay the SAME original message within --window seconds
                        of each other, at least --min-shared times
  cascades              one row per original message with at least --min-cascade relays:
                        n_relays, n_channels, first_delay_s, span_s, n_first10min, month
  forward_speed_monthly month, n_forwards, n_fast10, n_fast60, median_delay_s

Definitions
  forwarded message   kind == 'channel' with a known original post time (origin_ts)
  delay_s             ts - origin_ts (seconds between the original post and the relay)
  share_fast10        share of a channel's forwarded messages relayed within 10 s of the original
  top_origin_share    share of a channel's forwarded messages coming from its single most used source
  sec_mode_share      share of posts published on the most frequent second of the minute (baseline 1/60)
  coordinated pair    sort the relays of one original message by time; each relay is paired with the next
                      --neighbours relays when they follow within --window seconds (keeps the join bounded)

Nothing here says WHY a channel behaves like this; the tables only measure behaviour.

Usage: python3 job6_suspicious.py --out telescope_pipeline_files [--min-posts 30] [--window 60] [--csv]
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--clean", type=Path, default=None)
    ap.add_argument("--min-posts", type=int, default=30, help="channels with fewer messages are ignored")
    ap.add_argument("--window", type=int, default=60, help="max seconds between two relays of the same message to pair them")
    ap.add_argument("--neighbours", type=int, default=5, help="number of following relays paired with each relay")
    ap.add_argument("--max-relays", type=int, default=500, help="skip original messages relayed more than this (viral posts)")
    ap.add_argument("--min-shared", type=int, default=5, help="min distinct original messages shared by a pair")
    ap.add_argument("--min-cascade", type=int, default=10, help="min relays to keep a cascade")
    ap.add_argument("--min-date", default="2015-01-01")
    ap.add_argument("--max-date", default="2026-12-31")
    ap.add_argument("--csv", action="store_true", help="also write single CSV files (gold/<table>_csv)")
    args = ap.parse_args()
    from spark_session import default_clean
    clean = args.clean or default_clean(args.out)

    from pyspark.sql import Window
    from pyspark.sql import functions as F
    from spark_session import get_spark
    spark = get_spark("telescope-job6-suspicious")

    def save(df, name):
        dst = args.out / "gold" / name
        df.write.mode("overwrite").parquet(str(dst))
        res = spark.read.parquet(str(dst))
        print(f"{name}: {res.count():,} rows -> {dst}")
        if args.csv:
            res.coalesce(1).write.mode("overwrite").option("header", True).csv(str(args.out / "gold" / f"{name}_csv"))

    c = (spark.read.parquet(str(clean))
         .where(F.col("dest_channel").isNotNull() & F.col("ts").isNotNull())
         .withColumn("date", F.to_date(F.timestamp_seconds("ts")))
         .where((F.col("date") >= F.lit(args.min_date)) & (F.col("date") <= F.lit(args.max_date))))

    fwd = (c.where((F.col("kind") == "channel") & F.col("origin_channel").isNotNull() & F.col("origin_ts").isNotNull())
            .withColumn("delay_s", F.col("ts") - F.col("origin_ts"))
            .where(F.col("delay_s") >= 0))

    # ---- per-channel behaviour ------------------------------------------------------------------
    base = (c.groupBy("dest_channel")
            .agg(F.count(F.lit(1)).alias("n_posts"),
                 F.avg("views").alias("views_mean"),
                 F.percentile_approx("views", 0.5).alias("views_median"),
                 F.avg(F.when(F.col("views").isNull() | (F.col("views") == 0), 1.0).otherwise(0.0)).alias("zero_view_share"),
                 F.avg("forwards").alias("forwards_mean"))
            .where(F.col("n_posts") >= args.min_posts))

    daily = (c.groupBy("dest_channel", "date").count()
             .groupBy("dest_channel")
             .agg(F.count(F.lit(1)).alias("n_active_days"),
                  F.max("count").alias("max_posts_day"),
                  F.percentile_approx("count", 0.5).alias("median_posts_day")))

    fagg = (fwd.groupBy("dest_channel")
            .agg(F.count(F.lit(1)).alias("n_forwarded"),
                 F.countDistinct("origin_channel").alias("n_origins"),
                 F.avg(F.when(F.col("delay_s") <= 10, 1.0).otherwise(0.0)).alias("share_fast10"),
                 F.avg(F.when(F.col("delay_s") <= 60, 1.0).otherwise(0.0)).alias("share_fast60"),
                 F.percentile_approx("delay_s", 0.5).alias("median_delay_s"),
                 F.percentile_approx("delay_s", 0.25).alias("delay_p25_s"),
                 F.percentile_approx("delay_s", 0.75).alias("delay_p75_s")))

    top_src = (fwd.groupBy("dest_channel", "origin_channel").count()
               .groupBy("dest_channel").agg(F.max("count").alias("top_origin_posts")))

    sec = (c.withColumn("sec", F.col("ts") % 60).groupBy("dest_channel", "sec").count()
           .groupBy("dest_channel").agg(F.max("count").alias("sec_mode_posts")))

    behavior = (base.join(daily, "dest_channel", "left").join(fagg, "dest_channel", "left")
                .join(top_src, "dest_channel", "left").join(sec, "dest_channel", "left")
                .withColumn("top_origin_share", F.col("top_origin_posts") / F.col("n_forwarded"))
                .withColumn("sec_mode_share", F.col("sec_mode_posts") / F.col("n_posts"))
                .drop("top_origin_posts", "sec_mode_posts")
                .withColumnRenamed("dest_channel", "channel_id"))
    save(behavior, "channel_behavior")

    hours = (c.withColumn("hour", ((F.col("ts") % 86400) / 3600).cast("int"))
             .groupBy("dest_channel", "hour").agg(F.count(F.lit(1)).alias("n_posts"))
             .withColumnRenamed("dest_channel", "channel_id"))
    save(hours.join(behavior.select("channel_id"), "channel_id"), "channel_hours")

    # ---- coordinated pairs ------------------------------------------------------------------------
    key = ["origin_channel", "origin_post"]
    f = (fwd.where(F.col("origin_post").isNotNull())
         .withColumn("n_relays", F.count(F.lit(1)).over(Window.partitionBy(*key)))
         .where((F.col("n_relays") >= 2) & (F.col("n_relays") <= args.max_relays)))
    ordered = Window.partitionBy(*key).orderBy("ts", "dest_channel", "msg_id")
    for k in range(1, args.neighbours + 1):
        f = (f.withColumn(f"b{k}", F.lead("dest_channel", k).over(ordered))
              .withColumn(f"t{k}", F.lead("ts", k).over(ordered)))
    parts = [f.select(*key, F.col("dest_channel").alias("a"), F.col(f"b{k}").alias("b"),
                      (F.col(f"t{k}") - F.col("ts")).alias("dt"))
             for k in range(1, args.neighbours + 1)]
    allp = parts[0]
    for p in parts[1:]:
        allp = allp.unionByName(p)
    allp = allp.where(F.col("b").isNotNull() & (F.col("a") != F.col("b")) & (F.col("dt") <= args.window))
    pairs = (allp.withColumn("channel_a", F.least("a", "b")).withColumn("channel_b", F.greatest("a", "b"))
             .groupBy("channel_a", "channel_b")
             .agg(F.countDistinct("origin_channel", "origin_post").alias("n_shared"),
                  F.countDistinct("origin_channel").alias("n_origins"),
                  F.percentile_approx("dt", 0.5).alias("median_dt_s"))
             .where(F.col("n_shared") >= args.min_shared))
    save(pairs, "coordinated_pairs")

    # ---- cascades -----------------------------------------------------------------------------------
    casc = (fwd.where(F.col("origin_post").isNotNull()).groupBy(*key)
            .agg(F.count(F.lit(1)).alias("n_relays"),
                 F.countDistinct("dest_channel").alias("n_channels"),
                 F.min("ts").alias("first_ts"), F.max("ts").alias("last_ts"),
                 F.min("delay_s").alias("first_delay_s"), F.min("origin_ts").alias("origin_ts"))
            .where(F.col("n_relays") >= args.min_cascade))
    within = (fwd.join(casc.select(*key, "first_ts"), key)
              .where(F.col("ts") - F.col("first_ts") <= 600)
              .groupBy(*key).agg(F.count(F.lit(1)).alias("n_first10min")))
    casc = (casc.join(within, key, "left")
            .withColumn("span_s", F.col("last_ts") - F.col("first_ts"))
            .withColumn("month", F.date_format(F.timestamp_seconds("origin_ts"), "yyyy-MM"))
            .drop("first_ts", "last_ts", "origin_ts"))
    save(casc, "cascades")

    # ---- monthly speed trend ------------------------------------------------------------------------
    speed = (fwd.withColumn("month", F.date_format(F.timestamp_seconds("ts"), "yyyy-MM"))
             .groupBy("month")
             .agg(F.count(F.lit(1)).alias("n_forwards"),
                  F.sum(F.when(F.col("delay_s") <= 10, 1).otherwise(0)).alias("n_fast10"),
                  F.sum(F.when(F.col("delay_s") <= 60, 1).otherwise(0)).alias("n_fast60"),
                  F.percentile_approx("delay_s", 0.5).alias("median_delay_s")))
    save(speed, "forward_speed_monthly")
    spark.stop()


if __name__ == "__main__":
    main()