-- ClawOS api/system.lua
-- Stable ClawOS system facade. Hardware-specific telemetry is adapter-driven.

local errors = require("core.errors")
local version = require("core.version")

local M = {}

local function unsupported(name)
    return nil, errors.new("E_UNSUPPORTED", name .. " telemetry is unavailable on this board/runtime")
end

function M.new(options)
    options = options or {}
    local api = {}

    function api.info()
        local display = nil
        if options.ui_state then
            display = {
                width = options.ui_state.width,
                height = options.ui_state.height,
            }
        end
        return {
            clawos_version = version.clawos,
            app_api = version.app_api,
            manifest_schema = version.manifest_schema,
            board = options.board,
            chip = options.chip,
            display = display,
        }
    end

    function api.now_ms()
        local fn = options.now_ms or function()
            return math.floor(os.clock() * 1000)
        end
        local ok, value = pcall(fn)
        if not ok or type(value) ~= "number" then
            return nil, errors.new("E_IO", "system clock failed", { cause = tostring(value) })
        end
        return math.floor(value)
    end

    function api.memory()
        if type(options.memory) == "function" then
            local ok, value = pcall(options.memory)
            if not ok then return nil, errors.new("E_IO", "memory telemetry failed", { cause = tostring(value) }) end
            return value
        end
        return unsupported("memory")
    end

    function api.battery()
        if type(options.battery) == "function" then
            local ok, value = pcall(options.battery)
            if not ok then return nil, errors.new("E_IO", "battery telemetry failed", { cause = tostring(value) }) end
            return value
        end
        return unsupported("battery")
    end

    function api.wifi()
        if type(options.wifi) == "function" then
            local ok, value = pcall(options.wifi)
            if not ok then return nil, errors.new("E_IO", "Wi-Fi telemetry failed", { cause = tostring(value) }) end
            return value
        end
        return unsupported("Wi-Fi")
    end

    return api
end

return M
