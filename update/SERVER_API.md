# Loom OS Runtime Release Server API v1




This is the minimal server contract used by `update/release_client.lua`.




Version syntax and publication rules are defined only by `VERSIONING.md`.




## 1. Check latest compatible release




```text
GET /v1/loom-os/releases/latest
```




Required query parameters:




```text
board=<board-id>
channel=<stable|rc|beta|dev>
current=<current-runtime-version>
bootstrap=<current-bootstrap-version>
```




Example:




```text
GET /v1/loom-os/releases/latest?board=esp-mosaico&channel=stable&current=0.1.0&bootstrap=0.1.0
```




The server MUST validate every version using the canonical grammar in `VERSIONING.md`.




## 2. Selection algorithm




For a valid request, the server:




1. selects product `loom-os`;
2. selects the requested board;
3. selects the requested channel;
4. rejects releases incompatible with the supplied bootstrap version;
5. keeps only releases where `release.version > current`;
6. chooses the highest version using canonical numeric precedence;
7. returns that immutable manifest.




The server MUST NOT compare versions lexically.




The server MUST NOT return an equal or older version.




## 3. Success responses




### Update available




```text
HTTP 200
Content-Type: application/json
```




The response body is the release manifest itself, not an envelope:




```json
{
  "schema": 1,
  "product": "loom-os",
  "board": "esp-mosaico",
  "channel": "stable",
  "version": "0.1.1",
  "release_id": "loom-os:esp-mosaico:0.1.1",
  "entry": "main.lua",
  "min_bootstrap": "0.1.0",
  "files": [
    {
      "path": "main.lua",
      "url": "https://updates.example.com/files/esp-mosaico/0.1.1/main.lua",
      "size": 5563
    }
  ]
}
```




### No update




```text
HTTP 204
```




No response body is required.




## 4. Error responses




Recommended status codes:




```text
400  invalid board/channel/version/bootstrap query
404  unsupported board or channel
500  internal release service failure
```




Loom OS treats non-2xx responses as errors.




## 5. Manifest requirements




Every HTTP 200 manifest MUST satisfy:




```text
release-manifest.schema.json
```




In addition:




- `release_id == loom-os:<board>:<version>`;
- all file URLs use HTTPS;
- each file declares its exact byte size;
- `main.lua` is present;
- the manifest is immutable after publication.




Loom OS v0.1 intentionally does not require per-file hash fields.




## 6. Device-side defense




The device does not trust the server response blindly.




`update/release_client.lua` rechecks:




- version grammar;
- channel/version suffix match;
- board;
- `release_id`;
- candidate > current;
- `min_bootstrap <= device bootstrap`.




`core/runtime_update.lua` validates again before staging/activation.




## 7. Update flow




```text
Update Center
   ↓
core.update_async.start_latest()
   ↓
ESP-Claw async Lua job
   ↓
update.release_client.latest()
   ↓
GET /v1/loom-os/releases/latest
   ↓
200 manifest / 204 no update
   ↓
runtime_update.install_default()
   ↓
staging → validation → pending_version
   ↓
foreground poll → soft restart
   ↓
confirm / rollback
```


## Reference implementation


The minimal P0 server implementation is stored under:


```text
loom-os/server/
├── main.go
├── release.go
├── publish.go
├── release_test.go
├── go.mod
└── README.md
```


Behavior implemented:


- strict Loom OS version parsing and numeric ordering;
- immutable version directories;
- bootstrap compatibility filtering;
- `GET /v1/loom-os/releases/latest`;
- HTTP 200 with a strict manifest when an update is available;
- HTTP 204 when no compatible newer release exists;
- static release-file download from manifest-listed paths only;
- exact file-size calculation during publish;
- refusal to overwrite an existing published version.


The reference service is intentionally standard-library-only and should be placed behind HTTPS termination in production. Loom OS v0.1 intentionally does not add accounts, databases, signatures, hashes, dashboards, or admin APIs.


Go unit tests cover numeric version ordering, prerelease ordering, invalid version rejection, manifest validation, latest selection, and bootstrap compatibility filtering.