-- ClawOS provision/install_initial.lua
-- One-time provisioning of immutable Runtime release 0.1.1.
-- Run as a system script, not from an App sandbox.


local storage = require("storage")
local json = require("json")
local files = require("provision.runtime_files")


local VERSION = "0.1.1"
local source_root = args and args.source_root
assert(type(source_root) == "string" and source_root ~= "", "args.source_root is required")


local data_root = assert(storage.get_root_dir())
local runtime_root = storage.join_path(data_root, "clawos-runtime")
local releases_root = storage.join_path(runtime_root, "releases")
local staging_root = storage.join_path(runtime_root, "staging")
local staging_dir = storage.join_path(staging_root, "provision-" .. VERSION)
local final_dir = storage.join_path(releases_root, VERSION)
local state_path = storage.join_path(runtime_root, "state.json")
local state_tmp = storage.join_path(runtime_root, "state.json.provisioning")


local function mkdir(path)
    if storage.exists(path) then return true end
    local ok, result = pcall(storage.mkdir, path)
    assert(ok and result ~= false, "mkdir failed: " .. tostring(path))
    return true
end


local function mkdir_parents(base, relative)
    local current = base
    local parts = {}
    for seg in relative:gmatch("[^/]+") do parts[#parts + 1] = seg end
    for i = 1, #parts - 1 do
        current = storage.join_path(current, parts[i])
        mkdir(current)
    end
end


local function copy_file(relative)
    local src = storage.join_path(source_root, relative)
    local dst = storage.join_path(staging_dir, relative)
    assert(storage.exists(src), "source file missing: " .. relative)
    mkdir_parents(staging_dir, relative)


    local read_ok, content = pcall(storage.read_file, src)
    assert(read_ok and type(content) == "string", "read failed: " .. relative)


    local write_ok, result = pcall(storage.write_file, dst, content)
    assert(write_ok and result ~= false, "write failed: " .. relative)
end


local function validate_lua(relative)
    if relative:sub(-4) ~= ".lua" then return end
    local path = storage.join_path(staging_dir, relative)
    local chunk, err = loadfile(path, "t", {})
    assert(chunk, "Lua syntax validation failed for " .. relative .. ": " .. tostring(err))
end


assert(not storage.exists(state_path), "state.json already exists; Runtime is already provisioned or requires manual recovery")
assert(not storage.exists(final_dir), "release 0.1.1 already exists")
assert(not storage.exists(staging_dir), "provision staging already exists; inspect/remove it before retrying")


mkdir(runtime_root)
mkdir(releases_root)
mkdir(staging_root)
mkdir(staging_dir)


for index, relative in ipairs(files) do
    copy_file(relative)
    print(string.format("CLAWOS_PROVISION_COPY %d/%d %s", index, #files, relative))
end


for _, relative in ipairs(files) do
    validate_lua(relative)
end


assert(storage.exists(storage.join_path(staging_dir, "main.lua")), "staged main.lua is missing")


local rename_ok, rename_result = pcall(storage.rename, staging_dir, final_dir)
assert(rename_ok and rename_result ~= false, "failed to activate initial release directory")


local state = {
    schema = 1,
    active_version = VERSION,
    previous_version = nil,
    pending_version = nil,
    last_good_version = VERSION,
    pending_attempts = 0,
}


local encode_ok, state_json = pcall(json.encode, state)
assert(encode_ok and type(state_json) == "string", "failed to encode initial Runtime state")


local write_ok, write_result = pcall(storage.write_file, state_tmp, state_json)
assert(write_ok and write_result ~= false, "failed to write temporary Runtime state")


local state_rename_ok, state_rename_result = pcall(storage.rename, state_tmp, state_path)
assert(state_rename_ok and state_rename_result ~= false, "failed to activate Runtime state")


print("CLAWOS_PROVISION_READY " .. VERSION)
print("Run the stable bootstrap.lua to start ClawOS from releases/" .. VERSION)