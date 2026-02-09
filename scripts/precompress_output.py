#!/usr/bin/env python3
"""
Precompress output/ assets with gzip sidecar files.

Why:
- Cloud Run + a simple static server won't gzip by default.
- The generated HTML can be ~16MB; gzip reduces first-load failures and improves mobile UX.

Creates: <file>.<ext>.gz next to the original file.
"""

from __future__ import annotations

import gzip
import os
import shutil
from pathlib import Path
from typing import Iterable


BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output"

COMPRESS_EXTS = {
    ".html",
    ".htm",
    ".json",
    ".xml",
    ".txt",
    ".js",
    ".css",
    ".svg",
}


def iter_files(root: Path) -> Iterable[Path]:
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in filenames:
            yield Path(dirpath) / name


def gzip_sidecar(path: Path) -> Path:
    gz_path = Path(str(path) + ".gz")
    # Skip if up-to-date
    try:
        if gz_path.exists() and gz_path.stat().st_mtime >= path.stat().st_mtime:
            return gz_path
    except OSError:
        pass

    with open(path, "rb") as f_in, open(gz_path, "wb") as f_out, gzip.GzipFile(
        filename=path.name,
        mode="wb",
        fileobj=f_out,
        compresslevel=9,
        mtime=0,
    ) as gz:
        shutil.copyfileobj(f_in, gz)
    return gz_path


def main() -> None:
    if not OUTPUT_DIR.exists():
        raise SystemExit(f"output dir not found: {OUTPUT_DIR}")

    total = 0
    compressed = 0
    for p in iter_files(OUTPUT_DIR):
        if p.suffix.lower() not in COMPRESS_EXTS:
            continue
        if p.name.endswith(".gz"):
            continue
        total += 1
        gz_path = Path(str(p) + ".gz")
        before = gz_path.exists()
        gzip_sidecar(p)
        if not before:
            compressed += 1

    print(f"Precompressed: {compressed} new gzip sidecars (considered {total} files).")


if __name__ == "__main__":
    main()
