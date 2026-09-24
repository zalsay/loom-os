-- ClawOS api/storage.lua
-- App-private storage sandbox over ESP-Claw's official storage module.

local storage = require("storage")
local json = require("json")
local errors = require("core.errors")

local M = {}

local function valid_relative(path)
    if type(path) ~= "string" then return false end
    if path == "" or path == "." then return true end
    if path:sub(1, 1) == "/" or path:sub(1, 1) == "\\" then return false end
    if path:match("^[A-Za-z]:[\\/]") then return false end
    for segment in path:gmatch("[^/\\]+") do
        if segment == ".." then return false end
    end
    return true
end

local function invoke(name, ...)
    local fn = storage[name]
    if type(fn) ~= "function" then
        return nil, errors.new("E_UNSUPPORTED", "storage backend does not provide " .. name)
    end
    local ok, a, b = pcall(fn, ...)
    if not ok then
        return nil, errors.new("E_IO", "storage." .. name .. " failed", { cause = tostring(a) })
    end
    if a == false then
        return nil, errors.new("E_IO", "storage." .. name .. " failed", { cause = b })
    end
    return a, b
end

local function mutate(name, ...)
    local fn = storage[name]
    if type(fn) ~= "function" then
        return nil, errors.new("E_UNSUPPORTED", "storage backend does not provide " .. name)
    end
    local ok, result, detail = pcall(fn, ...)
    if not ok then
        return nil, errors.new("E_IO", "storage." .. name .. " failed", { cause = tostring(result) })
    end
    if result == false then
        return nil, errors.new("E_IO", "storage." .. name .. " failed", { cause = detail })
    end
    -- Some ESP-Claw mutating storage calls return no values on success.
    return true
end

function M.new(app_record)
    if type(app_record) ~= "table" or type(app_record.data_dir) ~= "string" then
        return nil, errors.new("E_INVALID_ARG", "app_record.data_dir is required")
    end

    if not storage.exists(app_record.data_dir) then
        local ok, err = mutate("mkdir", app_record.data_dir)
        if not ok then return nil, err end
    end

    local function resolve(relative)
        relative = relative or ""
        if not valid_relative(relative) then
            return nil, errors.new("E_PERMISSION", "storage path escapes App data root", {
                path = relative,
            })
        end
        if relative == "" or relative == "." then
            return app_record.data_dir
        end
        local normalized = relative:gsub("\\", "/")
        return storage.join_path(app_record.data_dir, normalized)
    end

    local api = {}

    function api.read_text(path)
        local full, err = resolve(path)
        if not full then return nil, err end
        if not storage.exists(full) then
            return nil, errors.new("E_NOT_FOUND", "file not found", { path = path })
        end
        return invoke("read_file", full)
    end

    function api.write_text(path, text)
        if type(text) ~= "string" then
            return nil, errors.new("E_INVALID_ARG", "text must be a string")
        end
        local full, err = resolve(path)
        if not full then return nil, err end
        return mutate("write_file", full, text)
    end

    function api.read_json(path)
        local text, err = api.read_text(path)
        if not text then return nil, err end
        local ok, value = pcall(json.decode, text)
        if not ok then
            return nil, errors.new("E_IO", "JSON decode failed", { path = path, cause = tostring(value) })
        end
        return value
    end

    function api.write_json(path, value)
        local ok, text = pcall(json.encode, value)
        if not ok then
            return nil, errors.new("E_INVALID_ARG", "JSON encode failed", { cause = tostring(text) })
        end
        return api.write_text(path, text)
    end

    function api.exists(path)
        local full, err = resolve(path)
        if not full then return false, err end
        return storage.exists(full) == true
    end

    function api.list(path)
        local full, err = resolve(path or "")
        if not full then return nil, err end
        if not storage.exists(full) then
            return nil, errors.new("E_NOT_FOUND", "directory not found", { path = path or "" })
        end
        return invoke("listdir", full)
    end

    function api.mkdir(path)
        local full, err = resolve(path)
        if not full then return nil, err end
        if storage.exists(full) then return true end
        return mutate("mkdir", full)
    end

    function api.remove(path)
        local full, err = resolve(path)
        if not full then return nil, err end
        if full == app_record.data_dir then
            return nil, errors.new("E_PERMISSION", "cannot remove App data root")
        end
        if not storage.exists(full) then return true end
        return mutate("remove", full)
    end

    return api
end

return M
