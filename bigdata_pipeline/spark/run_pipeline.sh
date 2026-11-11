#!/usr/bin/env bash
# Whole pipeline: raw data -> clean Parquet -> deduplicated messages -> chains, monthly edges, channel stats.
#
# Usage:  bigdata/spark/run_pipeline.sh <raw_dir_or_zips> <out_dir>
# Example: bigdata/spark/run_pipeline.sh /media/0EFC061CFC05FF29/telescope_raw ~/telescope_v2
#
# Job 1 is resumable. Jobs 2-4 need ALL batches, so run them after the last batch
# (use the individual job scripts to run only one of them).
set -euo pipefail
RAW="${1:?raw dir (folder of .jsonl / .zip, or one .zip)}"; OUT="${2:?output dir}"
HERE="$(cd "$(dirname "$0")" && pwd)"
export TELESCOPE_CORES="${TELESCOPE_CORES:-3}"

python3 "$HERE/job1_clean.py"  --raw "$RAW" --out "$OUT"
python3 "$HERE/job1b_dedup.py" --out "$OUT"
python3 "$HERE/job2_chains.py" --out "$OUT"
python3 "$HERE/job3_edges.py"  --out "$OUT" --csv
python3 "$HERE/job4_stats.py"  --out "$OUT" --csv
echo "all done -> $OUT/gold"
