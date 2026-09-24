-- Loom OS core/app_runtime.lua
-- Foreground App loader/lifecycle execution.


local storage = require("storage")
local errors = require("core.errors")
local apps = require("core.apps")
local sandbox = require("core.sandbox")
local resources_mod = require("core.resources")
local context = require("core.context")
local ui_api = require("api.ui")
local nav_api = require("api.nav")
local storage_api = require("api.storage")
local timer_api = require("api.timer")
local gpio_api = require("api.gpio")
local system_api = require("api.system")
local sensor_api = require("api.sensor")
local notify_api = require("api.notify")
local service_api = require("api.service")
local network_api = require("api.network")
local agent_api = require("api.agent")
local app_update = require("core.app_update").new(require("core.app_backend"))


local M = {}


local ui_state = nil
local current = nil
local instance_seq = 0
local crash_handler = nil
local system_options = {}


local function safe_lifecycle(fn, ...)
    if type(fn) ~= "function" then
        return true
    end
    local args = table.pack(...)
    local ok, result = xpcall(function()
        return fn(table.unpack(args, 1, args.n))
    end, function(err)
        return tostring(err)
    end)
    if not ok then
        return nil, errors.new("E_CRASH", "App lifecycle callback failed", {
            cause = result,
        })
    end
    return true
end


local function build_record_paths(record)
    local p = apps.paths()
    record.data_dir = storage.join_path(p.appdata, record.id)
    record.assets_dir = storage.join_path(record.dir, "assets")
    if not storage.exists(record.data_dir) then
        local ok, err = pcall(storage.mkdir, record.data_dir)
        if not ok or err == false then
            return nil, errors.new("E_IO", "failed to create App data directory", {
                path = record.data_dir,
                cause = ok and nil or tostring(err),
            })
        end
    end
    return true
end


local function build_system_api()
    local options = {}
    for key, value in pairs(system_options or {}) do
        options[key] = value
    end
    options.ui_state = ui_state
    return system_api.new(options)
end


function M.configure(options)
    options = options or {}
    ui_state = assert(options.ui_state, "ui_state is required")
    crash_handler = options.on_crash
    system_options = options.system_options or {}
    return true
end


function M.current()
    return current
end


function M.stop(reason)
    if not current then
        return true
    end


    local inst = current
    current = nil


    local pause_ok, pause_err = safe_lifecycle(inst.app_def.on_pause, inst.ctx, reason or "stop")
    local destroy_ok, destroy_err = safe_lifecycle(inst.app_def.on_destroy, inst.ctx, reason or "stop")


    if inst.resources then
        inst.resources:release_all()
    end
    sandbox.clear_cache(inst.module_cache)


    if not pause_ok then return nil, pause_err end
    if not destroy_ok then return nil, destroy_err end
    return true
end


function M.launch(app_id, args)
    local pending_resume = {}
    local function pending_result(record, ok, err)
        if record and record.pending_version then
            if ok then
                local confirmed, confirm_err = app_update.confirm(record.id, record.pending_version)
                if not confirmed then
                    require("core.service_runner").stop_app(record.id, record.manifest.version)
                    app_update.rollback(record.id)
                    apps.scan()
                    require("core.service_runner").restore(pending_resume)
                    return nil, confirm_err
                end
            else
                require("core.service_runner").stop_app(record.id, record.manifest.version)
                app_update.rollback(record.id)
                apps.scan()
                require("core.service_runner").restore(pending_resume)
            end
        end
        return ok, err
    end
    local record = apps.get(app_id)
    if not record or not record.enabled then
        return nil, errors.new("E_NOT_FOUND", "App not found or disabled", { app_id = app_id })
    end
    if record.pending_version then
        pending_resume = require("core.service_runner").prepare_update(record)
    end


    if current then
        M.stop("switch")
    end


    ui_state.app_layer:clean()
    local paths_ok, paths_err = build_record_paths(record)
    if not paths_ok then
        return pending_result(record, nil, paths_err)
    end


    instance_seq = instance_seq + 1
    local resources = assert(resources_mod.new(instance_seq))
    local env, module_cache = sandbox.build(record)
    if not env then
        resources:release_all()
        return pending_result(record, nil, module_cache)
    end


    local app_def, load_err = sandbox.load_entry(record, env)
    if not app_def then
        resources:release_all()
        return pending_result(record, nil, load_err)
    end


    local ui_provider, ui_err = ui_api.new(
        ui_state.lvgl,
        ui_state.app_layer,
        ui_state.app_width,
        ui_state.app_height,
        resources
    )
    if not ui_provider then
        resources:release_all()
        return pending_result(record, nil, ui_err)
    end


    local app_storage, storage_err = storage_api.new(record)
    if not app_storage then
        resources:release_all()
        return pending_result(record, nil, storage_err)
    end


    local app_timer, timer_err = timer_api.new(resources)
    if not app_timer then
        resources:release_all()
        return pending_result(record, nil, timer_err)
    end


    local app_gpio, gpio_err = gpio_api.new(record, resources)
    if not app_gpio then
        resources:release_all()
        return pending_result(record, nil, gpio_err)
    end


    local app_system = assert(build_system_api())
    local app_sensor = assert(sensor_api.new(record))
    local app_notify = assert(notify_api.new(record, resources))


    local ctx, ctx_err = context.new_app(record, resources, {
        ui = ui_provider,
        nav = nav_api.new(),
        storage = app_storage,
        timer = app_timer,
        gpio = app_gpio,
        system = app_system,
        sensor = app_sensor,
        notify = app_notify,
        service = service_api.new(record),
        network = network_api.new(record, resources),
        agent = agent_api.new(record, resources),
    })
    if not ctx then
        resources:release_all()
        return pending_result(record, nil, ctx_err)
    end


    current = {
        id = record.id,
        record = record,
        app_def = app_def,
        ctx = ctx,
        env = env,
        module_cache = module_cache,
        resources = resources,
        args = args,
    }


    local ok, lifecycle_err = safe_lifecycle(app_def.on_create, ctx, args or {})
    if ok then
        ok, lifecycle_err = safe_lifecycle(app_def.on_resume, ctx)
    end


    if not ok then
        local failed = current
        current = nil
        resources:release_all()
        sandbox.clear_cache(module_cache)
        if type(crash_handler) == "function" then
            pcall(crash_handler, failed, lifecycle_err)
        end
        return pending_result(record, nil, lifecycle_err)
    end


    return pending_result(record, true)
end


function M.reload(args)
    if not current then
        return nil, errors.new("E_NOT_FOUND", "no active App to reload")
    end
    local app_id = current.id
    local reload_args = args or current.args
    M.stop("reload")
    return M.launch(app_id, reload_args)
end


return M
