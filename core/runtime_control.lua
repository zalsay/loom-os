-- Loom OS core/runtime_control.lua
-- Coordinates a soft restart of Loom OS without rebooting ESP-Claw/ESP32.


local M = {}
local requested = nil


function M.request_restart(reason)
    requested = {
        action = "restart",
        reason = reason or "requested",
    }
    return true
end


function M.request_exit(reason)
    requested = {
        action = "exit",
        reason = reason or "requested",
    }
    return true
end


function M.should_exit()
    return requested ~= nil
end


function M.result()
    return requested or { action = "exit", reason = "main loop ended" }
end


function M.reset()
    requested = nil
end


return M