local resources = require("core.resources")
local network = require("api.network")
local agent = require("api.agent")
local requests = require("system.net.request")
local agent_runtime = require("system.agent.runtime")
local record = { id = "org.clawos.test", manifest = { permissions = {
    network = { enabled = true }, agent = true } } }
local jobs = {}
local adapter = {
    start = function(options) local job = { options = options }; jobs[#jobs + 1] = job; return job end,
    poll = function(job) return job.done == true, job.result end,
    cancel = function(job) job.cancelled = true end,
}
requests.set_adapter(adapter); agent_runtime.set_adapter(adapter)
local res = assert(resources.new(200))
local net, ai = network.new(record, res), agent.new(record, res)
local calls = 0
assert(net.get("https://example.test/data", function(result) assert(result.status == 200); calls = calls + 1 end))
assert(ai.ask("analyze", function(result) assert(result.text == "ok"); calls = calls + 1 end))
assert(calls == 0) -- callbacks are delivered by poll, not synchronously on the UI stack
jobs[1].done, jobs[1].result = true, { status = 200 }
jobs[2].done, jobs[2].result = true, { text = "ok" }
requests.poll(); agent_runtime.poll(); assert(calls == 2)
local id = assert(net.get("https://example.test/cancel", function() calls = calls + 1 end))
res:release_all(); assert(jobs[3].cancelled)
jobs[3].done = true; requests.poll(); assert(calls == 2)
local bad, err = net.get("http://example.test", function() end)
assert(bad == nil and err.code == "E_INVALID_ARG")
print("network_agent_api_test: PASS")
