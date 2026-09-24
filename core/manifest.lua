-- Loom OS core/manifest.lua
-- Loads and validates Loom OS App manifest.json files.

local storage = require("storage")
local json = require("json")
local errors = require("core.errors")
local version = require("core.version")

local M = {}

local SUPPORTED_SCHEMA = version.manifest_schema
local SUPPORTED_API_MAJOR, SUPPORTED_API_MINOR = version.app_api:match("^(%d+)%.(%d+)$")
SUPPORTED_API_MAJOR = tonumber(SUPPORTED_API_MAJOR)
SUPPORTED_API_MINOR = tonumber(SUPPORTED_API_MINOR)

local function split_version(text)
    if type(text) ~= "string" then
        return nil
    end
    local a, b, c = text:match("^(%d+)%.(%d+)%.(%d+)$")
    if not a then
        return nil
    end
    return tonumber(a), tonumber(b), tonumber(c)
end

local function split_api(text)
    if type(text) ~= "string" then
        return nil
    end
    local a, b = text:match("^(%d+)%.(%d+)$")
    if not a then
        return nil
    end
    return tonumber(a), tonumber(b)
end

local function valid_id_segment(seg, first)
    if type(seg) ~= "string" or seg == "" then
        return false
    end
    if first then
        return seg:match("^[a-z][a-z0-9]*$") ~= nil
    end
    return seg:match("^[a-z0-9][a-z0-9-]*$") ~= nil
end

local function valid_app_id(id)
    if type(id) ~= "string" or not id:find("%.") then
        return false
    end
    if id:sub(1, 1) == "." or id:sub(-1) == "." or id:find("%.%.", 1, false) then
        return false
    end
    local n = 0
    for seg in id:gmatch("[^.]+") do
        n = n + 1
        if not valid_id_segment(seg, n == 1) then
            return false
        end
    end
    return n >= 2
end

local function is_absolute(path)
    if type(path) ~= "string" then
        return false
    end
    if path:sub(1, 1) == "/" or path:sub(1, 1) == "\\" then
        return true
    end
    if path:match("^[A-Za-z]:[\\/]") then
        return true
    end
    return false
end

local function safe_relative_path(path)
    if type(path) ~= "string" or path == "" then
        return false
    end
    if is_absolute(path) then
        return false
    end
    for seg in path:gmatch("[^/\\]+") do
        if seg == ".." then
            return false
        end
    end
    return true
end

local function exists(path)
    local ok, value = pcall(storage.exists, path)
    return ok and value == true
end

local function decode_json(text)
    local ok, value = pcall(json.decode, text)
    if not ok then
        return nil, errors.new("E_LOAD", "invalid manifest JSON", {
            cause = tostring(value),
        })
    end
    if type(value) ~= "table" then
        return nil, errors.new("E_LOAD", "manifest root must be an object")
    end
    return value
end

local function validate_permissions(p)
    if p == nil then
        return true
    end
    if type(p) ~= "table" then
        return nil, errors.new("E_INVALID_ARG", "permissions must be an object")
    end

    if p.sensor ~= nil and type(p.sensor) ~= "table" then
        return nil, errors.new("E_INVALID_ARG", "permissions.sensor must be an array")
    end

    if p.gpio ~= nil then
        if type(p.gpio) ~= "table" or type(p.gpio.pins) ~= "table" then
            return nil, errors.new("E_INVALID_ARG", "permissions.gpio.pins must be an array")
        end
        for _, pin in ipairs(p.gpio.pins) do
            if type(pin) ~= "number" or pin < 0 or pin % 1 ~= 0 then
                return nil, errors.new("E_INVALID_ARG", "GPIO pins must be non-negative integers")
            end
        end
    end

    if p.network ~= nil and type(p.network) ~= "table" and type(p.network) ~= "boolean" then
        return nil, errors.new("E_INVALID_ARG", "permissions.network must be an object or boolean")
    end

    for _, key in ipairs({"notification", "agent", "background"}) do
        if p[key] ~= nil and type(p[key]) ~= "boolean" then
            return nil, errors.new("E_INVALID_ARG", "permissions." .. key .. " must be boolean")
        end
    end

    return true
end

local function validate_services(services, app_dir)
    if services == nil then
        return true
    end
    if type(services) ~= "table" then
        return nil, errors.new("E_INVALID_ARG", "services must be an array")
    end

    local ids = {}
    for i, svc in ipairs(services) do
        if type(svc) ~= "table" then
            return nil, errors.new("E_INVALID_ARG", "service entry must be an object", { index = i })
        end
        if type(svc.id) ~= "string" or svc.id == "" then
            return nil, errors.new("E_INVALID_ARG", "service.id is required", { index = i })
        end
        if ids[svc.id] then
            return nil, errors.new("E_EXISTS", "duplicate service id", { id = svc.id })
        end
        ids[svc.id] = true

        if not safe_relative_path(svc.entry) then
            return nil, errors.new("E_INVALID_ARG", "invalid service entry path", {
                id = svc.id,
                entry = svc.entry,
            })
        end

        local service_path = storage.join_path(app_dir, svc.entry)
        if not exists(service_path) then
            return nil, errors.new("E_NOT_FOUND", "service entry does not exist", {
                id = svc.id,
                path = service_path,
            })
        end

        if svc.autostart ~= nil and type(svc.autostart) ~= "boolean" then
            return nil, errors.new("E_INVALID_ARG", "service.autostart must be boolean", { id = svc.id })
        end
    end
    return true
end

function M.validate(value, app_dir, options)
    options = options or {}

    if type(value) ~= "table" then
        return nil, errors.new("E_INVALID_ARG", "manifest must be a table")
    end
    if type(app_dir) ~= "string" or app_dir == "" then
        return nil, errors.new("E_INVALID_ARG", "app_dir is required")
    end

    if value.schema ~= SUPPORTED_SCHEMA then
        return nil, errors.new("E_VERSION", "unsupported manifest schema", {
            expected = SUPPORTED_SCHEMA,
            actual = value.schema,
        })
    end

    local api_major, api_minor = split_api(value.api)
    if not api_major then
        return nil, errors.new("E_VERSION", "manifest api must be MAJOR.MINOR")
    end
    if api_major ~= SUPPORTED_API_MAJOR or api_minor > SUPPORTED_API_MINOR then
        return nil, errors.new("E_VERSION", "unsupported Loom OS App API", {
            supported = string.format("%d.%d", SUPPORTED_API_MAJOR, SUPPORTED_API_MINOR),
            actual = value.api,
        })
    end

    if not valid_app_id(value.id) then
        return nil, errors.new("E_INVALID_ARG", "invalid app id", { id = value.id })
    end
    if type(value.name) ~= "string" or value.name == "" then
        return nil, errors.new("E_INVALID_ARG", "name is required")
    end
    if not split_version(value.version) then
        return nil, errors.new("E_VERSION", "version must be MAJOR.MINOR.PATCH", { version = value.version })
    end
    if not split_version(value.min_loom_os) then
        return nil, errors.new("E_VERSION", "min_loom_os must be MAJOR.MINOR.PATCH", {
            min_loom_os = value.min_loom_os,
        })
    end

    local current_loom_os = options.loom_os_version or version.loom_os
    local cmp, cmp_err = M.compare_semver(current_loom_os, value.min_loom_os)
    if cmp == nil then
        return nil, cmp_err
    end
    if cmp < 0 then
        return nil, errors.new("E_VERSION", "App requires a newer Loom OS version", {
            current = current_loom_os,
            required = value.min_loom_os,
        })
    end

    if not safe_relative_path(value.entry) then
        return nil, errors.new("E_INVALID_ARG", "invalid entry path", { entry = value.entry })
    end
    local entry_path = storage.join_path(app_dir, value.entry)
    if not exists(entry_path) then
        return nil, errors.new("E_NOT_FOUND", "entry file does not exist", { path = entry_path })
    end

    if value.icon ~= nil then
        if not safe_relative_path(value.icon) then
            return nil, errors.new("E_INVALID_ARG", "invalid icon path", { icon = value.icon })
        end
        local icon_path = storage.join_path(app_dir, value.icon)
        if options.require_icon and not exists(icon_path) then
            return nil, errors.new("E_NOT_FOUND", "icon file does not exist", { path = icon_path })
        end
    end

    local ok, err = validate_permissions(value.permissions)
    if not ok then
        return nil, err
    end

    ok, err = validate_services(value.services, app_dir)
    if not ok then
        return nil, err
    end

    return true
end

function M.load(app_dir, options)
    if type(app_dir) ~= "string" or app_dir == "" then
        return nil, errors.new("E_INVALID_ARG", "app_dir is required")
    end

    local manifest_path = storage.join_path(app_dir, "manifest.json")
    if not exists(manifest_path) then
        return nil, errors.new("E_NOT_FOUND", "manifest.json not found", { path = manifest_path })
    end

    local ok, text = pcall(storage.read_file, manifest_path)
    if not ok or type(text) ~= "string" then
        return nil, errors.new("E_IO", "failed to read manifest.json", {
            path = manifest_path,
            cause = ok and nil or tostring(text),
        })
    end

    local value, err = decode_json(text)
    if not value then
        if err and err.detail then
            err.detail.path = manifest_path
        end
        return nil, err
    end

    local valid, valid_err = M.validate(value, app_dir, options)
    if not valid then
        return nil, valid_err
    end

    return value
end

function M.compare_semver(a, b)
    local a1, a2, a3 = split_version(a)
    local b1, b2, b3 = split_version(b)
    if not a1 or not b1 then
        return nil, errors.new("E_VERSION", "invalid semantic version")
    end
    if a1 ~= b1 then return a1 < b1 and -1 or 1 end
    if a2 ~= b2 then return a2 < b2 and -1 or 1 end
    if a3 ~= b3 then return a3 < b3 and -1 or 1 end
    return 0
end

M.is_safe_relative_path = safe_relative_path
M.is_valid_app_id = valid_app_id

return M
