-- ClawOS Phase 5 device-side non-destructive test.
-- Tests managed timers and permission-before-hardware behavior.

local timers = require("core.timers")
local resources = require("core.resources")
local timer_api = require("api.timer")
local gpio_api = require("api.gpio")

local now = 1000
timers.clear()
assert(timers.set_clock(function() return now end))

local registry = assert(resources.new(5001))
local app = {
    manifest = {
        id = "org.clawos.phase5-test",
        permissions = {},
    }
}

local timer = assert(timer_api.new(registry))
local fired = 0
local id = assert(timer.every(100, function()
    fired = fired + 1
end))

now = 1099
assert(timers.tick() == 0)
assert(fired == 0)
now = 1100
assert(timers.tick() == 1)
assert(fired == 1)

assert(registry:release_all())
now = 1300
timers.tick()
assert(fired == 1, "timer must not run after App release")

-- This must fail at permission check before touching any physical pin.
local registry2 = assert(resources.new(5002))
local gpio = assert(gpio_api.new(app, registry2))
local handle, err = gpio.open(9999, "output")
assert(handle == nil)
assert(err and err.code == "E_PERMISSION")
registry2:release_all()

timers.reset_clock()
print("ClawOS Phase 5 core API test: PASS")
