-- Opt-in development log forwarding. Runs only in the system Lua state.
local storage = require("storage")
local json = require("json")
local requests = require("system.net.request")

local M = {}
local config, session, queue, seq, pending, ticks = nil, nil, {}, 0, nil, 0
local paused = false

local function valid_base(url)
    if type(url) ~= "string" or #url > 256 or url:find("[%s%c]") then return false end
    local host, port = url:match("^https://([%w%.%-]+):(%d+)$")
    if not host then host = url:match("^https://([%w%.%-]+)$") end
    if not host or not host:match("^[%w][%w%.%-]*[%w]$") then return false end
    if port and (tonumber(port) < 1 or tonumber(port) > 65535) then return false end
    return true
end

local function valid_config(value)
    return type(value) == "table" and value.enabled == true and value.channel == "dev"
        and type(value.device_id) == "string" and #value.device_id <= 64
        and value.device_id:match("^[%w_-]+$") ~= nil
        and valid_base(value.server_url)
        and type(value.token) == "string" and #value.token >= 32 and #value.token <= 256
        and value.token:find("[%c]") == nil
end

function M.configure(paths)
    config, session, queue, seq, pending, ticks, paused = nil, nil, {}, 0, nil, 0, false
    local path = storage.join_path(paths.state, "remote-debug.json")
    if not storage.exists(path) then return true end
    local ok, raw = pcall(storage.read_file, path)
    if not ok or type(raw) ~= "string" or #raw > 2048 then return nil, "invalid remote debug config" end
    local decoded, value = pcall(json.decode, raw)
    if not decoded or type(value) ~= "table" then return nil, "invalid remote debug config" end
    if value.enabled ~= true then return true end
    if not valid_config(value) then return nil, "invalid remote debug config" end

    -- A persisted boot counter lets the server distinguish retries from a new boot.
    local session_path = storage.join_path(paths.state, "remote-debug-session.txt")
    local old = "0"
    if storage.exists(session_path) then
        local read_ok, data = pcall(storage.read_file, session_path)
        if not read_ok or type(data) ~= "string" or not data:match("^%d+$") or #data > 15 then
            return nil, "invalid remote debug session"
        end
        old = data
    end
    local next_session = tostring(tonumber(old) + 1)
    local wrote, result = pcall(storage.write_file, session_path, next_session)
    if not wrote or not result then return nil, "cannot save remote debug session" end
    config = value
    session = next_session
    return true
end

function M.enabled() return config ~= nil end

function M.write(level, source, ...)
    if not config then return end
    if level ~= "WARN" and level ~= "ERROR" then level = "INFO" end
    source = tostring(source):gsub("[^%w._-]", "_"):sub(1, 64)
    local values = {}
    for i = 1, select("#", ...) do values[i] = tostring(select(i, ...)) end
    local message = table.concat(values, "\t"):sub(1, 512)
    seq = seq + 1
    queue[#queue + 1] = { seq = seq, level = level, source = source, message = message }
    if #queue > 80 then table.remove(queue, 1) end
end

function M.flush()
    if not config or paused or pending or #queue == 0 then return false end
    local batch = {}
    for i = 1, math.min(#queue, 16) do batch[i] = queue[i] end
    local last_seq = batch[#batch].seq
    local ok, body = pcall(json.encode, { session = session, entries = batch })
    if not ok or type(body) ~= "string" or #body > 32768 then return nil, "log encoding failed" end
    local id, err = requests.create({
        method = "POST",
        url = config.server_url .. "/v1/loom-os/devices/" .. config.device_id .. "/logs",
        headers = { ["Authorization"] = "Bearer " .. config.token, ["Content-Type"] = "application/json" },
        body = body,
        max_body_bytes = 1024,
    }, function(response, request_err)
        pending = nil
        if request_err then return end
        if response and response.status == 401 then paused = true; return end
        if response and response.status == 204 then
            while queue[1] and queue[1].seq <= last_seq do table.remove(queue, 1) end
        end
    end)
    if not id then return nil, err end
    pending = id
    return true
end

function M.poll()
    if not config then return end
    ticks = ticks + 1
    if ticks >= 250 then
        ticks = 0
        M.flush()
    end
end

return M
