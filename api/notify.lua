-- ClawOS api/notify.lua
-- Permission-aware notification API; UI remains system-owned.

local errors = require("core.errors")
local permissions = require("core.permissions")
local notifications = require("core.notifications")

local M = {}

function M.new(app_record, resources)
    if type(app_record) ~= "table" or type(app_record.manifest) ~= "table" then
        return nil, errors.new("E_INVALID_ARG", "app_record.manifest is required")
    end

    local api = {}
    local owned = {}

    function api.show(options)
        local ok, perm_err = permissions.check(app_record, "notification")
        if not ok then return nil, perm_err end
        local id, err = notifications.show(options, app_record.manifest.id)
        if not id then return nil, err end
        owned[id] = true
        return id
    end

    function api.dismiss(id)
        if not owned[id] then
            return nil, errors.new("E_PERMISSION", "App does not own this notification", { id = id })
        end
        owned[id] = nil
        notifications.dismiss(id)
        return true
    end

    return api
end

return M
