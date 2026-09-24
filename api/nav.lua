-- ClawOS api/nav.lua

local navigation = require("core.navigation")

local M = {}

function M.new()
    return {
        home = function()
            return navigation.enqueue({ type = "home" })
        end,
        back = function()
            return navigation.enqueue({ type = "back" })
        end,
        open = function(app_id, args)
            return navigation.enqueue({ type = "open", app_id = app_id, args = args })
        end,
        reload = function(args)
            return navigation.enqueue({ type = "reload", args = args })
        end,
    }
end

return M
