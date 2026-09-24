-- Agent jobs are asynchronous and unavailable until a verified adapter is installed.
local errors = require("core.errors")
local M = {}
local adapter, pending, next_id = nil, {}, 0
function M.available() return adapter ~= nil end
function M.set_adapter(value)
    if value ~= nil and (type(value.start) ~= "function" or type(value.poll) ~= "function") then
        return nil, errors.new("E_INVALID_ARG", "Agent adapter needs start and poll")
    end
    adapter = value
    return true
end
function M.ask(options, callback)
    if not adapter then return nil, errors.new("E_UNSUPPORTED", "Agent backend unavailable") end
    if type(callback) ~= "function" then return nil, errors.new("E_INVALID_ARG", "callback required") end
    local job, err = adapter.start(options)
    if not job then return nil, err end
    next_id = next_id + 1
    pending[next_id] = { job = job, callback = callback }
    return next_id
end
function M.cancel(id)
    local req = pending[id]
    if not req then return false end
    pending[id] = nil
    if adapter and type(adapter.cancel) == "function" then pcall(adapter.cancel, req.job) end
    return true
end
function M.poll()
    for id, req in pairs(pending) do
        local ok, done, value, err = pcall(adapter.poll, req.job)
        if not ok then done, value, err = true, nil, errors.new("E_IO", tostring(done)) end
        if done then pending[id] = nil; pcall(req.callback, value, err) end
    end
end
return M
