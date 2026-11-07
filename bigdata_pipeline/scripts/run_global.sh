#!/usr/bin/env bash
# Phase B - jobs 2, 3 and 4 over ALL clean TSV files (local mode, same code as Hadoop).
#
# Usage:  scripts/run_global.sh <clean_dir> <out_dir> [tmp_dir]
#   clean_dir  output of run_clean.py (e.g. ~/telescope_clean)
#   out_dir    where chains.tsv, edges_monthly.tsv, channel_stats.tsv are written
#   tmp_dir    big scratch space for sort (default: <out_dir>/tmp, INTERNAL disk)
#
# The shuffle is done by `sort`, exactly what Hadoop does between map and reduce.
set -euo pipefail

CLEAN="${1:?clean_dir}"; OUT="${2:?out_dir}"; TMP="${3:-$OUT/tmp}"
HERE="$(cd "$(dirname "$0")/.." && pwd)/mapreduce"
SORT_MEM="${SORT_MEM:-2G}"          # keep it well below your free RAM (8 GB machine: 2G)
SORT_THREADS="${SORT_THREADS:-2}"   # sort is multi-threaded by default: cap it (3 cores budget = map + reduce + 2 sort threads share them)
mkdir -p "$OUT" "$TMP"
export LC_ALL=C
TAB=$'\t'

read_clean() { find "$CLEAN" -name '*.tsv' -print0 | xargs -0 cat; }
run() {  # name, map script, sort keys, reduce script, output
  echo "[$1] start $(date +%T)"
  read_clean | python3 "$HERE/$2" \
    | sort -t "$TAB" $3 --parallel="$SORT_THREADS" -S "$SORT_MEM" -T "$TMP" \
    | python3 "$HERE/$4" > "$OUT/$5.tmp"
  mv "$OUT/$5.tmp" "$OUT/$5"
  echo "[$1] done  $(date +%T)  -> $OUT/$5 ($(wc -l < "$OUT/$5") lines)"
}

run chains  chains_map.py "-k1,1 -k2,2"        chains_reduce.py "chains.tsv"
run edges   edges_map.py  "-k1,1 -k2,2 -k3,3"  edges_reduce.py  "edges_monthly.tsv"
run stats   stats_map.py  "-k1,1"              stats_reduce.py  "channel_stats.tsv"
rm -rf "$TMP"
