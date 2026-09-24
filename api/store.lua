local M = {}


function M.new(deps)
    local api = {}


    function api.install(package_descriptor)
        if not deps.permissions:has("system.app.install") then
            return nil, {
                code = "E_PERMISSION",
                message = "system.app.install permission required"
            }
        end


        return deps.app_update.install(package_descriptor)
    end


    function api.rollback(app_id)
        if not deps.permissions:has("system.app.install") then
            return nil, {
                code = "E_PERMISSION",
                message = "system.app.install permission required"
            }
        end


        return deps.app_update.rollback(app_id)
    end


    return api
end


return M
