local version = require("core.runtime_version")


local valid = {
    {"0.1.0", "stable"},
    {"0.1.10", "stable"},
    {"0.2.0-dev.1", "dev"},
    {"0.2.0-beta.12", "beta"},
    {"0.2.0-rc.3", "rc"},
    {"1.0.0", "stable"},
}


for _, item in ipairs(valid) do
    local parsed, err = version.validate_for_channel(item[1], item[2])
    assert(parsed, item[1] .. ": " .. tostring(err))
end


local invalid = {
    "v0.1.0",
    "0.01.0",
    "0.1",
    "0.1.0-alpha.1",
    "0.1.0-beta",
    "0.1.0-beta.0",
    "0.1.0-beta.01",
    "0.1.0+build.4",
    "latest",
}


for _, v in ipairs(invalid) do
    assert(version.parse(v) == nil, "expected invalid version: " .. v)
end


assert(version.compare("0.1.10", "0.1.9") > 0)
assert(version.compare("0.2.0-dev.2", "0.2.0-dev.1") > 0)
assert(version.compare("0.2.0-beta.1", "0.2.0-dev.99") > 0)
assert(version.compare("0.2.0-rc.1", "0.2.0-beta.99") > 0)
assert(version.compare("0.2.0", "0.2.0-rc.99") > 0)
assert(version.compare("1.0.0", "0.99.99") > 0)


local manifest = {
    schema = 1,
    product = "loom-os",
    board = "esp-mosaico",
    channel = "stable",
    version = "0.1.1",
    release_id = "loom-os:esp-mosaico:0.1.1",
    min_bootstrap = "0.1.0",
}
assert(version.validate_manifest(manifest))


manifest.channel = "beta"
assert(version.validate_manifest(manifest) == nil)


print("runtime_version_test: PASS")