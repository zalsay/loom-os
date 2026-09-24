# Loom OS Runtime OTA P0
































This updates **Loom OS itself** (Lua/LVGL runtime files), not ESP-IDF / ESP-Claw firmware.
































ESP-Claw keeps running as the host runtime. Loom OS releases live entirely in the writable DATA root, which ESP-Claw exposes through `storage.get_root_dir()`.
































## Device layout
































```text
<DATA_ROOT>/
├── loom-os/                       # Apps + appdata + logs; NOT replaced by Loom OS OTA
└── loom-os-runtime/
    ├── state.json
    ├── releases/
    │   ├── 0.1.0/
    │   │   ├── main.lua
    │   │   ├── core/
    │   │   ├── api/
    │   │   ├── ui/
    │   │   └── boards/
    │   └── 0.1.1/
    └── staging/
```
































A stable `bootstrap.lua` sits outside the versioned release directory and is not replaced by normal Loom OS updates.
































## Why version directories instead of overwriting
































A release is immutable after installation. Updating 0.1.0 -> 0.1.1 means:
































```text
download files -> staging/0.1.1
        ↓
validate every required file
        ↓
compile-check Lua files
        ↓
rename staging/0.1.1 -> releases/0.1.1
        ↓
state.pending_version = 0.1.1
        ↓
soft restart Loom OS
        ↓
bootstrap loads 0.1.1
        ↓
health checks pass
        ↓
confirm_boot()
        ↓
active_version = 0.1.1
previous_version = 0.1.0
```
































If the candidate throws before `confirm_boot()`, bootstrap clears the pending candidate and immediately loads the previous active release.
































No ESP32 reboot is required for normal Loom OS updates. A board reboot is optional and does not change firmware slots.
































## State file
































Example:
































```json
{
  "schema": 1,
  "active_version": "0.1.0",
  "previous_version": null,
  "pending_version": "0.1.1",
  "last_good_version": "0.1.0",
  "pending_attempts": 0
}
```
































The critical rule is that `active_version` is not changed until the new runtime explicitly confirms healthy boot.
































## Health checkpoint
































The candidate Loom OS should call `core.runtime_update.confirm_boot(boot_context)` only after:
































- DATA paths are available;
- App registry scan succeeds;
- Board adapter loads;
- display/touch initialize;
- Launcher is built;
- the event loop is ready to start.
































## Download backend
































`core.runtime_update.install(release, backend, on_progress)` intentionally separates update transaction logic from network transport.
































Backend contract:
































```lua
backend.download(url, destination, {
    size = 1234,
    path = "core/apps.lua",
    version = "0.1.1"
})
```
































The backend MUST:
































- use HTTPS;
- write only to the provided staging destination;
- fail closed on TLS or declared-size mismatch.
































The install routine SHOULD run in an ESP-Claw asynchronous Lua job or another system worker, not inside the LVGL callback/main loop.
































ESP-Claw already separates read-only SYSTEM from writable DATA and supports runtime Lua/file workflows, so this design does not require ESP-IDF application OTA for normal Loom OS fixes or features.
































## Update boundaries
































Loom OS Runtime OTA updates:
































- `main.lua`
- `core/`
- `api/`
- `ui/`
- `boards/`
- system Lua services belonging to Loom OS
































It does not update:
































- ESP-IDF;
- ESP-Claw C runtime;
- bootloader;
- partition table;
- built-in Lua native modules;
- user App data.
































If a future Loom OS feature requires a new native ESP-Claw Lua module, that dependency is a firmware compatibility requirement and cannot be solved by Loom OS Runtime OTA alone.
































## P0 acceptance
































- C01: install a new release without modifying the active release.
- C02: Lua syntax failure never sets `pending_version`.
- C03: download failure leaves active Loom OS untouched.
- C04: new release soft-restarts without rebooting ESP32.
- C05: candidate crash before confirmation returns to previous release.
- C06: healthy candidate confirms and becomes active.
- C07: Apps/appdata survive Loom OS update.
- C08: normal App sandbox cannot write `loom-os-runtime/`.
- C09: update progress can be surfaced by system UI.
- C10: HTTPS, version-policy, or declared-size validation failure blocks activation.
















## Async worker and strict versioning
















Runtime OTA now has an integrity + non-blocking execution layer:
















```text
core/runtime_version.lua
update/VERSIONING.md
update/release-manifest.schema.json
system/async/espclaw_jobs.lua
core/update_async.lua
update/async_install_worker.lua
```
















Runtime OTA intentionally does not use per-file hash verification in v0.1. It uses HTTPS, exact declared file sizes, manifest/version validation, Lua syntax validation, candidate confirmation, and rollback.
















Normal update execution:
















```text
Update Center / system caller
  -> core.update_async.start_latest(query)
  -> ESP-Claw lua_run_script_async
  -> update/async_install_worker.lua in separate Lua State
  -> update.release_client.latest()
  -> HTTP 200 manifest / 204 no update
  -> runtime_update.install_default()
  -> HTTP + staging + declared size + Lua syntax validation
  -> pending_version
  -> main.lua observes pending state
  -> clean soft restart
  -> bootstrap candidate boot
  -> confirm / rollback
```
















The LVGL main Lua State performs no HTTP download or release-file validation.
















The async job uses the exclusive group `loom-os-runtime-update`; v0.1 allows only one Runtime OTA job at a time.
















Device tests still required:
















- `tests/runtime_version_test.lua`
- `tests/release_client_test.lua`
- `tests/runtime_provision_check.lua`
- `tests/runtime_ota_device_start.lua`
- `tests/async_jobs_test.lua`
- `tests/update_async_test.lua`
- `tests/net_espclaw_http_smoke.lua`




## Release server contract




- `update/VERSIONING.md` — canonical version grammar and immutable publication rules.
- `update/release-manifest.schema.json` — strict release manifest schema.
- `update/SERVER_API.md` — canonical HTTP API.
- `update/release_client.lua` — device-side client and defensive validation.




Normal product flow uses:




```lua
core.update_async.start_latest({
    base_url = "https://updates.example.com",
    board = "esp-mosaico",
    channel = "stable",
    current_version = "0.1.0",
    bootstrap_version = "0.1.0"
})
```




The worker performs the network request in a separate Lua State. HTTP 204 means no update. HTTP 200 must contain a strict release manifest.


## Initial provisioning


Before testing Runtime OTA on a clean device:


1. install stable `bootstrap.lua` outside the versioned release directory;
2. copy the current Loom OS source tree to a temporary DATA directory;
3. run `provision/install_initial.lua` with `args.source_root`;
4. run `tests/runtime_provision_check.lua`;
5. start Loom OS through `bootstrap.lua`.


The provisioning script stages and validates the full Runtime before creating `releases/0.1.0` and `state.json`.


For a real `0.1.0 -> 0.1.1` test, `tests/runtime_ota_device_start.lua` performs the server query and installation in a system Lua State. Persisted `pending_version` is authoritative; the foreground Loom OS loop will request soft restart even if its in-memory update job object does not exist.