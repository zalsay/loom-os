-- App release state machine; filesystem operations are isolated in a backend.
local installer = require("core.app_installer")
local errors = require("core.errors")
local M = {}
local function fail(code, message) return nil, errors.new(code, message) end
function M.new(backend)
    assert(type(backend) == "table", "backend required")
    local self = {}
    function self.install(pkg)
        local valid, err = installer.validate_package(pkg)
        if not valid then return nil, err end
        local id, version = pkg.manifest.id, pkg.manifest.version
        local state, state_err = backend.read_state(id)
        if state_err then return nil, state_err end
        state = state or {}
        if state.pending_version then return fail("E_BUSY", "App already has a pending release") end
        if state.active_version then
            local comparison = require("core.manifest").compare_semver(version, state.active_version)
            if not comparison or comparison <= 0 then
                return fail("E_APP_VERSION", "App update must advance the version")
            end
        end
        if backend.release_exists(id, version) then return fail("E_APP_VERSION_EXISTS", "release already exists") end
        local staging, stage_err = backend.create_staging(id, version)
        if not staging then return nil, stage_err end
        local function abort(e) backend.remove_tree(staging); return nil, e end
        local wrote, write_err = backend.write_package(staging, pkg)
        if not wrote then return abort(write_err) end
        local checked, check_err = backend.validate_staging(staging, pkg)
        if not checked then return abort(check_err) end
        local committed, commit_err = backend.commit_release(staging, id, version)
        if not committed then return abort(commit_err) end
        local saved, save_err = backend.write_state(id, {
            active_version = state.active_version,
            previous_version = state.previous_version,
            pending_version = version,
        })
        if not saved then
            if backend.discard_release then backend.discard_release(id, version) end
            return nil, save_err
        end
        return { app_id = id, version = version, pending = true }
    end
    function self.confirm(id, version)
        local state, err = backend.read_state(id)
        if err then return nil, err end
        if not state or state.pending_version ~= version then
            return fail("E_APP_NOT_PENDING", "version is not pending")
        end
        return backend.write_state(id, {
            active_version = version, previous_version = state.active_version,
        })
    end
    function self.rollback(id)
        local state, err = backend.read_state(id)
        if err then return nil, err end
        if not state then return fail("E_APP_STATE", "missing app state") end
        if not state.pending_version and not state.previous_version then
            return fail("E_APP_ROLLBACK", "no rollback target")
        end
        local fallback = state.pending_version and state.active_version or state.previous_version
        local saved, save_err = backend.write_state(id, { active_version = fallback })
        if not saved then return nil, save_err end
        return fallback or true
    end
    function self.active_version(id)
        local state, err = backend.read_state(id)
        if not state then return nil, err end
        return state.pending_version or state.active_version
    end
    return self
end
return M
