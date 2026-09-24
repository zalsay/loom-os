local jobs = require("system.async.espclaw_jobs")

local calls = {}
jobs.set_capability_adapter({
    call = function(name, args)
        calls[#calls + 1] = { name = name, args = args }
        if name == "lua_run_script_async" then
            return "Started Lua job job-42 (name=ota, exclusive=loom-os-update, timeout_ms=0, log_bytes=4096, status=running) for /fatfs/worker.lua. Use lua_get_async_job or lua_tail_async_job with job_id=job-42 to read logs/results."
        end
        return "ok"
    end,
})

local job = assert(jobs.start({
    path = "/fatfs/worker.lua",
    name = "ota",
    exclusive = "loom-os-update",
    timeout_ms = 0,
}))
assert(job.job_id == "job-42")
assert(calls[1].name == "lua_run_script_async")
assert(calls[1].args.path == "/fatfs/worker.lua")
assert(calls[1].args.exclusive == "loom-os-update")

assert(jobs.get("job-42"))
assert(jobs.tail("job-42"))
assert(jobs.stop("job-42"))
print("async_jobs_test: PASS")
