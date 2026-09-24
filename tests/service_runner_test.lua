local runner = require("core.service_runner")


local started = false
local stopped = false


local service = assert(runner.start("test", {
    on_start=function()
        started=true
    end,
    on_stop=function()
        stopped=true
    end
}))


assert(service.state == "RUNNING")
assert(started)


assert(runner.stop("test"))
assert(stopped)
assert(runner.status("test") == nil)


print("service_runner_test: PASS")
