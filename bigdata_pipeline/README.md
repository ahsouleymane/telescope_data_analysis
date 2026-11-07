# TeleScope - Big Data pipeline (v2, PySpark)

Message-level processing of the TeleScope Telegram dataset (about 345 GB of JSONL
for the 15 batches extracted so far, about 120 M messages in total). The v1
analysis (`code/`, `telescope_files/`) works on the pre-aggregated channel graph;
this pipeline rebuilds the same information from the messages, with dates and
weights.

The raw data stays where it is, read-only. Only reduced tables are written to the
internal disk. Spark runs in LOCAL mode (one JVM, no cluster).

## Pipeline

```
raw JSONL / ZIP (external disk, read-only)
   |  job 1  CLEAN        job1_clean.py     typed Parquet, one folder per batch
   v
<out>/clean/batch=<folder>/*.parquet                 (a few GB)
   |  job 2  CHAINS       job2_chains.py
   |  job 3  EDGES        job3_edges.py
   |  job 4  STATS        job4_stats.py
   v
<out>/gold/chains   <out>/gold/edges_monthly   <out>/gold/channel_stats
   |  analysis (igraph, pandas): communities, languages, traceability
```

| Job | What it computes | Output columns |
|---|---|---|
| 1 clean | one typed row per message (9 columns, see `clean_records.py`) | dest_channel, msg_id, ts, views, forwards, kind, origin_channel, origin_post, origin_ts |
| 2 chains | all relays of each original message, ordered by time | origin_channel, origin_post, origin_date, rank, dest_channel, dest_msg, date, delay_s, n_relays |
| 3 edges | monthly weighted edges A -> B (B forwarded A's messages) | origin_channel, dest_channel, month, n_forwards |
| 4 stats | activity of each channel | channel_id, n_messages, n_forwarded_in, n_forwarded_in_from_channels, total_views, total_forwards, first_date, last_date |

## Install (once)

```bash
sudo apt install openjdk-17-jre-headless          # Java 17 or newer
pip install -r bigdata/requirements.txt           # pyspark, pandas, pyarrow
java -version && python3 -c "import pyspark; print(pyspark.__version__)"
```

## First thing to do: check that everything works on one channel

This was NOT run by the author of the code (PySpark could not be installed in his
environment), so run it before anything else:

```bash
python3 -m unittest bigdata/tests/test_clean_records.py -v      # no Spark needed, 15 tests
python3 bigdata/tests/verify_spark.py /path/to/1961746451.jsonl # runs jobs 1-4 and checks the numbers
```
`verify_spark.py` ends with `ALL CHECKS PASSED`. If a check fails or a job crashes,
send the message it prints.

## Run

```bash
# 1. trial on 50 files (written to <out>/clean_trial, never mixed with the real data)
python3 bigdata/spark/job1_clean.py --raw /media/0EFC061CFC05FF29/telescope_raw --out ~/telescope_v2 --limit 50

# 2. job 1 on everything. Resumable: stop it (Ctrl+C) and run it again, finished batches are skipped
python3 bigdata/spark/job1_clean.py --raw /media/0EFC061CFC05FF29/telescope_raw --out ~/telescope_v2

# 3. jobs 2-4, once, after the LAST batch (they need every batch together)
python3 bigdata/spark/job2_chains.py --out ~/telescope_v2
python3 bigdata/spark/job3_edges.py  --out ~/telescope_v2 --csv
python3 bigdata/spark/job4_stats.py  --out ~/telescope_v2 --csv
# or everything in one go:  bigdata/spark/run_pipeline.sh <raw> ~/telescope_v2
```

Job 1 prints, for each batch, the messages kept and the read speed; `clean_log.csv`
keeps one line per batch (messages, bad JSON lines, service messages skipped, GB, seconds).

### Archives not extracted yet

`--raw` accepts a `.zip`, a folder of `.zip`, a folder of `.jsonl`, or a mix. The
`.jsonl` files inside a zip are read straight from the archive, nothing is
extracted. Raw folders and zips can live in different places: the same `--out`
collects everything.

```bash
python3 bigdata/spark/job1_clean.py --raw /path/to/folder_of_zips --out ~/telescope_v2
```
A batch is skipped when it is already done with the same number of files. If you
add files to an already processed batch, the count changes and it is redone (or use `--force`).

### Machine settings (default: 3 cores, 8 GB RAM)

| Variable | Default | Meaning |
|---|---|---|
| `TELESCOPE_CORES` | 3 | cores used by Spark |
| `TELESCOPE_SPARK_MEMORY` | 4g | JVM memory (in local mode this is all of Spark's memory) |
| `TELESCOPE_SPARK_TMP` | `~/spark_tmp` | shuffle/spill folder: keep it on the INTERNAL disk, with a few tens of GB free |
| `TELESCOPE_SHUFFLE_PARTITIONS` | 48 | raise it if a job runs out of memory in a shuffle |

Example: `TELESCOPE_CORES=2 TELESCOPE_SPARK_MEMORY=3g python3 bigdata/spark/job2_chains.py --out ~/telescope_v2`.
If a job fails with `OutOfMemoryError`, raise `TELESCOPE_SHUFFLE_PARTITIONS` (for example 96 or 200) before raising the memory.

### Reading the results

```python
import pandas as pd
edges = pd.read_parquet("~/telescope_v2/gold/edges_monthly")     # a folder of Parquet files
stats = pd.read_parquet("~/telescope_v2/gold/channel_stats")
```
`--csv` on jobs 3 and 4 also writes a single CSV (`gold/edges_monthly_csv/`,
`gold/channel_stats_csv/`, header included) for scripts that read CSV.

## Things to know

- Dates are stored as epoch seconds (UTC) in the clean data, and converted in
  Spark with the session time zone fixed to UTC.
- Service messages (joins, pins...) are skipped and counted in `clean_log.csv`.
- A forward whose origin is a user, or hidden by Telegram privacy, is kept
  (`kind` = `user` / `hidden`) but cannot become an edge or a chain.
- A forward from a channel without the original post id counts as an edge, but
  cannot be grouped into a chain (about 0.1 % in the sample channel).
- Telegram keeps the ORIGINAL author in every forward header, so intermediate
  hops are not stored: order and delay come from the dates.
- Spark has no zip reader, so job 1 hands the files to Spark tasks as a list and
  parses them with plain Python (`clean_records.py`); Spark builds the typed
  DataFrame and writes the Parquet. Jobs 2-4 are ordinary Spark DataFrame code.
- The message text is not part of the dataset.
- The dataset is licensed CC BY-NC-SA 4.0 (research use, cite DOI 10.7802/2825).
