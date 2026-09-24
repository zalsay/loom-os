-- ClawOS system/net/websocket_client.lua
-- Stable WebSocket facade. Wire protocol is supplied by a backend adapter.

local json = require("json")
local errors = require("system.net.errors")

local M = {}
local backend = nil
local next_id = 0

local VALID_EVENTS = { open=true, message=true, close=true, error=true, pong=true }

local function validate_url(url, allow_ws)
    if type(url) ~= "string" or url == "" then
        return nil, errors.new("E_NET_INVALID_ARG", "WebSocket url is required")
    end
    if url:sub(1, 6):lower() == "wss://" then return true end
    if allow_ws == true and url:sub(1, 5):lower() == "ws://" then return true end
    return nil, errors.new("E_TLS", "WSS is required", { url = url })
end

function M.set_backend(custom)
    if custom ~= nil and (type(custom) ~= "table" or type(custom.connect) ~= "function") then
        return nil, errors.new("E_NET_INVALID_ARG", "WebSocket backend must provide connect(options, emit)")
    end
    backend = custom
    return true
end

local Connection = {}
Connection.__index = Connection

function Connection:on(event, fn)
    if not VALID_EVENTS[event] then
        return nil, errors.new("E_NET_INVALID_ARG", "unsupported WebSocket event", { event = event })
    end
    if type(fn) ~= "function" then
        return nil, errors.new("E_NET_INVALID_ARG", "WebSocket event handler must be a function")
    end
    self.handlers[event] = fn
    return self
end

function Connection:_emit(event, ...)
    if self.closed and event ~= "close" then return false end
    local fn = self.handlers[event]
    if type(fn) ~= "function" then return true end
    local ok, callback_err = pcall(fn, ...)
    if not ok and event ~= "error" then
        local error_fn = self.handlers.error
        if type(error_fn) == "function" then
            pcall(error_fn, errors.wrap("E_NET_BACKEND", "WebSocket callback failed", callback_err))
        end
    end
    return ok
end

function Connection:send_text(text)
    if self.closed then return nil, errors.new("E_WS_CLOSED", "WebSocket is closed") end
    if type(text) ~= "string" then
        return nil, errors.new("E_NET_INVALID_ARG", "WebSocket text payload must be a string")
    end
    if type(self.backend_handle.send_text) ~= "function" then
        return nil, errors.new("E_NET_UNSUPPORTED", "WebSocket backend has no send_text")
    end
    return self.backend_handle:send_text(text)
end

function Connection:send_binary(data)
    if self.closed then return nil, errors.new("E_WS_CLOSED", "WebSocket is closed") end
    if type(data) ~= "string" then
        return nil, errors.new("E_NET_INVALID_ARG", "binary payload must be a Lua string")
    end
    if type(self.backend_handle.send_binary) ~= "function" then
        return nil, errors.new("E_NET_UNSUPPORTED", "WebSocket backend has no send_binary")
    end
    return self.backend_handle:send_binary(data)
end

function Connection:send_json(value)
    local ok, payload = pcall(json.encode, value)
    if not ok then
        return nil, errors.new("E_PROTOCOL", "failed to encode WebSocket JSON", { cause = tostring(payload) })
    end
    return self:send_text(payload)
end

function Connection:is_connected()
    if self.closed then return false end
    if type(self.backend_handle.is_connected) == "function" then
        local ok, value = pcall(self.backend_handle.is_connected, self.backend_handle)
        return ok and value == true
    end
    return self.opened == true
end

function Connection:close(code, reason)
    if self.closed then return true end
    self.closed = true
    if type(self.backend_handle.close) == "function" then
        local ok, err = self.backend_handle:close(code, reason)
        if ok == nil or ok == false then return nil, err end
    end
    self:_emit("close", code or 1000, reason or "client close")
    return true
end

function M.connect(options)
    if type(options) ~= "table" then
        return nil, errors.new("E_NET_INVALID_ARG", "WebSocket options table is required")
    end
    local ok, url_err = validate_url(options.url, options.allow_ws)
    if not ok then return nil, url_err end
    if not backend then
        return nil, errors.new("E_NET_UNSUPPORTED", "no WebSocket backend is configured")
    end

    next_id = next_id + 1
    local conn = setmetatable({
        id = next_id,
        url = options.url,
        handlers = {},
        opened = false,
        closed = false,
    }, Connection)

    local function emit(event, ...)
        if event == "open" then conn.opened = true end
        if event == "close" then conn.closed = true end
        return conn:_emit(event, ...)
    end

    local handle, connect_err = backend.connect({
        url = options.url,
        headers = options.headers or {},
        subprotocol = options.subprotocol,
        connect_timeout_ms = options.connect_timeout_ms or 10000,
        heartbeat = options.heartbeat,
        reconnect = options.reconnect,
    }, emit)
    if not handle then return nil, connect_err end

    conn.backend_handle = handle
    return conn
end

return M
