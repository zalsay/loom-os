local files = {}
local json_values = {}
local json_id = 0
package.preload.storage = function()
    return {
        join_path = function(a, b) return a .. "/" .. b end,
        exists = function(path) return files[path] ~= nil end,
        read_file = function(path) return files[path] end,
        write_file = function(path, value) files[path] = value; return true end,
    }
end
package.preload.json = function()
    return {
        encode = function(value)
            json_id = json_id + 1
            local key = "json:" .. json_id
            json_values[key] = value
            return key
        end,
        decode = function(key) return assert(json_values[key]) end,
    }
end
local request, callback, network_available = nil, nil, true
package.preload["system.net.request"] = function()
    return { create = function(options, cb)
        if not network_available then return nil, { code = "E_UNSUPPORTED" } end
        request, callback = options, cb
        return 1
    end }
end

local config = {
    enabled = true, channel = "dev", device_id = "test-device",
    server_url = "https://debug.example.com", token = string.rep("a", 40),
}
files["state/remote-debug.json"] = "config"
json_values.config = config

local logger = require("core.remote_debug")
assert(logger.configure({state = "state"}))
assert(logger.enabled() and files["state/remote-debug-session.txt"] == "1")
logger.write("INFO", "org.example.app", "hello", 42)
logger.write("ERROR", "runtime", "crash")
assert(logger.flush())
assert(request.url == "https://debug.example.com/v1/loom-os/devices/test-device/logs")
assert(request.headers.Authorization == "Bearer " .. config.token)
local body = json_values[request.body]
assert(body.session == "1" and #body.entries == 2)
assert(body.entries[1].message == "hello\t42")
callback(nil, {code = "E_IO"})
assert(logger.flush()) -- Failed upload remains queued.
callback({status = 204})
assert(logger.flush() == false)

logger.write("INFO", "runtime", "next")
network_available = false
local ok, err = logger.flush()
assert(ok == nil and err.code == "E_UNSUPPORTED")
network_available = true
assert(logger.flush())
callback({status = 401})
assert(logger.flush() == false) -- Stop retrying invalid credentials.

assert(logger.configure({state = "state"}))
assert(files["state/remote-debug-session.txt"] == "2")
config.channel = "stable"
local enabled, config_err = logger.configure({state = "state"})
assert(enabled == nil and config_err == "invalid remote debug config")
assert(not logger.enabled())
print("remote_debug_test: PASS")
