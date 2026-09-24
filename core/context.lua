-- ClawOS core/context.lua
-- Builds read-only App and Service Context objects from system API adapters.

local errors = require("core.errors")

local M = {}

local function readonly(data, label)
    return setmetatable({}, {
        __index = data,
        __newindex = function()
            error((label or "value") .. " is read-only", 2)
        end,
        __pairs = function()
            return pairs(data)
        end,
        __len = function()
            return #data
        end,
        __metatable = "locked",
    })
end

local function app_info(app_record)
    local m = app_record.manifest
    return readonly({
        id = m.id,
        name = m.name,
        version = m.version,
        api = m.api,
        path = app_record.dir,
        data_path = app_record.data_dir,
        assets_path = app_record.assets_dir,
    }, "ctx.app")
end

local function wrap_provider(value, label)
    if type(value) ~= "table" then
        return value
    end
    return readonly(value, label)
end

local function build(app_record, resources, apis, is_service)
    if type(app_record) ~= "table" or type(app_record.manifest) ~= "table" then
        return nil, errors.new("E_INVALID_ARG", "app_record.manifest is required")
    end
    if type(resources) ~= "table" then
        return nil, errors.new("E_INVALID_ARG", "resources registry is required")
    end

    apis = apis or {}
    local data = {
        app = app_info(app_record),
    }

    local allowed = {
        "storage",
        "timer",
        "system",
        "sensor",
        "gpio",
        "network",
        "notify",
        "agent",
        "service",
    }

    if not is_service then
        allowed[#allowed + 1] = "ui"
        allowed[#allowed + 1] = "nav"
    end

    for _, name in ipairs(allowed) do
        if apis[name] ~= nil then
            data[name] = wrap_provider(apis[name], "ctx." .. name)
        end
    end

    return readonly(data, is_service and "service ctx" or "app ctx")
end

function M.new_app(app_record, resources, apis)
    return build(app_record, resources, apis, false)
end

function M.new_service(app_record, service_record, resources, apis)
    if type(service_record) ~= "table" then
        return nil, errors.new("E_INVALID_ARG", "service_record is required")
    end
    local ctx, err = build(app_record, resources, apis, true)
    if not ctx then
        return nil, err
    end
    return ctx
end

return M
