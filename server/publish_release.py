#!/usr/bin/env python3
"""Publish one immutable ClawOS Runtime release into the file-backed store."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from urllib.parse import quote

from release_server import ReleaseError, ReleaseStore, parse_version, validate_manifest


def file_url(base: str, board: str, version: str, relative: str) -> str:
    base = base.rstrip("/")
    escaped = "/".join(quote(seg, safe="") for seg in relative.split("/"))
    return f"{base}/files/{quote(board, safe='')}/{quote(version, safe='')}/{escaped}"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--store-root", required=True)
    p.add_argument("--source-root", required=True)
    p.add_argument("--manifest", required=True, help="manifest template containing canonical path list")
    p.add_argument("--public-base-url", required=True)
    args = p.parse_args()

    if not args.public_base_url.startswith("https://"):
        raise SystemExit("public base URL must use HTTPS")

    store = ReleaseStore(Path(args.store_root))
    source_root = Path(args.source_root).resolve()
    with open(args.manifest, "r", encoding="utf-8") as fh:
        manifest = json.load(fh)

    version = parse_version(manifest.get("version")).raw
    board = manifest.get("board")
    target = store.release_root(board, version)
    if target.exists():
        raise SystemExit(f"release already exists and is immutable: {target}")

    files = manifest.get("files")
    if not isinstance(files, list) or not files:
        raise SystemExit("manifest files are required")

    for item in files:
        relative = item.get("path")
        if not isinstance(relative, str):
            raise SystemExit("invalid file path")
        source = (source_root / relative).resolve()
        if source_root != source and source_root not in source.parents:
            raise SystemExit(f"source path escaped source root: {relative}")
        if not source.is_file():
            raise SystemExit(f"source file missing: {relative}")
        item["size"] = source.stat().st_size
        item["url"] = file_url(args.public_base_url, board, version, relative)

    try:
        validate_manifest(manifest)
    except ReleaseError as exc:
        raise SystemExit(str(exc)) from exc

    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix=f".{version}.publishing-", dir=target.parent))
    try:
        for item in manifest["files"]:
            relative = item["path"]
            src = source_root / relative
            dst = tmp / relative
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)
            if dst.stat().st_size != item["size"]:
                raise SystemExit(f"copied size mismatch: {relative}")

        with (tmp / "manifest.json").open("w", encoding="utf-8", newline="\n") as fh:
            json.dump(manifest, fh, ensure_ascii=False, indent=2)
            fh.write("\n")

        os.rename(tmp, target)
        tmp = None
    finally:
        if tmp is not None and tmp.exists():
            shutil.rmtree(tmp)

    print(f"published {manifest['release_id']} -> {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
