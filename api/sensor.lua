-- ClawOS api/sensor.lua
-- Permission-aware logical sensor facade.

local errors = require("core.errors")
local permissions = require("core.permissions")
local sensors = require("core.sensors")

local M = {}

function M.new(app_record)
    if type(app_record) ~= "table" or type(app_record.manifest) ~= "table" then
        return nil, errors.new("E_INVALID_ARG", "app_record.manifest is required")
    end

    local api = {}

    function api.list()
        local visible = {}
        for _, item in ipairs(sensors.list()) do
            local ok = permissions.check(app_record, "sensor", { id = item.id })
            if ok then visible[#visible + 1] = item end
        end
        return visible
    end

    function api.read(sensor_id, options)
        local ok, perm_err = permissions.check(app_record, "sensor", { id = sensor_id })
        if not ok then return nil, perm_err end
        return sensors.read(sensor_id, options)
    end

    return api
end

return M
