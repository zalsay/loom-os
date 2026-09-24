-- Loom OS core/update_async.lua
-- Main-state coordinator for non-blocking Runtime OTA.


local storage = require("storage")
local json = require("json")
local errors = require("core.errors")
local jobs = require("system.async.espclaw_jobs")
local runtime_update = require("core.runtime_update")
local runtime_control = require("core.runtime_control")


local M = {}
local runtime_root = nil
local active = nil
local last_result = nil


local function ensure_dir(path)
    if storage.exists(path) then return true end
    local ok, result = pcall(storage.mkdir, path)
    if not ok or result == false then
        return nil, errors.new("E_IO", "failed to create update jobs directory", {
            path = path,
            cause = ok and nil or tostring(result),
        })
    end
    return true
end


local function remove_if_exists(path)
    if storage.exists(path) and type(storage.remove) == "function" then
        pcall(storage.remove, path)
    end
end


local function paths()
    local data = storage.get_root_dir()
    local root = storage.join_path(data, "loom-os-runtime")
    local job_dir = storage.join_path(root, "jobs")
    return {
        root = root,
        jobs = job_dir,
        request = storage.join_path(job_dir, "runtime-update-request.json"),
        result = storage.join_path(job_dir, "runtime-update-result.json"),
    }
end


local function write_request(payload)
    local p = paths()
    local ok, err = ensure_dir(p.root)
    if not ok then return nil, err end
    ok, err = ensure_dir(p.jobs)
    if not ok then return nil, err end


    remove_if_exists(p.request)
    remove_if_exists(p.result)


    payload.schema = 1
    payload.result_path = p.result


    local encoded_ok, text = pcall(json.encode, payload)
    if not encoded_ok then
        return nil, errors.new("E_IO", "failed to encode update request", { cause = tostring(text) })
    end


    local write_ok, result = pcall(storage.write_file, p.request, text)
    if not write_ok or result == false then
        return nil, errors.new("E_IO", "failed to write update request", {
            path = p.request,
            cause = write_ok and nil or tostring(result),
        })
    end


    return p.request, p.result
end


local function start_worker(payload, options, target_version)
    options = options or {}
    if active then
        return nil, errors.new("E_BUSY", "a Loom OS Runtime update job is already active", {
            job_id = active.job_id,
        })
    end
    if type(runtime_root) ~= "string" then
        return nil, errors.new("E_INVALID_ARG", "update_async is not configured")
    end


    local request_path, result_path = write_request(payload)
    if not request_path then return nil, result_path end


    local worker = storage.join_path(runtime_root, "update/async_install_worker.lua")
    if not storage.exists(worker) then
        return nil, errors.new("E_NOT_FOUND", "Runtime OTA async worker is missing", { path = worker })
    end


    local job, job_err = jobs.start({
        path = worker,
        args = { request_path = request_path },
        timeout_ms = options.timeout_ms == nil and 0 or options.timeout_ms,
        log_bytes = options.log_bytes or 8192,
        name = "loom-os-runtime-update",
        exclusive = "loom-os-runtime-update",
        replace = options.replace == true,
    })
    if not job then return nil, job_err end


    active = {
        job_id = job.job_id,
        request_path = request_path,
        result_path = result_path,
        target_version = target_version,
        mode = payload.mode,
        started = true,
    }
    last_result = nil
    return active
end


function M.configure(options)
    options = options or {}
    if type(options.runtime_root) ~= "string" or options.runtime_root == "" then
        return nil, errors.new("E_INVALID_ARG", "runtime_root is required")
    end
    runtime_root = options.runtime_root
    return true
end


function M.start(release, options)
    if type(release) ~= "table" or type(release.version) ~= "string" then
        return nil, errors.new("E_INVALID_ARG", "release manifest is required")
    end
    return start_worker({ mode = "direct", release = release }, options, release.version)
end


function M.start_latest(query, options)
    query = query or {}
    if type(query.base_url) ~= "string"
       or type(query.board) ~= "string"
       or type(query.channel) ~= "string"
       or type(query.current_version) ~= "string"
       or type(query.bootstrap_version) ~= "string" then
        return nil, errors.new("E_INVALID_ARG", "release query requires base_url, board, channel, current_version and bootstrap_version")
    end
    return start_worker({ mode = "latest", query = query }, options, nil)
end


function M.active()
    return active
end


function M.last_result()
    return last_result
end


local function read_result(path)
    if not path or not storage.exists(path) then return nil end
    local ok, raw = pcall(storage.read_file, path)
    if not ok or type(raw) ~= "string" then
        return nil, errors.new("E_IO", "failed to read Runtime update result")
    end
    local decoded_ok, value = pcall(json.decode, raw)
    if not decoded_ok or type(value) ~= "table" then
        return nil, errors.new("E_IO", "invalid Runtime update result JSON")
    end
    return value
end


function M.status()
    if not active then
        return { active = false, last_result = last_result }
    end


    local job_status, err = jobs.get(active.job_id)
    if not job_status then return nil, err end


    local result, result_err = read_result(active.result_path)
    if result_err then return nil, result_err end


    return {
        active = true,
        job_id = active.job_id,
        target_version = active.target_version,
        mode = active.mode,
        result = result,
        raw = job_status.raw,
        text = job_status.text,
    }
end


function M.tail(options)
    if not active then
        return nil, errors.new("E_NOT_FOUND", "no active Runtime update job")
    end
    return jobs.tail(active.job_id, options)
end


function M.cancel()
    if not active then return true end
    local stopped, err = jobs.stop(active.job_id, 2000)
    if not stopped then return nil, err end
    last_result = { status = "canceled", mode = active.mode }
    active = nil
    return true
end


-- Called from the Loom OS main loop. It performs no network or release-file I/O.
-- pending_version in state.json is authoritative even if in-memory job state was lost.
function M.poll(current_version)
    if active then
        local result, result_err = read_result(active.result_path)
        if result_err then return nil, result_err end


        if result then
            last_result = result
            if result.status == "ready" then
                local version = result.version
                active = nil
                runtime_control.request_restart("loom_os_update_ready:" .. tostring(version))
                return true
            elseif result.status == "no_update" then
                active = nil
                return false
            elseif result.status == "failed" then
                active = nil
                return nil, errors.new("E_IO", "Runtime update worker failed", {
                    cause = result.message,
                })
            end
        end
    end


    local state, state_err = runtime_update.status()
    if not state then return nil, state_err end


    if state.pending_version and state.pending_version ~= current_version then
        local version = state.pending_version
        active = nil
        last_result = last_result or { status = "ready", version = version }
        runtime_control.request_restart("loom_os_update_ready:" .. tostring(version))
        return true
    end


    return false
end


return M