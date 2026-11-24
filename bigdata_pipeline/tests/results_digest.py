#!/usr/bin/env python3
"""
Fingerprint of the results, to check that two runs give EXACTLY the same numbers.

For every dataset found under --roots it writes one line: path, rows, columns, digest.
A dataset is a folder of Spark part files (parquet or csv) or a standalone csv file. The digest does not
depend on the order of the rows, nor on the names of the part files (random in Spark), nor on the number of files:
it only changes when the content changes. Values are compared as text, so a difference in the last decimal is seen.
Images (png), json run reports and logs are ignored (they hold dates or fonts that change).

Usage:
    python3 results_digest.py --roots telescope_pipeline_files/gold bigdata_pipeline/analysis --out run1.tsv
    python3 results_digest.py --compare run1.tsv run2.tsv
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

MASK = (1 << 64) - 1
SKIP_DIRS = {"figures", "__pycache__", "app", "tmp", "_temporary"}
SKIP_NAMES = {"clean_log.csv", "dedup_log.csv", "clean_trial_log.csv"}   # logs: they hold durations / dates


def batches_csv(files):
    for f in files:
        for chunk in pd.read_csv(f, dtype=str, keep_default_na=False, chunksize=500_000):
            yield chunk


def batches_parquet(files):
    import pyarrow.parquet as pq
    for f in files:
        for b in pq.ParquetFile(f).iter_batches(batch_size=500_000):
            yield b.to_pandas().astype(str)


def digest(batches):
    rows, total, cols = 0, 0, None
    for df in batches:
        df = df.astype(str)
        df = df[sorted(df.columns)]
        cols = list(df.columns) if cols is None else cols
        total = (total + int(pd.util.hash_pandas_object(df, index=False).sum())) & MASK
        rows += len(df)
    return rows, cols or [], total


def datasets(root):
    """Yield (name, kind, files). A folder holding part-* files is ONE dataset."""
    root = Path(root)
    for d in sorted([root] + [p for p in root.rglob("*") if p.is_dir()]):
        if SKIP_DIRS & set(d.relative_to(root).parts) or d.name in SKIP_DIRS:
            continue
        parts = sorted(d.glob("part-*.parquet")) or sorted(d.glob("part-*.csv"))
        if parts:
            yield d, ("parquet" if parts[0].suffix == ".parquet" else "csv"), parts
        else:
            for f in sorted(d.glob("*.csv")):
                if f.name not in SKIP_NAMES:
                    yield f, "csv", [f]


def run(roots, out):
    lines = []
    for root in roots:
        for name, kind, files in datasets(root):
            try:
                n, cols, h = digest((batches_parquet if kind == "parquet" else batches_csv)(files))
            except Exception as e:                      # empty file, unreadable file: reported, not hidden
                lines.append(f"{name}\tERROR\t{type(e).__name__}\t-")
                continue
            lines.append(f"{name}\t{n}\t{len(cols)}\t{h:016x}")
    Path(out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{len(lines)} datasets written to {out}")


def compare(a, b):
    def load(p):
        return {l.split("\t")[0]: l.rstrip("\n").split("\t")[1:] for l in Path(p).read_text(encoding="utf-8").splitlines() if l}
    A, B = load(a), load(b)
    only_a, only_b = sorted(set(A) - set(B)), sorted(set(B) - set(A))
    diff = sorted(k for k in set(A) & set(B) if A[k] != B[k])
    for k in only_a: print(f"ONLY IN {a}: {k}")
    for k in only_b: print(f"ONLY IN {b}: {k}")
    for k in diff: print(f"DIFFERENT: {k}\n    {a}: rows/cols/digest = {A[k]}\n    {b}: rows/cols/digest = {B[k]}")
    same = len(set(A) & set(B)) - len(diff)
    print(f"\n{same} identical datasets, {len(diff)} different, {len(only_a)+len(only_b)} present in one run only")
    return 0 if not (diff or only_a or only_b) else 1


def selftest():
    import tempfile
    with tempfile.TemporaryDirectory() as t:
        t = Path(t)
        (t / "x").mkdir()
        pd.DataFrame({"a": ["1", "2", "3"], "b": ["x", "y", "z"]}).to_csv(t / "x" / "part-00000-aaa.csv", index=False)
        d1 = digest(batches_csv([t / "x" / "part-00000-aaa.csv"]))
        # same rows, other order, other part names and split in two files -> same digest
        (t / "y").mkdir()
        pd.DataFrame({"b": ["z", "x"], "a": ["3", "1"]}).to_csv(t / "y" / "part-00001-bbb.csv", index=False)
        pd.DataFrame({"b": ["y"], "a": ["2"]}).to_csv(t / "y" / "part-00000-ccc.csv", index=False)
        d2 = digest(batches_csv(sorted((t / "y").glob("part-*.csv"))))
        assert d1 == d2, (d1, d2)
        pd.DataFrame({"a": ["1", "2", "3.0000001"], "b": ["x", "y", "z"]}).to_csv(t / "x" / "part-00000-aaa.csv", index=False)
        assert digest(batches_csv([t / "x" / "part-00000-aaa.csv"])) != d1
        found = [str(n.relative_to(t)) for n, _, _ in datasets(t)]
        assert found == ["x", "y"], found
    print("selftest OK")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--roots", nargs="+", default=["telescope_pipeline_files/gold", "bigdata_pipeline/analysis"])
    ap.add_argument("--out", default="results_digest.tsv")
    ap.add_argument("--compare", nargs=2, metavar=("RUN_A", "RUN_B"))
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.compare:
        sys.exit(compare(*a.compare))
    run(a.roots, a.out)


if __name__ == "__main__":
    main()