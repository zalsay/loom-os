local permissions = require("core.permissions")
local requests = require("system.net.request")
local errors = require("core.errors")
local M = {}
function M.new(record, resources)
    local api = {}
    function api.request(options, callback)
        local ok, err = permissions.check(record, "network")
        if not ok then return nil, err end
        if type(callback) ~= "function" then
            return nil, errors.new("E_INVALID_ARG", "callback required")
        end
        if type(options) ~= "table" or options.method == "DOWNLOAD" or options.save_path then
            return nil, errors.new("E_INVALID_ARG", "download requires a private storage adapter")
        end
        local id, request_err = requests.create(options, resources:guard(callback))
        if not id then return nil, request_err end
        local entry, track_err = resources:add("network_requests", id, requests.cancel)
        if not entry then requests.cancel(id); return nil, track_err end
        return id
    end
    function api.get(url, callback) return api.request({ method = "GET", url = url }, callback) end
    function api.cancel(id)
        resources:remove("network_requests", id, false)
        return requests.cancel(id)
    end
    return api
end
return M
