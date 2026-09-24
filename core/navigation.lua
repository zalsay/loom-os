-- ClawOS core/navigation.lua
-- Queued navigation avoids destroying an App inside its own LVGL callback.


local errors = require("core.errors")


local M = {}
local queue = {}
local handler = nil
local processing = false


local VALID = {
    home = true,
    back = true,
    open = true,
    reload = true,
}


function M.set_handler(fn)
    if type(fn) ~= "function" then
        return nil, errors.new("E_INVALID_ARG", "navigation handler must be a function")
    end
    handler = fn
    return true
end


function M.enqueue(action)
    if type(action) ~= "table" or not VALID[action.type] then
        return nil, errors.new("E_INVALID_ARG", "invalid navigation action")
    end
    queue[#queue + 1] = action
    return true
end


function M.has_pending()
    return #queue > 0
end


function M.process_next()
    if processing or not M.has_pending() then
        return false
    end
    if type(handler) ~= "function" then
        return nil, errors.new("E_BUSY", "navigation handler is not configured")
    end


    local action = table.remove(queue, 1)


    processing = true
    local ok, result, err = xpcall(function()
        return handler(action)
    end, function(e)
        return tostring(e)
    end)
    processing = false


    if not ok then
        return nil, errors.new("E_CRASH", "navigation transition failed", {
            cause = result,
            action = action.type,
        })
    end
    return result, err
end


function M.clear()
    queue = {}
end


return M