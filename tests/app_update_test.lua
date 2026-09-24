local app_update = require("core.app_update")


local states = {}
local releases = {}
local staging = {}


local backend = {}


function backend.read_state(app_id)
    return states[app_id]
end


function backend.write_state(app_id, state)
    states[app_id] = state
    return true
end


function backend.release_exists(app_id, version)
    return releases[app_id .. ":" .. version] == true
end


function backend.create_staging(app_id, version)
    local path = "staging/" .. app_id .. "-" .. version
    staging[path] = true
    return path
end


function backend.write_package(path, pkg)
    assert(staging[path])
    return true
end


function backend.validate_staging(path, pkg)
    assert(staging[path])
    return true
end


function backend.commit_release(path, app_id, version)
    assert(staging[path])
    staging[path] = nil
    releases[app_id .. ":" .. version] = true
    return true
end


function backend.remove_tree(path)
    staging[path] = nil
    return true
end


local updater = app_update.new(backend)


local pkg_100 = {
    manifest = {
        schema = 1, api = "0.1", min_clawos = "0.1.0",
        id = "org.clawos.demo",
        name = "Demo",
        version = "1.0.0",
        entry = "main.lua"
    },
    files = {
        { path = "main.lua", content = "return { on_create = function() end }" }
    }
}


assert(updater.install(pkg_100))
assert(states["org.clawos.demo"].pending_version == "1.0.0")


assert(updater.confirm("org.clawos.demo", "1.0.0"))
assert(states["org.clawos.demo"].active_version == "1.0.0")
assert(states["org.clawos.demo"].pending_version == nil)


local pkg_110 = {
    manifest = {
        schema = 1, api = "0.1", min_clawos = "0.1.0",
        id = "org.clawos.demo",
        name = "Demo",
        version = "1.1.0",
        entry = "main.lua"
    },
    files = {
        { path = "main.lua", content = "return { on_create = function() end }" }
    }
}


assert(updater.install(pkg_110))
assert(states["org.clawos.demo"].pending_version == "1.1.0")


assert(updater.rollback("org.clawos.demo") == "1.0.0")
assert(states["org.clawos.demo"].active_version == "1.0.0")
assert(states["org.clawos.demo"].pending_version == nil)


print("app_update_test: PASS")
