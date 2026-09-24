-- ClawOS core/sandbox.lua
-- Per-App Lua environment and App-local require implementation.

local storage = require("storage")
local errors = require("core.errors")

local M = {}

local LOADING = {}

local function readonly_library(source, label)
    if type(source) ~= "table" then
        return source
    end
    return setmetatable({}, {
        __index = source,
        __newindex = function()
            error((label or "library") .. " is read-only", 2)
        end,
        __pairs = function()
            return pairs(source)
        end,
        __len = function()
            return #source
        end,
        __metatable = "locked",
    })
end

local function safe_module_name(name)
    if type(name) ~= "string" or name == "" then
        return false
    end
    if name:find("/", 1, true) or name:find("\\", 1, true) then
        return false
    end
    if name:find("..", 1, true) then
        return false
    end
    return name:match("^[A-Za-z_][A-Za-z0-9_.]*$") ~= nil
end

local function file_exists(path)
    local ok, value = pcall(storage.exists, path)
    return ok and value == true
end

local function load_chunk(path, env)
    local chunk, err = loadfile(path, "t", env)
    if not chunk then
        return nil, errors.new("E_LOAD", "failed to compile Lua file", {
            path = path,
            cause = tostring(err),
        })
    end
    return chunk
end

local function protected_run(chunk, path)
    local ok, value = xpcall(chunk, function(err)
        return tostring(err)
    end)
    if not ok then
        return nil, errors.new("E_LOAD", "Lua module execution failed", {
            path = path,
            cause = value,
        })
    end
    return value
end

local function build_require(app_record, env, cache)
    local lib_root = storage.join_path(app_record.dir, "lib")

    return function(name)
        if not safe_module_name(name) then
            error("invalid or forbidden App-local module name: " .. tostring(name), 2)
        end

        local cached = cache[name]
        if cached == LOADING then
            error("circular App-local require: " .. name, 2)
        end
        if cached ~= nil then
            return cached
        end

        local rel = name:gsub("%.", "/")
        local candidates = {
            storage.join_path(lib_root, rel .. ".lua"),
            storage.join_path(lib_root, rel, "init.lua"),
        }

        local path = nil
        for _, candidate in ipairs(candidates) do
            if file_exists(candidate) then
                path = candidate
                break
            end
        end
        if not path then
            error("App-local module not found: " .. name, 2)
        end

        cache[name] = LOADING
        local chunk, compile_err = load_chunk(path, env)
        if not chunk then
            cache[name] = nil
            error(compile_err.message, 2)
        end

        local value, run_err = protected_run(chunk, path)
        if run_err then
            cache[name] = nil
            error(run_err.message, 2)
        end

        if value == nil then
            value = true
        end
        cache[name] = value
        return value
    end
end

function M.build(app_record, options)
    options = options or {}
    if type(app_record) ~= "table" or type(app_record.dir) ~= "string" then
        return nil, errors.new("E_INVALID_ARG", "app_record.dir is required")
    end

    local env = {}
    local cache = {}

    local allow = {
        assert = assert,
        error = error,
        ipairs = ipairs,
        pairs = pairs,
        next = next,
        pcall = pcall,
        xpcall = xpcall,
        select = select,
        tonumber = tonumber,
        tostring = tostring,
        type = type,
        print = options.print_fn or print,
        math = readonly_library(math, "math"),
        string = readonly_library(string, "string"),
        table = readonly_library(table, "table"),
        utf8 = readonly_library(utf8, "utf8"),
        coroutine = readonly_library(coroutine, "coroutine"),
    }

    for key, value in pairs(allow) do
        env[key] = value
    end

    env._VERSION = _VERSION
    env._G = env
    env.require = build_require(app_record, env, cache)

    return env, cache
end

function M.load_service(record, descriptor, env)
    if type(descriptor) ~= "table" or type(descriptor.entry) ~= "string" then
        return nil, errors.new("E_INVALID_ARG", "service entry required")
    end
    local path = storage.join_path(record.dir, descriptor.entry)
    local chunk, err = load_chunk(path, env)
    if not chunk then return nil, err end
    local definition, run_err = protected_run(chunk, path)
    if run_err then return nil, run_err end
    if type(definition) ~= "table" or type(definition.on_start) ~= "function" then
        return nil, errors.new("E_LOAD", "service entry must provide on_start(ctx)")
    end
    return definition
end

function M.load_entry(app_record, env)
    if type(app_record) ~= "table" or type(app_record.manifest) ~= "table" then
        return nil, errors.new("E_INVALID_ARG", "app_record.manifest is required")
    end
    if type(env) ~= "table" then
        return nil, errors.new("E_INVALID_ARG", "sandbox env is required")
    end

    local entry_path = storage.join_path(app_record.dir, app_record.manifest.entry)
    local chunk, err = load_chunk(entry_path, env)
    if not chunk then
        return nil, err
    end

    local app_def, run_err = protected_run(chunk, entry_path)
    if run_err then
        return nil, run_err
    end
    if type(app_def) ~= "table" then
        return nil, errors.new("E_LOAD", "App entry must return a table", { path = entry_path })
    end
    if type(app_def.on_create) ~= "function" then
        return nil, errors.new("E_LOAD", "App entry must define on_create(ctx, args)", { path = entry_path })
    end

    for _, name in ipairs({"on_resume", "on_pause", "on_destroy"}) do
        if app_def[name] ~= nil and type(app_def[name]) ~= "function" then
            return nil, errors.new("E_LOAD", name .. " must be a function when present", { path = entry_path })
        end
    end

    return app_def
end

function M.clear_cache(cache)
    if type(cache) ~= "table" then
        return
    end
    for key, _ in pairs(cache) do
        cache[key] = nil
    end
end

return M
