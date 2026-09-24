-- ClawOS Phase 1 device-side seed + scan test.
-- Creates one valid App and one invalid path-traversal App in DATA storage,
-- then runs apps.scan() and checks isolation behavior.

local storage = require("storage")
local json = require("json")
local paths_mod = require("core.paths")
local apps = require("core.apps")

local paths, err = paths_mod.resolve()
assert(paths, err and err.message or "paths.resolve failed")
assert(paths_mod.ensure_layout(paths))

local function ensure_dir(path)
    if not storage.exists(path) then
        storage.mkdir(path)
    end
end

local function write_app(app_id, manifest, main_lua)
    local dir = storage.join_path(paths.apps, app_id)
    ensure_dir(dir)
    storage.write_file(storage.join_path(dir, "manifest.json"), json.encode(manifest))
    if main_lua then
        storage.write_file(storage.join_path(dir, "main.lua"), main_lua)
    end
end

write_app("org.clawos.hello", {
    schema = 1,
    api = "0.1",
    id = "org.clawos.hello",
    name = "Hello",
    version = "0.1.0",
    entry = "main.lua",
    min_clawos = "0.1.0",
    permissions = {},
}, [[
return {
    on_create = function(ctx, args)
        print("Hello ClawOS")
    end,
}
]])

write_app("org.clawos.invalid-path", {
    schema = 1,
    api = "0.1",
    id = "org.clawos.invalid-path",
    name = "Invalid Path Fixture",
    version = "0.1.0",
    entry = "../main.lua",
    min_clawos = "0.1.0",
    permissions = {},
}, nil)

local result, scan_err = apps.scan()
assert(result, scan_err and scan_err.message or "apps.scan failed")

local hello = result.apps["org.clawos.hello"]
assert(hello and hello.enabled, "T01 failed: Hello App was not discovered")

local found_invalid = false
for _, record in ipairs(result.invalid) do
    if record.source_name == "org.clawos.invalid-path" then
        found_invalid = true
        assert(record.error, "T02/T04 failed: invalid App has no error")
        assert(record.error.code == "E_INVALID_ARG", "T04 failed: expected E_INVALID_ARG")
    end
end
assert(found_invalid, "T02/T04 failed: invalid path App was not isolated")

print("PASS T01 App Discovery")
print("PASS T02 Invalid Manifest Isolation")
print("PASS T04 Path Escape")
print("APPS_ROOT:", result.paths.apps)
