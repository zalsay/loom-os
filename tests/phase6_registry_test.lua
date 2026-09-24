-- ClawOS Phase 6 sensor/notification core tests (no hardware required).

local sensors = require("core.sensors")
local sensor_api = require("api.sensor")
local notify_api = require("api.notify")
local notifications = require("core.notifications")
local resources = require("core.resources")

sensors.clear()
notifications.clear()

assert(sensors.register("environment", {
    read = function()
        return { temperature = 25.5, humidity = 61 }
    end,
}, { unit = "mixed" }))

local app = {
    manifest = {
        id = "org.clawos.phase6-test",
        permissions = {
            sensor = { "environment" },
            notification = true,
        },
    }
}

local sensor = assert(sensor_api.new(app))
local visible = sensor.list()
assert(#visible == 1 and visible[1].id == "environment")
local reading = assert(sensor.read("environment"))
assert(reading.temperature == 25.5)

local registry = assert(resources.new(6001))
local notify = assert(notify_api.new(app, registry))
local id = assert(notify.show({ title = "Test", message = "Hello", level = "info" }))
local actions = notifications.drain_actions()
assert(#actions == 1 and actions[1].type == "show" and actions[1].item.id == id)
assert(notify.dismiss(id))
actions = notifications.drain_actions()
assert(#actions == 1 and actions[1].type == "dismiss")

print("ClawOS Phase 6 registry test: PASS")
