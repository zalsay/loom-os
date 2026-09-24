-- ClawOS api/timer.lua
-- App-scoped managed timers backed by core.timers.

local errors = require("core.errors")
local timers = require("core.timers")

local M = {}

function M.new(resources)
    if type(resources) ~= "table" then
        return nil, errors.new("E_INVALID_ARG", "resources registry is required")
    end

    local api = {}

    local function track(timer_id)
        local entry, err = resources:add("timers", timer_id, function(id)
            timers.cancel(id)
            return true
        end)
        if not entry then
            timers.cancel(timer_id)
            return nil, err
        end
        return timer_id
    end

    function api.after(delay_ms, fn)
        if type(fn) ~= "function" then
            return nil, errors.new("E_INVALID_ARG", "timer callback must be a function")
        end
        local guarded = resources:guard(fn)
        local id, err = timers.after(delay_ms, guarded)
        if not id then return nil, err end
        return track(id)
    end

    function api.every(interval_ms, fn)
        if type(fn) ~= "function" then
            return nil, errors.new("E_INVALID_ARG", "timer callback must be a function")
        end
        local guarded = resources:guard(fn)
        local id, err = timers.every(interval_ms, guarded)
        if not id then return nil, err end
        return track(id)
    end

    function api.cancel(timer_id)
        if type(timer_id) ~= "number" then
            return nil, errors.new("E_INVALID_ARG", "timer_id must be a number")
        end
        resources:remove("timers", timer_id, false)
        timers.cancel(timer_id)
        return true
    end

    return api
end

return M
