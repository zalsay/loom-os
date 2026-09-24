-- Loom OS core/timers.lua
-- Cooperative timer scheduler driven by the Loom OS main loop.

local errors = require("core.errors")

local M = {}
local timers = {}
local next_id = 1

-- Provisional monotonic-ish fallback. Production boards may inject a more
-- precise monotonic clock with set_clock(). Keeping this behind one function
-- means the App API does not change when the backend is upgraded.
local clock_ms = function()
    return math.floor(os.clock() * 1000)
end

local function now_ms()
    local ok, value = pcall(clock_ms)
    if not ok or type(value) ~= "number" then
        return nil, errors.new("E_IO", "timer clock failed", { cause = tostring(value) })
    end
    return math.floor(value)
end

function M.set_clock(fn)
    if type(fn) ~= "function" then
        return nil, errors.new("E_INVALID_ARG", "clock must be a function")
    end
    clock_ms = fn
    return true
end

function M.reset_clock()
    clock_ms = function()
        return math.floor(os.clock() * 1000)
    end
end

local function schedule(delay_ms, interval_ms, callback)
    if type(delay_ms) ~= "number" or delay_ms <= 0 then
        return nil, errors.new("E_INVALID_ARG", "delay_ms must be > 0")
    end
    if interval_ms ~= nil and (type(interval_ms) ~= "number" or interval_ms <= 0) then
        return nil, errors.new("E_INVALID_ARG", "interval_ms must be > 0")
    end
    if type(callback) ~= "function" then
        return nil, errors.new("E_INVALID_ARG", "timer callback must be a function")
    end

    local now, err = now_ms()
    if not now then return nil, err end

    local id = next_id
    next_id = next_id + 1
    timers[id] = {
        id = id,
        due_at = now + math.floor(delay_ms),
        interval_ms = interval_ms and math.floor(interval_ms) or nil,
        callback = callback,
        cancelled = false,
    }
    return id
end

function M.after(delay_ms, callback)
    return schedule(delay_ms, nil, callback)
end

function M.every(interval_ms, callback)
    return schedule(interval_ms, interval_ms, callback)
end

function M.cancel(timer_id)
    local timer = timers[timer_id]
    if not timer then
        return false
    end
    timer.cancelled = true
    timers[timer_id] = nil
    return true
end

function M.tick(max_callbacks)
    local now, err = now_ms()
    if not now then return nil, err end

    max_callbacks = max_callbacks or 32
    local due = {}
    for id, timer in pairs(timers) do
        if not timer.cancelled and timer.due_at <= now then
            due[#due + 1] = id
        end
    end

    table.sort(due, function(a, b)
        local ta, tb = timers[a], timers[b]
        if not ta then return false end
        if not tb then return true end
        if ta.due_at == tb.due_at then return a < b end
        return ta.due_at < tb.due_at
    end)

    local ran = 0
    local failures = {}
    for _, id in ipairs(due) do
        if ran >= max_callbacks then break end
        local timer = timers[id]
        if timer and not timer.cancelled then
            if timer.interval_ms then
                -- Reschedule before callback so callback may cancel itself safely.
                local next_due = timer.due_at + timer.interval_ms
                if next_due <= now then
                    local missed = math.floor((now - timer.due_at) / timer.interval_ms) + 1
                    next_due = timer.due_at + missed * timer.interval_ms
                end
                timer.due_at = next_due
            else
                timers[id] = nil
            end

            local ok, callback_err = pcall(timer.callback)
            if not ok then
                failures[#failures + 1] = errors.new("E_CRASH", "timer callback failed", {
                    timer_id = id,
                    cause = tostring(callback_err),
                })
            end
            ran = ran + 1
        end
    end

    return ran, failures
end

function M.clear()
    timers = {}
end

function M.count()
    local n = 0
    for _ in pairs(timers) do n = n + 1 end
    return n
end

return M
