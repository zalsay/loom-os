-- ClawOS core/paths.lua
-- Resolves writable ClawOS paths from ESP-Claw's storage DATA root.


local storage = require("storage")
local errors = require("core.errors")


local M = {}


local function safe_call(fn, ...)
    local ok, a, b = pcall(fn, ...)
    if not ok then
        return nil, errors.from_exception("E_IO", a)
    end
    return a, b
end


local function ensure_dir(path)
    local exists, err = safe_call(storage.exists, path)
    if exists == nil then
        return nil, err
    end
    if exists then
        return true
    end


    local call_ok, mkdir_result = pcall(storage.mkdir, path)
    if not call_ok then
        return nil, errors.new("E_IO", "failed to create directory", {
            path = path,
            cause = tostring(mkdir_result),
        })
    end
    if mkdir_result == false then
        return nil, errors.new("E_IO", "failed to create directory", { path = path })
    end
    return true
end


function M.resolve()
    local root, err = safe_call(storage.get_root_dir)
    if not root then
        return nil, err or errors.new("E_IO", "storage.get_root_dir() failed")
    end


    local clawos = storage.join_path(root, "clawos")
    local result = {
        data_root = root,
        root = clawos,
        apps = storage.join_path(clawos, "apps"),
        appdata = storage.join_path(clawos, "appdata"),
        app_staging = storage.join_path(clawos, "app-staging"),
        authoring = storage.join_path(clawos, "authoring"),
        cache = storage.join_path(clawos, "cache"),
        logs = storage.join_path(clawos, "logs"),
        state = storage.join_path(clawos, "state"),
        versions = storage.join_path(clawos, "versions"),
    }
    return result
end


function M.ensure_layout(paths)
    if type(paths) ~= "table" or type(paths.root) ~= "string" then
        return nil, errors.new("E_INVALID_ARG", "paths table is required")
    end


    local order = {
        paths.root,
        paths.apps,
        paths.appdata,
        paths.app_staging,
        paths.authoring,
        paths.cache,
        paths.logs,
        paths.state,
        paths.versions,
    }


    for _, path in ipairs(order) do
        local ok, err = ensure_dir(path)
        if not ok then
            return nil, err
        end
    end


    return true
end


function M.app_dir(paths, app_id)
    return storage.join_path(paths.apps, app_id)
end


function M.appdata_dir(paths, app_id)
    return storage.join_path(paths.appdata, app_id)
end


function M.app_log_dir(paths, app_id)
    return storage.join_path(paths.logs, app_id)
end


function M.app_versions_dir(paths, app_id)
    return storage.join_path(paths.versions, app_id)
end


return M