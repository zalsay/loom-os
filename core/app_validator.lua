local errors = require("core.errors")


local M = {}


local FORBIDDEN_REQUIRE = {
    os = true,
    io = true,
    debug = true,
    package = true
}


local function fail(code, message, detail)
    return nil, errors.new(code, message, detail)
end


local function scan_lua(path, source)
    if type(source) ~= "string" then
        return fail("E_VALIDATE_SOURCE", "source must be text")
    end


    for name in pairs(FORBIDDEN_REQUIRE) do
        local pattern1 = 'require%s*%(%s*["\']' .. name .. '["\']'
        local pattern2 = 'require%s*["\']' .. name .. '["\']'


        if source:match(pattern1) or source:match(pattern2) then
            return fail("E_VALIDATE_REQUIRE", "forbidden module requested", {
                path = path,
                module = name
            })
        end
    end


    if source:find("dofile%s*%(")
        or source:find("loadfile%s*%(")
        or source:find("load%s*%(") then
        return fail("E_VALIDATE_DYNAMIC_CODE", "dynamic code loading is forbidden", {
            path = path
        })
    end


    return true
end


function M.new(deps)
    assert(type(deps) == "table" and type(deps.lua_check) == "function"
        and type(deps.api_check) == "function" and type(deps.board_check) == "function")
    local self = {}


    function self.validate_draft(draft_id, draft)
        local report = {
            ok = false,
            errors = {},
            warnings = {},
            permissions = draft.manifest.permissions or {}
        }


        for _, file in ipairs(draft.files or {}) do
            if file.path:match("%.lua$") then
                local syntax_ok, syntax_err = deps.lua_check(file.content)


                if not syntax_ok then
                    return fail("E_VALIDATE_LUA", "Lua syntax validation failed", {
                        path = file.path,
                        cause = tostring(syntax_err)
                    })
                end


                local scan_ok, scan_err = scan_lua(file.path, file.content)


                if not scan_ok then
                    return nil, scan_err
                end
            end
        end


        local api_ok, api_err =
            deps.api_check(draft.manifest, draft.files)


        if not api_ok then
            return nil, api_err
        end


        local board_ok, board_err =
            deps.board_check(draft.manifest, draft.files)


        if not board_ok then
            return nil, board_err
        end


        report.ok = true
        return report
    end


    function self.validate_approval(draft, approval)
        approval = approval or {}


        local requested = {}
        for name, rule in pairs(draft.manifest.permissions or {}) do
            if rule ~= false and rule ~= nil then requested[name] = true end
        end
        local approved = {}
        for _, name in ipairs(approval.permissions or {}) do approved[name] = true end
        for name in pairs(requested) do
            if not approved[name] then
                return fail("E_PERMISSION_APPROVAL", "permission not approved", { permission = name })
            end
        end

        return true
    end


    return self
end


return M
