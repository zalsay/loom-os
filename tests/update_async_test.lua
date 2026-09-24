-- Contract-level test. Device execution still requires ESP-Claw async capability.
local jobs = require("system.async.espclaw_jobs")

jobs.set_capability_adapter({
    call = function(name, payload)
        if name == "lua_run_script_async" then
            assert(type(payload.path) == "string")
            assert(payload.exclusive == "loom-os-runtime-update")
            return "Started Lua job test-job (name=loom-os-runtime-update, exclusive=loom-os-runtime-update, timeout_ms=0, log_bytes=8192, status=running) for " .. payload.path .. ". Use lua_get_async_job or lua_tail_async_job with job_id=test-job to read logs/results."
        end
        return "ok"
    end,
})

-- update_async itself is integration-tested on device because it requires storage paths.
local started = assert(jobs.start({
    path = "/fatfs/loom-os-runtime/releases/0.1.0/update/async_install_worker.lua",
    args = { request_path = "/fatfs/loom-os-runtime/jobs/runtime-update-0.1.1.json" },
    timeout_ms = 0,
    log_bytes = 8192,
    name = "loom-os-runtime-update",
    exclusive = "loom-os-runtime-update",
}))
assert(started.job_id == "test-job")
print("update_async_test: PASS")
