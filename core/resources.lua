-- Loom OS core/resources.lua
-- Per-App resource registry with fail-safe teardown and callback guards.

local errors = require("core.errors")

local M = {}

local DEFAULT_RELEASE_ORDER = {
    "network_requests",
    "agent_requests",
    "timers",
    "listeners",
    "sensors",
    "gpio",
    "ui_objects",
    "other",
}

local Registry = {}
Registry.__index = Registry

local function release_entry(entry)
    if entry.released then
        return true
    end
    entry.released = true

    if type(entry.release) ~= "function" then
        return true
    end

    local ok, result, err = pcall(entry.release, entry.resource)
    if not ok then
        return nil, errors.new("E_IO", "resource release raised an error", {
            kind = entry.kind,
            cause = tostring(result),
        })
    end
    if result == false or result == nil and err ~= nil then
        return nil, errors.new("E_IO", "resource release failed", {
            kind = entry.kind,
            cause = err,
        })
    end
    return true
end

function Registry:is_active()
    return self.state == "active"
end

function Registry:add(kind, resource, release_fn)
    if self.state ~= "active" then
        return nil, errors.new("E_BUSY", "resource registry is not active", {
            state = self.state,
            kind = kind,
        })
    end
    if type(kind) ~= "string" or kind == "" then
        return nil, errors.new("E_INVALID_ARG", "resource kind is required")
    end

    local bucket = self.buckets[kind]
    if not bucket then
        bucket = {}
        self.buckets[kind] = bucket
    end

    local entry = {
        kind = kind,
        resource = resource,
        release = release_fn,
        released = false,
    }
    bucket[#bucket + 1] = entry
    return entry
end

function Registry:remove(kind, resource, release_now)
    local bucket = self.buckets[kind]
    if not bucket then
        return false
    end

    for i = #bucket, 1, -1 do
        local entry = bucket[i]
        if entry.resource == resource then
            table.remove(bucket, i)
            if release_now then
                return release_entry(entry)
            end
            entry.released = true
            return true
        end
    end
    return false
end

function Registry:release_kind(kind)
    local bucket = self.buckets[kind]
    if not bucket then
        return true, {}
    end

    local failures = {}
    for i = #bucket, 1, -1 do
        local entry = bucket[i]
        local ok, err = release_entry(entry)
        if not ok then
            failures[#failures + 1] = err
        end
        bucket[i] = nil
    end
    return #failures == 0, failures
end

function Registry:release_all(order)
    if self.state == "released" then
        return true, {}
    end

    self.state = "stopping"
    self.generation = self.generation + 1

    local failures = {}
    local visited = {}
    local release_order = order or DEFAULT_RELEASE_ORDER

    for _, kind in ipairs(release_order) do
        visited[kind] = true
        local ok, errs = self:release_kind(kind)
        if not ok then
            for _, err in ipairs(errs) do
                failures[#failures + 1] = err
            end
        end
    end

    for kind, _ in pairs(self.buckets) do
        if not visited[kind] then
            local ok, errs = self:release_kind(kind)
            if not ok then
                for _, err in ipairs(errs) do
                    failures[#failures + 1] = err
                end
            end
        end
    end

    self.state = "released"
    return #failures == 0, failures
end

function Registry:guard(fn, on_error)
    assert(type(fn) == "function", "guard requires a function")
    local registry = self
    local generation = self.generation

    return function(...)
        if registry.state ~= "active" or registry.generation ~= generation then
            return nil, errors.new("E_CANCELLED", "callback belongs to an inactive App instance")
        end

        local args = table.pack(...)
        local ok, result_or_err, b, c = xpcall(function()
            return fn(table.unpack(args, 1, args.n))
        end, function(err)
            return tostring(err)
        end)

        if not ok then
            local wrapped = errors.new("E_CRASH", "App callback failed", {
                cause = result_or_err,
            })
            if type(on_error) == "function" then
                pcall(on_error, wrapped)
            end
            return nil, wrapped
        end

        return result_or_err, b, c
    end
end

function M.new(app_instance_id)
    if type(app_instance_id) ~= "number" then
        return nil, errors.new("E_INVALID_ARG", "app_instance_id must be a number")
    end

    return setmetatable({
        app_instance_id = app_instance_id,
        generation = 1,
        state = "active",
        buckets = {},
    }, Registry)
end

return M
