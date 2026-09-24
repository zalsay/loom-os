local app_author = require("core.app_author")


local saved = {}
local reports = {}


local deps = {}


deps.agent = {
    generate_app = function(input)
        return {
            operation = input.operation,
            manifest = {
                schema = 1, api = "0.1", min_loom_os = "0.1.0",
                id = "org.loom-os.generated.demo",
                name = "Generated Demo",
                version = "1.0.0",
                entry = "main.lua",
                permissions = { notification = true }
            },
            files = {
                {
                    path = "main.lua",
                    content = "return function(ctx) return true end"
                }
            }
        }
    end
}


deps.workspace = {
    create = function(draft)
        saved["draft-1"] = draft
        return "draft-1"
    end,


    read = function(id)
        return saved[id]
    end,


    write_report = function(id, report)
        reports[id] = report
    end,


    read_report = function(id)
        return reports[id]
    end,


    mark_failed = function() end,


    read_active_app = function()
        return nil
    end
}


deps.validator = {
    validate_draft = function()
        return {
            ok = true
        }
    end,


    validate_approval = function()
        return true
    end
}


deps.app_update = {
    install = function(package)
        return {
            pending = true,
            app_id = package.manifest.id,
            version = package.manifest.version
        }
    end
}


local author = app_author.new(deps)


local result = assert(author.create({
    prompt = "Create a demo App"
}))


assert(result.draft_id == "draft-1")
assert(result.report.ok == true)


local installed = assert(author.install("draft-1", {
    permissions = { "notification" }
}))


assert(installed.pending == true)


print("app_author_test: PASS")
