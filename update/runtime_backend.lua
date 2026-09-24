-- Loom OS update/runtime_backend.lua
-- System-only Runtime OTA transport based on system.net.download.

local download = require("system.net.download")

return download.runtime_backend()
