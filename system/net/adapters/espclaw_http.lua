-- Loom OS system/net/adapters/espclaw_http.lua
-- Adapter for ESP-Claw's registered http_request Capability.

local errors = require("system.net.errors")

local M = {}

local function load_capability()
    local ok, capability = pcall(require, "capability")
    if not ok or type(capability) ~= "table" then
        return nil, errors.wrap("E_NET_UNSUPPORTED", "ESP-Claw capability Lua module is unavailable", capability)
    end
    return capability
end

local function invoke(capability, name, args)
    if type(capability.call) == "function" then
        local ok, a, b = pcall(capability.call, name, args)
        if not ok then return nil, errors.wrap("E_HTTP", "capability.call failed", a) end
        if a == nil or a == false then return nil, errors.wrap("E_HTTP", "http_request capability failed", b or a) end
        return a, b
    end

    -- Defensive compatibility aliases. Current Loom OS code does not depend on
    -- these names, but keeping the adapter tolerant makes upstream refactors
    -- less disruptive.
    for _, key in ipairs({"invoke", "execute", "run"}) do
        if type(capability[key]) == "function" then
            local ok, a, b = pcall(capability[key], name, args)
            if not ok then return nil, errors.wrap("E_HTTP", "capability." .. key .. " failed", a) end
            if a == nil or a == false then return nil, errors.wrap("E_HTTP", "http_request capability failed", b or a) end
            return a, b
        end
    end

    return nil, errors.new("E_NET_UNSUPPORTED", "capability module has no supported call function")
end

local function parse_string(raw)
    if raw:match("^Error:") then
        return nil, errors.new("E_HTTP", raw)
    end

    local status = tonumber(raw:match("^HTTP%s+(%d+)") or raw:match("HTTP%s+(%d+)"))
    if not status then
        return nil, errors.new("E_PROTOCOL", "unrecognized ESP-Claw http_request output", { raw = raw })
    end

    local saved_path, bytes = raw:match("Saved response body to%s+([^\r\n]+)%s+%((%d+)%s+bytes%)")
    if saved_path then
        return {
            status = status,
            headers = nil,
            body = nil,
            saved_path = saved_path,
            bytes = tonumber(bytes),
            raw = raw,
        }
    end

    local body = raw:match("^[^\r\n]*[\r\n]+(.*)$") or ""
    return {
        status = status,
        headers = nil,
        body = body,
        bytes = #body,
        raw = raw,
    }
end

function M.request(options)
    local capability, cap_err = load_capability()
    if not capability then return nil, cap_err end

    local args = {
        url = options.url,
        method = options.method,
        headers = options.headers,
        body = options.body,
        timeout_ms = options.timeout_ms,
        max_body_bytes = options.max_body_bytes,
        save_path = options.save_path,
        max_file_bytes = options.max_file_bytes,
    }

    -- Keep the JSON input compact by removing nil fields.
    for k, v in pairs(args) do
        if v == nil then args[k] = nil end
    end

    local raw, raw_err = invoke(capability, "http_request", args)
    if not raw then return nil, raw_err end

    if type(raw) == "table" then
        if raw.status then return raw end
        if raw.output and type(raw.output) == "string" then
            return parse_string(raw.output)
        end
        if raw.result and type(raw.result) == "string" then
            return parse_string(raw.result)
        end
    elseif type(raw) == "string" then
        return parse_string(raw)
    end

    return nil, errors.new("E_PROTOCOL", "unsupported capability return shape", { value_type = type(raw) })
end

return M
