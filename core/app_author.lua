local errors = require("core.errors")
local installer = require("core.app_installer")


local M = {}


local function fail(code, message, detail)
    return nil, errors.new(code, message, detail)
end


local function copy_table(value)
    if type(value) ~= "table" then
        return value
    end


    local out = {}
    for k, v in pairs(value) do
        out[k] = copy_table(v)
    end
    return out
end


local function validate_file(file)
    if type(file) ~= "table" then
        return fail("E_AUTHOR_FILE", "generated file descriptor required")
    end


    if type(file.path) ~= "string"
        or file.path == ""
        or file.path:sub(1, 1) == "/"
        or not installer.safe_path(file.path) then
        return fail("E_AUTHOR_PATH", "generated file path is invalid", {
            path = file.path
        })
    end


    if type(file.content) ~= "string" then
        return fail("E_AUTHOR_CONTENT", "generated file content must be text", {
            path = file.path
        })
    end


    return true
end


function M.validate_draft(draft)
    if type(draft) ~= "table" then
        return fail("E_AUTHOR_DRAFT", "draft required")
    end


    if draft.operation ~= "create" and draft.operation ~= "modify" then
        return fail("E_AUTHOR_OPERATION", "unsupported authoring operation")
    end


    local ok, err = installer.validate_manifest(draft.manifest)
    if not ok then
        return nil, err
    end


    if type(draft.files) ~= "table" or #draft.files == 0 then
        return fail("E_AUTHOR_FILES", "generated draft contains no files")
    end


    local seen = {}


    for _, file in ipairs(draft.files) do
        local valid, file_err = validate_file(file)
        if not valid then
            return nil, file_err
        end


        if seen[file.path] then
            return fail("E_AUTHOR_DUPLICATE", "duplicate generated file", {
                path = file.path
            })
        end


        seen[file.path] = true
    end


    if not seen[draft.manifest.entry] then
        return fail("E_AUTHOR_ENTRY", "manifest entry was not generated", {
            entry = draft.manifest.entry
        })
    end


    return true
end


function M.new(deps)
    assert(type(deps) == "table", "deps required")
    assert(deps.agent, "agent required")
    assert(deps.workspace, "workspace required")
    assert(deps.validator, "validator required")
    assert(deps.app_update, "app_update required")


    local self = {}


    function self.create(request)
        local draft, err = deps.agent.generate_app({
            operation = "create",
            request = copy_table(request)
        })


        if not draft then
            return nil, err
        end


        draft.operation = "create"


        local ok, draft_err = M.validate_draft(draft)
        if not ok then
            return nil, draft_err
        end


        local draft_id, workspace_err = deps.workspace.create(draft)
        if not draft_id then return nil, workspace_err end


        local report, validate_err =
            deps.validator.validate_draft(draft_id, draft)


        if not report then
            deps.workspace.mark_failed(draft_id, validate_err)
            return nil, validate_err
        end


        deps.workspace.write_report(draft_id, report)


        return {
            draft_id = draft_id,
            draft = draft,
            report = report
        }
    end


    function self.modify(app_id, request)
        local active, active_err = deps.workspace.read_active_app(app_id)


        if not active then
            return nil, active_err
        end


        local draft, err = deps.agent.generate_app({
            operation = "modify",
            request = copy_table(request),
            current_app = active
        })


        if not draft then
            return nil, err
        end


        draft.operation = "modify"


        if draft.manifest.id ~= app_id then
            return fail("E_AUTHOR_ID_CHANGE", "modify cannot change app id")
        end
        local compare = require("core.manifest").compare_semver
        local ordering = compare(draft.manifest.version, active.manifest.version)
        if not ordering or ordering <= 0 then
            return fail("E_APP_VERSION", "modified App version must increase")
        end


        local ok, draft_err = M.validate_draft(draft)
        if not ok then
            return nil, draft_err
        end


        local draft_id, workspace_err = deps.workspace.create(draft)
        if not draft_id then return nil, workspace_err end


        local report, validate_err =
            deps.validator.validate_draft(draft_id, draft)


        if not report then
            deps.workspace.mark_failed(draft_id, validate_err)
            return nil, validate_err
        end


        deps.workspace.write_report(draft_id, report)


        return {
            draft_id = draft_id,
            draft = draft,
            report = report
        }
    end


    function self.install(draft_id, approval)
        local draft = deps.workspace.read(draft_id)


        if not draft then
            return fail("E_AUTHOR_NOT_FOUND", "draft not found")
        end


        local valid, draft_err = M.validate_draft(draft)
        if not valid then return nil, draft_err end
        local report = deps.workspace.read_report(draft_id)


        if not report or report.ok ~= true then
            return fail("E_AUTHOR_NOT_VALID", "draft has not passed validation")
        end


        local fresh_report, fresh_err = deps.validator.validate_draft(draft_id, draft)
        if not fresh_report or fresh_report.ok ~= true then
            return nil, fresh_err or errors.new("E_AUTHOR_NOT_VALID", "draft validation changed")
        end
        local permission_ok, permission_err =
            deps.validator.validate_approval(draft, approval)


        if not permission_ok then
            return nil, permission_err
        end


        local package = {
            manifest = draft.manifest,
            files = draft.files
        }


        return deps.app_update.install(package)
    end


    return self
end


return M
