-- ClawOS system/net/errors.lua
-- Stable error objects shared by HTTP, download and WebSocket helpers.

local M = {}

local VALID = {
    E_NET_INVALID_ARG = true,
    E_NET_UNSUPPORTED = true,
    E_NET_BACKEND = true,
    E_HTTP = true,
    E_HTTP_STATUS = true,
    E_TLS = true,
    E_TIMEOUT = true,
    E_IO = true,
    E_PROTOCOL = true,
    E_HASH = true,
    E_WS_CLOSED = true,
}

function M.new(code, message, detail)
    if type(code) ~= "string" or not VALID[code] then
        code = "E_NET_BACKEND"
    end
    return {
        code = code,
        message = tostring(message or code),
        detail = detail,
    }
end

function M.wrap(code, prefix, err, detail)
    local message = prefix or code
    if type(err) == "table" and err.message then
        message = message .. ": " .. tostring(err.message)
    elseif err ~= nil then
        message = message .. ": " .. tostring(err)
    end
    detail = detail or {}
    detail.cause = err
    return M.new(code, message, detail)
end

function M.is(err, code)
    return type(err) == "table" and err.code == code
end

return M
