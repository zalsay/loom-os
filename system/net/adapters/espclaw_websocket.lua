-- ClawOS system/net/adapters/espclaw_websocket.lua
-- Deliberately not auto-enabled.
--
-- ESP-Claw currently uses esp_websocket_client internally (for example Web Chat
-- and IM integrations), but the current public Lua module catalog does not
-- expose a generic WebSocket client. ClawOS keeps this backend boundary so a
-- future native binding can be added without changing system/net/websocket_client.lua.

local errors = require("system.net.errors")
local M = {}

function M.connect(options, emit)
    return nil, errors.new("E_NET_UNSUPPORTED",
        "ESP-Claw generic Lua WebSocket backend is not available in the verified module catalog", {
            url = options and options.url,
        })
end

return M
