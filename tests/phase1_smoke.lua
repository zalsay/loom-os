-- Loom OS Phase 1 smoke test.
-- Assumes core/ is visible on package.path and ESP-Claw storage/json modules exist.

local apps = require("core.apps")

local result, err = apps.scan()
if not result then
    error(string.format("scan failed: %s: %s", err.code or "?", err.message or "?"))
end

print("Loom OS Phase 1 scan complete")
print("DATA_ROOT:", result.paths.data_root)
print("APPS_ROOT:", result.paths.apps)

local count = 0
for id, record in pairs(result.apps) do
    count = count + 1
    print("APP:", id, record.manifest.name, record.manifest.version)
end

print("valid apps:", count)
print("invalid apps:", #result.invalid)

for _, record in ipairs(result.invalid) do
    local e = record.error or {}
    print("INVALID:", record.source_name or record.dir, e.code or "?", e.message or "?")
end
