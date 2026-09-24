#!/usr/bin/env python3
"""Minimal ClawOS Runtime release server v1.

Standard-library only. Put it behind HTTPS termination in production.
"""
from __future__ import annotations

import argparse
import json
import mimetypes
import os
import re
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path, PurePosixPath
from typing import Any, Iterable
from urllib.parse import parse_qs, unquote, urlparse

VERSION_RE = re.compile(
    r"^(0|[1-9][0-9]*)\."
    r"(0|[1-9][0-9]*)\."
    r"(0|[1-9][0-9]*)"
    r"(?:-(dev|beta|rc)\.([1-9][0-9]*))?$"
)
BOARD_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
CHANNEL_RANK = {"dev": 1, "beta": 2, "rc": 3, "stable": 4}
CHANNELS = frozenset(CHANNEL_RANK)


class ReleaseError(ValueError):
    pass


@dataclass(frozen=True)
class Version:
    major: int
    minor: int
    patch: int
    channel_rank: int
    sequence: int
    raw: str

    @property
    def channel(self) -> str:
        for name, rank in CHANNEL_RANK.items():
            if rank == self.channel_rank:
                return name
        raise AssertionError("invalid channel rank")

    def key(self) -> tuple[int, int, int, int, int]:
        return (self.major, self.minor, self.patch, self.channel_rank, self.sequence)

    def __lt__(self, other: "Version") -> bool:
        return self.key() < other.key()

    def __le__(self, other: "Version") -> bool:
        return self.key() <= other.key()


def parse_version(raw: str) -> Version:
    if not isinstance(raw, str) or not raw or len(raw) > 32:
        raise ReleaseError("version must be a non-empty string up to 32 characters")
    match = VERSION_RE.fullmatch(raw)
    if not match:
        raise ReleaseError("invalid ClawOS version")
    major, minor, patch, prerelease, sequence = match.groups()
    channel = prerelease or "stable"
    return Version(
        int(major), int(minor), int(patch), CHANNEL_RANK[channel], int(sequence or 0), raw
    )


def validate_board(board: str) -> str:
    if not isinstance(board, str) or not BOARD_RE.fullmatch(board):
        raise ReleaseError("invalid board")
    return board


def safe_relative(path: str) -> bool:
    if not isinstance(path, str) or not path or "\\" in path:
        return False
    p = PurePosixPath(path)
    if p.is_absolute():
        return False
    return all(part not in ("", ".", "..") for part in p.parts)


def validate_manifest(manifest: dict[str, Any]) -> Version:
    if not isinstance(manifest, dict):
        raise ReleaseError("manifest must be an object")
    if manifest.get("schema") != 1:
        raise ReleaseError("schema must be 1")
    if manifest.get("product") != "clawos":
        raise ReleaseError("product must be clawos")

    board = validate_board(manifest.get("board"))
    channel = manifest.get("channel")
    if channel not in CHANNELS:
        raise ReleaseError("invalid channel")

    version = parse_version(manifest.get("version"))
    if version.channel != channel:
        raise ReleaseError("version suffix does not match channel")

    expected_id = f"clawos:{board}:{version.raw}"
    if manifest.get("release_id") != expected_id:
        raise ReleaseError(f"release_id must equal {expected_id}")
    if manifest.get("entry") != "main.lua":
        raise ReleaseError("entry must be main.lua")

    parse_version(manifest.get("min_bootstrap"))

    files = manifest.get("files")
    if not isinstance(files, list) or not files:
        raise ReleaseError("files must be a non-empty array")

    seen: set[str] = set()
    for item in files:
        if not isinstance(item, dict):
            raise ReleaseError("invalid file entry")
        path = item.get("path")
        url = item.get("url")
        size = item.get("size")
        if not safe_relative(path):
            raise ReleaseError(f"invalid file path: {path!r}")
        if path in seen:
            raise ReleaseError(f"duplicate file path: {path}")
        seen.add(path)
        if not isinstance(url, str) or not url.startswith("https://"):
            raise ReleaseError(f"file url must use HTTPS: {path}")
        if isinstance(size, bool) or not isinstance(size, int) or size < 1:
            raise ReleaseError(f"file size must be a positive integer: {path}")

    if "main.lua" not in seen:
        raise ReleaseError("files must include main.lua")
    return version


class ReleaseStore:
    def __init__(self, root: Path):
        self.root = root.resolve()

    def board_root(self, board: str) -> Path:
        validate_board(board)
        return self.root / "clawos" / board

    def release_root(self, board: str, version: str) -> Path:
        parse_version(version)
        return self.board_root(board) / version

    def manifest_path(self, board: str, version: str) -> Path:
        return self.release_root(board, version) / "manifest.json"

    def load_manifest(self, board: str, version: str) -> dict[str, Any]:
        path = self.manifest_path(board, version)
        with path.open("r", encoding="utf-8") as fh:
            manifest = json.load(fh)
        validate_manifest(manifest)
        if manifest["board"] != board or manifest["version"] != version:
            raise ReleaseError("manifest identity does not match directory")
        return manifest

    def iter_manifests(self, board: str) -> Iterable[dict[str, Any]]:
        root = self.board_root(board)
        if not root.is_dir():
            return []
        manifests: list[dict[str, Any]] = []
        for child in root.iterdir():
            if not child.is_dir():
                continue
            try:
                parse_version(child.name)
                manifests.append(self.load_manifest(board, child.name))
            except (OSError, json.JSONDecodeError, ReleaseError):
                continue
        return manifests

    def latest(self, board: str, channel: str, current: str, bootstrap: str) -> dict[str, Any] | None:
        validate_board(board)
        if channel not in CHANNELS:
            raise ReleaseError("invalid channel")
        current_v = parse_version(current)
        bootstrap_v = parse_version(bootstrap)

        candidates: list[tuple[Version, dict[str, Any]]] = []
        for manifest in self.iter_manifests(board):
            if manifest["channel"] != channel:
                continue
            version = validate_manifest(manifest)
            if version <= current_v:
                continue
            if parse_version(manifest["min_bootstrap"]) > bootstrap_v:
                continue
            candidates.append((version, manifest))

        if not candidates:
            return None
        candidates.sort(key=lambda pair: pair[0].key())
        return candidates[-1][1]

    def resolve_file(self, board: str, version: str, relative: str) -> Path:
        validate_board(board)
        parse_version(version)
        relative = unquote(relative)
        if not safe_relative(relative):
            raise ReleaseError("invalid file path")
        root = self.release_root(board, version).resolve()
        candidate = (root / relative).resolve()
        if root != candidate and root not in candidate.parents:
            raise ReleaseError("file path escaped release root")
        manifest = self.load_manifest(board, version)
        allowed = {item["path"] for item in manifest["files"]}
        if relative not in allowed:
            raise ReleaseError("file is not part of published manifest")
        return candidate


class ReleaseHandler(BaseHTTPRequestHandler):
    server_version = "ClawOSReleaseServer/1"

    @property
    def store(self) -> ReleaseStore:
        return self.server.release_store  # type: ignore[attr-defined]

    def _json_error(self, status: HTTPStatus, message: str) -> None:
        body = json.dumps({"error": message}, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/v1/clawos/releases/latest":
            return self._latest(parsed.query)
        if parsed.path.startswith("/files/"):
            return self._file(parsed.path)
        self._json_error(HTTPStatus.NOT_FOUND, "not found")

    def _latest(self, query: str) -> None:
        params = parse_qs(query, keep_blank_values=True)
        required = ("board", "channel", "current", "bootstrap")
        if any(len(params.get(key, [])) != 1 or params[key][0] == "" for key in required):
            return self._json_error(
                HTTPStatus.BAD_REQUEST,
                "board, channel, current and bootstrap are required",
            )

        board = params["board"][0]
        channel = params["channel"][0]
        current = params["current"][0]
        bootstrap = params["bootstrap"][0]
        try:
            validate_board(board)
            if not self.store.board_root(board).is_dir():
                return self._json_error(HTTPStatus.NOT_FOUND, "unsupported board")
            manifest = self.store.latest(board, channel, current, bootstrap)
        except ReleaseError as exc:
            return self._json_error(HTTPStatus.BAD_REQUEST, str(exc))

        if manifest is None:
            self.send_response(HTTPStatus.NO_CONTENT)
            self.end_headers()
            return

        body = json.dumps(manifest, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _file(self, path: str) -> None:
        parts = path.split("/", 4)
        if len(parts) != 5 or not parts[2] or not parts[3] or not parts[4]:
            return self._json_error(HTTPStatus.NOT_FOUND, "not found")
        _, _, board, version, relative = parts
        try:
            file_path = self.store.resolve_file(board, version, relative)
        except (ReleaseError, OSError, json.JSONDecodeError):
            return self._json_error(HTTPStatus.NOT_FOUND, "not found")
        if not file_path.is_file():
            return self._json_error(HTTPStatus.NOT_FOUND, "not found")
        data = file_path.read_bytes()
        mime = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt: str, *args: object) -> None:
        if os.environ.get("CLAWOS_SERVER_QUIET") == "1":
            return
        super().log_message(fmt, *args)


class ReleaseHTTPServer(ThreadingHTTPServer):
    def __init__(self, addr: tuple[str, int], store: ReleaseStore):
        super().__init__(addr, ReleaseHandler)
        self.release_store = store


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=os.environ.get("CLAWOS_RELEASE_ROOT", "./release-data"))
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()

    store = ReleaseStore(Path(args.root))
    server = ReleaseHTTPServer((args.host, args.port), store)
    print(f"ClawOS release server: http://{args.host}:{args.port} root={store.root}")
    print("Production deployment must put this service behind HTTPS termination.")
    server.serve_forever()


if __name__ == "__main__":
    main()
