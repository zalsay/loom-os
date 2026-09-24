local runner = require("core.service_runner")
local M = {}
function M.new(record)
    local api = {}
    function api.start(id) return runner.start_app(record, id) end
    function api.stop(id) return runner.stop(record.id .. ":" .. id) end
    function api.status(id) return runner.status(record.id .. ":" .. id) end
    return api
end
return M
