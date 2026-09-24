-- ClawOS core/permissions.lua
-- Manifest-backed capability authorization.

local errors = require("core.errors")

local M = {}

local function manifest_of(app)
    if type(app) ~= "table" then
        return nil
    end
    if type(app.manifest) == "table" then
        return app.manifest
    end
    return app
end

local function permission_denied(capability, detail)
    return false, errors.new("E_PERMISSION", "permission denied: " .. tostring(capability), detail)
end

local function contains(array, value)
    if type(array) ~= "table" then
        return false
    end
    for _, item in ipairs(array) do
        if item == value then
            return true
        end
    end
    return false
end

function M.check(app, capability, detail)
    if type(capability) ~= "string" or capability == "" then
        return false, errors.new("E_INVALID_ARG", "capability is required")
    end

    local manifest = manifest_of(app)
    if not manifest then
        return false, errors.new("E_INVALID_ARG", "App manifest is required")
    end

    local permissions = manifest.permissions or {}
    local rule = permissions[capability]
    if rule == nil or rule == false then
        return permission_denied(capability, detail)
    end
    if rule == true then
        return true
    end

    if capability == "gpio" then
        local pin = detail and detail.pin
        if type(pin) ~= "number" then
            return false, errors.new("E_INVALID_ARG", "GPIO permission check requires detail.pin")
        end
        if type(rule) == "table" and contains(rule.pins, pin) then
            return true
        end
        return permission_denied(capability, { pin = pin })
    end

    if capability == "sensor" then
        local id = detail and detail.id
        if type(id) ~= "string" or id == "" then
            return false, errors.new("E_INVALID_ARG", "sensor permission check requires detail.id")
        end
        if contains(rule, id) then
            return true
        end
        return permission_denied(capability, { id = id })
    end

    if capability == "network" then
        if type(rule) == "table" and rule.enabled == true then
            return true
        end
        return permission_denied(capability, detail)
    end

    -- Future structured capabilities (i2c/uart/audio/storage.shared) may use
    -- either boolean true or an object carrying `enabled = true` in v0.1.
    if type(rule) == "table" and rule.enabled == true then
        return true
    end

    return permission_denied(capability, detail)
end

function M.require(app, capability, detail)
    local ok, err = M.check(app, capability, detail)
    if not ok then
        error(err.message, 2)
    end
    return true
end

return M
