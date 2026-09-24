-- ClawOS core/notifications.lua
-- Data/command queue for system-owned notifications.

local errors = require("core.errors")

local M = {}
local next_id = 1
local active = {}
local actions = {}

local VALID_LEVEL = { info = true, warning = true, error = true }

function M.show(options, source_app_id)
    if type(options) ~= "table" then
        return nil, errors.new("E_INVALID_ARG", "notification options must be a table")
    end
    if type(options.message) ~= "string" or options.message == "" then
        return nil, errors.new("E_INVALID_ARG", "notification message is required")
    end
    local level = options.level or "info"
    if not VALID_LEVEL[level] then
        return nil, errors.new("E_INVALID_ARG", "invalid notification level", { level = level })
    end

    local id = next_id
    next_id = next_id + 1
    local item = {
        id = id,
        source_app_id = source_app_id,
        title = options.title or source_app_id or "ClawOS",
        message = options.message,
        level = level,
    }
    active[id] = item
    actions[#actions + 1] = { type = "show", item = item }
    return id
end

function M.dismiss(id)
    local item = active[id]
    if not item then return false end
    active[id] = nil
    actions[#actions + 1] = { type = "dismiss", id = id }
    return true
end

function M.drain_actions(limit)
    local out = {}
    limit = limit or 16
    while #actions > 0 and #out < limit do
        out[#out + 1] = table.remove(actions, 1)
    end
    return out
end

function M.get(id)
    return active[id]
end

function M.clear()
    active = {}
    actions = {}
end

return M
