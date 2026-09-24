-- System-only Creator composition. The UI must explicitly supply a verified provider.
local M = {}
function M.new(provider)
    local catalog = require("core.capability_catalog")
    local allowed = {}
    for _, name in ipairs(catalog.current().apis) do allowed[name:sub(5)] = true end
    local validator = require("core.app_validator").new({
        lua_check = function(source)
            local chunk, err = load(source, "@draft", "t", {})
            return chunk ~= nil, err
        end,
        api_check = function(_, files)
            for _, file in ipairs(files) do
                if file.path:match("%.lua$") then
                    for name in file.content:gmatch("ctx%.([%a_][%w_]*)") do
                        if not allowed[name] and name ~= "app" then
                            return nil, { code = "E_UNSUPPORTED", message = "unknown ctx API: " .. name }
                        end
                    end
                end
            end
            return true
        end,
        board_check = function(manifest)
            local known = {}
            for _, id in ipairs(catalog.current().sensors) do known[id] = true end
            for _, id in ipairs((manifest.permissions or {}).sensor or {}) do
                if not known[id] then
                    return nil, { code = "E_UNSUPPORTED", message = "sensor unavailable: " .. id }
                end
            end
            return true
        end,
    })
    local author = require("core.app_author").new({
        agent = require("system.agent.app_builder").new(provider, catalog),
        workspace = require("core.author_workspace"), validator = validator,
        app_update = require("core.app_update").new(require("core.app_backend")),
    })
    return author
end
return M
