-- Host integration: real Lua modules and staged files, mocked ESP-Claw storage/JSON/GPIO.
local base = "./.host-patch-test"
os.execute("rm -rf " .. base)
os.execute("mkdir -p " .. base)
local function q(path) return "'" .. path:gsub("'", "'\\''") .. "'" end
local function join(...)
    local parts = {...}
    local path = table.concat(parts, "/"):gsub("/+", "/")
    return path
end
local function exists(path)
    local f = io.open(path, "rb")
    if f then f:close(); return true end
    local result = os.rename(path, path); return result == true or result == 0
end
package.preload.storage = function()
    return {
        get_root_dir = function() return base end,
        join_path = join,
        exists = exists,
        mkdir = function(path) local result = os.execute("mkdir -p " .. q(path)); return result == true or result == 0 end,
        read_file = function(path) local f = assert(io.open(path,"rb")); local v = f:read("*a"); f:close(); return v end,
        write_file = function(path, value) local f = assert(io.open(path,"wb")); f:write(value); f:close(); return true end,
        rename = os.rename,
        remove = os.remove,
        listdir = function(path)
            local is_dir = os.execute("test -d " .. q(path))
            if is_dir ~= true and is_dir ~= 0 then error("not a directory") end
            local handle = assert(io.popen("ls -A " .. q(path)))
            local items = {}
            for name in handle:lines() do items[#items + 1] = name end
            handle:close(); return items
        end,
    }
end
local encoded, next_json = {}, 0
package.preload.json = function()
    return {
        encode = function(value) next_json = next_json + 1; local key = "@json:" .. next_json; encoded[key] = value; return key end,
        decode = function(text) assert(encoded[text], "invalid fixture JSON"); return encoded[text] end,
    }
end
package.preload.gpio = function() return {} end

local function check(ok, err) if not ok then print("CHECK FAIL", err and err.code, err and err.message, err and err.detail and err.detail.cause, err and err.detail and err.detail.path) end; assert(ok, err and (err.message or tostring(err))); return ok end
local backend = require("core.app_backend")
local updater = require("core.app_update").new(backend)
local apps = require("core.apps")
local runtime = require("core.app_runtime")
local storage = require("storage")
local paths = assert(require("core.paths").resolve())
local layout, layout_err = require("core.paths").ensure_layout(paths)
if not layout then print("layout",layout_err and layout_err.message,layout_err and layout_err.detail and layout_err.detail.path,layout_err and layout_err.detail and layout_err.detail.cause) end
check(layout, layout_err)

local function pkg(id, version, source, extra, permissions, services)
    local files = { { path = "main.lua", content = source } }
    for _, f in ipairs(extra or {}) do files[#files + 1] = f end
    return { manifest = { schema = 1, api = "0.1", min_loom_os = "0.1.0", id = id,
        name = "Test App", version = version, entry = "main.lua",
        permissions = permissions or {}, services = services }, files = files }
end
local id = "org.loom-os.integration"
local service_file = { path = "services/monitor.lua", content = [[return {
  on_start = function(ctx)
    assert(ctx.ui == nil and ctx.nav == nil)
    ctx.storage.write_text("started.txt", "yes")
    ctx.timer.every(1000, function() end)
  end
}]] }
local v1 = pkg(id, "1.0.0", [[return { on_create = function(ctx)
  assert(ctx.service.start("monitor"))
end }]], {service_file}, {background=true}, {{id="monitor",entry="services/monitor.lua"}})
check(updater.install(v1))
assert(backend.read_state(id).pending_version == "1.0.0")
local scanned = check(apps.scan()); assert(scanned.apps[id].dir:find("releases/1.0.0", 1, true))
local layer = { clean = function() end }
local widget = { is_valid = function() return true end, delete = function() end }
runtime.configure({ ui_state = { app_layer = layer, lvgl = {container=function() return widget end},
    app_width=480, app_height=480 }, system_options={board="mosaico"} })
check(runtime.launch(id))
assert(backend.read_state(id).active_version == "1.0.0")
assert(require("core.service_runner").exists(id .. ":monitor"))
check(runtime.stop("home"))
assert(require("core.service_runner").exists(id .. ":monitor")) -- service survives UI close
assert(storage.read_file(join(paths.appdata,id,"started.txt")) == "yes")

local bad, bad_err = updater.install(pkg(id, "1.0.1", "return true", {{path="../escape.lua",content="bad"}}))
assert(bad == nil and bad_err.code == "E_APP_PATH")
assert(backend.read_state(id).pending_version == nil)
local crash = pkg(id, "1.0.1", [[return { on_create=function() error("candidate crash") end }]])
check(updater.install(crash)); check(apps.scan())
local launched, launch_err = runtime.launch(id)
assert(launched == nil and launch_err.code == "E_CRASH")
assert(backend.read_state(id).active_version == "1.0.0")
assert(backend.read_state(id).pending_version == nil)
assert(require("core.service_runner").exists(id .. ":monitor")) -- old service restored
assert(storage.read_file(join(paths.appdata,id,"started.txt")) == "yes")
local v2 = pkg(id, "1.0.2", "return { on_create=function() end }")
check(updater.install(v2)); check(apps.scan()); check(runtime.launch(id))
assert(backend.read_state(id).active_version == "1.0.2")
assert(not require("core.service_runner").exists(id .. ":monitor")) -- old version stopped
check(runtime.stop("home"))
local invalid_lua = pkg(id, "1.0.3", "return {")
assert(updater.install(invalid_lua) == nil)
assert(not backend.release_exists(id, "1.0.3"))
assert(backend.read_state(id).pending_version == nil)
local failed_state_backend = setmetatable({write_state=function()
    return nil, {code="E_IO",message="simulated state failure"}
end}, {__index=backend})
assert(require("core.app_update").new(failed_state_backend).install(pkg(id, "1.0.4", "return {on_create=function() end}")) == nil)
assert(not backend.release_exists(id, "1.0.4"))
local service_crash = pkg(id, "1.0.5", [[return {on_create=function(ctx)
    assert(ctx.service.start("monitor")); error("crash after service start")
end}]], {service_file}, {background=true}, {{id="monitor",entry="services/monitor.lua"}})
check(updater.install(service_crash)); check(apps.scan())
assert(runtime.launch(id) == nil)
assert(not require("core.service_runner").exists(id .. ":monitor"))
assert(backend.read_state(id).active_version == "1.0.2")

local provider = { generate_app = function()
    return { operation="create", manifest = {schema=1,api="0.1",min_loom_os="0.1.0",
        id="org.loom-os.generated",name="Generated",version="1.0.0",entry="main.lua",permissions={}},
        files={{path="main.lua",content="return { on_create=function(ctx) end }"}} }
end }
local author = require("core.creator_runtime").new(provider)
local draft = check(author.create({prompt="demo"}))
assert(draft.report.ok)
local installed = check(author.install(draft.draft_id, {permissions={}}))
assert(installed.pending and backend.read_state("org.loom-os.generated").pending_version == "1.0.0")
local forbidden = require("core.app_validator").new({
    lua_check=function() return true end, api_check=function() return true end,
    board_check=function() return true end,
})
local no, err = forbidden.validate_draft("x", {manifest={permissions={}},files={{path="main.lua",content="require('os')"}}})
assert(no == nil and err.code == "E_VALIDATE_REQUIRE")
local ota = require("core.runtime_update")
local release = require("tests.ota_full_flow_test")(ota, storage, base)
require("tests.ota_rollback_test")(ota, release, storage)
require("tests.ota_bad_manifest_test")(ota, release)
require("tests.ota_size_mismatch_test")(ota, release)
for _, name in ipairs({
    "service_runner_test", "network_agent_api_test", "app_update_test",
    "app_bad_package_test", "app_author_test", "app_modify_guard_test",
    "app_permission_review_test", "runtime_version_test", "phase7_mosaico_board_test",
}) do dofile("tests/" .. name .. ".lua") end
print("patch01_08_integration_test: PASS")
