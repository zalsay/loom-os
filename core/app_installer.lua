-- Validates App packages before staging. Files are text-only in v0.1.
local errors = require("core.errors")
local manifest_core = require("core.manifest")
local M = {}
local function fail(code, message, detail) return nil, errors.new(code, message, detail) end

function M.safe_path(path)
    if type(path) ~= "string" or path == "" or path:sub(1, 1) == "/"
        or path:find("\\", 1, true) or path:find("//", 1, true)
        or path:match("^[A-Za-z]:") then return false end
    for segment in path:gmatch("[^/]+") do
        if segment == "." or segment == ".." or segment == "" then return false end
    end
    return true
end

function M.validate_manifest(manifest)
    if type(manifest) ~= "table" then return fail("E_APP_MANIFEST", "manifest must be a table") end
    if not manifest_core.is_valid_app_id(manifest.id) then return fail("E_APP_ID", "invalid app id") end
    if type(manifest.version) ~= "string" or not manifest.version:match("^%d+%.%d+%.%d+$") then
        return fail("E_APP_VERSION", "invalid app version")
    end
    if not M.safe_path(manifest.entry) or not manifest.entry:match("%.lua$") then
        return fail("E_APP_ENTRY", "invalid Lua entry path")
    end
    if manifest.schema ~= 1 or manifest.api ~= "0.1" or type(manifest.name) ~= "string"
        or manifest.name == "" or type(manifest.min_loom_os) ~= "string" then
        return fail("E_APP_MANIFEST", "schema, api, name and min_loom_os are required")
    end
    if manifest.permissions ~= nil and type(manifest.permissions) ~= "table" then
        return fail("E_APP_MANIFEST", "permissions must be an object")
    end
    return true
end

function M.validate_package(pkg)
    if type(pkg) ~= "table" then return fail("E_APP_PACKAGE", "package descriptor required") end
    local ok, err = M.validate_manifest(pkg.manifest)
    if not ok then return nil, err end
    if type(pkg.files) ~= "table" or #pkg.files == 0 then
        return fail("E_APP_FILES", "package contains no files")
    end
    local seen = {}
    for _, file in ipairs(pkg.files) do
        if type(file) ~= "table" or not M.safe_path(file.path)
            or file.path == "manifest.json" or type(file.content) ~= "string" then
            return fail("E_APP_PATH", "invalid package file", { path = type(file) == "table" and file.path })
        end
        if seen[file.path] then return fail("E_EXISTS", "duplicate package file", { path = file.path }) end
        seen[file.path] = true
    end
    if not seen[pkg.manifest.entry] then return fail("E_APP_ENTRY", "entry file missing from package") end
    return true
end
return M
