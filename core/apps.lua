-- ClawOS core/apps.lua
-- Phase 1 App discovery and registry construction.

local storage = require("storage")
local paths_mod = require("core.paths")
local manifest = require("core.manifest")
local errors = require("core.errors")
local app_backend = require("core.app_backend")
local app_update = require("core.app_update").new(app_backend)

local M = {}
local registry = {}
local current_paths = nil

local function entry_name(entry)
    if type(entry) == "string" then
        return entry
    end
    if type(entry) == "table" then
        return entry.name or entry.filename or entry.basename
    end
    return nil
end

local function listdir(path)
    local ok, entries = pcall(storage.listdir, path)
    if not ok then
        return nil, errors.new("E_IO", "failed to list apps directory", {
            path = path,
            cause = tostring(entries),
        })
    end
    if type(entries) ~= "table" then
        return nil, errors.new("E_IO", "storage.listdir returned non-table", { path = path })
    end
    return entries
end

local function clone_registry(src)
    local out = {}
    for id, record in pairs(src) do
        out[id] = record
    end
    return out
end

local function safe_scan_one(apps_root, name, options)
    if type(name) ~= "string" or name == "" or name == "." or name == ".." then
        return nil
    end

    local app_dir = storage.join_path(apps_root, name)
    local state, state_err = app_backend.read_state(name)
    if state_err then
        return { id = nil, dir = app_dir, source_name = name, enabled = false, error = state_err }
    end
    local selected = state and (state.pending_version or state.active_version)
    if state then
        if not selected then return nil end
        app_dir = storage.join_path(app_dir, "releases", selected)
    end
    local manifest_path = storage.join_path(app_dir, "manifest.json")

    local ok, exists = pcall(storage.exists, manifest_path)
    if not ok or not exists then
        return nil
    end

    local value, err = manifest.load(app_dir, options)
    if not value and state and state.pending_version then
        app_update.rollback(name)
        return safe_scan_one(apps_root, name, options)
    end
    if not value then
        return {
            id = nil,
            dir = app_dir,
            source_name = name,
            enabled = false,
            error = err,
        }
    end

    return {
        id = value.id,
        manifest = value,
        dir = app_dir,
        pending_version = state and state.pending_version,
        enabled = true,
        error = nil,
    }
end

function M.scan(options)
    options = options or {}

    local paths, err = paths_mod.resolve()
    if not paths then
        return nil, err
    end
    local ok
    ok, err = paths_mod.ensure_layout(paths)
    if not ok then
        return nil, err
    end

    local entries
    entries, err = listdir(paths.apps)
    if not entries then
        return nil, err
    end

    local next_registry = {}
    local invalid = {}
    local seen_ids = {}

    for _, raw_entry in ipairs(entries) do
        local name = entry_name(raw_entry)
        local record = safe_scan_one(paths.apps, name, options)
        if record then
            if record.enabled then
                local first = seen_ids[record.id]
                if first then
                    local duplicate = errors.new("E_EXISTS", "duplicate app id", {
                        id = record.id,
                        first_dir = first.dir,
                        second_dir = record.dir,
                    })

                    if first.enabled then
                        first.enabled = false
                        first.error = duplicate
                        invalid[#invalid + 1] = first
                    end

                    record.enabled = false
                    record.error = duplicate
                    invalid[#invalid + 1] = record
                    next_registry[record.id] = nil
                else
                    seen_ids[record.id] = record
                    next_registry[record.id] = record
                end
            else
                invalid[#invalid + 1] = record
            end
        end
    end

    registry = next_registry
    current_paths = paths

    return {
        apps = clone_registry(registry),
        invalid = invalid,
        paths = paths,
    }
end

function M.get(app_id)
    if type(app_id) ~= "string" then
        return nil
    end
    return registry[app_id]
end

function M.list(options)
    options = options or {}
    local out = {}
    for _, record in pairs(registry) do
        if options.include_disabled or record.enabled then
            out[#out + 1] = record
        end
    end
    table.sort(out, function(a, b)
        local an = (a.manifest and a.manifest.name) or a.id or ""
        local bn = (b.manifest and b.manifest.name) or b.id or ""
        return an < bn
    end)
    return out
end

function M.paths()
    return current_paths
end

return M
