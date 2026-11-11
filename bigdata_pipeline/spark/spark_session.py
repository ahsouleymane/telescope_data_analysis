"""
One place to configure Spark for a small machine (default: 3 cores, 8 GB RAM).

Spark runs in LOCAL mode: a single JVM, no cluster. Everything is overridable
with environment variables:

  TELESCOPE_CORES              cores used                       (default 3)
  TELESCOPE_SPARK_MEMORY       JVM memory                       (default 4g)
  TELESCOPE_SPARK_TMP          shuffle/spill folder, INTERNAL disk (default ~/spark_tmp)
  TELESCOPE_SHUFFLE_PARTITIONS partitions after a shuffle       (default 48)

In local mode the "executors" live inside the driver JVM, so TELESCOPE_SPARK_MEMORY
is the whole Spark memory. With 8 GB total, 4g leaves room for the OS and the
Python workers. Raise it only if your machine has memory to spare.
"""

import os
import sys


def get_spark(app="telescope"):
    os.environ.setdefault("PYSPARK_PYTHON", sys.executable)
    os.environ.setdefault("PYSPARK_DRIVER_PYTHON", sys.executable)
    from pyspark.sql import SparkSession

    cores = int(os.environ.get("TELESCOPE_CORES", "3"))
    memory = os.environ.get("TELESCOPE_SPARK_MEMORY", "4g")
    tmp = os.environ.get("TELESCOPE_SPARK_TMP", os.path.expanduser("~/spark_tmp"))
    os.makedirs(tmp, exist_ok=True)

    spark = (
        SparkSession.builder.master(f"local[{cores}]").appName(app)
        .config("spark.driver.memory", memory)
        .config("spark.local.dir", tmp)
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.sql.shuffle.partitions", os.environ.get("TELESCOPE_SHUFFLE_PARTITIONS", "48"))
        .config("spark.python.worker.reuse", "true")
        .config("spark.ui.enabled", "false")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")
    return spark


def default_clean(out):
    """Folder the jobs 2-4 read: the deduplicated messages when job1b_dedup.py has produced them, else the raw clean/."""
    from pathlib import Path
    out = Path(out)
    dedup = out / "clean_dedup"
    if dedup.exists():
        return dedup
    print("WARNING: reading clean/ with duplicated messages; run job1b_dedup.py first", file=sys.stderr)
    return out / "clean"
