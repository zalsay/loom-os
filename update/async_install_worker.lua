-- Loom OS update/async_install_worker.lua
-- Runs in an ESP-Claw async Lua job (separate Lua State).


local storage = require("storage")
local json = require("json")
local runtime_update = require("core.runtime_update")
local release_client = require("update.release_client")


local request_path = args and args.request_path
assert(type(request_path) == "string" and request_path ~= "", "args.request_path is required")


local raw = assert(storage.read_file(request_path), "failed to read update request")
local request = assert(json.decode(raw), "invalid update request JSON")
assert(type(request) == "table", "update request must be a table")
assert(type(request.result_path) == "string" and request.result_path ~= "",
    "request.result_path is required")


local function write_result(value)
    local text = assert(json.encode(value), "failed to encode update result")
    assert(storage.write_file(request.result_path, text), "failed to write update result")
end


local function fail(message)
    write_result({
        status = "failed",
        mode = request.mode,
        message = tostring(message),
    })
    error("LOOM_OS_UPDATE_FAILED " .. tostring(message))
end


local release


if request.mode == "latest" then
    local latest, latest_err = release_client.latest(request.query)
    if not latest then
        local message = type(latest_err) == "table"
            and (latest_err.message or latest_err.code)
            or tostring(latest_err)
        fail(message)
    end


    if not latest.available then
        write_result({
            status = "no_update",
            mode = "latest",
            current_version = request.query.current_version,
        })
        print("LOOM_OS_UPDATE_NO_UPDATE " .. tostring(request.query.current_version))
        return
    end


    release = latest.release
elseif request.mode == "direct" then
    release = request.release
else
    fail("unsupported update request mode")
end


assert(type(release) == "table", "release manifest is required")


local function progress(p)
    print(string.format("LOOM_OS_UPDATE_PROGRESS %d/%d %s",
        tonumber(p.index) or 0,
        tonumber(p.total) or 0,
        tostring(p.path or "")))
end


local ok, err = runtime_update.install_default(release, progress)
if not ok then
    local message = type(err) == "table" and (err.message or err.code) or tostring(err)
    fail(message)
end


write_result({
    status = "ready",
    mode = request.mode,
    version = release.version,
    release_id = release.release_id,
})


print("LOOM_OS_UPDATE_READY " .. tostring(release.version))