local permissions = require("core.permissions")
local runtime = require("system.agent.runtime")
local M = {}
function M.new(record, resources)
    local api = {}
    function api.ask(prompt, callback)
        local ok, err = permissions.check(record, "agent")
        if not ok then return nil, err end
        local id, ask_err = runtime.ask({ prompt = prompt, app_id = record.id }, resources:guard(callback))
        if not id then return nil, ask_err end
        local entry, track_err = resources:add("agent_requests", id, runtime.cancel)
        if not entry then runtime.cancel(id); return nil, track_err end
        return id
    end
    function api.cancel(id)
        resources:remove("agent_requests", id, false)
        return runtime.cancel(id)
    end
    return api
end
return M
