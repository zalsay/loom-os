-- ClawOS tests/runtime_ota_device_start.lua
-- Real-device server/download/staging smoke test.
-- Run in a system Lua State, preferably through ESP-Claw async execution.


local release_client = require("update.release_client")
local runtime_update = require("core.runtime_update")


assert(args and type(args.base_url) == "string", "args.base_url is required")
local channel = args.channel or "stable"
local board = args.board or "esp-mosaico"
local bootstrap_version = args.bootstrap_version or "0.1.0"


local state = assert(runtime_update.status())
assert(type(state.active_version) == "string", "Runtime active_version is missing")
assert(state.pending_version == nil, "Runtime already has a pending_version")


local latest, latest_err = release_client.latest({
    base_url = args.base_url,
    board = board,
    channel = channel,
    current_version = state.active_version,
    bootstrap_version = bootstrap_version,
})
assert(latest, latest_err and (latest_err.message or latest_err.code) or "release lookup failed")


if not latest.available then
    print("runtime_ota_device_start: NO_UPDATE active=" .. state.active_version)
    return
end


local release = latest.release
print("runtime_ota_device_start: candidate=" .. tostring(release.version))


local installed, install_err = runtime_update.install_default(release, function(progress)
    print(string.format("runtime_ota_device_start: %d/%d %s",
        tonumber(progress.index) or 0,
        tonumber(progress.total) or 0,
        tostring(progress.path or "")))
end)
assert(installed, install_err and (install_err.message or install_err.code) or "Runtime install failed")


local after = assert(runtime_update.status())
assert(after.pending_version == release.version, "pending_version was not committed")
assert(after.active_version == state.active_version, "active_version changed before candidate confirmation")


print("runtime_ota_device_start: PASS pending=" .. release.version)
print("The running ClawOS main loop will observe pending_version and soft-restart through bootstrap.")