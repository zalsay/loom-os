-- Read-only Wi-Fi state from ESP-Claw's native system Lua module.
local M = {}

function M.wifi_status()
    local loaded, system = pcall(require, "system")
    if not loaded or type(system) ~= "table" or type(system.info) ~= "function" then
        return nil
    end
    local ok, info = pcall(system.info)
    if not ok or type(info) ~= "table" then return nil end
    local ip
    if type(system.ip) == "function" then
        local ip_ok, address = pcall(system.ip)
        if ip_ok then ip = address end
    end
    return { connected = type(info.wifi_ssid) == "string" and info.wifi_ssid ~= "",
        ssid = info.wifi_ssid, ip = ip }
end

return M
