-- Uses a verified structured-output provider; no placeholder success response.
local errors = require("core.errors")
local M = {}
local RULES = "Return a JSON Loom OS App draft. Use only catalog APIs and no native modules, os, io, debug, package, load, dofile or loadfile."
function M.new(provider, catalog)
    local self = {}
    function self.generate_app(input)
        if type(provider) ~= "table" or type(provider.generate_app) ~= "function" then
            return nil, errors.new("E_UNSUPPORTED", "structured App provider unavailable")
        end
        local draft, err = provider.generate_app({ system = RULES, operation = input.operation,
            request = input.request, current_app = input.current_app,
            capability_catalog = catalog.current() })
        if not draft then return nil, err end
        if type(draft) ~= "table" then return nil, errors.new("E_AGENT_FORMAT", "invalid App draft") end
        return draft
    end
    return self
end
return M
