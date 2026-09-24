-- Advertise only APIs and logical sensors actually registered in this Runtime.
local version = require("core.version")
local sensors = require("core.sensors")
local M = {}
function M.current(board)
    local sensor_ids = {}
    for _, item in ipairs(sensors.list()) do sensor_ids[#sensor_ids + 1] = item.id end
    local apis = { "ctx.ui", "ctx.nav", "ctx.storage", "ctx.timer", "ctx.system",
        "ctx.sensor", "ctx.notify", "ctx.service" }
    local permissions = { "background", "notification", "sensor", "gpio" }
    if require("system.net.request").available() then
        apis[#apis + 1] = "ctx.network"
        permissions[#permissions + 1] = "network"
    end
    if require("system.agent.runtime").available() then
        apis[#apis + 1] = "ctx.agent"
        permissions[#permissions + 1] = "agent"
    end
    return {
        runtime_version = version.loom_os,
        board = board or "mosaico",
        apis = apis,
        sensors = sensor_ids,
        permissions = permissions,
    }
end
return M
