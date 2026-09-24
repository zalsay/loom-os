-- Private drafts under DATA/loom-os/authoring; never scanned as runnable Apps.
local storage = require("storage")
local json = require("json")
local paths = require("core.paths")
local errors = require("core.errors")
local M, seq = {}, 0
local function root()
    local p, err = paths.resolve()
    if not p then return nil, err end
    local ok, layout_err = paths.ensure_layout(p)
    if not ok then return nil, layout_err end
    return p.authoring
end
local function file(id, name)
    if type(id) ~= "string" or not id:match("^draft%-%d+%-%d+$") then
        return nil, errors.new("E_INVALID_ARG", "invalid draft id")
    end
    local base, err = root()
    if not base then return nil, err end
    return storage.join_path(base, id, name)
end
local function write(id, name, value)
    local path, err = file(id, name)
    if not path then return nil, err end
    local ok, content = pcall(json.encode, value)
    if not ok then return nil, errors.new("E_IO", "draft encode failed") end
    local wrote, result = pcall(storage.write_file, path, content)
    if not wrote or result == false then return nil, errors.new("E_IO", "draft write failed") end
    return true
end
local function read(id, name)
    local path, err = file(id, name)
    if not path then return nil, err end
    if not storage.exists(path) then return nil end
    local ok, content = pcall(storage.read_file, path)
    if not ok then return nil, errors.new("E_IO", "draft read failed") end
    local decoded, value = pcall(json.decode, content)
    if not decoded then return nil, errors.new("E_IO", "invalid draft JSON") end
    return value
end
function M.create(draft)
    local base, err = root()
    if not base then return nil, err end
    seq = seq + 1
    local id = "draft-" .. tostring(math.floor(os.clock() * 1000000)) .. "-" .. tostring(seq)
    while storage.exists(storage.join_path(base, id)) do
        seq = seq + 1
        id = "draft-" .. tostring(math.floor(os.clock() * 1000000)) .. "-" .. tostring(seq)
    end
    local dir = storage.join_path(base, id)
    local ok, mkdir_err = pcall(storage.mkdir, dir)
    if not ok or mkdir_err == false then return nil, errors.new("E_IO", "draft directory failed") end
    local saved, save_err = write(id, "draft.json", draft)
    if saved == false or saved == nil then return nil, save_err end
    return id
end
function M.read(id) return read(id, "draft.json") end
function M.write_report(id, report) return write(id, "report.json", report) end
function M.read_report(id) return read(id, "report.json") end
function M.mark_failed(id, err) return write(id, "report.json", { ok = false, error = err }) end
function M.read_active_app(id)
    local state, state_err = require("core.app_backend").read_state(id)
    if state_err then return nil, state_err end
    if state and state.pending_version then
        return nil, errors.new("E_BUSY", "confirm pending App before modifying it")
    end
    local apps = require("core.apps")
    local record = apps.get(id)
    if not record then return nil, errors.new("E_NOT_FOUND", "active App not found") end
    return { manifest = record.manifest, entry_source = storage.read_file(
        storage.join_path(record.dir, record.manifest.entry)) }
end
return M
