# ClawOS Release Server

Minimal reference server for ClawOS Runtime OTA v1.

## Scope

This server intentionally implements only the P0 contract:

- strict ClawOS version parsing and ordering;
- immutable per-board releases;
- `GET /v1/clawos/releases/latest`;
- `HTTP 200` with a release manifest when an update is available;
- `HTTP 204` when no compatible newer release exists;
- static release-file download under `/files/...`;
- exact file sizes in manifests;
- bootstrap compatibility filtering.

It intentionally does **not** add accounts, database state, signing, hashes, dashboards, or admin APIs.

## Files

- `release_server.py` — file-backed HTTP service.
- `publish_release.py` — immutable release publisher.
- `tests/test_release_server.py` — version/manifest/store unit tests.

## Store layout

```text
release-data/
└── clawos/
    └── esp-mosaico/
        └── 0.1.1/
            ├── manifest.json
            ├── main.lua
            ├── core/
            ├── system/
            └── update/
```

## Run tests

```bash
python3 -m unittest discover -s tests -v
```

## Publish

Start from a manifest template that already has the canonical file path list. The publisher recalculates `size` and rewrites file URLs to the configured public base URL.

```bash
python3 publish_release.py \
  --store-root ./release-data \
  --source-root ./clawos-0.1.1 \
  --manifest ./release-manifest.json \
  --public-base-url https://updates.example.com
```

Publishing fails if the target version directory already exists. A published version is immutable; fixes require a new version.

## Run server

```bash
python3 release_server.py \
  --root ./release-data \
  --host 127.0.0.1 \
  --port 8080
```

For production, place this process behind HTTPS termination/reverse proxy. Device-facing manifest/file URLs must be HTTPS because ClawOS rejects plain HTTP by default.

## Device query

```text
GET /v1/clawos/releases/latest?board=esp-mosaico&channel=stable&current=0.1.0&bootstrap=0.1.0
```

The server uses the same version precedence as `ClawOS/update/VERSIONING.md`.
