local M = {}


function M.new(deps)
    local api = {}


    local function allowed()
        return deps.permissions:has("system.app.author")
    end


    function api.create(request)
        if not allowed() then
            return nil, {
                code = "E_PERMISSION",
                message = "system.app.author permission required"
            }
        end


        return deps.app_author.create(request)
    end


    function api.modify(app_id, request)
        if not allowed() then
            return nil, {
                code = "E_PERMISSION",
                message = "system.app.author permission required"
            }
        end


        return deps.app_author.modify(app_id, request)
    end


    function api.install(draft_id, approval)
        if not allowed() then
            return nil, {
                code = "E_PERMISSION",
                message = "system.app.author permission required"
            }
        end


        return deps.app_author.install(draft_id, approval)
    end


    return api
end


return M
