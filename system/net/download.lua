-- ClawOS system/net/download.lua
-- File download helper with size verification only.


local storage = require("storage")
local http = require("system.net.http_client")
local errors = require("system.net.errors")


local M = {}


local function stat_size(path)
    if type(storage.stat) ~= "function" then return nil end
    local ok, info = pcall(storage.stat, path)
    if not ok or type(info) ~= "table" then return nil end
    return tonumber(info.size or info.size_bytes)
end


function M.verify(path, options)
    options = options or {}


    if options.size and options.size > 0 then
        local actual = stat_size(path) or tonumber(options.reported_bytes)
        if not actual then
            return nil, errors.new("E_UNSUPPORTED", "download size cannot be verified", { path = path })
        end
        if actual ~= options.size then
            return nil, errors.new("E_IO", "downloaded file size mismatch", {
                path = path,
                expected = options.size,
                actual = actual,
            })
        end
    end


    return true
end


function M.to_file(options)
    if type(options) ~= "table" then
        return nil, errors.new("E_NET_INVALID_ARG", "download options are required")
    end
    if type(options.url) ~= "string" or type(options.path) ~= "string" then
        return nil, errors.new("E_NET_INVALID_ARG", "url and path are required")
    end


    local response, err = http.download({
        url = options.url,
        path = options.path,
        headers = options.headers,
        timeout_ms = options.timeout_ms or 30000,
        max_bytes = options.max_bytes or options.size,
        allow_http = options.allow_http,
    })
    if not response then return nil, err end


    local ok, verify_err = M.verify(options.path, {
        size = options.size,
        reported_bytes = response.bytes,
    })
    if not ok then
        if type(storage.remove) == "function" then pcall(storage.remove, options.path) end
        return nil, verify_err
    end


    return {
        status = response.status,
        path = response.saved_path or options.path,
        bytes = response.bytes or stat_size(options.path),
    }
end


function M.runtime_backend()
    return {
        download = function(url, destination, options)
            options = options or {}
            return M.to_file({
                url = url,
                path = destination,
                size = options.size,
                max_bytes = options.size,
                timeout_ms = options.timeout_ms or 30000,
            })
        end,
    }
end


return M
