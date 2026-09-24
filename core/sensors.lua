-- ClawOS core/sensors.lua
-- Logical sensor registry decoupling Apps from board/driver-specific module names.

local errors = require("core.errors")

local M = {}
local registry = {}

local function valid_id(id)
    return type(id) == "string" and id:match("^[a-z][a-z0-9_.-]*$") ~= nil
end

function M.register(id, provider, metadata)
    if not valid_id(id) then
        return nil, errors.new("E_INVALID_ARG", "invalid sensor id", { id = id })
    end
    if type(provider) ~= "table" or type(provider.read) ~= "function" then
        return nil, errors.new("E_INVALID_ARG", "sensor provider.read is required", { id = id })
    end
    if registry[id] then
        return nil, errors.new("E_EXISTS", "sensor id already registered", { id = id })
    end

    registry[id] = {
        id = id,
        provider = provider,
        metadata = metadata or {},
    }
    return true
end

function M.unregister(id)
    if not registry[id] then return false end
    registry[id] = nil
    return true
end

function M.get(id)
    return registry[id]
end

function M.list()
    local out = {}
    for id, entry in pairs(registry) do
        out[#out + 1] = {
            id = id,
            metadata = entry.metadata,
        }
    end
    table.sort(out, function(a, b) return a.id < b.id end)
    return out
end

function M.read(id, options)
    local entry = registry[id]
    if not entry then
        return nil, errors.new("E_NOT_FOUND", "sensor is not registered", { id = id })
    end

    local ok, value, err = pcall(entry.provider.read, options or {})
    if not ok then
        return nil, errors.new("E_IO", "sensor read failed", {
            id = id,
            cause = tostring(value),
        })
    end
    if value == nil then
        if type(err) == "table" and err.code then return nil, err end
        return nil, errors.new("E_IO", "sensor read failed", { id = id, cause = err })
    end
    return value
end

function M.clear()
    registry = {}
end

return M
