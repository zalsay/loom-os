-- Loom OS core/runtime_update.lua
-- Transactional Loom OS Runtime updater. Updates DATA files only.


local storage = require("storage")
local json = require("json")
local errors = require("core.errors")
local runtime_control = require("core.runtime_control")
local runtime_version = require("core.runtime_version")


local M = {}


local function invoke(name, ...)
    local fn = storage[name]
    if type(fn) ~= "function" then
        return nil, errors.new("E_UNSUPPORTED", "storage backend missing " .. name)
    end
    local ok, a, b = pcall(fn, ...)
    if not ok then
        return nil, errors.new("E_IO", "storage." .. name .. " failed", { cause = tostring(a) })
    end
    if a == false then
        return nil, errors.new("E_IO", "storage." .. name .. " failed", { cause = b })
    end
    return a, b
end


local function mutate(name, ...)
    local a, b = invoke(name, ...)
    if a == nil and b then return nil, b end
    return true
end


local function ensure_dir(path)
    if storage.exists(path) then return true end
    return mutate("mkdir", path)
end


local function safe_rel(path)
    if type(path) ~= "string" or path == "" then return false end
    if path:sub(1, 1) == "/" then return false end
    if path:find("\\", 1, true) then return false end
    for seg in path:gmatch("[^/]+") do
        if seg == ".." or seg == "." or seg == "" then return false end
    end
    return true
end


local function valid_version(version)
    return runtime_version.parse(version) ~= nil
end


local function roots()
    local data, err = invoke("get_root_dir")
    if not data then return nil, err end
    local root = storage.join_path(data, "loom-os-runtime")
    return {
        data = data,
        root = root,
        releases = storage.join_path(root, "releases"),
        staging = storage.join_path(root, "staging"),
        state = storage.join_path(root, "state.json"),
    }
end


local function ensure_layout(p)
    for _, dir in ipairs({ p.root, p.releases, p.staging }) do
        local ok, err = ensure_dir(dir)
        if not ok then return nil, err end
    end
    return true
end


local function read_state(p)
    if not storage.exists(p.state) then return { schema = 1 } end
    local text, err = invoke("read_file", p.state)
    if not text then return nil, err end
    local ok, value = pcall(json.decode, text)
    if not ok or type(value) ~= "table" then
        return nil, errors.new("E_IO", "runtime state JSON is invalid")
    end
    value.schema = value.schema or 1
    return value
end


local function write_state(p, state)
    local ok, text = pcall(json.encode, state)
    if not ok then
        return nil, errors.new("E_IO", "runtime state encode failed", { cause = tostring(text) })
    end
    return mutate("write_file", p.state, text)
end


local function mkdir_parents(base, relative)
    local current = base
    local parts = {}
    for seg in relative:gmatch("[^/]+") do parts[#parts + 1] = seg end
    for i = 1, #parts - 1 do
        current = storage.join_path(current, parts[i])
        local ok, err = ensure_dir(current)
        if not ok then return nil, err end
    end
    return true
end


local function validate_release(release)
    if type(release) ~= "table" then
        return nil, errors.new("E_INVALID_ARG", "release manifest must be a table")
    end


    local parsed, version_err = runtime_version.validate_manifest(release)
    if not parsed then
        return nil, errors.new("E_VERSION", "invalid Loom OS release manifest", {
            version = release.version,
            cause = version_err,
        })
    end


    if release.entry ~= "main.lua" then
        return nil, errors.new("E_VERSION", "v0.1 runtime entry must be main.lua")
    end
    if type(release.files) ~= "table" or #release.files == 0 then
        return nil, errors.new("E_INVALID_ARG", "release.files is required")
    end


    local seen = {}
    for _, file in ipairs(release.files) do
        if type(file) ~= "table"
           or not safe_rel(file.path)
           or type(file.url) ~= "string"
           or file.url:sub(1, 8):lower() ~= "https://"
           or type(file.size) ~= "number"
           or file.size < 1
           or file.size % 1 ~= 0 then
            return nil, errors.new("E_INVALID_ARG", "invalid release file entry", {
                path = type(file) == "table" and file.path or nil,
            })
        end
        if seen[file.path] then
            return nil, errors.new("E_EXISTS", "duplicate release file", { path = file.path })
        end
        seen[file.path] = true
    end


    if not seen["main.lua"] then
        return nil, errors.new("E_INVALID_ARG", "release.files must include main.lua")
    end
    return true
end


local function validate_staged(release, dir)
    for _, file in ipairs(release.files) do
        local full = storage.join_path(dir, file.path)
        if not storage.exists(full) then
            return nil, errors.new("E_NOT_FOUND", "staged release file missing", { path = file.path })
        end
        if file.path:sub(-4) == ".lua" then
            local chunk, load_err = loadfile(full, "t", {})
            if not chunk then
                return nil, errors.new("E_LOAD", "Lua syntax validation failed", {
                    path = file.path,
                    cause = load_err,
                })
            end
        end
    end
    return true
end


function M.status()
    local p, err = roots()
    if not p then return nil, err end
    local state, state_err = read_state(p)
    if not state then return nil, state_err end
    return state
end


function M.provision(version)
    if not valid_version(version) then
        return nil, errors.new("E_VERSION", "invalid initial Runtime version")
    end
    local p, err = roots()
    if not p then return nil, err end
    local layout_ok, layout_err = ensure_layout(p)
    if not layout_ok then return nil, layout_err end


    local release_dir = storage.join_path(p.releases, version)
    if not storage.exists(storage.join_path(release_dir, "main.lua")) then
        return nil, errors.new("E_NOT_FOUND", "initial release is not installed", { version = version })
    end


    local state, state_err = read_state(p)
    if not state then return nil, state_err end
    if state.active_version then
        return nil, errors.new("E_EXISTS", "runtime already provisioned")
    end


    state.active_version = version
    state.last_good_version = version
    return write_state(p, state)
end


-- backend.download(url, destination, options) -> result | nil, err
-- Backend MUST enforce HTTPS. Declared file size is verified by the download layer.
function M.install(release, backend, on_progress)
    local valid, valid_err = validate_release(release)
    if not valid then return nil, valid_err end
    if type(backend) ~= "table" or type(backend.download) ~= "function" then
        return nil, errors.new("E_UNSUPPORTED", "update download backend is not configured")
    end


    local p, root_err = roots()
    if not p then return nil, root_err end
    local layout_ok, layout_err = ensure_layout(p)
    if not layout_ok then return nil, layout_err end
    local state, state_err = read_state(p)
    if not state then return nil, state_err end


    if state.active_version then
        local newer, compare_err = runtime_version.is_newer(release.version, state.active_version)
        if newer == nil then
            return nil, errors.new("E_VERSION", "failed to compare Runtime versions", {
                candidate = release.version,
                current = state.active_version,
                cause = compare_err,
            })
        end
        if not newer then
            return nil, errors.new("E_VERSION", "automatic Runtime update must move forward", {
                candidate = release.version,
                current = state.active_version,
            })
        end
    end


    if release.version == state.pending_version then
        return nil, errors.new("E_EXISTS", "release is already pending", { version = release.version })
    end


    local final_dir = storage.join_path(p.releases, release.version)
    local staging_dir = storage.join_path(p.staging, release.version)
    if storage.exists(final_dir) or storage.exists(staging_dir) then
        return nil, errors.new("E_EXISTS", "release/staging directory already exists", {
            version = release.version,
        })
    end


    local mk_ok, mk_err = ensure_dir(staging_dir)
    if not mk_ok then return nil, mk_err end


    for index, file in ipairs(release.files) do
        local parent_ok, parent_err = mkdir_parents(staging_dir, file.path)
        if not parent_ok then return nil, parent_err end


        local dest = storage.join_path(staging_dir, file.path)
        local dl_ok, dl_err = backend.download(file.url, dest, {
            size = file.size,
            path = file.path,
            version = release.version,
        })
        if not dl_ok then
            return nil, dl_err or errors.new("E_IO", "download failed", { path = file.path })
        end


        if type(on_progress) == "function" then
            pcall(on_progress, {
                index = index,
                total = #release.files,
                path = file.path,
                version = release.version,
            })
        end
    end


    local encoded_ok, release_json = pcall(json.encode, release)
    if not encoded_ok then
        return nil, errors.new("E_IO", "failed to encode release manifest")
    end
    local write_ok, write_err = mutate(
        "write_file",
        storage.join_path(staging_dir, "release.json"),
        release_json
    )
    if not write_ok then return nil, write_err end


    local staged_ok, staged_err = validate_staged(release, staging_dir)
    if not staged_ok then return nil, staged_err end


    local rename_ok, rename_err = mutate("rename", staging_dir, final_dir)
    if not rename_ok then return nil, rename_err end


    state.previous_version = state.active_version
    state.pending_version = release.version
    state.pending_attempts = 0
    state.last_update_error = nil


    local state_ok, state_write_err = write_state(p, state)
    if not state_ok then return nil, state_write_err end


    runtime_control.request_restart("loom_os_update:" .. release.version)
    return true
end


function M.install_default(release, on_progress)
    local ok, backend = pcall(require, "update.runtime_backend")
    if not ok or type(backend) ~= "table" or type(backend.download) ~= "function" then
        return nil, errors.new("E_UNSUPPORTED", "default Runtime OTA backend is unavailable", {
            cause = tostring(backend),
        })
    end
    return M.install(release, backend, on_progress)
end


function M.confirm_boot(boot)
    if type(boot) ~= "table" or not valid_version(boot.version) then return true end
    local p, err = roots()
    if not p then return nil, err end
    local state, state_err = read_state(p)
    if not state then return nil, state_err end
    if state.pending_version ~= boot.version then return true end


    local old_active = state.active_version
    state.active_version = boot.version
    state.previous_version = old_active
    state.last_good_version = boot.version
    state.pending_version = nil
    state.pending_attempts = 0
    state.last_update_error = nil
    return write_state(p, state)
end


function M.rollback_pending(reason)
    local p, err = roots()
    if not p then return nil, err end
    local state, state_err = read_state(p)
    if not state then return nil, state_err end
    if not state.pending_version then return true end


    state.last_failed_version = state.pending_version
    state.last_update_error = tostring(reason or "rollback requested")
    state.pending_version = nil
    state.pending_attempts = 0
    return write_state(p, state)
end


return M