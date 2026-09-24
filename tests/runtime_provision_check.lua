-- ClawOS tests/runtime_provision_check.lua
-- Read-only verification after initial 0.1.1 provisioning.


local storage = require("storage")
local json = require("json")
local files = require("provision.runtime_files")


local expected = (args and args.expected_version) or "0.1.1"
local data_root = assert(storage.get_root_dir())
local runtime_root = storage.join_path(data_root, "clawos-runtime")
local state_path = storage.join_path(runtime_root, "state.json")
local release_dir = storage.join_path(storage.join_path(runtime_root, "releases"), expected)


assert(storage.exists(state_path), "Runtime state.json is missing")
local state = assert(json.decode(assert(storage.read_file(state_path))))
assert(state.active_version == expected, "unexpected active_version: " .. tostring(state.active_version))
assert(state.pending_version == nil, "initial provisioning must not leave pending_version")
assert(state.last_good_version == expected, "unexpected last_good_version")


for _, relative in ipairs(files) do
    local path = storage.join_path(release_dir, relative)
    assert(storage.exists(path), "provisioned Runtime file missing: " .. relative)
end


print("runtime_provision_check: PASS active=" .. expected .. " files=" .. tostring(#files))