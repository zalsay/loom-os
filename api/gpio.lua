-- ClawOS api/gpio.lua
-- Permission-aware GPIO wrapper over ESP-Claw lua_driver_gpio.

local gpio = require("gpio")
local errors = require("core.errors")
local permissions = require("core.permissions")

local M = {}
local claims = {}

local VALID_MODES = {
    input = true,
    output = true,
    input_output = true,
    output_od = true,
    input_output_od = true,
    disable = true,
}

local function call_gpio(name, ...)
    local fn = gpio[name]
    if type(fn) ~= "function" then
        return nil, errors.new("E_UNSUPPORTED", "GPIO backend does not provide " .. name)
    end
    local ok, value = pcall(fn, ...)
    if not ok then
        return nil, errors.new("E_IO", "gpio." .. name .. " failed", { cause = tostring(value) })
    end
    return value
end

function M.reserve_system(pin, owner)
    if claims[pin] then
        return nil, errors.new("E_BUSY", "GPIO pin is already claimed", { pin = pin })
    end
    claims[pin] = { owner = owner or "system", system = true }
    return true
end

function M.release_system(pin, owner)
    local claim = claims[pin]
    if not claim or not claim.system then return false end
    if owner ~= nil and claim.owner ~= owner then return false end
    claims[pin] = nil
    return true
end

function M.new(app_record, resources)
    if type(app_record) ~= "table" or type(app_record.manifest) ~= "table" then
        return nil, errors.new("E_INVALID_ARG", "app_record.manifest is required")
    end
    if type(resources) ~= "table" then
        return nil, errors.new("E_INVALID_ARG", "resources registry is required")
    end

    local api = {}

    function api.open(pin, mode)
        if type(pin) ~= "number" or pin < 0 or pin % 1 ~= 0 then
            return nil, errors.new("E_INVALID_ARG", "pin must be a non-negative integer")
        end
        if not VALID_MODES[mode] then
            return nil, errors.new("E_INVALID_ARG", "unsupported GPIO mode", { mode = mode })
        end

        local allowed, perm_err = permissions.check(app_record, "gpio", { pin = pin })
        if not allowed then return nil, perm_err end

        if claims[pin] then
            return nil, errors.new("E_BUSY", "GPIO pin is already claimed", {
                pin = pin,
                owner = claims[pin].owner,
            })
        end

        local _, dir_err = call_gpio("set_direction", pin, mode)
        if dir_err then return nil, dir_err end

        local handle = {
            pin = pin,
            mode = mode,
            closed = false,
        }
        claims[pin] = { owner = app_record.manifest.id, handle = handle }

        local function close_handle()
            if handle.closed then return true end
            handle.closed = true
            if claims[pin] and claims[pin].handle == handle then
                claims[pin] = nil
            end
            -- Best-effort release. Official GPIO driver supports "disable".
            pcall(gpio.set_direction, pin, "disable")
            return true
        end

        local entry, reg_err = resources:add("gpio", handle, close_handle)
        if not entry then
            close_handle()
            return nil, reg_err
        end

        function handle:read()
            if self.closed then
                return nil, errors.new("E_BUSY", "GPIO handle is closed", { pin = pin })
            end
            return call_gpio("get_level", pin)
        end

        function handle:write(level)
            if self.closed then
                return nil, errors.new("E_BUSY", "GPIO handle is closed", { pin = pin })
            end
            if level ~= 0 and level ~= 1 then
                return nil, errors.new("E_INVALID_ARG", "GPIO level must be 0 or 1")
            end
            local _, write_err = call_gpio("set_level", pin, level)
            if write_err then return nil, write_err end
            return true
        end

        function handle:close()
            resources:remove("gpio", handle, false)
            return close_handle()
        end

        return handle
    end

    return api
end

return M
