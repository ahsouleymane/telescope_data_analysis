#!/usr/bin/env python3
"""
Phase A - run job 1 (clean) over the raw JSONL files, in parallel, with resume.

Reads the raw disk (read-only), writes one TSV per channel file on the INTERNAL
disk, in the same folder layout:

    <out>/<batch_folder>/<channel>.tsv

A file whose TSV already exists is skipped, so an interrupted run simply
continues. Output is written to *.tmp then renamed, so a crash never leaves a
half-written TSV. It uses the same clean_line() as the Hadoop mapper.

--raw may be a folder of .jsonl files, a folder of .zip archives (or one .zip),
or a mix: the .jsonl files INSIDE a zip are read directly from the archive,
nothing is extracted to disk. Output layout is the same in every case:
<out>/<batch_folder>/<channel>.tsv, where <batch_folder> is the folder inside
the zip, or the zip's own name when the .jsonl files sit at its root.

Usage:
    python3 scripts/run_clean.py --raw /media/<disk>/telescope_raw --out ~/telescope_clean
    python3 scripts/run_clean.py --raw /path/to/lot_11.zip --out ~/telescope_clean
    python3 scripts/run_clean.py --raw /path/to/folder_of_zips --out ~/telescope_clean
    python3 scripts/run_clean.py --raw .../telescope_raw/1000015666_to_1054523330 --out ~/telescope_clean
    python3 scripts/run_clean.py --raw ... --out ... --jobs 4 --limit 50     # quick trial
"""
import argparse
import csv
import io
import os
import sys
import time
import zipfile
from multiprocessing import Pool
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "mapreduce"))
from common import clean_line  # noqa: E402


def _open_text(src, member):
    """Text stream of a plain .jsonl file, or of a .jsonl member inside a .zip."""
    if member is None:
        return open(src, encoding="utf-8", errors="replace"), None
    zf = zipfile.ZipFile(src)
    return io.TextIOWrapper(zf.open(member), encoding="utf-8", errors="replace"), zf


def process(task):
    src, member, dst = task
    dst = Path(dst)
    tmp = dst.with_suffix(".tsv.tmp")
    dst.parent.mkdir(parents=True, exist_ok=True)
    default_channel = Path(member or src).stem
    stats = {"ok": 0, "bad_json": 0, "skipped": 0}
    fin, zf = _open_text(src, member)
    try:
        with fin, open(tmp, "w", encoding="utf-8") as fout:
            for line in fin:
                rec, status = clean_line(line, default_channel)
                stats[status] += 1
                if rec is not None:
                    fout.write(rec + "\n")
    finally:
        if zf is not None:
            zf.close()
    os.replace(tmp, dst)
    label = f"{src}::{member}" if member else str(src)
    size = zipfile.ZipFile(src).getinfo(member).file_size if member else os.path.getsize(src)
    return label, stats["ok"], stats["bad_json"], stats["skipped"], size


def list_inputs(raw):
    """Yield (source_path, zip_member_or_None, batch_name, channel_stem)."""
    raw = Path(raw)
    paths = [raw] if raw.is_file() else sorted(raw.rglob("*"))
    for p in paths:
        if p.suffix.lower() == ".jsonl":
            rel = p.relative_to(raw) if raw.is_dir() else Path(p.name)
            batch = rel.parent.as_posix() if str(rel.parent) != "." else raw.name
            yield p, None, batch, p.stem
        elif p.suffix.lower() == ".zip":
            with zipfile.ZipFile(p) as zf:
                for name in sorted(zf.namelist()):
                    if name.lower().endswith(".jsonl") and not name.endswith("/"):
                        folder = Path(name).parent.as_posix()
                        batch = folder if folder != "." else p.stem
                        yield p, name, batch, Path(name).stem


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--raw", type=Path, required=True,
                    help="folder of .jsonl, folder of .zip, or one .zip (root or one batch)")
    ap.add_argument("--out", type=Path, required=True, help="output folder (internal disk)")
    ap.add_argument("--jobs", type=int, default=3, help="worker processes (default 3: leaves a core free)")
    ap.add_argument("--limit", type=int, default=0, help="only the N first files (trial run)")
    args = ap.parse_args()

    items = list(list_inputs(args.raw))
    if args.limit:
        items = items[:args.limit]
    tasks, skipped = [], 0
    for src, member, batch, stem in items:
        dst = args.out / batch / (stem + ".tsv")
        if dst.exists():
            skipped += 1
        else:
            tasks.append((src, member, dst))
    print(f"{len(items):,} files found, {skipped:,} already done, {len(tasks):,} to process")

    args.out.mkdir(parents=True, exist_ok=True)
    log_path = args.out / "clean_log.csv"
    new_log = not log_path.exists()
    t0, done, gb = time.time(), 0, 0.0
    with open(log_path, "a", newline="", encoding="utf-8") as log, Pool(args.jobs) as pool:
        w = csv.writer(log)
        if new_log:
            w.writerow(["file", "messages_ok", "bad_json", "skipped", "bytes"])
        for src, ok, bad, skip, size in pool.imap_unordered(process, tasks, chunksize=4):
            w.writerow([src, ok, bad, skip, size])
            done += 1
            gb += size / 1e9
            if done % 200 == 0 or done == len(tasks):
                dt = time.time() - t0
                print(f"   {done:,}/{len(tasks):,} files, {gb:,.1f} GB read, "
                      f"{gb * 1000 / max(dt, 1e-9):,.0f} MB/s", flush=True)
    print("done")


if __name__ == "__main__":
    main()
