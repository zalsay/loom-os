-- Device storage backend for App staging and versioned releases.
local storage = require("storage")
local json = require("json")
local errors = require("core.errors")
local manifest = require("core.manifest")
local paths = require("core.paths")
local M = {}
local nonce = 0
local function fail(message, cause)
    return nil, errors.new("E_IO", message, { cause = tostring(cause) })
end
local function call(name, ...)
    local fn = storage[name]
    if type(fn) ~= "function" then return fail("storage." .. name .. " unavailable") end
    local ok, a, b = pcall(fn, ...)
    if not ok or a == false then return fail("storage." .. name .. " failed", ok and b or a) end
    return a == nil and true or a, b
end
local function join(...) return storage.join_path(...) end
local function roots()
    local p, err = paths.resolve()
    if not p then return nil, err end
    p.app_staging = join(p.root, "app-staging")
    return p
end
local function ensure(path)
    if storage.exists(path) then return true end
    return call("mkdir", path)
end
local function parents(root, relative)
    local dir = root
    local parts = {}
    for segment in relative:gmatch("[^/]+") do parts[#parts + 1] = segment end
    for i = 1, #parts - 1 do
        dir = join(dir, parts[i])
        local ok, err = ensure(dir)
        if not ok then return nil, err end
    end
    return true
end
local function app_root(p, id) return join(p.apps, id) end
local function state_path(p, id) return join(app_root(p, id), "state.json") end
function M.read_state(id)
    local p, err = roots()
    if not p then return nil, err end
    local path = state_path(p, id)
    if not storage.exists(path) then return nil end
    local content, read_err = call("read_file", path)
    if not content then return nil, read_err end
    local ok, value = pcall(json.decode, content)
    if not ok or type(value) ~= "table" then return fail("invalid App state JSON", path) end
    return value
end
function M.write_state(id, state)
    local p, err = roots()
    if not p then return nil, err end
    local root = app_root(p, id)
    local ok, mkdir_err = ensure(root)
    if not ok then return nil, mkdir_err end
    local encoded, content = pcall(json.encode, state)
    if not encoded then return fail("App state encode failed", content) end
    -- A single small state write follows the existing Runtime OTA storage contract.
    return call("write_file", state_path(p, id), content)
end
function M.release_exists(id, version)
    local p = roots()
    return p and storage.exists(join(app_root(p, id), "releases", version)) == true
end
function M.create_staging(id, version)
    local p, err = roots()
    if not p then return nil, err end
    local ok, layout_err = paths.ensure_layout(p)
    if not ok then return nil, layout_err end
    ok, layout_err = ensure(p.app_staging)
    if not ok then return nil, layout_err end
    local stage
    repeat
        nonce = nonce + 1
        stage = join(p.app_staging, id .. "-" .. version .. "-" .. tostring(nonce))
    until not storage.exists(stage)
    local created, create_err = ensure(stage)
    if not created then return nil, create_err end
    return stage
end
function M.write_package(stage, pkg)
    for _, file in ipairs(pkg.files) do
        local ok, err = parents(stage, file.path)
        if not ok then return nil, err end
        ok, err = call("write_file", join(stage, file.path), file.content)
        if not ok then return nil, err end
    end
    local encoded, content = pcall(json.encode, pkg.manifest)
    if not encoded then return fail("App manifest encode failed", content) end
    return call("write_file", join(stage, "manifest.json"), content)
end
function M.validate_staging(stage, pkg)
    local loaded, err = manifest.load(stage)
    if not loaded then return nil, err end
    if loaded.id ~= pkg.manifest.id or loaded.version ~= pkg.manifest.version then
        return nil, errors.new("E_APP_MANIFEST", "staged manifest does not match package")
    end
    for _, file in ipairs(pkg.files) do
        if file.path:match("%.lua$") then
            local chunk, syntax_err = loadfile(join(stage, file.path), "t", {})
            if not chunk then return nil, errors.new("E_LOAD", "invalid Lua file", { path = file.path, cause = syntax_err }) end
        end
    end
    return true
end
function M.commit_release(stage, id, version)
    local p, err = roots()
    if not p then return nil, err end
    local root = app_root(p, id)
    for _, dir in ipairs({ root, join(root, "releases") }) do
        local ok, e = ensure(dir)
        if not ok then return nil, e end
    end
    local final = join(root, "releases", version)
    if storage.exists(final) then return nil, errors.new("E_EXISTS", "release exists") end
    return call("rename", stage, final)
end
function M.discard_release(id, version)
    local p, err = roots()
    if not p then return nil, err end
    return M.remove_tree(join(app_root(p, id), "releases", version))
end
function M.remove_tree(path)
    if not storage.exists(path) then return true end
    local entries, err = call("listdir", path)
    if not entries then return call("remove", path) end
    for _, entry in ipairs(entries) do
        local name = type(entry) == "table" and (entry.name or entry.filename) or entry
        if name and name ~= "." and name ~= ".." then
            local child = join(path, name)
            local ok = M.remove_tree(child)
            if not ok then return nil, errors.new("E_IO", "staging cleanup failed", { path = child }) end
        end
    end
    return call("remove", path)
end
return M
