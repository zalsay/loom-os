-- ClawOS system/async/espclaw_jobs.lua
-- Thin system wrapper around ESP-Claw cap_lua async job capabilities.

local errors = require("system.net.errors")

local M = {}
local capability_adapter = nil

local function load_capability()
    if capability_adapter then return capability_adapter end
    local ok, capability = pcall(require, "capability")
    if not ok or type(capability) ~= "table" then
        return nil, errors.wrap("E_NET_UNSUPPORTED", "ESP-Claw capability module unavailable", capability)
    end
    capability_adapter = capability
    return capability_adapter
end

function M.set_capability_adapter(adapter)
    capability_adapter = adapter
    return true
end

local function call_cap(name, args)
    local cap, err = load_capability()
    if not cap then return nil, err end
    if type(cap.call) ~= "function" then
        return nil, errors.new("E_NET_UNSUPPORTED", "capability.call is unavailable")
    end
    local ok, a, b = pcall(cap.call, name, args or {})
    if not ok then
        return nil, errors.wrap("E_NET_BACKEND", name .. " capability call failed", a)
    end
    if a == nil or a == false then
        return nil, errors.wrap("E_NET_BACKEND", name .. " failed", b or a)
    end
    return a, b
end

local function as_text(value)
    if type(value) == "string" then return value end
    if type(value) == "table" then
        if type(value.output) == "string" then return value.output end
        if type(value.result) == "string" then return value.result end
        if type(value.text) == "string" then return value.text end
    end
    return nil
end

local function parse_job_id(value)
    if type(value) == "table" then
        if type(value.job_id) == "string" then return value.job_id end
        if type(value.id) == "string" then return value.id end
    end
    local text = as_text(value)
    if not text then return nil end
    return text:match("Started Lua job%s+([%w%-%._]+)")
        or text:match("job[_%s]id[=:]%s*([%w%-%._]+)")
end

function M.start(options)
    if type(options) ~= "table" or type(options.path) ~= "string" or options.path == "" then
        return nil, errors.new("E_NET_INVALID_ARG", "async Lua job path is required")
    end
    local raw, err = call_cap("lua_run_script_async", {
        path = options.path,
        args = options.args or {},
        timeout_ms = options.timeout_ms == nil and 0 or options.timeout_ms,
        log_bytes = options.log_bytes or 4096,
        name = options.name,
        exclusive = options.exclusive,
        replace = options.replace == true,
    })
    if not raw then return nil, err end
    local id = parse_job_id(raw)
    if not id then
        return nil, errors.new("E_PROTOCOL", "could not parse ESP-Claw async Lua job id", { raw = as_text(raw) })
    end
    return { job_id = id, raw = raw }
end

function M.get(job_id_or_name)
    if type(job_id_or_name) ~= "string" or job_id_or_name == "" then
        return nil, errors.new("E_NET_INVALID_ARG", "job id/name is required")
    end
    local raw, err = call_cap("lua_get_async_job", { job_id = job_id_or_name })
    if not raw then return nil, err end
    return { raw = raw, text = as_text(raw) }
end

function M.tail(job_id_or_name, options)
    options = options or {}
    if type(job_id_or_name) ~= "string" or job_id_or_name == "" then
        return nil, errors.new("E_NET_INVALID_ARG", "job id/name is required")
    end
    local raw, err = call_cap("lua_tail_async_job", {
        job_id = job_id_or_name,
        since_seq = options.since_seq,
        max_bytes = options.max_bytes or 2048,
    })
    if not raw then return nil, err end
    return { raw = raw, text = as_text(raw) }
end

function M.stop(job_id_or_name, wait_ms)
    if type(job_id_or_name) ~= "string" or job_id_or_name == "" then
        return nil, errors.new("E_NET_INVALID_ARG", "job id/name is required")
    end
    return call_cap("lua_stop_async_job", {
        job_id = job_id_or_name,
        wait_ms = wait_ms or 2000,
    })
end

function M.list(status)
    local raw, err = call_cap("lua_list_async_jobs", { status = status or "all" })
    if not raw then return nil, err end
    return { raw = raw, text = as_text(raw) }
end

return M
