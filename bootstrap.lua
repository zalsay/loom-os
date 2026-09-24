-- ClawOS bootstrap.lua
-- Stable loader for DATA-root ClawOS runtime releases.
-- Normal ClawOS OTA updates MUST NOT replace this file.


local storage = require("storage")
local json = require("json")


local DATA_ROOT = assert(storage.get_root_dir())
local RUNTIME_ROOT = storage.join_path(DATA_ROOT, "clawos-runtime")
local RELEASES_ROOT = storage.join_path(RUNTIME_ROOT, "releases")
local STATE_PATH = storage.join_path(RUNTIME_ROOT, "state.json")
local BOOTSTRAP_VERSION = "0.1.0"


local function decode(text)
    local ok, value = pcall(json.decode, text)
    if not ok or type(value) ~= "table" then return nil end
    return value
end


local function encode(value)
    local ok, text = pcall(json.encode, value)
    if not ok then return nil end
    return text
end


local function load_state()
    if not storage.exists(STATE_PATH) then return { schema = 1 } end
    local ok, text = pcall(storage.read_file, STATE_PATH)
    if not ok or type(text) ~= "string" then
        return { schema = 1, last_error = "state read failed" }
    end
    return decode(text) or { schema = 1, last_error = "state decode failed" }
end


local function save_state(state)
    local text = assert(encode(state), "failed to encode ClawOS runtime state")
    local ok, result = pcall(storage.write_file, STATE_PATH, text)
    assert(ok and result ~= false, "failed to write ClawOS runtime state")
end


local function clear_clawos_modules()
    local prefixes = {
        "^core%.", "^api%.", "^ui%.", "^boards%.", "^services%.",
        "^system%.", "^update%.",
    }
    for name in pairs(package.loaded) do
        for _, pattern in ipairs(prefixes) do
            if name:match(pattern) then
                package.loaded[name] = nil
                break
            end
        end
    end
end


local function run_release(version, pending)
    local root = storage.join_path(RELEASES_ROOT, version)
    local entry = storage.join_path(root, "main.lua")
    if not storage.exists(entry) then
        return nil, "ClawOS release missing main.lua: " .. tostring(version)
    end


    local old_path = package.path
    package.path =
        storage.join_path(root, "?.lua") .. ";" ..
        storage.join_path(root, "?/init.lua") .. ";" ..
        old_path


    clear_clawos_modules()


    local chunk, load_err = loadfile(entry, "t", _G)
    if not chunk then
        package.path = old_path
        clear_clawos_modules()
        return nil, load_err
    end


    local ok, result = xpcall(function()
        return chunk({
            version = version,
            pending = pending == true,
            runtime_root = root,
            data_root = DATA_ROOT,
            bootstrap_version = BOOTSTRAP_VERSION,
        })
    end, debug.traceback)


    package.path = old_path
    clear_clawos_modules()


    if not ok then return nil, result end
    return result or { action = "exit" }
end


local function rollback_pending(state, failed_version, reason)
    state.last_failed_version = failed_version
    state.last_error = tostring(reason or "pending release exited before confirmation")
    state.pending_version = nil
    state.pending_attempts = 0
    save_state(state)
end


while true do
    local state = load_state()
    local selected = state.pending_version or state.active_version
    assert(selected, "ClawOS runtime is not provisioned: no active_version")


    local was_pending = state.pending_version == selected
    if was_pending then
        state.pending_attempts = (state.pending_attempts or 0) + 1
        save_state(state)
    end


    local result, run_err = run_release(selected, was_pending)


    if not result then
        if was_pending and state.active_version then
            rollback_pending(load_state(), selected, run_err)
        else
            error(run_err)
        end
    else
        local latest = load_state()
        local still_pending = latest.pending_version == selected
        if was_pending and still_pending then
            rollback_pending(latest, selected, "candidate returned before confirm_boot")
        elseif type(result) == "table" and result.action == "restart" then
            -- Re-read state and select active/pending release again.
        else
            return result
        end
    end
end