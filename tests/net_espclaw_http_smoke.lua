-- Device-side smoke test for the real ESP-Claw http_request Capability.
-- Run with args.url pointing at a host already present in ESP-Claw's HTTP allowlist.

local http = require("system.net.http_client")

assert(type(args) == "table" and type(args.url) == "string", "args.url is required")

local response, err = http.get(args.url, {
    timeout_ms = args.timeout_ms or 10000,
    max_body_bytes = args.max_body_bytes or 4096,
})

if not response then
    error((err and err.code or "E_HTTP") .. ": " .. (err and err.message or "request failed"))
end

print("status:", response.status)
print("bytes:", response.bytes or 0)
if response.body then
    print(response.body)
end

print("net_espclaw_http_smoke: PASS")
