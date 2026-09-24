-- ClawOS Phase 2 core test.
-- Covers ResourceRegistry, permissions, sandbox restrictions and Service ctx isolation.

local storage = require("storage")
local json = require("json")
local paths_mod = require("core.paths")
local apps = require("core.apps")
local resources_mod = require("core.resources")
local permissions = require("core.permissions")
local sandbox = require("core.sandbox")
local context = require("core.context")

local paths = assert(paths_mod.resolve())
assert(paths_mod.ensure_layout(paths))

local function ensure_dir(path)
    if not storage.exists(path) then storage.mkdir(path) end
end

local app_dir = storage.join_path(paths.apps, "org.clawos.sandbox")
local lib_dir = storage.join_path(app_dir, "lib")
ensure_dir(app_dir)
ensure_dir(lib_dir)

storage.write_file(storage.join_path(app_dir, "manifest.json"), json.encode({
    schema = 1,
    api = "0.1",
    id = "org.clawos.sandbox",
    name = "Sandbox Fixture",
    version = "0.1.0",
    entry = "main.lua",
    min_clawos = "0.1.0",
    permissions = {
        gpio = { pins = {10} },
        sensor = {"environment"},
    },
}))

storage.write_file(storage.join_path(lib_dir, "greeting.lua"), [[
return {
    text = function(name)
        return "Hello " .. tostring(name)
    end,
}
]])

storage.write_file(storage.join_path(app_dir, "main.lua"), [[
local greeting = require("greeting")
return {
    on_create = function(ctx, args)
        assert(io == nil)
        assert(os == nil)
        assert(debug == nil)
        local mutate_ok = pcall(function() math.pi = 0 end)
        assert(not mutate_ok)
        assert(greeting.text("ClawOS") == "Hello ClawOS")
    end,
}
]])

local scan = assert(apps.scan())
local record = assert(scan.apps["org.clawos.sandbox"], "Sandbox fixture missing")
record.data_dir = storage.join_path(paths.appdata, record.id)
record.assets_dir = storage.join_path(record.dir, "assets")

-- T05 permission behavior.
assert(permissions.check(record, "gpio", { pin = 10 }))
local allowed, denied = permissions.check(record, "gpio", { pin = 11 })
assert(not allowed and denied.code == "E_PERMISSION")
assert(permissions.check(record, "sensor", { id = "environment" }))

-- ResourceRegistry must continue cleanup even when one release callback fails.
local registry = assert(resources_mod.new(1001))
local released = {}
assert(registry:add("timers", "t1", function(v) released[#released + 1] = v; return true end))
assert(registry:add("gpio", "g1", function(v) released[#released + 1] = v; error("intentional release error") end))
assert(registry:add("other", "o1", function(v) released[#released + 1] = v; return true end))
local cleanup_ok, cleanup_errors = registry:release_all()
assert(not cleanup_ok)
assert(#cleanup_errors == 1)
assert(#released == 3)

-- Callback generation guard: stopped registry rejects callbacks.
local guarded_registry = assert(resources_mod.new(1002))
local guarded = guarded_registry:guard(function() return "ran" end)
assert(guarded() == "ran")
guarded_registry:release_all()
local result, guard_err = guarded()
assert(result == nil and guard_err.code == "E_CANCELLED")

-- Sandbox: local require works; privileged globals/modules are unavailable.
local env, cache = assert(sandbox.build(record))
local app_def = assert(sandbox.load_entry(record, env))
assert(type(app_def.on_create) == "function")

local ctx = assert(context.new_app(record, assert(resources_mod.new(1003)), {
    storage = { read_text = function() end },
    ui = { root = {} },
    nav = { home = function() end },
}))
assert(ctx.ui ~= nil and ctx.nav ~= nil)
app_def.on_create(ctx, {})

-- Native modules cannot be required through App-local require.
local require_ok = pcall(env.require, "gpio")
assert(not require_ok, "T03 failed: native gpio module should be blocked")

-- T11 service ctx must not expose UI/navigation.
local service_ctx = assert(context.new_service(record, { id = "svc" }, assert(resources_mod.new(1004)), {
    storage = {},
    ui = { root = {} },
    nav = { home = function() end },
}))
assert(service_ctx.ui == nil)
assert(service_ctx.nav == nil)

sandbox.clear_cache(cache)

print("PASS T03 Sandbox")
print("PASS T05 GPIO Permission")
print("PASS T08 Callback Generation Guard core primitive")
print("PASS T11 Service UI Isolation")
print("PASS ResourceRegistry fail-safe teardown")
