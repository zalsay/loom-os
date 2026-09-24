-- ClawOS system/net/http_client.lua
-- Stable HTTP facade. The default adapter uses ESP-Claw's capability bridge.

local json = require("json")
local errors = require("system.net.errors")

local M = {}
local adapter = nil

local ALLOWED_METHOD = {
    GET = true, POST = true, PUT = true, PATCH = true, DELETE = true, HEAD = true,
}

local function load_default_adapter()
    local ok, mod = pcall(require, "system.net.adapters.espclaw_http")
    if ok and type(mod) == "table" then
        return mod
    end
    return nil, errors.wrap("E_NET_BACKEND", "failed to load ESP-Claw HTTP adapter", mod)
end

local function get_adapter()
    if adapter then return adapter end
    local mod, err = load_default_adapter()
    if not mod then return nil, err end
    adapter = mod
    return adapter
end

local function validate_url(url, allow_http)
    if type(url) ~= "string" or url == "" then
        return nil, errors.new("E_NET_INVALID_ARG", "url must be a non-empty string")
    end
    if url:sub(1, 8):lower() == "https://" then return true end
    if allow_http == true and url:sub(1, 7):lower() == "http://" then return true end
    return nil, errors.new("E_TLS", "HTTPS is required", { url = url })
end

local function normalize_headers(headers)
    if headers == nil then return {} end
    if type(headers) ~= "table" then
        return nil, errors.new("E_NET_INVALID_ARG", "headers must be a table")
    end
    local out = {}
    for k, v in pairs(headers) do
        if type(k) ~= "string" or type(v) ~= "string" then
            return nil, errors.new("E_NET_INVALID_ARG", "HTTP header keys and values must be strings")
        end
        out[k] = v
    end
    return out
end

function M.set_adapter(custom)
    if custom ~= nil and (type(custom) ~= "table" or type(custom.request) ~= "function") then
        return nil, errors.new("E_NET_INVALID_ARG", "HTTP adapter must provide request(options)")
    end
    adapter = custom
    return true
end

function M.request(options)
    if type(options) ~= "table" then
        return nil, errors.new("E_NET_INVALID_ARG", "HTTP options table is required")
    end

    local method = tostring(options.method or "GET"):upper()
    if not ALLOWED_METHOD[method] then
        return nil, errors.new("E_NET_INVALID_ARG", "unsupported HTTP method", { method = method })
    end

    local ok, url_err = validate_url(options.url, options.allow_http)
    if not ok then return nil, url_err end

    local headers, header_err = normalize_headers(options.headers)
    if not headers then return nil, header_err end

    if (method == "GET" or method == "HEAD") and options.body ~= nil and options.body ~= "" then
        return nil, errors.new("E_NET_INVALID_ARG", method .. " does not accept a request body")
    end

    local backend, backend_err = get_adapter()
    if not backend then return nil, backend_err end

    local response, err = backend.request({
        method = method,
        url = options.url,
        headers = headers,
        body = options.body,
        timeout_ms = options.timeout_ms or 15000,
        max_body_bytes = options.max_body_bytes or 16384,
        save_path = options.save_path,
        max_file_bytes = options.max_file_bytes,
    })
    if not response then return nil, err end

    if type(response.status) ~= "number" then
        return nil, errors.new("E_PROTOCOL", "HTTP backend returned no numeric status")
    end

    if options.accept_status then
        local accepted = false
        if type(options.accept_status) == "function" then
            accepted = options.accept_status(response.status) == true
        elseif type(options.accept_status) == "table" then
            accepted = options.accept_status[response.status] == true
        end
        if not accepted then
            return nil, errors.new("E_HTTP_STATUS", "unexpected HTTP status", {
                status = response.status,
                body = response.body,
            })
        end
    elseif response.status < 200 or response.status >= 300 then
        return nil, errors.new("E_HTTP_STATUS", "HTTP request failed", {
            status = response.status,
            body = response.body,
        })
    end

    return response
end

function M.get(url, options)
    options = options or {}
    options.url = url
    options.method = "GET"
    return M.request(options)
end

function M.post(url, body, options)
    options = options or {}
    options.url = url
    options.method = "POST"
    options.body = body
    return M.request(options)
end

function M.get_json(url, options)
    local response, err = M.get(url, options)
    if not response then return nil, err end
    local ok, value = pcall(json.decode, response.body or "")
    if not ok then
        return nil, errors.new("E_PROTOCOL", "HTTP response is not valid JSON", {
            status = response.status,
            cause = tostring(value),
        })
    end
    return value, response
end

function M.download(options)
    if type(options) ~= "table" or type(options.path) ~= "string" or options.path == "" then
        return nil, errors.new("E_NET_INVALID_ARG", "download path is required")
    end
    local request_options = {}
    for k, v in pairs(options) do request_options[k] = v end
    request_options.method = "GET"
    request_options.save_path = options.path
    request_options.max_file_bytes = options.max_bytes
    request_options.path = nil
    request_options.max_bytes = nil
    return M.request(request_options)
end

return M
