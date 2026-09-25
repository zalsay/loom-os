-- System-owned preferences and optional board settings providers.
local storage = require("storage")
local json = require("json")
local errors = require("core.errors")

local M = {}
local path, providers = nil, {}
local values = { theme = "dark" }

local function fail(code, message)
    return nil, errors.new(code, message)
end

local function save(candidate)
    if not path then return fail("E_BUSY", "settings are not configured") end
    local ok, body = pcall(json.encode, { schema = 1, theme = candidate.theme,
        brightness = candidate.brightness, volume = candidate.volume })
    if not ok then return fail("E_IO", "cannot encode settings") end
    local wrote, result = pcall(storage.write_file, path, body)
    if not wrote or not result then return fail("E_IO", "cannot save settings") end
    values = candidate
    return true
end

local function percent(value, minimum)
    return type(value) == "number" and value % 1 == 0 and value >= minimum and value <= 100
end

local function apply(provider, method, value)
    if type(provider) ~= "table" or type(provider[method]) ~= "function" then
        return fail("E_UNSUPPORTED", method .. " is unavailable on this firmware")
    end
    local ok, result, err = pcall(provider[method], value)
    if not ok or not result then return fail("E_IO", tostring(err or result or "device setting failed")) end
    return true
end

function M.configure(paths, hooks)
    if type(paths) ~= "table" or type(paths.state) ~= "string" then
        return fail("E_INVALID_ARG", "settings state directory is required")
    end
    local target = storage.join_path(paths.state, "settings.json")
    local candidate = { theme = "dark" }
    if storage.exists(target) then
        local read_ok, body = pcall(storage.read_file, target)
        if not read_ok or type(body) ~= "string" or #body > 1024 then
            return fail("E_IO", "invalid settings file")
        end
        local decoded, data = pcall(json.decode, body)
        if not decoded or type(data) ~= "table" or data.schema ~= 1 or
            (data.theme ~= "dark" and data.theme ~= "light") or
            (data.brightness ~= nil and not percent(data.brightness, 5)) or
            (data.volume ~= nil and not percent(data.volume, 0)) then
            return fail("E_IO", "invalid settings file")
        end
        candidate = { theme = data.theme, brightness = data.brightness, volume = data.volume }
    end
    path, providers, values = target, hooks or {}, candidate
    if type(providers.theme) == "function" then
        local applied, result = pcall(providers.theme, values.theme)
        if not applied or result == false then return fail("E_IO", "cannot restore theme") end
    end
    if values.brightness and type(providers.display) == "table" and
        type(providers.display.set_brightness) == "function" then
        local applied, err = apply(providers.display, "set_brightness", values.brightness)
        if not applied then return nil, err end
    end
    if values.volume and type(providers.audio) == "table" and
        type(providers.audio.set_volume) == "function" then
        local applied, err = apply(providers.audio, "set_volume", values.volume)
        if not applied then return nil, err end
    end
    return true
end

function M.snapshot()
    return {
        theme = values.theme, brightness = values.brightness, volume = values.volume,
        brightness_available = type(providers.display) == "table" and
            type(providers.display.set_brightness) == "function",
        volume_available = type(providers.audio) == "table" and
            type(providers.audio.set_volume) == "function",
        wifi_available = type(providers.wifi) == "table" and
            type(providers.wifi.connect) == "function",
    }
end

function M.set_theme(theme)
    if theme ~= "dark" and theme ~= "light" then return fail("E_INVALID_ARG", "invalid theme") end
    if type(providers.theme) == "function" then
        local ok, result = pcall(providers.theme, theme)
        if not ok or result == false then return fail("E_IO", "cannot apply theme") end
    end
    local candidate = { theme = theme, brightness = values.brightness, volume = values.volume }
    local saved, err = save(candidate)
    if not saved and type(providers.theme) == "function" then pcall(providers.theme, values.theme) end
    return saved, err
end

function M.set_brightness(value)
    if not percent(value, 5) then return fail("E_INVALID_ARG", "brightness must be 5–100") end
    local ok, err = apply(providers.display, "set_brightness", value)
    if not ok then return nil, err end
    return save({ theme = values.theme, brightness = value, volume = values.volume })
end

function M.set_volume(value)
    if not percent(value, 0) then return fail("E_INVALID_ARG", "volume must be 0–100") end
    local ok, err = apply(providers.audio, "set_volume", value)
    if not ok then return nil, err end
    return save({ theme = values.theme, brightness = values.brightness, volume = value })
end

function M.wifi_status()
    if type(providers.wifi) ~= "table" or type(providers.wifi.status) ~= "function" then
        return fail("E_UNSUPPORTED", "Wi-Fi status is unavailable on this firmware")
    end
    local ok, result = pcall(providers.wifi.status)
    if not ok or type(result) ~= "table" then return fail("E_IO", "cannot read Wi-Fi status") end
    return {
        connected = result.connected == true,
        ssid = type(result.ssid) == "string" and result.ssid:sub(1, 32) or nil,
        ip = type(result.ip) == "string" and result.ip:sub(1, 64) or nil,
    }
end

function M.connect_wifi(ssid, password)
    if type(ssid) ~= "string" or #ssid < 1 or #ssid > 32 or type(password) ~= "string" or
        #password > 63 or (#password > 0 and #password < 8) then
        return fail("E_INVALID_ARG", "invalid Wi-Fi credentials")
    end
    -- Credentials are passed only to the firmware provider; never stored in settings.json.
    if type(providers.wifi) ~= "table" or type(providers.wifi.connect) ~= "function" then
        return fail("E_UNSUPPORTED", "Wi-Fi configuration is unavailable on this firmware")
    end
    local ok, result, err = pcall(providers.wifi.connect, ssid, password)
    if not ok or not result then return fail("E_IO", tostring(err or result or "Wi-Fi connection failed")) end
    return true
end

return M
