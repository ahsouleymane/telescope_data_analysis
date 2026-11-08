"""
Finding and opening the raw files: plain .jsonl files or .jsonl members of .zip
archives (read straight from the archive, nothing is extracted). No Spark here.
"""

import io
import re
import zipfile
from pathlib import Path


def open_text(src, member=None):
    """Return (text_stream, closer). `member` is the name inside the zip, or None."""
    if member is None:
        f = open(src, encoding="utf-8", errors="replace")
        return f, f
    zf = zipfile.ZipFile(src)
    return io.TextIOWrapper(zf.open(member), encoding="utf-8", errors="replace"), zf


def safe_batch(name):
    """Batch name usable as a folder name in a Parquet partition path."""
    return re.sub(r"[^A-Za-z0-9._-]+", "__", str(name)).strip("_") or "batch"


def channel_of(path_or_member):
    """'.../1961746451.jsonl' -> 1961746451 (None when the stem is not a number)."""
    stem = Path(path_or_member).stem
    return int(stem) if stem.isdigit() else None


def list_inputs(raw):
    """
    Yield dicts {src, member, batch, channel, size} for every .jsonl found under
    `raw`, which may be a folder of .jsonl, a folder of .zip, one .zip, or a mix.
    `batch` is the folder (inside the zip, or on disk) that holds the file. For a
    file at the root of a zip (one zip per channel), it is the folder of the
    DISK that holds the zip (e.g. 1877677892_to_1961731638/1877677892.zip ->
    batch 1877677892_to_1961731638); when `raw` is itself one zip, its name.
    """
    raw = Path(raw)
    paths = [raw] if raw.is_file() else sorted(raw.rglob("*"))
    for p in paths:
        suffix = p.suffix.lower()
        if suffix == ".jsonl":
            rel = p.relative_to(raw) if raw.is_dir() else Path(p.name)
            batch = rel.parent.as_posix() if str(rel.parent) != "." else raw.name
            yield {"src": str(p), "member": None, "batch": safe_batch(batch),
                   "channel": channel_of(p), "size": p.stat().st_size}
        elif suffix == ".zip":
            with zipfile.ZipFile(p) as zf:
                for info in sorted(zf.infolist(), key=lambda i: i.filename):
                    name = info.filename
                    if name.lower().endswith(".jsonl") and not name.endswith("/"):
                        folder = Path(name).parent.as_posix()
                        if folder != ".":
                            batch = folder
                        else:
                            batch = p.parent.name if raw.is_dir() else p.stem
                        yield {"src": str(p), "member": name, "batch": safe_batch(batch),
                               "channel": channel_of(name), "size": info.file_size}
