-- Loom OS main.lua
-- Mosaico v0.1 runtime entry. Loaded by bootstrap.lua from a versioned release.




local boot_context = ... or {}




local paths_mod = require("core.paths")
local apps = require("core.apps")
local board = require("core.board")
local navigation = require("core.navigation")
local ui_runtime = require("core.ui_runtime")
local app_runtime = require("core.app_runtime")
local timers = require("core.timers")
local sensors = require("core.sensors")
local runtime_control = require("core.runtime_control")
local runtime_update = require("core.runtime_update")
local update_async = require("core.update_async")
local gpio_api = require("api.gpio")
local nav_api = require("api.nav")
local launcher = require("ui.launcher")
local crash_screen = require("ui.crash_screen")
local notification_center = require("ui.notification_center")
local service_runner = require("core.service_runner")
local net_requests = require("system.net.request")
local agent_runtime = require("system.agent.runtime")
local remote_debug = require("core.remote_debug")
local settings = require("core.settings")
local settings_screen = require("ui.settings")
local settings_status = require("system.settings_status")




runtime_control.reset()


if type(boot_context.runtime_root) == "string" and boot_context.runtime_root ~= "" then
    assert(update_async.configure({
        runtime_root = boot_context.runtime_root,
    }))
end




local paths, err = paths_mod.resolve()
assert(paths, err and err.message or "failed to resolve Loom OS paths")
assert(paths_mod.ensure_layout(paths))
local debug_ok, debug_err = remote_debug.configure(paths)
if not debug_ok then print("Loom OS remote debug disabled:", debug_err) end
remote_debug.write("INFO", "runtime", "boot", boot_context.version or "unknown")




local scan, scan_err = apps.scan()
assert(scan, scan_err and scan_err.message or "App scan failed")




local board_adapter, board_info = board.load("mosaico")
assert(board_adapter, board_info and board_info.message or "Mosaico board adapter failed")




local reserved, reserve_err = board_adapter.reserve_gpio(gpio_api)
assert(reserved, reserve_err and reserve_err.message or reserve_err or "GPIO reservation failed")




-- Sensor providers are intentionally empty until their official ESP-Claw Lua
-- driver path is verified on Mosaico. Board metadata is already available.
local registered, sensor_err = board_adapter.register_sensors(sensors, {})
assert(registered, sensor_err and sensor_err.message or sensor_err or "sensor registration failed")




local ui, ui_err = ui_runtime.init({
    display_device = board_adapter.display.lcd_device,
    touch_device = board_adapter.display.touch_device,
    expected_width = board_adapter.display.width,
    expected_height = board_adapter.display.height,
    require_touch = true,
})
assert(ui, ui_err and ui_err.message or "Loom OS UI init failed")
local settings_ok, settings_err = settings.configure(paths, {
    theme = ui_runtime.set_theme,
    wifi = { status = settings_status.wifi_status },
})
if not settings_ok then print("Loom OS settings unavailable:", settings_err.message) end




local nav = nav_api.new()




local function show_launcher()
    ui_runtime.set_title("Loom OS")
    launcher.show(ui, apps.list(), nav)
end




service_runner.configure(board_adapter.system_options({}))
for _, record in ipairs(apps.list()) do
    if not record.pending_version then
        for _, service in ipairs(record.manifest.services or {}) do
            if service.autostart == true then
                local started, start_err = service_runner.start_app(record, service.id)
                if not started then
                    print("Loom OS service start failed:", record.id, service.id,
                        start_err and start_err.message or "unknown error")
                    remote_debug.write("ERROR", "service", record.id, service.id,
                        start_err and start_err.message or "unknown error")
                end
            end
        end
    end
end

app_runtime.configure({
    ui_state = ui,
    system_options = board_adapter.system_options({}),
    on_crash = function(instance, app_err)
        remote_debug.write("ERROR", instance.record.id, "crash",
            app_err and app_err.message or "unknown error",
            app_err and app_err.detail and app_err.detail.cause or "")
        ui_runtime.set_title("Crash")
        crash_screen.show(ui, instance.record.manifest.name, app_err, nav)
    end,
})




navigation.set_handler(function(action)
    if action.type == "home" or action.type == "back" then
        app_runtime.stop(action.type)
        show_launcher()
        return true
    end




    if action.type == "open" then
        local ok, open_err = app_runtime.launch(action.app_id, action.args)
        if not ok then
            ui_runtime.set_title("Crash")
            crash_screen.show(ui, action.app_id, open_err, nav)
            return nil, open_err
        end
        local current = app_runtime.current()
        if current then
            ui_runtime.set_title(current.record.manifest.name)
        end
        return true
    end

    if action.type == "settings" then
        app_runtime.stop("settings")
        ui_runtime.set_title("设置")
        settings_screen.show(ui, settings, nav)
        return true
    end




    if action.type == "reload" then
        local current = app_runtime.current()
        local name = current and current.record.manifest.name or "App"
        local ok, reload_err = app_runtime.reload(action.args)
        if not ok then
            ui_runtime.set_title("Crash")
            crash_screen.show(ui, name, reload_err, nav)
            return nil, reload_err
        end
        current = app_runtime.current()
        if current then ui_runtime.set_title(current.record.manifest.name) end
        return true
    end




    return true
end)




show_launcher()
-- Let LVGL complete one event cycle before a pending release is marked healthy.
ui_runtime.process_events(0)




local confirm_ok, confirm_err = runtime_update.confirm_boot(boot_context)
assert(confirm_ok, confirm_err and confirm_err.message or "failed to confirm Loom OS runtime boot")




local ok, loop_err = xpcall(function()
    while not runtime_control.should_exit() do
        ui_runtime.process_events(20)
        net_requests.poll()
        remote_debug.poll()
        agent_runtime.poll()




        local _, timer_failures = timers.tick()
        if timer_failures and #timer_failures > 0 then
            for _, timer_err in ipairs(timer_failures) do
                print("Loom OS timer error:", timer_err.message)
                remote_debug.write("ERROR", "timer", timer_err.message)
            end
        end




        notification_center.process(ui)
        navigation.process_next()


        -- Network/file download runs in an ESP-Claw async Lua job.
        -- The UI state only observes pending_version and requests soft restart.
        local update_ready, update_err = update_async.poll(boot_context.version)
        if update_ready == nil and update_err then
            print("Loom OS update poll error:", update_err.message or update_err)
            remote_debug.write("ERROR", "update", update_err.message or update_err)
        end
    end
end, function(e)
    return debug.traceback(tostring(e), 2)
end)




app_runtime.stop("runtime_exit")
notification_center.clear()
ui_runtime.shutdown()




if not ok then
    error(loop_err)
end




return runtime_control.result()
