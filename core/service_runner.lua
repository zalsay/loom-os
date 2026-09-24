-- Background services own a separate sandbox and resource registry from the UI.
local errors = require("core.errors")
local M, running, system_options, next_instance = {}, {}, {}, 100000
function M.configure(options) system_options = options or {}; return true end
function M.start(id, spec)
    if type(id) ~= "string" or id == "" or type(spec) ~= "table" then
        return nil, errors.new("E_INVALID_ARG", "service id and spec required")
    end
    if running[id] then return nil, errors.new("E_EXISTS", "service already running") end
    local service = { id = id, state = "CREATED", spec = spec, generation = 1 }
    if type(spec.on_start) == "function" then
        local ok, err = pcall(spec.on_start, service)
        if not ok then
            if spec.resources then spec.resources:release_all() end
            return nil, errors.new("E_START", tostring(err))
        end
    end
    service.state = "RUNNING"
    running[id] = service
    return service
end
function M.stop(id)
    local service = running[id]
    if not service then return nil, errors.new("E_NOT_FOUND", "service not found") end
    running[id] = nil
    service.state = "STOPPING"
    service.generation = service.generation + 1
    if type(service.spec.on_stop) == "function" then pcall(service.spec.on_stop, service) end
    if service.spec.resources then service.spec.resources:release_all() end
    service.state = "STOPPED"
    return true
end
function M.status(id)
    if id then return running[id] end
    local out = {}; for k, v in pairs(running) do out[k] = v end; return out
end
function M.exists(id) return running[id] ~= nil end
function M.stop_app(app_id, version)
    local prefix = app_id .. ":"
    for id, service in pairs(running) do
        if id:sub(1, #prefix) == prefix
            and (not version or service.spec.version == version) then M.stop(id) end
    end
    return true
end
function M.prepare_update(record)
    local resume = {}
    local prefix = record.id .. ":"
    for id, service in pairs(running) do
        if id:sub(1, #prefix) == prefix and service.spec.version ~= record.manifest.version then
            resume[#resume + 1] = { record = service.spec.record, service_id = service.spec.service_id }
            M.stop(id)
        end
    end
    return resume
end
function M.restore(previous)
    for _, item in ipairs(previous or {}) do M.start_app(item.record, item.service_id) end
end
function M.start_app(record, service_id)
    local permissions = require("core.permissions")
    local ok, perm_err = permissions.check(record, "background")
    if not ok then return nil, perm_err end
    local descriptor
    for _, item in ipairs(record.manifest.services or {}) do
        if item.id == service_id then descriptor = item; break end
    end
    if not descriptor then return nil, errors.new("E_NOT_FOUND", "service not declared in manifest") end
    local id = record.id .. ":" .. service_id
    if running[id] then return nil, errors.new("E_EXISTS", "service already running") end
    next_instance = next_instance + 1
    local resources = assert(require("core.resources").new(next_instance))
    local storage = require("storage")
    local data_dir = storage.join_path(require("core.apps").paths().appdata, record.id)
    if not storage.exists(data_dir) then storage.mkdir(data_dir) end
    record.data_dir, record.assets_dir = data_dir, storage.join_path(record.dir, "assets")
    local providers = {
        storage = assert(require("api.storage").new(record)),
        timer = assert(require("api.timer").new(resources)),
        system = require("api.system").new(system_options),
        sensor = assert(require("api.sensor").new(record)),
        notify = assert(require("api.notify").new(record, resources)),
        network = require("api.network").new(record, resources),
        agent = require("api.agent").new(record, resources),
    }
    local ctx = assert(require("core.context").new_service(record, descriptor, resources, providers))
    local sandbox = require("core.sandbox")
    local env, cache = sandbox.build(record, { print_fn = function(...)
        require("core.remote_debug").write("INFO", id, ...)
        print(...)
    end })
    local definition, load_err = sandbox.load_service(record, descriptor, env)
    if not definition then resources:release_all(); return nil, load_err end
    local service, start_err = M.start(id, {
        record = record, service_id = service_id, version = record.manifest.version,
        resources = resources,
        on_start = function() if definition.on_start then definition.on_start(ctx) end end,
        on_stop = function() if definition.on_stop then definition.on_stop(ctx) end; sandbox.clear_cache(cache) end,
    })
    return service, start_err
end
return M
